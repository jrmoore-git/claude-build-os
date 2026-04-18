---
debate_id: new_defect__02-learning-velocity-staleness-threshold__pass
created: 2026-04-18T13:21:36-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# new_defect__02-learning-velocity-staleness-threshold__pass — Challenger Reviews

## Challenger A (pm) — Challenges
### Spec Constraints & Negative Compliance
* **MUST NOT**: "never auto-prune."
* **EXPLICITLY EXCLUDED**: "Positive signal capture as a new system"
* **EXPLICITLY EXCLUDED**: "Dashboards or reporting UI: Metrics surface entirely in `/healthcheck` CLI output."
* **EXPLICITLY EXCLUDED**: "Automated pruning: Pruning candidates are flagged for the user to delete; the system does not delete files itself."
* **EXCEPTION**: "unless the hook is tagged as `[critical]` or is a security invariant."

*The diff does not violate any of these negative constraints, primarily because it omits almost all of the required functionality.*

### PM/Acceptance

*   **[MATERIAL] Missing Spec Implementation (Positive Compliance):** The spec explicitly requires four Git-derived velocity metrics (Time-to-Resolution, Promotion Rate, Active Lifespan, Churn/Recurrence) as the core value delivery in Step 1. The diff implements none of them, only providing a basic script to count stale lessons.
*   **[MATERIAL] Missing Integration:** The recommendation is to "Add three capabilities to the existing `/healthcheck` skill". The diff introduces a standalone script (`scripts/learning_velocity.py`) and makes no modifications to `skills/healthcheck`, failing to deliver the user value where requested.
*   **[ADVISORY] Premature Configuration:** The script adds support for a `config/learning_velocity.json` file to override the 14-day staleness threshold. The spec defines the trigger simply as "older than 14 days." Adding file-based config parsing before the core metrics are even built is unnecessary scope creep.
*   **Risk Evaluation:**
    *   **Risk of proposed change:** Merging this diff introduces disconnected, unused code that fails to establish the learning loop, creating technical debt without addressing the problem.
    *   **Risk of NOT changing:** If we reject this and do nothing, BuildOS will continue its one-way governance growth, increasing session drag and context token consumption while persisting stale rules [EVIDENCED: spec cites 3 out of 4 active lessons contained stale/wrong information during a manual check].

### Architecture

*   **[MATERIAL] Rollout Sequence Violation:** The spec defines a strict implementation sequence: "The metrics should land first so `/healthcheck` output remains interpretable". The diff skips Step 1 (the 4 metrics) and jumps into building the staleness check (part of Step 2), ignoring the architectural roadmap laid out in the spec.

---
