# Changelog — gold annotations

## v1.1 — 2026-10-21/22 (DEC-005, TASK-013)

Исправления по результатам аудита TASK-011 и решений Farit'а (DEC-005). Источник:
`data/annotations/source/`, регенерация `gold.json` — `python -m scripts.build_annotations`.

### Исправлено

- **sds_10** — пропущенное явное объявление ARTICLE (стр. 1, OSHA 29 CFR 1910.1200(b)(6)(v)):
  `product_form` UNDETERMINED→ARTICLE; `substance_or_mixture` NOT_STATED→PRESENT/ARTICLE
  (evidence: обе цитаты стр. 1); `product_cas_number`, `chemical_formula`,
  `molecular_weight` NOT_STATED→NOT_APPLICABLE/ONTOLOGY (premise — то же объявление).
- **sds_17** — внутренняя несогласованность: `molecular_weight` NOT_STATED→
  NOT_APPLICABLE/ONTOLOGY (CAS и формула уже были N/A от того же premise).
- **sds_19** — химическая интерпретация по политике DEC-005 п.1 («Concrete Admixture» =
  смесь): `product_cas_number`, `chemical_formula`, `molecular_weight`
  NOT_STATED→NOT_APPLICABLE/ONTOLOGY (premise: «General Use: Concrete Admixture», стр. 1).
- **sds_03** — missed-evidence: в `substance_or_mixture` добавлен спан стр. 5
  («As the product is a mixture of several substances, …»). Побочный эффект механизма
  premise: этот спан также стал premise для ONTOLOGY-полей MW/формулы того же документа.
- **sds_12** — расширение evidence `product_name` по политике DEC-005 п.2 (помеченные
  шапки = evidence): «Trade name: Westland Bone Meal» добавлен для всех 10 страниц
  (проверено дословно на каждой).

### Известные остатки (сознательные)

- **sds_19**: `product_form` остаётся UNDETERMINED, `substance_or_mixture` — NOT_STATED
  (DEC-005 санкционирует только form-зависимые поля). Из-за этого
  `scripts.build_annotations` печатает 3 consistency-предупреждения («ONTOLOGY derivation
  but the field is defined for UNDETERMINED»). Когерентное завершение (form→MIXTURE) —
  отдельное решение Farit'а.
- **sds_24** (locked): одна bbox-координата `product_name` отличается от прежнего
  gold.json в 7-м знаке (0.28680340137357024 → 0.2868034263062321) — float-шум ресолвера
  bbox (окружение/PyMuPDF), воспроизводится стабильно. Контент (страница, спан, char
  offsets) не изменён; locked-разметка по смыслу не тронута; на метрики не влияет
  (bbox в retrieval-метриках не используется).
- **sds_06**: проверен и оставлен NOT_STATED (категория использования не задаёт форму
  однозначно) — решение Farit'а 2026-10-21.

### Эффект на корпус и метрики

- `gold_evidence.jsonl`: 232 записи (без изменений по числу); state-распределение:
  PRESENT 111→112, NOT_APPLICABLE 62→69, NOT_STATED 21→13, NO_DATA 9; derivation:
  EXPLICIT 134→135, ONTOLOGY 44→51, ABSENT 21→13.
- `units_native/ocr.jsonl` — байт-в-байт идентичны (md5 сверен).
- Включённых в retrieval-оценку dev-инстансов: 125 → 133 (+8 — ровно затронутые поля).
- Дельта BM25/dense (gold v1.0 → v1.1): |Δ| ≤ 0.021 по всем macro/micro метрикам —
  выводы scouting-таблиц устойчивы. Новые числа: `farit/results/*_goldv11.{json,md}`;
  frozen-выходы (gold v1.0) сохранены без изменений.
