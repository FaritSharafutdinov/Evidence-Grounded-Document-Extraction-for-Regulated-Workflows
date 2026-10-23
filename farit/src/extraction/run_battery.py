#!/usr/bin/env python3
"""Run the S4 baseline battery and write predictions + cost meta (TASK-015).

Usage (from the repository root)::

    ~/ds_env/bin/python farit/src/extraction/run_battery.py \
        --backend mlx --model mlx-community/Qwen3.5-2B-MLX-4bit \
        --layer both --methods M1,M2,M3,M4,M5 --docs sds_05.pdf --split dev --smoke

Writes ``farit/data/predictions/s4_<method>_<layer>[_smoke].json`` (a valid
``PredictionSet``, system tag ``s4-...``) and ``*.meta.json`` with per-call
token/latency usage. Only ``farit/`` is written; the locked split is refused and
every document list is filtered to ``split == "dev"``.
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

from sdsbench import annotations, textlayer  # noqa: E402
from sdsbench.schema import PredictionSet  # noqa: E402
from scripts.evaluate import guard_split  # noqa: E402

from backends import make_backend  # noqa: E402
from methods import (  # noqa: E402
    DEPENDS_ON_M1,
    METHODS,
    CallRecord,
    m1_all_fields,
    m2_individual_field,
    m3_contextual_verification,
    m4_rules_v4,
    m5_basic_verifier,
)

DEFAULT_MODEL = "mlx-community/Qwen3.5-2B-MLX-4bit"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "farit" / "data" / "predictions"
DEFAULT_CACHE_DIR = REPO_ROOT / "farit" / "data" / "llm_cache" / "s4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="S4 extraction battery runner")
    parser.add_argument("--backend", choices=["mlx", "openai"], default="mlx")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default=None, help="hub base URL for --backend openai")
    parser.add_argument("--layer", choices=["native", "ocr", "both"], default="both")
    parser.add_argument(
        "--methods",
        default="M1,M2,M3,M4,M5",
        help="comma-separated subset of M1,M2,M3,M4,M5",
    )
    parser.add_argument("--docs", default=None, help="comma-separated document names to run")
    parser.add_argument("--limit", type=int, default=None, help="keep only the first N documents")
    parser.add_argument("--split", choices=["dev"], default="dev")
    parser.add_argument("--smoke", action="store_true", help="append _smoke to artifact names")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    return parser.parse_args()


def cost_summary(calls: list[CallRecord]) -> dict:
    return {
        "n_calls": sum(call.n_calls for call in calls),
        "n_records": len(calls),
        "prompt_tokens": sum(call.prompt_tokens for call in calls),
        "completion_tokens": sum(call.completion_tokens for call in calls),
        "latency_s": round(sum(call.latency_s for call in calls), 3),
        "n_cached": sum(1 for call in calls if call.cached),
        "n_errors": sum(1 for call in calls if call.error),
    }


def select_documents(args: argparse.Namespace) -> list[str]:
    gold = annotations.load_gold(split=args.split)
    guard_split(gold, allow_locked=False)
    all_documents = [item.document for item in gold]
    if args.docs:
        wanted = {name if name.endswith(".pdf") else f"{name}.pdf" for name in args.docs.split(",")}
        unknown = wanted - set(all_documents)
        if unknown:
            raise SystemExit(f"--docs names not in the dev split: {sorted(unknown)}")
        documents = [name for name in all_documents if name in wanted]
    else:
        documents = all_documents
    if args.limit is not None:
        documents = documents[: args.limit]
    if not documents:
        raise SystemExit("no documents selected")
    return documents


def layers_for(choice: str) -> list[str]:
    return [textlayer.NATIVE, textlayer.OCR] if choice == "both" else [choice]


def suffix(method: str, layer: str, smoke: bool) -> str:
    return f"s4_{method}_{layer}" + ("_smoke" if smoke else "")


def configuration(
    method: str, layer: str, backend_name: str, model: str, smoke: bool
) -> dict[str, str]:
    config = {
        "layer": layer,
        "layout": "rows",
        "extractor": f"s4:{method}",
        "backend": backend_name,
        "model": model,
        "split": "dev",
        "scope": "smoke" if smoke else "full",
    }
    if method == "M4":
        config["extractor"] = "rules-v4"
        config["note"] = "inherited rules-v4 (rows), re-scored on gold v1.2, 0 LLM calls"
    if method in DEPENDS_ON_M1:
        config["depends_on"] = "M1"
    return config


def write_artifacts(
    args: argparse.Namespace,
    method: str,
    layer: str,
    documents: list[str],
    predictions: dict[str, object],
    calls: list[CallRecord],
    info: dict,
) -> Path:
    backend_name = calls[0].backend if calls else args.backend
    system = f"s4-{method}-{layer}" + ("-smoke" if args.smoke else "")
    config = configuration(method, layer, backend_name, args.model, args.smoke)
    prediction_set = PredictionSet(
        system=system,
        configuration=config,
        documents=[predictions[name] for name in documents],
    )
    stem = suffix(method, layer, args.smoke)
    path = args.output / f"{stem}.json"
    prediction_set.save(path)
    meta = {
        "method": method,
        "method_description": METHODS[method],
        "system": system,
        "backend": backend_name,
        "model": args.model,
        "layer": layer,
        "split": "dev",
        "documents": documents,
        "prediction_id": prediction_set.prediction_id,
        "configuration": config,
        "cost": cost_summary(calls),
        "info": info,
        "calls": [call.to_dict() for call in calls],
    }
    with open(args.output / f"{stem}.meta.json", "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2, ensure_ascii=False)
    return path


def run_first_pass(
    backend,
    documents: list[str],
    layer: str,
) -> tuple[dict[str, object], list[CallRecord], dict]:
    predictions: dict[str, object] = {}
    calls: list[CallRecord] = []
    info: dict = {"documents_with_contract_violations": 0, "contract_violations": {}}
    for document in documents:
        prediction, records, document_info = m1_all_fields(document, layer, backend)
        predictions[document] = prediction
        calls.extend(records)
        counts = document_info.get("contract_violations", {})
        if counts:
            info["documents_with_contract_violations"] += 1
            for code, count in counts.items():
                info["contract_violations"][code] = info["contract_violations"].get(code, 0) + count
    return predictions, calls, info


def main() -> int:
    args = parse_args()
    systems = [name.strip().upper() for name in args.methods.split(",") if name.strip()]
    unknown = [name for name in systems if name not in METHODS]
    if unknown:
        raise SystemExit(f"unknown methods: {unknown}")

    documents = select_documents(args)
    layers = layers_for(args.layer)
    backend = make_backend(
        args.backend, args.model, args.base_url, args.cache_dir, use_cache=not args.no_cache
    )

    print(f"backend={args.backend} model={args.model} layers={layers} methods={systems}")
    print(f"documents ({len(documents)}): {', '.join(documents)}")

    needs_m1 = any(name in ("M1", *DEPENDS_ON_M1) for name in systems)
    first_pass: dict[str, tuple[dict[str, object], list[CallRecord], dict]] = {}
    if needs_m1:
        for layer in layers:
            predictions, calls, info = run_first_pass(backend, documents, layer)
            first_pass[layer] = (predictions, calls, info)

    written: list[Path] = []
    for method in systems:
        for layer in layers:
            if method == "M1":
                predictions, calls, info = first_pass[layer]
            elif method == "M4":
                predictions, calls, info = {}, [], {"extractor": "rules-v4", "n_calls": 0}
                for document in documents:
                    prediction, records, document_info = m4_rules_v4(document, layer)
                    predictions[document] = prediction
                    calls.extend(records)
                    info.update(document_info)
            elif method == "M2":
                predictions, calls, info = {}, [], {"contract_violations": {}}
                for document in documents:
                    prediction, records, document_info = m2_individual_field(
                        document, layer, backend
                    )
                    predictions[document] = prediction
                    calls.extend(records)
                    info.update(document_info)
            else:  # M3 / M5 depend on the shared M1 pass
                base_predictions, m1_calls, m1_info = first_pass[layer]
                predictions, calls, info = {}, [], {"depends_on": "M1"}
                info["m1_dependency_cost"] = cost_summary(m1_calls)
                for document in documents:
                    if method == "M3":
                        prediction, records, document_info = m3_contextual_verification(
                            document, layer, backend, base_predictions[document]
                        )
                    else:
                        prediction, records, document_info = m5_basic_verifier(
                            document, layer, backend, base_predictions[document]
                        )
                    predictions[document] = prediction
                    calls.extend(records)
                    info.update(document_info)

            path = write_artifacts(args, method, layer, documents, predictions, calls, info)
            cost = cost_summary(calls)
            written.append(path)
            print(
                f"  {suffix(method, layer, args.smoke)}: "
                f"{len(predictions)} docs, calls={cost['n_calls']}, "
                f"prompt_tokens={cost['prompt_tokens']}, "
                f"completion_tokens={cost['completion_tokens']}, "
                f"latency={cost['latency_s']:.1f}s -> {path.name}"
            )

    print(f"wrote {len(written)} prediction set(s) + meta -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())