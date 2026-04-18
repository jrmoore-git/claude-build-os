---
debate_id: new_defect__02-learning-velocity-staleness-threshold__fail
created: 2026-04-18T13:21:22-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# new_defect__02-learning-velocity-staleness-threshold__fail — Challenger Reviews

## Challenger A (pm) — Challenges
### PM/Acceptance Review

**Risk of Proposed Change:** The proposed script introduces an orphaned tool (`scripts/learning_velocity.py`) that fails to integrate with the system, adding dead code without delivering user value. It computes staleness but does not trigger the mandated investigation or cap the results to control costs. 

**Risk of NOT Changing (Current State):** Without implementing the metrics and automated triggers, the system will continue to accumulate unchecked, stale lessons (as evidenced by the manual investigation finding 3 out of 4 lessons contained stale/wrong information). Governance will continue its one-way growth without validation.

#### Specification Compliance & Exceptions
* **EXCEPTION/MUST NOT:** "never auto-prune" (Compliant: No auto-pruning introduced).
* **EXPLICITLY EXCLUDED:** Dashboards or reporting UI (Compliant: CLI JSON output only).

#### Findings

**[MATERIAL] Missing Capability: Velocity Metrics**
The spec requires four specific Git-derived metrics: Time-to-Resolution, Promotion Rate, Active Lifespan, and Churn/Recurrence. The diff implements none of these, fundamentally failing Step 1 of the rollout plan.

**[MATERIAL] Missing Integration: `/healthcheck` and Investigation Trigger**
The spec requires these capabilities to be added to the existing `/healthcheck` skill and to automatically trigger `/investigate --claim` on the selected stale entries. The diff simply dumps JSON to stdout from a standalone script, abandoning the user value of automated verification.

**[MATERIAL] Missing Capability: Pruning Flags**
The spec explicitly outlines a pruning check (Step 3) to flag redundant rules and stale hooks (older than 30 days, respecting the `[critical]` exemption). This logic is completely missing from the implementation.

**[ADVISORY] Missing Constraints: Capping and Sorting**
For the one feature it does attempt (stale lesson detection), the spec requires ranking by staleness and capping at 3 items to control cost (**EVIDENCED:** limits cost to $0.15–$0.30 per run). The script returns an unsorted array of *all* stale lessons, violating the cost-control constraint if it were to be wired up to the investigator.

---
