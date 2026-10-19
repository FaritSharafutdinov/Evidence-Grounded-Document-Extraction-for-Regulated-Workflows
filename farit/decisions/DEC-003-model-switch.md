# DEC-003 — Working model: switch to Qwen3.5-2B, hub for full runs

**Date:** 2026-10-19 · **Status:** decided (Farit)

**Context.** Scouting-phase LLM results were produced with Qwen2.5-7B-4bit (MLX, local M2 — a full judge run took ~4.5 h). Farit has a GPU hub allowance (60 points/month) that was idle. Qwen3.5 (released 2026) offers a 2B model with a newer architecture that is claimed competitive with older 7B models — cheaper and faster.

**Decision.** Qwen3.5-2B becomes the working LLM for new experiments. Pipeline per experiment: **local smoke first** (`mlx-community/Qwen3.5-2B-MLX-4bit`; fallback `Qwen3.5-2B-OptiQ-4bit` if the VLM-tagged build breaks `mlx_lm`) → **full run on the hub** (vLLM backend; `llm_reranker.py` was designed with isolated model access for this). The LLM-judge baseline will be re-run on Qwen3.5-2B so that any new comparison table is same-model throughout.

**Constraints this does NOT change.** Frozen scouting results (Qwen2.5-7B) stay untouched and labeled with their model; every new result records its model in `configuration`; comparisons across tables never mix models.

**Side benefit.** "Does a 2B of a newer architecture match a 7B of an older one on the judge task?" is itself a measurable cost-quality datapoint for the report — our testbed answers it for free.

**Risks.** (a) The marketing claim may not hold on SDS evidence judging — that is a finding, not a failure. (b) Hub runs need a vLLM path in the code — planned anyway as the TASK-005 fallback.
