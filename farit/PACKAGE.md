# S8 — repository package for the supervisor

This maps your request (*"send the complete repository, development documents,
annotations, prompts, raw results, and configurations"*, note 2026-10-19) to
concrete paths. Everything under **committed** is in the git repo; everything
under **attach separately** is gitignored by policy and Farit sends it alongside.

- **Repo:** `https://github.com/FaritSharafutdinov/Evidence-Grounded-Document-Extraction-for-Regulated-Workflows`
- **Branch:** `farit_dev` (the working line; `main` is not the current state)
- **Pinned commit for this package:** see `farit/logs/TASK-020/hub-HEAD.txt` and the tip of `farit_dev` at send time.

## Repository (committed)

| What you asked for | Where |
|---|---|
| Framework code | `sdsbench/` (inherited), `scripts/`, `ocr.py` |
| Our extraction code | `farit/src/` (retrieval, extraction, analysis) |
| **Annotations** | `data/annotations/` — `gold.json`, `source/sds_*.json`, `CHANGELOG.md` (v1.0→v1.3) |
| **Prompts** | `farit/src/extraction/methods.py` (M1–M6 templates + system prompts), `sdsbench/extractors/llm.py` (`SYSTEM_PROMPT`) |
| **Raw results** | `farit/results/` — see table below |
| **Configurations** | `requirements.txt`, `farit/requirements.txt`; `farit/decisions/` (DEC-003/004/005/006/007); `farit/logs/TASK-020/` (hub env, pip-freeze) |
| Governance | `farit/ROADMAP.md`, `farit/SPRINT.md`, `farit/steering/*.md`, `farit/steering/reviews/*.md`, `farit/experiments/EXP-06-*/` |
| Regression tests | `tests/` (inherited, 68), `farit/tests/` (ours) |

### Raw results (`farit/results/`)

- `s4_battery_goldv13.{json,md}` — the canonical baseline battery (M1–M5 × native/ocr, gold v1.3, hub bf16).
- `llm_reranker_hub_Qwen_Qwen3.5-2B_v2.{json,md}` — full 2B pointwise judge (hub).
- `s5_cases.{json,md}` — 24 real error cases + 5-category taxonomy (frozen input = S4).
- `cost_accounting.{json,md}` — total cost (calls, tokens, wall-clock).
- `state_anomaly.{json,md}` — why the second-pass methods lower the `state` axis.
- `claims_audit.{json,md}` — the reliability gate (numbers recomputed from raw artifacts).
- `bm25_baseline*.{json,md}`, `dense_baseline*.{json,md}`, `llm_reranker_qwen7b.*` — retrieval baselines (frozen).

## Attach separately (gitignored working data)

- `farit/docs/` — `RESEARCH-STATE.md`, `report-2026-10-23.md` (week report draft), `PROJECT_GUIDE.md`.
- `farit/tasks/` — `BOARD.md` + `TASK-NNN-*.md` specs (incl. TASK-020, TASK-021).
- `farit/data/` — regenerated corpus (`corpus/units_*.jsonl`, `gold_evidence.jsonl`), prediction JSONs, LLM caches.

## Reproduce

```bash
git clone -b farit_dev <repo-url> && cd <repo>
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r farit/requirements.txt
python farit/src/retrieval/build_corpus.py
python -m pytest tests/ -q          # 68 inherited tests
# canonical battery + judge (needs an OpenAI-compatible vLLM endpoint, see farit/logs/TASK-020/):
BASE_URL=http://<host>:8000 LAUNCH_VLLM=never JOB=all bash farit/hub/run_on_hub.sh
```

## Honest notes

- Canonical config = **hub bf16** (DEC-007); local MLX-4bit numbers are dev-only.
- **Single run, no repeats.**
- The 7B-judge numbers are on the **previous gold (v1.0)** and are not directly comparable to the 2B run (disclosed; re-score owed).