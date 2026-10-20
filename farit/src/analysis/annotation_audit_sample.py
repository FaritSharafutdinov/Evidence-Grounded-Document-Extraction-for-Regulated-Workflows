#!/usr/bin/env python3
"""TASK-011: deterministic stratified sample for the gold-annotation audit.

Reads farit/data/corpus/gold_evidence.jsonl — dev split only (locked split
sds_21..29 is never touched), product fields only. The 29 'ingredients'
aggregate rows are ingredient instances, not part of the 203 field instances
the spec's distributions refer to (7 product fields x 29 documents = 203),
so they are excluded from sampling.

Sample (seed=42, groups A-D disjoint; E may overlap with A by design):

    A  EXPLICIT + PRESENT             8   (diverse documents and fields)
    B  ONTOLOGY                       8   (all NOT_APPLICABLE in dev)
    C  COMPOSITION_IMPLIED            4   (all of them)
    D  missing-value states          10   (NOT_APPLICABLE 5, NOT_STATED 3, NO_DATA 2)
    E  PRESENT, full-document view   10   (one instance per document, 10 distinct docs)

Writes the audit skeleton farit/results/annotation_audit.json (array of
records with verdict=null), each record carrying the spec schema
{document, field, state, derivation, group, verdict, error_type, quotes,
notes} plus a "gold" helper key (value + evidence quotes) so the audit file
is self-contained for K3 verification.

With --dump, also writes human-readable worksheets to
farit/logs/TASK-011/worksheet-*.txt: gold info + full native text of the
evidence pages (groups A-D) or of every page of the document (group E).

CLI (from repo root):
    ~/ds_env/bin/python farit/src/analysis/annotation_audit_sample.py [--dump]
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

REPO_ROOT = Path.cwd()
CORPUS_DIR = REPO_ROOT / "farit" / "data" / "corpus"
RESULTS_DIR = REPO_ROOT / "farit" / "results"
LOG_DIR = REPO_ROOT / "farit" / "logs" / "TASK-011"

SEED = 42

# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_dev_product_instances() -> list[dict]:
    rows = [
        json.loads(line)
        for line in (CORPUS_DIR / "gold_evidence.jsonl").read_text().splitlines()
        if line.strip()
    ]
    dev = [r for r in rows if r["split"] == "dev" and r["field"] != "ingredients"]
    # Hard invariant: dev split only, and no locked document may leak in.
    locked = {f"sds_{i:02d}.pdf" for i in range(21, 30)}
    assert not any(r["document"] in locked for r in dev), "locked split leaked into sample pool"
    return dev


def load_native_pages() -> dict[tuple[str, int], str]:
    pages: dict[tuple[str, int], str] = {}
    for line in (CORPUS_DIR / "units_native.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        unit = json.loads(line)
        assert unit["layer"] == "native"
        pages[(unit["document"], unit["page"])] = unit["text"]
    return pages


# ---------------------------------------------------------------------------
# Stratified sampling (deterministic: sorted pools + random.Random(SEED))
# ---------------------------------------------------------------------------


def _pool(rows: list[dict], **crit: str) -> list[dict]:
    """Sorted pool matching derivation/state criteria (None = no filter)."""
    out = []
    for r in rows:
        if all(r[k] == v for k, v in crit.items() if v is not None):
            out.append(r)
    return sorted(out, key=lambda r: (r["document"], r["field"]))


def _pick_diverse(
    rng: random.Random,
    pool: list[dict],
    n: int,
    max_per_doc: int = 1,
    max_per_field: int = 1,
    exclude: set | None = None,
) -> list[dict]:
    """Greedy diversity pick: prefer unseen documents, then unseen fields.

    Relaxation passes: if the constraints cannot fill the quota, retry with
    max_per_doc/max_per_field + 1 until filled (pool is always large enough).
    """
    exclude = exclude or set()
    candidates = [r for r in pool if (r["document"], r["field"]) not in exclude]
    cur_doc, cur_field = max_per_doc, max_per_field
    while True:
        shuffled = sorted(candidates, key=lambda r: (r["document"], r["field"]))
        rng.shuffle(shuffled)
        docs: Counter = Counter()
        fields: Counter = Counter()
        picked: list[dict] = []
        for r in shuffled:
            if len(picked) == n:
                break
            if docs[r["document"]] < cur_doc and fields[r["field"]] < cur_field:
                picked.append(r)
                docs[r["document"]] += 1
                fields[r["field"]] += 1
        if len(picked) == n:
            return picked
        cur_doc += 1
        cur_field += 1


def build_sample(rows: list[dict]) -> list[dict]:
    rng = random.Random(SEED)
    taken: set[tuple[str, str]] = set()  # (document, field) already in A-D

    group_a = _pick_diverse(rng, _pool(rows, derivation="EXPLICIT", state="PRESENT"), 8,
                            max_per_doc=1, max_per_field=2)
    taken |= {(r["document"], r["field"]) for r in group_a}

    group_b = _pick_diverse(rng, _pool(rows, derivation="ONTOLOGY"), 8,
                            max_per_doc=1, max_per_field=2, exclude=taken)
    taken |= {(r["document"], r["field"]) for r in group_b}

    group_c = _pool(rows, derivation="COMPOSITION_IMPLIED")  # all 4
    taken |= {(r["document"], r["field"]) for r in group_c}

    group_d = (
        _pick_diverse(rng, _pool(rows, state="NOT_APPLICABLE"), 5, exclude=taken)
        + _pick_diverse(rng, _pool(rows, state="NOT_STATED"), 3, exclude=taken)
        + _pick_diverse(rng, _pool(rows, state="NO_DATA"), 2, exclude=taken)
    )
    taken |= {(r["document"], r["field"]) for r in group_d}

    # E: one PRESENT instance per document, 10 distinct documents (full read).
    present = _pool(rows, state="PRESENT")
    by_doc: dict[str, list[dict]] = {}
    for r in present:
        by_doc.setdefault(r["document"], []).append(r)
    group_e = _pick_diverse(rng, present, 10, max_per_doc=1, max_per_field=2)

    sample = (
        [("A", r) for r in group_a]
        + [("B", r) for r in group_b]
        + [("C", r) for r in group_c]
        + [("D", r) for r in group_d]
        + [("E", r) for r in group_e]
    )
    # Quota assertions (acceptance criteria).
    assert len(group_a) == 8 and len(group_b) == 8 and len(group_c) == 4
    assert len(group_d) == 10
    assert Counter(r["state"] for r in group_d) == Counter(
        {"NOT_APPLICABLE": 5, "NOT_STATED": 3, "NO_DATA": 2}
    )
    assert len(group_e) == 10 and len({r["document"] for r in group_e}) == 10
    assert len({(r["document"], r["field"]) for _, r in sample[:30]}) == 30  # A-D disjoint
    return sample


# ---------------------------------------------------------------------------
# Skeleton records + worksheets
# ---------------------------------------------------------------------------


def skeleton_record(group: str, r: dict) -> dict:
    return {
        "document": r["document"],
        "field": r["field"],
        "state": r["state"],
        "derivation": r["derivation"],
        "group": group,
        "verdict": None,
        "error_type": None,
        "quotes": [],
        "notes": "",
        "gold": {
            "value": r["value"],
            "evidence": [
                {"page": e["page"], "text": e["text"]} for e in r["evidence_set"]
            ],
        },
    }


def dump_worksheets(records: list[dict], pages: dict[tuple[str, int], str]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    for rec in records:
        doc, field, group = rec["document"], rec["field"], rec["group"]
        gold_pages = sorted({e["page"] for e in rec["gold"]["evidence"]}) or [1]
        # Group E: read every page of the document; A-D: the evidence pages.
        all_pages = sorted({p for (d, p) in pages if d == doc})
        wanted = all_pages if group == "E" else gold_pages
        lines = [
            f"# TASK-011 worksheet — group {group} — {doc} / {field}",
            f"state={rec['state']}  derivation={rec['derivation']}  "
            f"gold_value={rec['gold']['value']!r}",
            "",
            "## gold evidence_set",
        ]
        for e in rec["gold"]["evidence"]:
            lines.append(f"- page {e['page']}: {e['text']!r}")
        for p in wanted:
            lines += ["", f"===== PAGE {p} (native) =====", pages[(doc, p)]]
        out = LOG_DIR / f"worksheet-{group}-{doc.replace('.pdf', '')}-{field}.txt"
        out.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", action="store_true",
                        help="also write worksheets to farit/logs/TASK-011/")
    args = parser.parse_args()

    rows = load_dev_product_instances()
    sample = build_sample(rows)
    records = [skeleton_record(group, r) for group, r in sample]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "annotation_audit.json"
    out_path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")

    counts = Counter(rec["group"] for rec in records)
    print(f"wrote {out_path} ({len(records)} records: " +
          ", ".join(f"{g}={counts[g]}" for g in "ABCDE") + ")")
    if args.dump:
        pages = load_native_pages()
        dump_worksheets(records, pages)
        print(f"wrote worksheets to {LOG_DIR}/")


if __name__ == "__main__":
    main()
