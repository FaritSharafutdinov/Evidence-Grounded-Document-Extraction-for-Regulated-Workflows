#!/usr/bin/env python3
"""M6 routing coverage (K3, 2026-10-26).

The critic's M1 finding: "section routing does not improve grounding" is not
separated from "the hand-written map routed away the pages that held the
evidence". This measures that directly: for each dev product field, does the
sentence that carries the gold evidence/premise live on a *routed* page?

Writes farit/results/m6_routing_coverage.{json,md}.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "farit" / "src" / "extraction"))

from sdsbench import annotations  # noqa: E402
from sdsbench.ontology import PRODUCT_FIELD_NAMES  # noqa: E402
import methods  # noqa: E402

CORPUS = ROOT / "farit" / "data" / "corpus"
RESULTS = ROOT / "farit" / "results"


def page_texts(layer: str) -> dict[tuple[str, int], str]:
    out: dict[tuple[str, int], str] = {}
    with (CORPUS / f"units_{layer}.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            u = json.loads(line)
            out[(u["document"], u["page"])] = u["text"]
    return out


def routed(document: str, pages: dict, cues: tuple[str, ...]) -> set[int]:
    hit = {
        p for (doc, p), text in pages.items()
        if doc == document and any(re.search(c, text, re.IGNORECASE) for c in cues)
    }
    if hit:
        return hit
    return {p for (doc, p) in pages if doc == document}  # fallback: whole doc


def gold_pages(field) -> set[int]:
    pages = {s.page for s in field.gold_targets}
    return pages


def main() -> int:
    gold = annotations.load_gold(split="dev")
    out: dict = {"layers": {}}
    for layer in ("native", "ocr"):
        pages = page_texts(layer)
        rows = []
        any_in = all_in = total = 0
        for doc in gold:
            for name in PRODUCT_FIELD_NAMES:
                field = doc.fields.get(name)
                if field is None or not field.gold_targets:
                    continue
                gp = gold_pages(field)
                if not gp:
                    continue
                rp = routed(doc.document, pages, methods._SECTION_CUES.get(name, ()))
                total += 1
                if gp & rp:
                    any_in += 1
                if gp <= rp:
                    all_in += 1
                else:
                    rows.append({"document": doc.document, "field": name,
                                 "gold_pages": sorted(gp), "routed_pages": sorted(rp)})
        out["layers"][layer] = {
            "n_instances": total,
            "any_gold_page_routed": any_in,
            "all_gold_pages_routed": all_in,
            "misses": rows,
        }
    (RESULTS / "m6_routing_coverage.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    lines = ["# M6 routing coverage (K3)", "",
             "Does the gold-evidence page fall inside the section-routed pages for M6?", ""]
    for layer, d in out["layers"].items():
        lines.append(f"## {layer}")
        lines.append("")
        lines.append(f"- instances: **{d['n_instances']}**")
        lines.append(f"- **any** gold page routed: **{d['any_gold_page_routed']}** ({round(100*d['any_gold_page_routed']/max(d['n_instances'],1))}%)")
        lines.append(f"- **all** gold pages routed: **{d['all_gold_pages_routed']}** ({round(100*d['all_gold_pages_routed']/max(d['n_instances'],1))}%)")
        lines.append("")
        if d["misses"]:
            lines.append("| document | field | gold pages | routed pages |")
            lines.append("| --- | --- | --- | --- |")
            for m in d["misses"][:20]:
                lines.append(f"| {m['document']} | {m['field']} | {m['gold_pages']} | {m['routed_pages']} |")
            lines.append("")
    (RESULTS / "m6_routing_coverage.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())