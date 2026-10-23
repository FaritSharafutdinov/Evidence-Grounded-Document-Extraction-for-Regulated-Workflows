#!/usr/bin/env python3
"""K3 audit of product/component ownership in the sds_18 gold annotations.

Targeted check requested by the supervisor (steering note 2026-10-22, item 2:
"product/component ownership (sds_18)").

Read-only with respect to the shared data. For every gold field and ingredient
row of sds_18 it:
  * resolves each cited evidence/premise span verbatim against the native and
    OCR text layers (exact, or fuzzy with a reported score);
  * reports the page each span lands on and the surrounding line;
  * prints an ownership verdict per claim (product-level vs ingredient-level)
    so the verdicts can be reviewed by hand.

Outputs JSON + Markdown to farit/results/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path.cwd()
SRC = REPO_ROOT / "sdsbench"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(REPO_ROOT))

from sdsbench import annotations, textlayer  # noqa: E402
from sdsbench.ontology import (  # noqa: E402
    FIELD_SPECS,
    PRODUCT_FIELD_NAMES,
    field_is_defined_for,
)
from sdsbench import derivation  # noqa: E402

DOC = "sds_18.pdf"
RESULTS = REPO_ROOT / "farit" / "results"


def line_of(text: str, quote: str) -> str:
    idx = text.find(quote)
    if idx < 0:
        return ""
    start = text.rfind("\n", 0, idx) + 1
    end = text.find("\n", idx)
    if end < 0:
        end = len(text)
    return text[start:end].strip()


def resolve(native: textlayer.DocumentText, ocr, ref) -> dict:
    page = native.page(ref.page)
    exact = ref.text in page.text
    score = None
    if not exact:
        found = textlayer.find_in_page(page, ref.text, min_score=0.0)
        score = found.score if found is not None else None
    ocr_exact = None
    if ocr is not None:
        ocr_exact = ref.text in ocr.page(ref.page).text
    return {
        "page": ref.page,
        "text": ref.text,
        "exact_native": exact,
        "fuzzy_score": score,
        "ocr_exact": ocr_exact,
        "context": line_of(page.text, ref.text) or line_of(page.text, ref.text.strip()),
    }


def main() -> int:
    gold = annotations.load_gold(split="dev")
    doc = next(d for d in gold if d.document == DOC)
    native = textlayer.load(DOC, textlayer.NATIVE)
    try:
        ocr = textlayer.load(DOC, textlayer.OCR)
    except FileNotFoundError:
        ocr = None

    report: dict = {
        "document": DOC,
        "split": doc.split,
        "product_form": doc.product_form.value,
        "fields": {},
        "ingredients": {},
    }

    for name in PRODUCT_FIELD_NAMES:
        field = doc.fields[name]
        spec = FIELD_SPECS[name]
        refs = [("source", r) for r in field.evidence]
        resolved = [
            {"role": role, **resolve(native, ocr, ref)} for role, ref in refs
        ]
        resolved_spans = [
            {"role": "resolved_evidence", "page": r.page, "text": r.text,
             "bbox": r.bbox, "ocr_exact": r.ocr_exact}
            for r in field.resolved_evidence
        ] + [
            {"role": "resolved_premise", "page": r.page, "text": r.text,
             "bbox": r.bbox, "ocr_exact": r.ocr_exact}
            for r in field.resolved_premises
        ]
        report["fields"][name] = {
            "state": field.state.value,
            "derivation": field.derivation.value,
            "rule": field.rule,
            "value": field.value,
            "defined_for_form": field_is_defined_for(name, doc.product_form),
            "description": spec.description,
            "resolved": resolved,
            "resolved_spans": resolved_spans,
        }
        print(f"\n=== {name} :: {field.state.value}/{field.derivation.value} "
              f"value={field.value!r} defined_for_form={field_is_defined_for(name, doc.product_form)}")
        for item in resolved:
            flag = "OK " if item["exact_native"] else f"FUZZ {item['fuzzy_score']}"
            print(f"   [{item['role']:<8}] p{item['page']} {flag:<14} {item['text'][:70]!r}")
            if item["context"]:
                print(f"              ctx: {item['context'][:100]!r}")

    ing = doc.ingredients
    report["ingredients"]["state"] = ing.state.value if ing else None
    rows = []
    for item in (ing.items if ing else []):
        evs = item.evidence if isinstance(item.evidence, list) else ([item.evidence] if item.evidence else [])
        r = [resolve(native, ocr, e) for e in evs]
        rows.append(
            {
                "name": item.name,
                "cas": item.cas_number,
                "cas_state": item.cas_state.value,
                "concentration": item.concentration,
                "resolved": r,
            }
        )
    report["ingredients"]["items"] = rows
    print(f"\n=== ingredients :: {report['ingredients']['state']} ({len(rows)} rows)")
    for row in rows:
        r = row["resolved"]
        first = r[0] if r else None
        flag = "OK " if first and first["exact_native"] else "FUZZ"
        print(f"   {flag} cas={row['cas']} conc={row['concentration']:<10} p{first['page'] if first else '-'} "
              f"{row['name'][:50]!r}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / "sds18_ownership_check.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())