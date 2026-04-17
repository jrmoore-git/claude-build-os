# Handoff — 2026-04-16

## Session Focus
Claude 4.7 fresh-eyes audit of BuildOS followed by targeted remediation: Tier 1 fixes, F5 promoted-then-killed, and the first four extractions of the debate.py monolith split.

## Decided
- **Kill auto-capture Stop hook** (replaces F5's reconciliation approach). Auto-capture was never preventing data loss — files stay on disk, `detect-uncommitted.py` catches uncommitted state at `/start`. The hook was converting "uncommitted" into "committed half-work needing reconciliation." Now dead (9e69929).
- **debate.py split strategy: sibling modules, not a package.** Each extraction creates `scripts/debate_<topic>.py` with the function body; debate.py re-imports the name; lazy `import debate` inside the new module pulls shared state. Chosen over a `scripts/debate/` package because tests do `import debate` and reach into ~80 private symbols — package-level re-exports were error-prone. Sibling-module pattern keeps debate.py as the shared-state module and requires no changes to test imports.
- **"User-Facing Output — No Framework Plumbing"** added to `.claude/rules/skill-authoring.md`: rule-of-thumb that skill output must not surface internal flag names, script filenames, or JSON keys (e.g. `SCRIPT_MISSING`, `has_stale_memory`, raw `/tmp/` paths).
- **requirements.txt + requirements-dev.txt pinned.** Tests now fail loudly if pytest is missing instead of silently skipping 913 tests.

## Implemented
- `tasks/audit-2026-04-16-fresh-eyes.md` — 8-finding structural audit
- F2: requirements files + `tests/run_all.sh` exits non-zero on missing pytest
- F3/F4: 34 task artifacts archived (170 → 134)
- audit.db/metrics.db doc cleanup (operational-context.md, changelog, etc.)
- Killed `hook-stop-autocommit.py`, archived to `archive/stop-autocommit/`. Reverted F5's `/start` Step 1f-wrap and `/wrap` Step 5b. Simplified `session-discipline.md`. Trimmed STALE-marker branch from `check-current-state-freshness.py`.
- debate.py split 1/N–4/N: `cmd_check_models`, `cmd_outcome_update`, `cmd_stats`, `cmd_compare` → sibling modules
- L35, L36 added to lessons.md

## NOT Finished
- debate.py split: 6 subcommands remain in the monolith (`cmd_verdict` 250L, `cmd_explore` 193L, `cmd_pressure_test` 262L, `cmd_review` 275L, `cmd_challenge` 265L, `cmd_refine` 385L, `cmd_judge` 515L). `cmd_premortem` is a 7-line shim — probably leave inline.
- Remaining audit findings from `audit-2026-04-16-fresh-eyes.md`:
  - F6 (hook latency telemetry, ~30 min)
  - F7 (external BuildOS user — strategic)
  - F8 (contract test upgrades — opportunistic)
- Historical `[auto-captured]` entries (100+) in `tasks/session-log.md` — deliberately left as historical record per session discussion. Harmless now that the Stop hook no longer generates new ones.
- `stores/debate-log.jsonl` has unstaged runtime appends (test runs during the session) — not part of this wrap commit.

## Next Session Should
1. Resume debate.py split. Next target: `cmd_verdict` (250L, legacy path, lower risk than larger siblings). Follow the pattern landed in 4 commits this session. Full suite is 923 tests in ~7s — run between every extraction.
2. Or pick F6 (hook latency telemetry) for a fast 30-minute win that unlocks demoting hooks that aren't earning their keep.

## Key Files Changed
- scripts/debate.py (-260 lines across 4 commits)
- scripts/debate_check_models.py, debate_outcome.py, debate_stats.py, debate_compare.py (new)
- hooks/hook-stop-autocommit.py → archive/stop-autocommit/
- .claude/settings.json (Stop: [])
- .claude/rules/skill-authoring.md (+ User-Facing Output rule)
- .claude/rules/session-discipline.md (simplified wrap contract)
- tests/run_all.sh (loud fail on missing pytest)
- requirements.txt, requirements-dev.txt (new)
- tasks/lessons.md (+L35, +L36)
- tasks/audit-2026-04-16-fresh-eyes.md (new)
- 34 `tasks/*.md` moved to `tasks/_archive/`
- Docs: hooks.md, changelog-april-2026.md, how-it-works.md, file-ownership.md, CLAUDE.md, current-state.md, operational-context.md
- scripts/check-current-state-freshness.py, scripts/buildos-sync.sh

## Doc Hygiene Warnings
- None
