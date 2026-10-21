# Аудит gold-аннотаций (TASK-011, S2)

Выборочная проверка качества gold-разметки глазами, до любых выводов из метрик.
Аудит **ничего не исправляет** — только документирует. Источник сомнений: замечание
профессора (steering 2026-10-19, п.1): «Some labels, chemical assumptions, and evidence
definitions may be incorrect».

## Метод

- Сэмплер: `farit/src/analysis/annotation_audit_sample.py`, seed=42, детерминированный;
  только dev split (sds_01–sds_20), только product-поля (203 field-инстансов схемы;
  29 агрегатных строк `ingredients` не входят). Скелет заполнен вердиктами скриптом
  `farit/logs/TASK-011/apply_verdicts.py`: стадия 1 — ручные аудиторские вердикты K2
  (каждая цитата проверена дословно против `units_native.jsonl`), стадия 2 — оверлей
  решений Farit'а по эскалациям (DEC-005, 2026-10-21).
- Выборка: **40 записей** (A=8 EXPLICIT/PRESENT, B=8 ONTOLOGY, C=4 COMPOSITION_IMPLIED,
  D=10 missing-value: N/A 5 + NOT_STATED 3 + NO_DATA 2, E=10 PRESENT на полный просмотр
  документа, 10 разных документов; пересечения: E∩A=2, E∩C=1 — допустимы по спеке).
  Уникальных инстансов — 37 (K3-verified 2026-10-20). [K3-verify: правильно 37 — E∩A=2 и ещё E∩C=1 (sds_18/substance_or_mixture);
  49 фрагментов — подсчёт по записям, по уникальным инстансам 45; 0 битых ссылок в обоих подсчётах]
- Воркшиты аудита: `farit/logs/TASK-011/worksheet-*.txt`.
- Вердикты: `correct` / `incorrect` (с типом ошибки) / `questionable` (эскалация Farit'у).
  Каждый вердикт подкреплён цитатой (страница + дословный текст).

Воспроизведение:
```bash
~/ds_env/bin/python farit/src/analysis/annotation_audit_sample.py --dump   # скелет + воркшиты
~/ds_env/bin/python farit/logs/TASK-011/apply_verdicts.py                  # вердикты + решения Farit'а (DEC-005)
```

## Сводка

| Группа | n | correct | incorrect | questionable |
|--------|---|---------|-----------|--------------|
| A (EXPLICIT+PRESENT) | 8 | 8 | 0 | 0 |
| B (ONTOLOGY) | 8 | 8 | 0 | 0 |
| C (COMPOSITION_IMPLIED) | 4 | 4 | 0 | 0 |
| D (missing-value) | 10 | 8 | 2 | 0 |
| E (alternative evidence) | 10 | 8 | 2 | 0 |
| **Итого (записей)** | **40** | **36 (90%)** | **4 (10%)** | **0** |

Базовые аудиторские вердикты K2 (до решений): 34 correct / 2 incorrect / 4 questionable.
Четыре questionable решены Farit'ом (DEC-005, 2026-10-21): 2 → correct (gold адекватен),
2 → incorrect (gold несовместим с решённой политикой, исправление — у K3). Сигнал
«нужен химик-ревьюер» (>30%) не срабатывал и до, и после решений.

## Таблица вердиктов

❇ — вердикт пересмотрен решением Farit'а по эскалации (DEC-005, 2026-10-21); полный
провенанс — в notes соответствующей записи `annotation_audit.json`.

| Гр. | Документ | Поле | State | Deriv | Вердикт | Тип | Суть |
|-----|----------|------|-------|-------|---------|-----|------|
| A | sds_04 | supplier_name | PRESENT | EXPLICIT | correct | | цитата дословно, дистрибьютор = валидный субъект |
| A | sds_15 | substance_or_mixture | PRESENT | EXPLICIT | correct | | заголовок 3.2 Mixtures → MIXTURE |
| A | sds_09 | product_name | PRESENT | EXPLICIT | correct | | дословно, 1.1 |
| A | sds_08 | flash_point | PRESENT | EXPLICIT | correct | | 120 °C, SECTION 9, продукт |
| A | sds_03 | flash_point | PRESENT | EXPLICIT | correct | | дословно; значение — утверждение, не температура (нюанс, см. паттерн 4) |
| A | sds_17 | substance_or_mixture | PRESENT | EXPLICIT | correct | | OSHA «article» → ARTICLE |
| A | sds_19 | supplier_name | PRESENT | EXPLICIT | correct | | дословно, 1.3 |
| A | sds_11 | product_name | PRESENT | EXPLICIT | correct | | дословно, 1.1 |
| B | sds_02 | chemical_formula | N/A | ONTOLOGY | correct | | «Preparation» → смесь → N/A |
| B | sds_11 | molecular_weight | N/A | ONTOLOGY | correct | | 3.1 Not applicable → смесь → N/A |
| B | sds_14 | product_cas_number | N/A | ONTOLOGY | correct | | вакцина = смесь; CAS ингредиентов не перепутаны |
| B | sds_17 | product_cas_number | N/A | ONTOLOGY | correct | | article → N/A; CAS ингредиента (8052-42-4) не взят |
| B | sds_01 | chemical_formula | N/A | ONTOLOGY | correct | | 3.1 Non-applicable → смесь |
| B | sds_15 | molecular_weight | N/A | ONTOLOGY | correct | | смесь → N/A |
| B | sds_12 | chemical_formula | N/A | ONTOLOGY | correct | | 3.1 N/A → смесь |
| B | sds_02 | product_cas_number | N/A | ONTOLOGY | correct | | preparation → N/A |
| C | sds_04 | substance_or_mixture | PRESENT | COMP.IMPL. | correct | | один компонент 100%, без примесей → SUBSTANCE |
| C | sds_09 | substance_or_mixture | PRESENT | COMP.IMPL. | correct | | несколько веществ + «for the mixtures» |
| C | sds_18 | substance_or_mixture | PRESENT | COMP.IMPL. | correct | | таблица ингредиентов + «the mixture» |
| C | sds_20 | substance_or_mixture | PRESENT | COMP.IMPL. | correct | | UVCB-остаток из нескольких сырей → MIXTURE |
| D | sds_20 | molecular_weight | N/A | ONTOLOGY | correct | | смесь → N/A |
| D | sds_07 | molecular_weight | N/A | ONTOLOGY | correct | | тонер = смесь → N/A |
| D | sds_15 | chemical_formula | N/A | ONTOLOGY | correct | | смесь → N/A |
| D | sds_03 | product_cas_number | N/A | EXPLICIT | correct | | 3.1 Non-applicable → смесь |
| D | sds_07 | product_cas_number | N/A | ONTOLOGY | correct | | CAS Fe2O3 (ингредиент) не взят |
| D | sds_13 | chemical_formula | NOT_STATED | ABSENT | correct | | формы нет нигде в 11 страницах; SUBSTANCE объявлен |
| D | sds_10 | molecular_weight | NOT_STATED | ABSENT | **incorrect** | wrong-state | документ явно объявляет ARTICLE → должно быть N/A |
| D | sds_19 | product_cas_number | NOT_STATED | ABSENT | **incorrect** ❇ | wrong-state | по DEC-005 п.1: admixture = смесь → CAS N/A; было questionable |
| D | sds_15 | flash_point | NO_DATA | EXPLICIT | correct | | «No data available» дословно |
| D | sds_16 | flash_point | NO_DATA | EXPLICIT | correct | | «No information available» дословно (нюанс: твёрдое вещество) |
| E | sds_03 | substance_or_mixture | PRESENT | EXPLICIT | **incorrect** | missed-evidence | на стр. 5 прямое «product is a mixture of several substances» вне gold |
| E | sds_09 | product_name | PRESENT | EXPLICIT | correct ❇ | | по DEC-005 п.2: имя в шапке БЕЗ метки — просто строка, gold адекватен; было questionable |
| E | sds_18 | substance_or_mixture | PRESENT | COMP.IMPL. | correct | | альтернатив нет; ложный ARTICLE от «Article Information Sheet» |
| E | sds_12 | product_name | PRESENT | EXPLICIT | **incorrect** ❇ | missed-evidence | по DEC-005 п.2: шапка С меткой («Trade name:») — evidence; было questionable |
| E | sds_13 | supplier_name | PRESENT | EXPLICIT | correct | | единственное вхождение — gold-спан |
| E | sds_04 | product_cas_number | PRESENT | EXPLICIT | correct | | CAS один раз, в gold; продукт = вещество 100% |
| E | sds_01 | flash_point | PRESENT | EXPLICIT | correct | | единственное упоминание — gold-спан |
| E | sds_19 | supplier_name | PRESENT | EXPLICIT | correct ❇ | | по DEC-005 п.3: упоминание в disclaimer — не evidence; было questionable |
| E | sds_05 | flash_point | PRESENT | EXPLICIT | correct | | оба вхождения (стр. 3, 7) в gold |
| E | sds_16 | molecular_weight | PRESENT | EXPLICIT | correct | | единственное вхождение — gold-спан |

## Показательные примеры ошибок

### 1. sds_10 / molecular_weight — wrong-state (пропущено явное объявление ARTICLE)

sds_10 (CIP Composites) — «Alternative Documentation to a Safety Data Sheet», стр. 1:

> «**Designation of ‘ARTICLES’** … **In accordance with 29 CFR 1910.1200(b)(6)(v), CIP
> Composites are exempted as an “Article”**, and therefore, do not require an SDS be
> created or provided to end users.»

Gold: `molecular_weight = NOT_STATED (ABSENT)`. Но форма продукта объявлена явно →
по онтологии (`defined_for_forms=(SUBSTANCE,)`) ожидается `NOT_APPLICABLE (ONTOLOGY)`.
Прецедент внутри самого gold: sds_17 с идентичной формулировкой («defined by OSHA as an
“article”») аннотирован `substance_or_mixture=ARTICLE`, и его `product_cas_number` /
`chemical_formula` — `N/A ONTOLOGY` от того же premise.

**Вне выборки (найдено при аудите sds_10, требует решения Farit'а):** в sds_10 то же
объявление пропущено для всех полей — `substance_or_mixture=NOT_STATED` (ожидалось
PRESENT/ARTICLE), `product_cas_number` и `chemical_formula=NOT_STATED` (ожидалось N/A).
И обратная несогласованность в sds_17: `molecular_weight=NOT_STATED`, хотя у
CAS/формулы тот же premise и то же `defined_for_forms` → ожидалось N/A.

### 2. sds_03 / substance_or_mixture — missed-evidence (валидное evidence вне gold)

Gold evidence_set: стр. 2 «Chemical description: Mixture of polymers, dispersants and
organic compounds» + стр. 1 «Substance: Non-applicable». Но на стр. 5 (секция 8):

> «**As the product is a mixture of several substances**, the resistance of the glove
> material can not be calculated in advance with total reliability…»

Это прямое субстантивное объявление формы продукта, вне evidence_set (плюс заголовок
«3.2 Mixture:» на стр. 1). Система, цитирующая стр. 5, пройдёт gold-free проверку
support, но получит штраф по локализации → complete@k занижается несправедливо.

### 3. sds_09 / sds_12 / product_name — колонтитулы (решено: DEC-005 п.2)

Имя продукта стоит в шапке/колонтитуле **каждой** из 10 страниц обоих документов, но
шапки разные: у sds_09 — немеченая строка («REF: 920163 / VISOCOLOR HE Nitrite, refill
pack»), у sds_12 — с явной меткой («Trade name: Westland Bone Meal»). По букве
критерия support (name-substring) обе поддерживают значение; по смыслу это
повторяющийся boilerplate.

Решение Farit'а (DEC-005 п.2): помеченная строка = валидное evidence → gold sds_12
расширяется на все 10 страниц (исправление — K3); немеченая строка = просто строка →
gold sds_09 адекватен. Остаточный риск, вне решения: gold-free критерий support
оценщика всё ещё принимает немеченые строки — системы, цитирующие шапку sds_09,
по-прежнему пройдут support и будут оштрафованы по локализации.

### 4. sds_03 / flash_point — форма значения (нюанс, не ошибка)

Значение `flash_point = 'Non Flammable (>60 ºC)'` — не температура, а
классификационное утверждение документа. Лексикон онтологии не классифицирует «Non
Flammable» как NOT_APPLICABLE-cue, поэтому PRESENT консистентен с правилами схемы и
верен документу. Но для value_kind=TEMPERATURE такое значение проходит только через
fallback-ветку substring-сравнения — стоит иметь в виду при интерпретации метрик.

## Паттерны ошибок

1. **Form-зависимые N/A применены неконсистентно** (главный источник реальных ошибок):
   sds_10 — явное объявление ARTICLE пропущено, все поля NOT_STATED; sds_17 — N/A для
   CAS/формулы, но NOT_STATED для MW при том же premise. Затронуты 2 документа из 20
   dev (10%), в выборке — 1 инстанс, вне выборки — ещё 4.
2. **Неполный evidence_set у PRESENT-инстансов**: субстантивное объявление смеси на
   стр. 5 sds_03 не включено → занижение complete@k.
3. **Политика boilerplate была не определена → определена DEC-005**: помеченные
   («Trade name: …») шапки = evidence (gold sds_12 расширяется у K3), немеченые = не
   evidence (gold sds_09 адекватен); упоминание поставщика в disclaimer — не evidence
   (DEC-005 п.3). До фикса gold критерий support оценщика всё ещё принимает boilerplate.
4. **Значения-утверждения в TEMPERATURE-полях** («Non Flammable (>60 ºC)») — документ-верны,
   но ломают числовое сравнение (обходит через substring-fallback).

## Что в gold хорошо (важно для выводов из метрик)

- **0 broken-evidence-ref**: все 49 проверенных фрагментов evidence_set (по 40 записям;
  45 уникальных по 37 инстансам — K3-verified 2026-10-20) найдены дословно на указанных
  страницах native-слоя.
- **Product-vs-ingredient — чисто**: CAS ингредиентов никогда не взят как CAS продукта
  (sds_02, sds_07, sds_14, sds_17); CAS из таблицы композиции корректно использован как
  CAS продукта только там, где продукт = единственное вещество при 100% (sds_04).
- **ONTOLOGY-выводы (13/13 в выборке)**: все premise дословны, химия корректна
  (смесь/статья/препарация → N/A для полей вещества).
- **NO_DATA/NOT_STATED в основном документ-верны** (кроме sds_10): state читается из
  value slot документа, без домыслов.

## Решения Farit'а (эскалации решены, DEC-005 от 2026-10-21)

| # | Инстанс | Решение | Следствие |
|---|---------|---------|-----------|
| 1 | sds_19 / product_cas_number = NOT_STATED | **NOT_APPLICABLE**: категория использования («Concrete Admixture») однозначно задаёт смесь → form-зависимые поля N/A | gold несовместим с решённой политикой → incorrect/wrong-state; объём применения правила (все однозначные категории vs только sds_19/sds_10) — открытый вопрос для K3 |
| 2 | sds_09 / product_name | Немеченая строка в шапке = просто строка, не evidence | gold адекватен (канонический 1.1); уточнение критерия support оценщика — отдельное будущее решение |
| 3 | sds_12 / product_name | Шапка с явной меткой («Trade name: …») = валидное evidence, расширить gold | gold неполон → incorrect/missed-evidence; фикс — K3 (все 10 страниц) |
| 4 | sds_19 / supplier_name | Критерий «представлен как поставщик», а не «назван где угодно»; упоминание в disclaimer — не evidence | gold адекватен (1.3) |

Исправления gold переданы K3 (Farit, 2026-10-21): (a) sds_10 — все 4 form-зависимых
поля по явному объявлению ARTICLE; (b) sds_17 — molecular_weight; (c) sds_03 /
substance_or_mixture — добавить стр. 5 в evidence_set; (d) sds_12 / product_name —
расширить gold помеченными шапками; плюс объёмные вопросы из п.1/п.2 DEC-005. После
фикса — пересборка корпуса.

## Влияние на метрики (качественно)

- **complete@k / piece_recall**: минимум 1 инстанс (sds_03 substance_or_mixture) с
  гарантированным несправедливым штрафом до фикса gold; sds_12 product_name — по
  решённой политике (помеченные шапки) gold неполон, фикс — K3; при непересмотренном
  критерии support системы, цитирующие boilerplate, всё ещё штрафуются по локализации.
- **state-axis**: sds_10 (4 поля) и sds_19 product_cas_number (по DEC-005 п.1) —
  система, предсказавшая химически правильный N/A, засчитывается как ошибка против
  NOT_STATED gold до фикса; sds_17 MW — симметрично.
- 90% выборки correct (после решений) → выводы из метрик по dev split допустимы, кроме
  form-зависимых полей у документов с необъявленной/неявной формой — до фикса gold (K3).

## Ограничения аудита

- Выборка 40 записей (37 уникальных инстансов из 140 dev product-инстанцов, ~26%) —
  точечная, не исчерпывающая; locked split не проверялся (запрещён).
- Химические суждения — уровня K2 (на базе онтологии проекта и общих знаний), не
  профессионального химика; спорные случаи вынесены в эскалации, не решались самовольно.
- E-просмотр искал альтернативы по критериям спеки поля (support: value-in-span /
  form-cue); boilerplate-паттерны задокументированы как политика-вопрос.
