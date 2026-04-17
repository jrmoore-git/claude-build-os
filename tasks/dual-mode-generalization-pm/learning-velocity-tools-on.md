---
debate_id: learning-velocity-tools-on
created: 2026-04-17T14:51:12-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# learning-velocity-tools-on — Challenger Reviews

## Challenger A (pm) — Challenges
## Challenges

1. [OVER-ENGINEERED] [MATERIAL] [COST: MEDIUM]: Coupling expensive, high-latency LLM operations (`/investigate --claim` and rule/hook redundancy analysis) to `/healthcheck` violates the contract of a healthcheck. Healthchecks are typically fast, deterministic observability tools. Adding 60-90 seconds of blocking LLM calls (2-3 lessons * ~30s each [EVIDENCED]) changes the UX drastically. Scheduled verification and pruning analysis should be handled by a dedicated background job or distinct command (e.g., `/audit-governance`), not shoehorned into a status check.

2. [ASSUMPTION] [MATERIAL] [COST: TRIVIAL]: The proposal suggests deriving velocity metrics from "git log on tasks/lessons.md". This ignores existing infrastructure: `scripts/lesson_events.py` already tracks lesson lifecycle events deterministically in `stores/lesson-events.jsonl` and has a `metrics` command. Rebuilding this via git log math is unnecessary, brittle, and introduces edge cases around commit squashing and rebasing.

3. [RISK] [ADVISORY]: The pruning capability flags rules/hooks based on whether a hook has fired in the last 30 days. This creates a false negative risk for "guardrail" hooks (e.g., security checks or destructive action blocks) which may legitimately not fire for months because the behavior is rare, but are still critically load-bearing. 

## Concessions
1. Identifying that governance only ever accumulates is a highly accurate diagnosis of a common system failure.
2. Targeting only the top 2-3 stalest lessons rather than scanning all 12+ is a practical, cost-conscious approach.
3. Keeping pruning as "flag for review" rather than "auto-delete" correctly respects the destructive risk of removing enforcement.

## Verdict
REVISE: Drop the brittle git log math in favor of the existing `lesson_events.py` metrics, and move the expensive LLM-based verification/pruning steps out of the synchronous `/healthcheck` flow into a distinct governance audit task.

---
