# Handoff — 2026-04-14

## Session Focus
Gemini timeout hardening, compaction protocol refinement (research-grounded), healthcheck gap fix.

## Decided
- D18: Keep Gemini 3.1 Pro with timeout/fallback (not Grok 4, not 2.5 downgrade)
- D19: compactPrompt is not a valid settings.json field — only CLAUDE.md Compact Instructions works
- Compaction thresholds replaced: old 55/70% aspirational → research-grounded protocol (context rot is continuous from ~25%)
- /wrap now auto-triggers full healthcheck when >7d overdue (same marker as /start)

## Implemented
- Per-model timeout (120s for Gemini) + _call_with_model_fallback in debate.py
- Code review fixes: used_model variable (loop mutation bug), fallback failure logging
- `## Compact Instructions` section in CLAUDE.md
- Research-grounded compaction protocol in session-discipline.md
- Healthcheck >7d auto-trigger added to /wrap skill
- Documentation: infrastructure.md (timeout table), how-it-works.md (challenge synthesis + fallback)

## NOT Finished
- Nothing outstanding

## Next Session Should
1. Run `/start` — first session with healthcheck auto-trigger, verify it works
2. Consider running manual `/healthcheck` — no `[healthcheck]` marker exists in session-log yet

## Key Files Changed
- scripts/debate.py
- CLAUDE.md
- .claude/rules/session-discipline.md
- .claude/skills/healthcheck/SKILL.md
- .claude/skills/wrap/SKILL.md
- docs/infrastructure.md
- docs/how-it-works.md
- tasks/decisions.md

## Doc Hygiene Warnings
- None
