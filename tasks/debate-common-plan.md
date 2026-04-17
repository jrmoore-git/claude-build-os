---
scope: "Extract credential + LLM dispatch helpers from debate.py into scripts/debate_common.py per challenge fixes F1-F5. Simplest version (per proposal); cost tracking and other helper groups deferred."
surfaces_affected: "scripts/debate_common.py, scripts/debate.py, scripts/debate_check_models.py, scripts/debate_outcome.py, scripts/debate_stats.py, scripts/debate_compare.py, scripts/debate_verdict.py, scripts/debate_explore.py, tests/test_debate_commands.py, tests/test_debate_fallback.py, tests/test_debate_tools.py, tests/test_debate_smoke.py"
verification_commands: "bash tests/run_all.sh && grep -rn 'del sys\\.modules' tests/ && grep -n 'debate\\._load_credentials\\|debate\\._load_dotenv\\|debate\\._call_litellm\\|debate\\._call_with_model_fallback\\|debate\\._get_fallback_model\\|debate\\._is_timeout_error\\|debate\\._challenger_temperature' scripts/"
rollback: "git revert <sha> — all changes are within scripts/ and tests/, no infra/data state changes"
review_tier: "Tier 2"
verification_evidence: "PENDING"
challenge_artifact: "tasks/debate-common-challenge.md"
challenge_recommendation: "PROCEED-WITH-FIXES"
---
# Plan: Extract debate_common.py (simplest version)

Implements the **simplest version** from `tasks/debate-common-proposal.md` with all 5 fixes from `tasks/debate-common-challenge.md`:

- F1: file is `debate_common.py` (not `_common.py`)
- F2: Step 0 audits/removes `del sys.modules` glob in test_debate_commands.py + cargo-cult patterns elsewhere
- F3: import style is `import debate_common; debate_common.foo()` everywhere (no `from debate_common import …`)
- F4: cost tracking is OUT OF SCOPE for this commit (deferred — atomic migration in its own commit)
- F5: debate.py uses `debate_common.foo()` at call sites (no `from debate_common import` re-exports)

## What moves to debate_common.py (this commit only)

Credentials + LLM dispatch core (per the proposal's "simplest version"):

- `_load_credentials`
- `_load_dotenv` (called only from `main()` per advisory A1)
- `_call_litellm`
- `_call_with_model_fallback`
- `_get_fallback_model`
- `_get_model_family`
- `_challenger_temperature`
- `_is_timeout_error`
- `LLM_SAFE_EXCEPTIONS` (constant)
- `LLM_CALL_DEFAULTS` (constant — referenced by extracted siblings via `debate.LLM_CALL_DEFAULTS["explore_temperature"]` in current code)
- `LLMError` is re-exported from `llm_client.py` per advisory A2 (not duplicated)

**Out of scope (deferred to followup commits):** prompt loader, prompt constants, config loader, cost tracking, logging helpers, frontmatter helpers, redaction, posture floor.

## Build Order

| # | Step | Files | Verification |
|---|---|---|---|
| 0 | Audit + remove `del sys.modules` patterns in tests | `tests/test_debate_commands.py:22-23`, `tests/test_debate_tools.py:18-19`, `tests/test_debate_smoke.py:35,77` | `grep -rn 'del sys\.modules' tests/` returns 0; `bash tests/run_all.sh` passes (932/932) |
| 1 | Create `scripts/debate_common.py` with the 8 helpers + 2 constants. Lazy-load `LLMError` from llm_client. | `scripts/debate_common.py` (new) | File exists; `python3.11 -c "import sys; sys.path.insert(0,'scripts'); import debate_common; print(debate_common._load_credentials)"` returns a callable |
| 2 | In `debate.py`: add `import debate_common`. Delete the 8 helper definitions + 2 constants from debate.py. Replace internal call sites (debate.py's own usage in `cmd_*`) with `debate_common.foo()`. | `scripts/debate.py` | Suite passes (932/932); `grep -n 'def _load_credentials\|def _call_litellm\|def _call_with_model_fallback\|def _get_fallback_model\|def _get_model_family\|def _challenger_temperature\|def _is_timeout_error\|def _load_dotenv' scripts/debate.py` returns 0 |
| 3 | In each of 6 sibling modules: remove lazy `import debate`. Add `import debate_common`. Replace `debate.foo()` with `debate_common.foo()` for the 8 migrated symbols. Keep `debate.X` for symbols still in debate.py (config, prompts, cost, logging). | `scripts/debate_check_models.py`, `scripts/debate_outcome.py`, `scripts/debate_stats.py`, `scripts/debate_compare.py`, `scripts/debate_verdict.py`, `scripts/debate_explore.py` | Suite passes (932/932); `grep -n 'debate\._load_credentials\|debate\._load_dotenv\|debate\._call_litellm\|debate\._call_with_model_fallback\|debate\._get_fallback_model\|debate\._is_timeout_error\|debate\._challenger_temperature\|debate\._get_model_family' scripts/` returns 0 |
| 4 | Update test fixtures + scattered `setattr` to patch `debate_common.X` instead of `debate.X` for the 8 migrated symbols. Affected fixtures: `fake_credentials`, `fake_credentials_fallback`, `fake_llm`, `fake_llm_with_sections` in test_debate_commands.py. Affected scattered setattr: 13 in test_debate_fallback.py + test_debate_commands.py for `_call_litellm`, 5 in test_debate_commands.py for `_load_credentials`. | `tests/test_debate_commands.py`, `tests/test_debate_fallback.py` | Suite passes (932/932) |
| 5 | Final verification: full suite + greps for any leftover `debate.X` references to migrated symbols + verify no `del sys.modules` globs remain | (all above) | All `verification_commands` from frontmatter return clean |
| 6 | Commit | (above + `tasks/debate-common-*.md` artifacts) | `git status --short` clean except `stores/debate-log.jsonl` (audit log appends from this session) |

## Files

| File | Op | Scope |
|---|---|---|
| `scripts/debate_common.py` | CREATE | New module: 8 helpers + 2 constants + LLMError re-export. ~250 lines |
| `scripts/debate.py` | MODIFY | Delete 8 helpers + 2 constants. Add `import debate_common`. Replace internal call sites with `debate_common.X`. Net: ~-250 lines + a few prefix updates |
| `scripts/debate_check_models.py` | MODIFY | Remove lazy `import debate`; add `import debate_common`; rename `debate.X` → `debate_common.X` for migrated symbols only |
| `scripts/debate_outcome.py` | MODIFY | (same as above) |
| `scripts/debate_stats.py` | MODIFY | (same) |
| `scripts/debate_compare.py` | MODIFY | (same) |
| `scripts/debate_verdict.py` | MODIFY | (same) |
| `scripts/debate_explore.py` | MODIFY | (same) |
| `tests/test_debate_commands.py` | MODIFY | (a) remove `del sys.modules` glob lines 22-23; (b) update fixtures to patch `debate_common.X`; (c) update scattered `setattr` for migrated symbols |
| `tests/test_debate_fallback.py` | MODIFY | Update 9-10 `setattr(debate, "_call_litellm", …)` → `setattr(debate_common, "_call_litellm", …)` |
| `tests/test_debate_tools.py` | MODIFY | Remove `del sys.modules` block (lines 18-19) — narrower glob but same cargo-cult |
| `tests/test_debate_smoke.py` | MODIFY | Remove `del sys.modules["debate"]` (lines 35, 77) — exact match but cargo-cult |

## Execution Strategy

**Decision:** sequential
**Pattern:** pipeline
**Reason:** Each step depends on the previous: cannot move helpers (Step 1-2) before tests are sys.modules-clean (Step 0); cannot update siblings (Step 3) before debate_common exists (Step 1); cannot update tests (Step 4) before debate.py/siblings reference debate_common (Step 2-3). The full-suite checkpoint between each step is the only safe rhythm.

Single agent (this session). No worktree fan-out — files share too much state for parallel agents to be net-positive.

## Verification

```bash
# 1. Full test suite
bash tests/run_all.sh
# expect: 932 passed

# 2. No del sys.modules patterns left in tests
grep -rn 'del sys\.modules\|sys\.modules\[' tests/
# expect: only test_managed_agent.py:24,28 (unrelated, mocks anthropic SDK)

# 3. Migrated symbols not referenced via debate.X anywhere in scripts/
grep -n 'debate\._load_credentials\|debate\._load_dotenv\|debate\._call_litellm\|debate\._call_with_model_fallback\|debate\._get_fallback_model\|debate\._is_timeout_error\|debate\._challenger_temperature\|debate\._get_model_family' scripts/
# expect: 0 matches

# 4. debate_common.py loads cleanly
python3.11 -c "import sys; sys.path.insert(0, 'scripts'); import debate_common; assert callable(debate_common._load_credentials); assert callable(debate_common._call_litellm); print('OK')"

# 5. End-to-end smoke: dry-run a debate command (no LLM call needed for help)
python3.11 scripts/debate.py challenge --help > /dev/null && echo "CLI loads"
```

## Rollback

```bash
git revert HEAD  # this commit
# All changes are file content; no schema, no infra, no data state.
```

## Out of Scope (followup commits, separate plans)

- F4 atomic cost-tracking migration (`_session_costs`, lock, `_track_cost`, `_cost_delta_since`, `get_session_costs`)
- Prompt constants + `_load_prompt` migration
- `_load_config` migration
- `_log_debate_event` migration
- `_build_frontmatter`, `_redact_author`, `_apply_posture_floor`, `_shuffle_challenger_sections` migration
- Remaining 6 cmd_* extractions (cmd_pressure_test, cmd_review, cmd_challenge, cmd_refine, cmd_premortem, cmd_judge)
- Renaming `from X import foo` to module-reference style in any test or production code that already uses the captured-binding pattern beyond the 8 migrated symbols
