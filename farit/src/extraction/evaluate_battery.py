#!/usr/bin/env python3
"""Score the S4 battery and write the comparison table (TASK-015).

Usage (from the repository root)::

    ~/ds_env/bin/python farit/src/extraction/evaluate_battery.py --smoke

Loads every ``farit/data/predictions/s4_*.json`` (or explicit paths), scores it
against gold v1.3 ``dev`` with ``sdsbench.evaluator`` (7 axes + joint, evidence-
bearing subset, slices) and aggregates the per-call cost from the matching
``*.meta.json``. The frozen Qwen2.5-7B file is shown in a separate
"Inherited (old gold)" section; rules-v4 is a first-class method here and is not
duplicated there. Writes ``farit/results/s4_battery[_smoke].{json,md}``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EXTRACTION_DIR = Path(__file__).resolve().parent
for _path in (str(REPO_ROOT), str(EXTRACTION_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from sdsbench import annotations  # noqa: E402
from sdsbench.evaluator import (  # noqa: E402
    AXES,
    NOT_APPLICABLE,
    PASSING,
    evaluate,
    evaluate_ingredients,
)
from sdsbench.schema import PredictionSet  # noqa: E402
from scripts.evaluate import guard_split  # noqa: E402

DEFAULT_PREDICTIONS_DIR = REPO_ROOT / "farit" / "data" / "predictions"
DEFAULT_RESULTS_DIR = REPO_ROOT / "farit" / "results"
INHERITED_FILES = (
    REPO_ROOT / "data" / "predictions" / "llm-qwen2.5-7b-native-rows.json",
)

STAGES = (
    ("state", ("state",)),
    ("+ value", ("state", "value")),
    ("+ page", ("state", "value", "page")),
    ("+ span", ("state", "value", "page", "span")),
    ("+ bbox", ("state", "value", "page", "span", "bbox")),
    ("+ derivation", ("state", "value", "page", "span", "bbox", "derivation")),
    ("+ support (strict joint)", AXES),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="S4 battery evaluator")
    parser.add_argument("predictions", nargs="*", type=Path, help="explicit prediction files")
    parser.add_argument("--smoke", action="store_true", help="use s4_*_smoke.json artifacts")
    parser.add_argument("--predictions-dir", type=Path, default=DEFAULT_PREDICTIONS_DIR)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--tag", default=None, help="override output tag (default: smoke or battery)")
    return parser.parse_args()


def discover(args: argparse.Namespace) -> list[Path]:
    if args.predictions:
        return sorted(args.predictions)
    marker = "_smoke.json" if args.smoke else ".json"
    files = [
        path
        for path in sorted(args.predictions_dir.glob("s4_*.json"))
        if path.name.endswith(marker) and not path.name.endswith(".meta.json")
    ]
    if not args.smoke:
        files = [path for path in files if "_smoke" not in path.name]
    return files


def _axis(summary, name: str, subset=None) -> dict:
    stats = summary.axis(name, subset)
    return {
        "rate": stats.rate,
        "satisfied": stats.satisfied,
        "applicable": stats.applicable,
        "undecidable": stats.undecidable,
    }


def _conjunction(summary) -> dict:
    result = {}
    for label, axes in STAGES:
        result[label] = {
            "all": summary.conjunction_rate(axes),
            "evidence_bearing": summary.conjunction_rate(axes, summary.evidence_bearing),
        }
    return result


def ingredient_metrics(summary) -> dict:
    return {
        "gold_rows": summary.gold_rows,
        "predicted_rows": summary.predicted_rows,
        "matched": summary.matched,
        "records_exact": summary.records_exact,
        "records_with_evidence": summary.records_with_evidence,
        "precision": summary.precision,
        "recall": summary.recall,
        "key_recall": summary.key_recall,
    }


def score_prediction_set(
    path: Path, gold_all: list, gold_by_key: dict
) -> dict:
    prediction_set = PredictionSet.load(path)
    predicted = set(prediction_set.document_names)
    gold = [item for item in gold_all if item.document in predicted]
    missing = [name for name in predicted if name not in {item.document for item in gold_all}]
    if missing:
        raise SystemExit(f"{path.name}: predictions cover non-dev documents {missing}")
    guard_split(gold, allow_locked=False)
    summary = evaluate(gold, prediction_set)
    ingredients = evaluate_ingredients(gold, prediction_set)

    evidence_bearing = summary.evidence_bearing
    metrics = {
        "system": summary.system,
        "prediction_id": prediction_set.prediction_id,
        "split": prediction_set.split,
        "layer": prediction_set.configuration.get("layer"),
        "n_documents": len(gold),
        "n_instances": len(summary.instances),
        "n_evidence_bearing": len(evidence_bearing),
        "axes": {axis: _axis(summary, axis) for axis in AXES},
        "joint_all": summary.joint_rate(),
        "joint_evidence_bearing": summary.joint_rate(evidence_bearing),
        "conjunction": _conjunction(summary),
        "strict_state": summary.axis("state").rate,
        "lenient_state": summary.lenient_state_rate(),
        "undecidable_instances": summary.undecidable_count(),
        "verbatim": dict(zip(("ok", "cited"), summary.verbatim_rate())),
        "ingredients": ingredient_metrics(ingredients),
    }

    def subset_rate(items) -> dict:
        return {
            "n": len(items),
            "joint_all": summary.joint_rate(items),
        }

    explicit = [i for i in summary.instances if i.gold_derivation == "EXPLICIT"]
    derived = [i for i in summary.instances if i.gold_derivation != "EXPLICIT"]
    single, multi = [], []
    cross, single_page = [], []
    for instance in summary.instances:
        field = gold_by_key.get((instance.document, instance.field))
        targets = field.gold_targets if field is not None else []
        (multi if len(targets) >= 2 else single).append(instance)
        pages = {target.page for target in targets}
        (cross if len(pages) > 1 else single_page).append(instance)
    metrics["slices"] = {
        "explicit": subset_rate(explicit),
        "derived": subset_rate(derived),
        "single_evidence": subset_rate(single),
        "multi_evidence": subset_rate(multi),
        "cross_page": subset_rate(cross),
        "single_page": subset_rate(single_page),
    }
    return metrics


def load_cost(path: Path) -> dict:
    meta_path = path.with_name(path.stem + ".meta.json")
    if not meta_path.exists():
        return {"cost": None, "info": None}
    with open(meta_path, encoding="utf-8") as handle:
        meta = json.load(handle)
    return {
        "cost": meta.get("cost"),
        "info": meta.get("info"),
        "method": meta.get("method"),
        "backend": meta.get("backend"),
        "model": meta.get("model"),
    }


def score_inherited(path: Path, gold_all: list, gold_by_key: dict) -> dict | None:
    if not path.exists():
        return None
    metrics = score_prediction_set(path, gold_all, gold_by_key)
    metrics["gold"] = "gold v1.3 (dev); frozen predictions re-scored against the current gold"
    metrics["note"] = (
        "Qwen2.5-7B native rows, inherited. The predictions were produced on an earlier "
        "gold (v1.0; its own report quotes 6.4% joint there); the numbers below re-score "
        "those frozen predictions against the current gold v1.3 and are shown only as a "
        "historical reference, never combined with the battery."
    )
    return metrics


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def _fmt_int(value) -> str:
    return "-" if value is None else str(value)


def render_markdown(result: dict, smoke: bool) -> str:
    lines: list[str] = []
    lines.append("# S4 baseline battery — " + ("smoke" if smoke else "full") + " run")
    lines.append("")
    lines.append(
        "Six simple extraction methods on one model, scored against gold v1.3 (dev split). "
        "M3 and M5 depend on the M1 pass; M4 is the inherited rules-v4 re-scored against v1.3 "
        "with zero LLM calls; M6 routes each field to its SDS section by a hand-written rule."
    )
    lines.append("")
    entries = result["methods"]
    if not entries:
        lines.append("_no prediction files found_")
        return "\n".join(lines) + "\n"

    order = sorted(entries)

    lines.append("## Joint score (7-axis conjunction) by method × layer")
    lines.append("")
    lines.append("| Method | Layer | n inst | 7-axis joint | joint (evidence-bearing) |")
    lines.append("| --- | --- | ---: | ---: | ---: |")
    for key in order:
        method, layer = key.split("/", 1)
        item = entries[key]
        lines.append(
            f"| {method} | {layer} | {item['n_instances']} | {_pct(item['joint_all'])} | "
            f"{_pct(item['joint_evidence_bearing'])} |"
        )
    lines.append("")

    lines.append("## Per-axis rates (method × layer)")
    lines.append("")
    header = "| Method | Layer | " + " | ".join(AXES) + " |"
    lines.append(header)
    lines.append("|" + "|".join(["---"] * (2 + len(AXES))) + "|")
    for key in order:
        method, layer = key.split("/", 1)
        item = entries[key]
        cells = [_pct(item["axes"][axis]["rate"]) for axis in AXES]
        lines.append(f"| {method} | {layer} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Cumulative conjunction")
    lines.append("")
    lines.append("| Method | Layer | " + " | ".join(label for label, _ in STAGES) + " |")
    lines.append("|" + "|".join(["---"] * (2 + len(STAGES))) + "|")
    for key in order:
        method, layer = key.split("/", 1)
        item = entries[key]
        cells = [_pct(item["conjunction"][label]["all"]) for label, _ in STAGES]
        lines.append(f"| {method} | {layer} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Slices (joint score of the subset)")
    lines.append("")
    slice_names = ("explicit", "derived", "single_evidence", "multi_evidence", "cross_page", "single_page")
    lines.append("| Method | Layer | " + " | ".join(slice_names) + " |")
    lines.append("|" + "|".join(["---"] * (2 + len(slice_names))) + "|")
    for key in order:
        method, layer = key.split("/", 1)
        item = entries[key]
        cells = [
            f"{_pct(item['slices'][name]['joint_all'])} (n={item['slices'][name]['n']})"
            for name in slice_names
        ]
        lines.append(f"| {method} | {layer} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Cost (aggregated from *.meta.json)")
    lines.append("")
    lines.append("| Method | Layer | backend | n calls | prompt tokens | completion tokens | latency s |")
    lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: |")
    for key in order:
        method, layer = key.split("/", 1)
        cost_meta = result.get("cost", {}).get(key) or {}
        backend = cost_meta.get("backend", "")
        cost = cost_meta.get("cost")
        if cost is None:
            lines.append(f"| {method} | {layer} | {backend} | - | - | - | - |")
            continue
        lines.append(
            f"| {method} | {layer} | {backend} | {cost['n_calls']} | {cost['prompt_tokens']} | "
            f"{cost['completion_tokens']} | {cost['latency_s']:.1f} |"
        )
    lines.append("")

    lines.append("## Ingredients (matched records)")
    lines.append("")
    lines.append("| Method | Layer | gold rows | predicted rows | key recall | precision | recall |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for key in order:
        method, layer = key.split("/", 1)
        ing = entries[key]["ingredients"]
        lines.append(
            f"| {method} | {layer} | {ing['gold_rows']} | {ing['predicted_rows']} | "
            f"{_pct(ing['key_recall'])} | {_pct(ing['precision'])} | {_pct(ing['recall'])} |"
        )
    lines.append("")

    inherited = result.get("inherited")
    if inherited:
        lines.append("## Inherited (re-scored on gold v1.3)")
        lines.append("")
        lines.append("Frozen Qwen2.5-7B native-rows artifact, produced on gold v1.0 (its own "
                     "report quotes 6.4% joint there). The numbers below re-score those frozen "
                     "predictions against the current gold v1.3; shown only as a historical "
                     "reference and never mixed with the battery table.")
        lines.append("")
        lines.append("| System | n inst | 7-axis joint | joint (evidence-bearing) |")
        lines.append("| --- | ---: | ---: | ---: |")
        for name, item in inherited.items():
            lines.append(
                f"| {name} | {item['n_instances']} | {_pct(item['joint_all'])} | "
                f"{_pct(item['joint_evidence_bearing'])} |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    gold_all = annotations.load_gold(split="dev")
    guard_split(gold_all, allow_locked=False)
    gold_by_key = {
        (document.document, name): field
        for document in gold_all
        for name, field in document.fields.items()
    }

    files = discover(args)
    methods: dict[tuple[str, str], dict] = {}
    costs: dict[str, dict] = {}
    errors: dict[str, str] = {}
    for path in files:
        try:
            metrics = score_prediction_set(path, gold_all, gold_by_key)
        except Exception as error:  # noqa: BLE001 - one bad file must not kill the table
            errors[path.name] = f"{type(error).__name__}: {error}"
            continue
        meta = load_cost(path)
        method = (meta.get("method") or path.stem.split("_")[1]).upper()
        layer = metrics["layer"] or path.stem.split("_")[2]
        methods[(method, layer)] = metrics
        costs[f"{method}/{layer}"] = meta
        print(
            f"{path.name}: joint={_pct(metrics['joint_all'])} "
            f"joint_eb={_pct(metrics['joint_evidence_bearing'])} "
            f"n={metrics['n_instances']} (layer {layer})"
        )

    inherited = {}
    for path in INHERITED_FILES:
        item = score_inherited(path, gold_all, gold_by_key)
        if item is not None:
            inherited[item["system"]] = item
            print(f"inherited {item['system']}: joint={_pct(item['joint_all'])}")

    tag = args.tag or ("smoke" if args.smoke else "battery")
    result = {
        "configuration": {
            "gold": "v1.3",
            "split": "dev",
            "scope": "smoke" if args.smoke else "full",
            "methods": sorted({method for method, _ in methods}),
            "files": [path.name for path in files],
        },
        "methods": {f"{method}/{layer}": item for (method, layer), item in methods.items()},
        "cost": costs,
        "inherited": inherited,
        "errors": errors,
    }
    args.results_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.results_dir / f"s4_battery_{tag}.json"
    md_path = args.results_dir / f"s4_battery_{tag}.md"
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write(render_markdown(result, args.smoke))
    print(f"wrote {json_path} and {md_path}")
    if errors:
        print(f"WARNING: {len(errors)} file(s) failed: {errors}")
    return 0


if __name__ == "__main__":
    sys.exit(main())