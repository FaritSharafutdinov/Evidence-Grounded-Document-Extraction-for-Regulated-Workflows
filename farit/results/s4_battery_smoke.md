# S4 baseline battery — smoke run

Five simple extraction methods on one model, scored against gold v1.2 (dev split). M3 and M5 depend on the M1 pass; M4 is the inherited rules-v4 re-scored against v1.2 with zero LLM calls.

## Joint score (7-axis conjunction) by method × layer

| Method | Layer | n inst | 7-axis joint | joint (evidence-bearing) |
| --- | --- | ---: | ---: | ---: |
| M1 | native | 7 | 42.9% | 42.9% |
| M1 | ocr | 7 | 28.6% | 28.6% |
| M2 | native | 7 | 14.3% | 14.3% |
| M2 | ocr | 7 | 28.6% | 28.6% |
| M3 | native | 7 | 42.9% | 42.9% |
| M3 | ocr | 7 | 28.6% | 28.6% |
| M4 | native | 7 | 85.7% | 85.7% |
| M4 | ocr | 7 | 71.4% | 71.4% |
| M5 | native | 7 | 42.9% | 42.9% |
| M5 | ocr | 7 | 28.6% | 28.6% |

## Per-axis rates (method × layer)

| Method | Layer | state | value | page | span | bbox | derivation | support |
|---|---|---|---|---|---|---|---|---|
| M1 | native | 100.0% | 100.0% | 42.9% | 42.9% | 42.9% | 85.7% | 42.9% |
| M1 | ocr | 100.0% | 100.0% | 42.9% | 42.9% | 28.6% | 85.7% | 42.9% |
| M2 | native | 57.1% | 28.6% | 28.6% | 14.3% | 14.3% | 71.4% | 28.6% |
| M2 | ocr | 57.1% | 85.7% | 42.9% | 42.9% | 28.6% | 71.4% | 42.9% |
| M3 | native | 100.0% | 100.0% | 42.9% | 42.9% | 42.9% | 85.7% | 42.9% |
| M3 | ocr | 100.0% | 100.0% | 42.9% | 42.9% | 28.6% | 85.7% | 42.9% |
| M4 | native | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 85.7% | 100.0% |
| M4 | ocr | 100.0% | 100.0% | 100.0% | 100.0% | 85.7% | 85.7% | 100.0% |
| M5 | native | 42.9% | 85.7% | 42.9% | 42.9% | 42.9% | 100.0% | 100.0% |
| M5 | ocr | 42.9% | 85.7% | 42.9% | 42.9% | 28.6% | 100.0% | 100.0% |

## Cumulative conjunction

| Method | Layer | state | + value | + page | + span | + bbox | + derivation | + support (strict joint) |
|---|---|---|---|---|---|---|---|---|
| M1 | native | 100.0% | 100.0% | 42.9% | 42.9% | 42.9% | 42.9% | 42.9% |
| M1 | ocr | 100.0% | 100.0% | 42.9% | 42.9% | 28.6% | 28.6% | 28.6% |
| M2 | native | 57.1% | 28.6% | 14.3% | 14.3% | 14.3% | 14.3% | 14.3% |
| M2 | ocr | 57.1% | 42.9% | 42.9% | 42.9% | 28.6% | 28.6% | 28.6% |
| M3 | native | 100.0% | 100.0% | 42.9% | 42.9% | 42.9% | 42.9% | 42.9% |
| M3 | ocr | 100.0% | 100.0% | 42.9% | 42.9% | 28.6% | 28.6% | 28.6% |
| M4 | native | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 85.7% | 85.7% |
| M4 | ocr | 100.0% | 100.0% | 100.0% | 100.0% | 85.7% | 71.4% | 71.4% |
| M5 | native | 42.9% | 42.9% | 42.9% | 42.9% | 42.9% | 42.9% | 42.9% |
| M5 | ocr | 42.9% | 42.9% | 42.9% | 42.9% | 28.6% | 28.6% | 28.6% |

## Slices (joint score of the subset)

| Method | Layer | explicit | derived | single_evidence | multi_evidence | cross_page | single_page |
|---|---|---|---|---|---|---|---|
| M1 | native | 60.0% (n=5) | 0.0% (n=2) | 50.0% (n=2) | 40.0% (n=5) | 100.0% (n=1) | 33.3% (n=6) |
| M1 | ocr | 40.0% (n=5) | 0.0% (n=2) | 50.0% (n=2) | 20.0% (n=5) | 100.0% (n=1) | 16.7% (n=6) |
| M2 | native | 20.0% (n=5) | 0.0% (n=2) | 50.0% (n=2) | 0.0% (n=5) | 0.0% (n=1) | 16.7% (n=6) |
| M2 | ocr | 40.0% (n=5) | 0.0% (n=2) | 50.0% (n=2) | 20.0% (n=5) | 100.0% (n=1) | 16.7% (n=6) |
| M3 | native | 60.0% (n=5) | 0.0% (n=2) | 50.0% (n=2) | 40.0% (n=5) | 100.0% (n=1) | 33.3% (n=6) |
| M3 | ocr | 40.0% (n=5) | 0.0% (n=2) | 50.0% (n=2) | 20.0% (n=5) | 100.0% (n=1) | 16.7% (n=6) |
| M4 | native | 80.0% (n=5) | 100.0% (n=2) | 50.0% (n=2) | 100.0% (n=5) | 100.0% (n=1) | 83.3% (n=6) |
| M4 | ocr | 60.0% (n=5) | 100.0% (n=2) | 50.0% (n=2) | 80.0% (n=5) | 100.0% (n=1) | 66.7% (n=6) |
| M5 | native | 60.0% (n=5) | 0.0% (n=2) | 50.0% (n=2) | 40.0% (n=5) | 100.0% (n=1) | 33.3% (n=6) |
| M5 | ocr | 40.0% (n=5) | 0.0% (n=2) | 50.0% (n=2) | 20.0% (n=5) | 100.0% (n=1) | 16.7% (n=6) |

## Cost (aggregated from *.meta.json)

| Method | Layer | backend | n calls | prompt tokens | completion tokens | latency s |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| M1 | native | mlx | 1 | 8747 | 952 | 35.5 |
| M1 | ocr | mlx | 1 | 8610 | 1101 | 37.3 |
| M2 | native | mlx | 8 | 64458 | 689 | 141.6 |
| M2 | ocr | mlx | 8 | 63362 | 390 | 134.3 |
| M3 | native | mlx | 7 | 9781 | 255 | 23.6 |
| M3 | ocr | mlx | 7 | 9251 | 291 | 23.8 |
| M4 | native | rules | 0 | 0 | 0 | 0.0 |
| M4 | ocr | rules | 0 | 0 | 0 | 0.0 |
| M5 | native | mlx | 7 | 1174 | 7 | 3.0 |
| M5 | ocr | mlx | 7 | 1279 | 7 | 2.6 |

## Ingredients (matched records)

| Method | Layer | gold rows | predicted rows | key recall | precision | recall |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| M1 | native | 3 | 2 | 33.3% | 0.0% | 0.0% |
| M1 | ocr | 3 | 2 | 33.3% | 0.0% | 0.0% |
| M2 | native | 3 | 0 | 0.0% | n/a | 0.0% |
| M2 | ocr | 3 | 0 | 0.0% | n/a | 0.0% |
| M3 | native | 3 | 2 | 33.3% | 0.0% | 0.0% |
| M3 | ocr | 3 | 2 | 33.3% | 0.0% | 0.0% |
| M4 | native | 3 | 2 | 66.7% | 0.0% | 0.0% |
| M4 | ocr | 3 | 1 | 33.3% | 0.0% | 0.0% |
| M5 | native | 3 | 2 | 33.3% | 0.0% | 0.0% |
| M5 | ocr | 3 | 2 | 33.3% | 0.0% | 0.0% |

## Inherited (old gold)

Frozen Qwen2.5-7B native-rows artifact. Not re-scored on v1.2; shown only as a historical reference and never mixed with the battery table.

| System | n inst | 7-axis joint | joint (evidence-bearing) |
| --- | ---: | ---: | ---: |
| llm-qwen2.5-7b-native-rows | 140 | 3.6% | 2.2% |

