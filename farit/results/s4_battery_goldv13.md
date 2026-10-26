# S4 baseline battery — full run

Six simple extraction methods on one model, scored against gold v1.3 (dev split). M3 and M5 depend on the M1 pass; M4 is the inherited rules-v4 re-scored against v1.3 with zero LLM calls; M6 routes each field to its SDS section by a hand-written rule.

## Joint score (7-axis conjunction) by method × layer

| Method | Layer | n inst | 7-axis joint | joint (evidence-bearing) |
| --- | --- | ---: | ---: | ---: |
| M1 | native | 140 | 18.6% | 19.4% |
| M1 | ocr | 140 | 11.4% | 11.9% |
| M2 | native | 140 | 21.4% | 19.4% |
| M2 | ocr | 140 | 9.3% | 6.7% |
| M3 | native | 140 | 18.6% | 19.4% |
| M3 | ocr | 140 | 12.1% | 12.7% |
| M4 | native | 140 | 55.0% | 53.0% |
| M4 | ocr | 140 | 30.7% | 27.6% |
| M5 | native | 140 | 20.7% | 17.9% |
| M5 | ocr | 140 | 15.7% | 11.9% |
| M6 | native | 140 | 17.9% | 16.4% |
| M6 | ocr | 140 | 8.6% | 6.7% |

## Per-axis rates (method × layer)

| Method | Layer | state | value | page | span | bbox | derivation | support |
|---|---|---|---|---|---|---|---|---|
| M1 | native | 88.6% | 90.7% | 64.2% | 26.9% | 23.9% | 85.0% | 45.3% |
| M1 | ocr | 87.9% | 90.7% | 65.7% | 30.6% | 14.2% | 85.7% | 44.6% |
| M2 | native | 50.0% | 72.1% | 45.5% | 26.9% | 23.1% | 77.1% | 46.9% |
| M2 | ocr | 47.1% | 69.3% | 44.0% | 22.4% | 7.5% | 73.1% | 34.7% |
| M3 | native | 77.9% | 87.1% | 62.7% | 26.9% | 23.9% | 85.5% | 54.5% |
| M3 | ocr | 70.7% | 85.7% | 57.5% | 31.3% | 14.9% | 85.0% | 55.8% |
| M4 | native | 80.0% | 86.4% | 73.9% | 59.7% | 56.7% | 92.7% | 95.4% |
| M4 | ocr | 73.6% | 82.9% | 70.9% | 56.0% | 29.1% | 92.1% | 96.0% |
| M5 | native | 49.3% | 85.0% | 38.1% | 21.6% | 18.7% | 93.9% | 77.6% |
| M5 | ocr | 50.0% | 85.7% | 39.6% | 27.6% | 13.4% | 93.9% | 74.2% |
| M6 | native | 42.1% | 67.1% | 46.3% | 22.4% | 20.9% | 72.4% | 42.2% |
| M6 | ocr | 35.7% | 64.3% | 37.3% | 17.2% | 7.5% | 75.7% | 43.8% |

## Cumulative conjunction

| Method | Layer | state | + value | + page | + span | + bbox | + derivation | + support (strict joint) |
|---|---|---|---|---|---|---|---|---|
| M1 | native | 88.6% | 85.0% | 57.1% | 23.6% | 20.7% | 18.6% | 18.6% |
| M1 | ocr | 87.9% | 84.3% | 59.3% | 27.9% | 12.1% | 11.4% | 11.4% |
| M2 | native | 50.0% | 39.3% | 30.7% | 23.6% | 21.4% | 21.4% | 21.4% |
| M2 | ocr | 47.1% | 35.7% | 28.6% | 19.3% | 9.3% | 9.3% | 9.3% |
| M3 | native | 77.9% | 74.3% | 55.7% | 23.6% | 20.7% | 18.6% | 18.6% |
| M3 | ocr | 70.7% | 67.1% | 51.4% | 28.6% | 12.9% | 12.1% | 12.1% |
| M4 | native | 80.0% | 76.4% | 71.4% | 60.7% | 57.9% | 56.4% | 55.0% |
| M4 | ocr | 73.6% | 69.3% | 67.9% | 57.1% | 31.4% | 30.7% | 30.7% |
| M5 | native | 49.3% | 47.1% | 37.9% | 23.6% | 20.7% | 20.7% | 20.7% |
| M5 | ocr | 50.0% | 47.9% | 40.0% | 30.0% | 16.4% | 15.7% | 15.7% |
| M6 | native | 42.1% | 30.7% | 26.4% | 18.6% | 17.9% | 17.9% | 17.9% |
| M6 | ocr | 35.7% | 26.4% | 24.3% | 16.4% | 8.6% | 8.6% | 8.6% |

## Slices (joint score of the subset)

| Method | Layer | explicit | derived | single_evidence | multi_evidence | cross_page | single_page |
|---|---|---|---|---|---|---|---|
| M1 | native | 28.6% (n=91) | 0.0% (n=49) | 19.8% (n=91) | 16.3% (n=49) | 25.0% (n=20) | 17.5% (n=120) |
| M1 | ocr | 17.6% (n=91) | 0.0% (n=49) | 14.3% (n=91) | 6.1% (n=49) | 10.0% (n=20) | 11.7% (n=120) |
| M2 | native | 27.5% (n=91) | 10.2% (n=49) | 26.4% (n=91) | 12.2% (n=49) | 25.0% (n=20) | 20.8% (n=120) |
| M2 | ocr | 9.9% (n=91) | 8.2% (n=49) | 13.2% (n=91) | 2.0% (n=49) | 0.0% (n=20) | 10.8% (n=120) |
| M3 | native | 28.6% (n=91) | 0.0% (n=49) | 19.8% (n=91) | 16.3% (n=49) | 25.0% (n=20) | 17.5% (n=120) |
| M3 | ocr | 18.7% (n=91) | 0.0% (n=49) | 14.3% (n=91) | 8.2% (n=49) | 10.0% (n=20) | 12.5% (n=120) |
| M4 | native | 60.4% (n=91) | 44.9% (n=49) | 48.4% (n=91) | 67.3% (n=49) | 60.0% (n=20) | 54.2% (n=120) |
| M4 | ocr | 31.9% (n=91) | 28.6% (n=49) | 28.6% (n=91) | 34.7% (n=49) | 45.0% (n=20) | 28.3% (n=120) |
| M5 | native | 26.4% (n=91) | 10.2% (n=49) | 24.2% (n=91) | 14.3% (n=49) | 20.0% (n=20) | 20.8% (n=120) |
| M5 | ocr | 17.6% (n=91) | 12.2% (n=49) | 20.9% (n=91) | 6.1% (n=49) | 10.0% (n=20) | 16.7% (n=120) |
| M6 | native | 24.2% (n=91) | 6.1% (n=49) | 18.7% (n=91) | 16.3% (n=49) | 30.0% (n=20) | 15.8% (n=120) |
| M6 | ocr | 9.9% (n=91) | 6.1% (n=49) | 7.7% (n=91) | 10.2% (n=49) | 20.0% (n=20) | 6.7% (n=120) |

## Cost (aggregated from *.meta.json)

| Method | Layer | backend | n calls | prompt tokens | completion tokens | latency s |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| M1 | native | openai | 20 | 149276 | 15517 | 0.0 |
| M1 | ocr | openai | 20 | 146859 | 14319 | 0.0 |
| M2 | native | openai | 160 | 1083168 | 15565 | 0.0 |
| M2 | ocr | openai | 160 | 1063832 | 12448 | 195.7 |
| M3 | native | openai | 139 | 215974 | 4951 | 121.7 |
| M3 | ocr | openai | 139 | 206390 | 4523 | 112.2 |
| M4 | native | rules | 0 | 0 | 0 | 0.0 |
| M4 | ocr | rules | 0 | 0 | 0 | 0.0 |
| M5 | native | openai | 139 | 22713 | 278 | 13.2 |
| M5 | ocr | openai | 139 | 22617 | 278 | 9.4 |
| M6 | native | openai | 160 | 524870 | 13647 | 308.7 |
| M6 | ocr | openai | 160 | 515801 | 12640 | 284.0 |

## Ingredients (matched records)

| Method | Layer | gold rows | predicted rows | key recall | precision | recall |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| M1 | native | 63 | 45 | 60.3% | 51.1% | 36.5% |
| M1 | ocr | 63 | 35 | 33.3% | 20.0% | 11.1% |
| M2 | native | 63 | 32 | 42.9% | 43.8% | 22.2% |
| M2 | ocr | 63 | 18 | 20.6% | 22.2% | 6.3% |
| M3 | native | 63 | 45 | 60.3% | 51.1% | 36.5% |
| M3 | ocr | 63 | 35 | 33.3% | 20.0% | 11.1% |
| M4 | native | 63 | 39 | 61.9% | 5.1% | 3.2% |
| M4 | ocr | 63 | 32 | 50.8% | 6.2% | 3.2% |
| M5 | native | 63 | 45 | 60.3% | 51.1% | 36.5% |
| M5 | ocr | 63 | 35 | 33.3% | 20.0% | 11.1% |
| M6 | native | 63 | 31 | 44.4% | 51.6% | 25.4% |
| M6 | ocr | 63 | 18 | 27.0% | 38.9% | 11.1% |

## Inherited (re-scored on gold v1.3)

Frozen Qwen2.5-7B native-rows artifact, produced on gold v1.0 (its own report quotes 6.4% joint there). The numbers below re-score those frozen predictions against the current gold v1.3; shown only as a historical reference and never mixed with the battery table.

| System | n inst | 7-axis joint | joint (evidence-bearing) |
| --- | ---: | ---: | ---: |
| llm-qwen2.5-7b-native-rows | 140 | 3.6% | 2.2% |

