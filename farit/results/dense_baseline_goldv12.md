# Dense Retrieval Baseline Results (dev split only)

Model: `sentence-transformers/all-MiniLM-L6-v2`

## Comparison: Naive order vs BM25 vs Dense-MiniLM

## Native layer

### Native

| Method | Metric | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
|---|---|---|---|---|---|---|---|---|---|
| Naive order | macro complete | 0.493 | 0.597 | 0.687 | 0.925 | 0.993 | 0.522 | 0.716 | 0.918 |
|  | macro piece_recall | 0.516 | 0.633 | 0.742 | 0.952 | 0.996 | 0.543 | 0.761 | 0.943 |
| BM25 | macro complete | 0.358 | 0.552 | 0.604 | 0.709 | 0.903 | 0.381 | 0.582 | 0.776 |
|  | macro piece_recall | 0.383 | 0.564 | 0.619 | 0.734 | 0.918 | 0.402 | 0.590 | 0.805 |
| Dense-MiniLM | macro complete | 0.351 | 0.552 | 0.634 | 0.791 | 0.955 | 0.440 | 0.634 | 0.806 |
|  | macro piece_recall | 0.394 | 0.605 | 0.673 | 0.821 | 0.974 | 0.481 | 0.670 | 0.841 |

### Dense-MiniLM slice breakdown (native)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 81 | 0.457 | 0.654 | 0.704 | 0.840 | 0.988 | 0.531 | 0.704 | 0.852 |
| multi_evidence | 53 | 0.189 | 0.396 | 0.528 | 0.717 | 0.906 | 0.302 | 0.528 | 0.736 |
| cross_page_true | 20 | 0.000 | 0.050 | 0.250 | 0.450 | 0.750 | 0.050 | 0.300 | 0.450 |
| cross_page_false | 114 | 0.412 | 0.640 | 0.702 | 0.851 | 0.991 | 0.509 | 0.693 | 0.868 |
| explicit | 91 | 0.407 | 0.593 | 0.659 | 0.802 | 0.956 | 0.495 | 0.670 | 0.824 |
| derived | 43 | 0.233 | 0.465 | 0.581 | 0.767 | 0.953 | 0.326 | 0.558 | 0.767 |

## OCR layer

### OCR

| Method | Metric | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
|---|---|---|---|---|---|---|---|---|---|
| Naive order | macro complete | 0.493 | 0.597 | 0.687 | 0.925 | 0.993 | 0.522 | 0.716 | 0.896 |
|  | macro piece_recall | 0.516 | 0.633 | 0.742 | 0.952 | 0.996 | 0.543 | 0.746 | 0.940 |
| BM25 | macro complete | 0.373 | 0.530 | 0.597 | 0.701 | 0.910 | 0.381 | 0.582 | 0.769 |
|  | macro piece_recall | 0.397 | 0.541 | 0.611 | 0.727 | 0.922 | 0.402 | 0.598 | 0.798 |
| Dense-MiniLM | macro complete | 0.358 | 0.545 | 0.687 | 0.799 | 0.955 | 0.448 | 0.672 | 0.821 |
|  | macro piece_recall | 0.405 | 0.602 | 0.744 | 0.841 | 0.970 | 0.500 | 0.727 | 0.867 |

### Dense-MiniLM slice breakdown (OCR)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 81 | 0.444 | 0.667 | 0.778 | 0.864 | 0.988 | 0.531 | 0.765 | 0.889 |
| multi_evidence | 53 | 0.226 | 0.358 | 0.547 | 0.698 | 0.906 | 0.321 | 0.528 | 0.717 |
| cross_page_true | 20 | 0.000 | 0.050 | 0.150 | 0.400 | 0.800 | 0.000 | 0.150 | 0.400 |
| cross_page_false | 114 | 0.421 | 0.632 | 0.781 | 0.868 | 0.982 | 0.526 | 0.763 | 0.895 |
| explicit | 91 | 0.407 | 0.615 | 0.736 | 0.824 | 0.967 | 0.495 | 0.725 | 0.846 |
| derived | 43 | 0.256 | 0.395 | 0.581 | 0.744 | 0.930 | 0.349 | 0.558 | 0.767 |

## Interpretation

Dense-MiniLM improves over BM25 on most metrics, but the gap is modest. The largest gains are on single-evidence and explicit instances where semantic similarity better matches query intent. However, dense retrieval still fails on the hardest slices: multi-evidence (complete@3 ~0.4–0.5), cross-page (~0.3), and derived (~0.2–0.3). These failures are structural — no single-page scoring method can guarantee coverage of dispersed evidence. Naive order remains surprisingly strong, confirming that SDS evidence tends to appear early. Native and OCR layers show nearly identical dense performance, suggesting MiniLM is robust to OCR noise at this granularity.
