# farit/AGENTS.md — research workflow conventions

Roles: **K3** (main agent — designs, verifies, owns contact with Farit) and **K2** (separate session — implements per task specs). Farit is the human owner; judgement calls belong to him.

## Task board protocol (`farit/tasks/BOARD.md`, local/gitignored)

- K2 works **only** from a spec file `farit/tasks/TASK-NNN-*.md` (context → hard constraints → design → acceptance criteria → report section at the end).
- Statuses: `assigned` → `in_progress` → `review` (K2 done, awaits K3) → `done` / `rework`.
- K2's numbers are *unverified* until K3 moves the task to `done`.
- K3 documents its own work in the same format (spec written before, or post factum same day).

## Verification protocol (K3, before any task → done)

1. Independently recompute the headline numbers from raw artifacts (json/cache), never from the agent's report.
2. Invariants: A5 (`piece_recall ≥ complete`), instance counts (n=125 dev inclusions), dev-split-only filters.
3. Determinism where claimed (rerun or cache replay), with scope stated precisely.
4. Spot-check at least one concrete case end-to-end (prompt → model → metric).
5. Check git status: only expected files changed; gitignore zones respected.
6. Fix or annotate discrepancies in the agent's report (mark edits as K3-verification), then BOARD → `done`.

## Governance artifacts (committed)

- `ROADMAP.md` — long-term plan; updated after supervisor meetings.
- `SPRINT.md` — current week; items trace to steering action items; resolved decisions get struck through, not deleted.
- `steering/YYYY-MM-DD-note.md` — supervisor notes: verbatim + our reading + action items table.
- `decisions/DEC-NNN-*.md` — decision log: context, decision, alternatives, consequences. Judgement calls by the AI workflow that Farit approved are recorded here too.
- `experiments/EXP-NN-*/README.md` — one per experiment: why / method (+ mermaid diagram) / config / results / nuances / verification / **"Decisions for Farit"** section.

## External reviews (Gemini Deep Research / Argon)

Periodic, manual, two kinds:

1. **Literature scans** (Deep Research, web): report saved to `papers/summaries/`, then analyzed and link-checked before any claim is used.
2. **Teardown reviews** (Argon, web): a project artifact (PROGRESS.md, experiment design, week report) is pasted for critique. The critique + our point-by-point response is filed as `farit/steering/reviews/YYYY-MM-DD-<source>-<topic>.md`. No automation of the web UI (ToS, fragility).

## Reporting

- Week report to supervisor = steering action items with evidence links (experiments, logs, commits). Assembled per `SPRINT.md`, verified numbers only.
