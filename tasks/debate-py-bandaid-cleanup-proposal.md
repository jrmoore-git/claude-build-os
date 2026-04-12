---
topic: debate-py-bandaid-cleanup
created: 2026-04-09
author: anonymous
---
# debate.py Band-Aid Cleanup — Fix #2-#8 Before Phase 1b

## Problem

`scripts/debate.py` (2473 lines) has accumulated a recurring class of debt: **scattered inline literals and hardcoded values at multiple call sites, with no single source of truth**. The same pattern caused Fix 9 (CRITICAL) this session — refine was fixed in a prior session with `timeout=240, max_tokens=16384` but three other `llm_tool_loop` call sites silently stayed on `timeout=60, max_tokens=4096`, causing Opus to reliably timeout on plan challenges until we discovered it under time pressure.

`tasks/root-cause-queue.md` documents 5 entries. Entry #1 (tool-loop config) is RESOLVED. Entries #2-#5 are OPEN. An audit sweep of `debate.py` conducted on 2026-04-09 surfaced 3 additional entries (#6-#8) that were not previously logged.

All 7 remaining entries are the **same class of bug**: no shared config surface for a given concern, so each call site re-specifies its own value, and knowledge fails to propagate when one site is fixed.

**Phase 1b of the CloudZero velocity v3 rerun starts next.** It will add new `research` and `synthesize` subcommands, which introduce additional `llm_tool_loop` and `llm_call` call sites in `debate.py`. If we do not land the shared config surface + shared exception constant + model-name centralization BEFORE Phase 1b, the new code will inherit or copy-paste the same patterns — the exact failure mode that produced Fix 9.

## Proposed Approach

Land one cleanup commit before starting Phase 1b engineering. Scope: entries #2, #3, #4, #5 from the root-cause queue, plus the 3 audit findings (#6, #7, #8), plus a second audit pass for anything the first sweep missed. Rough cut:

**A. Config surface unification**
- Extend `TOOL_LOOP_DEFAULTS` → `LLM_CALL_DEFAULTS` covering both `llm_tool_loop` and `llm_call` sites, with documented rationale per key.
- Include: `timeout`, `max_tokens`, `max_turns`, `temperature` (with per-role or per-model overrides where legitimate).
- Refactor `_call_litellm` (line 632) to pull from the dict instead of inline `timeout=300, temperature=0.7`.
- Refactor `_consolidate_challenges` llm_call site (line 1111) to use `_call_litellm` or the shared config.
- Document the 300/240 timeout split: is it legitimate or cosmetic drift? Pick one, document why.

**B. Exception handling unification**
- Define `LLM_SAFE_EXCEPTIONS = (LLMError, urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError)` at module level.
- Replace all 8 inline tuple sites (861, 954, 1233, 1770, 1878, 1982, 2100, 2179) with `except LLM_SAFE_EXCEPTIONS`.
- Replace the 2 `except (LLMError, Exception)` sites (1076, 1117): if the broad catch was intentional, keep it and log the traceback; otherwise narrow to `LLM_SAFE_EXCEPTIONS`.

**C. Model name centralization**
- Audit all 15+ model name literals; route every one through `_load_config()`.
- Fix the drift bug at `debate.py:1861` — `judge_model = args.model or "gemini-3.1-pro"` contradicts `_DEFAULT_JUDGE = "gpt-5.4"` at line 431. Resolve to one default.
- Fix argparse defaults at lines 2343 (`"gpt-5.4"`) and 2414 (`"gemini-3.1-pro"`) — they bypass config entirely.
- Fix `_consolidate_challenges(model="claude-sonnet-4-6")` function-signature default.
- Fix the `author_models = {"claude-opus-4-6", "litellm/claude-opus-4-6"}` hardcoded set.

**D. Config validation (entry #5)**
- Add startup validation in `_load_config`: cross-reference `persona_model_map` values against LiteLLM available models (cached). Fail fast on typos.

**E. Linter extension**
- Extend `tests/test_tool_loop_config.py` (AST-based) to also scan:
  - `llm_call(` for inline `timeout=`, `max_tokens=`, `temperature=` literals
  - `except (` for inline `LLMError` tuple patterns
  - Model name literals outside the whitelist of declaration sites (`_DEFAULT_PERSONA_MODEL_MAP`, `MODEL_PROMPT_OVERRIDES`, `_DEFAULT_JUDGE`, `_DEFAULT_REFINE_ROTATION`)

**F. Second audit pass**
- Before committing, sweep `debate.py` again for any pattern the first audit missed (hardcoded URLs, inline prompts that should be module-level constants, retry counts, magic numbers in parsing regexes).

**Non-goals:**
- Not touching `debate_tools.py`, `llm_client.py`, or any other file outside `debate.py` unless the cleanup strictly requires it.
- Not refactoring subcommand logic, prompts, or persona configuration — only the config/exception/model-name surface.
- Not adding new features, new subcommands, or new capabilities.
- Not improving test coverage beyond extending the existing linter.
- Not changing any observable behavior of `debate.py` — this is a pure refactor. Every existing debate run should produce the same output after the cleanup.
- Not fixing #1 (already resolved).

## Simplest Version

The minimum version that still prevents the Phase 1b regression risk:
- **B + C-subset**: `LLM_SAFE_EXCEPTIONS` constant (10 sites) + fix the two `_DEFAULT_JUDGE` vs inline fallback drift bugs (lines 1861, 2343, 2414).
- Skip A, D, E, F entirely.

This is about 12 edits in one file, ~30 min of work, zero behavior change. It addresses the highest-risk items (drift bugs that would cause wrong-model calls) but leaves the config surface unification for later.

**Rationale for simplest version:** If the `/challenge` returns SIMPLIFY, this is the fallback. It still unblocks Phase 1b safely because the new subcommands will use `llm_tool_loop` (already covered by Fix 9's `TOOL_LOOP_DEFAULTS`) rather than `llm_call`.

### Current System Failures

1. **Fix 9 itself (2026-04-09, this session)** — refine was fixed to `timeout=240, max_tokens=16384` in a prior session, but three other `llm_tool_loop` call sites (`cmd_challenge`, `_run_claim_verifier`, `cmd_review_panel`) silently remained at `timeout=60, max_tokens=4096`. Opus reliably timed out on ~22KB plan reviews. The prior session's code comment literally said "60s is unworkable at 16K" but the knowledge did not propagate across call sites. Fixed today as Fix 9 + `TOOL_LOOP_DEFAULTS` refactor + linter. This is direct evidence that the scattered-literal pattern produces real bugs, not hypothetical ones.

2. **`_DEFAULT_JUDGE` drift (discovered during audit, 2026-04-09)** — `debate.py:431` defines `_DEFAULT_JUDGE = "gpt-5.4"`, but `debate.py:1861` uses `judge_model = args.model or "gemini-3.1-pro"` as a parallel inline default. Two different "judge defaults" in the same file, used by different code paths. This means: if the user runs `debate.py judge` without `--model`, one code path uses `gpt-5.4` and another uses `gemini-3.1-pro` — a latent behavior difference that has never been explicitly chosen by anyone. Not currently crashing but is a silent wrong-model call.

3. **Inline literals at `_call_litellm` (line 634)** — hardcoded `timeout=300, temperature=0.7` with no documentation. `_call_litellm` is the wrapper for judge, verdict, and consolidation calls. The `temperature=0.7` silently overrides the per-model temperature logic used elsewhere (`MODEL_PROMPT_OVERRIDES` tunes Gemini to 1.0). So Gemini-as-judge runs at 0.7, while Gemini-as-challenger runs at 1.0 — again, a behavior difference that was never chosen. This hasn't crashed anything, but it's the same class as #1: the kind of drift that produces wrong outputs until someone notices.

### Operational Context

- **`scripts/debate.py`**: 2473 lines, touched in 9 of the last 10 sessions. Central engine for `/challenge`, `/challenge --deep`, `/polish`, `/check`. Used daily.
- **Fix 9 root cause queue**: 5 entries pre-audit, 8 entries post-audit (#2-#8 from audit + #1 resolved).
- **Runs per week** (estimated from handoff and session log): ~10-20 debate/challenge/refine invocations.
- **Cost per run**: ~$1-5 for `/challenge`, ~$5-15 for `/challenge --deep`, ~$0.50-2 for `/polish`.
- **Direct dependency**: Phase 1b of CloudZero velocity v3 will add `research` and `synthesize` subcommands to this exact file. Plan at `tasks/cz-velocity-v3-plan.md` v2.3. The new subcommands will introduce ~2-4 new LLM call sites.
- **Linter infrastructure exists**: `tests/test_tool_loop_config.py` (AST-based, green) is designed to be extended. Extending it is cheap.

### Baseline Performance

**Current state before cleanup:**
- **Correctness failures attributable to scattered config**: 1 confirmed (Fix 9 — blocking bug, resolved). 2 latent (discovered during audit today: `_DEFAULT_JUDGE` drift, `_call_litellm` temperature override).
- **Time cost of discovering Fix 9**: ~45 min of debugging + ~30 min of root-cause refactor.
- **Expected incremental Phase 1b regression risk without this cleanup**: MEDIUM-HIGH. The new subcommands will introduce ~2-4 new LLM call sites. Without a shared config surface for `llm_call` sites, ~50% chance one of them copy-pastes an inline timeout/max_tokens/temperature/exception tuple.
- **Infrastructure refactor effort estimate**: ~2-4 hours for the full scope (A-F), ~30 min for the simplest version. No new tests required beyond extending the existing AST linter.

## Review questions for challengers

Please address ALL of the following:

1. **Sequencing**: Should this cleanup land BEFORE Phase 1b engineering (as proposed), AFTER, or concurrently? Pressure-test the "Phase 1b will copy-paste the pattern if we don't fix it now" premise.
2. **Scope**: Is the full A-F scope right-sized, or is it over-engineering? If SIMPLIFY, which items should stay and which should drop?
3. **Risk**: What's the actual risk of touching ~30 sites in a 2473-line file without behavior changes? Identify concrete regression scenarios. Is the existing linter + manual review enough, or do we need integration tests running before and after?
4. **The linter approach**: Is extending the AST linter the right forcing function, or is it a false-confidence trap (the linter will catch what it knows to look for, but not novel patterns)? What gaps will the linter miss?
5. **Model name centralization (#6)**: Is this actually a band-aid, or is argparse defaults at CLI boundaries a legitimate separate concern? Challenge the premise that CLI defaults need to flow through `_load_config`.
6. **Missed findings**: Read `debate.py` independently and identify at least one band-aid pattern the audit MISSED. Score the audit's completeness.
7. **Alternative approaches**: Is there a simpler structural fix we haven't considered — e.g., deleting `_call_litellm` entirely and forcing everything through `llm_tool_loop`, or making `debate.py` smaller by extracting a module?
