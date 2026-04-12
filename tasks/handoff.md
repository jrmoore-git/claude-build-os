# Handoff — 2026-04-11

## Session Focus
Made BuildOS discoverable without memorization — natural language routing as primary interface, deterministic intent routing via hooks, all docs updated.

## Decided
- Natural language is the primary interface; slash commands are power-user shortcuts
- Deterministic routing via UserPromptSubmit hook (suggests, doesn't block)
- Proactive routing via PostToolUse error tracking (same error 2x → suggest /investigate)
- Nag prevention: each skill suggested at most once per session

## Implemented
- Fixed 6 broken YAML multiline skill descriptions (design, elevate, investigate, research, sync, think)
- Fixed orphaned `Benefits from:` line in elevate SKILL.md that corrupted frontmatter
- Created `/guide` skill — intent-based skill map at `.claude/skills/guide/SKILL.md`
- Created `.claude/rules/natural-language-routing.md` — routing table + proactive pattern recognition
- Built `hooks/hook-intent-router.py` (UserPromptSubmit) — 13 intent patterns, session-scoped nag prevention
- Built `hooks/hook-error-tracker.py` (PostToolUse:Bash) — recurring error detection, feeds into intent router
- Wired both hooks in `.claude/settings.json`
- Updated README.md ("You Don't Need to Memorize Anything" section, skill count 18→19, /guide in table)
- Updated docs/getting-started.md, docs/cheat-sheet.md, docs/hooks.md (15→17 hooks), CLAUDE.md

## NOT Finished
- `tasks/lessons.md` not updated with YAML multiline description lesson
- `tasks/decisions.md` not updated with routing architecture decision
- Live testing of intent router in a fresh session (settings.json changed mid-session)

## Next Session Should
1. Start a fresh session to test intent router live — type natural language and verify routing suggestions appear
2. Add lesson about YAML `|` descriptions breaking Claude Code's skill menu
3. Add decision entry for natural-language-routing-as-primary-interface architecture

## Key Files Changed
- .claude/skills/guide/SKILL.md (NEW)
- .claude/rules/natural-language-routing.md (NEW)
- hooks/hook-intent-router.py (NEW)
- hooks/hook-error-tracker.py (NEW)
- .claude/settings.json (UserPromptSubmit + PostToolUse:Bash hooks added)
- .claude/skills/{design,elevate,investigate,research,sync,think}/SKILL.md (description fixes)
- CLAUDE.md, README.md, docs/getting-started.md, docs/cheat-sheet.md, docs/hooks.md

## Doc Hygiene Warnings
- ⚠ lessons.md NOT updated — add: YAML multiline `|` descriptions break `/` menu
- ⚠ decisions.md NOT updated — add: natural-language routing as primary interface
