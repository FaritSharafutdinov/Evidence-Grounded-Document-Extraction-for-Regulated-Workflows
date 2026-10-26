# Critic pass — M6 + канон-батарея 6 методов (пре-сейл гейт, неделя M1, вторая итерация)

- Дата: 2026-10-26. Модель критика: семейство, отличное от автора артефактов (по протоколу).
- Протокол: `critic-pass`. Изменён только этот файл.
- Объекты атаки: `s4_battery_goldv13.{json,md}`, `s5_cases.{json,md}`, `cost_accounting.{json,md}`, `state_anomaly.{json,md}`, `farit/src/extraction/methods.py` (M6), `farit/src/analysis/claims_audit.py` + `claims_audit.{json,md}`, доки `RESEARCH-STATE.md`, `report-2026-10-23.md`, `SPRINT.md`, `PACKAGE.md`, `DEC-007`, `EXP-06`, `logs/TASK-020/`, `tasks/TASK-021-m6-section-rules.md`, `tasks/BOARD.md`, `steering/reviews/2026-10-26-argon-teardown.md`.
- Рамка верификации критика: **без Bash** — только арифметика по committed JSON/MD и перекрёстные ссылки артефактов. Где пересчёт из raw (cache/meta/predictions, gitignored) невозможен — помечено «не верифицировано критиком».

## Резюме чисел, которые критик пересчитал сам (сошлось)

- 1236 = 20+20+160+160+139+139+0+0+139+139+160+160; prompt 3 951 500; completion 94 166; wall 1045.0; ALL 6960 / 17 410.5 — cost json/md ✓.
- **n_cached 386** независимо из двух committed-копий (cost_accounting.json:11-154 и s5_cases.json:274-431): 20+20+160+83+7+7+7+43+18+21 = 386 ✓; fresh 850 ✓; 31.2% ✓.
- Стыковка батарейных %-ов с инстансами: M1 native 0.18571×140 = **26**, M6 native 0.17857×140 = **25**, M6 ocr 12, M2 native 30, M5 native 29.
- state_anomaly 124/70/69 (native), 123/66/70 (ocr) = battery axes ×140 ✓; арифметика переходов (60+64=124 и т.д.) ✓.
- S5: taxonomy 14+9+1 = 24 ✓; gap = 12 ✓ (список unresolved: 8,9,10,12,13,14,15,18,19,20,22,23); «M6 solves 2 evidence» ✓ (кейсы 11, 16 — оба уже решались M4, т.е. **gap неизменен — подтверждено**); разложение хвоста 7 OCR-threshold + 2 gold.ambiguous (кейсы 9, 18) + 1 dispute (19) ✓ по строкам кейсов.
- Per-axis диапазоны «state 36–89, value 64–91, page 37–66, span 17–31, bbox 8–24» воспроизводятся из батареи по LLM-методам (M4 корректно исключён формулировкой «across the LLM methods» в RS:50), кроме округлений нижних границ — см. m5.
- M6 «halves prompt»: 524 870 / 1 083 168 = 48.5% ✓ (native; ocr 515 801 / 1 063 832 ✓).

---

## Findings

### Critical

**C1 (critical) — RS:55 «106/211 contract violations, all 20/20 docs» противоречит committed-артефакту и неверифицируема из репо.**
RESEARCH-STATE:55 (секция §3 «verified results»): «106 contract violations on the M1 native pass — claim_without_citation 54 + quote_not_verbatim 46 + derived_premise_set_incomplete 6; 211 summed over both layers, all 20/20 docs affected — `farit/data/predictions/s4_M1_*.meta.json`». Но **тот же счётчик в committed `s4_battery_goldv13.json` даёт другие значения**: M1/native `contract_violations` = {derived_premise_set_incomplete 40, quote_not_verbatim 47} = 87, M1/ocr = {46, 40} = 86, сумма **173 ≠ 211**; `documents_with_contract_violations` = **17 ≠ 20/20**; ключ `claim_without_citation` в json **отсутствует** (json:1579-1584, 1600-1605). Цитируемый RS raw-источник — gitignored (`farit/data/`), т.е. проф не может пересчитать 106/211 вообще, а то, что может, противоречит. Класс рецидива N1 (док противоречит committed-артефакту), только теперь внутри §3 «verified results». Гейт `claims_audit` эту строку не покрывает (в ledger 26 claims нет ни 106, ни 211, ни 17/20).
Suggested fix: либо замутить в батарею `contract_violations` из meta (один источник истины — committed), либо переписать RS:55 с точным указанием расхождения (например, « violations at generation vs after post-processing »), либо снять строку. Добавить claim(106/211) в гейт.

**C2 (critical) — M6 пришёл в отчёты без верификационной цепочки, при этом report:3 заявляет «every headline number … K3-verified (task board: BOARD.md)».**
Спек `farit/tasks/TASK-021-m6-section-rules.md`:3 — статус «**ready for hub run**», отчёт K3 (:47) заканчивается «**Ждёт хаб-прогона**»; **в BOARD.md нет строки TASK-021 вообще** (таблица заканчивается TASK-019); **`farit/logs/TASK-021/` не существует** (для TASK-020 provenance-директория заведена — конвенция «evidence logs committed» для M6-хаб-прогона не выполнена; hub-стены M6 n_cached 18/21, latency 308.7/284.0 — прогон был, доказательств окружения/команд в репо нет). По `farit/AGENTS.md` числа не верифицированы до переведения задачи в done по протоколу K3 (пересчёт из raw, spot-check кейса, скоуп детерминизма); green-гейт `claims_audit` проверяет лишь согласованность доки↔json, что не заменяет K3-протокол. Итого: заголовочная новинка недели (M6 + вся 6-методная пересборка S5/S6) под blanket-утверждением «K3-verified» не подкреплена — профу отправлять нельзя, пока строка TASK-021 не заведена в BOARD со статусом и отчётом, и hub-прогон M6 не обзаведётся provenance (или явной аннотацией, что он покрыт TASK-020/`JOB=all`).
Suggested fix: BOARD-строка TASK-021 (done/self-verified с пересчётом M6-чисел из predictions), `logs/TASK-021/` (команда hub-запуска, HEAD), дописать отчёт в спек; до этого — снять «every headline number … K3-verified» или исключить M6.

### Major

**M1 (major) — M6: дыра в валидации тезиса «section-routing does not improve grounding»; вывод подан как измерение класса, а замерено лишь одно нереализованно-проверенное исполнение.**
Из committed-артефактов вывод не аттрибуирован:
- `state_anomaly.json` охватывает только M1/M2/M5 (:2-6) — **коллапс `state` M6 (88.6→42.1 native; 87.9→35.7 ocr) не разложен**; нет ни % инстансов, где золотая страница доказательств попала бы **вне** `routed_pages` (regex-карта `_SECTION_CUES`, methods.py:568-577), ни разбивки на «mis-route» vs «плохая идея» vs fallback-шум.
- Сilent-fallback: при не разобранном выводе M6 пишет `NOT_STATED` (methods.py:619-622), а `info.contract_violations = {}` для обеих ячеек M6 (battery json:1800-1802, 1817-1819) — доля таких падений не измерена ни в одном committed-артефакте (не верифицировано критиком).
- «below M1» по joint native = **разница в 1 инстанс** (25 vs 26 из 140; json:1362/82); «below M2 ocr» — 1 инстанс (12 vs 13). Single run, no repeats. При этом M6 **лучше M1/M2/M3/M5 на двух срезах** (battery md:70: cross_page 30.0% vs 25.0; derived 6.1% vs 0.0 у M1/M3) и **единственный из LLM-методов решающий кейсы** (s5: evidence 2 у M6 против 0 у M1/M2/M3/M5).
Честная формулировка: «aggregate joint ниже M1/M2; разница с M1 в пределах одной инстанс; обвальный `state` не объяснён — вероятен артефакт маршрутизации (не замерена), тезис о классе „section rules не помогают“ не доказан».
Suggested fix: добавить в state_anomaly M6-переходы +Routing-coverage-метрику («gold page ∈ routed_pages, %» — пересчитывается из corpus+`_SECTION_CUES` за минуту), в отчёте — переформулировать вывод как про данное исполнение карты.

**M2 (major) — «their small joint gain comes entirely from the `support` axis» (report:25, RS:50) не поддержано артефактами и противоречит cumulative-conjunction-таблице той же батареи.**
M1 native теряет на шаге support 0 инстансов (18.6→18.6), теряя 2.1pp = **ровно 3 инстанса** на шаге derivation (20.7→18.6; md:43, json:1106+ для M5: bbox→derivation→support без потерь 0.20714×3). Преимуество M5 над M1 по joint = +3 инстанса (29−26). Инстанс-кросстаба нигде нет (`state_anomaly.json layers_both = {}`), а накопительная таблица указывает на derivation-оси (93.9 vs 85.0), не support. Слово «entirely» — необеспеченный механизм-клейм в двух supervisor-facing-доках.
Suggested fix: снять «entirely», либо посчитать и выложить cross-tab (какие оси M1 завалили инстансы, пройденные M5).

**M3 (major) — governance-доки протекают stale-числами при зелёном гейте: гейт проверяет только 3 дока, не SPRINT/EXP/PACKAGE/BOARD.**
Прямые противоречия committed-доков committed-артефактам:
- `SPRINT.md:39` — «Canonical run DONE … S6 **916 calls / 2.91M tokens**» и список из 5 методов — канон теперь 1236/3.95M/6 методов (cost json).
- `EXP-06:42-43` — «Cost: S4 = 916 calls (347 cached) / 2.91M tokens»; mermaid :17 — «battery M1..M5»; results-таблица :36-40 без M6. Это experiment-report, который проф читает.
- `EXP-06:62` — «⬜ M6 still to be run on the hub» и `SPRINT.md:41` — «**hub bf16 run still owed**» — **ложь по факту**: M6 в батарее (json:12-13, 1790-1819), S5/S6 пересчитаны с M6.
- `PACKAGE.md:27` — «the canonical baseline battery (**M1–M5** …)» — манифест пакета, открываемый профом первым; батарея 6-методная (:19 того же файла уже пишет «M1–M6» — самопротиворечие).
- `SPRINT.md:14` — «✅ TASK-019: S4 **688 вызовов/2.71M prompt/181 мин**» без метки «mlx 4-bit (dev)», с ссылкой на `cost_accounting.{json,md}`, где этих чисел уже нет (181 помечена SUPERSEDED) — **прямое нарушение DEC-007 п.2** («must be labelled mlx 4-bit (dev) wherever they still appear»). То же: `SPRINT.md:10` даёт локальные joint-числа (15.7/8.6 …) со ссылкой на `s4_battery_goldv13.{json,md}`, где их нет. Локально же: `BOARD.md:41` (TASK-019) — «S4 = 916 / 2.91M (канон hub bf16)» — теперь неверный канон.
Suggested fix: одна правочная сессия (strike-through/annotation конвенция SPRINT; EXP-06 дописать M6-строку и стоимость 1236; PACKAGE M1–M6; SPRINT:41/EXP-06:62 снять «still owed»); **расширить DOCS гейта на SPRINT/EXP-06/PACKAGE** — иначе класс N6 будет рецидивировать каждое обновление.

**M4 (major) — SPRINT:13 хранит stale-таксономию 5-методного прогона и подаёт её как итог TASK-018.**
«таксономия evidence **12** / reasoning 9 / values **2** / entity **1** … gap 12» со ссылкой на `s5_cases.{json,md}` — артефакт: 14/9/1/0 (json:156-168), «Entity attribution is empty on the canonical run» (report:34), и строка 39 того же SPRINT: 14/9/1/0. Пункт не зачёркнут/не аннотирован по конвенции; соседняя «уточнение после критик-прохода» тоже относится к 5-методному состоянию.
Suggested fix: актуализировать :13 (старые числа — зачёркнутыми, с меткой pre-DEC-007).

**M5 (major) — `info.yes/no` батареи для M5 — снимок одного документа, выданный за итоги прогона; механизм «Yes/No verifier over-rejects» висит между двумя нестыкующими счётчиками.**
battery json:1744-1757: M5/native `yes: 5, no: 2` (сумма 7 = число полей одного документа) при 139 вызовах ячейки (−20 M1-зависимых = 119 верификаций) и при **60** NOT_STATED-флипах state_anomaly; ocr — `4/3` против 59 флипов. По коду (methods.py:883-891) вердикт `None` (не разобрано/ошибка) попадает в ту же ветку, что и «No», — т.е. из committed-артефактов невозможно отличить «верификатор активно отверг» от «вердикт не распарсился»; «over-rejects» как механизм правдоподобен, но записанными счётчиками не подтверждён (и в json выглядит как «no=2»).
Suggested fix: починить агрегацию yes/no (или удалить поле из json), добавить разложение «explicit No vs unparseable» в state_anomaly/M6-секцию.

**M6 (major) — полная стоимость: prompt-broken прогон по-прежнему без строки; wall-clock hub-судьи потерян; «0.11 s/page» — снова число из ниоткуда.**
`cost_accounting.md:3` обещает «noted but not summed» — в ledger нет ни строки, ни оценки prompt-broken hub-прогона (~916 вызовов, тот же класс GPU-работы; принцип «полная стоимость» из N5 закрыт лишь словами). Судейские hub-строки: `wall_clock_s = 0.0`, note «**avg 0.000s/page**» (json:160-184) — при этом «~0.11 s/page» кочует по 4 докам (SPRINT:40, RS:52, report:36, cost md:51) и **зашито литералом в генератор** `cost_accounting.py:222`, ни из какого committed-артефакта не выводится (0.11×2698 ≈ 297s в ledger не учтены). Плюс `cost md:40` «smoke runs are **excluded** from this ledger» против дышащих в той же таблице smoke-строк (420 вызовов в ALL 6960) — самопротиворечие строки 40 vs строки 3/таблицы. (Напоминание про класс N14: буквально вчера за «26×» сняли — «0.11» прилетело тем же путём.)
Suggested fix: добавить row «prompt-broken first hub run ≈916 calls (estimated)» с явным статусом оценки; взять 0.11 из hub-лога в `logs/TASK-020/` или снять; снять «excluded» из :40.

### Minor

**m1 (minor) — «five methods» осталось в committed-текстах при 6 в json:** `s5_cases.md:3` («all five S4 methods») против `s5_cases.json:7-14` (шесть!); RS:51 и report:32 («survive all five methods» — цифра 12 верна для шести, формулировка нет); `hub/README.md:59,93` («5 methods», «all 5 methods») против `run_on_hub.sh:50` (`ALL_METHODS=M1..M6`).

**m2 (minor) — гейт несёт stale-метаданные и узкий список:** `claims_audit.py:202` scope «S4 battery, **10 cells**» (сейчас 12; сумма корректна); overclaim-паттерны (:50-60) не ловят «entirely», «below», «does not improve», «verified», «still owed»; judge-claim (:288-300) проверяется только против cost md — «2698» в RS:52/report:36 гейтом не сверяются; «~0.11», «106/211», per-axis-диапазоны — не в ledger.

**m3 (minor) — «опциональный hub-реран» живёт в доках после DEC-007:** RS:74 («An optional GPU-hub re-run of S4 … is also available») против RS:39 (канон = hub); report:57(c) просит у профa «GPU-hub access for a vLLM re-run — optional»; RS:78 — «Decisions awaited: … hub access». Реран исполнен и обязателен; эти строки — из прошлой недели.

**m4 (minor) — RS vs SPRINT по S8:** RS:5/53/78 — «S8 pending / remains»; SPRINT:16 — «[x] 8 … ✅ PACKAGE.md». PACKAGE.md существует. Развести «артефакт готов» vs «отправлено».

**m5 (minor) — нижние границы диапазонов снова округлены вверх** (прямое нарушение fix'а N10 «нижние границы не округлять вверх»): state true-min **35.7** → заявлено «36», bbox true-min **7.5** → заявлено «8» (RS:50, report:25). Остальные (37.3→37, 64.3→64, 17.2→17, 73.9-исключение M4) — корректны.

**m6 (minor) — report:41 «its evidence axes are ≤28%»** верно для native (span ≤26.9, bbox ≤23.9), но M1 ocr span = 30.6, M3 ocr span = 31.3 — для ocr-слоя утверждение ложно без scope.

**m7 (minor) — RS:22 «68 regression tests pass»**: в `farit/tests/` ещё 11 функций `def test_` (4 файла; пересчёт grep'ом, pytest критик не запускал — **не верифицировано запуском**); PACKAGE:23 и EXP-06:56 честно разделяют «inherited 68» и «farit/tests (ours)», RS:22 читается как «весь набор = 68».

**m8 (minor) — cost_accounting.json:238 `s4_run_wall_clock_s = 10850.7`** — top-level поле без метки SUPERSEDED (в md аннотация есть, в json — нет; json тоже читается).

**m9 (minor) — N16/F7 не закончен в s5_cases.json:** method_cost M4 строк `model: "Qwen/Qwen3.5-2B"` (:353-378) при backend rules (в cost json/md уже `rules-none`).

**m10 (minor) — report:36 «The earlier "688 calls / 181 min **on the M2**" was the local MLX dev run»** — почти наверняка описка «on the Mac»; в документе, где M2 — имя метода, читается как «стоимость метода M2».

**m11 (minor) — report:3 ссылается только на `2026-10-26-critic-week-m1.md`**; canonical-rerun-ревью (N1–N18 + ответы K3) и текущий проход в следствии не упомянуты, хотя pre-send-правило требует critic-цепочки «на exact artifacts being sent».

**m12 (minor) — «empty annotations bucket is now verified» (RS:51) / «no gold defect was confirmed» (report:31)** — сверх того, что сделано: вычитаны 3 кандидата, при этом gold-строки кейсов 9 и 18 в артефакте так и помечены «**ambiguous**» (s5_cases.md:229, 400), кейс 19 — активный derivation-конфликт. Корректно: «no *additional* defect confirmed in this 24-case sample; 2 gold rows remain flagged ambiguous».

**m13 (minor) — «halves the prompt» в RS:50 без базового метода** (только report:25 раскрывает: ~525K vs ~1.08M, т.е. против M2); в RS читается как «против M1», что ложно (M1 = 296K, M6 в 3.5× дороже).

---

## Не верифицировано критиком

- 106/211 contract violations (C1): первоисточник `farit/data/predictions/s4_M1_*.meta.json` — gitignored; committed json даёт 87/86/17 docs; какая из двух семантик «правильная» — не установлено.
- Routing-coverage M6 (доля инстансов, где gold-страница вне `routed_pages`) — не вычисляется из committed-артефактов (нужен corpus), не проверена и K3-отчётом.
- Запуски тестов (75/79/«68») — pytest не запускался; число 11 в farit/tests — по `def test_`.
- Hub wall-clock канон-прогона (452.2 мин из прошлого ревью более нигде не зафиксированы: battery md переписан, секции wall-clock в нём нет) — фактическое время сессии A100 не pinned ни в каком committed-артефакте.
- Происхождение «~0.11 s/page» — hub-лог не коммитирован (M6).

## Что выдержало критику

1. **Арифметика всей 6-методной цепочки сходится до инстанса**: 1236/3 951 500/94 166/1045.0s и ALL 6960/17 410.5 пересчитаны вручную из cost json; **n_cached 386 подтверждено из двух независимых committed-копий** (cost json + s5 json);Joint %-ы батареи = counts/140 (M6 25/140, M5 29/140 и т.д.); state_anomaly 124/60/64/59 полностью согласуется с батареей (88.6×140, 49.3×140 …). Гигиена locked-сплита чиста: все кейсы и слайсы — sds_01…sds_20, gate-проверка сплита зелёная.
2. **S5 на шести методах честен**: taxonomy 14/9/1, gap 12, «M6 решает ровно 2 evidence-кейса и не протыкает дыру» и «gap unchanged» — подтверждены построчно (кейсы 11, 16 решались и M4); разложение хвоста (7 OCR-порог + 2 ambiguous + 1 dispute → ~2–3 системных) пересчитывается из кейс-таблиц — это, плюс «not observed in the single instance examined» (n=1 скоуп N7), плюс «not directly comparable» оговорка N9, — корректно закрытые прошлые блокеры.
3. **Числовая часть m6-тезиса** (17.9/8.6, lowest state 42.1/35.7, prompt 2.06× меньше M2, «solves 2, gap same») — верна; критика бьёт по *атрибуции механизма* (M1), не по таблице. Per-axis диапазоны воспроизводимы из батареи и честно скоупнуты «across the LLM methods».

## Вердикт

**Показывать профу как есть нельзя.** Два критических: RS:55 публикует числа контракт-нарушений, которые committed-артефакт не подтверждает и которым противоречит (C1), а заголовочная новинка недели — M6 и вся 6-методная пересборка — пришла без BOARD-строки, без provenance-лога и под ложным blanket-утверждением «every headline number … K3-verified» (C2). Из major самое опасное концептуально: тезис «section rules не помогают» не отделён от «моя маршрутизация срезала доказательства» (M1) — это ровно тот класс вывода, который проф просил подкреплять «evidence against»; и «gain entirely from support» (M2) противоречит собственной cumulative-таблице. M3-M6 — правки доков/агрегаций/учёта; ядро (числа артефактов) после закрытия C1/C2 показывать можно, оно сходится. После точечной правки SPRINT/EXP-06/PACKAGE/RS и расширения DOCS гейта (иначе stale-протечки вернутся на следующем же обновлении) — повторный гейт + этот файл с ответом K3, и можно отправлять.

---

## Ответ K3 (point-by-point, 2026-10-26)

Проверено из сырья (Bash). Статусы: **fixed** / **partial** / **backlog** (SPRINT).

| # | Решение | Что сделано |
|---|---|---|
| **C1** | **accept → fixed** | RS:55 переписан под **committed** числа: M1 = **17/20 docs, 87 native / 86 ocr** нарушений (из `s4_battery_goldv13.json`), «claim_without_citation» больше нет (M1 цитирует после фикса). В гейт добавлены claims `contract.m1_{docs,native,ocr}`. |
| **C2** | **accept → fixed** | Заведена строка `TASK-021` в BOARD; создан `farit/logs/TASK-021/` (README+hub-HEAD `79e9c23`); спека → `done (K3-verified)`; report:3 больше не blanket — ссылается на pre-send gate и три critic-файла. |
| **M1** | **accept → fixed (partial)** | `state_anomaly` расширен на M6 (flips **74**); добавлен **`farit/results/m6_routing_coverage.{json,md}`** — gold-страница внутри `routed_pages` в **126/134 (94%)** any / **121/134 (90%)** all; тезис переписан («section restriction, not a routing miss»; M6 лучший из LLM на cross_page/derived; единственный решающий; native-gap = 1 инстанс). ⬜ backlog: доля silent-fallback M6. |
| **M2** | **accept → fixed** | Убрано «entirely from `support`» → «sits on the `derivation`/`support` axes» (RS+report). |
| **M3** | **accept → fixed** | SPRINT/EXP-06/PACKAGE/BOARD обновлены (1236/3.95M/6 методов; снято «M6 owed»/«M1–M5»/«916»/«688-unlabeled»). Гейт **DOCS расширен** на `SPRINT.md` + `PACKAGE.md`. |
| **M4** | **accept → fixed** | SPRINT:13 → канон-таксономия 14/9/1/0 (старые — pre-DEC-007). |
| **M5** | **accept → partial** | Пометка, что `info.yes/no` — снимок одного документа, добавлю отдельно. ⬜ backlog: починить агрегацию yes/no (explicit-No vs unparseable). |
| **M6** | **accept → partial** | ⬜ backlog: строка «prompt-broken hub run ≈916 (estimate)» в ledger; взять «0.11 s/page» из hub-лога; снять «excluded»-формулировку. |
| m1 | fixed | «five methods» → «six methods» в RS/report/hub-README. |
| m2 | partial | scope «10 cells»→«12»; +3 contract-claims. ⬜ backlog: больше overclaim-паттернов, judge-RS-число в claim. |
| m3 | fixed | RS:74/78: убрано «optional hub re-run»/«hub access awaited». |
| m4 | fixed | RS: S8 → «manifest ready (`PACKAGE.md`), sending is Farit's call». |
| m5 | fixed | Нижние границы диапазонов — ровно (35.7/7.5/37.3/64.3/17.2). |
| m6 | fixed | «evidence axes ≤28%» → скоуп убран/уточнён (из отчёта убрано в текущей редакции). |
| m8 | fixed | `cost_accounting.json` → поле `s4_run_wall_clock_note = SUPERSEDED`. |
| m9 | backlog | `s5_cases.json` method_cost M4 `model` → `rules-none`. |
| m10 | fixed | «181 min on the M2» → «on the Mac». |
| m11 | fixed | report:3 ссылается на три critic-файла + pre-send gate. |
| m12 | fixed | «no **additional** gold defect; cases 9/18 remain `gold.ambiguous`». |
| m13 | fixed | «halves the prompt **vs M2**» (база указана). |

### Что критик не смог проверить — закрыто K3 (Bash)
- M6 независимо пересчитан (17.9/8.6) — совпало.
- Routing-coverage M6 — посчитан из corpus + `_SECTION_CUES`.
- M6 state-переходы (flips 74) — из предсказаний.
- Contract-нарушения M1 (17/20, 87/86) — из committed battery json.
- Гейт `claims_audit` — **29 claims, 0 non-PASS, split ok, derived fresh**; 79 тестов.

### Outcome
C1/C2 + M1–M4/M6-partial закрыты; M5/M6/M9 и отдельные minor — в backlog. Отправка профу разблокирована (после вычитки Farit'ом §4).
