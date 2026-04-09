---
topic: debate-py-bandaid-cleanup
review_tier: cross-model
status: passed
git_head: pending
producer: claude-opus-4-6
created_at: 2026-04-09T17:55:00-0700
scope: scripts/debate.py, tests/test_tool_loop_config.py, tests/test_debate_smoke.py, config/debate-models.json
findings_count: 0
spec_compliance: true
rounds: 2
---
# /review — debate-py-bandaid-cleanup

Cross-model review of the debate.py band-aid cleanup commit, run via `scripts/debate.py challenge` with three independent reviewer lenses (architect/security/pm) on Opus 4.6, GPT 5.4, and Gemini 3.1 Pro.

## Final Status: PASSED (after one revision cycle)

| Lens         | Round 1 Material | Round 1 Advisory | Round 2 Material | Round 2 Advisory |
|--------------|------------------|------------------|------------------|------------------|
| PM           | 2 (1 false pos)  | 4                | 0                | 0                |
| Security     | 1 (false pos)    | 3                | 0                | 0                |
| Architecture | 1                | 3                | 0                | 2                |

Spec compliance: yes (`tasks/debate-py-bandaid-cleanup-plan.md`, `tasks/debate-py-bandaid-cleanup-challenge.md`)

## Round 1 — Initial Review

Artifacts: `tasks/debate-py-bandaid-cleanup-review-debate.md`

### Material findings (real)

**M1 [Architecture / SPEC VIOLATION] — `_challenger_temperature` defined but never called.**
All 3 reviewers independently flagged this. The cleanup added a `_challenger_temperature(model)` helper to encapsulate per-model challenger temperatures, but neither `cmd_challenge` nor `cmd_review_panel` actually called it. Result: all challenger paths fell back to `_call_litellm`'s judge-mode default (0.7), and Gemini-as-challenger silently regressed from its Fix 4 value of 1.0. The infrastructure was built but not wired.

**Resolution applied in round 2:**
- Wired `challenger_temp = _challenger_temperature(model)` into `cmd_challenge` (both tool path passing to `llm_tool_loop` and non-tool path passing to `_call_litellm`).
- Same wiring in `cmd_review_panel` (multi-persona panel reviews are also challenger-mode).
- Discovered during the fix that `LLM_CALL_DEFAULTS["challenger_temperature_default"]` was set to 0.7, which would have regressed Claude/GPT challenger temperatures from their pre-cleanup value of 0.0 (`llm_client._default_temperature_for_model`). Corrected to 0.0 with documentation linking the dict to `llm_client.py`'s per-model defaults.
- Added `temperature` to `TOOL_LOOP_GUARDED_KWARGS` in the linter so this class of regression is now structurally enforced (Gemini's advisory C from round 1).

### Material findings (false positives)

**M2 [Security] — `AssertionError` typo claim.**
Opus claimed `tests/test_tool_loop_config.py:182` had a misspelled `AssertionError`. Verified: `AssertionError` is the correct Python builtin spelling. Opus's response said "but wait, let me verify..." mid-thought and reached an incorrect conclusion. This was a hallucination, not a real bug. The round-2 review re-confirmed the file is correct.

### Advisory findings (round 1)

- **[Architecture, Opus]** `LLM_CALL_DEFAULTS` defined after first use. Python late-binds module-level names so it's runtime-safe, but readability hazard. **Decision: defer.** Logged as a possible follow-up; not blocking.
- **[Architecture, Opus]** `_consolidate_challenges` reads config redundantly when `model is None`. **Decision: defer.** Minor inefficiency, not worth caller-side complexity for a one-call function.
- **[Security, Opus]** `RuntimeError` in `LLM_SAFE_EXCEPTIONS` is broad and could swallow non-LLM bugs. **Decision: keep.** Inherited from prior code, not a regression. The 2 documented best-effort sites are the only places that catch broadly anyway, and they have traceback logging.
- **[PM/Test, GPT]** Test coverage doesn't assert behavioral properties (compare_default selection, traceback logging, challenger temperature routing). **Decision: keep current scope.** Smoke tests + AST linter cover the structural changes; behavioral assertions would require running real LLM calls. Out of scope.
- **[Security, GPT]** Broad catches will swallow programmer errors. **Decision: documented and accepted.** Best-effort enrichment paths must never crash the pipeline; traceback logging keeps them debuggable.
- **[Architecture, GPT]** `_consolidate_challenges` adds hidden config I/O. Same as Opus's advisory above. **Decision: defer.**
- **[Architecture, Gemini]** Linter doesn't guard `temperature` in `llm_tool_loop` calls. **FIXED IN ROUND 2** — added `temperature` to `TOOL_LOOP_GUARDED_KWARGS` and updated self-test fixture to 4 violations.

## Round 2 — Verification Review

Artifacts: `tasks/debate-py-bandaid-cleanup-review-debate-v2.md`

All 3 reviewers verified the M1 fix actually landed. Each cited specific line numbers:
- **Opus:** "cmd_challenge tool path: temperature=challenger_temp at line ~878 ✅. Non-tool path: temperature=challenger_temp at line ~898 ✅. cmd_review_panel: same pattern verified at lines ~2212 and ~2232 ✅."
- **GPT:** Verified at scripts/debate.py:872-883, 897-899, 2206-2217, 2231-2233. `_challenger_temperature(model)` at scripts/debate.py:659-668. LLM_CALL_DEFAULTS values at 1459-1467.
- **Gemini:** "FIXED. Same pattern successfully applied here. challenger_temp correctly controls the temperature for both paths." Verdict: ACCEPT.

### New material findings (round 2)

**None.** All three reviewers explicitly said no new MATERIAL issues were introduced.

### Advisory findings (round 2)

- **[Architecture, GPT]** `tests/test_debate_smoke.py` is not discovered by the repo's `check_test_coverage` tool, so the new smoke coverage may only run when invoked manually. **Decision: accepted as-is.** The test runs via `python3.11 tests/test_debate_smoke.py` per the verification_commands in the plan. If the project wants automated pytest discovery, that's a separate refactor. Logging as a possible follow-up.
- **[Architecture, GPT]** Per-model challenger temperatures are duplicated between `LLM_CALL_DEFAULTS["challenger_temperature_per_model"]` in `debate.py` and `_default_temperature_for_model` in `llm_client.py`. **Decision: accepted with documentation.** The two helpers represent conceptually different things — `llm_client`'s helper is "default for any unspecified call", `debate.py`'s helper is "challenger-mode override". They happen to have the same values today but could diverge. The drift hazard is documented in the `LLM_CALL_DEFAULTS` comment block at debate.py:1431-1450 with explicit instructions to keep the two aligned if values change.
- **[Architecture, Gemini]** Linter test fixtures are coupled to the scanner's AST logic. **Decision: accepted as scope-appropriate.** "Perfectly acceptable for the scope of this fix" per Gemini.

## Spec compliance check

Cross-referencing against `tasks/debate-py-bandaid-cleanup-plan.md`:

| Plan item | Implementation status |
|-----------|-----------------------|
| B' — `LLM_SAFE_EXCEPTIONS` constant + replace 8 inline tuples | ✅ Done. All 8 sites converted; linter scanner enforces. |
| B' — Keep broad `except Exception` at 2 best-effort sites with traceback | ✅ Done. Both sites documented, `traceback.print_exc` added. |
| A' — `LLM_CALL_DEFAULTS` dict + `_call_litellm` reads from it | ✅ Done. |
| A' — `_consolidate_challenges` routes through `_call_litellm` | ✅ Done. Signature now takes `litellm_url, api_key`. |
| A' — Per-role temperatures with documented intent | ✅ Done. Judge=0.7, challenger Claude/GPT=0.0, Gemini=1.0. |
| A' — `_challenger_temperature` helper actually used | ✅ Done in round 2 (was the round-1 MATERIAL finding). |
| C' — Fix `judge_default` dead-code path | ✅ Done. Argparse default → None, config resolves. |
| C' — `compare` config key + dead-code fix | ✅ Done. New `compare_default` config key. |
| C' — `_consolidate_challenges` model from config | ✅ Done. |
| C' — `author_models` inline comment | ✅ Done. |
| E' — Linter extends to `llm_call(` and exception tuples | ✅ Done. Self-test fixtures included. |
| E' — Linter guards `temperature` in tool-loop calls | ✅ Done in round 2 (Gemini's round-1 advisory). |
| G' — Smoke tests in `tests/test_debate_smoke.py` | ✅ Done. 6 tests, all green. |
| Out: Item D (startup config validation) | ✅ Correctly omitted. |
| Out: `author_models` config-ification | ✅ Correctly deferred. |

100% spec compliance.

## Verification evidence

```
$ python3.11 tests/test_tool_loop_config.py
OK: debate.py clean — no inline literals at LLM call sites and no banned exception tuples
    Scanners: tool-loop kwargs, llm_call/_call_litellm kwargs, exception tuples

$ python3.11 tests/test_debate_smoke.py
PASS: test_constants_exist
PASS: test_load_config_includes_compare_default
PASS: test_top_level_help_works
PASS: test_subcommand_help_works
PASS: test_judge_default_is_none_not_hardcoded
PASS: test_compare_default_is_none_not_hardcoded
All 6 smoke tests passed.

$ python3.11 scripts/debate.py check-models
Config version: 2026-04-09
Configured models: claude-opus-4-6, gemini-3.1-pro, gpt-5.4
Available in LiteLLM: claude-haiku-4-5-20251001, claude-opus-4-6, claude-sonnet-4-6, gemini-3.1-pro, gpt-5.4
```

All 8 verification commands from the plan frontmatter pass.

## Recommendation

**APPROVE for commit.** Proceed to `/ship` (or direct git commit per the project's commit doc-update rule).
