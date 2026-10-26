# External review — Argon (Gemini 4) teardown, 2026-10-26

- **Source & date:** Gemini 4 Argon (web, manual paste), 2026-10-26. Reviewed artifact: `farit/docs/RESEARCH-STATE.md` + steering notes 10-19/10-22 + the 10-21 short report.
- **Why filed (convention):** this teardown drove DEC-007; the critic flagged that the "review → decision" chain was not recorded (finding N11).

## Verbatim (key points)

1. **Substitution of the note's orders.** (1.1) The fp16 scoring fix required *recomputing affected rankings* (esp. `sds_03:molecular_weight`); we marked S2b done via a gold fix + BM25/dense recompute, but the LLM-judge rankings were not re-derived. (1.2) The note asked for **six** baselines on one 2B config; the battery had five, and slot 5 used Maria's `rules-v4` (non-LLM) instead of *simple entity/section rules*. (1.3) Missing an explicit "evidence against your proposed explanation".
2. **The S5 paradox:** in the residue, `entity attribution = 0`; misattribution is rare → *evidence against* the "misattributes what it belongs to" framing; the residue is localization (+ possibly dataset-convention).
3. **Split semantics:** `sds_21–29` are an **audit split** (previously examined), not an unbiased test (`PROJECT_GUIDE.md` §2.4) — contradicts our "reserved for final audit only".
4. **Transparency vs the 10-21 letter:** "gold mostly reliable / rankings unaffected" later contradicted by gold v1.2/v1.3 and shifted metrics; say so explicitly.
- Checklist: (1) recompute the fp16-affected rankings; (2) honour the 6-method list; (3) write the evidence-against; (4) clean internal contradictions (`native ≈ OCR`; 125 vs 134).

## Our point-by-point response (2026-10-26)

| # | Verdict | Action |
|---|---|---|
| 1.1 | accept | Split semantics fixed; the **judge ranking recompute is still owed** — disclosed, not hidden (report §1 says "recompute owed"; RS points to it). Re-run deferred by Farit's call (fix-in-words, no overclaim). |
| 1.2 | accept | **M6 implemented** (TASK-021): section-routed individual-field = the "simple entity/section rules on the 2B config" slot. |
| 1.3 | accept | Explicit evidence-against added (entity bucket empty; residue decomposed; "second passes move the error"). |
| 2 | accept | Per-category residue decomposed (2 gold.ambiguous + 1 dispute → ~2–3 system-side); entity claim scoped to n=1. |
| 3 | accept | `RESEARCH-STATE`/report now say **audit split / previously examined / not usable as an unbiased test**; new-document need stated. |
| 4 | accept | Report reconciles with the 10-21 letter (gold v1.1→v1.3 changes; metrics shifted). |
| checklist 4 | accept | `native ≈ OCR` claim reworded; instance counts synced (274 fragments; 71/203; dev 140/134). |

## Outcome

- **DEC-007** (canonical = hub bf16) + `farit/logs/TASK-020/` provenance.
- **TASK-021 / M6** implemented.
- Split semantics, overclaim and residue decomposition corrected; `claims_audit` gate + pre-send rule added (`farit/AGENTS.md`).
- Still owed (disclosed): re-score the 7B judge on v2 + gold v1.3 before any 2B-vs-7B claim.