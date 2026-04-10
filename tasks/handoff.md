# Handoff — 2026-04-10

## Session Focus
Redesigned the multi-model debate system from single adversarial mode to multi-mode thinking tool with adaptive pre-flight discovery.

## Decided
- D5: Thinking modes (explore, pressure-test, pre-mortem) are single-model — prompt design drives quality, not model diversity
- D6: Explore presents 3 bets fork-first, not 1 committed direction — prevents novelty bias skipping the obvious answer
- D7: Pre-flight uses GStack-style adaptive questioning, not batch questionnaires

## Implemented
- 3 new debate.py subcommands: explore, pressure-test, pre-mortem
- 5 prompt files + 3 pre-flight files + 1 adaptive protocol in config/prompts/
- Prompt loader with fallback, --context flag, version tracking
- Updated /debate skill with mode routing and pre-flight step

## NOT Finished
- Explore flow 4.6/5, not 4.7+ — narrow-market fix not applied
- Pressure-test of overall design suggests: measure decision impact, don't over-invest in mode architecture

## Next Session Should
1. Apply narrow-market fix to explore prompt, validate to 4.7+
2. Evaluate whether "explore before work" and "inspect code before answering" need hook-level enforcement
3. Use the new system on a real decision (not simulated) and assess whether it changes the outcome

## Key Files Changed
scripts/debate.py
.claude/skills/debate/SKILL.md
config/prompts/explore.md
config/prompts/explore-diverge.md
config/prompts/explore-synthesis.md
config/prompts/pressure-test.md
config/prompts/pre-mortem.md
config/prompts/preflight-product.md
config/prompts/preflight-solo-builder.md
config/prompts/preflight-architecture.md
config/prompts/preflight-adaptive.md
tasks/decisions.md
tasks/lessons.md

## Doc Hygiene Warnings
None — decisions.md and lessons.md updated this wrap.
