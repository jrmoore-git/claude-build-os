---
scope: "New /healthcheck skill + silent governance checks wired into /start and /wrap"
surfaces_affected:
  - ".claude/skills/healthcheck/SKILL.md"
  - ".claude/skills/start/SKILL.md"
  - ".claude/skills/wrap/SKILL.md"
  - ".claude/skills/review/SKILL.md"
verification_commands:
  - "cat .claude/skills/healthcheck/SKILL.md | head -5"
  - "grep -c 'healthcheck\\|governance health' .claude/skills/start/SKILL.md"
  - "grep -c 'healthcheck\\|governance health' .claude/skills/wrap/SKILL.md"
  - "grep -c 'healthcheck' .claude/skills/review/SKILL.md"
rollback: "rm -rf .claude/skills/healthcheck/ && git checkout .claude/skills/start/SKILL.md .claude/skills/wrap/SKILL.md .claude/skills/review/SKILL.md"
review_tier: "T1 — new skill + modifies 3 existing skills"
verification_evidence: "All 4 verification commands pass: healthcheck SKILL.md exists (5-line header confirmed), /start has 6 healthcheck/governance references, /wrap has 1 healthcheck reference, /review has 8 healthcheck references (redirect + --all + table + cost). Verified 2026-04-11."
---

# Plan: /healthcheck skill + automated governance hygiene

## What

1. Extract governance scan from `/review --governance` into standalone `/healthcheck` skill
2. Wire silent lightweight checks into `/start` and `/wrap`
3. Add auto-trigger conditions so full scan runs when needed, not when remembered
4. Redirect `/review --governance` to `/healthcheck`

## Three layers

| Layer | Where | Trigger | What |
|---|---|---|---|
| Silent | `/start` Step 1g, `/wrap` Step 1b | Every session | Lesson count, Resolved-still-Active, days since last scan |
| Auto full | `/healthcheck` auto-trigger | >7d since scan, lessons >25, post-investigate flag | Full 6-step governance scan |
| Manual | `/healthcheck` | User calls it | Same full scan |

## Files changed

1. `.claude/skills/healthcheck/SKILL.md` — new (extracted from /review --governance + auto-triggers)
2. `.claude/skills/start/SKILL.md` — add Step 1g (silent governance health)
3. `.claude/skills/wrap/SKILL.md` — add Step 1b (silent governance cleanup)
4. `.claude/skills/review/SKILL.md` — redirect --governance to /healthcheck
