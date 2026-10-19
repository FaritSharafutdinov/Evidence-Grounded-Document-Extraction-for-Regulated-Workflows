# EXP-05 — LLM pointwise reranker (Qwen2.5-7B)

**Status:** done, verified (K3 + human review) · **Dates:** 2026-10-13/14
**Code:** `farit/src/retrieval/llm_reranker.py` · **Results:** `farit/results/llm_reranker_qwen7b.{json,md}`

## Why (hypothesis)

BM25 and dense retrieval lose to naive front-to-back reading and structurally fail on multi-evidence / cross-page / derived slices. Question: does a strong zero-shot LLM judge close the gap — i.e., is the remaining problem retrieval *quality* or something else?

## Method

Per (document, field, page): a Yes/No prompt ("does this page state, imply, or help derive the field's value?"), score = P(Yes)/(P(Yes)+P(No)) from first-token logprobs. Pages ranked by score; metrics identical to all baselines (imported from `bm25_baseline.py`). Resumable score cache; deterministic (pure forward pass, no sampling).

```mermaid
flowchart LR
    A[gold_evidence.jsonl<br/>125 dev instances] --> C
    B[units_native/ocr.jsonl<br/>339 pages/layer] --> C
    C[for each instance:<br/>score every page of its document] --> D[Qwen2.5-7B 4bit MLX<br/>P Yes / P Yes+P No]
    D --> E[(score cache<br/>2606 records)]
    E --> F[rank pages by score]
    F --> G[complete@k, piece-recall@k,<br/>token budgets, slices]
```

## Config

- Model: `mlx-community/Qwen2.5-7B-Instruct-4bit` (smoke: 0.5B), Mac M2 16 GB
- Dev split only, 125 included instances (same exclusions as BM25)
- Runtime: ~4.5 h full run; ~6.4 s/page

## Results (native; OCR within ~0.01)

complete@1/3/10 = **0.704 / 0.864 / 1.000** — first method to beat naive (0.464/0.696/0.992). Slices complete@3: multi 0.792, cross-page 0.579, derived 0.750.

## Nuances (what the headline hides)

- **Cost:** 2,606 model calls for 125 fields — not deployable as-is.
- **Uncalibrated scores:** 51% of true gold pages score < 0.5; raw thresholds unusable.
- **Mentions, not premises:** derived gold pages' median score = 0.0; 14/36 derived instances fully degenerate (all-zero → tie-break = document order → hidden naive prior, 0.786@3); genuine signal on the rest is only +0.06 over naive.

## Verification

- A5 invariant (piece_recall ≥ complete): 0 violations.
- Determinism: warm-cache rerun → bit-identical metrics.
- Score distribution sanity: min/max/mean reported in the md.
- ⚠️ Supervisor note 2026-10-19 (S3): the all-zero degeneration needs a deeper trace (prompt → logits → probability) before it is treated as understood.

## Decisions for Farit

- Judge model size (7B vs larger) — kept 7B for local feasibility.
- Pointwise Yes/No framing — chosen over listwise ranking for simplicity.
- These were made by the AI workflow; flag if you want them revisited.
