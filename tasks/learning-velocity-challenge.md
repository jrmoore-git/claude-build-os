---
topic: learning-velocity
challenge_tier: cross-model
status: simplify
git_head: cceaa0d
producer: claude-opus-4-6
created_at: 2026-04-11T21:55:00-07:00
scope: .claude/skills/healthcheck/SKILL.md
findings_count: 3 material
recommendation: SIMPLIFY
---
# Challenge: Learning Velocity

## Recommendation: SIMPLIFY

The core thesis is validated — the measurement and verification gaps are real and evidenced (3/4 tested lessons were stale). But the proposal overreaches on pruning by assuming data that doesn't exist.

## Consensus Findings (3/3 models agree)

### 1. Hook firing telemetry doesn't exist [MATERIAL — all 3]
The pruning feature asks "has this hook fired in the last 30 days?" but the 17 hooks have zero firing telemetry. No `hook_log`, no `last_triggered`, no counters anywhere. This isn't a healthcheck addition — it's a new subsystem. **Rule redundancy** (does a hook enforce this rule?) is feasible via metadata, but **hook activity** (has it fired recently?) requires infrastructure that doesn't exist.

**Fix:** Defer hook activity pruning entirely. For rule/hook redundancy, use explicit `Enforced-By: hooks/X` metadata tags in rule files (Challenger C's alternative) instead of semantic matching. Healthcheck verifies the tag + file existence — no LLM inference needed.

### 2. Git log parsing is harder than "~15 lines" [MATERIAL — A, C]
Commit history is auto-generated messages on a single day. Extracting lesson creation dates, status transitions, and promotions requires parsing markdown table diffs across commits where multiple lessons change per commit. Realistic estimate: 50-80 lines with edge cases. At current scale (~12 lessons), git archaeology may not be worth the complexity.

**Fix (two options):**
- **Option A:** Structured event logging — append `{timestamp, lesson_id, from_status, to_status}` to `stores/lesson-events.jsonl` at the point of status change. Makes all metrics trivial. Small new infrastructure, but correct.
- **Option B:** Start with just recurrence rate (simplest metric — count of lessons that reference the same area/pattern). Defer the other 3 metrics until scale justifies them.

### 3. Auto `/investigate --claim` needs trust boundaries [MATERIAL — B]
Lesson text is freeform and can contain arbitrary content (error messages, model output, user quotes). Auto-feeding it into `/investigate --claim` creates a prompt injection surface into the cross-model panel. Lesson content must be treated as untrusted input.

**Fix:** Strip lesson text to structured claim fields before passing to investigate. Or: pass only the lesson ID and rule text, not the freeform source/description.

## Advisory Findings

- **Vanity metrics risk (C):** "Learning velocity" via git churn doesn't answer "are we making fewer mistakes?" High churn could mean thrashing. Focus on recurrence rate — the one metric that directly answers the question.
- **Cost guardrail is adequate (all 3):** 2-3 lessons at $0.05-0.10 each is well-bounded. But gate auto-investigation behind an explicit flag until trust boundaries are hardened.
- **Redundancy false positives (B, C):** Semantic matching between rules and hooks will hallucinate equivalences. Explicit metadata tags are safer and cheaper.

## What survives the challenge

| Proposed | Verdict | Notes |
|---|---|---|
| Velocity metrics in /healthcheck | SIMPLIFY | Start with recurrence rate only. Add structured event logging for the rest. |
| Auto /investigate --claim on stale lessons | PROCEED with guardrails | Hardcode claim template, treat lesson text as untrusted, gate behind flag initially |
| Rule/hook redundancy pruning | SIMPLIFY | Use `Enforced-By:` metadata tags, not semantic matching. Defer hook activity tracking. |
| Positive capture | DROP (already handled) | Rules already encode validated patterns. No new mechanism needed. |

## Recommended scope

**Phase 1 (now):** Add recurrence rate metric to `/healthcheck` Step 6. Add `Enforced-By:` tag convention to rule files. Healthcheck verifies tags.

**Phase 2 (after Phase 1 proves useful):** Add `stores/lesson-events.jsonl` for structured status tracking. Compute full velocity metrics from events, not git log.

**Phase 3 (after trust boundaries hardened):** Auto `/investigate --claim` on top 3 stalest lessons during full healthcheck scan. Structured claim template only — no freeform lesson text in prompts.
