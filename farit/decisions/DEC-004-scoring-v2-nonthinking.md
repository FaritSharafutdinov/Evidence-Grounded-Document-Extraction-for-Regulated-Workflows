# DEC-004 — Judge scoring on Qwen3.5: non-thinking mode, fp32-host softmax, versioned cache

**Date:** 2026-10-21 · **Status:** decided (Farit)

**Context.** TASK-010 (smoke of Qwen3.5-2B, the DEC-003 working model) found a blocker: the model's chat template opens a `<think>` channel by default, so the first generated token — which the judge's scoring reads as P(Yes)/P(No) — is a thinking token. Both probabilities collapse to the distribution tail (~1e-6/1e-8) and their ratio is noise: on a 9-page probe, scores compressed into a 0.967–0.983 band with no discriminative signal (reproduced bit-exactly by two independent K3 reruns, `farit/logs/TASK-010/`). Two further findings: (a) the cache key hashes the raw prompt *before* the chat template, so scores from different template modes would silently mix under one model tag; (b) this build's logits are bfloat16 (Qwen2.5-7B was float16), so the TASK-009 fp16-ladder numbers do not transfer.

**Decision.**

1. Judge scoring on Qwen3.5 runs in **non-thinking mode** (`enable_thinking=False`), applied conditionally so the frozen Qwen2.5 path stays byte-identical (its template does not accept the kwarg).
2. **Scoring mode becomes part of the cache identity** — v1 (legacy, frozen semantics) vs v2 (non-thinking + fp32-host softmax) write to different cache files; scores from different modes never mix.
3. New (v2) runs compute the softmax **in fp32 on host** from the raw logits (design note from TASK-009), eliminating the device-precision exp-collapse class of artifact for new results.
4. A **thinking-mode variant** of the judge is postponed to the backlog as a bounded cost–quality experiment (candidate subset: derived-field instances, where Qwen2.5-7B failed) — not part of unblocking S4.

**Alternatives considered.** (a) Adapt the pipeline to thinking mode (generate the full trace, read the post-think answer token) — rejected as the default path: tens of times more tokens per page-scoring call, new parse failure modes, and a rewrite of the frozen scoring contract; kept as the backlog experiment instead. (b) Score under the default thinking template — measured to be noise (see above). (c) Ship both variants at once — deferred until the smoke passes on v2.

**Consequences.** Frozen Qwen2.5-7B results stay untouched and reproducible via the v1 path. Every Qwen3.5 table records `score_mode: v2` (non-thinking, fp32-host) in its configuration. If the backlog experiment later shows real gains from thinking on derived fields, this decision is revisited with numbers in hand.

**Side benefit.** Non-thinking mode is also the cheap mode: one forward pass per page, which matters for the hub budget (S6 cost accounting).
