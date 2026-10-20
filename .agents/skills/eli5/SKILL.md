---
name: eli5
description: Explain a task spec (farit/tasks/TASK-NNN-*.md) in simple Russian before starting work — bottom-up brief for the human, with mermaid diagram, glossary, and self-check list
type: prompt
whenToUse: When the user asks to explain a task in simple words / ELI5 / простым языком, before starting the actual work on it
metadata:
  opencode/slash: "true"
---

The user named a task (TASK-NNN) in their message. Read its spec file `farit/tasks/TASK-NNN-*.md` and write an explanation **for the human's understanding**. Do NOT start the actual work — after writing the explanation, stop and wait for the command "приступай".

Правила:

1. Строго по тексту спеки. Ничего не выдумывай и не добавляй от себя. Если что-то в спеке неясно или противоречиво — не додумывай, а выпиши отдельным разделом «Вопросы к спеке».
2. Структура объяснения:
   - **Одним предложением**: что делаем.
   - **Зачем**: какую проблему решаем, что будет плохого, если задачу не сделать (1–3 предложения, без формул).
   - **Вход и выход**: что на входе (файлы, данные), что на выходе (какие файлы появятся, что в них будет).
   - **Пайплайн**: mermaid-диаграмма (flowchart LR) из 4–8 узлов — поток данных от входа к результату.
   - **Пошагово**: 5–10 шагов простым языком, каждый шаг — одно действие.
   - **Где можно сломаться**: 3–5 мест, где легко ошибиться (из ограничений, критериев приёмки, прошлых багов если упомянуты).
   - **Словарик**: все технические термины из спеки, каждый — одно предложение простыми словами.
   - **Как пойму, что задача сделана**: критерии приёмки своими словами, списком для самопроверки.
3. Язык: русский, простой, без канцелярита. Аналогии приветствуются, но не в ущерб точности. Объём — не больше одного экрана.
4. Сохрани объяснение в `farit/tasks/eli5/TASK-NNN.md` (создай папку, если её нет) и продублируй в чат.
5. Сама спека — источник истины; если объяснение и спека расходятся, права спека. Написав объяснение, жди команды «приступай».
