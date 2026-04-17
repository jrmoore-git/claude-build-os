---
scope: "F4 from debate-common-challenge.md: atomic migration of cost-tracking subsystem (7 functions + dict + lock + pricing table) from debate.py to debate_common.py in ONE commit. Update _call_litellm and 11 internal call sites. Update 4 sibling modules + 2 heavy test files. Verify zero debate.X references remain for migrated symbols."
surfaces_affected: "scripts/debate.py, scripts/debate_common.py, scripts/debate_explore.py, scripts/debate_compare.py, scripts/debate_verdict.py, scripts/debate_outcome.py, tests/test_debate_pure.py, tests/test_debate_utils.py, tests/test_debate_tools.py"
verification_commands: "bash tests/run_all.sh && grep -n 'debate\\._estimate_cost\\|debate\\._track_cost\\|debate\\.get_session_costs\\|debate\\._cost_delta_since\\|debate\\._track_tool_loop_cost\\|debate\\._session_costs' scripts/ tests/ && grep -n 'def _estimate_cost\\|def _track_cost\\|def get_session_costs\\|def _cost_delta_since\\|def _track_tool_loop_cost\\|^_session_costs\\|^_TOKEN_PRICING' scripts/debate.py"
rollback: "git revert <sha> — single atomic commit, no schema/infra/data changes"
review_tier: "Tier 1.5"
verification_evidence: "932/932 tests pass; 0 defs left in debate.py; 0 debate.X refs to migrated symbols in scripts/ or tests/; debate module has no shadow cost symbols (hasattr check); debate_common end-to-end smoke (track→get→delta) passes; CLI help loads; debate.py 3991→3897 (−94 LOC), debate_common.py 127→239 (+112 LOC); test_debate_tools substring/identifier tests still find _estimate_cost in new location"
challenge_artifact: "tasks/debate-cost-tracking-challenge.md"
challenge_recommendation: "PROCEED-WITH-FIXES"
---
# Plan: F4 Atomic Cost-Tracking Migration

Implements F4 from `tasks/debate-common-challenge.md` (Plan recommendation: PROCEED-WITH-FIXES). Cost tracking was deferred from the simplest-version commit (e2dd116) because it requires atomic migration to avoid double-counting between two `_session_costs` accumulators.

## What moves to debate_common.py (this commit only)

Cost-tracking subsystem (lines 780-911 in debate.py):

| Symbol | Type | Lines | Notes |
|---|---|---|---|
| `_TOKEN_PRICING` | constant dict | 782-791 | Per-model USD/1M token rates |
| `_estimate_cost(model, usage)` | function | 794-811 | Pure: returns float |
| `_session_costs` | mutable dict | 817 | Module-level accumulator (THE atomicity reason) |
| `_session_costs_lock` | threading.Lock | 818 | Protects accumulator |
| `_track_cost(model, usage, cost_usd)` | function | 821-832 | Locked write |
| `get_session_costs()` | function | 835-845 | Locked read; public API |
| `_cost_delta_since(snapshot)` | function | 848-874 | Compute event delta |
| `_track_tool_loop_cost(model, tool_result)` | function | 905-910 | Convenience wrapper |

**Atomicity rationale:** `_session_costs` is module-level state. If only some functions move, the dict gets duplicated (one in `debate`, one in `debate_common`) and writes from `_track_cost` and reads from `get_session_costs` could land in different copies → silent cost loss. All 7 symbols + 1 dict + 1 lock + 1 table must move together in one commit.

**Import style commitment (per challenge F1, accepted):** `debate.py` already uses `import debate_common` (line 68, from e2dd116). All 11 migrated call sites in debate.py WILL use `debate_common.X` qualified references — NOT `from debate_common import _track_cost, ...`. This preserves the ownership-clarity benefit and matches F3 from the parent `debate-common-challenge.md`.

**Re-export prohibition (per challenge F3, accepted):** `debate.py` will NOT re-export `_session_costs`, `_session_costs_lock`, `_TOKEN_PRICING`, or any of the 7 migrated functions via `from debate_common import …`. All access goes through `debate_common.X` qualified references. Pre-flight verification already confirmed: `grep -rn '_session_costs\s*=' scripts/ tests/` returns only the definition at `debate.py:817` (no reassignment sites in the codebase); `grep -rn 'debate\._session_costs' scripts/ tests/` returns zero external references. No backward-compat re-export needed.

## Build Order

| # | Step | Files | Verification |
|---|---|---|---|
| 0 | Pre-flight: verify clean tree, baseline test suite | — | `git status --short` clean; `bash tests/run_all.sh` → 932 passed |
| 1 | Add the 8 symbols + table to `debate_common.py`. Order: `_TOKEN_PRICING` → `_estimate_cost` → `_session_costs` + lock → `_track_cost` → `get_session_costs` → `_cost_delta_since` → `_track_tool_loop_cost`. Add `import threading` if not present. | `scripts/debate_common.py` | File contains all 8 symbols; `python3.11 -c "import sys; sys.path.insert(0,'scripts'); import debate_common; assert callable(debate_common._estimate_cost); assert callable(debate_common.get_session_costs); print('OK')"` |
| 2 | In `debate.py`: delete the 7 function defs + `_TOKEN_PRICING` + `_session_costs` + `_session_costs_lock` (lines 780-910). Replace 11 internal call sites with `debate_common.X`: lines 900-901 (`_call_litellm`), 908-909 (`_track_tool_loop_cost`), 1095, 1097, 1107, 1268, 1532, 1636-37, 1704-05, 2728, 2910, 3170, 3332, 3463. Remove unused `threading` import only if no other code uses it (likely still needed). | `scripts/debate.py` | Suite passes; `grep -n 'def _estimate_cost\|def _track_cost\|def get_session_costs\|def _cost_delta_since\|def _track_tool_loop_cost\|^_session_costs\|^_TOKEN_PRICING' scripts/debate.py` returns 0; `grep -cE '_track_cost\|_estimate_cost\|get_session_costs\|_cost_delta_since\|_track_tool_loop_cost' scripts/debate.py` shows only `debate_common.X` qualified references |
| 3 | In each of 4 sibling modules: replace `debate.get_session_costs()` with `debate_common.get_session_costs()`. Add `import debate_common` if missing (debate_compare/verdict/outcome had `import debate` only); confirm `debate_explore.py` already has `import debate_common` (it does after the prior commit). Update lazy-import comments. | `scripts/debate_explore.py`, `scripts/debate_compare.py`, `scripts/debate_verdict.py`, `scripts/debate_outcome.py` | Suite passes; `grep -n 'debate\.get_session_costs' scripts/` returns 0 |
| 4 | In `tests/test_debate_pure.py` and `tests/test_debate_utils.py`: rename `debate._estimate_cost` → `debate_common._estimate_cost` (12 + 8 sites). Add `import debate_common` (or change `from .. import debate` to include both). Verify imports at top of file. | `tests/test_debate_pure.py`, `tests/test_debate_utils.py` | Suite passes; `grep -n 'debate\._estimate_cost\|debate\._track_cost\|debate\.get_session_costs\|debate\._cost_delta_since' tests/test_debate_pure.py tests/test_debate_utils.py` returns 0 |
| 5 | Verify `tests/test_debate_tools.py:120,157` still passes — those reference `"def _estimate_cost"` and `"_estimate_cost"` as test data with `file_set: "scripts"`. Since the symbol moves WITHIN `scripts/`, the search should still find it in `debate_common.py`. If `_check_code_presence`/`_check_function_exists` scan the whole directory, no change needed. If they're hardcoded to `debate.py`, update tooling or change test inputs. | `tests/test_debate_tools.py`, possibly `scripts/debate_tools.py` | Suite passes |
| 6 | Final verification: full suite + all greps from frontmatter `verification_commands` | (all above) | All pass; `bash tests/run_all.sh` 932/932 |
| 7 | Commit | (above + this plan + challenge artifact) | `git status --short` clean except `stores/debate-log.jsonl` (audit appends) |

## Files

| File | Op | Scope |
|---|---|---|
| `scripts/debate_common.py` | MODIFY | Add 7 functions + 1 dict + 1 lock + `_TOKEN_PRICING` table. ~140 LOC added. Add `threading` import if missing. |
| `scripts/debate.py` | MODIFY | Delete 7 functions + 1 dict + 1 lock + `_TOKEN_PRICING` (lines 780-910, ~130 LOC). Update 11 internal references to `debate_common.X`. Net: −130 LOC + ~25 prefix updates. Will go from 3991 → ~3861 lines. |
| `scripts/debate_explore.py` | MODIFY | Update line 22: `debate.get_session_costs()` → `debate_common.get_session_costs()`. (`import debate_common` already exists from prior commit.) |
| `scripts/debate_compare.py` | MODIFY | Add `import debate_common`; update line 21: `debate.get_session_costs()` → `debate_common.get_session_costs()`. |
| `scripts/debate_verdict.py` | MODIFY | Add `import debate_common`; update line 20. |
| `scripts/debate_outcome.py` | MODIFY | Add `import debate_common`; update line 17 + comment line 15. |
| `tests/test_debate_pure.py` | MODIFY | Add `import debate_common`; rename 12 `debate._estimate_cost` call sites. |
| `tests/test_debate_utils.py` | MODIFY | Add `import debate_common`; rename 8 `debate._estimate_cost` call sites. |
| `tests/test_debate_tools.py` | VERIFY | If `_check_code_presence`/`_check_function_exists` scan whole `scripts/` dir, no change. Otherwise update test inputs to reference `debate_common`. |

## Execution Strategy

**Decision:** sequential
**Pattern:** pipeline
**Reason:** Atomic migration — `_session_costs` is mutable shared state. Step 1 must add full implementation to `debate_common.py` before Step 2 deletes from `debate.py` (otherwise the 11 internal call sites break). Step 3 sibling updates can only happen after Step 2 (else `debate.X` still resolves correctly and we miss the migration). Step 4 test updates likewise. Single agent, no worktree fan-out — files share too much state.

(Components field omitted: 1 logical component = atomic cost-tracking migration.)

## Verification

```bash
# 1. Full test suite
bash tests/run_all.sh
# expect: 932 passed (same baseline as e2dd116/0467c78)

# 2. No migrated symbols defined in debate.py anymore
grep -n 'def _estimate_cost\|def _track_cost\|def get_session_costs\|def _cost_delta_since\|def _track_tool_loop_cost\|^_session_costs\|^_TOKEN_PRICING' scripts/debate.py
# expect: 0 matches

# 3. No call site uses debate.X for migrated symbols (anywhere in scripts/ or tests/)
grep -rn 'debate\._estimate_cost\|debate\._track_cost\|debate\.get_session_costs\|debate\._cost_delta_since\|debate\._track_tool_loop_cost\|debate\._session_costs' scripts/ tests/
# expect: 0 matches

# 4. debate_common.py loads cleanly with all symbols
python3.11 -c "
import sys; sys.path.insert(0, 'scripts')
import debate_common
assert callable(debate_common._estimate_cost)
assert callable(debate_common._track_cost)
assert callable(debate_common.get_session_costs)
assert callable(debate_common._cost_delta_since)
assert callable(debate_common._track_tool_loop_cost)
assert isinstance(debate_common._session_costs, dict)
assert isinstance(debate_common._TOKEN_PRICING, dict)
print('OK')
"

# 5. End-to-end smoke: cost API still wires through
python3.11 -c "
import sys; sys.path.insert(0, 'scripts')
import debate_common
debate_common._track_cost('claude-opus-4-6', {'prompt_tokens': 1000, 'completion_tokens': 500}, 0.0525)
costs = debate_common.get_session_costs()
assert costs['total_usd'] == 0.0525
assert costs['calls'] == 1
print('OK')
"

# 6. Backward-compatible API check: debate.py still re-exports nothing for migrated symbols
python3.11 -c "
import sys; sys.path.insert(0, 'scripts')
import debate
assert not hasattr(debate, '_estimate_cost'), 'debate._estimate_cost still exists — incomplete migration'
assert not hasattr(debate, '_session_costs'), 'debate._session_costs still exists — incomplete migration'
print('OK')
"
```

## Rollback

```bash
git revert HEAD  # this commit
# All changes are file content; no schema, no infra, no data state.
```

## Risk Notes

- **Double-accumulation risk:** mitigated by atomicity — moving the dict requires moving the writers and readers in the same commit. Step 6 verification #6 catches any leftover `debate._session_costs` reference.
- **Test fixture monkeypatching:** Step 4 must update both the call sites AND any `setattr(debate, '_estimate_cost', …)` patterns. Pre-migration grep already shows test_debate_pure/utils have plain calls (no setattr), so no fixture rewrite expected. Will re-verify during build.
- **debate_tools.py test data:** Step 5 explicitly verifies the substring-match tests still find the symbol in its new location. Worst case requires updating 2 test input strings.
- **Lessons-at-cap:** L39 was added today. If this migration surfaces a new lesson, triage required before adding L40.
