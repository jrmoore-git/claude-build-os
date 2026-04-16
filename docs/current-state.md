# Current State — 2026-04-15

## What Changed This Session
- D22 critique loop spike: validated that directive injection degrades simulation quality (2.50→1.78 avg across 3v3 trials)
- 3-model pre-mortem confirmed wrong mechanism — eval_intake improved by editing skill prompts, not runtime injection
- /simulate smoke-test tested against N=23 skills, found 0 real issues (29 false positives) — no standalone value
- Shelved entire sim ecosystem: /simulate skill removed, 7 scripts + 5 test files + 40+ task artifacts archived to archive/sim/
- All GitHub-facing docs cleaned: CLAUDE.md (22 skills), README, cheat-sheet, routing rules, intent router
- D9 read-before-edit hook committed (built session 16, never committed)
- .gitignore updated to exclude .claude/projects/ (per-machine memory directory)

## Current Blockers
- None identified

## Next Action
Choose next product work. Context-packet-anchors has challenge+judgment on disk (archive/sim/tasks/), or pick something new.

## Recent Commits
d9139f8 Shelve sim ecosystem: archive to archive/sim/, remove from active codebase
26adb6e [auto] Session work captured 2026-04-15 22:19 PT
7077eca Session wrap 2026-04-15: README adoption rewrite, cross-model reviewed
