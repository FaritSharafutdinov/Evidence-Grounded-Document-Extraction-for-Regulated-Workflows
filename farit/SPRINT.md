# SPRINT — week of 2026-10-19

Source: `steering/2026-10-22-note.md` (latest; sharpens `steering/2026-10-19-note.md` — same fork, new specifics). Rule of the week: **no new complex system** — reproduce, verify, simple baselines, real error cases, report.

## Priorities (in the supervisor's order)

- [x] **1. Reproduce results** — clean-room: fresh clone → corpus build → all baselines → numbers match frozen JSONs. (S1) — ✅ TASK-008; найден и починён баг `build_corpus.py` (sys.path), корпус байт-в-байт
- [x] **2. Evaluation audit** — sample gold annotations; check product-vs-ingredient labels, missing-value handling, alternative valid evidence; document what is correct/incorrect. (S2) — ✅ TASK-011 (K3-verified): 34/2/4, 0 broken-evidence-ref; эскалации-решения Farit'а pending (4 questionable + вне-выборочные sds_10/sds_17). **Нота 10-22 (S2b/S2c):** пересчёт затронутых ranking'ов — sds_03 (`molecular_weight` premise после фикса missed-evidence) закрыт в TASK-013/goldv11 (|Δ| ≤ 0.021); **product/component ownership (sds_18)** — ✅ TASK-016 (аудит) + TASK-017 (gold v1.3 фикс premise p5→p1, DEC-006)
- [x] **3. Zero-score investigation** — ✅ TASK-009: механизм = fp16 device-softmax (не fp32-exp), модель честна (27/27 greedy); оговорка про детерминизм на fp16-плече; дизайн-нота для Qwen3.5-2B: softmax в fp32 на host
- [x] **4. Strong simple baselines** — ✅ TASK-015 (Фаза A смоук + **Фаза B-local: полный dev**, gold v1.3). Joint native/ocr: M1 15.7/8.6, M2 19.3/11.4, M3 15.7/7.9, **M4 55.0/30.7**, M5 16.4/9.3 (`farit/results/s4_battery_goldv13.{json,md}`). Inherited Qwen2.5-7B — отдельной таблицей (3.6%, old gold). Хаб-реран — опционален.
- [x] **4b. sds_18 product/component ownership check** — ✅ TASK-016 (0 битых ссылок; исторический баг не воспроизводится; 3 policy-вопроса) → TASK-017 (gold v1.3: premise p5→p1, DEC-006)
- [x] **4c. Назвать сильнейшую нерешённую проблему** — ✅ черновик в отчёте §4: evidence-локализация (premise у derived + OCR bbox) + attribution; с «evidence against» обоих простых ответов. Финализация — после прочтения профом.
- [x] **5. ~24 real extraction cases** — ✅ TASK-018: 24 кейса (18 hard + 6 control), таксономия evidence 12 / reasoning 9 / values 2 / entity 1 / annotations 0, gap 12 (`farit/results/s5_cases.{json,md}`).
- [x] **6. Total cost accounting** — ✅ TASK-019: S4 688 вызовов/2.71M prompt/181 мин; inherited 7B judge 2606/4.5 ч; M4 = 0 (`farit/results/cost_accounting.{json,md}`).
- [x] **7. Week report** — ✅ черновик `farit/docs/report-2026-10-23.md` (на вычитку Farit'а перед отправкой).
- [ ] **8. Repo package to supervisor** — repo link + dev docs + annotations + prompts + raw results + configs. (S8)

## Explicit non-goals this week

- No new agentic architecture.
- No locked-split (sds_21–29) evaluation — stays untouched (S9).
- No work on the evidence-completeness *checker* as a product — the direction is under revision (see ROADMAP).
- Thinking-mode judge variant — deferred to backlog (DEC-004, п.4): bounded cost–quality experiment on derived-field instances, after S4 unblocks.

## Decisions (resolved 2026-10-19)

- ~~Which ~24 real extraction cases~~ → **mixed sample**: ~18 from hard slices (derived / cross-page / multi-evidence) + ~6 random controls.
- ~~Whole-document baseline: which model~~ → **Qwen3.5-2B on the GPU hub** (vLLM), after a local smoke; the LLM-judge baseline is re-run on the same model to keep tables apples-to-apples. See `decisions/DEC-003-model-switch.md`.

## Decisions (resolved 2026-10-23, Farit)

- ~~sds_19 premise-evidence warnings~~ → **утверждено** (рекомендация K3): `product_form` UNDETERMINED→MIXTURE, `substance_or_mixture` NOT_STATED→PRESENT/MIXTURE → **gold v1.2** (TASK-014, done ✅): `build_annotations` 3 варнинга→0; n_included 133→134; пересчёт BM25/dense `*_goldv12` (|Δ| ≤ 0.0069). Frozen v1.0 и `*_goldv11` сохранены.
- Sequencing: **gold v1.2** (✅ TASK-014) → **gold v1.3** (✅ TASK-017, ownership-фикс sds_18, DEC-006) → батарея бейзлайнов S4 на **финальном gold v1.3**.
