#!/usr/bin/env python3
"""LLM pointwise reranker baseline for complete-evidence retrieval on dev split.

Uses mlx_lm for local inference on Apple Silicon.
Pointwise judge: for each (document, field, page) asks Yes/No question.
Score = P(Yes) / (P(Yes) + P(No)) from logprobs of first generated token.

CLI:
    python farit/src/retrieval/llm_reranker.py \
        --model mlx-community/Qwen2.5-0.5B-Instruct-4bit \
        --limit-docs 2 --out-tag smoke

Score modes (TASK-012, DEC-004):
    v1 (default, frozen): default chat template, device softmax via logprobs —
        byte-identical to the frozen Qwen2.5 baseline path.
    v2: non-thinking chat template (enable_thinking=False, TypeError fallback),
        host-side fp32 softmax of last-position logits; cache isolated to
        reranker_{model_tag}__v2.jsonl.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (repo root is cwd)
# ---------------------------------------------------------------------------
REPO_ROOT = Path.cwd()
CORPUS_DIR = REPO_ROOT / "farit" / "data" / "corpus"
RESULTS_DIR = REPO_ROOT / "farit" / "results"
CACHE_DIR = REPO_ROOT / "farit" / "data" / "llm_cache"
SRC_DIR = REPO_ROOT / "farit" / "src" / "retrieval"

UNITS_NATIVE = CORPUS_DIR / "units_native.jsonl"
UNITS_OCR = CORPUS_DIR / "units_ocr.jsonl"
GOLD_EVIDENCE = CORPUS_DIR / "gold_evidence.jsonl"
ONTOLOGY_PY = REPO_ROOT / "sdsbench" / "ontology.py"

# ---------------------------------------------------------------------------
# Import metrics from bm25_baseline (guarantees identical measurement)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(SRC_DIR))
from bm25_baseline import (
    QUERIES,
    aggregate,
    compute_instance_metrics,
    load_pages,
    slice_aggregate,
)

# ---------------------------------------------------------------------------
# Load ontology FIELD_SPECS
# ---------------------------------------------------------------------------

def load_field_specs() -> dict[str, dict]:
    code = ONTOLOGY_PY.read_text(encoding="utf-8")
    ns: dict = {}
    exec(compile(code, str(ONTOLOGY_PY), "exec"), ns)  # noqa: S102
    return ns["FIELD_SPECS"]


FIELD_SPECS = load_field_specs()

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE = """You are checking a Safety Data Sheet page for evidence about a specific field.

Field: {field_name} — {field_description}

Page {page_number} of {document}:
\"\"\"
{page_text}
\"\"\"

Does this page contain text that states, implies, or helps derive the field's
value? Answer Yes or No."""


def build_prompt(document: str, field_name: str, page_number: int, page_text: str) -> str:
    spec = FIELD_SPECS[field_name]
    return PROMPT_TEMPLATE.format(
        field_name=spec.name,
        field_description=spec.description,
        page_number=page_number,
        document=document,
        page_text=page_text,
    )


def prompt_sha256(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def load_cache(cache_path: Path) -> dict[tuple, float]:
    """Load cache as dict keyed by (document, field, page, layer, prompt_sha256)."""
    cache: dict[tuple, float] = {}
    if not cache_path.exists():
        return cache
    with cache_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                key = (
                    rec["document"],
                    rec["field"],
                    rec["page"],
                    rec["layer"],
                    rec["prompt_sha256"],
                )
                cache[key] = rec["score"]
            except (json.JSONDecodeError, KeyError):
                continue
    return cache


def append_cache(cache_path: Path, document: str, field: str, page: int, layer: str, psha: str, score: float) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    rec = {
        "document": document,
        "field": field,
        "page": page,
        "layer": layer,
        "prompt_sha256": psha,
        "score": score,
    }
    with cache_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# MLX model loading (isolated for fallback)
# ---------------------------------------------------------------------------

def load_mlx_model(model_name: str):
    from mlx_lm import load
    return load(model_name)


def score_page_mlx(model, tokenizer, prompt: str) -> float:
    """Return P(Yes) / (P(Yes) + P(No)) from logprobs of first generated token.

    Handles both "Yes" and " Yes" (with leading space) token variants.
    """
    from mlx_lm import generate

    # Build messages for chat model
    messages = [{"role": "user", "content": prompt}]
    chat_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    # Generate with logprobs — we need the first token's distribution
    # mlx_lm.generate returns text; we need to hook into generation for logprobs.
    # Use the lower-level API.
    import mlx.core as mx

    tokens = tokenizer.encode(chat_prompt, add_special_tokens=False)
    input_ids = mx.array(tokens)

    # Get logits for the next token
    logits = model(input_ids[None])
    next_token_logits = logits[0, -1, :]

    # Convert to probabilities
    log_probs = mx.log(mx.softmax(next_token_logits))

    # Find token ids for Yes/No variants
    yes_ids = []
    no_ids = []
    for text in ["Yes", " Yes", "yes", " yes"]:
        ids = tokenizer.encode(text, add_special_tokens=False)
        if len(ids) == 1:
            yes_ids.append(ids[0])
    for text in ["No", " No", "no", " no"]:
        ids = tokenizer.encode(text, add_special_tokens=False)
        if len(ids) == 1:
            no_ids.append(ids[0])

    # If no single-token variants found, fall back to first char
    if not yes_ids:
        ids = tokenizer.encode("Y", add_special_tokens=False)
        if len(ids) == 1:
            yes_ids.append(ids[0])
    if not no_ids:
        ids = tokenizer.encode("N", add_special_tokens=False)
        if len(ids) == 1:
            no_ids.append(ids[0])

    yes_logprob = max(float(log_probs[i]) for i in yes_ids) if yes_ids else -1e9
    no_logprob = max(float(log_probs[i]) for i in no_ids) if no_ids else -1e9

    # Convert log-probabilities (natural log) back to probabilities
    yes_prob = float(mx.exp(mx.array(yes_logprob)))
    no_prob = float(mx.exp(mx.array(no_logprob)))

    denom = yes_prob + no_prob
    if denom == 0:
        return 0.5
    return yes_prob / denom


# ---------------------------------------------------------------------------
# Score mode v2 (TASK-012, DEC-004): non-thinking template + host fp32 softmax
# ---------------------------------------------------------------------------

def _yes_no_token_ids(tokenizer) -> tuple[list[int], list[int]]:
    """Single-token ids for Yes/No variants — same table (and fallbacks) as v1.

    Used by the v2 path; v1 keeps its inline copy so the frozen path is untouched.
    """
    yes_ids = []
    no_ids = []
    for text in ["Yes", " Yes", "yes", " yes"]:
        ids = tokenizer.encode(text, add_special_tokens=False)
        if len(ids) == 1:
            yes_ids.append(ids[0])
    for text in ["No", " No", "no", " no"]:
        ids = tokenizer.encode(text, add_special_tokens=False)
        if len(ids) == 1:
            no_ids.append(ids[0])

    # If no single-token variants found, fall back to first char
    if not yes_ids:
        ids = tokenizer.encode("Y", add_special_tokens=False)
        if len(ids) == 1:
            yes_ids.append(ids[0])
    if not no_ids:
        ids = tokenizer.encode("N", add_special_tokens=False)
        if len(ids) == 1:
            no_ids.append(ids[0])
    return yes_ids, no_ids


def apply_chat_template_v2(tokenizer, messages: list[dict]) -> str:
    """v2 chat template: close the thinking channel; TypeError fallback.

    Models whose template has no thinking kwarg (e.g. Qwen2.5) fall back to the
    bare add_generation_prompt=True call, so the v2 path works for any model.
    """
    try:
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
    except TypeError:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def score_page_mlx_v2(model, tokenizer, prompt: str) -> float:
    """Score v2: P(Yes) / (P(Yes) + P(No)) under the non-thinking template.

    - Template: apply_chat_template(..., enable_thinking=False) (fallback: bare
      template without the kwarg for models without a thinking channel).
    - Softmax of the last-position logits is computed on host in fp32
      (numerically stable: minus max), so reduced device precision (bf16)
      cannot underflow small probabilities. The bf16 -> fp32 cast is exact
      (fp32 is a superset of bf16), then everything is host-side numpy.
    - P(Yes)/P(No): max probability over the same single-token variant table
      of Yes/No as v1.
    """
    import mlx.core as mx
    import numpy as np

    messages = [{"role": "user", "content": prompt}]
    chat_prompt = apply_chat_template_v2(tokenizer, messages)

    tokens = tokenizer.encode(chat_prompt, add_special_tokens=False)
    logits = model(mx.array(tokens)[None])
    # Exact cast to fp32 on device (lossless for bf16/fp16), host softmax in fp32.
    last_logits = np.asarray(logits[0, -1, :].astype(mx.float32), dtype=np.float32)
    probs = np.exp(last_logits - last_logits.max())
    probs /= probs.sum()

    yes_ids, no_ids = _yes_no_token_ids(tokenizer)
    yes_prob = max(float(probs[i]) for i in yes_ids) if yes_ids else 0.0
    no_prob = max(float(probs[i]) for i in no_ids) if no_ids else 0.0

    denom = yes_prob + no_prob
    if denom == 0:
        return 0.5
    return yes_prob / denom


def score_page_by_mode(model, tokenizer, prompt: str, score_mode: str) -> float:
    """Dispatch scoring by score mode: 'v1' (frozen) or 'v2'."""
    if score_mode == "v2":
        return score_page_mlx_v2(model, tokenizer, prompt)
    if score_mode == "v1":
        return score_page_mlx(model, tokenizer, prompt)
    raise ValueError(f"Unknown score mode: {score_mode}")


# ---------------------------------------------------------------------------
# vLLM / OpenAI-compatible scoring (GPU hub)
# ---------------------------------------------------------------------------

_YES_VARIANTS = ["Yes", " Yes", "yes", " yes", "Y", " Y"]
_NO_VARIANTS = ["No", " No", "no", " no", "N", " N"]


def score_page_openai(
    base_url: str,
    model: str,
    prompt: str,
    score_mode: str = "v2",
    api_key: str = "sk-noauth",
    top_logprobs: int = 20,
) -> float:
    """P(Yes)/(P(Yes)+P(No)) via the first-token logprobs of a vLLM server.

    Like v2, the chat template runs in non-thinking mode (``enable_thinking=False``)
    so the first generated token is the answer, not a thinking token (TASK-010).
    The Yes/No ratio is invariant to the softmax normaliser, so the top-k logprobs
    suffice as long as both tokens appear; a missing side is treated as -inf.
    """
    messages = [{"role": "user", "content": prompt}]
    body: dict = {
        "model": model,
        "messages": messages,
        "max_tokens": 1,
        "temperature": 0,
        "logprobs": True,
        "top_logprobs": top_logprobs,
    }
    if score_mode == "v2":
        body["chat_template_kwargs"] = {"enable_thinking": False}
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=900.0) as response:
        payload = json.loads(response.read().decode("utf-8"))

    choice = (payload.get("choices") or [{}])[0]
    content = ((choice.get("logprobs") or {}).get("content")) or []
    token_lp: dict[str, float] = {}
    if content:
        for item in content[0].get("top_logprobs") or []:
            token_lp[item.get("token", "")] = float(item.get("logprob", -1e9))

    def best(variants: list[str]) -> float:
        vals = [token_lp[t] for t in variants if t in token_lp]
        return max(vals) if vals else -1e9

    yes_lp = best(_YES_VARIANTS)
    no_lp = best(_NO_VARIANTS)
    if yes_lp <= -1e8 and no_lp <= -1e8:
        return 0.5
    yes_p = math.exp(yes_lp) if yes_lp > -1e8 else 0.0
    no_p = math.exp(no_lp) if no_lp > -1e8 else 0.0
    denom = yes_p + no_p
    return yes_p / denom if denom > 0 else 0.5


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_layer(
    layer_name: str,
    units_path: Path,
    model_name: str,
    limit_docs: int | None,
    cache_path: Path,
    score_mode: str = "v1",
    backend: str = "mlx",
    base_url: str | None = None,
) -> dict:
    pages = load_pages(units_path)
    pages = [p for p in pages if p["split"] == "dev"]

    # Group pages by document
    doc_pages: dict[str, list[dict]] = {}
    for p in pages:
        doc_pages.setdefault(p["document"], []).append(p)

    # Load gold evidence
    gold_instances = []
    with GOLD_EVIDENCE.open(encoding="utf-8") as f:
        for line in f:
            inst = json.loads(line)
            if inst["split"] != "dev":
                continue
            gold_instances.append(inst)

    # Same exclusions as BM25
    excluded_total = 0
    excluded_empty = 0
    excluded_ingredients = 0
    excluded_absent = 0
    included_instances = []

    for inst in gold_instances:
        if inst["field"] == "ingredients":
            excluded_ingredients += 1
            excluded_total += 1
            continue
        if not inst.get("evidence_set"):
            excluded_empty += 1
            excluded_total += 1
            continue
        if inst["state"] == "NOT_STATED":
            excluded_absent += 1
            excluded_total += 1
            continue
        included_instances.append(inst)

    # Limit documents for smoke test
    if limit_docs is not None:
        docs_with_included = sorted({inst["document"] for inst in included_instances})
        limited_docs = set(docs_with_included[:limit_docs])
        included_instances = [i for i in included_instances if i["document"] in limited_docs]

    # Load cache
    cache = load_cache(cache_path)
    cache_hits = 0
    cache_misses = 0

    # Load model (local mlx) or point at the hub server (openai)
    if backend == "openai":
        if not base_url:
            raise SystemExit("--backend openai requires --base-url")
        print(f"Using vLLM server {base_url} model {model_name} (score_mode={score_mode})")
        model = tokenizer = None
    else:
        print(f"Loading model {model_name} ...")
        model, tokenizer = load_mlx_model(model_name)
        print("Model loaded.")

    per_instance = []
    total_inference_time = 0.0
    n_inference_calls = 0

    for inst in included_instances:
        doc = inst["document"]
        field = inst["field"]
        gold_ev_set = inst["evidence_set"]
        n_evidence = inst["n_evidence"]
        cross_page = inst.get("cross_page", False)
        derivation = inst["derivation"]

        doc_ps = doc_pages.get(doc, [])
        if not doc_ps:
            page_tokens = {}
            ranked_llm = []
        else:
            page_scores = []
            for p in doc_ps:
                page_num = p["page"]
                page_text = p["text"]
                prompt = build_prompt(doc, field, page_num, page_text)
                psha = prompt_sha256(prompt)
                key = (doc, field, page_num, layer_name, psha)

                if key in cache:
                    score = cache[key]
                    cache_hits += 1
                else:
                    t0 = time.perf_counter()
                    if backend == "openai":
                        score = score_page_openai(base_url, model_name, prompt, score_mode)
                    else:
                        score = score_page_by_mode(model, tokenizer, prompt, score_mode)
                    t1 = time.perf_counter()
                    total_inference_time += (t1 - t0)
                    n_inference_calls += 1
                    cache[key] = score
                    append_cache(cache_path, doc, field, page_num, layer_name, psha, score)
                    cache_misses += 1

                page_scores.append((page_num, score))

            # Build page→score mapping BEFORE sorting
            page_score_map = {page: float(sc) for page, sc in page_scores}

            # Rank by descending score
            page_scores.sort(key=lambda x: x[1], reverse=True)
            ranked_llm = [p[0] for p in page_scores]
            page_tokens = {p["page"]: p.get("n_tokens", 0) for p in doc_ps}

        m_llm = compute_instance_metrics(ranked_llm, gold_ev_set, page_tokens)

        # A5: assert piece_recall >= complete
        for k in [1, 2, 3, 5, 10]:
            assert m_llm["piece_recall"][k] >= m_llm["complete"][k] - 1e-9, \
                f"A5 fail LLM {doc}/{field} @ {k}: piece_recall {m_llm['piece_recall'][k]} < complete {m_llm['complete'][k]}"
        for B in [500, 1000, 2000]:
            assert m_llm["token_piece_recall"][B] >= m_llm["token_complete"][B] - 1e-9, \
                f"A5 fail LLM {doc}/{field} @ {B}tok: piece_recall {m_llm['token_piece_recall'][B]} < complete {m_llm['token_complete'][B]}"

        per_instance.append({
            "document": doc,
            "field": field,
            "n_evidence": n_evidence,
            "cross_page": cross_page,
            "derivation": derivation,
            "llm": m_llm,
            "page_scores": page_score_map if doc_ps else {},
        })

    # Overall aggregate
    overall_llm = aggregate([{"metrics": i["llm"], "n_evidence": i["n_evidence"]} for i in per_instance])

    # Slices
    single_ev = slice_aggregate(
        [{"metrics": i["llm"], "n_evidence": i["n_evidence"]} for i in per_instance],
        lambda x: x["n_evidence"] == 1,
    )
    multi_ev = slice_aggregate(
        [{"metrics": i["llm"], "n_evidence": i["n_evidence"]} for i in per_instance],
        lambda x: x["n_evidence"] >= 2,
    )
    cross_true = slice_aggregate(
        [{"metrics": i["llm"], "n_evidence": i["n_evidence"]} for i in per_instance if i["cross_page"]],
        lambda x: True,
    )
    cross_false = slice_aggregate(
        [{"metrics": i["llm"], "n_evidence": i["n_evidence"]} for i in per_instance if not i["cross_page"]],
        lambda x: True,
    )
    explicit = slice_aggregate(
        [{"metrics": i["llm"], "n_evidence": i["n_evidence"]} for i in per_instance if i["derivation"] == "EXPLICIT"],
        lambda x: True,
    )
    derived = slice_aggregate(
        [{"metrics": i["llm"], "n_evidence": i["n_evidence"]} for i in per_instance if i["derivation"] != "EXPLICIT"],
        lambda x: True,
    )

    avg_time_per_page = total_inference_time / n_inference_calls if n_inference_calls > 0 else 0.0

    return {
        "layer": layer_name,
        "n_total_dev": len(gold_instances),
        "n_excluded": excluded_total,
        "n_excluded_empty": excluded_empty,
        "n_excluded_ingredients": excluded_ingredients,
        "n_excluded_absent": excluded_absent,
        "n_included": len(per_instance),
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "avg_time_per_page_sec": avg_time_per_page,
        "overall_llm": overall_llm,
        "slices_llm": {
            "single_evidence": single_ev,
            "multi_evidence": multi_ev,
            "cross_page_true": cross_true,
            "cross_page_false": cross_false,
            "explicit": explicit,
            "derived": derived,
        },
        "per_instance": per_instance,
    }


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def _get_val(d: dict, key) -> float:
    if key in d:
        return d[key]
    if str(key) in d:
        return d[str(key)]
    return 0.0


def format_table(data: dict, title: str) -> str:
    lines = [f"### {title}", ""]
    ks = [1, 2, 3, 5, 10]
    budgets = [500, 1000, 2000]

    header = "| Method | Metric | " + " | ".join(f"@{k}" for k in ks) + " | " + " | ".join(f"@{B}tok" for B in budgets) + " |"
    sep = "|" + "|".join(["---"] * (2 + len(ks) + len(budgets))) + "|"
    lines.append(header)
    lines.append(sep)

    agg = data.get("overall_llm", {})
    if agg:
        macro = agg.get("macro", {})

        row = ["LLM-judge", "macro complete"]
        for k in ks:
            row.append(f"{_get_val(macro.get('complete', {}), k):.3f}")
        for B in budgets:
            row.append(f"{_get_val(macro.get('token_complete', {}), B):.3f}")
        lines.append("| " + " | ".join(row) + " |")

        row = ["", "macro piece_recall"]
        for k in ks:
            row.append(f"{_get_val(macro.get('piece_recall', {}), k):.3f}")
        for B in budgets:
            row.append(f"{_get_val(macro.get('token_piece_recall', {}), B):.3f}")
        lines.append("| " + " | ".join(row) + " |")

        micro = agg.get("micro", {})
        row = ["", "micro piece_recall"]
        for k in ks:
            row.append(f"{_get_val(micro.get('piece_recall', {}), k):.3f}")
        for B in budgets:
            row.append(f"{_get_val(micro.get('token_piece_recall', {}), B):.3f}")
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    return "\n".join(lines)


def format_slices(data: dict, title: str) -> str:
    lines = [f"### {title}", ""]
    slices = data["slices_llm"]
    header = "| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |"
    sep = "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    lines.append(header)
    lines.append(sep)
    for name, agg in slices.items():
        if agg.get("n_instances", 0) == 0:
            continue
        n = agg["n_instances"]
        macro = agg["macro"]["complete"]
        tmacro = agg["macro"]["token_complete"]
        row = [
            name,
            str(n),
            f"{_get_val(macro, 1):.3f}",
            f"{_get_val(macro, 2):.3f}",
            f"{_get_val(macro, 3):.3f}",
            f"{_get_val(macro, 5):.3f}",
            f"{_get_val(macro, 10):.3f}",
            f"{_get_val(tmacro, 500):.3f}",
            f"{_get_val(tmacro, 1000):.3f}",
            f"{_get_val(tmacro, 2000):.3f}",
        ]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    return "\n".join(lines)


def format_comparison_table(llm_data: dict, bm25_data: dict, dense_data: dict, title: str) -> str:
    """Format comparison table: Naive, BM25, Dense, LLM-judge."""
    lines = [f"### {title}", ""]
    ks = [1, 2, 3, 5, 10]
    budgets = [500, 1000, 2000]

    header = "| Method | Metric | " + " | ".join(f"@{k}" for k in ks) + " | " + " | ".join(f"@{B}tok" for B in budgets) + " |"
    sep = "|" + "|".join(["---"] * (2 + len(ks) + len(budgets))) + "|"
    lines.append(header)
    lines.append(sep)

    methods = [
        ("naive", "Naive order", bm25_data),
        ("bm25", "BM25", bm25_data),
        ("dense", "Dense-MiniLM", dense_data),
        ("llm", "LLM-judge", llm_data),
    ]

    for method_key, label, data in methods:
        if method_key in ("naive", "bm25"):
            agg = data.get(f"overall_{method_key}", {})
        elif method_key == "dense":
            agg = data.get("overall_dense", {})
        else:  # llm
            agg = data.get("overall_llm", {})
        if not agg:
            continue
        macro = agg.get("macro", {})

        # Macro complete
        row = [label, "macro complete"]
        for k in ks:
            row.append(f"{_get_val(macro.get('complete', {}), k):.3f}")
        for B in budgets:
            row.append(f"{_get_val(macro.get('token_complete', {}), B):.3f}")
        lines.append("| " + " | ".join(row) + " |")

        # Macro piece_recall
        row = ["", "macro piece_recall"]
        for k in ks:
            row.append(f"{_get_val(macro.get('piece_recall', {}), k):.3f}")
        for B in budgets:
            row.append(f"{_get_val(macro.get('token_piece_recall', {}), B):.3f}")
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LLM pointwise reranker baseline")
    parser.add_argument(
        "--model",
        default="mlx-community/Qwen2.5-0.5B-Instruct-4bit",
        help="Model name/path for mlx_lm",
    )
    parser.add_argument(
        "--layer",
        choices=["native", "ocr", "both"],
        default="both",
        help="Which text layer to evaluate",
    )
    parser.add_argument(
        "--limit-docs",
        type=int,
        default=None,
        help="Limit to first N documents (for smoke test)",
    )
    parser.add_argument(
        "--out-tag",
        default="qwen7b",
        help="Tag for output files",
    )
    parser.add_argument(
        "--score-mode",
        choices=["v1", "v2"],
        default="v1",
        help=(
            "Scoring mode: v1 (frozen: default template, device softmax) or "
            "v2 (non-thinking template, host fp32 softmax). v2 uses its own "
            "cache file reranker_{model_tag}__v2.jsonl."
        ),
    )
    parser.add_argument(
        "--backend",
        choices=["mlx", "openai"],
        default="mlx",
        help="mlx (local Apple Silicon) or openai (vLLM hub /v1/chat/completions).",
    )
    parser.add_argument("--base-url", default=None, help="base URL for --backend openai")
    parser.add_argument("--api-key", default="sk-noauth", help="API key for --backend openai")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    model_tag = args.model.replace("/", "_")
    cache_mode_suffix = "" if args.score_mode == "v1" else "__v2"
    cache_path = CACHE_DIR / f"reranker_{model_tag}{cache_mode_suffix}.jsonl"

    out_json = RESULTS_DIR / f"llm_reranker_{args.out_tag}.json"
    out_md = RESULTS_DIR / f"llm_reranker_{args.out_tag}.md"

    # Load BM25 and Dense results for comparison (F3)
    bm25_results_path = RESULTS_DIR / "bm25_baseline.json"
    dense_results_path = RESULTS_DIR / "dense_baseline.json"
    bm25_results = {}
    dense_results = {}
    if bm25_results_path.exists():
        with bm25_results_path.open(encoding="utf-8") as f:
            bm25_results = json.load(f)
    if dense_results_path.exists():
        with dense_results_path.open(encoding="utf-8") as f:
            dense_results = json.load(f)

    layers = []
    if args.layer in ("native", "both"):
        layers.append(("native", UNITS_NATIVE))
    if args.layer in ("ocr", "both"):
        layers.append(("ocr", UNITS_OCR))

    results = {}
    for layer_name, units_path in layers:
        print(f"\n{'='*60}")
        print(f"Running layer: {layer_name}")
        print(f"{'='*60}")
        layer_result = run_layer(
            layer_name=layer_name,
            units_path=units_path,
            model_name=args.model,
            limit_docs=args.limit_docs,
            cache_path=cache_path,
            score_mode=args.score_mode,
            backend=args.backend,
            base_url=args.base_url,
        )
        results[layer_name] = layer_result
        print(f"Cache hits: {layer_result['cache_hits']}, misses: {layer_result['cache_misses']}")
        print(f"Avg time per page: {layer_result['avg_time_per_page_sec']:.3f}s")

    # Write JSON
    output = {
        "configuration": {
            "model": args.model,
            "backend": args.backend,
            "base_url": args.base_url,
            "layer": args.layer,
            "limit_docs": args.limit_docs,
            "score_mode": args.score_mode,
            "out_tag": args.out_tag,
        },
        **results,
    }
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, sort_keys=True)

    # Write Markdown
    md_lines = [
        f"# LLM Reranker Baseline Results (dev split only)",
        "",
        f"Model: `{args.model}`",
        f"Layer: `{args.layer}`",
        f"Score mode: `{args.score_mode}`",
        "",
    ]

    for layer_name in results:
        md_lines.append(f"## {layer_name.capitalize()} layer")
        md_lines.append("")
        # Comparison table (F3)
        bm25_layer = bm25_results.get(layer_name, {})
        dense_layer = dense_results.get(layer_name, {})
        md_lines.append(format_comparison_table(results[layer_name], bm25_layer, dense_layer, f"Comparison ({layer_name.capitalize()})"))
        md_lines.append(format_slices(results[layer_name], f"LLM-judge slice breakdown ({layer_name})"))

    # Score distribution sanity check
    md_lines.append("## Score distribution sanity")
    md_lines.append("")
    for layer_name in results:
        all_scores = []
        for inst in results[layer_name]["per_instance"]:
            all_scores.extend(inst["page_scores"].values())
        if all_scores:
            min_s = min(all_scores)
            max_s = max(all_scores)
            mean_s = sum(all_scores) / len(all_scores)
            n_sat = sum(1 for s in all_scores if s == 0.0 or s == 1.0)
            md_lines.append(f"- **{layer_name}**: n={len(all_scores)}, min={min_s:.4f}, max={max_s:.4f}, mean={mean_s:.4f}")
            if min_s < 0 or max_s > 1:
                md_lines.append(f"  ⚠️  Scores strictly outside [0,1] — extraction bug, investigate!")
            elif n_sat:
                md_lines.append(f"  ✓ Scores in [0,1]; {n_sat} exactly at 0.0/1.0 — float underflow of "
                                f"P(Yes)/(P(Yes)+P(No)) for extreme logprob gaps (expected saturation).")
            if max_s - min_s < 1e-6:
                md_lines.append(f"  ⚠️  All scores are identical — logprobs may not be extracted correctly!")
            else:
                md_lines.append(f"  ✓ Scores vary — logprobs extracted correctly.")
        else:
            md_lines.append(f"- **{layer_name}**: no scores")
    md_lines.append("")

    with out_md.open("w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\nResults written to {out_json} and {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
