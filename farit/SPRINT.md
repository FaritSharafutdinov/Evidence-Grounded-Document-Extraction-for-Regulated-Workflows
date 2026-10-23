# SPRINT — week of 2026-10-19

Source: `steering/2026-10-22-note.md` (latest; sharpens `steering/2026-10-19-note.md` — same fork, new specifics). Rule of the week: **no new complex system** — reproduce, verify, simple baselines, real error cases, report.

## Priorities (in the supervisor's order)

- [x] **1. Reproduce results** — clean-room: fresh clone → corpus build → all baselines → numbers match frozen JSONs. (S1) — ✅ TASK-008; найден и починён баг `build_corpus.py` (sys.path), корпус байт-в-байт
- [x] **2. Evaluation audit** — sample gold annotations; check product-vs-ingredient labels, missing-value handling, alternative valid evidence; document what is correct/incorrect. (S2) — ✅ TASK-011 (K3-verified): 34/2/4, 0 broken-evidence-ref; эскалации-решения Farit'а pending (4 questionable + вне-выборочные sds_10/sds_17). **Нота 10-22 (S2b/S2c):** пересчёт затронутых ranking'ов — sds_03 (`molecular_weight` premise после фикса missed-evidence) закрыт в TASK-013/goldv11 (|Δ| ≤ 0.021); **product/component ownership (sds_18) ещё НЕ проверен** — отдельный пункт ниже
- [x] **3. Zero-score investigation** — ✅ TASK-009: механизм = fp16 device-softmax (не fp32-exp), модель честна (27/27 greedy); оговорка про детерминизм на fp16-плече; дизайн-нота для Qwen3.5-2B: softmax в fp32 на host
- [ ] **4. Strong simple baselines** — (нота 10-22: **шесть** методов на одной конфигурации Qwen3.5-2B) (a) whole-document reading; (b) all-fields-in-one-pass extraction; (c) individual-field extraction; (d) citation verification with surrounding context; (e) simple entity/section rules; (f) basic LLM verifier. These are the bars any future method must clear. Inherited Qwen2.5-7B результаты — **отдельной таблицей, не смешивать** (S3). — разблокировано: TASK-012 done ✅ (scoring v2: non-thinking + fp32-host softmax, кэш-изоляция; K3-verified). Рабочий gold — v1.1 (TASK-013), после утверждения Farit'ом sds_19 → v1.2
- [ ] **4b. sds_18 product/component ownership check** — проф. явно просил (нота 10-22, S2c); ещё не сделан
- [ ] **4c. Назвать сильнейшую нерешённую проблему** — какие ошибки выживают после бейзлайнов, почему существующие подходы не справляются, кандидат-механизм + **evidence against** нашего объяснения (нота 10-22, S5)
- [ ] **5. ~24 real extraction cases** — end-to-end extraction (not retrieval) errors; per-case cause; build the error taxonomy. (S5)
- [ ] **6. Total cost accounting** — every model call counted (judge passes included), wall-clock + tokens, per method. (S6)
- [ ] **7. Week report** — which errors remain / why / which methods fix them. (S7)
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

- ~~sds_19 premise-evidence warnings~~ → **утверждено** (рекомендация K3): `product_form` UNDETERMINED→MIXTURE, `substance_or_mixture` NOT_STATED→PRESENT/MIXTURE → **gold v1.2** (малая правка + пересборка корпуса; бейзлайны на v1.2 пересчитываются; frozen-выходы v1.0/v1.1 сохраняются).
- Sequencing: **gold v1.2 до батареи бейзлайнов S4**, чтобы S4 считался на финальном gold.
