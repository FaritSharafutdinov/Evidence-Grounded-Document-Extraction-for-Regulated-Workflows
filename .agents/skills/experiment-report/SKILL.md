---
name: experiment-report
description: Write or update an experiment README (farit/experiments/EXP-NN-*/) in the project template, including mermaid pipeline and Decisions-for-Farit section
type: prompt
whenToUse: When an experiment finishes and needs its report, or when the user asks to document an experiment
arguments:
  - exp_id
metadata:
  opencode/slash: "true"
---

Write the experiment report for $exp_id as `farit/experiments/$exp_id/README.md`.

Template (see `farit/experiments/EXP-05-llm-reranker/README.md` as the reference example):

1. Header: status (in progress / done, verified), dates, code paths, result paths.
2. **Why (hypothesis)** — what question this experiment answers; link the steering action item / sprint item.
3. **Method** — short prose + a mermaid `flowchart LR` diagram of the data flow (inputs → processing → metrics).
4. **Config** — model (exact id), split, filters, runtime, hardware.
5. **Results** — verified numbers only; mark anything unverified explicitly.
6. **Nuances (what the headline hides)** — cost, caveats, failure modes, degenerate cases.
7. **Verification** — which checks were applied (invariants, determinism scope, spot-checks), with evidence links (`farit/logs/…`).
8. **Decisions for Farit** — every judgement call made by the AI workflow, listed for the human to confirm or override. This section is mandatory even if short.

Language: English (the report may be sent to the supervisor). Keep it to one screen where possible — detail goes to `farit/results/` and `farit/logs/`, not here.
