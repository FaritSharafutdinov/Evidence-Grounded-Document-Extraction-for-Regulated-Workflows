---
name: week-report
description: Assemble the weekly supervisor report from steering action items, sprint status, and verified experiment results
type: prompt
whenToUse: When the user asks to prepare the weekly report for the professor/supervisor
metadata:
  opencode/slash: "true"
---

Assemble the week report:

1. Read the current `farit/steering/*-note.md` action items and `farit/SPRINT.md` — the report must answer the supervisor's priorities in his order, not ours.
2. For each action item: status + one-paragraph summary + evidence links (experiment READMEs, `farit/results/`, `farit/logs/`, commit hashes).
3. **Verified numbers only** — check each number against the verification state on the task board (`farit/tasks/BOARD.md`); anything not K3-verified is marked as preliminary or excluded.
4. Include the honest section: what did NOT reproduce / what surprised us / what we are unsure about. The supervisor explicitly values this over polished claims.
5. End with next week's plan (from `ROADMAP.md` milestones) and any decisions needed from the supervisor.
6. Output: English, one page max, saved to `farit/docs/report-YYYY-MM-DD.md` (gitignored working doc) — the user reviews before anything is sent.

Do not invent results to fill gaps — an unanswered action item is reported as open with a reason.
