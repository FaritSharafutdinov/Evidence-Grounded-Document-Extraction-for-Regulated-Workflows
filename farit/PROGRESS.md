# Research Progress — Complete-Evidence Retrieval under Reading Budgets

**Farit Sharafutdinov · status report · October 9, 2026** (updated October 14 — LLM-judge baseline added, sections 5–7 revised)

Scope: first phase of topic scoping — verify that the problem (a) exists in our data, (b) is not solved by standard retrieval, (c) is not covered by recent literature. All results below are independently re-verified; all code and numbers are reproducible from this repo (see Reproducibility).

## 1. Research question

Given a limited reading budget (pages or tokens), retrieve the **complete** evidence set for each SDS field — all complementary premises — and know when the set is incomplete (abstain). This complements Maria's source-binding work; with the project now single-author, her framework is reused as infrastructure only.

## 2. Infrastructure audit (prerequisite)

- Environment rebuilt; all **68 regression tests pass**.
- Gold integrity verified independently: all 252 evidence/premise spans resolve to exact `textlayer` offsets; corpus control sums match (29 documents, 203 field instances).
- One latent dataset fact surfaced: `sds_30.pdf` exists in the manifest/OCR but is unannotated — excluded from all metrics, kept as a future distractor document.

## 3. Corpus built for the retrieval formulation

`farit/data/corpus/` (regenerable via `farit/src/retrieval/build_corpus.py`):

- Page-level units for both text layers: **339 pages × 2 layers** (native / OCR), median 292 tokens/page.
- Gold evidence sets per field instance, merging direct evidence and derivation premises: **252 fragments** (166 evidence + 86 premises).
- Completeness is frequent, not exotic: **70/203 instances (34%) need ≥2 fragments**; **26 are cross-page**; 48 fields are derived (premise-bearing).

## 4. Literature check (threat analysis)

Full analysis of all five recommended papers in `farit/results/threat_analysis.md`, numbers spot-checked against the PDFs:

- **ExtractBench** (Aug 2026): grounding is scored with **OR-acceptance** — one of N evidence readings suffices; completeness of the evidence set is not measured; cost is measured but never constrains reading; no abstention calibration.
- **SDS LLM Benchmark** (Apr 2026): value accuracy only, **no evidence annotations**, 10 documents, sections processed independently; calibration named only as future work.
- **LMDX** (ACL Findings 2024): extraction + localization, but one value per field, chunks processed independently — no cross-page premise fusion, no completeness, no budgets.
- **Learn then Test** (Angelopoulos et al.): not a threat but a **tool** — a distribution-free framework for calibrating an acceptance/abstention threshold with finite-sample risk control; we plan to reuse it for the stopping/abstention rule.
- **LayoutLMv3** (MM 2022): strong Document AI baseline methodology; token classification per page, no notion of evidence sets, completeness or abstention.
- Conclusion: evidence-set completeness under reading budgets, cross-page premise fusion, alternative derivations, and completeness-aware abstention are **open**.

## 5. Baseline experiments

Protocol: schema-driven queries (field name + ontology description only — no access to gold values), page-level retrieval, **dev split only** (locked split untouched, reserved for final audit), deterministic implementations, 125 evidence-bearing dev instances (140 dev field instances minus 15 with empty evidence sets; ingredients excluded).

**Headline (native layer, macro strict completeness — ALL gold evidence pages retrieved):**

| Method | complete@1 | complete@3 | complete@10 | piece-recall@3 (lenient) |
|---|---|---|---|---|
| Naive front-to-back | 0.464 | 0.696 | 0.992 | 0.736 |
| BM25 | 0.352 | 0.600 | 0.896 | 0.612 |
| Dense (MiniLM-L6) | 0.328 | 0.632 | 0.952 | 0.668 |
| LLM judge (Qwen2.5-7B, zero-shot) | **0.704** | **0.864** | **1.000** | **0.896** |

The LLM judge is a pointwise reranker: for every (document, field, page) it answers "does this page contain evidence for the field?", and the page score is P(Yes)/(P(Yes)+P(No)) from first-token logprobs. It is the only method that beats naive order, and its lead *grows* under tight token budgets (complete@1000tok: **0.880** vs 0.728 naive, 0.632 dense, 0.576 BM25).

**Hard slices, complete@3 (BM25 → Dense → LLM judge):** multi-evidence 0.40 → 0.52 → 0.79; cross-page 0.316 → 0.316 → 0.58 (the 0.316 → 0.316 step is not a typo: 6 of 19 instances for both retrievers); derived fields 0.22 → 0.56 → 0.75. Cross-page remains the hardest slice even for the LLM judge.

Verification notes: an initial piece-recall bug (pages counted against a fragment denominator) was caught by an invariant check (`piece_recall ≥ complete`) and fixed; `complete@k` values were unaffected. Determinism confirmed by bitwise-identical reruns for all methods (for the LLM judge: a warm-cache rerun; scoring is a pure forward pass, no sampling). BM25/naive figures in the dense and LLM reports are read from the frozen BM25 output, not recomputed.

**Score separation analysis (post-hoc, computed from the cached judge scores, native layer):**

- **As a ranker, the judge is strong**: per-instance AUROC mean = 0.87, median = 1.0; 68% of instances are ranked perfectly, only 7/125 rank worse than chance. The headline completeness numbers are not luck.
- **As a calibrated classifier, it is not**: 51% of *true* gold pages receive score < 0.5, and ~9% of non-gold pages score ≥ 0.5. Raw scores are not comparable across fields/documents — a fixed global threshold would discard half of the real evidence. Any abstention rule must be calibrated (e.g. via Learn then Test), not thresholded raw.
- **The split by field type is the sharpest result.** Median judge score on gold pages: **0.9998 for EXPLICIT fields vs 0.0000 for derived fields** (91% of derived gold pages score < 0.5). The judge confidently recognizes explicit evidence but does not *understand* that a page helps derive a field — its derived-field completeness (0.75@3) rests on ranking by tiny score margins between near-zero scores. Recognizing derivation-relevant evidence is a concrete, measurable gap, not a solved problem.

## 6. Findings

1. **The phenomenon is real and frequent** — a third of fields need multi-fragment evidence (data property, not a modeling artifact).
2. **Standard single-pass retrieval does not solve completeness** — lenient recall is consistently higher than strict completeness; finding *one* span is easy, finding *all* is not.
3. **The failure is structural, not lexical** — BM25 ≈ dense on the hard slices, and native ≈ OCR; per-page scoring has no notion of *coverage*, which is exactly what multi-premise and cross-page fields require.
4. **A trivial document prior beats both retrievers** — SDS templates concentrate evidence early, so naive reading sets the bar any proposed method must clear.
5. **Completeness is only interesting under budget** — naive@10 ≈ 0.99, i.e. "read everything" trivially solves completeness. The non-trivial problem is achieving completeness *cheaply* and *knowing when to stop / abstain* — which no existing benchmark measures. This sharpens the proposed contribution: budget-aware evidence gathering with a calibrated stopping rule.
6. **A strong zero-shot judge nearly saturates retrieval *quality* for explicit evidence** — LLM-judge complete@5 = 0.91, @10 = 1.00, with per-instance AUROC median 1.0. So "build a better retriever" is no longer a viable contribution on its own: an expensive ranker already solves the explicit case (at ~2,600 model calls for 125 fields). This *strengthens* the budget + abstention framing: the open problems are reaching LLM-judge-level completeness **cheaply** (few pages read, few model calls), **knowing when the evidence set is complete** — the raw scores are unusable for this without calibration — and **recognizing derivation-relevant evidence**, where even the judge is weak (median score 0.0 on derived gold pages).

## 7. Open questions for the topic decision

- **Does the budget constraint actually bite?** Partly answered: all methods saturate by page 5–10, so the interesting regime is the *tight* band (≤3 pages / ≤1000 tokens) — exactly where the LLM judge keeps a large lead (complete@1000tok 0.88 vs 0.58–0.73 for the rest) and where cheap methods fail. Next step: plot completeness-vs-budget curves for all four methods to locate the hard regime precisely.
- **Is 29 annotated sheets enough?** Sufficient for this pilot; whether to extend annotation is an open decision — it depends on which method direction we choose, so it should follow the topic decision, not precede it.
- **What is the contribution's shape?** The LLM-judge result rules out "better retrieval" as the core contribution. Remaining options: (i) measurement framework alone (corpus + completeness/budget metrics + failure analysis); (ii) a method for **cheap** budget-aware evidence gathering that approaches LLM-judge completeness at a fraction of its cost and **abstains** — declines a field and routes it to human review — when the evidence set is predicted incomplete (threshold calibrated via Learn then Test); (iii) both as one story. Option (ii)/(iii) look strongest given the data.

## Reproducibility

- Corpus: `python farit/src/retrieval/build_corpus.py` (writes `farit/data/corpus/`, validates offsets/counts)
- Baselines: `python farit/src/retrieval/bm25_baseline.py`, `python farit/src/retrieval/dense_baseline.py`, `python farit/src/retrieval/llm_reranker.py --model mlx-community/Qwen2.5-7B-Instruct-4bit --out-tag qwen7b` (~4.5 h on M2 16 GB; resumable score cache)
- Results: `farit/results/bm25_baseline.{md,json}`, `farit/results/dense_baseline.{md,json}`, `farit/results/llm_reranker_qwen7b.{md,json}`
- Python env: `~/ds_env` (3.11); pinned `pymupdf==1.28.2` preserved (gold boxes depend on its segmentation)
