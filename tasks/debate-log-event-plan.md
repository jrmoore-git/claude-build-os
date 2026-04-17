---
scope: "Migrate _log_debate_event + PROJECT_TZ + DEFAULT_LOG_PATH from debate.py to debate_common.py. 7 internal debate.py call sites + 5 internal PROJECT_TZ sites + 4 sibling modules + 1 test monkeypatch fixture."
surfaces_affected: "scripts/debate.py, scripts/debate_common.py, scripts/debate_explore.py, scripts/debate_compare.py, scripts/debate_verdict.py, scripts/debate_outcome.py, scripts/debate_stats.py, tests/test_debate_commands.py"
verification_commands: "bash tests/run_all.sh && grep -n 'def _log_debate_event\\|^DEFAULT_LOG_PATH\\|^PROJECT_TZ' scripts/debate.py && grep -rn 'debate\\._log_debate_event\\|debate\\.PROJECT_TZ\\|debate\\.DEFAULT_LOG_PATH' scripts/ tests/ hooks/"
rollback: "git revert <sha> — single atomic commit, no schema/infra/data changes"
review_tier: "Tier 1.5"
verification_evidence: "932/932 tests pass; 0 defs in debate.py; 0 debate.X refs to migrated symbols across scripts/+tests/+hooks/; debate has no shadow symbols (hasattr check); debate_common._log_debate_event end-to-end load OK; CLI loads; debate.py 3834→3815 (−19 LOC), debate_common.py 311→338 (+27 LOC); 1 missed reference (debate_stats.py:18 debate.DEFAULT_LOG_PATH) caught by verification grep + fixed mid-build (lesson: word-boundary anchors miss substring-prefix patterns; grep should target whole identifier)"
challenge_artifact: "tasks/debate-common-challenge.md (parent: per F-list under D25 architectural pattern)"
challenge_recommendation: "PROCEED (mechanical move per established F4/load-config pattern; no new abstractions)"
---
# Plan: `_log_debate_event` + `PROJECT_TZ` Migration

Per D25 + parent debate-common-challenge.md F-list. Same pattern as F4
(commit 12a865b) and `_load_config` (commit 50a7fbd).

## What moves

| Symbol | Type | Lines |
|---|---|---|
| `PROJECT_TZ` | `ZoneInfo("America/Los_Angeles")` | 72 |
| `DEFAULT_LOG_PATH` | str ("stores/debate-log.jsonl") | 923 |
| `_log_debate_event(event, log_path=None, cost_snapshot=None)` | function | 926-942 |

`_log_debate_event` already calls `debate_common._cost_delta_since` and
`debate_common.get_session_costs` (since F4 commit 12a865b). After this
migration those become intra-module calls within `debate_common`.

**Lessons applied (from yesterday's `_load_config` retrospective):**
- Plan-time grep covered both call form (`debate.X(`) AND monkeypatch form
  (`monkeypatch.setattr(debate, "X", ...)`). Found exactly 1 monkeypatch site:
  `test_debate_commands.py:208 monkeypatch.setattr(debate, "_log_debate_event", ...)`.
  Already in scope.

## Build Order

| # | Step | Files | Verification |
|---|---|---|---|
| 0 | Pre-flight: clean tree, baseline test pass | — | `git status --short` clean; suite 932 passed |
| 1 | Add `PROJECT_TZ` + `DEFAULT_LOG_PATH` + `_log_debate_event` to `debate_common.py`. Add imports: `from datetime import datetime`, `from zoneinfo import ZoneInfo`, `import json` (already present). Inside `_log_debate_event`, use unqualified `_cost_delta_since` and `get_session_costs` (intra-module). | `scripts/debate_common.py` | Module loads; `python3.11 -c "import sys; sys.path.insert(0,'scripts'); import debate_common; assert callable(debate_common._log_debate_event); assert debate_common.PROJECT_TZ; print('OK')"` |
| 2 | In `debate.py`: delete the 3 symbols (lines 72, 923, 926-942). Replace 7 internal `_log_debate_event(` call sites + 5 internal `PROJECT_TZ` references with `debate_common.X`. | `scripts/debate.py` | Suite passes; `grep -n 'def _log_debate_event\|^DEFAULT_LOG_PATH\|^PROJECT_TZ' scripts/debate.py` returns 0 |
| 3 | Update 4 sibling modules: rename `debate._log_debate_event` (4 sites) and `debate.PROJECT_TZ` (3 sites) → `debate_common.X`. | `scripts/debate_explore.py`, `debate_compare.py`, `debate_verdict.py`, `debate_outcome.py` | `grep -n 'debate\._log_debate_event\|debate\.PROJECT_TZ' scripts/` returns 0 |
| 4 | Update test fixture: rename `monkeypatch.setattr(debate, "_log_debate_event", ...)` → `monkeypatch.setattr(debate_common, "_log_debate_event", ...)` at `test_debate_commands.py:208`. | `tests/test_debate_commands.py` | Suite passes |
| 5 | Final verification | (all above) | All commands clean |
| 6 | Commit | (above + plan + QA artifact) | clean status |

## Files

| File | Op | Scope |
|---|---|---|
| `scripts/debate_common.py` | MODIFY | Add 3 symbols + 2 imports. ~25 LOC. |
| `scripts/debate.py` | MODIFY | Delete 3 symbols + retarget 12 internal references (7 _log_debate_event + 5 PROJECT_TZ). Net ~−15 LOC. ~3834 → ~3819. |
| `scripts/debate_explore.py` | MODIFY | Rename 1 PROJECT_TZ + 1 _log_debate_event |
| `scripts/debate_compare.py` | MODIFY | Same |
| `scripts/debate_verdict.py` | MODIFY | Rename 1 _log_debate_event (no PROJECT_TZ ref) |
| `scripts/debate_outcome.py` | MODIFY | Rename 1 PROJECT_TZ + 1 _log_debate_event |
| `tests/test_debate_commands.py` | MODIFY | Rename 1 monkeypatch.setattr target |

## Execution Strategy

Sequential pipeline — same atomicity reasoning as the prior two migrations.
Single component, no fan-out.

## Verification

```bash
bash tests/run_all.sh                                # 932 passed
grep -n 'def _log_debate_event\|^DEFAULT_LOG_PATH\|^PROJECT_TZ' scripts/debate.py    # 0
grep -rn 'debate\._log_debate_event\|debate\.PROJECT_TZ\|debate\.DEFAULT_LOG_PATH' scripts/ tests/ hooks/    # 0
python3.11 -c "
import sys; sys.path.insert(0, 'scripts')
import debate
for sym in ['_log_debate_event', 'PROJECT_TZ', 'DEFAULT_LOG_PATH']:
    assert not hasattr(debate, sym), f'FAIL: debate.{sym} exists'
print('OK')
"
python3.11 scripts/debate.py challenge --help > /dev/null && echo OK
```

## Rollback

`git revert HEAD` — file content only.
