# SPRINT — week of 2026-10-19

Source: `steering/2026-10-19-note.md`. Rule of the week: **no new complex system** — reproduce, verify, simple baselines, real error cases, report.

## Priorities (in the supervisor's order)

- [ ] **1. Reproduce results** — clean-room: fresh clone → corpus build → all baselines → numbers match frozen JSONs. (S1)
- [ ] **2. Evaluation audit** — sample gold annotations; check product-vs-ingredient labels, missing-value handling, alternative valid evidence; document what is correct/incorrect. (S2)
- [ ] **3. Zero-score investigation** — trace the full path prompt → logits → P(Yes)/(P(Yes)+P(No)) → cache → metrics for the degenerate cases; confirm the underflow explanation or find the real bug. (S3)
- [ ] **4. Strong simple baselines** — (a) whole-document reading; (b) all-fields-in-one-pass extraction; (c) citation verification with surrounding context. These are the bars any future method must clear. (S4)
- [ ] **5. ~24 real extraction cases** — end-to-end extraction (not retrieval) errors; per-case cause; build the error taxonomy. (S5)
- [ ] **6. Total cost accounting** — every model call counted (judge passes included), wall-clock + tokens, per method. (S6)
- [ ] **7. Week report** — which errors remain / why / which methods fix them. (S7)
- [ ] **8. Repo package to supervisor** — repo link + dev docs + annotations + prompts + raw results + configs. (S8)

## Explicit non-goals this week

- No new agentic architecture.
- No locked-split (sds_21–29) evaluation — stays untouched (S9).
- No work on the evidence-completeness *checker* as a product — the direction is under revision (see ROADMAP).

## Decisions (resolved 2026-10-19)

- ~~Which ~24 real extraction cases~~ → **mixed sample**: ~18 from hard slices (derived / cross-page / multi-evidence) + ~6 random controls.
- ~~Whole-document baseline: which model~~ → **Qwen3.5-2B on the GPU hub** (vLLM), after a local smoke; the LLM-judge baseline is re-run on the same model to keep tables apples-to-apples. See `decisions/DEC-003-model-switch.md`.
