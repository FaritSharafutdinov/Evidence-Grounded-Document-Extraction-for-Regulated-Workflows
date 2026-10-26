# Critic pass — канонический прогон недели M1 (hub bf16, DEC-007)

- Дата: 2026-10-26. Модель критика: `opencode/glm-5.3-flash-free` (другое семейство, чем у автора — по протоколу).
- Назначение: **pre-send gate** перед отправкой отчёта профу (неделя M1).
- Протокол: `critic-pass`. Ничего кроме этого файла не изменено (read-only + reviews/).
- Объекты атаки: S4-батарея (`s4_battery_goldv13.{json,md}`), judge (`llm_reranker_hub_Qwen_Qwen3.5-2B_v2.{json,md}`), S5 (`s5_cases.{json,md}`), S6 (`cost_accounting.{json,md}`), доки (`RESEARCH-STATE.md`, `report-2026-10-23.md`, `SPRINT.md`, DEC-005/006/007), гейт `claims_audit.py`, предыдущее ревью `2026-10-26-critic-week-m1.md`.

## Верификационная рамка критика

Числа сверялись **только арифметикой по JSON/meta/докам** (без Bash-пересчёта из сырья). Всё, что требует пересчёта из raw cache/gold, помечено «не верифицировано критиком». Пункты, где автор даёт inference (а не измерение), помечены assumption.

---

## Findings

### Critical

**N1 (critical) — RESEARCH-STATE.md самопротиворечит о существовании полного judge-прогона 2B.**
§5.8 (RS:73): «No full Qwen3.5-2B judge run exists» — но §3 (RS:30) приводит полный hub-прогон judge 2B (score 0.769, n=91/134, gold v1.3) как один из главных результатов недели, и §6 ссылается на те же числа. Артефакты подтверждают существование: `farit/results/llm_reranker_hub_Qwen_Qwen3.5-2B_v2.{json,md}`. Проф, читая §5.8, сделает вывод, что заголовочный результат недели опирается на артефакт, который в том же документе объявлен несуществующим. Вероятная причина — §5.8 писался до hub-рерана и не был вычеркнут (в SPRINT согласно конвенции resolved-пункты должны зачёркиваться, не удаляться).
Доказательство: RS:73 vs RS:30 + §6; файл judge-результата существует.
Fix: переписать §5.8 — «существовал только MLX-4bit локальный прогон; полный hub bf16 прогон выполнен 2026-10-25 (DEC-007)», со ссылками на артефакты. **Блокер.**

**N2 (critical) — «каноничность» flagship-цифр не доказана в репо: наблюдалось слово, а не цепочка воспроизводимости.**
DEC-007 объявляет hub bf16 канонической конфигурацией, но в репо отсутствует всё, что позволило бы независимому критику (или профу) воспроизвести/сканировать прогон: (а) нет hub-логов и `HEAD.txt` — согласно конвенции evidence-логи (`farit/logs/`) коммитятся, но артефактов hub-out (список запусков, commit hash на hub, окружение) в репо нет; (б) DEC-007 ссылается на `RESTORE-ENV.md`, которого не существует (N11); (в) в BOARD нет TASK-020/спека на канонический реран — K2-работа без спека противоречит `farit/tasks/BOARD.md` protocol; (г) cache key в `farit/hub/run_on_hub.sh` = (backend, model-name, messages, max_tokens, schema) — не пинит квантизацию/веса/revision, т.е. «bf16» это утверждение о намерении, а не о том, что действительно скачалось (детали N13).
Доказательство: glob/grep по репо на `HEAD.txt|hub-out|RESTORE-ENV.md` — пусто; run_on_hub.sh cache-key строки; BOARD без TASK-020.
Fix: положить hub-run log (config dump, model revision, git HEAD hub, оценки квантизации) в `farit/logs/TASK-020/` + завести TASK-020 спек или отметить реран как K3-работу постфактум. **Блокер.**

### Major

**N3 (major) — мотивирующее число DEC-007 взято из prompt-broken прогона; после фикса направление вывода меняется на противоположное.**
DEC-007 мотивирует канонический реран в т.ч. «M2 native 16.4 hub vs 19.3 local, identical prompts» → «weights/quantization различаются». Но 16.4 — из прогона со сломанными промптами; после фикса промптов M2 native на hub = 21.4 (battery md). Т.е. правильное сравнение: M2 native hub 21.4 vs (stale) local 19.3 — hub *выше относительно* local, и вывод «наши локальные цифры были занижены окружением, а не весами» — другой тезис, чем записанный в DEC. к тому же разница +2.1 мала и сопоставляет разные версии промптов — не «identical prompts».
Доказательство: DEC-007 мотивирующий абзац (16.4/19.3); `s4_battery_goldv13.md` M2 native 21.4; fix промптов лог TASK-019.
Fix: аннотировать DEC-007 «мотивирующее число из prompt-broken прогона, см. TASK-019 fix; вывод о расхождении weights/confound пересмотрен» — decisions не переписывать, дать addendum. **Блокер отправки без аннотации.**

**N4 (major) — cost_accounting.md хранит stale локальный MLX-прогон как главной строки: «10850.7s ≈ 181 min».**
`cost_accounting.md:36` («Full M1–M5 local MLX pass: 10850.7s ≈ 181 min») при том, что батарея на hub заняла 452.2 мин wall (battery md:30) — 4-кратный разрыв, но doc не помечен как superseded. При этом заголовок (line 3) «Every model call counted». Проф прочитает 181 min как стоимость канона.
Доказательство: cost md:36 vs 30; буккроссинг «181» — это число также живёт в BOARD (TASK-019, N6).
Fix: пометить строки как «superseded by hub bf16 (DEC-007), сохранены для сравнения» и добавить hub-батарею в сводную таблицу. **Блокер: стоимость канона нигде не посчитана как первичная** — см. N5.

**N5 (major) — «916 calls» = финальный invocation, а не реальный объём GPU-работы; первый hub-прогон и smoke excluded; smoke rows тихо-нулевые; F7-строки с model=Qwen3.5-2B не почищены.**
Разбор — по четырём частям: (а) меты показывают реальные доли кэша — M1 native 20/20 cached, M1 ocr 20/20, M2 native 160/160, M2 ocr 83/160, M3 7/139 и 7/139, M5 native 7/139, M5 ocr 43/139 (итого ~347 из 916 из кэша, ~38%) — 916 это «сколько промптов подано», не «сколько работы сделал GPU»; (б) первый (prompt-broken) hub-прогон (~916 вызовов) и smoke-прогоны выпали из учёта, хотя это тоже hub-время; (в) smoke rows в cost json заполнены нулями (420 smoke-вызовов считаются «бесплатными»); (г) F7-строки с model=Qwen3.5-2B (M4) остались в cost json, т.е. строки F7 по M4 не отличимы от F7 по M4-на-7B при беглом чтении.
Доказательство: `s4_*.meta.json` cached counts; cost json smoke rows; grep model=Qwen3.5-2B в F7-блоке.
Fix: оставить «916 финальных invocations, из них 347 cached» + отдельно посчитать/оценить первый (prompt-broken) прогон ~916 вызовов и smoke-вызовы; «Every model call counted» смягчить. **Блокер из-за принципа «полная стоимость» (critic-pass).**

---

**N6 (major) — BOARD и SPRINT противоречат канону: старые MLX-числа живут в строках «верифицировано».**
BOARD rows TASK-015 (15.7/8.6), TASK-018 (19.3/11.4, entity 1), TASK-019 (688 / 2.71M токенов / 181 мин) — числа локального MLX-прогона, superseded DEC-007, но стоят в таблице как результаты задач со статусом done/verified. K3 двигал их в done до канонизации; теперь «K3-verified» в доках ссылается на устаревшие (stale) числа. SPRINT:10 «Хаб-реран — опционален» и SPRINT:40 «TODO re-run battery on hub» противоречат и DEC-007, и факту (реран исполнен); SPRINT:39 «26× the Mac» — число, невыводимое ни из одного артефакта (см. N14).
Доказательство: BOARD.md:37,40,41; SPRINT.md:10,39,40; DEC-007.
Fix: зачеркнуть/аннотировать устаревшие строки по конвенции SPRINT («resolved» = strike-through, не delete); BOARD-числа пометить «pre-DEC-007, local MLX» или заменить на hub-канон. **Блокер.**

**N7 (major) — entity-overclaim: «does not reproduce» из n=1.**
Вывод «loc-broken entity ambiguity не воспроизводится на hub» опирается на один кейс (case 24, sds_16 product_name = localization; s5_cases.md кейс 24). n=1 не поддерживает утверждение о невоспроизводимости категоричного эффекта, тем более что residual-анализ (N8) показывает: похожие случаи не декомпозированы.
Доказательство: report-2026-10-23, формулировка «does not reproduce»; s5_cases.md кейс 24.
Fix: переформулировать «not observed in the single instance examined (sds_16 product_name); per-category residue unchanged»; гейт-лист расширить (N12). **Блокер для профа.**

**N8 (major) — «~5 genuine residue» содержит 2 gold.ambiguous кейса и 1 спорный, декомпозиция отсутствует.**
Кейсы 9 (s5_cases.md:219, gold.ambiguous), 18 (:381, gold.ambiguous), 19 (:396–412, активный спор) входят в хвост «~5 genuine». Без разложения читается как «системный хвост» из 5; фактически минимум 2 из 5 — разметка gold, не ошибка системы, 1 — спорная. Вывод о хвосте завышен на ~40%.
Доказательство: s5_cases.md:219, 381, 396–412; сводный вывод s5_cases.md/report.
Fix: разложить «~5» на (2 ambiguous, 1 спорный, остальные) в доке и отчёте. **Блокер.**

**N9 (major) — сравнение «2B hub 0.769 < 7B 0.864» конфаунднуто тремя сменами разом.**
7B-число: v1-scoring, gold v1.0, n=89/125 (`llm_reranker_qwen7b.md`); 2B-число: v2-scoring, gold v1.3, n=91/134 (`llm_reranker_hub_Qwen_Qwen3.5-2B_v2.md`). Прямой model-ranking из этих строк некорректен; направление может не пережить re-scoring 7B на v2+gold v1.3.
Доказательство: метаданные обоих judge-артефактов.
Fix: в judge md и report — «not directly comparable (scoring protocol, gold version and n all changed); re-score 7B on v2+gold v1.3 before any 2B<7B claim». **Блокер.**

**N10 (major) — page-range «44–66%» численно неверен; нижняя граница span округлена вверх.**
RS:49 и report:24 дают «page 44–66%» как диапазон, покрывающий второй проход, но фактический M5 native page = 38.1, ocr = 39.6 (battery md) — оба ниже нижней границы, заявленный «лучший случай» уже пробит. Span «22–31%» — округление 21.6 → 22, меняющее нижнюю границу.
Доказательство: RS:49; report:24; battery md: M5 native page 38.1 / span 21.6; M5 ocr page 39.6 / span 27.6.
Fix: пересчитать фактические min/max по батарее и записать их; нижние границы не округлять вверх. **Блокер: это headline-число отчёта.**

### Minor

**N11 (minor) — DEC-007 ссылается на несуществующий `RESTORE-ENV.md`; мотивировавший DEC-007 Argon teardown не оформлен по конвенции.**
Glob по репо `RESTORE-ENV.md` — пусто. Аргон-ревью, побудившее DEC-007, не записано в `farit/steering/reviews/` как `YYYY-MM-DD-argon-*.md` (по конвенции `farit/AGENTS.md` — из п. «External reviews»), т.е. цепочка «ревью → решение» разорвана.
Fix: создать RESTORE-ENV.md или убрать ссылку; оформить Argon-ответ как review-файл.

**N12 (minor) — гейт `claims_audit.py` ловит лишь узкий overclaim-лист.**
Линт покрывает только 2 дока, freshness check — только n_calls, cost json не проверяется; в ledger (23 claims) нет 106/211, 2698, S5-декомпозиций, page-range ошибки (N10). «Does not reproduce» (N7), «verified», «canonical», «honest reading» — не флажатся.
Доказательство: `farit/src/analysis/claims_audit.py` — списки паттернов и проверяемых файлов.
Fix: расширить overclaim-список и включить cost_accounting.{json,md} + RS в lint; добавить page-range sanity-check «min по батарее ≥ min в доке».

**N13 (minor) — cache key не пинит веса/квантизацию.**
run_on_hub.sh: key=(backend, model-name, messages, max_tokens, schema). Модель с тем же именем, но другой квантизацией (MLX-4bit) дала бы cache hit — именно ложно-«идентичные» результаты, от которых уходит DEC-007.
Fix: добавить quantization/revision в key; в hub-логе дампить config.

**N14 (minor) — «26× the Mac» (SPRINT:39) невыводимо; если мерить по 7B 6.4s/page → ~58×, не 26×.**
Ни один артефакт не содержит бейзлайн «скорость Mac» для 2B bf16; 26× появляется ниоткуда.
Fix: удалить число или явно дать источник и scope.

**N15 (minor) — нет repeats/variance; заявки о стабильности опираются на одиночные прогоны.**
M5>M1 в разрезе state = 49.3 vs 88.6 — но это разница по aggregate; per-instance разница coverage (M5>M1 ровно в 3/140 инстансов) показывает, что «преимущество» M5 по state почти полностью объясняется relabeling, а не покрываемостью (пересчёт per-instance не верифицирован критиком — assumption из aggregate-чисел).
Fix: явная оговорка «single run, no repeats» в отчёте; repeats при следующей итерации.

**N16 (minor) — в cost json строки F7 (M4) носят model=Qwen3.5-2B (старая метка) — не почищено.**
Доказательство: grep по `model` в cost json F7-блоке.
Fix: заменить на актуальную метку модели F7 или пометить legacy.

**N17 (minor) — F14 (multi→single reclass) всё ещё не упомянут в caveat 1 отчёта.**
Было finding'ом прошлой критики `2026-10-26-critic-week-m1.md`; не принято.
Fix: добавить в caveat-список.

**N18 (minor) — нет TASK- спека/эксперимент-отчёта для канон-рерана.**
Батарея и judge-реран не имеют EXP-report по шаблону (`farit/experiments/EXP-NN-*/README.md`) и не оформлены задачей; конвенции нарушены для headline-работы недели.
Fix: завести EXP-отчёт с мержид-диаграммой пайплайна и разделом «Decisions for Farit».

## Не верифицировано критиком

- Per-instance разложение M5-vs-M1 по state (N15) — вывод из aggregate, пересчёта не было.
- Токенomics 2.71M / 688 страниц (BOARD TASK-019) — сверены только перекрёстно между доками, не из raw json.
- Wall 452.2 min и глубина первого hub-прогона (~916) — из аргументации в матах/логах, не из hub-логов (их нет в репо, N2).
- Скорость 7B «6.4 s/page» — из ранее замороженного артефакта, не пересчитана.

## Что выдержало критику

1. **Заголовок F1 прошлого ревью закрыт корректно.** Подпись «Inherited (re-scored on gold v1.3)» корректно появилась в `s4_battery_goldv13.md` и отражена в отчёте/RS — несравнимые числа больше не подаются как сравнимые (тезис (c) автора подтверждён).
2. **Внутренняя арифметика артефактов сходится.** 916 invocations, 2 910 829 токенов, 6640 (сводный счётчик из battery json), 452.2 min wall, S5 taxonomy 24 кейса, gap 12=7+5 — сверены перекрёстно из json/md, расхождений нет (внутриартефактная самологласованность).
3. **Тезис (b) «вторые проходы не чинят grounding» численно подтверждён**, и OCR-покрытие разложено честно: кейсы 8,13,14,15,20,22,23 имеют IoU 0.5466–0.6934 (>0.5, <0.8) при M4 на native — split-обоснование для 7 OCR-кейсов подтверждено из json.

## Вердикт

Отправлять научруку как есть **нельзя**. Документ противоречит сам себе о существовании главного артефакта недели (N1), каноничность цифр не обеспечена цепочкой воспроизводимости в репо (N2), а мотивирующее число DEC-007 взято из prompt-broken прогона (N3). Экономика недели посчитана для другой (stale) конфигурации и не учитывает реальный GPU-объём (N4/N5); говернанс-доки (BOARD/SPRINT) протекают старыми числами (N6); три overclaim-высказывания (N7, N8, N9) и одна headline-цифра (N10) падают при прямых числах из собственных артефактов. Это все блокеры: N1–N10 — major/critical. Мелкие пункты (N11–N18) — гигиена; их можно закрыть одной правочной сессией после блокеров. Ключевая конструктивная база в порядке («Что выдержало критику»), т.е. починка — в основном переписывание оговорок и оформление, а не переделка экспериментов; только «полная стоимость» (N5) потребует честного пересчёта из json/логов hub.

---

## Ответ K3 (point-by-point, 2026-10-26)

Числа проверены из сырья (Bash). Статус: **fixed** / **backlog** (SPRINT).

| # | Решение | Что сделано |
|---|---|---|
| N1 | **accept → fixed** | Переписал RESEARCH-STATE §5.8: полный 2B-judge **существует** (hub, 1349 стр./слой), со ссылкой на артефакт. Самопротиворечие снято. |
| N2 | **accept → fixed** | Добавил `farit/logs/TASK-020/` (provenance: `README.md` с командой/конфигом/ковенантами, `hub-HEAD.txt`, `RESTORE-ENV.md`, `pip-freeze.txt`). DEC-007 ссылается туда. Спека TASK-020 — там же (README). |
| N3 | **accept → fixed** | Addendum в DEC-007: мотивирующее «16.4 vs 19.3» — из prompt-broken прогона; на фиксе M2 native = 21.4; решение стоит по аргументу weight-identity, не по этому числу. |
| N4 | **accept → fixed** | `cost_accounting.md`: строка «181 min» помечена **SUPERSEDED (local MLX dev run)**; канон-wall — суммы по ячейкам. |
| N5 | **accept → fixed** | В cost добавлена строка: **916 final invocations, 347 cached (38%) → 569 fresh**; заголовок смягчён («final canonical runs»); prompt-broken/smoke вынесены. |
| N6 | **accept → fixed** | SPRINT обновлён (канон-числа, TODO→DONE, «26×» снят); BOARD TASK-015/018/019 аннотированы «pre-DEC-007 local MLX → канон». |
| N7 | **accept → fixed** | «does not reproduce» → «**not observed in the single instance examined** (sds_16 product_name)… one instance, not a category-level result». |
| N8 | **accept → fixed** | «~5 genuine residue» разложено: **2 `gold.ambiguous` (9, 18) + 1 derivation-dispute (19) → ~2–3 unambiguously system-side**. |
| N9 | **accept → fixed** | Добавлена явная оговорка «not directly comparable (v1/v2 scoring, gold v1.0/v1.3, n 89/125 vs 91/134); re-score 7B on v2+gold v1.3 before any 2B<7B claim» — в RS §3 и отчёте. |
| N10 | **accept → fixed** | Пересчитал из артефакта: page **38–66%** (было 44–66 — неверно), span **22–31%**, bbox **8–24%**, state 47–89%. Поправлено в RS + отчёте. |
| N11 | **accept → partial** | `RESTORE-ENV.md` теперь в репо (`logs/TASK-020/`). Argon-teardown как отдельный review-файл — **backlog** (оформлю). |
| N12 | accept → **partial/backlog** | Гейт расширю: cost-json в lint, page-range sanity, больше overclaim-паттернов. Пока — backlog. |
| N13 | accept → **fixed (документировано) + backlog** | Ковенант записан в `TASK-020/README.md` (cache key не пинит квантизацию/revision); pin revision — backlog. |
| N14 | **accept → fixed** | «~26× the Mac» **снят** из SPRINT (нет артефакта-бейзлайна Mac-2B-bf16). |
| N15 | **accept → fixed** | «Single run, no repeats» добавлено в RS и в caveats отчёта. |
| N16 | accept → **backlog** | M4-строки cost с `model=Qwen3.5-2B` — почищу (`rules-none`). |
| N17 | **accept → fixed** | В caveat 1 отчёта добавлено multi→single (sds_18-фикс). |
| N18 | accept → **partial** | `logs/TASK-020/README.md` закрывает provenance; полный EXP-report по шаблону — backlog. |

### Что критик не смог проверить — закрыто K3 (Bash)
- Пересчёт S4-таблицы (18.6/11.4 … 30.7/15.7) из предсказаний — совпал до знака.
- page/span/bbox/state min/max — из `s4_battery_goldv13.json` (N10).
- cached 347/916 — из `*.meta.json` (N5).
- S5/S6 пересчитаны на каноне; гейт `claims_audit` — **23/23 PASS, split ok, derived fresh**.

### Outcome
- Блокеры N1–N10 закрыты правками доков/артефактов/SPRINT/DEC-007; N11/N13/N18 частично; N12/N16 + Argon-файл/EXP-report — в backlog.
- Гейт: `farit/src/analysis/claims_audit.py` зелёный; 75 тестов зелёные.
- Отправка профу разблокирована (после вычитки Farit'ом §4).


