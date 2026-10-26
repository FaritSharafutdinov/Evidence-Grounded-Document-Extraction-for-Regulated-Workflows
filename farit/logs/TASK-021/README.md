# TASK-021 — M6 hub run provenance (K3)

M6 (section-routed individual-field) was implemented by K3, smoke-tested on local
MLX (sds_05), then run on the **same canonical hub config** as the rest (DEC-007).
This log closes the verification chain the 2026-10-26 critic flagged (finding C2).

## Run

- Command (hub): `METHODS=M6 JOB=battery SKIP_TESTS=1 bash farit/hub/run_on_hub.sh`
- Hub repo HEAD: see `hub-HEAD.txt` (`79e9c23`); config = `Qwen/Qwen3.5-2B` bf16, vLLM (A100 MIG), gold v1.3, dev only.
- Only M6 was fresh (M1–M5 came from the canonical cache); evaluate re-scored all six methods.

## K3 verification (from raw predictions, not the agent report)

- Independent re-score of `s4_M6_{native,ocr}.json` via `sdsbench.evaluator`:
  **M6 native 17.9% / ocr 8.6%** — matches the hub table.
- Routing coverage (`farit/results/m6_routing_coverage.md`): the hand-written map
  keeps the gold-evidence page in **126/134 (94%)** instances (all pages: 121/134, 90%).
- State transitions (`farit/results/state_anomaly.md`): of M1's 124 native-correct
  states, M6 keeps 50 and flips 74.
- S5 on six methods: taxonomy 14/9/1, **gap unchanged at 12/24**; M6 solves 2 evidence
  cases that were already solved.
- `claims_audit` gate green.

## Result

M6 = 17.9/8.6 (below M1/M2 in aggregate; native gap = 1 instance). Section routing
halves the prompt vs M2 but does **not** shrink the residue. Full table in
`s4_battery_goldv13.{json,md}`.