# S6 — total cost accounting

Every model call of the **final canonical runs** is counted (retrieval judges included); the earlier prompt-broken hub run and the smoke runs are noted but not summed. Gold v1.3, dev split. Tokens are reported where the backend recorded them; the legacy 7B judge runner did not record tokens, and its call count is taken from the cache.

## Model-touching methods (per method × layer)

| Family | Method | Layer | Backend | Model | n calls | prompt tok | completion tok | wall-clock s |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| S4 extraction battery | M1 | native | openai | Qwen/Qwen3.5-2B | 20 | 149276 | 15517 | 0.0 |
| S4 extraction battery | M1 | ocr | openai | Qwen/Qwen3.5-2B | 20 | 146859 | 14319 | 0.0 |
| S4 extraction battery | M2 | native | openai | Qwen/Qwen3.5-2B | 160 | 1083168 | 15565 | 0.0 |
| S4 extraction battery | M2 | ocr | openai | Qwen/Qwen3.5-2B | 160 | 1063832 | 12448 | 195.71 |
| S4 extraction battery | M3 | native | openai | Qwen/Qwen3.5-2B | 139 | 215974 | 4951 | 121.7 |
| S4 extraction battery | M3 | ocr | openai | Qwen/Qwen3.5-2B | 139 | 206390 | 4523 | 112.206 |
| S4 extraction battery | M4 | native | rules | Qwen/Qwen3.5-2B | 0 | 0 | 0 | 0.0 |
| S4 extraction battery | M4 | ocr | rules | Qwen/Qwen3.5-2B | 0 | 0 | 0 | 0.0 |
| S4 extraction battery | M5 | native | openai | Qwen/Qwen3.5-2B | 139 | 22713 | 278 | 13.228 |
| S4 extraction battery | M5 | ocr | openai | Qwen/Qwen3.5-2B | 139 | 22617 | 278 | 9.396 |
| retrieval LLM judge (Qwen3.5-2B, hub bf16) | judge | native | openai | Qwen/Qwen3.5-2B | 1349 | n/a | n/a | 0.0 |
| retrieval LLM judge (Qwen3.5-2B, hub bf16) | judge | ocr | openai | Qwen/Qwen3.5-2B | 1349 | n/a | n/a | 0.0 |
| retrieval LLM judge (inherited, old gold) | judge | native | mlx | mlx-community/Qwen2.5-7B-Instruct-4bit | 1303 | n/a | n/a | 8295.7 |
| retrieval LLM judge (inherited, old gold) | judge | ocr | mlx | mlx-community/Qwen2.5-7B-Instruct-4bit | 1303 | n/a | n/a | 8069.8 |
| judge smoke/probe (not a full run) | judge-smoke | both | mlx | mlx-community/Qwen3.5-2B-MLX-4bit | 210 | n/a | n/a | n/a |
| judge smoke/probe (not a full run) | judge-smoke | both | mlx | mlx-community/Qwen2.5-0.5B-Instruct-4bit | 210 | n/a | n/a | n/a |

## Totals by family

| Family | n calls | prompt tok | completion tok | wall-clock s |
| --- | ---: | ---: | ---: | ---: |
| S4 extraction battery | 916 | 2910829 | 67879 | 452.2 |
| retrieval LLM judge (Qwen3.5-2B, hub bf16) | 2698 | 0 | 0 | 0.0 |
| retrieval LLM judge (inherited, old gold) | 2606 | 0 | 0 | 16365.5 |
| judge smoke/probe (not a full run) | 420 | 0 | 0 | 0.0 |
| **ALL** | 6640 | 2910829 | 67879 | 16817.7 |

**SUPERSEDED (local MLX dev run):** S4 full-battery wall-clock from the old runner log = 10850.7s ≈ 181 min. The canonical run is the hub bf16 battery above; its wall-clock is the sum of the per-cell latencies (cached cells show 0.0).

S4 battery: **916 final-run invocations, of which 347 were cache hits (38%)** — i.e. 569 fresh GPU calls. The prompt-broken first hub run and the smoke runs are excluded from this ledger.

## Non-LLM methods (0 model calls)

BM25, dense (MiniLM-L6) retrieval and rules-v4 (M4) issue **no** model calls; their cost is CPU wall-clock only and is not the bottleneck (M4 ran in the battery at 0 LLM calls).

## Notes

- M4 (rules-v4) is non-LLM: `n_calls = 0` by construction.
- **S4 battery is the canonical hub bf16 config (`Qwen/Qwen3.5-2B`, vLLM, A100 MIG — DEC-007).** Wall-clock cells that reuse cache show `0.0` (cached calls are content-identical).
- The inherited Qwen2.5-7B judge is the old-gold baseline — its 2606 calls (1303 native + 1303 ocr) were ~4.5 h on the M2 (local MLX; tokens not recorded by the legacy runner).
- The Qwen3.5-2B judge is now a **full run** (hub, vLLM): 1349 pages/layer at ~0.11 s/page; its page rankings do not beat naive order on strict completeness (see `llm_reranker_hub_*.md`).
- `wall_clock_s` for S4 is the sum of per-call latencies (model time); the runner-log total includes model load overhead.
