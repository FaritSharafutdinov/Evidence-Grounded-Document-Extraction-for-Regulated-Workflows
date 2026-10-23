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
| BM25 | macro complete | 0.358 | 0.552 | 0.612 | 0.724 | 0.918 | 0.381 | 0.582 | 0.791 |
|  | macro piece_recall | 0.383 | 0.564 | 0.626 | 0.749 | 0.933 | 0.402 | 0.590 | 0.820 |
|  | micro piece_recall | 0.344 | 0.513 | 0.579 | 0.723 | 0.938 | 0.364 | 0.544 | 0.800 |
| Naive order | macro complete | 0.522 | 0.627 | 0.716 | 0.925 | 0.993 | 0.552 | 0.746 | 0.918 |
|  | macro piece_recall | 0.546 | 0.662 | 0.771 | 0.952 | 0.996 | 0.573 | 0.791 | 0.943 |
|  | micro piece_recall | 0.513 | 0.651 | 0.759 | 0.923 | 0.995 | 0.559 | 0.785 | 0.928 |

### Slice breakdown (BM25 macro complete)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 85 | 0.435 | 0.635 | 0.694 | 0.788 | 0.929 | 0.459 | 0.659 | 0.859 |
| multi_evidence | 49 | 0.224 | 0.408 | 0.469 | 0.612 | 0.898 | 0.245 | 0.449 | 0.673 |
| cross_page_true | 20 | 0.000 | 0.250 | 0.300 | 0.400 | 0.750 | 0.050 | 0.300 | 0.400 |
| cross_page_false | 114 | 0.421 | 0.605 | 0.667 | 0.781 | 0.947 | 0.439 | 0.632 | 0.860 |
| explicit | 91 | 0.451 | 0.692 | 0.758 | 0.835 | 0.945 | 0.484 | 0.736 | 0.857 |
| derived | 43 | 0.163 | 0.256 | 0.302 | 0.488 | 0.860 | 0.163 | 0.256 | 0.651 |

## OCR layer

### OCR

| Method | Metric | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
|---|---|---|---|---|---|---|---|---|---|
| BM25 | macro complete | 0.373 | 0.530 | 0.612 | 0.716 | 0.925 | 0.381 | 0.582 | 0.784 |
|  | macro piece_recall | 0.397 | 0.541 | 0.626 | 0.742 | 0.937 | 0.402 | 0.598 | 0.813 |
|  | micro piece_recall | 0.354 | 0.497 | 0.595 | 0.723 | 0.944 | 0.364 | 0.569 | 0.805 |
| Naive order | macro complete | 0.522 | 0.627 | 0.716 | 0.925 | 0.993 | 0.552 | 0.746 | 0.896 |
|  | macro piece_recall | 0.546 | 0.662 | 0.771 | 0.952 | 0.996 | 0.573 | 0.776 | 0.940 |
|  | micro piece_recall | 0.513 | 0.651 | 0.759 | 0.923 | 0.995 | 0.559 | 0.764 | 0.918 |

### Slice breakdown (BM25 macro complete)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 85 | 0.459 | 0.600 | 0.659 | 0.765 | 0.929 | 0.459 | 0.635 | 0.835 |
| multi_evidence | 49 | 0.224 | 0.408 | 0.531 | 0.633 | 0.918 | 0.245 | 0.490 | 0.694 |
| cross_page_true | 20 | 0.000 | 0.250 | 0.300 | 0.400 | 0.800 | 0.050 | 0.300 | 0.400 |
| cross_page_false | 114 | 0.439 | 0.579 | 0.667 | 0.772 | 0.947 | 0.439 | 0.632 | 0.851 |
| explicit | 91 | 0.462 | 0.670 | 0.736 | 0.824 | 0.956 | 0.473 | 0.736 | 0.846 |
| derived | 43 | 0.186 | 0.233 | 0.349 | 0.488 | 0.860 | 0.186 | 0.256 | 0.651 |

## Interpretation

BM25 achieves moderate piece-level recall but struggles with strict complete-evidence retrieval. Complete@3 is low because multi-evidence instances require all pages to be retrieved, and BM25 ranks pages independently without awareness of coverage. Cross-page instances are harder than single-page ones. The naive page-order baseline is surprisingly competitive on some metrics, suggesting that evidence often appears early in SDS documents. Native and OCR layers perform similarly, with OCR slightly lagging on fine-grained matches.
