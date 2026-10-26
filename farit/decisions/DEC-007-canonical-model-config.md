# DEC-007 — Canonical S4 model config, and the prompt↔schema contract

**Date:** 2026-10-26 · **Status:** decided (Farit)

**Context.** The S4 battery has to be apples-to-apples, but it was being run on two
different artifacts of the same model family:

- local: `mlx-community/Qwen3.5-2B-MLX-4bit` (4-bit, Apple MLX);
- hub:   `Qwen/Qwen3.5-2B` (bf16, vLLM on the A100 MIG).

These are **not the same weights**: 4-bit quantization is lossy, and the runtimes
differ. The 2026-10-26 hub run made this concrete — M2 native came out 16.4% on
the hub vs 19.3% locally on identical prompts. A "hub parity" table that mixes the
two is not a real comparison.

A single quantization cannot be shared across the two runtimes: MLX-4bit is an MLX
format vLLM cannot serve, and vLLM's 4-bit (AWQ/GPTQ/FP8) is a different quantizer —
so "4-bit everywhere" would still be two different weight sets. bf16 is the only
precision both runtimes consume identically, and **bf16 on the Mac does not fit in
memory**.

**Decision.**

1. **Canonical reported config = hub bf16**: `Qwen/Qwen3.5-2B` served by vLLM on the
   A100 MIG, scored against gold v1.3. Every S4 number that reaches the supervisor
   comes from this config (`--backend openai`).
2. **Local MLX 4-bit is dev/smoke only.** Its numbers are never reported as
   canonical and must be labelled `mlx 4-bit (dev)` wherever they still appear.
3. **Judge** stays a separate table: the frozen Qwen2.5-7B reranker is untouched;
   the 2B pointwise judge is run on the hub (`llm_reranker.py --backend openai`).
4. **Prompt↔schema contract (the 2026-10-26 incident).** The battery sends
   `LlmOutput`/`LlmField` JSON-schemas as `response_format`. The prompt templates
   must describe the *same* shape (`evidence`/`premises`/`citation`), never the flat
   `page`/`quote` form: MLX does not enforce the schema (so a flat template silently
   worked), vLLM does (so the mismatch made the model emit `evidence: null` and
   collapsed M1/M3/M5 to ~0%). Enforced by `farit/tests/test_prompt_schema_alignment.py`
   and by the runner's citation-contract gate.

**Alternatives considered.** (a) 4-bit everywhere — rejected: two different
quantizers ⇒ still not the same weights, and no single artifact spans the runtimes.
(b) bf16 everywhere — rejected on hardware: the Mac lacks the memory. (c) Keep
mixing both and report a caveat — rejected: it undermines the baseline comparison.

**Consequences.** The week's S4 table is re-run on the hub bf16 config (M1/M2 prompts
fixed first). The earlier local MLX numbers become dev-only. Cost/parity statements
must name the config ("A100 MIG, bf16, vLLM") explicitly. `RESTORE-ENV.md` from the
hub run records the working stack (vLLM 0.19.1, torch 2.10.0+cu128, CUDA 12.5).

**Addendum (2026-10-26, after the canonical re-run — critic N2/N3/N11).** The
motivating observation originally cited here ("M2 native 16.4 hub vs 19.3 local,
identical prompts") came from the **prompt-broken first hub run** and is superseded:
on the fixed run M2 native is **21.4%**, i.e. the hub is *higher* than the (stale)
local 19.3%. The decision (canonical = hub bf16) stands, but its rationale is the
*reproducibility/weight-identity* argument, not that single number. The run's
provenance is now committed in `farit/logs/TASK-020/` (hub HEAD, env, pip-freeze);
`RESTORE-ENV.md` lives there (the earlier dangling reference is resolved).