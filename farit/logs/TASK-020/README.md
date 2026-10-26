# TASK-020 — canonical hub run provenance (K3, post factum)

The **canonical S4 + judge run** (DEC-007) was executed on the Innopolis IDH hub
(NVIDIA A100 MIG) on 2026-10-26 by the `hub-runner` agent driving
`farit/hub/run_on_hub.sh`. This log records enough to reproduce and audit it
(raised by the 2026-10-26 canonical-rerun critic, finding N2).

## What defines "canonical"

- **Model:** `Qwen/Qwen3.5-2B`, **bf16**, served by **vLLM 0.19.1** (OpenAI-compatible).
- **Backend tag:** `openai` on the artifacts; `farit/data/predictions/s4_*_*.meta.json` carry `backend=openai`, `model=Qwen/Qwen3.5-2B`.
- **Gold:** v1.3, dev split only (`guard_split`, locked `sds_21–29` never loaded).
- **Scoring:** non-thinking chat template (`chat_template_kwargs={"enable_thinking": false}`), `temperature 0`, `seed 0`.

## Reproduce (from the repo root; needs an OpenAI-compatible vLLM endpoint)

```bash
SKIP_TESTS=1 JOB=all BASE_URL=http://<host>:8000 LAUNCH_VLLM=never bash farit/hub/run_on_hub.sh
```

The hub itself used `farit/hub/run_on_hub.sh` (clone → venv → corpus → `vllm serve` → smoke → battery → judge → collect).

## Artifacts produced (committed)

- `farit/results/s4_battery_goldv13.{json,md}` — the canonical battery table.
- `farit/results/llm_reranker_hub_Qwen_Qwen3.5-2B_v2.{json,md}` — the full 2B judge.
- `farit/results/s5_cases.{json,md}`, `farit/results/cost_accounting.{json,md}` — derived, recomputed on the canonical predictions.

## Environment (this directory)

- `hub-HEAD.txt` — the repo commit the hub ran (`origin/farit_dev`).
- `RESTORE-ENV.md` — the working CUDA/vLLM stack (vLLM 0.19.1, torch 2.10.0+cu128, driver CUDA 12.5, A100 MIG), pooled by the agent on the node.
- `pip-freeze.txt` — the exact package set at run time.

## Known confounds / caveats (be honest)

- **Single run, no repeats** — no variance estimate.
- The generation **cache key** pins `(backend, model-name, prompt, max_tokens, schema)` but **not** the weight quantization/revision, so a different build under the same model name would be a false cache hit (critic N13). The lock in practice: vLLM bf16 over gold v1.3.
- The **prompt↔schema fix** (commit `a51ad2b`) landed *between* the first (broken) hub run and this canonical one; the first run's predictions are discarded, not mixed.
- Hub wall-clock for the battery is the sum of per-cell latencies; cached cells show `0.0` and are not re-paid (see `cost_accounting.md`).