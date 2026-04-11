# Current State — 2026-04-10

## ⚠ STALE — auto-captured session ended without /wrap-session
**Auto-capture date:** 2026-04-10 23:41 PT
**Files changed this session:** 9 files in .claude, config, scripts, tasks, tests
**WARNING:** The "Next Action" below may be outdated. Cross-check with `git log --oneline -10` and recent session-log entries.


## What Changed This Session
- Created `.claude/rules/reference/debate-invocations.md` — complete invocation patterns for all debate.py subcommands
- Updated CLAUDE.md infrastructure reference to point to the new invocation doc
- Root cause: prior session wasted 4+ failed CLI calls guessing debate.py arguments; fix puts the patterns where they're read at session start

## Current Blockers
- None identified

## Next Action
Update gstack 0.14.5.0 → 0.16.3.0 and create `scripts/browse.sh` (carried over from prior session).

## Recent Commits
f4b2934 [auto] Session work captured 2026-04-10 23:20 PT
9b436ab Decouple design-shotgun from gstack: env vars + setup script
330eb48 [auto] Session work captured 2026-04-10 21:59 PT
