# farit/AGENTS.md — research workflow conventions

## Agent roles (opencode)

The multi-agent setup lives entirely in opencode; agents are defined in `.opencode/agents/` (committed). Roles:

- **K3** (`.opencode/agents/k3.md`, primary, `alibaba-cloud/deepseek-v4.1-flash`) — main agent: designs, delegates, verifies, owns contact with Farit.
- **K2** (`.opencode/agents/k2.md`, subagent, `opencode/deepseek-v4.1-flash-free`) — executor, implements per task specs. K2 is a *role*, not a specific model: the model line in the agent file may be swapped for any cheap model (GLM, Qwen, Kimi K2, ...).
- **critic** (`.opencode/agents/critic.md`, subagent, `opencode/glm-5.3-flash-free`) — adversarial reviewer, deliberately on a *different model family* than K3 to decorrelate blind spots. Read-only except `farit/steering/reviews/`; works per the `critic-pass` skill.

Farit is the human owner; judgement calls belong to him. Visibility into subagent work: opencode child sessions (Leader+Down to enter, Left/Right to cycle) plus `opencode debug agents`.

## Task board protocol (`farit/tasks/BOARD.md`, local/gitignored)

- K2 works **only** from a spec file `farit/tasks/TASK-NNN-*.md` (context → hard constraints → design → acceptance criteria → report section at the end).
- Statuses: `assigned` → `in_progress` → `review` (K2 done, awaits K3) → `done` / `rework`.
- Delegation is two-phase: K3 first invokes K2 with «только eli5» — K2 writes an ELI5 brief (skill `eli5`) to `farit/tasks/eli5/TASK-NNN.md` and stops; after Farit's «приступай» K3 invokes K2 again to execute.
- K2's numbers are *unverified* until K3 moves the task to `done`.
- K3 documents its own work in the same format (spec written before, or post factum same day).

## Verification protocol (K3, before any task → done)

1. Independently recompute the headline numbers from raw artifacts (json/cache), never from the agent's report.
2. Invariants: A5 (`piece_recall ≥ complete`), instance counts (dev = 140 non-ingredient instances, 134 evidence-bearing), dev-split-only filters.
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
2. **Teardown reviews** (Argon, web): `farit/docs/RESEARCH-STATE.md` (living document, updated after every significant step) is the artifact under review; the `critic-packet` skill assembles it + fresh artifacts + questions into a paste-ready packet (`farit/docs/argon-packet-YYYY-MM-DD.md`). The critique + our point-by-point response is filed as `farit/steering/reviews/YYYY-MM-DD-<source>-<topic>.md`. No automation of the web UI (ToS, fragility). (`opencode/gemini-4-argon` exists in the zen catalog if API access is ever wanted.)

## Internal criticism (critic agent)

In addition to external reviews, the `critic` subagent runs adversarial passes **inside** the workflow: after every significant artifact (experiment report, week report, direction decision) and ~weekly on the overall research vector. Protocol: `critic-pass` skill; output: `farit/steering/reviews/YYYY-MM-DD-critic-<topic>.md`; K3 writes the point-by-point response and routes consequences to SPRINT/DEC.

## Pre-send gate (mandatory, before anything goes to the supervisor)

No document (week report, `RESEARCH-STATE`, packet, letter) may go to the supervisor until **both** of these pass on the exact artifacts being sent:

1. **`claims_audit` gate** — `~/ds_env/bin/python farit/src/analysis/claims_audit.py` must exit 0: every headline number recomputed from raw artifacts (PASS), overclaim lint clean or each hit explicitly dispositioned, split semantics ok, and **derived artifacts fresh** (S5/S6 built from the canonical predictions). A red gate blocks the send.
2. **`critic` pass** — invoke the `critic` subagent (protocol `critic-pass`) on the artifacts; it files `farit/steering/reviews/YYYY-MM-DD-critic-<topic>.md`; K3 appends the point-by-point response to the same file. **All critical/major findings are resolved or explicitly dispositioned before sending**; minors may go to the SPRINT backlog.

Rationale (2026-10-26): the gate caught stale derived artifacts (S5 on old predictions) and a stale cost table; the critic caught a document that denied its own headline artifact (its §5.8 vs §3) and a decision justified by a subsequent-broken run. "Numbers recomputed by hand" is not enough — run the gate, then the critic.

## Reporting

- Week report to supervisor = steering action items with evidence links (experiments, logs, commits). Assembled per `SPRINT.md`, verified numbers only, and it must clear the **Pre-send gate** above (claims_audit green + critic pass).
