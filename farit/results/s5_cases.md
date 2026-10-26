# S5 — real extraction cases and the error taxonomy

Case = `(document, field)` (both text layers and all five S4 methods live inside one case). Gold v1.3, dev split. Scored with `sdsbench.evaluator` (7 axes + joint). S4 predictions are a frozen input.

## Selection (deterministic)

- seed = 42; dev pairs = 140
- hard pool = 67 pairs (pairs whose slices include any of derived/cross_page/multi_evidence and where at least one method fails the 7-axis joint on at least one layer); **sampled 18**
- controls = 6 from 122 remaining pairs (seed=42, disjoint from hard)
- hard primary slices: {'multi_evidence': 4, 'derived': 10, 'cross_page': 4}
- control primary slices: {'single_evidence': 4, 'unknown': 1, 'derived': 1}
- deterministic: **True**

## Taxonomy over 24 cases

| category | total | hard | control |
| --- | ---: | ---: | ---: |
| annotations | 0 | 0 | 0 |
| entity attribution | 0 | 0 | 0 |
| reasoning | 9 | 8 | 1 |
| values | 1 | 0 | 1 |
| evidence | 14 | 10 | 4 |
| none | 0 | 0 | 0 |

## Which methods solve which category

A method *solves* a case when it passes joint on **both** layers; `(none)` marks cases no simple method solves (the gap).

| category | M1 | M2 | M3 | M4 | M5 | M6 | (none) |
|---|---|---|---|---|---|---|---|
| annotations | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| entity attribution | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| reasoning | 0 | 0 | 0 | 4 | 0 | 0 | 5 |
| values | 0 | 1 | 0 | 1 | 1 | 0 | 0 |
| evidence | 0 | 0 | 0 | 7 | 0 | 2 | 7 |
| none | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Cost per method x layer (from *.meta.json)

| method | layer | backend | n calls | prompt tok | completion tok | latency s |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| M1 | native | openai | 20 | 149276 | 15517 | 0.0 |
| M1 | ocr | openai | 20 | 146859 | 14319 | 0.0 |
| M2 | native | openai | 160 | 1083168 | 15565 | 0.0 |
| M2 | ocr | openai | 160 | 1063832 | 12448 | 195.71 |
| M3 | native | openai | 139 | 215974 | 4951 | 121.7 |
| M3 | ocr | openai | 139 | 206390 | 4523 | 112.206 |
| M4 | native | rules | 0 | 0 | 0 | 0.0 |
| M4 | ocr | rules | 0 | 0 | 0 | 0.0 |
| M5 | native | openai | 139 | 22713 | 278 | 13.228 |
| M5 | ocr | openai | 139 | 22617 | 278 | 9.396 |
| M6 | native | openai | 160 | 524870 | 13647 | 308.736 |
| M6 | ocr | openai | 160 | 515801 | 12640 | 284.044 |

## Unresolved cases (no simple method solves them)

| case | document | field | taxonomy |
| ---: | --- | --- | --- |
| 8 | sds_07.pdf | chemical_formula | evidence |
| 9 | sds_09.pdf | substance_or_mixture | reasoning |
| 10 | sds_10.pdf | product_cas_number | reasoning |
| 12 | sds_11.pdf | molecular_weight | reasoning |
| 13 | sds_12.pdf | molecular_weight | evidence |
| 14 | sds_14.pdf | substance_or_mixture | evidence |
| 15 | sds_16.pdf | chemical_formula | evidence |
| 18 | sds_20.pdf | substance_or_mixture | reasoning |
| 19 | sds_01.pdf | product_cas_number | reasoning |
| 20 | sds_03.pdf | product_name | evidence |
| 22 | sds_07.pdf | flash_point | evidence |
| 23 | sds_14.pdf | product_cas_number | evidence |

## Cases

### Case 1 — `sds_01.pdf` / `substance_or_mixture` (hard, primary slice `multi_evidence`)

- **Slices:** [multi_evidence] · evidence-set 2
- **Gold:** state `PRESENT`, value `MIXTURE`, derivation `EXPLICIT`, page(s) [1]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** span IoU 0.2 / coverage 1.0 below threshold; bbox IoU 0.0826 / coverage 1.0 below threshold
- **solved_by:** ['M4']
- **min_cost_solved:** M4: 0.0s 0 LLM calls · **min_cost_llm_solved:** —
- **reference failure:** `M1` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ span,bbox | ✘ span,bbox,support |
| M2 | ✘ state,value,page,span,bbox | ✘ state,value,page,span,bbox |
| M3 | ✘ span,bbox | ✘ state,value,page,span,bbox |
| M4 | ✔ | ✔ |
| M5 | ✘ span,bbox | ✘ state,value,page,span,bbox |
| M6 | ✘ state,value,page,span,bbox | ✘ state,value,page,span,bbox |

### Case 2 — `sds_02.pdf` / `chemical_formula` (hard, primary slice `derived`)

- **Slices:** [derived, single_evidence] · evidence-set 1
- **Gold:** state `NOT_APPLICABLE`, value `None`, derivation `ONTOLOGY`, rule `identifier_undefined_for_form`, page(s) [4]
- **Taxonomy:** **reasoning** · actual_error: _reasoning (derived)_
- **Cause:** located 0/1 required premise role(s)
- **solved_by:** ['M4']
- **min_cost_solved:** M4: 0.0s 0 LLM calls · **min_cost_llm_solved:** —
- **reference failure:** `M1` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ page,span,bbox,support | ✘ page,span,bbox |
| M2 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M3 | ✘ page,span,bbox,support | ✘ page,span,bbox |
| M4 | ✔ | ✔ |
| M5 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M6 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |

### Case 3 — `sds_02.pdf` / `product_cas_number` (hard, primary slice `derived`)

- **Slices:** [derived, single_evidence] · evidence-set 1
- **Gold:** state `NOT_APPLICABLE`, value `None`, derivation `ONTOLOGY`, rule `identifier_undefined_for_form`, page(s) [4]
- **Taxonomy:** **reasoning** · actual_error: _reasoning (derived)_
- **Cause:** located 0/1 required premise role(s)
- **solved_by:** ['M4']
- **min_cost_solved:** M4: 0.0s 0 LLM calls · **min_cost_llm_solved:** —
- **reference failure:** `M1` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ page,span,bbox,support | ✘ page,span,bbox |
| M2 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M3 | ✘ page,span,bbox,support | ✘ page,span,bbox |
| M4 | ✔ | ✔ |
| M5 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M6 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |

### Case 4 — `sds_03.pdf` / `molecular_weight` (hard, primary slice `derived`)

- **Slices:** [derived, cross_page, multi_evidence] · evidence-set 3
- **Gold:** state `NOT_APPLICABLE`, value `None`, derivation `ONTOLOGY`, rule `identifier_undefined_for_form`, page(s) [1, 2, 5]
- **Taxonomy:** **reasoning** · actual_error: _reasoning (derived)_
- **Cause:** rule None vs gold 'identifier_undefined_for_form'; derivation DIRECT vs gold DERIVED; located 0/1 required premise role(s)
- **solved_by:** ['M4']
- **min_cost_solved:** M4: 0.0s 0 LLM calls · **min_cost_llm_solved:** —
- **reference failure:** `M2` on `ocr`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ span,bbox,support | ✘ span,bbox,support |
| M2 | ✔ | ✘ state,span,bbox,derivation,support |
| M3 | ✘ span,bbox,support | ✘ span,bbox,support |
| M4 | ✔ | ✔ |
| M5 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M6 | ✘ state,span,bbox,derivation,support | ✘ state,span,bbox,derivation,support |

### Case 5 — `sds_03.pdf` / `substance_or_mixture` (hard, primary slice `cross_page`)

- **Slices:** [cross_page, multi_evidence] · evidence-set 3
- **Gold:** state `PRESENT`, value `MIXTURE`, derivation `EXPLICIT`, page(s) [1, 2, 5]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** span IoU 0.0 / coverage 0.0 below threshold; bbox IoU 0.0 / coverage 0.0 below threshold; support: cited span declares no product form
- **solved_by:** ['M4']
- **min_cost_solved:** M4: 0.0s 0 LLM calls · **min_cost_llm_solved:** —
- **reference failure:** `M1` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ span,bbox,support | ✘ span,bbox,support |
| M2 | ✘ value,support | ✘ state,value,page,span,bbox |
| M3 | ✘ span,bbox,support | ✘ span,bbox,support |
| M4 | ✔ | ✔ |
| M5 | ✘ span,bbox,support | ✘ state,value,page,span,bbox |
| M6 | ✘ value,span,bbox,support | ✘ state,value,page,span,bbox |

### Case 6 — `sds_04.pdf` / `substance_or_mixture` (hard, primary slice `derived`)

- **Slices:** [derived, multi_evidence] · evidence-set 2
- **Gold:** state `PRESENT`, value `SUBSTANCE`, derivation `COMPOSITION_IMPLIED`, rule `composition_implies_form`, page(s) [2]
- **Taxonomy:** **reasoning** · actual_error: _reasoning (derived)_
- **Cause:** rule None vs gold 'composition_implies_form'; derivation DIRECT vs gold DERIVED; located 0/2 required premise role(s)
- **solved_by:** ['M4']
- **min_cost_solved:** M4: 0.0s 0 LLM calls · **min_cost_llm_solved:** —
- **reference failure:** `M1` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ page,span,bbox,derivation,support | ✘ page,span,bbox,derivation,support |
| M2 | ✘ value,page,span,bbox,derivation,support | ✘ value,page,span,bbox,derivation,support |
| M3 | ✘ page,span,bbox,derivation,support | ✘ page,span,bbox,derivation,support |
| M4 | ✔ | ✔ |
| M5 | ✘ state,value,page,span,bbox | ✘ state,value,page,span,bbox |
| M6 | ✘ value,span,bbox,derivation,support | ✘ value,span,bbox,derivation,support |

### Case 7 — `sds_05.pdf` / `substance_or_mixture` (hard, primary slice `multi_evidence`)

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
| M2 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M3 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M4 | ✔ | ✔ |
| M5 | ✘ state,value,page,span,bbox | ✘ state,value,page,span,bbox |
| M6 | ✘ value,page,span,bbox,support | ✘ state,value,page,span,bbox |

### Case 8 — `sds_07.pdf` / `chemical_formula` (hard, primary slice `derived`)

- **Slices:** [derived, multi_evidence] · evidence-set 2
- **Gold:** state `NOT_APPLICABLE`, value `None`, derivation `ONTOLOGY`, rule `identifier_undefined_for_form`, page(s) [1]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** bbox IoU 0.5466 / coverage 0.5466 below threshold
- **solved_by:** — (gap: no simple method solves it)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **reference failure:** `M4` on `ocr`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ derivation,support | ✘ bbox |
| M2 | ✘ state,bbox,derivation,support | ✘ state,bbox,derivation,support |
| M3 | ✘ derivation,support | ✘ bbox |
| M4 | ✔ | ✘ bbox |
| M5 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M6 | ✘ state,span,bbox,derivation | ✘ state,span,bbox,derivation |

### Case 9 — `sds_09.pdf` / `substance_or_mixture` (hard, primary slice `derived`)

- **Slices:** [derived, cross_page, multi_evidence] · evidence-set 2
- **Gold:** state `PRESENT`, value `MIXTURE`, derivation `COMPOSITION_IMPLIED`, rule `composition_implies_form`, page(s) [3, 6]  · **ambiguous**
- **Taxonomy:** **reasoning** · actual_error: _reasoning (derived)_
- **Cause:** no derived conclusion produced (prediction is NOT_STATED); located 0/1 required premise role(s)
- **solved_by:** — (gap: no simple method solves it)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **reference failure:** `M4` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ page,span,bbox,derivation,support | ✘ page,span,bbox,derivation,support |
| M2 | ✘ state,value,page,span,bbox | ✘ state,value,page,span,bbox |
| M3 | ✘ page,span,bbox,derivation,support | ✘ page,span,bbox,derivation,support |
| M4 | ✘ state,value,page,span,bbox | ✘ state,value,page,span,bbox |
| M5 | ✘ state,value,page,span,bbox | ✘ state,value,page,span,bbox |
| M6 | ✘ state,value,page,span,bbox | ✘ state,value,page,span,bbox |

### Case 10 — `sds_10.pdf` / `product_cas_number` (hard, primary slice `derived`)

- **Slices:** [derived, multi_evidence] · evidence-set 2
- **Gold:** state `NOT_APPLICABLE`, value `None`, derivation `ONTOLOGY`, rule `identifier_undefined_for_form`, page(s) [1]
- **Taxonomy:** **reasoning** · actual_error: _reasoning (derived)_
- **Cause:** no derived conclusion produced (prediction is NOT_STATED); located 0/1 required premise role(s)
- **solved_by:** — (gap: no simple method solves it)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **reference failure:** `M4` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ span,bbox,support | ✘ span,bbox,support |
| M2 | ✘ span,bbox,support | ✘ state,page,span,bbox |
| M3 | ✘ span,bbox | ✘ state,page,span,bbox |
| M4 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M5 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M6 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |

### Case 11 — `sds_11.pdf` / `flash_point` (hard, primary slice `multi_evidence`)

- **Slices:** [multi_evidence] · evidence-set 2
- **Gold:** state `NO_DATA`, value `None`, derivation `EXPLICIT`, page(s) [5]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** cited page 9 vs gold page(s) [5]; span IoU 0.0 / coverage 0.0 below threshold; bbox IoU 0.0 / coverage 0.0 below threshold; cited quote is not verbatim on its page; support: citation is not verbatim
- **solved_by:** ['M4', 'M6']
- **min_cost_solved:** M4: 0.0s 0 LLM calls · **min_cost_llm_solved:** M6: 33.3s 16 calls, 58420→1645 tok
- **reference failure:** `M1` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M2 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M3 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M4 | ✔ | ✔ |
| M5 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M6 | ✔ | ✔ |

### Case 12 — `sds_11.pdf` / `molecular_weight` (hard, primary slice `derived`)

- **Slices:** [derived, multi_evidence] · evidence-set 2
- **Gold:** state `NOT_APPLICABLE`, value `None`, derivation `ONTOLOGY`, rule `identifier_undefined_for_form`, page(s) [2]
- **Taxonomy:** **reasoning** · actual_error: _reasoning (derived)_
- **Cause:** located 0/1 required premise role(s)
- **solved_by:** — (gap: no simple method solves it)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **reference failure:** `M4` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M2 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M3 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M4 | ✘ span,bbox | ✘ span,bbox |
| M5 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M6 | ✘ state,span,bbox,derivation,support | ✘ state,page,span,bbox,derivation,support |

### Case 13 — `sds_12.pdf` / `molecular_weight` (hard, primary slice `derived`)

- **Slices:** [derived, multi_evidence] · evidence-set 2
- **Gold:** state `NOT_APPLICABLE`, value `None`, derivation `ONTOLOGY`, rule `identifier_undefined_for_form`, page(s) [1]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** bbox IoU 0.6611 / coverage 0.6611 below threshold
- **solved_by:** — (gap: no simple method solves it)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **reference failure:** `M4` on `ocr`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ span,bbox,support | ✘ span,bbox,support |
| M2 | ✘ state,span,bbox,derivation,support | ✘ state,span,bbox,derivation,support |
| M3 | ✘ span,bbox,support | ✘ span,bbox,support |
| M4 | ✔ | ✘ bbox |
| M5 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M6 | ✘ state,page,span,bbox,derivation,support | ✘ state,span,bbox,derivation,support |

### Case 14 — `sds_14.pdf` / `substance_or_mixture` (hard, primary slice `multi_evidence`)

- **Slices:** [multi_evidence] · evidence-set 2
- **Gold:** state `PRESENT`, value `MIXTURE`, derivation `EXPLICIT`, page(s) [1]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** bbox IoU 0.5784 / coverage 0.5784 below threshold
- **solved_by:** — (gap: no simple method solves it)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **reference failure:** `M4` on `ocr`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M2 | ✘ value,support | ✘ value,bbox,support |
| M3 | ✘ state,value,page,span,bbox | ✘ state,value,page,span,bbox |
| M4 | ✔ | ✘ bbox |
| M5 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M6 | ✘ value,support | ✘ value,page,span,bbox,support |

### Case 15 — `sds_16.pdf` / `chemical_formula` (hard, primary slice `cross_page`)

- **Slices:** [cross_page, multi_evidence] · evidence-set 2
- **Gold:** state `PRESENT`, value `O2 Si`, derivation `EXPLICIT`, page(s) [1, 5]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** bbox IoU 0.6934 / coverage 0.6934 below threshold
- **solved_by:** — (gap: no simple method solves it)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **reference failure:** `M4` on `ocr`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✔ | ✘ bbox |
| M2 | ✔ | ✘ span,bbox,support |
| M3 | ✔ | ✘ bbox |
| M4 | ✔ | ✘ bbox |
| M5 | ✔ | ✘ bbox |
| M6 | ✔ | ✘ span,bbox,support |

### Case 16 — `sds_18.pdf` / `flash_point` (hard, primary slice `cross_page`)

- **Slices:** [cross_page, multi_evidence] · evidence-set 2
- **Gold:** state `PRESENT`, value `>=290 ºF [Test Method:Tagliabue Closed Cup]`, derivation `EXPLICIT`, page(s) [8, 19]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** cited page 1 vs gold page(s) [8, 19]; span IoU 0.0 / coverage 0.0 below threshold; bbox IoU 0.0 / coverage 0.0 below threshold; cited quote is not verbatim on its page; support: citation is not verbatim
- **solved_by:** ['M4', 'M6']
- **min_cost_solved:** M4: 0.0s 0 LLM calls · **min_cost_llm_solved:** M6: 37.3s 16 calls, 111073→1073 tok
- **reference failure:** `M1` on `ocr`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✔ | ✘ page,span,bbox,support |
| M2 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M3 | ✔ | ✘ state,value,page,span,bbox |
| M4 | ✔ | ✔ |
| M5 | ✔ | ✘ page,span,bbox,support |
| M6 | ✔ | ✔ |

### Case 17 — `sds_18.pdf` / `supplier_name` (hard, primary slice `cross_page`)

- **Slices:** [cross_page, multi_evidence] · evidence-set 2
- **Gold:** state `PRESENT`, value `3M`, derivation `EXPLICIT`, page(s) [1, 3]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** cited page 15 vs gold page(s) [1, 3]; span IoU 0.0 / coverage 0.0 below threshold; bbox IoU 0.0 / coverage 0.0 below threshold
- **solved_by:** ['M4']
- **min_cost_solved:** M4: 0.0s 0 LLM calls · **min_cost_llm_solved:** —
- **reference failure:** `M1` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ page,span,bbox | ✔ |
| M2 | ✔ | ✘ state,value,page,span,bbox |
| M3 | ✘ page,span,bbox | ✔ |
| M4 | ✔ | ✔ |
| M5 | ✘ page,span,bbox | ✔ |
| M6 | ✘ value | ✔ |

### Case 18 — `sds_20.pdf` / `substance_or_mixture` (hard, primary slice `derived`)

- **Slices:** [derived, single_evidence] · evidence-set 1
- **Gold:** state `PRESENT`, value `MIXTURE`, derivation `COMPOSITION_IMPLIED`, rule `composition_implies_form`, page(s) [3]  · **ambiguous**
- **Taxonomy:** **reasoning** · actual_error: _reasoning (derived)_
- **Cause:** no derived conclusion produced (prediction is NOT_STATED); located 0/1 required premise role(s)
- **solved_by:** — (gap: no simple method solves it)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **reference failure:** `M4` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ span,bbox,derivation,support | ✘ span,bbox,derivation,support |
| M2 | ✘ state,value,page,span,bbox | ✘ value,page,span,bbox,derivation,support |
| M3 | ✘ state,value,page,span,bbox | ✘ state,value,page,span,bbox |
| M4 | ✘ state,value,page,span,bbox | ✘ state,value,page,span,bbox |
| M5 | ✘ span,bbox,derivation,support | ✘ span,bbox,derivation,support |
| M6 | ✘ state,value,page,span,bbox | ✘ value,page,span,bbox,derivation,support |

### Case 19 — `sds_01.pdf` / `product_cas_number` (control, primary slice `single_evidence`)

- **Slices:** [single_evidence] · evidence-set 1
- **Gold:** state `NOT_APPLICABLE`, value `None`, derivation `EXPLICIT`, page(s) [1]
- **Taxonomy:** **reasoning** · actual_error: _reasoning (derivation)_
- **Cause:** gold is a direct (EXPLICIT) claim but the prediction declares DERIVED with rule 'identifier_undefined_for_form'
- **solved_by:** — (gap: no simple method solves it)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **reference failure:** `M4` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ span,bbox,derivation | ✘ span,bbox,derivation |
| M2 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M3 | ✘ span,bbox,derivation | ✘ span,bbox,derivation |
| M4 | ✘ span,bbox,derivation | ✘ span,bbox,derivation |
| M5 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M6 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |

### Case 20 — `sds_03.pdf` / `product_name` (control, primary slice `single_evidence`)

- **Slices:** [single_evidence] · evidence-set 1
- **Gold:** state `PRESENT`, value `STYCCOBOND F49 BASE`, derivation `EXPLICIT`, page(s) [1]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** bbox IoU 0.6481 / coverage 0.6481 below threshold
- **solved_by:** — (gap: no simple method solves it)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **reference failure:** `M4` on `ocr`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ span,bbox | ✘ bbox |
| M2 | ✔ | ✘ bbox |
| M3 | ✘ span,bbox | ✘ bbox |
| M4 | ✔ | ✘ bbox |
| M5 | ✘ span,bbox | ✘ bbox |
| M6 | ✔ | ✘ bbox |

### Case 21 — `sds_06.pdf` / `product_cas_number` (control, primary slice `unknown`)

- **Slices:** [] · evidence-set 0
- **Gold:** state `NOT_STATED`, value `None`, derivation `ABSENT`, page(s) []
- **Taxonomy:** **values** · actual_error: _value_
- **Cause:** predicted NOT_APPLICABLE/None vs gold NOT_STATED/None
- **solved_by:** ['M2', 'M4', 'M5']
- **min_cost_solved:** M2: 0.0s 16 calls, 103088→1189 tok · **min_cost_llm_solved:** M2: 0.0s 16 calls, 103088→1189 tok
- **reference failure:** `M1` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ state,support | ✘ state,support |
| M2 | ✔ | ✔ |
| M3 | ✘ state,support | ✘ state,support |
| M4 | ✔ | ✔ |
| M5 | ✔ | ✔ |
| M6 | ✘ state,support | ✘ state,support |

### Case 22 — `sds_07.pdf` / `flash_point` (control, primary slice `single_evidence`)

- **Slices:** [single_evidence] · evidence-set 1
- **Gold:** state `NOT_APPLICABLE`, value `None`, derivation `EXPLICIT`, page(s) [4]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** bbox IoU 0.6813 / coverage 0.6813 below threshold
- **solved_by:** — (gap: no simple method solves it)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **reference failure:** `M4` on `ocr`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M2 | ✘ state,page,span,bbox,support | ✘ state,page,span,bbox,support |
| M3 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M4 | ✔ | ✘ bbox |
| M5 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M6 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |

### Case 23 — `sds_14.pdf` / `product_cas_number` (control, primary slice `derived`)

- **Slices:** [derived, multi_evidence] · evidence-set 2
- **Gold:** state `NOT_APPLICABLE`, value `None`, derivation `ONTOLOGY`, rule `identifier_undefined_for_form`, page(s) [1]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** bbox IoU 0.5784 / coverage 0.5784 below threshold
- **solved_by:** — (gap: no simple method solves it)
- **min_cost_solved:** — · **min_cost_llm_solved:** —
- **reference failure:** `M4` on `ocr`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ page,span,bbox,support | ✘ page,span,bbox,support |
| M2 | ✘ state,derivation,support | ✘ state,page,span,bbox |
| M3 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M4 | ✔ | ✘ bbox |
| M5 | ✘ state,page,span,bbox | ✘ state,page,span,bbox |
| M6 | ✘ state,derivation,support | ✘ state,page,span,bbox |

### Case 24 — `sds_16.pdf` / `product_name` (control, primary slice `single_evidence`)

- **Slices:** [single_evidence] · evidence-set 1
- **Gold:** state `PRESENT`, value `Sand, Ottawa`, derivation `EXPLICIT`, page(s) [1]
- **Taxonomy:** **evidence** · actual_error: _evidence localization_
- **Cause:** span IoU 0.3333 / coverage 0.5 below threshold; bbox IoU 0.0 / coverage 0.0 below threshold; cited quote is not verbatim on its page; support: citation is not verbatim
- **solved_by:** ['M4']
- **min_cost_solved:** M4: 0.0s 0 LLM calls · **min_cost_llm_solved:** —
- **reference failure:** `M1` on `native`

| method | native | ocr |
| --- | --- | --- |
| M1 | ✘ span,bbox,support | ✘ span,bbox,support |
| M2 | ✘ bbox | ✘ bbox |
| M3 | ✘ state,value,page,span,bbox | ✘ state,value,page,span,bbox |
| M4 | ✔ | ✔ |
| M5 | ✘ span,bbox,support | ✘ span,bbox,support |
| M6 | ✘ state,value,page,span,bbox | ✘ state,value,page,span,bbox |

