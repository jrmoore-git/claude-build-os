# Handoff — 2026-04-15 (session 5)

## Session Focus
Built, tested, reviewed, and fixed the /simulate skill. Added structural review enforcement.

## Decided
- /simulate SKILL.md: write-to-file execution (not bash -c) for shell quoting safety
- Expanded denylist: eval, source, pip/npm install, tee, dd, mv/cp outside tmp, curl -o to non-tmp
- Expanded env scrub: DATABASE_URL, *_DSN, REDIS_URL, MONGODB_URI, SENTRY_DSN
- Quality-eval inner agent gets explicit safety constraints (matching smoke-test denylist)
- Review-proactive enforcement: hook-based, not advisory — fires on dirty tree + plan + no review artifact
- L25: advisory rules fail under context pressure; recurring violations need hook enforcement

## Implemented
- .claude/skills/simulate/SKILL.md (created, ~380 lines, both modes)
- .claude/skills/elevate/SKILL.md (mktemp BSD fix)
- hooks/hook-intent-router.py (simulate pattern + review-proactive check + _has_uncommitted_changes helper)
- .claude/rules/natural-language-routing.md (simulate routing + proactive pattern)
- CLAUDE.md (skill count 21→22, /simulate in specialist listing)
- tasks/lessons.md (L25 added)
- tests/test_hook_intent_router.py (3 new tests: review-proactive enforcement)
- tasks/elevate-simulate.md (smoke-test report)
- tasks/simulate-skill-review.md (cross-model review, status: revise → fixed)

## NOT Finished
- Battle testing /simulate against diverse skills (user's explicit request for next session)
- Quality-eval mode not yet tested end-to-end (depends on LiteLLM/debate.py availability)

## Next Session Should
1. Battle test: `/simulate /explore --mode smoke-test`, `/simulate /think`, `/simulate /review`
2. Try quality-eval mode on a simpler skill
3. Verify review-proactive hook fires in a real workflow (not just tests)

## Key Files Changed
- .claude/skills/simulate/SKILL.md
- .claude/skills/elevate/SKILL.md
- hooks/hook-intent-router.py
- .claude/rules/natural-language-routing.md
- CLAUDE.md
- tasks/lessons.md
- tests/test_hook_intent_router.py
