# Test Visibility Investigation — Evidence

## Claim (L18)
"Standalone test scripts invisible to pytest = invisible to pre-commit = linter violations ship uncaught. run_all.sh now runs both pytest AND standalone scripts."

## Evidence Collected

### E1: run_all.sh structure
- Line 10: runs `pytest tests/ -q`
- Line 17: hardcoded standalone loop: `tests/test_tool_loop_config.py` and `tests/test_debate_smoke.py`
- Both pytest failures and standalone failures set FAILED=1; script exits non-zero on any failure.

### E2: Test file inventory (9 files)
| File | pytest discovers? | In run_all.sh standalone? | Has `__main__`? |
|------|-------------------|---------------------------|-----------------|
| test_artifact_check.py | Yes (19 tests) | No | No |
| test_conviction_gate.py | Yes (7 tests via unittest.TestCase) | No | Yes |
| test_debate_smoke.py | Yes (6 tests) | Yes | Yes |
| test_enrich_context.py | Yes | No | No |
| test_finding_tracker.py | Yes | No | No |
| test_llm_client.py | Yes (11 tests) | No | Yes |
| test_managed_agent.py | Yes (29 tests) | No | No |
| test_tier_classify.py | Yes | No | No |
| test_tool_loop_config.py | **NO** (0 test_ functions) | Yes | Yes |

### E3: Pytest collection output
`pytest tests/ --collect-only` collects 96 tests across 8 modules. `test_tool_loop_config.py` is the ONLY file not discovered — it has no `def test_*` functions, only `main()`, `find_violations()`, and private helpers.

### E4: run_all.sh execution output
```
96 passed in 3.23s
OK: debate.py clean — no inline literals at LLM call sites and no banned exception tuples
    Scanners: tool-loop kwargs, llm_call/_call_litellm kwargs, exception tuples
PASS: test_constants_exist
PASS: test_load_config_includes_compare_default
PASS: test_top_level_help_works
PASS: test_subcommand_help_works
PASS: test_judge_default_is_none_not_hardcoded
PASS: test_compare_default_is_none_not_hardcoded
All 6 smoke tests passed.
```
All tests pass. Both pytest and standalone phases execute.

### E5: Hook wiring
- `hook-pre-commit-tests.sh` fires on every `git commit*` Bash command (PreToolUse matcher on Bash)
- It runs `bash tests/run_all.sh` and exits 2 (BLOCK) on failure
- This is a hard block — commits cannot proceed if any test fails

### E6: Temperature violations (the original symptom)
- `grep -rn temperature .claude/skills/explore/ .claude/skills/pressure-test/` returns NO matches
- All temperature references in `scripts/debate.py` now go through `LLM_CALL_DEFAULTS` dict or `_challenger_temperature()` helper
- `test_tool_loop_config.py` structurally enforces this via AST scanning — would catch any regression

### E7: Ruff hook
- `hook-ruff-check.sh` runs PostToolUse on Write|Edit — advisory only (always exits 0)
- No commit-time ruff enforcement — ruff runs per-file-edit, not at commit gate
- The ruff hook is non-blocking; actual linting enforcement relies on the AST scanner in test_tool_loop_config.py

### E8: Structural fragility — hardcoded standalone list
- `run_all.sh` line 17 is a hardcoded list: `for script in tests/test_tool_loop_config.py tests/test_debate_smoke.py`
- Adding a new pytest-invisible test file requires manually editing this list
- No dynamic discovery of standalone scripts
- `test_debate_smoke.py` is listed in BOTH pytest discovery and standalone — redundant but harmless

---

## Hypotheses

### A) Fix is complete — run_all.sh discovers all standalone tests
Evidence FOR: test_tool_loop_config.py (the only pytest-invisible file) is in the standalone list. run_all.sh runs successfully. The pre-commit hook calls run_all.sh and blocks on failure.

Evidence AGAINST: The standalone list is hardcoded. test_debate_smoke.py runs twice (redundant). No mechanism to detect a future pytest-invisible file that's missing from the list.

### B) Fix is partial — some standalone tests still not discovered
Evidence FOR: The only file invisible to pytest (test_tool_loop_config.py) IS in run_all.sh. All other __main__ files (test_conviction_gate.py, test_debate_smoke.py, test_llm_client.py) are also discovered by pytest.

Evidence AGAINST: All 9 test files are covered by at least one execution path.

### C) Fix is structural but fragile — the hook wiring means untested code can still ship in the future
Evidence FOR: The hardcoded standalone list in run_all.sh means a new standalone-only test file added without updating run_all.sh would be invisible. There is no dynamic discovery mechanism. L18 lesson says "verify bash tests/run_all.sh discovers it" but this is advisory text, not enforced.

Evidence AGAINST: The current state has no gaps. The pattern of pytest-invisible tests is rare (only 1 of 9 files). The L18 lesson documents the check procedure.
