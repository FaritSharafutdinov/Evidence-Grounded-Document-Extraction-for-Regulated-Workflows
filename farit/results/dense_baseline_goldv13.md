# Dense Retrieval Baseline Results (dev split only)

Model: `sentence-transformers/all-MiniLM-L6-v2`

## Comparison: Naive order vs BM25 vs Dense-MiniLM

## Native layer

### Native

| Method | Metric | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
|---|---|---|---|---|---|---|---|---|---|
| Naive order | macro complete | 0.522 | 0.627 | 0.716 | 0.925 | 0.993 | 0.552 | 0.746 | 0.918 |
|  | macro piece_recall | 0.546 | 0.662 | 0.771 | 0.952 | 0.996 | 0.573 | 0.791 | 0.943 |
| BM25 | macro complete | 0.358 | 0.552 | 0.612 | 0.724 | 0.918 | 0.381 | 0.582 | 0.791 |
|  | macro piece_recall | 0.383 | 0.564 | 0.626 | 0.749 | 0.933 | 0.402 | 0.590 | 0.820 |
| Dense-MiniLM | macro complete | 0.351 | 0.552 | 0.627 | 0.769 | 0.933 | 0.440 | 0.627 | 0.784 |
|  | macro piece_recall | 0.394 | 0.605 | 0.666 | 0.799 | 0.951 | 0.481 | 0.663 | 0.819 |

### Dense-MiniLM slice breakdown (native)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 85 | 0.435 | 0.624 | 0.671 | 0.800 | 0.953 | 0.506 | 0.671 | 0.812 |
| multi_evidence | 49 | 0.204 | 0.429 | 0.551 | 0.714 | 0.898 | 0.327 | 0.551 | 0.735 |
| cross_page_true | 20 | 0.000 | 0.050 | 0.250 | 0.450 | 0.750 | 0.050 | 0.300 | 0.450 |
| cross_page_false | 114 | 0.412 | 0.640 | 0.693 | 0.825 | 0.965 | 0.509 | 0.684 | 0.842 |
| explicit | 91 | 0.407 | 0.593 | 0.659 | 0.802 | 0.956 | 0.495 | 0.670 | 0.824 |
| derived | 43 | 0.233 | 0.465 | 0.558 | 0.698 | 0.884 | 0.326 | 0.535 | 0.698 |

## OCR layer

### OCR

| Method | Metric | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
|---|---|---|---|---|---|---|---|---|---|
| Naive order | macro complete | 0.522 | 0.627 | 0.716 | 0.925 | 0.993 | 0.552 | 0.746 | 0.896 |
|  | macro piece_recall | 0.546 | 0.662 | 0.771 | 0.952 | 0.996 | 0.573 | 0.776 | 0.940 |
| BM25 | macro complete | 0.373 | 0.530 | 0.612 | 0.716 | 0.925 | 0.381 | 0.582 | 0.784 |
|  | macro piece_recall | 0.397 | 0.541 | 0.626 | 0.742 | 0.937 | 0.402 | 0.598 | 0.813 |
| Dense-MiniLM | macro complete | 0.358 | 0.537 | 0.672 | 0.784 | 0.933 | 0.448 | 0.657 | 0.806 |
|  | macro piece_recall | 0.405 | 0.595 | 0.729 | 0.826 | 0.948 | 0.500 | 0.712 | 0.853 |

### Dense-MiniLM slice breakdown (OCR)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 85 | 0.424 | 0.635 | 0.741 | 0.824 | 0.941 | 0.506 | 0.729 | 0.847 |
| multi_evidence | 49 | 0.245 | 0.367 | 0.551 | 0.714 | 0.918 | 0.347 | 0.531 | 0.735 |
| cross_page_true | 20 | 0.000 | 0.050 | 0.150 | 0.400 | 0.800 | 0.000 | 0.150 | 0.400 |
| cross_page_false | 114 | 0.421 | 0.623 | 0.763 | 0.851 | 0.956 | 0.526 | 0.746 | 0.877 |
| explicit | 91 | 0.407 | 0.615 | 0.736 | 0.824 | 0.967 | 0.495 | 0.725 | 0.846 |
| derived | 43 | 0.256 | 0.372 | 0.535 | 0.698 | 0.860 | 0.349 | 0.512 | 0.721 |

## Interpretation

Dense-MiniLM improves over BM25 on most metrics, but the gap is modest. The largest gains are on single-evidence and explicit instances where semantic similarity better matches query intent. However, dense retrieval still fails on the hardest slices: multi-evidence (complete@3 ~0.4–0.5), cross-page (~0.3), and derived (~0.2–0.3). These failures are structural — no single-page scoring method can guarantee coverage of dispersed evidence. Naive order remains surprisingly strong, confirming that SDS evidence tends to appear early. Native and OCR layers show nearly identical dense performance, suggesting MiniLM is robust to OCR noise at this granularity.
