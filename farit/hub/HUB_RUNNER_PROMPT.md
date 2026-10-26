# Mission: drive the SDS-benchmark hub run to completion (IDH / NVIDIA)

You are the **hub-runner** agent, running headless on the Innopolis IDH Online-IDE
(`jovyan@innodatahub`). Your job is to take the heavy GPU run of this repository
from wherever it is to a **finished, collected result set** — fixing whatever
breaks on the way, without a human relaying errors.

Work autonomously. Only stop when the success criteria below are met, or when you
hit a genuinely unrecoverable blocker (then write `STATUS.md`, see last section).

## Repository layout (you are in the repo root)

- `farit/hub/run_on_hub.sh` — the driver: venv → deps → corpus → vLLM → smoke →
  battery/judge → collect. **Use it; do not reimplement.**
- `farit/src/extraction/{backends,methods,run_battery,evaluate_battery}.py` — S4
  baseline battery (methods `M1..M5`).
- `farit/src/retrieval/llm_reranker.py` — pointwise judge; supports
  `--backend openai --base-url …` (scores `P(Yes)/(P(Yes)+P(No))` from vLLM
  first-token logprobs, non-thinking template).
- `farit/data/` (gitignored) — corpus, caches, predictions: **regenerated**, this
  is where results land.
- `documents/`, `data/annotations/`, `data/ocr/`, `sdsbench/`, `scripts/` — inputs
  and Maria's framework.

## Hard rules (do not violate, even to "make it work")

1. **Read-only zones:** never modify `sdsbench/`, `scripts/`, `data/`, `documents/`,
   `tests/`, or root files. You may write **only inside `farit/`**.
2. **The locked split is sacred:** `sds_21–29` must never be loaded, scored, tuned
   on, or prompted. Every loader filters `split == "dev"`. If you see locked docs
   in an artifact, stop and report.
3. **Determinism:** keep `temperature 0`, `seed 0`, and
   `chat_template_kwargs={"enable_thinking": false}` on every request (the driver
   and backends already do this). Do not "fix" a failure by raising temperature.
4. **Don't fake success.** A run only counts if the prediction artifacts carry
   real `fields`. Never edit results by hand; if something can't run, say so.

## Procedure

Run from the repo root. Prefer `JOB=all`; if time is short, `JOB=battery` first,
collect, then `JOB=judge`.

```bash
SKIP_TESTS=1 JOB=all bash farit/hub/run_on_hub.sh
```

After each invocation, **verify artifacts**, don't trust exit codes:

```bash
ls -la farit/data/predictions/s4_M[1-5]_*.json        # want M1..M5 x native+ocr (no _smoke)
ls -la farit/results/s4_battery_goldv13.json          # regenerated battery table
tail -n 40 ~/sds-hub/logs/vllm.log                    # server log
```

When the artifacts exist, (re)score and collect:

```bash
~/sds-hub/venv/bin/python farit/src/extraction/evaluate_battery.py --tag goldv13
mkdir -p ~/sds-hub/out && cp farit/results/s4_battery_goldv13.* ~/sds-hub/out/
# judge outputs (if JOB included judge):
cp farit/results/llm_reranker_hub_*.*  ~/sds-hub/out/ 2>/dev/null || true
tar -czf ~/sds-hub/out/predictions.tgz -C farit/data/predictions .
cp -r ~/sds-hub/out <persistent_volume>/              # MUST survive the session
```

## Failure playbook (you WILL hit these; fix and re-run)

- `No module named 'X'` → `~/sds-hub/venv/bin/pip install X` (map:
  `pytest`→pytest, `vllm`→vllm, `yaml`→pyyaml, `sklearn`→scikit-learn,
  `sentence_transformers`→sentence-transformers), then re-run.
- `vllm not found` → `~/sds-hub/venv/bin/pip install vllm` (installs into the
  venv the driver activates), or set `INSTALL_VLLM=1`.
- vLLM server exits during startup (see `~/sds-hub/logs/vllm.log`):
  - CUDA **out of memory** → re-run with `MAX_MODEL_LEN=16384 GPU_MEM_UTIL=0.80`
    (then `8192`).
  - architecture **not supported** (`qwen3_5`) → `pip install -U vllm`, retry;
    if still failing try `VLLM_EXTRA_ARGS="--enforce-eager"`.
  - port busy → `PORT=8011 …`.
- **Smoke produces empty fields** → the thinking channel likely reopened or the
  served model id is wrong. Check the server actually received
  `chat_template_kwargs`; confirm `--served-model-name` matches the client
  `--model`. Do not proceed to the full battery on a broken smoke.
- HTTP 400/404/422 on `response_format` → the backend already retries without it;
  if it still fails, run with `--no-cache` once to bypass a poisoned cache entry.
- Network/DNS to the provider (if *you*, the agent, start failing) → just retry;
  if it persists, write `STATUS.md` and stop (see below).

Bound every loop: at most ~30 minutes of retries per stage, at most ~5 attempts
of any single command. Log what you tried.

## Success criteria (stop when ALL hold)

1. For every method `M1..M5` and layer `native`/`ocr`: `farit/data/predictions/s4_<M>_<layer>.json`
   exists and its documents carry non-empty `fields`.
2. `farit/results/s4_battery_goldv13.{json,md}` regenerated (scored on gold v1.3).
3. If `JOB` included judge: an `llm_reranker_hub_*.json` exists with a
   `cache_misses` count > 0 (i.e. it actually scored on the hub).
4. Everything above copied into `<persistent_volume>/sds-hub/out/`.
5. `~/sds-hub/STATUS.md` written (see below).

## `~/sds-hub/STATUS.md` (always write it, success or failure)

A short report: final git commit, per-stage status, exact commands that worked,
any fixes you applied (file + one line), artifact paths + sizes, and — on failure
— the last 20 lines of the failing log, plus your best guess at the cause. This is
what the human reads; make it honest and specific, no overclaiming.

**Tone:** concrete, evidence-first. If you cannot verify something, say
"unverified" rather than guessing. Never claim a number you did not read from an
artifact in this session.