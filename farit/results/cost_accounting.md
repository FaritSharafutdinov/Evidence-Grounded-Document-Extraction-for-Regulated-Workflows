# S6 — total cost accounting

Every model call counted (retrieval judges included). Gold v1.3, dev split. Tokens are reported where the backend recorded them; the legacy 7B judge runner did not record tokens, and its call count is taken from the cache.

## Model-touching methods (per method × layer)

| Family | Method | Layer | Backend | Model | n calls | prompt tok | completion tok | wall-clock s |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| S4 extraction battery | M1 | native | mlx | mlx-community/Qwen3.5-2B-MLX-4bit | 20 | 149176 | 14923 | 737.121 |
| S4 extraction battery | M1 | ocr | mlx | mlx-community/Qwen3.5-2B-MLX-4bit | 20 | 146759 | 19159 | 1127.676 |
| S4 extraction battery | M2 | native | mlx | mlx-community/Qwen3.5-2B-MLX-4bit | 160 | 1083048 | 11387 | 3849.962 |
| S4 extraction battery | M2 | ocr | mlx | mlx-community/Qwen3.5-2B-MLX-4bit | 160 | 1063712 | 9179 | 4104.673 |
| S4 extraction battery | M3 | native | mlx | mlx-community/Qwen3.5-2B-MLX-4bit | 86 | 126224 | 2632 | 498.639 |
| S4 extraction battery | M3 | ocr | mlx | mlx-community/Qwen3.5-2B-MLX-4bit | 78 | 111697 | 2468 | 442.959 |
| S4 extraction battery | M4 | native | rules | mlx-community/Qwen3.5-2B-MLX-4bit | 0 | 0 | 0 | 0.0 |
| S4 extraction battery | M4 | ocr | rules | mlx-community/Qwen3.5-2B-MLX-4bit | 0 | 0 | 0 | 0.0 |
| S4 extraction battery | M5 | native | mlx | mlx-community/Qwen3.5-2B-MLX-4bit | 86 | 14198 | 86 | 53.672 |
| S4 extraction battery | M5 | ocr | mlx | mlx-community/Qwen3.5-2B-MLX-4bit | 78 | 12846 | 78 | 35.862 |
| retrieval LLM judge (inherited, old gold) | judge | native | mlx | mlx-community/Qwen2.5-7B-Instruct-4bit | 1303 | n/a | n/a | 8295.7 |
| retrieval LLM judge (inherited, old gold) | judge | ocr | mlx | mlx-community/Qwen2.5-7B-Instruct-4bit | 1303 | n/a | n/a | 8069.8 |
| judge smoke/probe (not a full run) | judge-smoke | both | mlx | mlx-community/Qwen3.5-2B-MLX-4bit | 210 | n/a | n/a | n/a |
| judge smoke/probe (not a full run) | judge-smoke | both | mlx | mlx-community/Qwen2.5-0.5B-Instruct-4bit | 210 | n/a | n/a | n/a |

## Totals by family

| Family | n calls | prompt tok | completion tok | wall-clock s |
| --- | ---: | ---: | ---: | ---: |
| S4 extraction battery | 688 | 2707660 | 59912 | 10850.6 |
| retrieval LLM judge (inherited, old gold) | 2606 | 0 | 0 | 16365.5 |
| judge smoke/probe (not a full run) | 420 | 0 | 0 | 0.0 |
| **ALL** | 3714 | 2707660 | 59912 | 27216.1 |

S4 full battery run wall-clock (sum of per-set latencies in the runner log): **10850.7s ≈ 181 min**.

## Non-LLM methods (0 model calls)

BM25, dense (MiniLM-L6) retrieval and rules-v4 (M4) issue **no** model calls; their cost is CPU wall-clock only and is not the bottleneck (M4 ran in the battery at 0 LLM calls).

## Notes

- M4 (rules-v4) is non-LLM: `n_calls = 0` by construction.
- The Qwen2.5-7B judge numbers are the inherited baseline (old gold) — shown for cost orientation; its 2606 calls (1303 native + 1303 ocr) are the single largest per-run cost of the project (~4.5 h on the M2).
- The Qwen3.5-2B judge has only a 210-call smoke; no full judge run was performed (the S4 extraction battery replaced it for the supervisor's item 2).
- `wall_clock_s` for S4 is the sum of per-call latencies (model time); the runner-log total includes model load overhead.
