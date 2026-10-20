# Аудит gold-аннотаций (TASK-011, S2)

Выборочная проверка качества gold-разметки глазами, до любых выводов из метрик.
Аудит **ничего не исправляет** — только документирует. Источник сомнений: замечание
профессора (steering 2026-10-19, п.1): «Some labels, chemical assumptions, and evidence
definitions may be incorrect».

## Метод

- Сэмплер: `farit/src/analysis/annotation_audit_sample.py`, seed=42, детерминированный;
  только dev split (sds_01–sds_20), только product-поля (203 field-инстансов схемы;
  29 агрегатных строк `ingredients` не входят). Скелет заполнен вердиктами скриптом
  `farit/logs/TASK-011/apply_verdicts.py` (вердикты — ручные суждения K2, каждая цитата
  проверена дословно против `units_native.jsonl`).
- Выборка: **40 записей** (A=8 EXPLICIT/PRESENT, B=8 ONTOLOGY, C=4 COMPOSITION_IMPLIED,
  D=10 missing-value: N/A 5 + NOT_STATED 3 + NO_DATA 2, E=10 PRESENT на полный просмотр
  документа, 10 разных документов; E∩A = 2 инстанса — допустимо по спеке). Уникальных
  инстансов — 38. [K3-verify: правильно 37 — E∩A=2 и ещё E∩C=1 (sds_18/substance_or_mixture);
  49 фрагментов — подсчёт по записям, по уникальным инстансам 45; 0 битых ссылок в обоих подсчётах]
- Воркшиты аудита: `farit/logs/TASK-011/worksheet-*.txt`.
- Вердикты: `correct` / `incorrect` (с типом ошибки) / `questionable` (эскалация Farit'у).
  Каждый вердикт подкреплён цитатой (страница + дословный текст).

Воспроизведение:
```bash
~/ds_env/bin/python farit/src/analysis/annotation_audit_sample.py --dump   # скелет + воркшиты
~/ds_env/bin/python farit/logs/TASK-011/apply_verdicts.py                  # вердикты
```

## Сводка

| Группа | n | correct | incorrect | questionable |
|--------|---|---------|-----------|--------------|
| A (EXPLICIT+PRESENT) | 8 | 8 | 0 | 0 |
| B (ONTOLOGY) | 8 | 8 | 0 | 0 |
| C (COMPOSITION_IMPLIED) | 4 | 4 | 0 | 0 |
| D (missing-value) | 10 | 8 | 1 | 1 |
| E (alternative evidence) | 10 | 6 | 1 | 3 |
| **Итого (записей)** | **40** | **34 (85%)** | **2 (5%)** | **4 (10%)** |

Questionable = 10% < 30% → сигнал «нужен химик-ревьюер» не срабатывает, но эскалации есть (ниже).

## Таблица вердиктов

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
| D | sds_19 | product_cas_number | NOT_STATED | ABSENT | **questionable** | | форма не объявлена; химически admixture = смесь → N/A? |
| D | sds_15 | flash_point | NO_DATA | EXPLICIT | correct | | «No data available» дословно |
| D | sds_16 | flash_point | NO_DATA | EXPLICIT | correct | | «No information available» дословно (нюанс: твёрдое вещество) |
| E | sds_03 | substance_or_mixture | PRESENT | EXPLICIT | **incorrect** | missed-evidence | на стр. 5 прямое «product is a mixture of several substances» вне gold |
| E | sds_09 | product_name | PRESENT | EXPLICIT | **questionable** | | имя в колонтитуле каждой из 10 страниц — политика? |
| E | sds_18 | substance_or_mixture | PRESENT | COMP.IMPL. | correct | | альтернатив нет; ложный ARTICLE от «Article Information Sheet» |
| E | sds_12 | product_name | PRESENT | EXPLICIT | **questionable** | | «Trade name: Westland Bone Meal» в шапке всех 10 страниц |
| E | sds_13 | supplier_name | PRESENT | EXPLICIT | correct | | единственное вхождение — gold-спан |
| E | sds_04 | product_cas_number | PRESENT | EXPLICIT | correct | | CAS один раз, в gold; продукт = вещество 100% |
| E | sds_01 | flash_point | PRESENT | EXPLICIT | correct | | единственное упоминание — gold-спан |
| E | sds_19 | supplier_name | PRESENT | EXPLICIT | **questionable** | | компания названа в disclaimer на стр. 7 вне gold |
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

### 3. sds_09 / product_name — колонтитулы (политика)

Имя продукта стоит в колонтитуле **каждой** из 10 страниц: «REF: 920163 / VISOCOLOR HE
Nitrite, refill pack». Gold — только спан в 1.1. По букве критерия support
(name-substring) колонтитул поддерживает значение; по смыслу это повторяющийся
boilerplate. Если считать — complete@k для product_name вырождается («валидна любая
страница»); если не считать — системы, цитирующие колонтитул, несправедливо штрафуются.
Нужна явная политика (см. эскалации). То же для sds_12 («Trade name: Westland Bone
Meal» в шапке всех страниц) и sds_19 (название компании в legal disclaimer, стр. 7).

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
3. **Политика boilerplate не определена**: колонтитулы/шапки/disclaimer поддерживают
   значения по букве критерия support, но не включены в gold (3 инстанса из 10
   E-просмотров).
4. **Значения-утверждения в TEMPERATURE-полях** («Non Flammable (>60 ºC)») — документ-верны,
   но ломают числовое сравнение (обходит через substring-fallback).

## Что в gold хорошо (важно для выводов из метрик)

- **0 broken-evidence-ref**: все 49 проверенных фрагментов evidence_set (по всем 40
  записям) найдены дословно на указанных страницах native-слоя.
- **Product-vs-ingredient — чисто**: CAS ингредиентов никогда не взят как CAS продукта
  (sds_02, sds_07, sds_14, sds_17); CAS из таблицы композиции корректно использован как
  CAS продукта только там, где продукт = единственное вещество при 100% (sds_04).
- **ONTOLOGY-выводы (13/13 в выборке)**: все premise дословны, химия корректна
  (смесь/статья/препарация → N/A для полей вещества).
- **NO_DATA/NOT_STATED в основном документ-верны** (кроме sds_10): state читается из
  value slot документа, без домыслов.

## Эскалации Farit'у (questionable, 4)

| # | Инстанс | Сомнение | Варианты |
|---|---------|----------|----------|
| 1 | sds_19 / product_cas_number = NOT_STATED | Форма в документе не объявлена; химически «Concrete Admixture» = смесь → CAS должен быть N/A | (a) оставить NOT_STATED — документ-верно; (b) N/A — химическая интерпретация |
| 2 | sds_09 / product_name | Имя в колонтитуле всех 10 страниц; support-критерий его принимает, gold — нет | (a) расширить gold колонтитулами; (b) исключить boilerplate из support-критерия; (c) принять каноническую политику gold (только 1.1) и задокументировать |
| 3 | sds_12 / product_name | «Trade name: Westland Bone Meal» в шапке всех 10 страниц | те же варианты, что №2 |
| 4 | sds_19 / supplier_name | Компания названа в legal disclaimer (стр. 7) вне gold | (a) считать evidence; (b) не считать (только идентификация поставщика в 1.3) |

Плюс 2 зафиксированных incorrect (sds_10 molecular_weight wrong-state; sds_03
substance_or_mixture missed-evidence) и вне-выборочные наблюдения по sds_10 (4 поля) и
sds_17 (molecular_weight) — см. «Показательные примеры» №1.

## Влияние на метрики (качественно)

- **complete@k / piece_recall**: минимум 1 инстанс (sds_03 substance_or_mixture) с
  гарантированным несправедливым штрафом; при политике «колонтитулы = evidence» таких
  станет заметно больше (каждый multi-page doc с повторяющимся именем).
- **state-axis**: sds_10 (4 поля) — система, предсказавшая химически правильный N/A,
  засчитывается как ошибка против NOT_STATED gold; sds_17 MW — симметрично.
- 85% выборки correct → выводы из метрик по dev split в целом можно делать, но
  form-зависимые поля (product_cas_number, chemical_formula, molecular_weight у
  article/mixture-документов с необъявленной формой) несут систематический риск.

## Ограничения аудита

- Выборка 40 записей (38 уникальных инстансов из 140 dev product-инстанцов, ~27%) —
  точечная, не исчерпывающая; locked split не проверялся (запрещён).
- Химические суждения — уровня K2 (на базе онтологии проекта и общих знаний), не
  профессионального химика; спорные случаи вынесены в эскалации, не решались самовольно.
- E-просмотр искал альтернативы по критериям спеки поля (support: value-in-span /
  form-cue); boilerplate-паттерны задокументированы как политика-вопрос.
