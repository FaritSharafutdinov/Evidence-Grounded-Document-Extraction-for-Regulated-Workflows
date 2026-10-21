# DEC-005 — Аннотационная политика: headers как evidence, missing-value статусы, критерий supplier

**Date:** 2026-10-21 · **Status:** decided (Farit)

**Context.** TASK-011 (выборочный аудит gold-аннотаций, 40 записей / 37 уникальных
инстансов dev split [K3-verify: в исходной записи стояло 38 — верно 37, E∩A=2 и E∩C=1]) нашёл 2 подтверждённые ошибки gold и вынес Farit'у 4
questionable-эскалации — случаи, где факт установлен, а вердикт зависит от политики
разметки. Решения приняты Farit'ом 2026-10-21; аудиторские вердикты с оверлеем решений
пересчитаны в `farit/results/annotation_audit.json` (стадия RESOLUTIONS в
`farit/logs/TASK-011/apply_verdicts.py`). Исправление самого gold (правка
`data/annotations/`) — задача K3; аудит ничего не исправлял.

**Decision.**

1. **sds_19 / product_cas_number → NOT_APPLICABLE.** Когда категория использования
   продукта, названная в документе («General Use: Concrete Admixture»), однозначно
   задаёт форму продукта (admixture = смесь), form-зависимые поля (CAS, формула,
   молекулярный вес) получают NOT_APPLICABLE — химическая интерпретация разрешена,
   а не только дословные объявления формы.
   *Открытый вопрос объёма (для K3 при фиксе gold):* применять ли это правило ко всем
   NOT_STATED-инстансам form-зависимых полей, чья категория использования однозначна,
   или только к самим sds_19 и sds_10 (где к тому же есть явное объявление ARTICLE).
2. **Evidence для product_name / помеченные vs немеченые колонтитулы.** Повторяющаяся
   шапка страницы считается валидным evidence **только если строка явно помечена как
   имя** (например, «Trade name: Westland Bone Meal»); немеченая строка в шапке
   (например, «REF: 920163 / VISOCOLOR HE Nitrite, refill pack» в sds_09) — просто
   строка, не evidence, gold остаётся каноническим (секция 1.1). Расширение gold на
   помеченные шапки **документируется** (notes инстанса + фикс-лист K3).
   *Остаточный риск вне решения:* gold-free критерий support в оценщике всё ещё
   принимает немеченые строки (substring-сравнение); его уточнение — отдельное
   решение, не входящее в DEC-005.
3. **Критерий supplier_name: «представлен как поставщик», а не «назван где угодно».**
   Упоминание компании в юридическом disclaimer (sds_19, стр. 7: «use of this product
   is not within the control of Buddy Rhodes Concrete Products…») — не evidence;
   gold-спан идентификации в секции 1.3 адекватен.
4. **Обе подтверждённые ошибки gold переданы K3 на исправление** (аудит — read-only):
   (a) sds_10 — molecular_weight / substance_or_mixture / product_cas_number /
   chemical_formula: явное объявление ARTICLE (стр. 1, OSHA 29 CFR 1910.1200(b)(6)(v))
   пропущено; (b) sds_17 — molecular_weight: NOT_STATED при N/A у CAS/формулы с тем же
   premise (внутренняя несогласованность); (c) sds_03 / substance_or_mixture —
   missed-evidence: стр. 5 «As the product is a mixture of several substances…» не в
   evidence_set; (d) sds_12 / product_name — расширить gold на помеченные шапки
   («Trade name: Westland Bone Meal», все 10 страниц) по п.2 настоящего решения.

**Alternatives considered.** (a) Для sds_19 CAS: оставить NOT_STATED («строго то, что
написано») — отклонено: химию добавки в бетон как смеси можно считать частью
компетенции разметки, о чём и состоялось сомнение профессора. (b) Для колонтитулов:
включать все повторения в gold — отклонено: complete@k для product_name вырождается
(«правильно = любая страница»); исключить boilerplate из критерия support — отложено
как отдельное решение про оценщик. (c) Для supplier_name: считать упоминание в
disclaimer evidence — отклонено: это юридическая boilerplate-оговорка, а не
идентификация поставщика.

**Consequences.** Итог аудита после решений: correct 36/40 (90%), incorrect 4/40
(10%, все — конкретные дефекты gold с типом), questionable 0 (все решены). Пересмотр
метрик по dev split допустим, кроме form-зависимых полей у документов с необъявленной
формой — там до фикса gold (K3) метрики state-оси искажены. Фикс-лист для K3 — пункт 4
настоящего решения + объёмные открытые вопросы п.1/п.2; после фикса gold корпус
(`farit/data/corpus/gold_evidence.jsonl`) пересобирается, замороженные baseline-выходы
пересчитывать не нужно (они останутся только для истории — новые прогоны против
нового gold идут в новые файлы).

**Scope resolved (2026-10-21, Farit).** Открытые вопросы объёма закрыты: (1) правило
п.1 применяется ко **всем** form-зависимым полям документа — sds_19: CAS +
chemical_formula + molecular_weight → NOT_APPLICABLE; (2) sds_06 («Building materials,
wood pulp raw material, fuel, landscaping») под правило **не подпадает** — категория
использования не задаёт форму однозначно, поля остаются NOT_STATED; (3) после фикса
gold (v1.1) дешёвые baselines (BM25, dense) пересчитываются против нового gold в новые
файлы — чтобы таблица S4 была одногoldовой; frozen Qwen2.5-7B остаётся историей
(old-gold). Известный остаток: `substance_or_mixture` у sds_19 сознательно не меняется
(DEC-005 санкционирует только form-зависимые поля) — задокументировать в changelog.
Исполнение: TASK-013 (K3).
