# Claims audit (pre-send gate)

- artifact-backed claims: **22**
- non-PASS: **1**
- split semantics ok: **False**

## Ledger

| claim | status | expected | found | source | scope |
| --- | --- | ---: | --- | --- | --- |
| S4.M1.native | PASS | 15.7 | state=15.7, report=15.7 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M1.ocr | PASS | 8.6 | state=8.6, report=8.6 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M2.native | PASS | 19.3 | state=19.3, report=19.3 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M2.ocr | PASS | 11.4 | state=11.4, report=11.4 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M3.native | PASS | 15.7 | state=15.7, report=15.7 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M3.ocr | PASS | 7.9 | state=7.9, report=7.9 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M4.native | PASS | 55.0 | state=55.0, report=55.0 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M4.ocr | PASS | 30.7 | state=30.7, report=30.7 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M5.native | PASS | 16.4 | state=16.4, report=16.4 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M5.ocr | PASS | 9.3 | state=9.3, report=9.3 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S5.evidence | PASS | 12 | state=12, report=12 | s5_cases.json | 24 cases (18 hard + 6 control), gold v1.3 |
| S5.reasoning | PASS | 9 | state=9, report=9 | s5_cases.json | 24 cases (18 hard + 6 control), gold v1.3 |
| S5.values | PASS | 2 | state=2, report=2 | s5_cases.json | 24 cases (18 hard + 6 control), gold v1.3 |
| S5.entity attribution | PASS | 1 | state=1, report=1 | s5_cases.json | 24 cases (18 hard + 6 control), gold v1.3 |
| S5.unresolved | PASS | 12 | state=12, report=12 | s5_cases.json | solved_by requires joint on both layers |
| cost.s4_calls | PASS | 688 | state=688, report=688 | cost_accounting.json | S4 battery, 10 cells |
| corpus.field_instances | PASS | 203 | state=203 | corpus_stats.json | all 29 documents |
| corpus.fragments | MISMATCH | 274 | state=278 | corpus_stats.json | all 29 documents (evidence + premise) |
| corpus.ontology | PASS | 51 | state=51 | corpus_stats.json | all 29 documents, derived fields |
| corpus.composition_implied | PASS | 4 | state=4 | corpus_stats.json | all 29 documents, derived fields |
| corpus.dev_instances | PASS | 140 | report=140 | gold_evidence.jsonl | dev, non-ingredient (evaluator n) |
| corpus.dev_included | PASS | 134 | state=134 | gold_evidence.jsonl (judge inclusion rule) | dev, non-ingredient, evidence_set present, state != NOT_STATED |

## Overclaim language (advisory — each line needs evidence or reword)

**RESEARCH-STATE:**
- 4. **M2 fork is now answered by the data**: simple baselines do **not** solve the problem — 12/24 S5 cases survive all simple methods. Candidate contribution: premise-aware, layout-robust grounding + calibrated abstention.
**report-2026-10-23:**
- - **Scoring issue fixed and rankings recomputed.** The low/zero judge scores were an arithmetic artifact: float16 device softmax flushed anything below ~6e-8 to exactly 0. The model itself is honest (27/27 greedy agreement on zero pages), and recomputing the same logits in fp32 confirms confident "No". Rankings and previously reported numbers are unaffected. Scoring v2 = non-thinking mode + fp32 host softmax + cache isolation (`TASK-012`, `DEC-004`).
- 3. No full Qwen3.5-2B *judge* run was made (the extraction battery replaced it); the sds_24 bbox float-noise on regeneration persists (metrics unaffected).

## Split semantics

- forbidden phrases present: ['reserved for final audit only']
- required phrases present: none

## Falsifiers (what would break each claim)

- **S4.M1.native** — rerun evaluate_battery.py changes the joint rate
- **S4.M1.ocr** — rerun evaluate_battery.py changes the joint rate
- **S4.M2.native** — rerun evaluate_battery.py changes the joint rate
- **S4.M2.ocr** — rerun evaluate_battery.py changes the joint rate
- **S4.M3.native** — rerun evaluate_battery.py changes the joint rate
- **S4.M3.ocr** — rerun evaluate_battery.py changes the joint rate
- **S4.M4.native** — rerun evaluate_battery.py changes the joint rate
- **S4.M4.ocr** — rerun evaluate_battery.py changes the joint rate
- **S4.M5.native** — rerun evaluate_battery.py changes the joint rate
- **S4.M5.ocr** — rerun evaluate_battery.py changes the joint rate
- **S5.evidence** — resampling or reclassification changes the count
- **S5.reasoning** — resampling or reclassification changes the count
- **S5.values** — resampling or reclassification changes the count
- **S5.entity attribution** — resampling or reclassification changes the count
- **S5.unresolved** — a simple method passing on both layers changes the count
- **cost.s4_calls** — a rerun with a different method set changes the call count
- **corpus.field_instances** — a corpus rebuild changes the instance count
- **corpus.fragments** — a gold edit changes the fragment count
- **corpus.ontology** — a gold edit changes the derivation mix
- **corpus.composition_implied** — a gold edit changes the derivation mix
- **corpus.dev_instances** — a gold edit changes the instance count
- **corpus.dev_included** — a gold or inclusion-rule edit changes the count
