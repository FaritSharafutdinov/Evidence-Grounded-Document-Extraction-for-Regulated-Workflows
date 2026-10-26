#!/usr/bin/env python3
"""Why M5 (and M2) "break" the `state` axis: a per-instance look (K3, 2026-10-26).

M5 keeps M1's value but drops a claim to NOT_STATED when its verifier says No;
M2 re-decides each field from scratch. The aggregate `state` axis is much lower
for M2/M5 than for M1 — this script decomposes *which* instances they change and
in which direction, so the anomaly is explained rather than hidden.

Writes farit/results/state_anomaly.{json,md}.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path.cwd()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdsbench import annotations
from sdsbench.ontology import PRODUCT_FIELD_NAMES
from sdsbench.schema import PredictionSet

ROOT = Path.cwd()
PRED = ROOT / "farit" / "data" / "predictions"
RESULTS = ROOT / "farit" / "results"
METHODS = ("M1", "M2", "M5")


def load(method: str, layer: str) -> PredictionSet:
    return PredictionSet.load(PRED / f"s4_{method}_{layer}.json")


def field_state(pred, document, name):
    for doc in pred.documents:
        if doc.document == document:
            f = doc.fields.get(name)
            return f.state.value if f else None
    return None


def main() -> int:
    gold = annotations.load_gold(split="dev")
    gold_state = {
        (d.document, name): d.fields[name].state.value
        for d in gold
        for name in PRODUCT_FIELD_NAMES
        if name in d.fields
    }
    out: dict = {"layers": {}, "layers_both": {}}
    for layer in ("native", "ocr"):
        preds = {m: load(m, layer) for m in METHODS}
        per = {}
        for m in METHODS:
            right = sum(
                1 for (doc, name), gs in gold_state.items()
                if field_state(preds[m], doc, name) == gs
            )
            per[m] = {"state_correct": right, "n": len(gold_state)}
        # M1 -> M5 / M2 transitions on instances M1 got right
        trans = {}
        for m in ("M2", "M5"):
            changed = kept = 0
            to_not_stated = to_other = 0
            for (doc, name), gs in gold_state.items():
                s1 = field_state(preds["M1"], doc, name)
                sm = field_state(preds[m], doc, name)
                if s1 != gs:
                    continue  # only M1-correct instances
                if sm == gs:
                    kept += 1
                else:
                    changed += 1
                    if sm == "NOT_STATED":
                        to_not_stated += 1
                    else:
                        to_other += 1
            trans[m] = {
                "m1_correct": kept + changed,
                "kept": kept,
                "changed": changed,
                "changed_to_not_stated": to_not_stated,
                "changed_to_other": to_other,
            }
        out["layers"][layer] = {"state_accuracy": per, "m1_to": trans}
    payload = {"methods": list(METHODS), "result": out}
    (RESULTS / "state_anomaly.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = ["# State-anomaly decomposition (K3)", "",
             "Instances = dev product fields; `changed` counts only instances **M1 got right**.", ""]
    for layer in ("native", "ocr"):
        L = out["layers"][layer]
        lines.append(f"## {layer}")
        lines.append("")
        lines.append("| method | state correct / n |")
        lines.append("| --- | --- |")
        for m in METHODS:
            d = L["state_accuracy"][m]
            lines.append(f"| {m} | {d['state_correct']} / {d['n']} |")
        lines.append("")
        lines.append("| transition | M1-correct | kept | changed | → NOT_STATED | → other |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        for m in ("M2", "M5"):
            t = L["m1_to"][m]
            lines.append(f"| M1 → {m} | {t['m1_correct']} | {t['kept']} | {t['changed']} | {t['changed_to_not_stated']} | {t['changed_to_other']} |")
        lines.append("")
    (RESULTS / "state_anomaly.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print("wrote farit/results/state_anomaly.{json,md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())