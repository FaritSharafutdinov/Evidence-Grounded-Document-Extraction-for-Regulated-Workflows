# Hub runs (NVIDIA / vLLM)

One script does the whole heavy-compute dance on the GPU hub:
`farit/hub/run_on_hub.sh`. It clones/updates the repo, builds a venv, installs
deps, **regenerates the retrieval corpus** from the tracked PDFs + annotations,
launches (or connects to) a vLLM OpenAI-compatible server, runs a smoke test,
then the requested jobs, and copies every artifact into `$WORKDIR/out`.

Everything the run needs is in the git clone: `documents/*.pdf`, `data/annotations/`,
`data/ocr/*.json`, `data/manifest.csv`, `sdsbench/`, `scripts/`, `farit/src/`,
`farit/results/`. Only `farit/data/` (corpus + caches) is regenerated.

## Prereqs on the hub

- A GPU with enough VRAM for `Qwen/Qwen3.5-2B` (bf16 ≈ 4–5 GB weights + KV).
- `vllm` installed, **or** an already-running server you point at with `BASE_URL`.
- Internet for `git clone` and the HF model download (set `HF_TOKEN` if gated).
- Disk for the model + corpus (~10–20 GB is comfortable).

## Quick start

```bash
# full run: smoke -> S4 battery (20 docs x 2 layers x 5 methods) -> judge
JOB=all bash farit/hub/run_on_hub.sh

# or step by step
JOB=smoke   bash farit/hub/run_on_hub.sh   # fail-fast validation
JOB=battery bash farit/hub/run_on_hub.sh   # S4 parity vs the local MLX table
JOB=judge   bash farit/hub/run_on_hub.sh   # pointwise judge via vLLM logprobs
```

If a vLLM server is already up (skip launching / installing it):

```bash
BASE_URL=http://127.0.0.1:8000 JOB=battery bash farit/hub/run_on_hub.sh
```

## Configuration (env vars)

| var | default | meaning |
|---|---|---|
| `REPO_URL` | the fork (GitHub) | repo to clone |
| `BRANCH` / `COMMIT` | `farit_dev` / — | branch, optional exact pin |
| `WORKDIR` | `$HOME/sds-hub` | everything lives here |
| `MODEL` | `Qwen/Qwen3.5-2B` | HF id served by vLLM |
| `SERVED_NAME` | `= MODEL` | value sent as `model` by our client |
| `PORT` / `BASE_URL` | `8000` / — | launch port; `BASE_URL` set ⇒ don't launch |
| `JOB` | `smoke` | `smoke` \| `battery` \| `judge` \| `all` |
| `LAYER` | `both` | `native` \| `ocr` \| `both` |
| `LAUNCH_VLLM` | `auto` | `auto` \| `always` \| `never` |
| `MAX_MODEL_LEN` | `32768` | vLLM context length |
| `VLLM_EXTRA_ARGS` | — | extra `vllm serve` flags |
| `SKIP_TESTS` | `0` | skip the 68-test gate |

## What each job computes

- **smoke** — 1 doc (`sds_05`), both layers, all 5 methods. Asserts the predictions
  are non-empty, which is how a wrong `chat_template_kwargs` (thinking channel
  reopening, TASK-010) shows up immediately.
- **battery** — the S4 baseline table (`M1..M5`) on the full dev split
  (20 docs × 2 layers), for an apples-to-apples speed/parity check against the
  local MLX numbers. Writes `s4_M*_{native,ocr}.json` + metas.
- **judge** — the pointwise reranker (`llm_reranker.py --backend openai`) scoring
  `P(Yes)/(P(Yes)+P(No))` from vLLM's first-token logprobs, non-thinking template.
  This is the run owed by steering note 2026-10-22 p.1 ("recompute affected
  rankings") and the never-done full judge pass.

## Determinism & cache

Generations are cached under `farit/data/llm_cache/` keyed by
`sha256(backend, model, messages, max_tokens, schema)` — so **hub (openai) and
local (mlx) results never mix**, a warm re-run is free, and `latency 0` marks
cache hits (they are excluded from wall-clock summaries, by design).

## Retrieving results

The script prints the `$OUT_DIR` path and a ready `scp` line. It bundles the S4
JSON/MD, a tarball of all prediction JSONs+metas, the judge JSON/MD, and
`HEAD.txt` (the exact commit).

## Known risks / notes

- The model is `qwen3_5` (hybrid linear + full attention, VL arch). It needs a
  **recent vLLM** — if `vllm serve` errors on the architecture, update vLLM or
  set `VLLM_EXTRA_ARGS="--disable-custom-all-reduce"` etc. The smoke job exists
  precisely to catch this before the full run.
- The client always sends `chat_template_kwargs={"enable_thinking": false}` and
  `seed=0`; if a server rejects those fields the backend retries without them
  (and the smoke assertion will then flag the thinking-channel collapse).
- **Not yet runnable:** the `M6 = Qwen3.5-2B + simple section/entity rules`
  baseline (steering note p.2 / Argon teardown) still needs to be implemented
  before it can be scheduled — see the task board.