# DEC-001 — Repository migrated to own fork

**Date:** 2026-10-19 · **Status:** done

**Context.** Maria left the project; the work continued in her repository. Ownership and push access were awkward.

**Decision.** Farit forked the repository (`FaritSharafutdinov/Evidence-Grounded-Document-Extraction-for-Regulated-Workflows`). Local clone kept as-is; `origin` repointed to the fork, Maria's repo kept as `upstream`. No re-clone: gitignored local artifacts (corpus, LLM cache, docs, tasks) were preserved untouched. Local `farit_dev` was 9 commits ahead of the fork — pushed to sync.

**Alternatives considered.** Fresh clone + copying gitignored files (rejected: laborious, error-prone); keeping Maria's repo as origin (rejected: push rights/confusion).

**Consequences.** All pushes go to Farit's fork. `git fetch upstream` available if Maria's repo ever changes.
