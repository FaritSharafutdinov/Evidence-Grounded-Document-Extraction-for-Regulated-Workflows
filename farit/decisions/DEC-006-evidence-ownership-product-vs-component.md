# DEC-006 — Evidence ownership: product-level vs component-level premises (kit/multipart)

**Date:** 2026-10-23 · **Status:** decided (Farit)

**Context.** Аудит TASK-016 (по просьбе профа, steering note 2026-10-22 п.2) проверил gold
sds_18 на product/component ownership. `sds_18.pdf` — **kit/multipart product**: титул (p1–2)
явно объявляет «This product is a kit or a multipart product which consists of multiple,
independently packaged components»; далее идут две полные SDS компонентов: Part A (p3–14) и
Part B (p15–24). Находка: product-level form-выводы (`substance_or_mixture = MIXTURE` и
NOT_APPLICABLE-идентификаторы CAS/формула/MW) обосновывались **premise из состава компонента
Part A (p5)** — то есть компонентное evidence использовалось для product-level claim.

**Decision.**

1. **Premise ownership.** Product-level выводы должны опираться на **product-level evidence**.
   Для sds_18 premise переносится с p5 (состав Part A) на p1 (kit-декларация с титула).
2. **Форма kit-продукта.** В онтологии нет формы KIT/MULTIPART; набор моделируется как
   **MIXTURE** (ближайшая доступная форма). Введение новой формы — отвергнуто на этом этапе
   (правка read-only инфраструктуры Марии; противоречит «no complex new architecture»).
3. **Покрытие компонентов.** Для kit-документа аннотируется **один компонент** (Part A) для
   `ingredients`; evidence `product_name`/`supplier_name` не расширяется на Part B. Политика
   «один компонент» сохраняется.

**Alternatives considered.** (a) `product_form = UNDETERMINED` (kit ≠ mixture) — отклонено:
`field_is_defined_for(UNDETERMINED)=True` заставляет CAS/формулу/MW стать NOT_STATED (теряются
product-level выводы и premise p1); плюс NOT_STATED не несёт evidence → решение о premise
обнуляется. (b) Новая форма KIT/MULTIPART в онтологии — отклонено как выходящее за текущую зону
(`sdsbench/` read-only). (c) Оставить p5-заголовок состава — отклонено: это и есть ownership-нарушение.

**Consequences.** Gold v1.3 (TASK-017): sds_18 premise p5→p1 для 4 полей; `gold_evidence` — 4
изменённых записи, n_included 134 (без изменений); 4 инстанса multi_evidence→single_evidence;
max |Δ| BM25/dense ≈ 0.07 (срез derived). Ограничение чекера: p1 kit-текст не распознаётся
реестром правил как `form_declaration` → sds_18 поля попадают в информационный список
`unverifiable` (не PROBLEM). Задача: TASK-017 (K3).