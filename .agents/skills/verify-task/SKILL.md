---
name: verify-task
description: Run the K3 verification protocol on a completed K2 task (recompute numbers independently, check invariants, update BOARD)
type: prompt
whenToUse: When the user says a task is done/finished/ready for review, or asks to verify/validate K2's work
arguments:
  - task_id
metadata:
  opencode/slash: "true"
---

Verify task $task_id per the protocol in `farit/AGENTS.md` (section "Verification protocol").

Steps:

1. Read `farit/tasks/$task_id-*.md` — the spec and the «Отчёт K2» section. Note every claim with a number in it.
2. **Independently recompute** every headline number from raw artifacts (`farit/results/*.json`, `farit/data/llm_cache/*.jsonl`, corpus files). Never trust the report's arithmetic.
3. Invariants: A5 (`piece_recall ≥ complete` per instance), instance counts (n=125 dev inclusions unless the spec says otherwise), dev-split-only filters.
4. Determinism where claimed — rerun or replay, state the exact scope of the claim.
5. Spot-check one concrete case end-to-end (prompt → model output → metric).
6. `git status` — only expected files changed, gitignore zones respected.
7. Report to the user in Russian: таблица {claim, verified?, evidence}. Fix small numeric errors directly in the report with a K3-verification note; larger problems → BOARD `rework` with a precise fix list (F1, F2, …).
8. If everything checks out: BOARD → `done ✅ (K3-verified …)` and propose the commit list (per root AGENTS.md git zones). Only commit after the user verifies the list.
