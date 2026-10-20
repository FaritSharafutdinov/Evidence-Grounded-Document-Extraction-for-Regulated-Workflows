#!/usr/bin/env python3
"""TASK-009 (S3): zero-score trace diagnostics.

Investigates exact-0.0 reranker scores from farit/data/llm_cache/
reranker_mlx-community_Qwen2.5-7B-Instruct-4bit.jsonl.

Read-only with respect to the frozen baseline:
- farit/src/retrieval/llm_reranker.py is imported, never modified;
- the cache file is only read (load_cache), never appended.

Per traced (instance, page) this script prints/teaches a diagnostic line:
1. full prompt (after build_prompt) + sha256;
2. chat template after apply_chat_template;
3. top-10 tokens at the last position by logit: (token_string, logit, logprob32, logprob64);
4. resolved token ids for Yes/No variants (single-token or not);
5. yes_logprob / no_logprob (raw), exp -> probabilities -> score, float32 (frozen path) vs float64;
6. free generation: greedy generate 5 tokens from the same prompt;
7. float32 vs float64 comparison on the boundary values.

Traces are written to farit/logs/TASK-009/ and printed to stdout.

CLI:
    ~/ds_env/bin/python farit/src/analysis/zero_score_trace.py \
        --instance "sds_03.pdf:molecular_weight" \
        --model mlx-community/Qwen2.5-7B-Instruct-4bit \
        [--layer native] [--pages 1,2] [--q4]

Run from repository root.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path.cwd()
SRC_RETRIEVAL = REPO_ROOT / "farit" / "src" / "retrieval"
CORPUS_DIR = REPO_ROOT / "farit" / "data" / "corpus"
LOG_DIR = REPO_ROOT / "farit" / "logs" / "TASK-009"

sys.path.insert(0, str(SRC_RETRIEVAL))
from llm_reranker import (  # noqa: E402  # frozen module: imported, NOT modified
    CACHE_DIR,
    build_prompt,
    load_cache,
    load_mlx_model,
    prompt_sha256,
    score_page_mlx,
)

YES_VARIANTS = ["Yes", " Yes", "yes", " yes"]
NO_VARIANTS = ["No", " No", "no", " no"]

UNITS_PATHS = {
    "native": CORPUS_DIR / "units_native.jsonl",
    "ocr": CORPUS_DIR / "units_ocr.jsonl",
}


# ---------------------------------------------------------------------------
# Small IO helpers
# ---------------------------------------------------------------------------

class Tee:
    """Print to stdout and append to a log file."""

    def __init__(self, path: Path):
        self.path = path
        self.lines: list[str] = []

    def __call__(self, msg: str = ""):
        print(msg)
        self.lines.append(msg)

    def flush(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")


def load_page_texts(layer: str, document: str) -> dict[int, str]:
    units_path = UNITS_PATHS[layer]
    pages: dict[int, str] = {}
    with units_path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            u = json.loads(line)
            if u["document"] == document and u["split"] == "dev":
                pages[u["page"]] = u["text"]
    if not pages:
        raise RuntimeError(f"No dev pages for {document} in {units_path.name}")
    return pages


# ---------------------------------------------------------------------------
# Scoring trace (replicates frozen score_page_mlx exactly, adds diagnostics)
# ---------------------------------------------------------------------------

def resolve_yes_no_ids(tokenizer) -> tuple[list[int], list[int], list[str]]:
    """Identical variant resolution as frozen score_page_mlx, plus audit trail."""
    lines = []
    yes_ids: list[int] = []
    no_ids: list[int] = []

    def audit(variant: str):
        ids = tokenizer.encode(variant, add_special_tokens=False)
        tok_str = tokenizer.convert_ids_to_tokens(ids)
        lines.append(f"  {variant!r:8} -> ids={ids} single_token={len(ids) == 1} pieces={tok_str}")
        return ids

    for text in YES_VARIANTS:
        ids = audit(text)
        if len(ids) == 1:
            yes_ids.append(ids[0])
    for text in NO_VARIANTS:
        ids = audit(text)
        if len(ids) == 1:
            no_ids.append(ids[0])
    # Frozen fallbacks
    for text, bucket in [("Y", "yes"), ("N", "no")]:
        if (bucket == "yes" and not yes_ids) or (bucket == "no" and not no_ids):
            ids = audit(f"[fallback] {text}")
            if len(ids) == 1:
                (yes_ids if bucket == "yes" else no_ids).append(ids[0])
    return yes_ids, no_ids, lines


def trace_page(model, tokenizer, document: str, field: str, page_num: int,
               page_text: str, layer: str, cache: dict | None) -> dict:
    """Trace one (instance, page); returns summary dict."""
    log(f"\n{'=' * 80}")
    log(f"TRACING {document}:{field} page {page_num} layer {layer}")
    log(f"{'=' * 80}")

    # --- frozen prompt pipeline ------------------------------------------------
    prompt = build_prompt(document, field, page_num, page_text)
    psha = prompt_sha256(prompt)
    log("")
    log("[1] PROMPT (build_prompt) — full text, len=%d chars" % len(prompt))
    log(prompt)
    log(f"prompt_sha256 = {psha}")

    messages = [{"role": "user", "content": prompt}]
    chat_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    log("")
    log("[2] CHAT TEMPLATE (apply_chat_template, add_generation_prompt=True) — full text")
    log(repr(chat_prompt))
    if "<|im_start|>" in chat_prompt and "<|im_end|>" in chat_prompt:
        log("    -> template check: Qwen2.5 <|im_start|>/<|im_end|> markers present: OK")
    else:
        log("    -> template check: WARNING: Qwen2.5 im markers NOT found — inspect manually!")

    import mlx.core as mx
    from mlx_lm.generate import generate

    tokens = tokenizer.encode(chat_prompt, add_special_tokens=False)
    input_ids = mx.array(tokens)
    logits = model(input_ids[None])
    next_token_logits = logits[0, -1, :]

    # Frozen step: log_softmax in float32 (mx default dtype)
    log_probs32 = mx.log(mx.softmax(next_token_logits))

    # float64 recompute from the same logits tensor
    ntl64 = np.asarray(next_token_logits, dtype=np.float64)
    z64 = ntl64 - ntl64.max()
    p64 = np.exp(z64)
    p64 /= p64.sum()
    lp64 = np.log(p64)

    # --- [3] top-10 tokens by logit ------------------------------------------
    top_ids = np.argsort(-ntl64)[:10]
    log("")
    log("[3] TOP-10 tokens at last position (sorted by logit, desc)")
    log("    rank | token_id | logit         | logprob_float32   | logprob_float64     | token_string")
    for rank, tid in enumerate(top_ids.tolist(), 1):
        ts = tokenizer.convert_ids_to_tokens([tid])[0]
        dec = tokenizer.decode([tid])
        log(f"    {rank:>4} | {tid:>8} | {ntl64[tid]:>13.6f} | "
            f"{float(log_probs32[tid]):>17.6e} | {lp64[tid]:>19.6e} | {ts!r} (decode: {dec!r})")

    # --- [4] Yes/No token ids --------------------------------------------------
    log("")
    log("[4] YES/NO token-id resolution (frozen variant list + fallbacks)")
    yes_ids, no_ids, audit_lines = resolve_yes_no_ids(tokenizer)
    for l in audit_lines:
        log(l)
    log(f"    resolved yes_ids={yes_ids}  no_ids={no_ids}")

    # --- [5] logprobs -> exp -> score, float32 vs float64 ----------------------
    yes_lp32 = max(float(log_probs32[i]) for i in yes_ids) if yes_ids else -1e9
    no_lp32 = max(float(log_probs32[i]) for i in no_ids) if no_ids else -1e9
    yes_lp64 = max(float(lp64[i]) for i in yes_ids) if yes_ids else -1e9
    no_lp64 = max(float(lp64[i]) for i in no_ids) if no_ids else -1e9

    # Frozen path: mx.exp on float32
    yes_prob32 = float(mx.exp(mx.array(yes_lp32)))
    no_prob32 = float(mx.exp(mx.array(no_lp32)))
    denom32 = yes_prob32 + no_prob32
    score32 = 0.5 if denom32 == 0 else yes_prob32 / denom32

    # Frozen end-to-end (direct call of the frozen function, same prompt):
    frozen_score = score_page_mlx(model, tokenizer, prompt)

    # float64 path
    with np.errstate(under="ignore"):
        yes_prob64 = np.exp(yes_lp64)
        no_prob64 = np.exp(no_lp64)
    denom64 = yes_prob64 + no_prob64
    score64 = float("nan") if denom64 == 0 else float(yes_prob64 / denom64)

    gap64 = yes_lp64 - no_lp64  # ln(P(Yes)/P(No))
    ratio = math.exp(gap64) if -700 < gap64 < 700 else float("inf") if gap64 > 0 else 0.0

    log("")
    log("[5] SCORE PIPELINE")
    log(f"    yes_logprob (best single-token Yes; float32 log_softmax path) = {yes_lp32:.9e}")
    log(f"    no_logprob  (best single-token No;  float32 log_softmax path) = {no_lp32:.9e}")
    log(f"    yes_logprob / no_logprob recomputed in float64 from same logits = "
        f"{yes_lp64:.9e} / {no_lp64:.9e}")
    log(f"    ln(P(Yes)/P(No)) float64 = {gap64:.6f}  ->  P(Yes)/P(No) = {ratio:.6e}")
    log(f"    P(Yes)  float32 (mx.exp, frozen)  = {yes_prob32:.9e}")
    log(f"    P(No)   float32 (mx.exp, frozen)  = {no_prob32:.9e}")
    log(f"    score float32 (frozen math)       = {score32:.9f}")
    log(f"    frozen score_page_mlx() direct    = {frozen_score:.9f}   "
        f"({'== replica OK' if frozen_score == score32 else '!! MISMATCH with replica'})")
    log(f"    P(Yes)  float64 (np.exp)          = {yes_prob64:.9e}")
    log(f"    P(No)   float64 (np.exp)          = {no_prob64:.9e}")
    log(f"    score float64:                    = {score64:.9f}")
    log(f"    float32 vs float64 score equal:   {score32 == score64}")

    if cache is not None:
        key = (document, field, page_num, layer, psha)
        cached = cache.get(key)
        log(f"    cache score for this key          = {cached!r}   "
            f"({'== frozen ok' if cached is not None and cached == frozen_score else 'not in cache or differs'})")

    # --- [6] free generation (greedy, 5 tokens) --------------------------------
    gen_text = generate(model, tokenizer, prompt=chat_prompt, max_tokens=5, verbose=False)
    log("")
    log(f"[6] GREEDY GENERATION (max_tokens=5): {gen_text!r}")
    first = gen_text.strip()[:3].lower()
    gen_answer = "yes" if first.startswith("yes") else "no" if first.startswith("no") else f"other({gen_text!r})"
    log(f"    first-token answer: {gen_answer}")
    log(f"    consistency vs frozen score {frozen_score:.3f}: "
        f"{'AGREE (high Yes / Yes answer · low Yes / No answer)' if ((frozen_score >= 0.5) == (gen_answer == 'yes')) or (frozen_score == 0.0 and gen_answer == 'no') or (frozen_score == 1.0 and gen_answer == 'yes') else 'CHECK: generation disagrees with logprob score'}")

    return {
        "document": document, "field": field, "page": page_num, "layer": layer,
        "prompt_sha256": psha,
        "yes_ids": yes_ids, "no_ids": no_ids,
        "yes_logprob_f32": yes_lp32, "no_logprob_f32": no_lp32,
        "yes_logprob_f64": yes_lp64, "no_logprob_f64": no_lp64,
        "yes_prob_f32": yes_prob32, "no_prob_f32": no_prob32,
        "yes_prob_f64": yes_prob64, "no_prob_f64": no_prob64,
        "score_f32": score32, "score_f64": score64,
        "score_frozen": frozen_score,
        "ln_ratio_f64": gap64,
        "cache_score": None if cache is None else cache.get((document, field, page_num, layer, psha)),
        "greedy_generation": gen_text,
        "greedy_first_answer": gen_answer,
    }


# ---------------------------------------------------------------------------
# Q4: cache replay check
# ---------------------------------------------------------------------------

def q4_replay(model, tokenizer) -> list[dict]:
    """Recompute 3 cache records (zero / one / mid) with the same 7B model."""
    tag = "mlx-community_Qwen2.5-7B-Instruct-4bit"
    cache_path = CACHE_DIR / f"reranker_{tag}.jsonl"
    cache = load_cache(cache_path)
    recs = [json.loads(l) for l in cache_path.open(encoding="utf-8") if l.strip()]

    def pick(pred, label):
        for r in recs:
            if pred(r):
                print(f"Q4 selected ({label}): {r}")
                return r
        raise RuntimeError(f"Q4: no cache record matches {label}")

    r_zero = pick(lambda r: r["score"] == 0.0 and (r["document"], r["field"]) == ("sds_03.pdf", "molecular_weight") and r["layer"] == "native", "zero (degenerate case)")
    r_one = pick(lambda r: r["score"] == 1.0 and (r["document"], r["field"]) == ("sds_19.pdf", "product_name") and r["layer"] == "native", "one (control gold page)")
    r_mid = pick(lambda r: 0.0 < r["score"] < 1.0 and (r["document"], r["field"]) == ("sds_19.pdf", "product_name") and r["layer"] == "native", "mid (control non-extreme)")

    out = []
    for label, r in [("zero", r_zero), ("one", r_one), ("mid", r_mid)]:
        pages = load_page_texts(r["layer"], r["document"])
        page_text = pages[r["page"]]
        prompt = build_prompt(r["document"], r["field"], r["page"], page_text)
        psha = prompt_sha256(prompt)
        sha_ok = psha == r["prompt_sha256"]
        new_score = score_page_mlx(model, tokenizer, prompt)
        match = new_score == r["score"]
        print(f"\nQ4 replay {label}: {r['document']}:{r['field']} p{r['page']} ({r['layer']})")
        print(f"    prompt_sha256 rebuild == cached sha: {sha_ok}")
        print(f"    cached score = {r['score']:.12f}")
        print(f"    recomputed   = {new_score:.12f}")
        print(f"    EXACTLY EQUAL: {match}")
        out.append({"record": r, "sha_ok": sha_ok, "recomputed": new_score, "equal": match})
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TASK-009 zero-score trace diagnostics")
    p.add_argument("--instance", help='"<document>.pdf:<field>", e.g. "sds_03.pdf:molecular_weight"')
    p.add_argument("--model", default="mlx-community/Qwen2.5-0.5B-Instruct-4bit")
    p.add_argument("--layer", choices=["native", "ocr"], default="native")
    p.add_argument("--pages", help="comma-separated page numbers; default = all devel pages", default=None)
    p.add_argument("--q4", action="store_true", help="run Q4 cache-replay check (7B cache expected)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    model_tag = args.model.replace("/", "_")

    if args.q4:
        model, tokenizer = load_mlx_model(args.model)
        q4_replay(model, tokenizer)
        return 0

    if not args.instance:
        print("--instance is required unless --q4", file=sys.stderr)
        return 2

    document, _, field = args.instance.partition(":")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"trace_{model_tag}_{document.replace('.pdf', '')}_{field}_{args.layer}.log"
    global log
    log = Tee(log_path)

    cache_path = CACHE_DIR / f"reranker_{model_tag}.jsonl"
    cache = load_cache(cache_path) if cache_path.exists() else None
    if cache is None:
        log(f"(note: no cache file at {cache_path} — cache column will be empty)")

    pages = load_page_texts(args.layer, document)
    if args.pages:
        wanted = {int(x) for x in args.pages.split(",")}
        pages = {p: t for p, t in pages.items() if p in wanted}
        if not pages:
            print(f"Pages {args.pages} not found for {document}", file=sys.stderr)
            return 2

    print(f"Loading model {args.model} ...")
    model, tokenizer = load_mlx_model(args.model)
    print("Model loaded.")
    log(f"# TASK-009 zero-score trace")
    log(f"# instance: {args.instance}  layer: {args.layer}  pages: {sorted(pages)}")
    log(f"# model: {args.model}")

    results = [trace_page(model, tokenizer, document, field, p, t, args.layer, cache)
               for p, t in sorted(pages.items())]

    # Per-case summary
    log("")
    log(f"{'=' * 80}")
    log(f"SUMMARY {document}:{field} layer={args.layer} pages={sorted(pages)}")
    log(f"{'=' * 80}")
    log("page | score_f32(frozen) | yes_lp64        | no_lp64         | score_f64      | greedy | cache")
    for r in results:
        log(f"{r['page']:>4} | {r['score_f32']:.6f}          | {r['yes_logprob_f64']:>12.6e} | "
            f"{r['no_logprob_f64']:>12.6e} | {r['score_f64']:.6f} | {r['greedy_first_answer']:>6} | {r['cache_score']!r}")
    log.flush()
    print(f"\nLog written to {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
