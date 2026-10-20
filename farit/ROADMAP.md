# ROADMAP — long-term research plan

Owner: Farit Sharafutdinov. Updated after each supervisor meeting. Last update: 2026-10-19.

## Current topic hypothesis (2026-10-19, supervisor — hypothesis, not final)

**AI may find correct information but misunderstand what it belongs to, miss important context, or combine evidence incorrectly. Can we detect and repair such mistakes?**

- First application: chemical documents (SDS corpus — exists, annotated, verified).
- Generalization test (later): financial documents.
- Target contribution: genuinely new, generalizable, with strong comparisons and clear improvements in accuracy, evidence reliability, expert verification effort, and cost.

## Landscape after the scouting phase (verified results)

- Strict evidence completeness under reading budget: measured; naive prior beats BM25/dense; LLM judge (Qwen2.5-7B) saturates explicit evidence (complete@3 = 0.864) at ~2,600 model calls per 125 fields.
- Judge recognizes mentions, not premises (derived gold pages: median score 0.0; 14/36 degenerate all-zero → ranking = document order).
- Corpus: 29 annotated SDS (20 dev / 9 locked audit), 252 gold fragments, both text layers.

## Killed / deprioritized directions (and why)

| Direction | Status | Reason |
|---|---|---|
| Better retriever per se | killed (data) | LLM judge saturates explicit evidence; gap over naive on derived ≈ +0.06 |
| Evidence-completeness checker as the thesis | deprioritized (supervisor, 2026-10-19) | "not yet a strong new contribution; similar ideas exist" |
| Parser-invariant representations | killed (data) | native ≈ OCR everywhere measured |

## Milestones

1. **M1 — Trustworthy base (this week):** reproduced results, audited evaluation, zero-scores explained, simple baselines measured, ~24 real error cases with taxonomy, total cost accounting. → week report.
2. **M2 — Fork:** if simple methods solve the observed problems → find a deeper question. If important errors remain → formalize detection + repair of misinterpretation errors.
3. **M3 — Method + evaluation on SDS** (shape depends on M2).
4. **M4 — Generalization:** same problem class on financial documents.
5. **M5 — Thesis write-up.**

## Open risks

- 20 dev documents are thin for calibration — annotation-extension decision pending.
- Gold annotation quality itself is under audit this week (S2) — downstream numbers may shift.
