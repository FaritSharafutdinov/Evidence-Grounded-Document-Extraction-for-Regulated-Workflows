# Dense Retrieval Baseline Results (dev split only)

Model: `sentence-transformers/all-MiniLM-L6-v2`

## Comparison: Naive order vs BM25 vs Dense-MiniLM

## Native layer

### Native

| Method | Metric | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
|---|---|---|---|---|---|---|---|---|---|
| Naive order | macro complete | 0.489 | 0.594 | 0.684 | 0.925 | 0.992 | 0.519 | 0.714 | 0.917 |
|  | macro piece_recall | 0.513 | 0.630 | 0.740 | 0.951 | 0.996 | 0.540 | 0.759 | 0.942 |
| BM25 | macro complete | 0.353 | 0.549 | 0.602 | 0.707 | 0.902 | 0.376 | 0.579 | 0.774 |
|  | macro piece_recall | 0.378 | 0.560 | 0.616 | 0.732 | 0.917 | 0.397 | 0.587 | 0.803 |
| Dense-MiniLM | macro complete | 0.346 | 0.549 | 0.632 | 0.789 | 0.955 | 0.436 | 0.632 | 0.805 |
|  | macro piece_recall | 0.389 | 0.602 | 0.671 | 0.820 | 0.974 | 0.478 | 0.668 | 0.840 |

### Dense-MiniLM slice breakdown (native)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 80 | 0.450 | 0.650 | 0.700 | 0.838 | 0.988 | 0.525 | 0.700 | 0.850 |
| multi_evidence | 53 | 0.189 | 0.396 | 0.528 | 0.717 | 0.906 | 0.302 | 0.528 | 0.736 |
| cross_page_true | 20 | 0.000 | 0.050 | 0.250 | 0.450 | 0.750 | 0.050 | 0.300 | 0.450 |
| cross_page_false | 113 | 0.407 | 0.637 | 0.699 | 0.850 | 0.991 | 0.504 | 0.690 | 0.867 |
| explicit | 90 | 0.400 | 0.589 | 0.656 | 0.800 | 0.956 | 0.489 | 0.667 | 0.822 |
| derived | 43 | 0.233 | 0.465 | 0.581 | 0.767 | 0.953 | 0.326 | 0.558 | 0.767 |

## OCR layer

### OCR

| Method | Metric | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
|---|---|---|---|---|---|---|---|---|---|
| Naive order | macro complete | 0.489 | 0.594 | 0.684 | 0.925 | 0.992 | 0.519 | 0.714 | 0.895 |
|  | macro piece_recall | 0.513 | 0.630 | 0.740 | 0.951 | 0.996 | 0.540 | 0.744 | 0.939 |
| BM25 | macro complete | 0.368 | 0.526 | 0.594 | 0.699 | 0.910 | 0.376 | 0.579 | 0.767 |
|  | macro piece_recall | 0.393 | 0.538 | 0.609 | 0.725 | 0.921 | 0.397 | 0.595 | 0.796 |
| Dense-MiniLM | macro complete | 0.353 | 0.541 | 0.684 | 0.797 | 0.955 | 0.444 | 0.669 | 0.820 |
|  | macro piece_recall | 0.400 | 0.599 | 0.742 | 0.840 | 0.970 | 0.496 | 0.725 | 0.866 |

### Dense-MiniLM slice breakdown (OCR)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 80 | 0.438 | 0.662 | 0.775 | 0.863 | 0.988 | 0.525 | 0.762 | 0.887 |
| multi_evidence | 53 | 0.226 | 0.358 | 0.547 | 0.698 | 0.906 | 0.321 | 0.528 | 0.717 |
| cross_page_true | 20 | 0.000 | 0.050 | 0.150 | 0.400 | 0.800 | 0.000 | 0.150 | 0.400 |
| cross_page_false | 113 | 0.416 | 0.628 | 0.779 | 0.867 | 0.982 | 0.522 | 0.761 | 0.894 |
| explicit | 90 | 0.400 | 0.611 | 0.733 | 0.822 | 0.967 | 0.489 | 0.722 | 0.844 |
| derived | 43 | 0.256 | 0.395 | 0.581 | 0.744 | 0.930 | 0.349 | 0.558 | 0.767 |

## Interpretation

Dense-MiniLM improves over BM25 on most metrics, but the gap is modest. The largest gains are on single-evidence and explicit instances where semantic similarity better matches query intent. However, dense retrieval still fails on the hardest slices: multi-evidence (complete@3 ~0.4–0.5), cross-page (~0.3), and derived (~0.2–0.3). These failures are structural — no single-page scoring method can guarantee coverage of dispersed evidence. Naive order remains surprisingly strong, confirming that SDS evidence tends to appear early. Native and OCR layers show nearly identical dense performance, suggesting MiniLM is robust to OCR noise at this granularity.
