# S5 — real extraction cases and the error taxonomy (smoke)

Case = `(document, field)` (both text layers and all five S4 methods live inside one case). Gold v1.3, dev split. Scored with `sdsbench.evaluator` (7 axes + joint). S4 predictions are a frozen input.

## Selection (deterministic)

- seed = 42; dev pairs = 140
- hard pool = 5 pairs (pairs whose slices include any of derived/cross_page/multi_evidence and where at least one method fails the 7-axis joint on at least one layer); **sampled 5**
- controls = 6 from 135 remaining pairs (seed=42, disjoint from hard)
- hard primary slices: {'derived': 2, 'cross_page': 1, 'multi_evidence': 2}
- control primary slices: {'single_evidence': 5, 'unknown': 1}
- deterministic: **True**

## Taxonomy over 11 cases

| category | total | hard | control |
| --- | ---: | ---: | ---: |
| annotations | 0 | 0 | 0 |
| entity attribution | 0 | 0 | 0 |
| reasoning | 3 | 2 | 1 |
| values | 0 | 0 | 0 |
| evidence | 3 | 3 | 0 |
| none | 5 | 0 | 5 |

## Which methods solve which category

A method *solves* a case when it passes joint on **both** layers; `(none)` marks cases no simple method solves (the gap).

| category | M1 | M2 | M3 | M4 | M5 | (none) |
|---|---|---|---|---|---|---|
| annotations | 0 | 0 | 0 | 0 | 0 | 0 |
| entity attribution | 0 | 0 | 0 | 0 | 0 | 0 |
| reasoning | 0 | 0 | 0 | 2 | 0 | 1 |
| values | 0 | 0 | 0 | 0 | 0 | 0 |
| evidence | 1 | 0 | 1 | 2 | 1 | 1 |
| none | 0 | 0 | 0 | 0 | 0 | 5 |

## Cost per method x layer (from *.meta.json)

| method | layer | backend | n calls | prompt tok | completion tok | latency s |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| M1 | native | mlx | 1 | 8747 | 952 | 35.507 |
| M1 | ocr | mlx | 1 | 8610 | 1101 | 37.341 |
| M2 | native | mlx | 8 | 64458 | 689 | 141.574 |
| M2 | ocr | mlx | 8 | 63362 | 390 | 134.273 |
| M3 | native | mlx | 7 | 9781 | 255 | 23.554 |
| M3 | ocr | mlx | 7 | 9251 | 291 | 23.822 |
| M4 | native | rules | 0 | 0 | 0 | 0.0 |
| M4 | ocr | rules | 0 | 0 | 0 | 0.0 |
| M5 | native | mlx | 7 | 1174 | 7 | 3.04 |
| M5 | ocr | mlx | 7 | 1279 | 7 | 2.552 |

## Unresolved cases (no simple method solves them)

| case | document | field | taxonomy |
| ---: | --- | --- | --- |
| 4 | sds_05.pdf | product_name | evidence |
| 7 | sds_05.pdf | product_cas_number | reasoning |

## Cases

### Case 1 — `sds_05.pdf` / `chemical_formula` (hard, primary slice `derived`)

- **Slices:** [derived, multi_evidence] · evidence-set 2
- **Gold:** state `NOT_APPLICABLE`, value `None`, derivation `ONTOLOGY`, rule `identifier_undefined_for_form`, page(s) [2]
- **Taxonomy:** **reasoning** · actual_error: _reasoning (derived)_
- **Cause:** located 0/1 required premise role(s)
- **solved_by:** ['M4']
- **min_cost_solved:** M4: 0.0s 0 LLM calls · **min_cost_llm_solved:** —
- **reference failure:** `M1` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M2 | ✘ state,value,page,span,bbox,derivation,support | ✘ state,page,span,bbox,derivation,support |
| M3 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M4 | ✔ | ✔ |
| M5 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |

### Case 2 — `sds_05.pdf` / `flash_point` (hard, primary slice `cross_page`)

- **Slices:** [cross_page, multi_evidence] · evidence-set 2
- **Gold:** state `PRESENT`, value `>225°C (437°F) [ASTM D-92]`, derivation `EXPLICIT`, page(s) [3, 7]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** cited page 5 vs gold page(s) [3, 7]; span IoU 0.0 / coverage 0.0 below threshold; bbox IoU 0.0 / coverage 0.0 below threshold; cited quote is not verbatim on its page; support: citation is not verbatim
- **solved_by:** ['M1', 'M3', 'M4', 'M5']
- **min_cost_solved:** M4: 0.0s 0 LLM calls · **min_cost_llm_solved:** M5: 5.6s 14 calls, 2453→14 tok
- **reference failure:** `M2` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✔ | ✔ |
| M2 | ✘ page,span,bbox,support | ✔ |
| M3 | ✔ | ✔ |
| M4 | ✔ | ✔ |
| M5 | ✔ | ✔ |

### Case 3 — `sds_05.pdf` / `molecular_weight` (hard, primary slice `derived`)

- **Slices:** [derived, multi_evidence] · evidence-set 2
- **Gold:** state `NOT_APPLICABLE`, value `None`, derivation `ONTOLOGY`, rule `identifier_undefined_for_form`, page(s) [2]
- **Taxonomy:** **reasoning** · actual_error: _reasoning (derived)_
- **Cause:** located 0/1 required premise role(s)
- **solved_by:** ['M4']
- **min_cost_solved:** M4: 0.0s 0 LLM calls · **min_cost_llm_solved:** —
- **reference failure:** `M1` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M2 | ✘ state,value,page,span,bbox,derivation,support | ✘ state,page,span,bbox,derivation,support |
| M3 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M4 | ✔ | ✔ |
| M5 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |

### Case 4 — `sds_05.pdf` / `product_name` (hard, primary slice `multi_evidence`)

- **Slices:** [multi_evidence] · evidence-set 2
- **Gold:** state `PRESENT`, value `MOBIL SHC PM 220`, derivation `EXPLICIT`, page(s) [1]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** bbox IoU 0.6404 / coverage 0.6404 below threshold
- **solved_by:** — (gap: no simple method solves it)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **reference failure:** `M4` on `ocr`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✔ | ✘ bbox |
| M2 | ✘ value,span,bbox | ✘ bbox |
| M3 | ✔ | ✘ bbox |
| M4 | ✔ | ✘ bbox |
| M5 | ✔ | ✘ bbox |

### Case 5 — `sds_05.pdf` / `substance_or_mixture` (hard, primary slice `multi_evidence`)

- **Slices:** [multi_evidence] · evidence-set 2
- **Gold:** state `PRESENT`, value `MIXTURE`, derivation `EXPLICIT`, page(s) [2]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** cited page 1 vs gold page(s) [2]; span IoU 0.0 / coverage 0.0 below threshold; bbox IoU 0.0 / coverage 0.0 below threshold; support: cited span declares no product form
- **solved_by:** ['M4']
- **min_cost_solved:** M4: 0.0s 0 LLM calls · **min_cost_llm_solved:** —
- **reference failure:** `M1` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M2 | ✘ value,page,span,bbox,support | ✘ value,page,span,bbox,support |
| M3 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M4 | ✔ | ✔ |
| M5 | ✘ state,value,page,span,bbox | ✘ state,value,page,span,bbox |

### Case 6 — `sds_01.pdf` / `supplier_name` (control, primary slice `single_evidence`)

- **Slices:** [single_evidence] · evidence-set 1
- **Gold:** state `PRESENT`, value `SECILTEK SA`, derivation `EXPLICIT`, page(s) [1]
- **Taxonomy:** **none** · actual_error: _none (control)_
- **Cause:** all methods pass joint on both layers
- **solved_by:** — (control; no error to solve)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **coverage:** partial — some method x layer cells were not scored

| method | native | ocr |
| --- | --- | --- |
| M1 | · | · |
| M2 | · | · |
| M3 | · | · |
| M4 | · | · |
| M5 | · | · |

### Case 7 — `sds_05.pdf` / `product_cas_number` (control, primary slice `single_evidence`)

- **Slices:** [single_evidence] · evidence-set 1
- **Gold:** state `NOT_APPLICABLE`, value `None`, derivation `EXPLICIT`, page(s) [2]
- **Taxonomy:** **reasoning** · actual_error: _reasoning (derivation)_
- **Cause:** gold is a direct (EXPLICIT) claim but the prediction declares DERIVED with rule 'identifier_undefined_for_form'
- **solved_by:** — (gap: no simple method solves it)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **reference failure:** `M4` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ page,span,bbox,derivation,support | ✘ page,span,bbox,derivation,support |
| M2 | ✘ state,value,page,span,bbox,support | ✘ state,page,span,bbox,support |
| M3 | ✘ page,span,bbox,derivation,support | ✘ page,span,bbox,derivation,support |
| M4 | ✘ derivation | ✘ derivation |
| M5 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |

### Case 8 — `sds_06.pdf` / `substance_or_mixture` (control, primary slice `unknown`)

- **Slices:** [] · evidence-set 0
- **Gold:** state `NOT_STATED`, value `None`, derivation `ABSENT`, page(s) []
- **Taxonomy:** **none** · actual_error: _none (control)_
- **Cause:** all methods pass joint on both layers
- **solved_by:** — (control; no error to solve)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **coverage:** partial — some method x layer cells were not scored

| method | native | ocr |
| --- | --- | --- |
| M1 | · | · |
| M2 | · | · |
| M3 | · | · |
| M4 | · | · |
| M5 | · | · |

### Case 9 — `sds_09.pdf` / `supplier_name` (control, primary slice `single_evidence`)

- **Slices:** [single_evidence] · evidence-set 1
- **Gold:** state `PRESENT`, value `MACHEREY-NAGEL GmbH & Co. KG`, derivation `EXPLICIT`, page(s) [1]
- **Taxonomy:** **none** · actual_error: _none (control)_
- **Cause:** all methods pass joint on both layers
- **solved_by:** — (control; no error to solve)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **coverage:** partial — some method x layer cells were not scored

| method | native | ocr |
| --- | --- | --- |
| M1 | · | · |
| M2 | · | · |
| M3 | · | · |
| M4 | · | · |
| M5 | · | · |

### Case 10 — `sds_10.pdf` / `product_name` (control, primary slice `single_evidence`)

- **Slices:** [single_evidence] · evidence-set 1
- **Gold:** state `PRESENT`, value `CIP Composites`, derivation `EXPLICIT`, page(s) [1]
- **Taxonomy:** **none** · actual_error: _none (control)_
- **Cause:** all methods pass joint on both layers
- **solved_by:** — (control; no error to solve)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **coverage:** partial — some method x layer cells were not scored

| method | native | ocr |
| --- | --- | --- |
| M1 | · | · |
| M2 | · | · |
| M3 | · | · |
| M4 | · | · |
| M5 | · | · |

### Case 11 — `sds_11.pdf` / `substance_or_mixture` (control, primary slice `single_evidence`)

- **Slices:** [single_evidence] · evidence-set 1
- **Gold:** state `PRESENT`, value `MIXTURE`, derivation `EXPLICIT`, page(s) [2]
- **Taxonomy:** **none** · actual_error: _none (control)_
- **Cause:** all methods pass joint on both layers
- **solved_by:** — (control; no error to solve)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **coverage:** partial — some method x layer cells were not scored

| method | native | ocr |
| --- | --- | --- |
| M1 | · | · |
| M2 | · | · |
| M3 | · | · |
| M4 | · | · |
| M5 | · | · |

