# Handoff — 2026-04-16

## Session Focus
Diagnose and fix the Bash deadlock that bricked the prior session: relative hook paths in `.claude/settings.json` resolve against CWD, so a single mid-session `cd` makes PreToolUse:Bash unable to find its scripts and block every command.

## Decided
- **Settings.json hook commands use `$CLAUDE_PROJECT_DIR/hooks/...` (absolute), not `hooks/...` (relative).** The "avoid `cd`" rule in CLAUDE.md is prose; one slip was enough to deadlock. Promoted to config.
- **L38 added:** Relative hook paths in `.claude/settings.json` cause total Bash deadlock the first time CWD shifts. Source: prior session's `cd scripts && pytest` left CWD in `scripts/` and bricked Bash. Fix shipped this session.

## Implemented
- `.claude/settings.json`: 14 hook entries rewritten to use `$CLAUDE_PROJECT_DIR/hooks/...`. JSON validates.
- `tasks/lessons.md`: L38 appended.

## NOT Finished
- **Settings.json change requires a fresh session to take effect.** Current session is still on the old (relative-path) config — it works only because CWD never shifted here. Next session picks up the absolute paths and is immune to `cd` drift.
- **debate.py split 6/N (cmd_explore extraction)** is on disk uncommitted from the prior session that died from the Bash deadlock:
  - `scripts/debate_explore.py` (untracked) — extraction target
  - `scripts/debate.py` (modified, -192L) — `cmd_explore` removed
  - `stores/debate-log.jsonl` (modified) — runtime audit log appends
  - Test status: `test_basic_explore` passes in isolation; full suite has 3 failures attributed to pre-existing test-ordering pollution (monkeypatch fixture isolation), not the extraction. Verify before committing as split 6/N.
- **Audit findings open** (unchanged): F6 (hook latency telemetry, ~30 min), F7 (external BuildOS user, strategic), F8 (contract tests, opportunistic).
- **debate.py split 7/N onward** (unchanged): `cmd_pressure_test` (262L), `cmd_review` (275L), `cmd_challenge` (265L), `cmd_refine` (385L), `cmd_judge` (515L).

## Next Session Should
1. Verify the absolute-path hooks load — start fresh, run a quick `pwd` + `ls` to confirm Bash still works, then deliberately `cd /tmp && pwd` and confirm a follow-up Bash call still passes the PreToolUse:Bash gate.
2. Triage the uncommitted debate.py split 6/N: rerun the failing tests in isolation, confirm the 3 failures are pre-existing pollution and not extraction regressions, then commit as split (6/N) following the landed pattern.
3. Continue debate.py split 7/N (cmd_pressure_test next).

## Key Files Changed
- .claude/settings.json (14 hook commands → absolute paths)
- tasks/lessons.md (+L38)

## Doc Hygiene Warnings
- None. Active lessons: 13/30.
- Pre-existing uncommitted code in `scripts/debate.py`, `scripts/debate_explore.py`, `stores/debate-log.jsonl` is from the prior session, intentionally left for next session to verify and commit.
