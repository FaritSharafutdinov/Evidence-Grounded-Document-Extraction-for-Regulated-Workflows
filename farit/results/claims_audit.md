# Claims audit (pre-send gate)

- artifact-backed claims: **29**
- non-PASS: **0**
- split semantics ok: **True**
- derived artifacts fresh: **True**

## Ledger

| claim | status | expected | found | source | scope |
| --- | --- | ---: | --- | --- | --- |
| S4.M1.native | PASS | 18.6 | state=18.6, report=18.6 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M1.ocr | PASS | 11.4 | state=11.4, report=11.4 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M2.native | PASS | 21.4 | state=21.4, report=21.4 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M2.ocr | PASS | 9.3 | state=9.3, report=9.3 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M3.native | PASS | 18.6 | state=18.6, report=18.6 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M3.ocr | PASS | 12.1 | state=12.1, report=12.1 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M4.native | PASS | 55.0 | state=55.0, report=55.0 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M4.ocr | PASS | 30.7 | state=30.7, report=30.7 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M5.native | PASS | 20.7 | state=20.7, report=20.7 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M5.ocr | PASS | 15.7 | state=15.7, report=15.7 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M6.native | PASS | 17.9 | state=17.9, report=17.9 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S4.M6.ocr | PASS | 8.6 | state=8.6, report=8.6 | s4_battery_goldv13.json | dev, n=140, gold v1.3 |
| S5.evidence | PASS | 14 | state=14, report=14 | s5_cases.json | 24 cases (18 hard + 6 control), gold v1.3 |
| S5.reasoning | PASS | 9 | state=9, report=9 | s5_cases.json | 24 cases (18 hard + 6 control), gold v1.3 |
| S5.values | PASS | 1 | state=1, report=1 | s5_cases.json | 24 cases (18 hard + 6 control), gold v1.3 |
| S5.entity attribution | PASS | 0 | state=0, report=0 | s5_cases.json | 24 cases (18 hard + 6 control), gold v1.3 |
| S5.unresolved | PASS | 12 | state=12, report=12 | s5_cases.json | solved_by requires joint on both layers |
| cost.s4_calls | PASS | 1236 | state=1236, report=1236 | cost_accounting.json | S4 battery, 12 cells |
| corpus.field_instances | PASS | 203 | state=203 | corpus_stats.json | all 29 documents |
| corpus.fragments | PASS | 274 | state=274 | corpus_stats.json | all 29 documents (evidence + premise) |
| corpus.ge2_fragments | PASS | 71 | state=71 | corpus_stats.json (evidence_set_sizes) | all 29 documents, instances needing >=2 fragments |
| corpus.ontology | PASS | 51 | state=51 | corpus_stats.json | all 29 documents, derived fields |
| corpus.composition_implied | PASS | 4 | state=4 | corpus_stats.json | all 29 documents, derived fields |
| corpus.dev_instances | PASS | 140 | report=140 | gold_evidence.jsonl | dev, non-ingredient (evaluator n) |
| corpus.dev_included | PASS | 134 | state=134 | gold_evidence.jsonl (judge inclusion rule) | dev, non-ingredient, evidence_set present, state != NOT_STATED |
| contract.m1_docs | PASS | 17 | state=17 | s4_battery_goldv13.json | M1 pass (both layers), canonical hub bf16 |
| contract.m1_native | PASS | 87 | state=87 | s4_battery_goldv13.json | M1 native violations |
| contract.m1_ocr | PASS | 86 | state=86 | s4_battery_goldv13.json | M1 ocr violations |
| cost.hub_judge_calls | PASS | 2698 | cost=2698 | cost_accounting.json | hub 2B judge, both layers |

## Overclaim language (advisory — each line needs evidence or reword)

_none_

## Split semantics

- forbidden phrases present: none
- required phrases present: ['audit split', 'previously examined']

## Derived-artifact freshness

_all derived artifacts match the canonical battery_

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
- **S4.M6.native** — rerun evaluate_battery.py changes the joint rate
- **S4.M6.ocr** — rerun evaluate_battery.py changes the joint rate
- **S5.evidence** — resampling or reclassification changes the count
- **S5.reasoning** — resampling or reclassification changes the count
- **S5.values** — resampling or reclassification changes the count
- **S5.entity attribution** — resampling or reclassification changes the count
- **S5.unresolved** — a simple method passing on both layers changes the count
- **cost.s4_calls** — a rerun with a different method set changes the call count
- **corpus.field_instances** — a corpus rebuild changes the instance count
- **corpus.fragments** — a gold edit changes the fragment count
- **corpus.ge2_fragments** — a gold edit changes the completeness distribution
- **corpus.ontology** — a gold edit changes the derivation mix
- **corpus.composition_implied** — a gold edit changes the derivation mix
- **corpus.dev_instances** — a gold edit changes the instance count
- **corpus.dev_included** — a gold or inclusion-rule edit changes the count
- **contract.m1_docs** — a prompt/schema change alters it
- **contract.m1_native** — same
- **contract.m1_ocr** — same
- **cost.hub_judge_calls** — a judge rerun changes the call count
