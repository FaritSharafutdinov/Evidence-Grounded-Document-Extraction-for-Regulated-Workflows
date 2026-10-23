# AGENTS.md — project conventions (any AI agent working in this repo)

## Environment

- Python: `~/ds_env/bin/python` (3.11). Run all scripts **from the repository root**.
- `pymupdf==1.28.2` is pinned — gold bounding boxes depend on its segmentation. **Never upgrade.**
- Regression suite: `~/ds_env/bin/python -m pytest tests/ -q` — 68 tests must pass.

## Write zones

- Agents may write **only inside `farit/`**.
- `data/`, `documents/`, `sdsbench/`, `scripts/`, `tests/`, root files — **read-only** for agents (Maria's legacy infrastructure, reused as-is).
- Do not commit from throwaway environments (`/tmp/repro-check` etc.).

## The locked split is sacred

- `sds_21`–`sds_29` (9 audit documents) are the locked evaluation split. **Never** train on, tune on, prompt against, or report metrics from them. Every data load filters `split == "dev"`. The split is reserved for the final audit.

## Git zones

- Committed: code (`farit/src/`), results (`farit/results/`), governance docs (`farit/ROADMAP.md`, `SPRINT.md`, `steering/`, `decisions/`, `experiments/`), evidence logs (`farit/logs/`), project skills (`.agents/skills/`), agent definitions (`.opencode/agents/`).
- Gitignored (local only): `farit/tasks/` (K2 coordination), `farit/docs/` (working docs), `farit/data/` (regenerable corpus + LLM caches).

## Numbers discipline (supervisor requirement)

- Every number reported to the supervisor must be **independently verified** — recomputed from raw artifacts, not trusted from another agent's report.
- A number produced by an agent is *unverified* until the verification protocol in `farit/AGENTS.md` is applied.
- Determinism claims must name their exact scope (e.g. "bit-identical warm-cache rerun" — and note the fp16-shoulder caveat, see `farit/logs/TASK-009/`).
- Frozen baseline outputs (`farit/results/bm25_baseline.*`, `dense_baseline.*`, `llm_reranker_qwen7b.*`) are never edited; new results go to new files.

## Research workflow

See `farit/AGENTS.md` for the task board protocol, experiment report template, decision log and steering-note conventions.
