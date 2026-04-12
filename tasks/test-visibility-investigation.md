# Investigation: Test Visibility (L18 Claim Verification)

**Mode:** CLAIM
**Claim:** "Standalone test scripts invisible to pytest = invisible to pre-commit = linter violations ship uncaught. run_all.sh now runs both pytest AND standalone scripts."
**Date:** 2026-04-11
**Status:** CONFIRMED with structural fragility

---

## Summary

The L18 fix is **operationally complete for the current codebase** but **structurally fragile for future additions**. All 9 test files are executed by at least one path. The pre-commit hook hard-blocks on failure. The original symptom (inline temperature violations shipping uncaught) is resolved. However, the standalone test list in `run_all.sh` is hardcoded, meaning a future pytest-invisible test file added without updating the list would be silently invisible.

## Evidence Summary

| Evidence | Finding |
|----------|---------|
| `run_all.sh` structure | Runs pytest (96 tests across 8 modules) + 2 hardcoded standalone scripts |
| Test file inventory | 9 files total. Only `test_tool_loop_config.py` is pytest-invisible (no `test_*` functions) |
| `run_all.sh` execution | All tests pass. Both phases execute correctly. |
| Pre-commit hook | `hook-pre-commit-tests.sh` calls `run_all.sh`; exits 2 (BLOCK) on failure |
| Temperature violations | Zero inline temperature literals remain. All go through `LLM_CALL_DEFAULTS` or `_challenger_temperature()` |
| Ruff hook | Advisory only (non-blocking). Structural enforcement is via the AST scanner in `test_tool_loop_config.py` |
| Standalone list | Hardcoded on line 17: `test_tool_loop_config.py` and `test_debate_smoke.py` |

## Hypothesis Verdicts

| Hypothesis | Verdict | Panel Consensus |
|------------|---------|----------------|
| A) Fix is complete | LIKELY for current state | 3/3 agree it works today; 2/3 say "complete" overstates it |
| B) Fix is partial (current gaps) | UNSUPPORTED | 3/3 unanimous — no current test file is uncovered |
| C) Fix is fragile (future risk) | CONFIRMED | 3/3 unanimous at 5/5 confidence |

## Cross-Model Panel Results

Three models reviewed (claude-opus-4-6, gemini-3.1-pro, gpt-5.4). All three:
- Rated Hypothesis C at 5/5 confidence
- Identified E8 (hardcoded standalone list) as the key structural gap
- Suggested the same remediation: a meta-test that verifies every `tests/test_*.py` is either pytest-collected or in the standalone list
- Noted `test_debate_smoke.py` runs twice (pytest + standalone) — harmless but indicates manual curation

## Root Cause Chain

1. `test_tool_loop_config.py` uses a custom `main()` runner with no `def test_*` functions -> pytest cannot discover it
2. `run_all.sh` originally only ran `pytest tests/` -> standalone scripts never executed at commit time
3. `hook-pre-commit-tests.sh` calls `run_all.sh` -> the hook was only as good as the runner
4. Result: 3 inline temperature violations shipped in explore/pressure-test skills because the AST linter never ran

## Fix Status

- **Original symptom resolved:** Temperature violations fixed, AST scanner enforces via `LLM_CALL_DEFAULTS`
- **run_all.sh updated:** Now runs both pytest and standalone scripts
- **Pre-commit hook intact:** Hard-blocks commits on any test failure

## Structural Fragility (Actionable)

The standalone list in `run_all.sh` line 17 is hardcoded:
```bash
for script in tests/test_tool_loop_config.py tests/test_debate_smoke.py; do
```

**Risk:** A new test file with only a `main()` runner and no `def test_*` functions would be invisible to both pytest and `run_all.sh` unless someone manually edits the list. The L18 lesson documents the procedure ("verify `bash tests/run_all.sh` discovers it") but this is advisory text, not enforcement.

**Recommended fix:** Add a meta-test (either in `run_all.sh` or as a pytest test) that compares the set of `tests/test_*.py` files against the union of pytest-collected modules and the standalone list. Fail if any file is uncovered.

---

*Investigation conducted 2026-04-11. Panel: claude-opus-4-6, gemini-3.1-pro, gpt-5.4.*
