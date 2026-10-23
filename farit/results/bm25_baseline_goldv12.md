# BM25 Baseline Results (dev split only)

## Queries used

- **product_name**: `product name Trade name / product identifier.`
- **supplier_name**: `supplier name Supplier, manufacturer or distributor named on the SDS.`
- **substance_or_mixture**: `substance or mixture Whether the product is a substance, mixture or article.`
- **product_cas_number**: `product cas number CAS of the product itself. Defined only for a substance.`
- **chemical_formula**: `chemical formula Molecular formula of the product. Defined only for a substance.`
- **molecular_weight**: `molecular weight Molecular weight in g/mol. Defined only for a substance.`
- **flash_point**: `flash point Flash point, compared in degrees Celsius.`

## Inclusion / exclusion statistics

- Total dev instances: 160
- Excluded (ingredients): 20
- Excluded (empty evidence_set): 6
- Excluded (NOT_STATED / no evidence required): 0
- **Included in metrics**: 134

## Sanity checks

- A1: `sds_01.pdf` / `product_name` page 1 rank in native: **2**

## Native layer

### Native

| Method | Metric | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
|---|---|---|---|---|---|---|---|---|---|
| BM25 | macro complete | 0.358 | 0.552 | 0.604 | 0.709 | 0.903 | 0.381 | 0.582 | 0.776 |
|  | macro piece_recall | 0.383 | 0.564 | 0.619 | 0.734 | 0.918 | 0.402 | 0.590 | 0.805 |
|  | micro piece_recall | 0.337 | 0.503 | 0.563 | 0.698 | 0.915 | 0.357 | 0.533 | 0.774 |
| Naive order | macro complete | 0.493 | 0.597 | 0.687 | 0.925 | 0.993 | 0.522 | 0.716 | 0.918 |
|  | macro piece_recall | 0.516 | 0.633 | 0.742 | 0.952 | 0.996 | 0.543 | 0.761 | 0.943 |
|  | micro piece_recall | 0.482 | 0.618 | 0.724 | 0.925 | 0.995 | 0.528 | 0.749 | 0.930 |

### Slice breakdown (BM25 macro complete)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 81 | 0.457 | 0.667 | 0.716 | 0.802 | 0.938 | 0.481 | 0.691 | 0.877 |
| multi_evidence | 53 | 0.208 | 0.377 | 0.434 | 0.566 | 0.849 | 0.226 | 0.415 | 0.623 |
| cross_page_true | 20 | 0.000 | 0.250 | 0.300 | 0.400 | 0.750 | 0.050 | 0.300 | 0.400 |
| cross_page_false | 114 | 0.421 | 0.605 | 0.658 | 0.763 | 0.930 | 0.439 | 0.632 | 0.842 |
| explicit | 91 | 0.451 | 0.692 | 0.758 | 0.835 | 0.945 | 0.484 | 0.736 | 0.857 |
| derived | 43 | 0.163 | 0.256 | 0.279 | 0.442 | 0.814 | 0.163 | 0.256 | 0.605 |

## OCR layer

### OCR

| Method | Metric | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
|---|---|---|---|---|---|---|---|---|---|
| BM25 | macro complete | 0.373 | 0.530 | 0.597 | 0.701 | 0.910 | 0.381 | 0.582 | 0.769 |
|  | macro piece_recall | 0.397 | 0.541 | 0.611 | 0.727 | 0.922 | 0.402 | 0.598 | 0.798 |
|  | micro piece_recall | 0.347 | 0.487 | 0.573 | 0.698 | 0.920 | 0.357 | 0.558 | 0.779 |
| Naive order | macro complete | 0.493 | 0.597 | 0.687 | 0.925 | 0.993 | 0.522 | 0.716 | 0.896 |
|  | macro piece_recall | 0.516 | 0.633 | 0.742 | 0.952 | 0.996 | 0.543 | 0.746 | 0.940 |
|  | micro piece_recall | 0.482 | 0.618 | 0.724 | 0.925 | 0.995 | 0.528 | 0.729 | 0.920 |

### Slice breakdown (BM25 macro complete)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 81 | 0.481 | 0.630 | 0.667 | 0.778 | 0.938 | 0.481 | 0.667 | 0.852 |
| multi_evidence | 53 | 0.208 | 0.377 | 0.491 | 0.585 | 0.868 | 0.226 | 0.453 | 0.642 |
| cross_page_true | 20 | 0.000 | 0.250 | 0.300 | 0.400 | 0.800 | 0.050 | 0.300 | 0.400 |
| cross_page_false | 114 | 0.439 | 0.579 | 0.649 | 0.754 | 0.930 | 0.439 | 0.632 | 0.833 |
| explicit | 91 | 0.462 | 0.670 | 0.736 | 0.824 | 0.956 | 0.473 | 0.736 | 0.846 |
| derived | 43 | 0.186 | 0.233 | 0.302 | 0.442 | 0.814 | 0.186 | 0.256 | 0.605 |

## Interpretation

BM25 achieves moderate piece-level recall but struggles with strict complete-evidence retrieval. Complete@3 is low because multi-evidence instances require all pages to be retrieved, and BM25 ranks pages independently without awareness of coverage. Cross-page instances are harder than single-page ones. The naive page-order baseline is surprisingly competitive on some metrics, suggesting that evidence often appears early in SDS documents. Native and OCR layers perform similarly, with OCR slightly lagging on fine-grained matches.
