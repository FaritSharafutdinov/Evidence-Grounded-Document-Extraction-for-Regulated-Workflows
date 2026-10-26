#!/usr/bin/env python3
"""S6 — total cost accounting across every model-touching method (TASK-019).

Counts *every* model call (retrieval judges included), wall-clock and, where the
backend recorded them, prompt/completion tokens. Non-LLM methods (BM25, dense,
rules-v4/M4) are listed with zero model calls but their wall-clock is reported
where measured.

Sources (read-only):
  * farit/data/predictions/s4_M{1..5}_{native,ocr}.meta.json  — S4 battery usage
  * farit/results/llm_reranker_qwen7b.json                    — inherited 7B judge
  * farit/data/llm_cache/reranker_*.jsonl                     — judge call counts
  * farit/logs/TASK-015/run_battery_full_mlx.log              — run wall-clock

Writes farit/results/cost_accounting.{json,md}.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path.cwd()
PRED = ROOT / "farit" / "data" / "predictions"
CACHE = ROOT / "farit" / "data" / "llm_cache"
RESULTS = ROOT / "farit" / "results"
LOG = ROOT / "farit" / "logs" / "TASK-015" / "run_battery_full_mlx.log"

METHODS = {
    "M1": "all-fields one-pass (Qwen3.5-2B)",
    "M2": "individual-field (Qwen3.5-2B)",
    "M3": "contextual citation verification (Qwen3.5-2B)",
    "M4": "rules-v4 (non-LLM, inherited)",
    "M5": "basic LLM verifier (Qwen3.5-2B)",
}


def s4_rows() -> list[dict]:
    rows = []
    for m in METHODS:
        for layer in ("native", "ocr"):
            meta_path = PRED / f"s4_{m}_{layer}.meta.json"
            if not meta_path.exists():
                continue
            meta = json.load(open(meta_path))
            cost = meta["cost"]
            rows.append(
                {
                    "family": "S4 extraction battery",
                    "method": m,
                    "description": METHODS[m],
                    "layer": layer,
                    "backend": meta["backend"],
                    "model": meta["model"],
                    "n_calls": cost["n_calls"],
                    "prompt_tokens": cost["prompt_tokens"],
                    "completion_tokens": cost["completion_tokens"],
                    "wall_clock_s": cost["latency_s"],
                }
            )
    return rows


def judge_rows() -> list[dict]:
    rows = []
    j = json.load(open(RESULTS / "llm_reranker_qwen7b.json"))
    for layer in ("native", "ocr"):
        L = j[layer]
        calls = int(L.get("cache_misses", 0)) + int(L.get("cache_hits", 0))
        avg = float(L.get("avg_time_per_page_sec", 0.0))
        rows.append(
            {
                "family": "retrieval LLM judge (inherited, old gold)",
                "method": "judge",
                "description": "pointwise page judge (Qwen2.5-7B)",
                "layer": layer,
                "backend": "mlx",
                "model": j["configuration"]["model"],
                "n_calls": calls,
                "prompt_tokens": None,
                "completion_tokens": None,
                "wall_clock_s": round(calls * avg, 1),
                "note": f"avg {avg:.2f}s/page; tokens not recorded by the legacy runner",
            }
        )
    return rows


def judge_smoke_rows() -> list[dict]:
    rows = []
    for path, label, model in [
        (CACHE / "reranker_mlx-community_Qwen3.5-2B-MLX-4bit__v2.jsonl", "Qwen3.5-2B judge (v2 smoke)", "mlx-community/Qwen3.5-2B-MLX-4bit"),
        (CACHE / "reranker_mlx-community_Qwen2.5-0.5B-Instruct-4bit.jsonl", "Qwen2.5-0.5B judge (legacy smoke)", "mlx-community/Qwen2.5-0.5B-Instruct-4bit"),
    ]:
        if path.exists():
            n = sum(1 for _ in path.open())
            rows.append(
                {
                    "family": "judge smoke/probe (not a full run)",
                    "method": "judge-smoke",
                    "description": label,
                    "layer": "both",
                    "backend": "mlx",
                    "model": model,
                    "n_calls": n,
                    "prompt_tokens": None,
                    "completion_tokens": None,
                    "wall_clock_s": None,
                    "note": "smoke only; full Qwen3.5-2B judge run not performed",
                }
            )
    return rows


def hub_judge_rows() -> list[dict]:
    """The full Qwen3.5-2B pointwise judge, run on the hub (vLLM, bf16)."""
    path = RESULTS / "llm_reranker_hub_Qwen_Qwen3.5-2B_v2.json"
    if not path.exists():
        return []
    j = json.load(open(path))
    rows = []
    for layer in ("native", "ocr"):
        if layer not in j:
            continue
        L = j[layer]
        calls = int(L.get("cache_misses", 0)) + int(L.get("cache_hits", 0))
        avg = float(L.get("avg_time_per_page_sec", 0.0))
        rows.append(
            {
                "family": "retrieval LLM judge (Qwen3.5-2B, hub bf16)",
                "method": "judge",
                "description": "pointwise page judge (Qwen/Qwen3.5-2B, vLLM)",
                "layer": layer,
                "backend": "openai",
                "model": j.get("configuration", {}).get("model", "Qwen/Qwen3.5-2B"),
                "n_calls": calls,
                "prompt_tokens": None,
                "completion_tokens": None,
                "wall_clock_s": round(calls * avg, 1),
                "note": f"avg {avg:.3f}s/page; full run, tokens not recorded by the judge runner",
            }
        )
    return rows


def run_wall_clock() -> float | None:
    if not LOG.exists():
        return None
    times = []
    total = 0.0
    for line in LOG.read_text().splitlines():
        m = re.search(r"latency=([0-9.]+)s", line)
        if m:
            total += float(m.group(1))
    return round(total, 1) if total else None


def md(rows: list[dict], run_wc: float | None) -> str:
    lines = [
        "# S6 — total cost accounting",
        "",
        "Every model call counted (retrieval judges included). Gold v1.3, dev split. "
        "Tokens are reported where the backend recorded them; the legacy 7B judge runner "
        "did not record tokens, and its call count is taken from the cache.",
        "",
        "## Model-touching methods (per method × layer)",
        "",
        "| Family | Method | Layer | Backend | Model | n calls | prompt tok | completion tok | wall-clock s |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for r in rows:
        pt = r["prompt_tokens"] if r["prompt_tokens"] is not None else "n/a"
        ct = r["completion_tokens"] if r["completion_tokens"] is not None else "n/a"
        wc = r["wall_clock_s"] if r["wall_clock_s"] is not None else "n/a"
        lines.append(
            f"| {r['family']} | {r['method']} | {r['layer']} | {r['backend']} | "
            f"{r['model']} | {r['n_calls']} | {pt} | {ct} | {wc} |"
        )

    def agg(family: str) -> tuple[int, int, int, float]:
        sub = [r for r in rows if r["family"] == family]
        calls = sum(r["n_calls"] for r in sub)
        pt = sum(r["prompt_tokens"] or 0 for r in sub)
        ct = sum(r["completion_tokens"] or 0 for r in sub)
        wc = sum(r["wall_clock_s"] or 0.0 for r in sub)
        return calls, pt, ct, wc

    lines += ["", "## Totals by family", "", "| Family | n calls | prompt tok | completion tok | wall-clock s |", "| --- | ---: | ---: | ---: | ---: |"]
    for fam in dict.fromkeys(r["family"] for r in rows):
        c, pt, ct, wc = agg(fam)
        lines.append(f"| {fam} | {c} | {pt} | {ct} | {round(wc,1)} |")

    allc = sum(r["n_calls"] for r in rows)
    allpt = sum(r["prompt_tokens"] or 0 for r in rows)
    allct = sum(r["completion_tokens"] or 0 for r in rows)
    allwc = sum(r["wall_clock_s"] or 0.0 for r in rows)
    lines.append(f"| **ALL** | {allc} | {allpt} | {allct} | {round(allwc,1)} |")

    if run_wc is not None:
        lines += ["", f"S4 full battery run wall-clock (sum of per-set latencies in the runner log): **{run_wc:.1f}s ≈ {run_wc/60:.0f} min**."]
    lines += [
        "",
        "## Non-LLM methods (0 model calls)",
        "",
        "BM25, dense (MiniLM-L6) retrieval and rules-v4 (M4) issue **no** model calls; "
        "their cost is CPU wall-clock only and is not the bottleneck (M4 ran in the battery at 0 LLM calls).",
        "",
        "## Notes",
        "",
        "- M4 (rules-v4) is non-LLM: `n_calls = 0` by construction.",
        "- **S4 battery is the canonical hub bf16 config (`Qwen/Qwen3.5-2B`, vLLM, A100 MIG — DEC-007).** Wall-clock cells that reuse cache show `0.0` (cached calls are content-identical).",
        "- The inherited Qwen2.5-7B judge is the old-gold baseline — its 2606 calls (1303 native + 1303 ocr) were ~4.5 h on the M2 (local MLX; tokens not recorded by the legacy runner).",
        "- The Qwen3.5-2B judge is now a **full run** (hub, vLLM): 1349 pages/layer at ~0.11 s/page; its page rankings do not beat naive order on strict completeness (see `llm_reranker_hub_*.md`).",
        "- `wall_clock_s` for S4 is the sum of per-call latencies (model time); the runner-log total includes model load overhead.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    rows = s4_rows() + hub_judge_rows() + judge_rows() + judge_smoke_rows()
    run_wc = run_wall_clock()
    RESULTS.mkdir(parents=True, exist_ok=True)
    payload = {"rows": rows, "s4_run_wall_clock_s": run_wc}
    (RESULTS / "cost_accounting.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (RESULTS / "cost_accounting.md").write_text(md(rows, run_wc), encoding="utf-8")
    print(md(rows, run_wc))
    print("wrote farit/results/cost_accounting.{json,md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())