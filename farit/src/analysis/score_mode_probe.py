#!/usr/bin/env python3
"""Diagnostic probe (TASK-012): v1 vs v2 scoring on one (document, field) case.

For one case (native layer, dev split) prints per-page scores at full precision,
score statistics (min/max/mean/band), the count of exactly-0.0 scores, the rank
of the gold evidence pages, the chat-template tail, and the greedy first token
(argmax of last-position logits) for every page — the gold-page token is the T2
evidence.

CLI (run from repo root):
    ~/ds_env/bin/python farit/src/analysis/score_mode_probe.py \
        --model mlx-community/Qwen3.5-2B-MLX-4bit \
        --score-mode v2 --document sds_01.pdf --field product_name

Comparative run (TASK-012 design item 7): invoke four times — {v1,v2} x
{sds_01.pdf/product_name, sds_03.pdf/molecular_weight} — and compare the stats.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path.cwd()
sys.path.insert(0, str(REPO_ROOT / "farit" / "src" / "retrieval"))

import mlx.core as mx  # noqa: E402
import numpy as np  # noqa: E402

from llm_reranker import (  # noqa: E402
    GOLD_EVIDENCE,
    UNITS_NATIVE,
    apply_chat_template_v2,
    build_prompt,
    load_mlx_model,
    score_page_by_mode,
)


def load_pages(document: str) -> dict[int, str]:
    """Native-layer pages of one document from the corpus."""
    pages: dict[int, str] = {}
    with UNITS_NATIVE.open(encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            if u["document"] == document and u["layer"] == "native":
                pages[u["page"]] = u["text"]
    if not pages:
        raise SystemExit(f"No native pages for {document}")
    return pages


def check_dev_split(document: str) -> str:
    """Split of the document per gold_evidence.jsonl (probe is dev-only)."""
    with GOLD_EVIDENCE.open(encoding="utf-8") as f:
        for line in f:
            inst = json.loads(line)
            if inst["document"] == document:
                return inst["split"]
    raise SystemExit(f"{document} not found in gold_evidence.jsonl")


def load_gold_pages(document: str, field: str) -> list[int]:
    """Gold evidence page numbers of the (document, field) instance (dev only)."""
    with GOLD_EVIDENCE.open(encoding="utf-8") as f:
        for line in f:
            inst = json.loads(line)
            if inst["document"] == document and inst["field"] == field:
                if inst["split"] != "dev":
                    raise SystemExit(f"{document}/{field} is not dev split")
                return sorted({e["page"] for e in inst["evidence_set"]})
    raise SystemExit(f"{document}/{field} not found in gold_evidence.jsonl")


def chat_prompt_for(mode: str, tokenizer, prompt: str) -> str:
    """Chat prompt under the template of the scoring mode."""
    messages = [{"role": "user", "content": prompt}]
    if mode == "v2":
        return apply_chat_template_v2(tokenizer, messages)
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def greedy_first_token(model, tokenizer, chat_prompt: str) -> dict:
    """Argmax (greedy) first token of the last-position logits + top-3 tokens.

    The logits are cast to fp32 on device (lossless for bf16) before the
    host-side argmax — the same numerics domain as score mode v2.
    """
    tokens = tokenizer.encode(chat_prompt, add_special_tokens=False)
    logits = model(mx.array(tokens)[None])[0, -1, :]
    probs = np.asarray(logits.astype(mx.float32), dtype=np.float32)
    probs = np.exp(probs - probs.max())
    probs /= probs.sum()
    top = np.argsort(-probs)[:3]
    label = is_answer_variant(tokenizer.decode([int(np.argmax(probs))]))
    return {
        "text": tokenizer.decode([int(np.argmax(probs))]),
        "label": label,
        "top3": [(tokenizer.decode([int(i)]), float(probs[i])) for i in top],
    }


def is_answer_variant(text: str) -> str:
    """Classify a greedy token as a Yes/No-variant answer token."""
    t = text.strip()
    if t in ("Yes", "yes", "Y"):
        return "Yes"
    if t in ("No", "no", "N"):
        return "No"
    return f"NOT-ANSWER:{text!r}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Score-mode probe: one case, one mode")
    parser.add_argument("--model", required=True, help="MLX model id (mlx-community/...)")
    parser.add_argument("--score-mode", choices=["v1", "v2"], default="v1")
    parser.add_argument("--document", required=True, help="e.g. sds_01.pdf")
    parser.add_argument("--field", required=True, help="ontology field, e.g. product_name")
    args = parser.parse_args()
    doc, field, mode = args.document, args.field, args.score_mode

    split = check_dev_split(doc)
    if split != "dev":
        raise SystemExit(f"{doc} is locked/non-dev ({split}) — probe aborted (dev only)")
    gold_pages = load_gold_pages(doc, field)
    pages = load_pages(doc)
    print(f"MODEL={args.model} MODE={mode} CASE={doc}/{field} "
          f"pages={sorted(pages)} gold_pages={gold_pages} split={split}")

    t0 = time.time()
    model, tokenizer = load_mlx_model(args.model)
    print(f"model loaded in {time.time() - t0:.1f}s")

    # T2 evidence: template tail on the first page
    first_page = min(pages)
    tail = chat_prompt_for(mode, tokenizer, build_prompt(doc, field, first_page, pages[first_page]))
    print(f"  template tail ({mode}): {tail[-40:]!r}")

    rows = []
    for p in sorted(pages):
        prompt = build_prompt(doc, field, p, pages[p])
        t0 = time.perf_counter()
        score = score_page_by_mode(model, tokenizer, prompt, mode)
        dt = time.perf_counter() - t0
        greedy = greedy_first_token(model, tokenizer, chat_prompt_for(mode, tokenizer, prompt))
        rows.append({
            "page": p,
            "score": score,
            "greedy_first_token": greedy["text"],
            "greedy_label": greedy["label"],
            "greedy_top3": greedy["top3"],
            "gold": p in gold_pages,
            "score_sec": round(dt, 3),
        })
        print(f"  p{p:>2}: score={score!r} greedy={greedy['text']!r} "
              f"({greedy['label']}) gold={'Y' if p in gold_pages else ''} [{dt:.2f}s]")

    vals = [r["score"] for r in rows]
    order = sorted(rows, key=lambda r: r["score"], reverse=True)  # stable, as in reranker
    rank_by_page = {r["page"]: i for i, r in enumerate(order, start=1)}
    gold_ranks = [rank_by_page[p] for p in gold_pages]

    print(f"\n[stats] {doc}/{field} mode={mode}")
    print(f"  min={min(vals)!r} max={max(vals)!r}")
    print(f"  mean={sum(vals) / len(vals)!r}")
    print(f"  band={max(vals) - min(vals)!r}")
    print(f"  n_exact_zero={sum(1 for v in vals if v == 0.0)}")
    print(f"  gold_page_ranks={gold_ranks}  best_rank={min(gold_ranks)}")
    for r in rows:
        if r["gold"]:
            print(f"  gold p{r['page']}: greedy_first_token={r['greedy_first_token']!r} "
                  f"({r['greedy_label']})")
    print(f"[ranks] " + "  ".join(f"p{r['page']}:{rank_by_page[r['page']]}" for r in order))
    return 0


if __name__ == "__main__":
    sys.exit(main())
