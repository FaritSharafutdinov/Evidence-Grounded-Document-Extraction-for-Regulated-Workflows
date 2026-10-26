# S4 baseline battery — full run

Five simple extraction methods on one model, scored against gold v1.3 (dev split). M3 and M5 depend on the M1 pass; M4 is the inherited rules-v4 re-scored against v1.3 with zero LLM calls.

## Joint score (7-axis conjunction) by method × layer

| Method | Layer | n inst | 7-axis joint | joint (evidence-bearing) |
| --- | --- | ---: | ---: | ---: |
| M1 | native | 140 | 15.7% | 16.4% |
| M1 | ocr | 140 | 8.6% | 9.0% |
| M2 | native | 140 | 19.3% | 18.7% |
| M2 | ocr | 140 | 11.4% | 10.4% |
| M3 | native | 140 | 15.7% | 16.4% |
| M3 | ocr | 140 | 7.9% | 8.2% |
| M4 | native | 140 | 55.0% | 53.0% |
| M4 | ocr | 140 | 30.7% | 27.6% |
| M5 | native | 140 | 16.4% | 16.4% |
| M5 | ocr | 140 | 9.3% | 9.0% |

## Per-axis rates (method × layer)

| Method | Layer | state | value | page | span | bbox | derivation | support |
|---|---|---|---|---|---|---|---|---|
| M1 | native | 82.1% | 78.6% | 37.3% | 20.9% | 19.4% | 66.4% | 32.9% |
| M1 | ocr | 72.1% | 70.7% | 35.1% | 20.1% | 9.0% | 59.7% | 27.1% |
| M2 | native | 55.0% | 65.0% | 44.0% | 27.6% | 23.1% | 70.1% | 41.3% |
| M2 | ocr | 54.3% | 70.0% | 41.8% | 26.1% | 11.9% | 70.5% | 42.2% |
| M3 | native | 78.6% | 80.0% | 38.1% | 22.4% | 20.9% | 63.7% | 37.7% |
| M3 | ocr | 67.9% | 73.6% | 34.3% | 20.9% | 9.7% | 65.2% | 33.9% |
| M4 | native | 80.0% | 86.4% | 73.9% | 59.7% | 56.7% | 92.7% | 95.4% |
| M4 | ocr | 73.6% | 82.9% | 70.9% | 56.0% | 29.1% | 92.1% | 96.0% |
| M5 | native | 72.1% | 75.0% | 35.8% | 20.9% | 19.4% | 66.4% | 39.0% |
| M5 | ocr | 64.3% | 72.9% | 32.1% | 19.4% | 9.0% | 67.0% | 34.3% |

## Cumulative conjunction

| Method | Layer | state | + value | + page | + span | + bbox | + derivation | + support (strict joint) |
|---|---|---|---|---|---|---|---|---|
| M1 | native | 82.1% | 75.7% | 30.0% | 17.9% | 16.4% | 16.4% | 15.7% |
| M1 | ocr | 72.1% | 67.9% | 29.3% | 17.9% | 8.6% | 8.6% | 8.6% |
| M2 | native | 55.0% | 38.6% | 29.3% | 23.6% | 19.3% | 19.3% | 19.3% |
| M2 | ocr | 54.3% | 38.6% | 31.4% | 23.6% | 11.4% | 11.4% | 11.4% |
| M3 | native | 78.6% | 72.9% | 30.0% | 17.9% | 16.4% | 16.4% | 15.7% |
| M3 | ocr | 67.9% | 64.3% | 28.6% | 17.1% | 7.9% | 7.9% | 7.9% |
| M4 | native | 80.0% | 76.4% | 71.4% | 60.7% | 57.9% | 56.4% | 55.0% |
| M4 | ocr | 73.6% | 69.3% | 67.9% | 57.1% | 31.4% | 30.7% | 30.7% |
| M5 | native | 72.1% | 67.1% | 30.0% | 18.6% | 17.1% | 17.1% | 16.4% |
| M5 | ocr | 64.3% | 61.4% | 27.9% | 17.9% | 9.3% | 9.3% | 9.3% |

## Slices (joint score of the subset)

| Method | Layer | explicit | derived | single_evidence | multi_evidence | cross_page | single_page |
|---|---|---|---|---|---|---|---|
| M1 | native | 24.2% (n=91) | 0.0% (n=49) | 18.7% (n=91) | 10.2% (n=49) | 15.0% (n=20) | 15.8% (n=120) |
| M1 | ocr | 13.2% (n=91) | 0.0% (n=49) | 11.0% (n=91) | 4.1% (n=49) | 10.0% (n=20) | 8.3% (n=120) |
| M2 | native | 27.5% (n=91) | 4.1% (n=49) | 24.2% (n=91) | 10.2% (n=49) | 20.0% (n=20) | 19.2% (n=120) |
| M2 | ocr | 15.4% (n=91) | 4.1% (n=49) | 14.3% (n=91) | 6.1% (n=49) | 10.0% (n=20) | 11.7% (n=120) |
| M3 | native | 24.2% (n=91) | 0.0% (n=49) | 18.7% (n=91) | 10.2% (n=49) | 15.0% (n=20) | 15.8% (n=120) |
| M3 | ocr | 12.1% (n=91) | 0.0% (n=49) | 9.9% (n=91) | 4.1% (n=49) | 10.0% (n=20) | 7.5% (n=120) |
| M4 | native | 60.4% (n=91) | 44.9% (n=49) | 48.4% (n=91) | 67.3% (n=49) | 60.0% (n=20) | 54.2% (n=120) |
| M4 | ocr | 31.9% (n=91) | 28.6% (n=49) | 28.6% (n=91) | 34.7% (n=49) | 45.0% (n=20) | 28.3% (n=120) |
| M5 | native | 24.2% (n=91) | 2.0% (n=49) | 19.8% (n=91) | 10.2% (n=49) | 15.0% (n=20) | 16.7% (n=120) |
| M5 | ocr | 13.2% (n=91) | 2.0% (n=49) | 12.1% (n=91) | 4.1% (n=49) | 10.0% (n=20) | 9.2% (n=120) |

## Cost (aggregated from *.meta.json)

| Method | Layer | backend | n calls | prompt tokens | completion tokens | latency s |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| M1 | native | mlx | 20 | 149176 | 14923 | 737.1 |
| M1 | ocr | mlx | 20 | 146759 | 19159 | 1127.7 |
| M2 | native | mlx | 160 | 1083048 | 11387 | 3850.0 |
| M2 | ocr | mlx | 160 | 1063712 | 9179 | 4104.7 |
| M3 | native | mlx | 86 | 126224 | 2632 | 498.6 |
| M3 | ocr | mlx | 78 | 111697 | 2468 | 443.0 |
| M4 | native | rules | 0 | 0 | 0 | 0.0 |
| M4 | ocr | rules | 0 | 0 | 0 | 0.0 |
| M5 | native | mlx | 86 | 14198 | 86 | 53.7 |
| M5 | ocr | mlx | 78 | 12846 | 78 | 35.9 |

## Ingredients (matched records)

| Method | Layer | gold rows | predicted rows | key recall | precision | recall |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| M1 | native | 63 | 55 | 66.7% | 49.1% | 42.9% |
| M1 | ocr | 63 | 60 | 46.0% | 8.3% | 7.9% |
| M2 | native | 63 | 19 | 25.4% | 42.1% | 12.7% |
| M2 | ocr | 63 | 6 | 9.5% | 50.0% | 4.8% |
| M3 | native | 63 | 55 | 66.7% | 49.1% | 42.9% |
| M3 | ocr | 63 | 60 | 46.0% | 8.3% | 7.9% |
| M4 | native | 63 | 39 | 61.9% | 5.1% | 3.2% |
| M4 | ocr | 63 | 32 | 50.8% | 6.2% | 3.2% |
| M5 | native | 63 | 55 | 66.7% | 49.1% | 42.9% |
| M5 | ocr | 63 | 60 | 46.0% | 8.3% | 7.9% |

## Inherited (re-scored on gold v1.3)

Frozen Qwen2.5-7B native-rows artifact, produced on gold v1.0 (its own report quotes 6.4% joint there). The numbers below re-score those frozen predictions against the current gold v1.3; shown only as a historical reference and never mixed with the battery table.

| System | n inst | 7-axis joint | joint (evidence-bearing) |
| --- | ---: | ---: | ---: |
| llm-qwen2.5-7b-native-rows | 140 | 3.6% | 2.2% |

