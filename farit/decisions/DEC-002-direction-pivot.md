# DEC-002 — Direction pivot: from completeness checker to error detection & repair

**Date:** 2026-10-19 · **Status:** hypothesis (supervisor's wording), pending confirmation after this week's report

**Context.** After the scouting phase (4 baselines, separation analysis, budget curves) the leading candidate was an *evidence-completeness auditor* (premise decomposition + cascades + calibrated abstention). The supervisor judged it "not yet a strong new research contribution" and proposed a more general problem: AI finds correct information but misunderstands what it belongs to, misses context, or combines evidence incorrectly — detect and repair.

**Decision.** Pause all auditor-flavored system building. This week: reproduce, audit evaluation, simple baselines, real error cases (see `SPRINT.md`). The error taxonomy from the ~24 real extraction cases will ground whether the detection-and-repair hypothesis holds on our data.

**Alternatives considered.** (a) Continue with the auditor as planned — rejected per supervisor. (b) Jump straight to building detection/repair — rejected per supervisor ("do not build a complicated new system yet").

**What survives from the scouting phase regardless of the final topic:** the corpus + metrics + baselines as the measurement layer; the verified failure analysis; the transparency workflow (experiment READMEs, decision log, human-verified numbers).
