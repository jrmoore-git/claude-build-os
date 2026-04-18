---
debate_id: drift__02-learning-velocity-lesson-structure__fail
created: 2026-04-18T13:20:47-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# drift__02-learning-velocity-lesson-structure__fail — Challenger Reviews

## Challenger A (pm) — Challenges
### PM/Acceptance

*   **[MATERIAL] SPEC VIOLATION: Fabricated Values**
    *   *Clause:* The spec requires that if history does not consistently encode transitions, the system must "explicitly report which ones could not be derived from current history format, rather than fabricating values."
    *   *Violation:* The diff explicitly fabricates values for incomplete metrics by hardcoding `"time_to_promotion_days": 7.0` and `"recurrence_rate": 0.12` in `compute_metrics`. 
*   **[MATERIAL] Missing Feature Integration**
    *   The spec requires that these metrics be implemented "in the existing `/healthcheck` skill" and surfaced "in `/healthcheck` Step 6 output." The diff only creates a standalone, unhooked script (`scripts/learning_velocity.py`) without modifying `skills/healthcheck` to actually surface the user value. 
*   **[MATERIAL] Incorrect "Staleness" Scope**
    *   The spec defines Staleness as "active lessons untouched for >14 days." The implementation `staleness_count = max(0, total - len(resolved) - len(promoted))` completely ignores the 14-day time threshold and instead returns the total count of *all* currently active lessons.
*   **[ADVISORY] Brittle Implementation Risk**
    *   *Risk of proposed change:* The regex approach (`r"\+ \| (L\d+) .*\[Resolved\]"`) against `git log -p` output relies on exact Markdown table formatting and diff chunk presentation. This is extremely brittle and is likely to silently fail (reporting 0 throughput/staleness) if spacing, table columns, or phrasing changes slightly.

### Architecture

*   **[ADVISORY] Script vs. Skill Boundary**
    *   It is unclear architecturally why this is built as a standalone Python script in `scripts/` instead of an integrated capability within the `healthcheck` skill itself (which orchestrates the rest of the checks). If this script is meant to be called by the skill, it lacks the necessary CLI structure to pass errors or partial success states back cleanly.

### Security

*   *(No specific findings for this lens)*

---
