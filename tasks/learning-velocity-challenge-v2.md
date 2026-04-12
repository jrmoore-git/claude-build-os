---
topic: learning-velocity
challenge_tier: cross-model
status: proceed-with-fixes
git_head: c4bca4e
producer: claude-opus-4-6
created_at: 2026-04-11T22:25:00-07:00
scope: .claude/skills/healthcheck/SKILL.md, scripts/lesson_events.py
findings_count: 3 material
recommendation: PROCEED-WITH-FIXES
complexity: medium
---
# Challenge v2: Learning Velocity

## Recommendation: PROCEED-WITH-FIXES

The core thesis is validated — measurement, verification, and pruning gaps are real and evidenced. All 3 MATERIAL findings have bounded fixes (SMALL or already addressed in the build). No new subsystems required. Build with the inline fixes below.

**Cost of inaction:** Governance accumulates without feedback. 3/4 tested lessons were stale/wrong (evidenced 2026-04-11). No way to answer "is BuildOS better this month than last month?" The system cannot self-correct at its current scale.

## Inline Fixes (include in build)

1. **Hook-firing telemetry doesn't exist** [MATERIAL, COST:MEDIUM by A — but already resolved]
   The build already uses `Enforced-By:` metadata tags instead of runtime hook logs. Healthcheck verifies tag + file existence. No runtime telemetry needed. **No additional work required.**

2. **Rule-hook redundancy detection mechanism** [MATERIAL, COST:SMALL by A]
   Use explicit `Enforced-By: hooks/X` tags in rule files (already added to 4 rule files). Healthcheck checks: tag exists → hook file exists → no active lessons reference the rule → flag as prune candidate. ~20 lines in healthcheck procedure. **Fix is bounded.**

3. **Auto-investigate needs trust boundaries** [MATERIAL, COST:SMALL by B]
   Build already uses structured claim templates — lesson text is not passed raw. Template: "Lesson <ID> asserts that <title assertion>. Verify whether this is still true." Title is extracted and sanitized. **Fix is bounded — already in the SKILL.md design.**

## Advisory Findings (noted, not blocking)

- **Git log parsing harder than ~15 lines** — Moot. Build uses `lesson-events.jsonl` structured event log, not git parsing.
- **Vanity metrics risk** — Valid. Metrics are labeled directional. Recurrence rate is the primary signal; others are supporting context.
- **Cost guardrail** — 2-3 lessons × $0.05-0.10 = $0.15-0.30 per full scan. Bounded by design.

## What the v1 challenge got wrong

The v1 synthesis (SIMPLIFY, 3 phases) treated every MATERIAL finding as a blocker regardless of fix cost. Two of three MATERIAL findings were already resolved in the design; the third requires ~20 lines. Phasing trivially-fixable work into Phase 2/3 gates produces busywork with no payoff.

## Consensus

| Finding | A (Opus) | B (GPT) | Cost | Resolution |
|---|---|---|---|---|
| Hook telemetry gap | MATERIAL | ADVISORY | MEDIUM (A) / already resolved | Enforced-By tags replace runtime logs |
| Redundancy detection | MATERIAL | — | SMALL | Explicit tag verification in healthcheck |
| Trust boundaries | — | MATERIAL | SMALL | Structured claim templates |

Both responding challengers issued REVISE (not REJECT). Both acknowledged the problem is real and the approach is sound. Disagreements were on implementation details, all with SMALL/MEDIUM cost fixes.
