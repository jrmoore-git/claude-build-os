---
topic: debate-common
created: 2026-04-16
---
# Extract shared helpers from debate.py into scripts/_common.py

## Project Context
BuildOS is a governance framework; `scripts/debate.py` is its cross-model debate engine (used by /challenge, /review, /judge, /explore, /pressure-test, /refine, /polish). Currently 4,090 lines containing 11 `cmd_*` subcommands + ~30 shared helpers (credential loading, LLM dispatch with fallback, config loader, prompt loader, cost tracking, frontmatter builders, redaction, temperature selection). An in-progress refactor (splits 1/N–6/N, commits b818579..6bbde96) has extracted 6 subcommand handlers into sibling modules that reach back into debate.py via lazy `import debate; debate.foo()`.

## Recent Context
- Commit 51e628e (2026-04-14): AI-authored test files added a cargo-cult `del sys.modules[debate*]; import debate` block at module level. Passed CI because nothing observable broke.
- Commits b818579 through 06f3dd0 (2026-04-15..16): splits 1/N through 5/N extracted cmd_check_models, cmd_outcome, cmd_stats, cmd_compare, cmd_verdict as sibling modules. Pattern: function body moves verbatim; lazy `import debate` inside each extracted function pulls shared state. Documented as L36: "zero behavior change by construction."
- Today (2026-04-16, this session): split 6/N (cmd_explore) revealed L39 — the lazy-import pattern is NOT zero-behavior-change when combined with test-side `sys.modules` manipulation. Three test files were patching module A while the extracted function was resolving through `sys.modules` to module B, silently no-opping `fake_credentials`. Fixed the 3 test files (commit c993edf) and shipped split 6/N (commit 6bbde96). Wrote L39.
- Today (this session, later): discussed whether to continue. Claude's original F1 audit recommendation (tasks/audit-2026-04-16-fresh-eyes.md: "Split into scripts/debate/ package: _common.py... half a day... zero feature risk because tests pin behavior") was recalibrated — estimate was off 3-5x, tests did not pin what was claimed, executed architecture (sibling leaves) differs from recommended architecture (package with _common).

## Problem
The current sibling-module pattern pays two ongoing taxes and carries one latent risk:

1. **Noise tax**: every extracted function has `debate.foo()` prefix on every shared helper call. Obscures reading; no architectural clarity gained.
2. **Lazy-import tax**: every extracted function opens with `import debate` to pull shared state at call-time. Cognitive overhead, minor runtime overhead.
3. **Module-identity split risk** (L39): any test code that manipulates `sys.modules` for `debate` creates two module objects in memory. Monkeypatch fixtures bind to one; lazy `import debate` at call-time can see the other. The bug is invisible at code-review time and only surfaces when an extracted function's cross-module lookup meets an unrelated test's sys.modules shuffle. One instance found today; no guarantee another instance isn't latent in test helper files not yet touched.

The original F1 audit framed this as size ("4,629 lines"). Size is a symptom. The real problem is that debate.py is both the shared-state module AND the dispatcher AND the helper library, so any extraction from it either (a) duplicates state (rejected) or (b) reaches back through the import system (current pattern, L39-prone).

Endgame of the current execution ("debate.py as thin entry point") is architecturally unreachable from the current pattern — all shared helpers still live in debate.py, so even if all 11 cmd_* are extracted, debate.py stays ~2,400 lines of helpers.

## Proposed Approach
**Step 1**: Create `scripts/_common.py` (name negotiable — could be `debate_common.py` for sibling-naming consistency). Move these groups of symbols from debate.py:

- Credentials: `_load_credentials`, `_load_dotenv`
- LLM dispatch: `_call_litellm`, `_call_with_model_fallback`, `_get_fallback_model`, `_get_model_family`, `_challenger_temperature`, `_is_timeout_error`, `LLM_SAFE_EXCEPTIONS`, `LLMError`
- Config + prompts: `_load_config`, `_load_prompt`, prompt constants (EXPLORE_SYSTEM_PROMPT, EXPLORE_DIVERGE_PROMPT, EXPLORE_SYNTHESIS_PROMPT, CHALLENGE_SYSTEM_PROMPT, etc.)
- Cost tracking: `_estimate_cost`, `_track_cost`, `get_session_costs`, `_cost_delta_since`, `_track_tool_loop_cost`, cost rate tables
- Logging: `_log_debate_event` and the audit-log helpers
- Generic helpers: `_build_frontmatter`, `_redact_author`, `_apply_posture_floor`, `_shuffle_challenger_sections`, `_file_or_string`
- Timezone: `PROJECT_TZ`, `LLM_CALL_DEFAULTS`, `SECURITY_POSTURE_*`, `SECURITY_FLOOR_MIN`

**Step 2**: Migrate the 6 existing sibling modules (debate_check_models, debate_outcome, debate_stats, debate_compare, debate_verdict, debate_explore) from `import debate; debate.foo()` to `from _common import foo`. Remove lazy imports.

**Step 3**: Migrate debate.py itself to `from _common import …`. Delete the now-duplicated helper definitions.

**Step 4**: Update tests. The monkeypatch targets change from `debate._load_credentials` to `_common._load_credentials` (or wherever the helper lives). Audit `tests/` for any other `debate.X` attribute access or `sys.modules` manipulation.

**Step 5**: With `_common` in place, extract the remaining 5 subcommand handlers (cmd_pressure_test, cmd_review, cmd_challenge, cmd_refine, cmd_judge) as pure moves — no lazy imports, no `debate.` prefix, just `from _common import …`. cmd_premortem if non-trivial also extracts; if it's a thin wrapper over cmd_pressure_test, it may stay co-located.

**Non-goals:**
- Splitting `_common` into sub-modules. Deferred until it's genuinely over-scoped (>800 lines or unclear boundaries).
- Changing any behavior. Pure refactor.
- Extracting `cmd_main` / arg parsing into its own module. Stays in debate.py as the entry point.
- Restructuring the test suite. One-to-one test-file-per-module is out of scope; existing tests adapt to new import paths.

## Simplest Version
Minimum viable step: move ONLY `_load_credentials`, `_load_dotenv`, `_call_litellm`, `_call_with_model_fallback` (credential + dispatch core, ~250 lines) into `_common.py`. Migrate the 6 sibling modules + the 3 test files that patch `_load_credentials`. Land it. Verify the 6 extractions no longer have lazy imports and tests pass. This validates the pattern against the highest-value helpers (the ones L39 was triggered by) before committing to the full migration.

If this smallest step works cleanly, proceed to the full proposal. If it reveals surprises, stop and reassess.

### Current System Failures
1. **2026-04-16 (today)**: Split 6/N (cmd_explore extraction) caused 3 tests in `TestCmdExplore` to fail when run in the full suite but pass in isolation. Root cause: module-identity split between test patches and extracted function's lazy `import debate`. Fixed at cost of ~1 hour investigation + 2 commits.
2. **Ongoing**: Every cross-model debate call in extracted modules costs one extra line of noise (`debate.` prefix) + one lazy import statement. 6 modules × ~5 helper calls average = 30+ instances of the pattern.
3. **Ongoing**: Each additional cmd_* extraction (5 remaining) repeats the same pattern. Estimated ~45 min per extraction partly because of the lazy-import pattern setup + cross-module verification. Without _common, this cost compounds.

### Operational Context
- debate.py runs ~5-15 times/day per `stores/debate-log.jsonl` audit trail (this session alone: 4 invocations).
- Full test suite: 932 tests, 7 seconds.
- Extracted modules so far: 6 siblings (34-208 lines each, total ~644 LOC).
- debate.py: 4,090 lines currently; pre-split 4,629.
- Remaining `cmd_*` inside debate.py: 6 functions (cmd_challenge, cmd_judge, cmd_refine, cmd_review, cmd_pressure_test, cmd_premortem). Collectively ~2,800 lines if subtracted by function boundaries (includes helpers between them).

### Operational Evidence
Yes — 6 sibling extractions already shipped (splits 1/N–6/N). Concrete data:
- Per-split time: ~45 min in a session, including test verification + commit message + artifact updates.
- Line reduction per split: 34-208 lines moved; net debate.py reduction includes ~17 lines of import/boilerplate overhead per module.
- Bugs surfaced: 1 (L39, in split 6/N). 0 in splits 1-5/N. This is consistent with the claim that cross-module lookup (L39 enabler) was absent from earlier splits' fixtures.
- Test suite impact: flat. 923 → 932 tests, all passing.

Baseline: the sibling pattern works but carries the taxes described. "Zero behavior change by construction" (L36) required a boundary condition (L39) that was not documented when L36 was written.

### Baseline Performance
- Current debate.py: 4,090 lines, 87 top-level definitions (cmd_* + helpers + constants).
- Current per-extraction cost (sibling pattern): ~45 min. Risk: L39-class latent bugs, 1 instance per 6 extractions observed.
- Current per-extraction reading cost: `debate.foo()` prefix everywhere + lazy `import debate` boilerplate. Extracted module `debate_explore.py` has 20 instances of `debate.` prefix across 208 lines.
- If proposal delivers: per-extraction cost ~20 min (pure move + import update), zero lazy-import/prefix noise, module-identity split class of bug structurally eliminated.
