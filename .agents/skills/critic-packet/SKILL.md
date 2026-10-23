---
name: critic-packet
description: Assemble a paste-ready packet for the external Argon teardown review — RESEARCH-STATE + fresh artifacts + reviewer role instructions + specific questions. Output is one markdown file the user pastes into the Argon web UI.
type: prompt
whenToUse: When the user asks to prepare a packet/artifact for Argon review, or periodically (every 1-2 weeks) after significant research progress
arguments:
  - focus
metadata:
  opencode/slash: "true"
---

Собери пакет для внешнего разбора в Argon (веб-версия, вставляется руками). Фокус разбора: $focus (если не указан — общий разбор вектора исследования).

Шаги:

1. Прочитай `farit/docs/RESEARCH-STATE.md`. Если какие-то разделы устарели относительно `farit/SPRINT.md`, `farit/experiments/`, `farit/steering/` — сначала обнови RESEARCH-STATE (это живой документ), перечисли в чате, что обновил.
2. Проверь, что все числа в RESEARCH-STATE — verified (сверь с `farit/tasks/BOARD.md`). Неверифицированное либо выкини, либо пометь «preliminary».
3. Собери пакет — один markdown-файл `farit/docs/argon-packet-YYYY-MM-DD.md`:

```
# Research teardown request

## Role
Ты — hostile reviewer научного проекта (уровень reviewer 2 на NeurIPS / строгий
оппонент на защите). Твоя задача — найти слабости, противоречия и недоработки,
а не хвалить. Каждое замечание подкрепи цитатой из текста ниже. Если замечание
основано на предположении — явно пометь его как assumption.

## Что разбирать
<фокус: из аргумента или "весь вектор исследования">

## Конкретные вопросы
<3-7 вопросов: сформулируй из открытых вопросов RESEARCH-STATE и свежих
steering-заметок; например "достаточно ли сильны бейзлайны для вывода X",
"какие альтернативные объяснения результата Y мы не рассмотрели">

## Research state
<полный текст RESEARCH-STATE.md>

## Свежие артефакты
<1-3 релевантных фокусу документа: последний experiment README, week report,
дизайн эксперимента — вставить целиком, не ссылкой>

## Формат ответа
- Findings списком: severity (critical/major/minor) → замечание → цитата →
  предлагаемое исправление.
- Отдельно: что в дизайне исследования сделано правильно (2-3 пункта).
- Отдельно: какую ОДНУ вещь вы бы изменили в первую очередь.
```

4. Правила сборки:
   - Пакет должен быть самодостаточным: Argon не имеет доступа к репо, поэтому ссылки на файлы заменяй вставленным содержимым.
   - Объём: не больше ~15-20 КБ текста (лимит веб-формы). Если не влезает — режь артефакты, а не RESEARCH-STATE и не вопросы.
   - Язык пакета: английский (внешний ревьюер), кроме случаев, когда пользователь просит русский.
5. Покажи пользователю путь к файлу и напомни протокол: ответ Argon сохранить в `farit/steering/reviews/YYYY-MM-DD-argon-<topic>.md`, затем K3 пишет point-by-point response в тот же файл (принимаем / отклоняем / нужен эксперимент — с обоснованием).
