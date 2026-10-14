# LLM Reranker Baseline Results (dev split only)

Model: `mlx-community/Qwen2.5-7B-Instruct-4bit`
Layer: `both`

## Native layer

### Comparison (Native)

| Method | Metric | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
|---|---|---|---|---|---|---|---|---|---|
| Naive order | macro complete | 0.464 | 0.600 | 0.696 | 0.928 | 0.992 | 0.496 | 0.728 | 0.944 |
|  | macro piece_recall | 0.492 | 0.620 | 0.736 | 0.952 | 0.996 | 0.520 | 0.756 | 0.948 |
| BM25 | macro complete | 0.352 | 0.544 | 0.600 | 0.720 | 0.896 | 0.376 | 0.576 | 0.776 |
|  | macro piece_recall | 0.372 | 0.552 | 0.612 | 0.740 | 0.912 | 0.392 | 0.576 | 0.796 |
| Dense-MiniLM | macro complete | 0.328 | 0.536 | 0.632 | 0.800 | 0.952 | 0.416 | 0.632 | 0.808 |
|  | macro piece_recall | 0.376 | 0.588 | 0.668 | 0.816 | 0.972 | 0.460 | 0.664 | 0.836 |
| LLM-judge | macro complete | 0.704 | 0.808 | 0.864 | 0.912 | 1.000 | 0.712 | 0.880 | 0.952 |
|  | macro piece_recall | 0.756 | 0.844 | 0.896 | 0.936 | 1.000 | 0.760 | 0.904 | 0.964 |

### LLM-judge slice breakdown (native)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 77 | 0.870 | 0.883 | 0.909 | 0.948 | 1.000 | 0.844 | 0.909 | 0.974 |
| multi_evidence | 48 | 0.438 | 0.688 | 0.792 | 0.854 | 1.000 | 0.500 | 0.833 | 0.917 |
| cross_page_true | 19 | 0.000 | 0.368 | 0.579 | 0.684 | 1.000 | 0.053 | 0.684 | 0.842 |
| cross_page_false | 106 | 0.830 | 0.887 | 0.915 | 0.953 | 1.000 | 0.830 | 0.915 | 0.972 |
| explicit | 89 | 0.798 | 0.876 | 0.910 | 0.944 | 1.000 | 0.798 | 0.921 | 0.978 |
| derived | 36 | 0.472 | 0.639 | 0.750 | 0.833 | 1.000 | 0.500 | 0.778 | 0.889 |

## Ocr layer

### Comparison (Ocr)

| Method | Metric | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
|---|---|---|---|---|---|---|---|---|---|
| Naive order | macro complete | 0.464 | 0.600 | 0.696 | 0.928 | 0.992 | 0.496 | 0.728 | 0.920 |
|  | macro piece_recall | 0.492 | 0.620 | 0.736 | 0.952 | 0.996 | 0.520 | 0.740 | 0.944 |
| BM25 | macro complete | 0.360 | 0.520 | 0.592 | 0.712 | 0.904 | 0.368 | 0.576 | 0.768 |
|  | macro piece_recall | 0.380 | 0.528 | 0.604 | 0.732 | 0.916 | 0.384 | 0.588 | 0.788 |
| Dense-MiniLM | macro complete | 0.344 | 0.520 | 0.688 | 0.808 | 0.952 | 0.432 | 0.664 | 0.824 |
|  | macro piece_recall | 0.396 | 0.584 | 0.744 | 0.840 | 0.968 | 0.488 | 0.724 | 0.864 |
| LLM-judge | macro complete | 0.656 | 0.792 | 0.856 | 0.920 | 1.000 | 0.680 | 0.848 | 0.936 |
|  | macro piece_recall | 0.704 | 0.824 | 0.880 | 0.944 | 1.000 | 0.720 | 0.868 | 0.960 |

### LLM-judge slice breakdown (ocr)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 77 | 0.818 | 0.870 | 0.909 | 0.974 | 1.000 | 0.805 | 0.883 | 0.987 |
| multi_evidence | 48 | 0.396 | 0.667 | 0.771 | 0.833 | 1.000 | 0.479 | 0.792 | 0.854 |
| cross_page_true | 19 | 0.000 | 0.368 | 0.526 | 0.632 | 1.000 | 0.053 | 0.579 | 0.684 |
| cross_page_false | 106 | 0.774 | 0.868 | 0.915 | 0.972 | 1.000 | 0.792 | 0.896 | 0.981 |
| explicit | 89 | 0.742 | 0.854 | 0.899 | 0.955 | 1.000 | 0.753 | 0.888 | 0.978 |
| derived | 36 | 0.444 | 0.639 | 0.750 | 0.833 | 1.000 | 0.500 | 0.750 | 0.833 |

## Score distribution sanity

- **native**: n=1303, min=0.0000, max=1.0000, mean=0.1387
  ⚠️  Scores outside (0,1) detected!
  ✓ Scores vary — logprobs extracted correctly.
- **ocr**: n=1303, min=0.0000, max=1.0000, mean=0.1347
  ⚠️  Scores outside (0,1) detected!
  ✓ Scores vary — logprobs extracted correctly.
