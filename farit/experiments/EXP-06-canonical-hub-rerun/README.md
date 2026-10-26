# EXP-06 — canonical hub re-run (hub bf16, DEC-007)

## Why

The S4 baselines must be apples-to-apples. Running them on the local MLX-4bit build
vs the hub bf16 build of the same model family produced different weight sets, so we
pinned one canonical configuration (DEC-007) and re-ran everything on it.

## Method

```mermaid
flowchart LR
  A[git clone farit_dev] --> B[build venv + deps]
  B --> C[build_corpus from PDFs+annotations]
  C --> D[vllm serve Qwen/Qwen3.5-2B bf16]
  D --> E[smoke: 1 doc, fail-fast if no citations]
  E --> F[battery M1..M6 x native/ocr]
  F --> G[evaluate_battery --tag goldv13]
  E --> H[llm_reranker --backend openai (2B judge)]
  G --> I[collect -> persistent_volume/out]
  H --> I
```

Driver: `farit/hub/run_on_hub.sh` (agent `hub-runner`), on the Innopolis IDH A100 MIG.

## Config

- Model `Qwen/Qwen3.5-2B`, **bf16**, vLLM 0.19.1; `temperature 0`, `seed 0`, `enable_thinking=False`.
- Gold v1.3, dev split only; locked `sds_21–29` never loaded.
- Provenance: `farit/logs/TASK-020/` (commit, env, pip-freeze).

## Results

| Method | native | ocr |
|---|---:|---:|
| M1 all-fields one-pass | 18.6% | 11.4% |
| M2 individual-field | 21.4% | 9.3% |
| M3 contextual citation verify | 18.6% | 12.1% |
| **M4 rules-v4 (non-LLM)** | **55.0%** | **30.7%** |
| M5 basic LLM verifier | 20.7% | 15.7% |
| M6 section-routed (rules) | 17.9% | 8.6% |

Judge (2B, hub): native `complete@3 = 0.694` (< naive 0.696). Cost: S4 = **1236 calls
(386 cached / 850 fresh) / 3.95M tokens**; 2B judge = 2698 calls.

## Nuances

- The **first** hub run was broken: M1/M2 prompt templates used a flat `page`/`quote`
  shape while the request enforced the nested `LlmOutput` schema — fine on MLX,
  `evidence: null` on vLLM. Fixed (commit `a51ad2b`) + regression gates.
- Single run, no repeats; cached cells show latency 0.
- M5/M2 lower the `state` axis (verifier over-rejects; see `results/state_anomaly.md`).

## Verification

- K3 independent re-score of the hub predictions **matches the table to the decimal**.
- `farit/tests/` (prompt↔schema, backend body, contract gate) + Maria's 68 tests pass.
- `claims_audit` gate green (numbers from raw artifacts, split ok, derived fresh).

## Decisions for Farit

- ✅ hub bf16 = canonical (DEC-007); local MLX-4bit = dev only.
- ✅ M6 (section-routed) implemented and run on the hub (TASK-021); does not shrink the S5 residue.
- ⬜ re-score the 7B judge on v2 + gold v1.3 before any 2B-vs-7B claim.