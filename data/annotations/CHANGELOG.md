# Changelog — gold annotations

## v1.3 — 2026-10-23 (TASK-016/017, ownership-фикс sds_18)

Устранение evidence-ownership нарушения в sds_18 (аудит TASK-016, решение Farit'а: пакет A).
Источник: `data/annotations/source/`, регенерация `gold.json` — `python -m scripts.build_annotations`.

### Исправлено

- **sds_18** (kit/multipart product) — product-level form-выводы были обоснованы **premise из
  состава компонента Part A (стр. 5, заголовок «Ingredient C.A.S. No. % by Wt»)**. Заменено на
  **product-level kit-декларацию с титула** (стр. 1, дословно): «This product is a kit or a
  multipart product which consists of multiple, independently packaged components.»
  - `substance_or_mixture` (COMPOSITION_IMPLIED/MIXTURE): evidence `[p5 header, p5 «35% of the
    mixture…»]` → `[p1 kit]`.
  - `product_cas_number` / `chemical_formula` / `molecular_weight` (NOT_APPLICABLE/ONTOLOGY):
    premise `p5 header` → `p1 kit`. Форма остаётся **MIXTURE** (в онтологии нет формы KIT/MULTIPART;
    пакет A — минимальный ownership-фикс без правки инфраструктуры Марии).

### Не менялось

- Состояния/значения полей sds_18 не изменены; `ingredients` — по-прежнему только Part A (p5),
  политика «один компонент»; locked не тронут.

### Эффект

- `scripts/build_annotations` — **0 PROBLEM(S)**. Информационный список `unverifiable` вырос
  6→10: реестр правил больше не распознаёт premise sds_18 как `form_declaration` (p1 kit-текст не
  матчится детектором декларации формы, в отличие от p5-заголовка состава) — это ограничение
  чекера, не дефект gold.
- `gold_evidence.jsonl`: 232 записи (число не изменилось), **изменены 4 записи** (sds_18:
  substance_or_mixture + 3 identifier) — gold-страница p5 → p1. Из-за сокращения premise-множества
  эти 4 инстанса перешли **multi_evidence → single_evidence** (срез: single 81→85, multi 53→49).
- Включённых dev-инстансов: **134 → 134** (без изменений).
- `units_native/ocr.jsonl` — байт-в-байт (md5 сверен).
- Дельта BM25/dense (v1.2 → v1.3): max |Δ| = **0.065** (BM25) / **0.070** (dense), сосредоточена в
  срезе `derived` (4 поля sds_18 — все derived) и на щедрых бюджетах; знаки смешанные.
  Headline native macro complete@3: BM25 0.604→**0.612**, dense 0.634→0.627, naive 0.687→**0.716**
  (naive/BM25 выросли из-за multi→single переклассификации). Новые числа:
  `farit/results/*_goldv13.{json,md}`; frozen и `*_goldv12` сохранены. **Рабочий gold для S4 — v1.3.**

## v1.2 — 2026-10-23 (DEC-005 п.1, TASK-014)

Когерентное завершение интерпретации sds_19 (единственный оставшийся artifact-gold
остаток от v1.1). Источник: `data/annotations/source/`, регенерация `gold.json` —
`python -m scripts.build_annotations`.

### Исправлено

- **sds_19** — `product_form` UNDETERMINED→MIXTURE и `substance_or_mixture`
  NOT_STATED/ABSENT→PRESENT/EXPLICIT/MIXTURE (evidence: `«General Use: Concrete Admixture»`,
  стр. 1 — та же строка, что у identifier-полей → дедуп по `EvidenceRef.key` не меняет
  их premises). Обоснование — DEC-005 п.1 (admixture = смесь). Механика: `ONTOLOGY`
  запрещён для PRESENT-поля, а `COMPOSITION_IMPLIED` требует premise-роли состава
  (таблицы состава у sds_19 нет → правило не верифицируется), поэтому derivation
  EXPLICIT с note, документирующей политическую интерпретацию.

### Эффект

- `scripts/build_annotations` — **0 PROBLEM(S)** (было 3 варнинга «ONTOLOGY derivation
  but the field is defined for UNDETERMINED»). Убраны именно варнинги консистентности;
  информационный список `unverifiable` по sds_19 (3 поля) существовал и в v1.1 — не регрессия.
- `gold_evidence.jsonl`: 232 записи (число не изменилось — запись = инстанс поля, лишь
  наполнение sds_19/substance_or_mixture). State: NOT_STATED 13→12, EXPLICIT 135→136;
  ABSENT 12, ONTOLOGY 51. Фрагментов: 277→278 (+1 evidence).
- Включённых dev-инстансов retrieval-оценки: 133 → **134** (+1 — sds_19 substance_or_mixture).
- `units_native/ocr.jsonl` — байт-в-байт идентичны (md5 сверен).
- Дельта BM25/dense (gold v1.1 → v1.2): max |Δ| по всем metric-ячейкам = **0.0069** (вверх);
  headline native macro complete@3: BM25 0.602→0.604, dense 0.632→0.634, naive 0.684→0.687.
  Новые числа: `farit/results/*_goldv12.{json,md}`; frozen-выходы (gold v1.0) и `*_goldv11`
  сохранены без изменений. Рабочий gold для батареи S4 — **v1.2**.

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
