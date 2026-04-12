# Handoff — 2026-04-11

## Session Focus
Built discoverability infrastructure so users never need to memorize skills — natural language routing with deterministic hooks, /guide skill, and YAML description fixes.

## Decided
- Natural language is the primary interface; slash commands are power-user shortcuts (D16)
- Three-layer routing: advisory rule → deterministic intent hook → proactive error tracker
- Hook-based routing is advisory (suggest, not block) — nag prevention via session-scoped tracker files
- YAML multiline `|` in skill descriptions breaks Claude Code's `/` menu — use single-line quoted strings only (L22)

## Implemented
- `hooks/hook-intent-router.py` — UserPromptSubmit hook, 13 compiled regex patterns, proactive /investigate on recurring errors
- `hooks/hook-error-tracker.py` — PostToolUse:Bash hook, passive observer, error signature normalization
- `.claude/skills/guide/SKILL.md` — intent-based skill map ("I want to...")
- `.claude/rules/natural-language-routing.md` — 18 intent-to-skill mappings + 8 proactive patterns
- Fixed YAML descriptions on 6 skills (design, elevate, investigate, research, sync, think)
- Updated README, getting-started, cheat-sheet, hooks docs
- Added L22, D16, wrap skill read-before-write rule

## NOT Finished
- Live test of intent router in a fresh session (all 20/20 in unit tests, not yet exercised end-to-end)
- Parallel session left: L13/L14/L15 staleness unverified, live /challenge test on new proposal

## Next Session Should
1. Start a fresh session to test intent routing end-to-end (hook fires on real user messages)
2. Optionally verify L13/L14/L15 staleness, test /challenge on a real proposal

## Key Files Changed
hooks/hook-intent-router.py, hooks/hook-error-tracker.py
.claude/skills/guide/SKILL.md, .claude/rules/natural-language-routing.md
.claude/skills/{design,elevate,investigate,research,sync,think}/SKILL.md
.claude/settings.json, CLAUDE.md, README.md
docs/getting-started.md, docs/cheat-sheet.md, docs/hooks.md
tasks/lessons.md (L22), tasks/decisions.md (D16)

## Doc Hygiene Warnings
None
