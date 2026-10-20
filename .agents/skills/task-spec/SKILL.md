---
name: task-spec
description: Write a K2 task specification (farit/tasks/TASK-NNN-*.md) following the project template and register it on the task board
type: prompt
whenToUse: When the user asks to create/write/prepare a task spec for K2, or to delegate a piece of research work to the second agent
arguments:
  - topic
metadata:
  opencode/slash: "true"
---

Write a K2 task spec for: $topic

Follow the conventions in `farit/AGENTS.md` and root `AGENTS.md` exactly (write zones, locked split, numbers discipline). Use `farit/tasks/TASK-009-zero-score-investigation.md` as the gold-standard example.

Spec structure (Russian, since K2 works in Russian):

1. Header: task id (next free TASK-NNN), исполнитель K2, статус assigned, источник (steering action item / sprint item), цель одним абзацем.
2. Контекст — everything K2 needs that is NOT in the repo's committed docs (K2 starts with zero context).
3. Жёсткие ограничения — write zones, frozen files that must not change, model to use, run commands (`~/ds_env/bin/python`, from repo root).
4. Дизайн/что делать — concrete numbered steps, exact paths, exact CLI.
5. Критерии приёмки — checkable, numbered (like S1–S5 / Q1–Q4 in past specs).
6. Результаты — exact output files.
7. Отчёт — instruct K2 to append «Отчёт K2» with concrete numbers (not generalities) and set BOARD → review.

Then register the task in `farit/tasks/BOARD.md` (status: assigned).

Do NOT start executing the task yourself — this skill only writes the spec.
