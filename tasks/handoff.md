# Handoff — 2026-04-16

## Session Focus
Verified absolute-path hooks survive CWD drift, then triaged the uncommitted debate.py split 6/N. Discovered prior session's "pre-existing test pollution" diagnosis was wrong — the 3 TestCmdExplore failures were caused by the extraction surfacing a latent module-identity split (L39). Fixed root cause in 3 + 1 test files, shipped split 6/N, then ran a full /challenge → /plan → build → /review --qa cycle to course-correct the entire refactor toward package style.

## Decided
- **D25**: debate.py split moves to package style (`scripts/debate_common.py`), not sibling leaves with lazy `import debate`. Migration is incremental: simplest version shipped (4 helpers + 2 constants); cost tracking next (atomic per F4); prompt loader / `_load_config` / `_log_debate_event` / remaining `cmd_*` follow.
- **L39**: Monolith extractions surface latent module-identity splits when test files manipulate `sys.modules`. Refines L36 with the boundary condition. Captured this morning during split 6/N triage.
- **Architectural recalibration**: original F1 audit's "half a day, zero risk" was off 3-5x and empirically wrong. The recalibration was driven by the user pushing back ("you were the one who said we needed to do it?") — without that, I would have continued the sibling-leaf pattern.

## Implemented
- `tests/test_debate_commands.py` (commit c993edf): removed `del sys.modules` glob in 3 test files (test_debate_posture_floor, test_debate_pure, test_debate_utils). MISSED test_debate_commands.py:22-23 — caught later by /challenge.
- `scripts/debate_explore.py` + `scripts/debate.py` (commit 6bbde96): split 6/N. L39 lesson added.
- `tasks/debate-common-{proposal,findings,judgment,challenge,plan,qa}.md` (commits 74843c9, 0467c78): full pipeline artifacts.
- `scripts/debate_common.py` (commit e2dd116): 126-line module with 4 helpers + 2 constants. debate.py: 4090 → 3991 lines.
- 4 sibling modules updated to dual-import (lazy `import debate` + lazy `import debate_common`).
- 2 test files updated: 8 monkeypatch sites + 24 direct call sites retargeted to `debate_common`. test_debate_commands.py:22-23 glob deleted.
- `.env` restored at framework root (copied from `~/buildos/products/debates/.env`).
- `tasks/decisions.md`: D25 added.

## NOT Finished
- **Cost tracking migration (F4)**: `_session_costs`, `_session_costs_lock`, `_estimate_cost`, `_track_cost`, `get_session_costs`, `_cost_delta_since`, `_track_tool_loop_cost`, cost rate tables — all still in debate.py. Atomic migration in their own commit. Will touch 4 sibling modules + test_debate_pure.py + test_debate_utils.py.
- **Other helper migrations** (incremental, separate commits): prompt loader + prompt constants; `_load_config`; `_log_debate_event`; frontmatter helpers (`_build_frontmatter`, `_redact_author`); `_apply_posture_floor`, `_shuffle_challenger_sections`.
- **Remaining 6 cmd_* extractions** (cmd_pressure_test 262L, cmd_review 275L, cmd_challenge 265L, cmd_refine 385L, cmd_premortem ?L, cmd_judge 515L) — each becomes ~20-min mechanical move once `_common` carries the full helper set.
- **Lessons triage**: at 30/30 cap. Should triage soon (archive resolved/promoted, or add /healthcheck cycle).
- **Audit findings open** (unchanged from prior sessions): F6 (hook latency telemetry, ~30 min), F7 (external BuildOS user, strategic), F8 (contract tests, opportunistic).

## Next Session Should
1. Read `tasks/debate-common-plan.md` "Out of scope (followup commits)" section. Pick cost tracking atomic migration as the next single-purpose commit.
2. Before starting: `grep -rn 'debate\._estimate_cost\|debate\._track_cost\|debate\.get_session_costs\|debate\._cost_delta_since\|debate\._track_tool_loop_cost' scripts/ tests/` to enumerate exact call sites that need updating.
3. Per F4: move all 7 cost symbols + 1 dict + 1 lock + cost rate tables in ONE commit. Verify zero `debate.X` references for these symbols afterward.
4. Update `_call_litellm` (still in debate.py) to call `debate_common._track_cost`.

## Key Files Changed
- `scripts/debate_common.py` (new)
- `scripts/debate.py` (4090→3991)
- `scripts/debate_explore.py` (new earlier this session, then dual-import update)
- `scripts/debate_check_models.py`, `debate_compare.py`, `debate_verdict.py` (dual-import update)
- `tests/test_debate_commands.py`, `tests/test_debate_fallback.py`, `tests/test_debate_posture_floor.py`, `tests/test_debate_pure.py`, `tests/test_debate_utils.py`
- `tasks/lessons.md` (+L39)
- `tasks/decisions.md` (+D25)
- `tasks/debate-common-*.md` (6 artifacts)

## Doc Hygiene Warnings
- ⚠ Lessons at 30/30 (hard cap). L39 was added today; queue is full. Should triage (archive resolved/promoted) before adding more.
- BuildOS sync: clean (0 changed, 0 new).
