---
topic: debate-cost-tracking
qa_result: go
git_head: 12a865b
producer: claude-opus-4-7
created_at: 2026-04-16T19:55:00-0700
---
# QA — F4 Atomic Cost-Tracking Migration (commit 12a865b)

## 5-Dimension Check

- [x] **Test coverage:** Existing tests cover `_estimate_cost` (14 cases in test_debate_pure.py + 8 in test_debate_utils.py, 22 total), plus full engine coverage in test_debate_commands.py + test_debate_fallback.py. No new test file needed — this is a migration, not new behavior. The existing test call sites were updated to `debate_common._estimate_cost` and all 22 still pass. `_track_cost` and `get_session_costs` are exercised via the engine's end-to-end paths (smoke tests + integration via test_debate_commands). Adding a dedicated single-accumulator invariant test was discussed in challenge F4 (dismissed as follow-up, not blocking).
- [x] **Regression risk:** Zero function signature changes (names + params + returns + exception semantics unchanged — diff confirms the old defs and new defs are byte-for-byte identical on `def` lines). Only the module location changed. 11 internal debate.py call sites retargeted to `debate_common.X`. 4 sibling modules + 2 test files updated. Whole-repo grep (scripts/, tests/, hooks/) for `debate.X` references to migrated symbols returns 0 matches — no stale caller remains.
- [x] **Plan compliance:** surfaces_affected matches actual diff exactly (debate.py, debate_common.py, 4 siblings, 2 tests + tests/test_debate_tools.py verified per Step 5). One minor advisory: sibling lazy-import comments were tightened to remove stale "credentials" token (debate_explore, debate_compare, debate_verdict) — this is follow-through from the prior commit (e2dd116 moved credentials to debate_common but the comments weren't updated then). Inside plan scope, not scope creep.
- [x] **Negative tests:** Existing `_estimate_cost` tests already cover: empty usage dict, None usage, unknown model, zero tokens, missing usage keys, None token values, unknown model prefix. All 22 tests exercise the function in its new home (verified by 932/932 suite pass). `_track_cost` thread-safety is implicit (not explicitly unit-tested in this commit, but the lock is bytewise-copied from the original).
- [x] **Integration:** All migrated symbol call sites updated across 3 trust surfaces:
  1. Internal debate.py (11 sites — verified via `grep 'debate_common\.X' scripts/debate.py`)
  2. Sibling modules (4 files — debate_explore, debate_compare, debate_verdict, debate_outcome)
  3. Test files (2 files — test_debate_pure.py, test_debate_utils.py)
  Hooks directory is cost-symbol-free (grep returns 0). `debate_tools._check_code_presence` / `_check_function_exists` still find `_estimate_cost` in the scripts/ directory scan (verified by 10/10 passing tests in those classes). The CLI loads cleanly (`debate.py challenge --help` → exit 0).

## Tests

PASS — 932 passed in 11.70s. All 6 run_all.sh smoke tests passed. debate.py clean-scan (no inline literals at LLM call sites, no banned exception tuples) green.

## Verification Battery (from plan frontmatter)

All 7 commands return as expected:
- `bash tests/run_all.sh` → 932 passed
- `grep -n 'def _estimate_cost|...' scripts/debate.py` → 0 matches
- `grep -rn 'debate\._estimate_cost|...' scripts/ tests/` → 0 matches
- `hasattr(debate, <migrated symbol>)` → all False (negative invariant confirmed)
- `debate_common._track_cost → get_session_costs → _cost_delta_since` end-to-end smoke → OK
- `debate.py challenge --help` → exit 0
- `wc -l scripts/debate.py scripts/debate_common.py` → 3897 + 239 = 4136 (vs 3991 + 127 = 4118 pre-commit; net +18 from expanded helper docstrings + atomicity comment block)

## Advisory (non-blocking)

- **Single-accumulator regression test (challenge F4):** Dismissed by the judge as advisory/follow-up. Not added in this commit. If an F4-style test is added later, it should write via `debate_common._track_cost(model, {p:1000, c:500}, 0.05)` then assert `debate_common.get_session_costs()['total_usd'] == 0.05` AND `not hasattr(debate, '_session_costs')` (negative invariant to guard against future re-exports).
- **Sibling lazy-import comment cleanup** (3 files): Strictly beyond plan text but documents stale prior-commit state. One-line-per-file change, clerical.

## Verdict: GO

- Zero MATERIAL issues
- Plan compliance clean
- Test suite green
- All verification commands pass
- 2 challenger material findings (F1: import style, F3: reassignment concern) both resolved pre-commit via explicit plan text + pre-flight grep verification

## Next

- `/ship` is technically ready (tier 1.5 + go verdict + clean tests)
- Or: move to the next incremental commit (prompt loader migration, then `_load_config`, then `_log_debate_event`, then the 6 remaining cmd_* extractions)
