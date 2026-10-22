# LLM Reranker Baseline Results (dev split only)

Model: `mlx-community/Qwen3.5-2B-MLX-4bit`
Layer: `both`
Score mode: `v2`

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
| LLM-judge | macro complete | 0.231 | 0.692 | 0.846 | 0.923 | 1.000 | 0.308 | 0.692 | 0.923 |
|  | macro piece_recall | 0.231 | 0.692 | 0.846 | 0.923 | 1.000 | 0.308 | 0.692 | 0.923 |

### LLM-judge slice breakdown (native)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 11 | 0.273 | 0.727 | 0.909 | 0.909 | 1.000 | 0.364 | 0.727 | 0.909 |
| multi_evidence | 2 | 0.000 | 0.500 | 0.500 | 1.000 | 1.000 | 0.000 | 0.500 | 1.000 |
| cross_page_false | 13 | 0.231 | 0.692 | 0.846 | 0.923 | 1.000 | 0.308 | 0.692 | 0.923 |
| explicit | 10 | 0.200 | 0.700 | 0.900 | 0.900 | 1.000 | 0.200 | 0.700 | 0.900 |
| derived | 3 | 0.333 | 0.667 | 0.667 | 1.000 | 1.000 | 0.667 | 0.667 | 1.000 |

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
| LLM-judge | macro complete | 0.538 | 0.615 | 0.769 | 0.923 | 1.000 | 0.538 | 0.615 | 0.923 |
|  | macro piece_recall | 0.538 | 0.615 | 0.769 | 0.923 | 1.000 | 0.538 | 0.615 | 0.923 |

### LLM-judge slice breakdown (ocr)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 11 | 0.636 | 0.727 | 0.818 | 0.909 | 1.000 | 0.636 | 0.727 | 0.909 |
| multi_evidence | 2 | 0.000 | 0.000 | 0.500 | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 |
| cross_page_false | 13 | 0.538 | 0.615 | 0.769 | 0.923 | 1.000 | 0.538 | 0.615 | 0.923 |
| explicit | 10 | 0.500 | 0.600 | 0.800 | 0.900 | 1.000 | 0.500 | 0.600 | 0.900 |
| derived | 3 | 0.667 | 0.667 | 0.667 | 1.000 | 1.000 | 0.667 | 0.667 | 1.000 |

## Score distribution sanity

- **native**: n=105, min=0.2689, max=0.8520, mean=0.5207
  ✓ Scores vary — logprobs extracted correctly.
- **ocr**: n=105, min=0.2942, max=0.8670, mean=0.5108
  ✓ Scores vary — logprobs extracted correctly.
