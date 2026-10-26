# State-anomaly decomposition (K3)

Instances = dev product fields; `changed` counts only instances **M1 got right**.

## native

| method | state correct / n |
| --- | --- |
| M1 | 124 / 140 |
| M2 | 70 / 140 |
| M5 | 69 / 140 |

| transition | M1-correct | kept | changed | → NOT_STATED | → other |
| --- | ---: | ---: | ---: | ---: | ---: |
| M1 → M2 | 124 | 60 | 64 | 37 | 27 |
| M1 → M5 | 124 | 64 | 60 | 60 | 0 |

## ocr

| method | state correct / n |
| --- | --- |
| M1 | 123 / 140 |
| M2 | 66 / 140 |
| M5 | 70 / 140 |

| transition | M1-correct | kept | changed | → NOT_STATED | → other |
| --- | ---: | ---: | ---: | ---: | ---: |
| M1 → M2 | 123 | 56 | 67 | 40 | 27 |
| M1 → M5 | 123 | 64 | 59 | 59 | 0 |

