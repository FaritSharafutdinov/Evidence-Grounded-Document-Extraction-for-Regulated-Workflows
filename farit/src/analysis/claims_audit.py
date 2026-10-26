#!/usr/bin/env python3
"""Pre-send claims audit — the reliability gate (K3).

Every number that reaches the supervisor must be traceable to a raw artifact and
carry an explicit scope. This script is the mechanical part of that discipline:

  1. **Artifact-backed claims** — a curated register of the headline claims in the
     supervisor-facing documents (`farit/docs/RESEARCH-STATE.md`,
     `farit/docs/report-*.md`). Each claim recomputes its expected value from a raw
     artifact and checks the document still states that value (PASS / MISMATCH /
     MISSING). Numbers are never hard-coded twice: the artifact is the source.
  2. **Overclaim lint** — flags absolute/confidence language ("unaffected",
     "answered", "proves", ...) that has burned us before (Argon teardown, 2026-10-26).
  3. **Split semantics** — `sds_21-29` are an *audit* split (previously examined),
     NOT an unbiased final test (`PROJECT_GUIDE.md` §2.4; steering note 2026-10-22).
     The gate fails if a doc still calls them an unbiased/final test.
  4. **Cross-document consistency** — the same quantity must not appear with two
     different values or scopes across documents.

Output: `farit/results/claims_audit.{json,md}`. Exit code 1 if any claim FAILs.

Usage (from the repository root)::

    ~/ds_env/bin/python farit/src/analysis/claims_audit.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

S4_ARTIFACT = REPO_ROOT / "farit" / "results" / "s4_battery_goldv13.json"
S5_ARTIFACT = REPO_ROOT / "farit" / "results" / "s5_cases.json"
COST_ARTIFACT = REPO_ROOT / "farit" / "results" / "cost_accounting.json"
CORPUS_STATS = REPO_ROOT / "farit" / "data" / "corpus" / "corpus_stats.json"
GOLD_EVIDENCE = REPO_ROOT / "farit" / "data" / "corpus" / "gold_evidence.jsonl"

DOCS = {
    "state": REPO_ROOT / "farit" / "docs" / "RESEARCH-STATE.md",
    "report": REPO_ROOT / "farit" / "docs" / "report-2026-10-23.md",
    "cost": REPO_ROOT / "farit" / "results" / "cost_accounting.md",
    "sprint": REPO_ROOT / "farit" / "SPRINT.md",
    "package": REPO_ROOT / "farit" / "PACKAGE.md",
}

# Absolute-language traps. Kept narrow to avoid false positives; each hit is a
# WARN that a human must resolve (either add evidence or reword).
OVERCLAIM_PATTERNS = [
    r"\bunaffected\b",
    r"\banswered by the data\b",
    r"\bproves?\b",
    r"\bproven\b",
    r"\bguarantee[sd]?\b",
    r"\bnever (?:is|are|was|were)\b",
    r"\bno (?:product-vs-ingredient|broken evidence)\b",
    r"\bclearly better\b",
    r"\bsolves the problem\b",
    r"\bentirely\b",
    r"\bdoes not improve\b",
    r"\bstill owed\b",
    r"\bremains owed\b",
]

SPLIT_FORBIDDEN = [
    r"unbiased final test",
    r"reserved for final audit only",
    r"\bfinal test\b",
    r"\bheld-?out test\b",
]
SPLIT_REQUIRED = [r"audit split", r"previously examined"]


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def load_artifacts() -> dict:
    s4 = json.loads(S4_ARTIFACT.read_text(encoding="utf-8"))
    s5 = json.loads(S5_ARTIFACT.read_text(encoding="utf-8"))
    cost = json.loads(COST_ARTIFACT.read_text(encoding="utf-8"))
    corpus = json.loads(CORPUS_STATS.read_text(encoding="utf-8"))

    gold = [json.loads(line) for line in GOLD_EVIDENCE.read_text(encoding="utf-8").splitlines() if line]
    dev = [r for r in gold if r.get("split") == "dev"]
    dev_noning = [r for r in dev if r.get("field") != "ingredients"]
    return {
        "s4": s4,
        "s5": s5,
        "cost": cost,
        "corpus": corpus,
        "gold_dev_records": len(dev),
        "gold_dev_noning": len(dev_noning),
        "gold_dev_included": sum(
            1 for r in dev_noning if r.get("evidence_set") and r.get("state") != "NOT_STATED"
        ),
    }


def s4_joint(a: dict, method: str, layer: str) -> float:
    return a["s4"]["methods"][f"{method}/{layer}"]["joint_all"] * 100


def build_claims(a: dict) -> list[dict]:
    """Return the ledger: each claim recomputed from raw artifacts.

    ``docs`` maps doc key -> regex with one capture group for the value the doc
    states. The regex is deliberately label-anchored so it cannot match a
    different row.
    """

    def claim(cid, docs, expect, source, scope, falsifier, unit="%"):
        return {
            "id": cid,
            "docs": docs,
            "expect": expect,
            "expect_str": f"{expect:.1f}" if unit == "%" else str(expect),
            "unit": unit,
            "source": source,
            "scope": scope,
            "falsifier": falsifier,
        }

    claims: list[dict] = []

    # --- S4 joint table (native / ocr) ---------------------------------------
    s4_rows = {
        "all-fields one-pass": "M1",
        "individual-field": "M2",
        "contextual citation verification": "M3",
        "rules-v4": "M4",
        "basic LLM verifier": "M5",
        "section-routed individual-field": "M6",
    }
    for label, method in s4_rows.items():
        native = s4_joint(a, method, "native")
        ocr = s4_joint(a, method, "ocr")
        claims.append(
            claim(
                f"S4.{method}.native",
                {
                    "state": rf"{label}[^\n|]*\|\s*\**\s*([\d.]+)%",
                    "report": rf"{label}[^\n|]*\|\s*\**\s*([\d.]+)%",
                },
                native,
                "s4_battery_goldv13.json",
                "dev, n=140, gold v1.3",
                "rerun evaluate_battery.py changes the joint rate",
            )
        )
        claims.append(
            claim(
                f"S4.{method}.ocr",
                {
                    "state": rf"{label}[^\n|]*\|[^\n|]*\|\s*\**\s*([\d.]+)%",
                    "report": rf"{label}[^\n|]*\|[^\n|]*\|\s*\**\s*([\d.]+)%",
                },
                ocr,
                "s4_battery_goldv13.json",
                "dev, n=140, gold v1.3",
                "rerun evaluate_battery.py changes the joint rate",
            )
        )

    # --- S5 taxonomy (per-document wording differs) ---------------------------
    tax = a["s5"]["summary"]["taxonomy_counts"]
    s5_patterns = {
        "evidence": {"state": r"evidence (\d+) /", "report": r"evidence \*\*(\d+)\*\*"},
        "reasoning": {"state": r"reasoning (\d+)", "report": r"reasoning(?:/derived)? \*\*(\d+)\*\*"},
        "values": {"state": r"values (\d+)", "report": r"wrong value \*\*(\d+)\*\*"},
        "entity attribution": {"state": r"entity attribution (\d+)", "report": r"entity attribution \*\*(\d+)\*\*"},
    }
    for cat, patterns in s5_patterns.items():
        claims.append(
            claim(
                f"S5.{cat}",
                patterns,
                tax.get(cat, 0),
                "s5_cases.json",
                "24 cases (18 hard + 6 control), gold v1.3",
                "resampling or reclassification changes the count",
                unit="n",
            )
        )
    claims.append(
        claim(
            "S5.unresolved",
            {"state": r"(\d+) of 24 cases", "report": r"(\d+) of 24 cases"},
            a["s5"]["summary"]["n_unresolved"],
            "s5_cases.json",
            "solved_by requires joint on both layers",
            "a simple method passing on both layers changes the count",
            unit="n",
        )
    )

    # --- cost -----------------------------------------------------------------
    s4_calls = sum(r["n_calls"] for r in a["cost"]["rows"] if r["family"] == "S4 extraction battery")
    claims.append(
        claim(
            "cost.s4_calls",
            {"state": r"(\d+)\s*calls", "report": r"(\d+) model calls"},
            s4_calls,
            "cost_accounting.json",
            "S4 battery, 12 cells",
            "a rerun with a different method set changes the call count",
            unit="n",
        )
    )

    # --- corpus (scope matters: corpus_stats is all 29 docs, not dev) ---------
    corpus = a["corpus"]
    claims.append(
        claim(
            "corpus.field_instances",
            {"state": r"(\d+) field instances"},
            corpus["field_instances"],
            "corpus_stats.json",
            "all 29 documents",
            "a corpus rebuild changes the instance count",
            unit="n",
        )
    )
    claims.append(
        claim(
            "corpus.fragments",
            {"state": r"(\d+) gold fragments"},
            corpus["total_fragments"],
            "corpus_stats.json",
            "all 29 documents (evidence + premise)",
            "a gold edit changes the fragment count",
            unit="n",
        )
    )
    claims.append(
        claim(
            "corpus.ge2_fragments",
            {"state": r"(\d+)/\d+ instances"},
            corpus["evidence_set_sizes"]["2"] + corpus["evidence_set_sizes"]["3+"],
            "corpus_stats.json (evidence_set_sizes)",
            "all 29 documents, instances needing >=2 fragments",
            "a gold edit changes the completeness distribution",
            unit="n",
        )
    )
    claims.append(
        claim(
            "corpus.ontology",
            {"state": r"(\d+) ONTOLOGY"},
            corpus["derivation_distribution"]["ONTOLOGY"],
            "corpus_stats.json",
            "all 29 documents, derived fields",
            "a gold edit changes the derivation mix",
            unit="n",
        )
    )
    claims.append(
        claim(
            "corpus.composition_implied",
            {"state": r"(\d+) COMPOSITION_IMPLIED"},
            corpus["derivation_distribution"]["COMPOSITION_IMPLIED"],
            "corpus_stats.json",
            "all 29 documents, derived fields",
            "a gold edit changes the derivation mix",
            unit="n",
        )
    )
    claims.append(
        claim(
            "corpus.dev_instances",
            {"report": r"n=(\d+) instances"},
            a["gold_dev_noning"],
            "gold_evidence.jsonl",
            "dev, non-ingredient (evaluator n)",
            "a gold edit changes the instance count",
            unit="n",
        )
    )
    claims.append(
        claim(
            "corpus.dev_included",
            {"state": r"(\d+) evidence-bearing"},
            a["gold_dev_included"],
            "gold_evidence.jsonl (judge inclusion rule)",
            "dev, non-ingredient, evidence_set present, state != NOT_STATED",
            "a gold or inclusion-rule edit changes the count",
            unit="n",
        )
    )

    m1n = (a["s4"]["cost"].get("M1/native", {}).get("info") or {})
    m1o = (a["s4"]["cost"].get("M1/ocr", {}).get("info") or {})
    if m1n:
        claims.append(claim("contract.m1_docs", {"state": r"on \*\*(\d+)/20 docs\*\*"},
                            m1n.get("documents_with_contract_violations", 0), "s4_battery_goldv13.json",
                            "M1 pass (both layers), canonical hub bf16", "a prompt/schema change alters it", unit="n"))
        claims.append(claim("contract.m1_native", {"state": r"\((\d+) native /"},
                            sum(m1n.get("contract_violations", {}).values()), "s4_battery_goldv13.json",
                            "M1 native violations", "same", unit="n"))
        claims.append(claim("contract.m1_ocr", {"state": r"native / (\d+) ocr"},
                            sum(m1o.get("contract_violations", {}).values()), "s4_battery_goldv13.json",
                            "M1 ocr violations", "same", unit="n"))

    hub_judge = [r for r in a["cost"]["rows"] if r["family"].startswith("retrieval LLM judge (Qwen3.5-2B")]
    if hub_judge:
        claims.append(
            claim(
                "cost.hub_judge_calls",
                {"cost": r"hub bf16\) \| (\d+)", "state": r"judge = \*\*(\d+) calls\*\*", "report": r"full run \((\d+) calls"},
                sum(r["n_calls"] for r in hub_judge),
                "cost_accounting.json",
                "hub 2B judge, both layers",
                "a judge rerun changes the call count",
                unit="n",
            )
        )
    return claims


def evaluate_claims(a: dict, doc_text: dict) -> list[dict]:
    claims = build_claims(a)
    results = []
    for c in claims:
        row = dict(c)
        row["status"] = "PASS"
        row["found"] = {}
        for doc_key, pattern in c["docs"].items():
            match = re.search(pattern, doc_text[doc_key])
            if not match:
                row["found"][doc_key] = None
                row["status"] = "MISSING"
                continue
            got = match.group(1)
            row["found"][doc_key] = got
            if got != c["expect_str"]:
                row["status"] = "MISMATCH"
        results.append(row)
    return results


def lint_overclaim(text: str) -> list[str]:
    hits = []
    for line in text.splitlines():
        for pat in OVERCLAIM_PATTERNS:
            if re.search(pat, line, flags=re.IGNORECASE):
                hits.append(line.strip())
                break
    return hits


def check_split_semantics(state_text: str, report_text: str) -> dict:
    combined = state_text + "\n" + report_text
    forbidden = [p for p in SPLIT_FORBIDDEN if re.search(p, combined, flags=re.IGNORECASE)]
    required = [p for p in SPLIT_REQUIRED if re.search(p, combined, flags=re.IGNORECASE)]
    return {
        "forbidden_hits": forbidden,
        "required_present": required,
        "ok": not forbidden,
    }


def check_derived_freshness(a: dict) -> list[str]:
    """Derived artifacts must be built from the same predictions as the battery.

    Catches the 2026-10-26 review finding: S5 was left on the old MLX predictions
    while the canonical battery moved to the hub bf16 run. We compare the per-cell
    call counts that both artifacts carry from the same ``*.meta.json`` files.
    """
    issues: list[str] = []
    s5_cost = a["s5"]["summary"].get("method_cost", {})
    for cell, meta in a["s4"].get("cost", {}).items():
        n_bat = (meta.get("cost") or {}).get("n_calls")
        n_s5 = ((s5_cost.get(cell) or {}).get("cost") or {}).get("n_calls")
        if n_bat is not None and n_s5 is not None and n_bat != n_s5:
            issues.append(f"S5/stale {cell}: n_calls {n_s5} != battery {n_bat}")
    return issues


def render_markdown(claims: list[dict], overclaim: dict, split: dict, derived: list[str]) -> str:
    lines = ["# Claims audit (pre-send gate)", ""]
    lines.append(f"- artifact-backed claims: **{len(claims)}**")
    n_fail = sum(1 for c in claims if c["status"] != "PASS")
    lines.append(f"- non-PASS: **{n_fail}**")
    lines.append(f"- split semantics ok: **{split['ok']}**")
    lines.append(f"- derived artifacts fresh: **{not derived}**")
    lines.append("")
    lines.append("## Ledger")
    lines.append("")
    lines.append("| claim | status | expected | found | source | scope |")
    lines.append("| --- | --- | ---: | --- | --- | --- |")
    for c in claims:
        found = ", ".join(f"{k}={v or '—'}" for k, v in c["found"].items())
        lines.append(
            f"| {c['id']} | {c['status']} | {c['expect_str']} | {found} | {c['source']} | {c['scope']} |"
        )
    lines.append("")
    lines.append("## Overclaim language (advisory — each line needs evidence or reword)")
    lines.append("")
    for key, hits in overclaim.items():
        if hits:
            lines.append(f"**{key}:**")
            for h in hits:
                lines.append(f"- {h}")
    if not any(overclaim.values()):
        lines.append("_none_")
    lines.append("")
    lines.append("## Split semantics")
    lines.append("")
    lines.append(f"- forbidden phrases present: {split['forbidden_hits'] or 'none'}")
    lines.append(f"- required phrases present: {split['required_present'] or 'none'}")
    lines.append("")
    lines.append("## Derived-artifact freshness")
    lines.append("")
    if derived:
        for d in derived:
            lines.append(f"- STALE: {d}")
    else:
        lines.append("_all derived artifacts match the canonical battery_")
    lines.append("")
    lines.append("## Falsifiers (what would break each claim)")
    lines.append("")
    for c in claims:
        lines.append(f"- **{c['id']}** — {c['falsifier']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="pre-send claims audit")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "farit" / "results" / "claims_audit")
    args = parser.parse_args()

    a = load_artifacts()
    doc_text = {key: path.read_text(encoding="utf-8") for key, path in DOCS.items()}

    claims = evaluate_claims(a, doc_text)
    overclaim = {key: lint_overclaim(text) for key, text in doc_text.items()}
    split = check_split_semantics(doc_text["state"], doc_text["report"])
    derived = check_derived_freshness(a)

    payload = {
        "claims": claims,
        "overclaim": overclaim,
        "split": split,
        "derived_issues": derived,
        "n_non_pass": sum(1 for c in claims if c["status"] != "PASS"),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.with_suffix(".json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    args.out.with_suffix(".md").write_text(render_markdown(claims, overclaim, split, derived), encoding="utf-8")

    print(f"claims: {len(claims)} | non-PASS: {payload['n_non_pass']} | split ok: {split['ok']} | derived fresh: {not derived}")
    for c in claims:
        if c["status"] != "PASS":
            print(f"  {c['status']:8} {c['id']}: expected {c['expect_str']}, found {c['found']}")
    for d in derived:
        print(f"  STALE    {d}")
    for key, hits in overclaim.items():
        if hits:
            print(f"  OVERCLAIM {key}: {len(hits)} line(s)")
    print(f"wrote {args.out.with_suffix('.json')} and {args.out.with_suffix('.md')}")
    return 1 if (payload["n_non_pass"] or not split["ok"] or derived) else 0


if __name__ == "__main__":
    sys.exit(main())