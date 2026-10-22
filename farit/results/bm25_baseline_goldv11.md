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
- Excluded (empty evidence_set): 7
- Excluded (NOT_STATED / no evidence required): 0
- **Included in metrics**: 133

## Sanity checks

- A1: `sds_01.pdf` / `product_name` page 1 rank in native: **2**

## Native layer

### Native

| Method | Metric | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
|---|---|---|---|---|---|---|---|---|---|
| BM25 | macro complete | 0.353 | 0.549 | 0.602 | 0.707 | 0.902 | 0.376 | 0.579 | 0.774 |
|  | macro piece_recall | 0.378 | 0.560 | 0.616 | 0.732 | 0.917 | 0.397 | 0.587 | 0.803 |
|  | micro piece_recall | 0.333 | 0.500 | 0.561 | 0.697 | 0.914 | 0.354 | 0.530 | 0.773 |
| Naive order | macro complete | 0.489 | 0.594 | 0.684 | 0.925 | 0.992 | 0.519 | 0.714 | 0.917 |
|  | macro piece_recall | 0.513 | 0.630 | 0.740 | 0.951 | 0.996 | 0.540 | 0.759 | 0.942 |
|  | micro piece_recall | 0.480 | 0.616 | 0.722 | 0.924 | 0.995 | 0.525 | 0.747 | 0.929 |

### Slice breakdown (BM25 macro complete)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 80 | 0.450 | 0.662 | 0.713 | 0.800 | 0.938 | 0.475 | 0.688 | 0.875 |
| multi_evidence | 53 | 0.208 | 0.377 | 0.434 | 0.566 | 0.849 | 0.226 | 0.415 | 0.623 |
| cross_page_true | 20 | 0.000 | 0.250 | 0.300 | 0.400 | 0.750 | 0.050 | 0.300 | 0.400 |
| cross_page_false | 113 | 0.416 | 0.602 | 0.655 | 0.761 | 0.929 | 0.434 | 0.628 | 0.841 |
| explicit | 90 | 0.444 | 0.689 | 0.756 | 0.833 | 0.944 | 0.478 | 0.733 | 0.856 |
| derived | 43 | 0.163 | 0.256 | 0.279 | 0.442 | 0.814 | 0.163 | 0.256 | 0.605 |

## OCR layer

### OCR

| Method | Metric | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
|---|---|---|---|---|---|---|---|---|---|
| BM25 | macro complete | 0.368 | 0.526 | 0.594 | 0.699 | 0.910 | 0.376 | 0.579 | 0.767 |
|  | macro piece_recall | 0.393 | 0.538 | 0.609 | 0.725 | 0.921 | 0.397 | 0.595 | 0.796 |
|  | micro piece_recall | 0.343 | 0.485 | 0.571 | 0.697 | 0.919 | 0.354 | 0.556 | 0.778 |
| Naive order | macro complete | 0.489 | 0.594 | 0.684 | 0.925 | 0.992 | 0.519 | 0.714 | 0.895 |
|  | macro piece_recall | 0.513 | 0.630 | 0.740 | 0.951 | 0.996 | 0.540 | 0.744 | 0.939 |
|  | micro piece_recall | 0.480 | 0.616 | 0.722 | 0.924 | 0.995 | 0.525 | 0.727 | 0.919 |

### Slice breakdown (BM25 macro complete)

| Slice | n | @1 | @2 | @3 | @5 | @10 | @500tok | @1000tok | @2000tok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_evidence | 80 | 0.475 | 0.625 | 0.662 | 0.775 | 0.938 | 0.475 | 0.662 | 0.850 |
| multi_evidence | 53 | 0.208 | 0.377 | 0.491 | 0.585 | 0.868 | 0.226 | 0.453 | 0.642 |
| cross_page_true | 20 | 0.000 | 0.250 | 0.300 | 0.400 | 0.800 | 0.050 | 0.300 | 0.400 |
| cross_page_false | 113 | 0.434 | 0.575 | 0.646 | 0.752 | 0.929 | 0.434 | 0.628 | 0.832 |
| explicit | 90 | 0.456 | 0.667 | 0.733 | 0.822 | 0.956 | 0.467 | 0.733 | 0.844 |
| derived | 43 | 0.186 | 0.233 | 0.302 | 0.442 | 0.814 | 0.186 | 0.256 | 0.605 |

## Interpretation

BM25 achieves moderate piece-level recall but struggles with strict complete-evidence retrieval. Complete@3 is low because multi-evidence instances require all pages to be retrieved, and BM25 ranks pages independently without awareness of coverage. Cross-page instances are harder than single-page ones. The naive page-order baseline is surprisingly competitive on some metrics, suggesting that evidence often appears early in SDS documents. Native and OCR layers perform similarly, with OCR slightly lagging on fine-grained matches.
