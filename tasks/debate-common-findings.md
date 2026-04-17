---
debate_id: debate-common-findings
created: 2026-04-16T18:46:32-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# debate-common-findings — Challenger Reviews

## Challenger A — Challenges


## Challenges

1. **RISK** [MATERIAL] [COST:SMALL]: **`_common.py` naming creates an import ambiguity with Python conventions.** The underscore-prefixed `_common.py` in a flat `scripts/` directory is unconventional — underscore-prefixed modules typically signal "private to a package," but `scripts/` is not a package (no `__init__.py`). The existing sibling modules use the `debate_*` naming convention (`debate_explore.py`, `debate_verdict.py`, etc.). Naming it `debate_common.py` instead of `_common.py` would be consistent with the established pattern and avoid confusion. The proposal acknowledges this ("name negotiable — could be `debate_common.py`") but doesn't commit. This should be a build condition: use `debate_common.py`.

2. **ASSUMPTION** [MATERIAL] [COST:MEDIUM]: **The proposal assumes ~30 helpers can move cleanly, but debate.py has mutable module-level state that complicates extraction.** Verified: `_session_costs_lock` (a `threading.Lock`) and `_session_costs` (a mutable dict) are module-level singletons in `debate.py` (line ~869). `get_session_costs()`, `_track_cost()`, and `_cost_delta_since()` all mutate/read this shared state. Moving these to `debate_common.py` means the cost accumulator lives in a different module than the callers. This works IF all callers import from the same module — but the transition period (Step 2 vs Step 3) creates a window where some callers use `debate._track_cost()` and others use `debate_common._track_cost()`, potentially splitting the accumulator into two instances. The "simplest version" (Step 1: move ~250 lines of credential + dispatch) wisely avoids this by not moving cost tracking first, but the full proposal doesn't call out this ordering constraint explicitly. The cost-tracking state migration needs its own atomic step with verification that no caller path sees a stale accumulator.

3. **RISK** [MATERIAL] [COST:SMALL]: **4 instances of `del sys.modules` in tests remain a live hazard during migration.** Verified: `del sys.modules` appears 4 times in the test suite, and `test_debate_commands.py` lines 22-25 show the cargo-cult pattern (`for mod in [k for k in sys.modules if k.startswith("debate")]: del sys.modules[mod]`). This glob pattern will also delete `debate_common` from `sys.modules` if it's been imported, creating exactly the L39-class bug the proposal aims to eliminate. Step 4 says "audit tests for sys.modules manipulation" but this should be Step 0 — these `del sys.modules` blocks must be removed or narrowed BEFORE the migration, not after. If `debate_common` is imported and then purged by this glob, any subsequent `import debate_common` in the same process creates a second module object, and monkeypatches bound to the first object become invisible.

4. **UNDER-ENGINEERED** [MATERIAL] [COST:TRIVIAL]: **No smoke test or CI gate proposed for the module-identity invariant.** The proposal eliminates the L39 class of bug structurally, but doesn't add a regression test that would catch it if someone reintroduces `sys.modules` manipulation or lazy imports. A single test asserting `debate_common is sys.modules['debate_common']` after importing through all paths would be a cheap sentinel. Without it, the structural guarantee is only as durable as code review discipline.

5. **ALTERNATIVE** [ADVISORY]: **The existing `llm_client.py` already provides a shared LLM abstraction.** Verified: `debate.py` line 66 imports `from llm_client import llm_call, llm_call_raw, LLMError`. The proposal lists moving `LLMError` and LLM dispatch helpers into `debate_common.py`, but `LLMError` is already exported from `llm_client.py`. The debate-specific wrappers (`_call_litellm`, `_call_with_model_fallback`) add debate-specific concerns (cost tracking, temperature selection, fallback logic), so they do belong in a debate-specific module — but the proposal should explicitly note that `LLMError` should continue to be re-exported from `llm_client.py` rather than duplicated.

6. **OVER-ENGINEERED** [ADVISORY]: **The "non-goal" of not splitting `_common` is correct but the 800-line threshold is arbitrary.** The proposed `_common` will contain credentials, LLM dispatch, config, cost tracking, logging, frontmatter, redaction, posture, timezone, and prompt constants. The prompt constants alone (CHALLENGE_SYSTEM_PROMPT, EXPLORE_SYSTEM_PROMPT, etc.) are multi-hundred-line string literals (verified: lines 195-774 are largely prompt constants). This module will likely exceed 800 lines on day one. The threshold should be "when there are two clearly distinct dependency graphs within the module" rather than a line count.

7. **RISK** [ADVISORY]: **`_load_dotenv()` is called exactly once (verified: 1 match in scripts).** Moving it to `debate_common.py` means it must be called at import time or explicitly by the entry point. If called at import time, every test that imports `debate_common` triggers `.env` loading as a side effect. If called explicitly, the entry point must remember to call it. The proposal doesn't specify which approach. The safe choice is: `_load_dotenv()` stays in `debate.py`'s `main()` and is NOT moved to `debate_common`.

## Concessions

1. **The problem diagnosis is precise and well-evidenced.** The L39 bug, the lazy-import tax, and the architectural dead-end of "debate.py as thin entry point being unreachable" are all verified by the tool data. The 6 sibling modules genuinely do use `debate.foo()` prefix throughout, and the `sys.modules` manipulation in tests is a real ongoing hazard.

2. **The "simplest version" strategy is sound.** Starting with credential + dispatch (~250 lines), validating against the 6 existing siblings, and only then proceeding to the full migration is the right risk-management approach. It targets exactly the helpers that triggered L39.

3. **The operational data is honest.** The proposal correctly recalibrated from the original "half a day, zero feature risk" estimate, documented the L39 surprise, and provided concrete per-split timing data. This is a team that learns from its mistakes.

## Verdict

**APPROVE** with three build conditions: (1) name the file `debate_common.py` not `_common.py`; (2) remove/narrow the `del sys.modules` glob in `test_debate_commands.py` as Step 0 before any migration; (3) keep `_load_dotenv()` in `debate.py`'s entry point rather than moving it to the common module.

---

## Challenger B — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposal frames this as a “pure refactor” but does not include an explicit compatibility plan for current test/import consumers of `debate._call_with_model_fallback`, `debate._load_credentials`, etc. Verified code shows tests directly monkeypatch `debate` today (`tests/test_debate_fallback.py` patches `debate._call_litellm`; `tests/test_debate_commands.py` imports `debate` after clearing `sys.modules`). Moving helpers outright to `_common.py` without temporary re-exports from `debate.py` creates avoidable breakage and can reintroduce module-identity confusion in a different form if some callers patch `debate.X` while others patch `_common.X`. Fix: keep `debate.py` re-export shims during a transition and standardize patch targets in one pass.

2. [RISK] [MATERIAL] [COST:SMALL]: Centralizing credentials, prompt text, logging, and LLM dispatch into a generic `scripts/_common.py` widens the trust boundary unless imports are kept intentionally narrow. Today `debate.py` is a single-purpose entrypoint; after extraction, any sibling script under `scripts/` can import helpers that load secrets from `.env`, talk to LiteLLM, or write debate audit logs. That is not automatically unsafe, but it does increase the blast radius for accidental misuse, test leakage, or future prompt injection paths from unrelated modules. If you proceed, `_common.py` should expose only debate-scoped helpers and avoid becoming a general “shared utilities” bucket with secret-loading side effects.

3. [ASSUMPTION] [ADVISORY]: The claim that module-identity split bugs are “structurally eliminated” is too strong. This change removes one specific trigger: lazy `import debate` inside extracted handlers, which is verified to exist in 6 places (`scripts/debate_explore.py` shows the pattern; code search found 6 matches). But tests still manipulate `sys.modules`, and future callers could still import/patch `debate` and `_common` inconsistently. The risk is reduced materially, not eliminated absolutely.

4. [ALTERNATIVE] [ADVISORY]: The “smallest version” is the safer security/operational move than the full helper migration. The concrete failure described involved credential/loading + dispatch lookup, not prompt constants, frontmatter, or cost tables. Since the highest-risk boundary is secret loading plus outbound LLM calls, extracting only those first gives you the architectural proof without immediately broadening import access to every debate constant and logging helper.

## Concessions
- The proposal correctly identifies a real flaw, not a hypothetical one: verified code shows lazy `import debate` in extracted modules, and verified tests manipulate `sys.modules`, matching the documented failure mode.
- It evaluates both directions of risk: continuing the current pattern repeats the same import/patch hazard on the 5 remaining extractions.
- The staged “minimum viable step” is a sound rollback-friendly way to validate the new boundary before a full migration.

## Verdict
REVISE — the refactor direction is sound, but add a compatibility/shim plan and tighter `_common.py` scope so the fix reduces import-state risk without expanding secret-bearing shared surface unnecessarily.

---

## Challenger C — Challenges
## Challenges
1. [RISK] [MATERIAL] [COST:SMALL]: **Mock Binding Failure via `from ... import`**. The proposal specifies migrating extracted modules to `from _common import foo` and updating test patches to target `_common.foo`. Due to Python's namespace binding rules, patching `_common.foo` will *not* mock the function in modules that have already bound it locally via `from ... import`. You must either change the proposed import style to `import debate_common` (retaining `debate_common.foo()` calls), or rewrite the test patches to target the local reference in each consuming module (e.g., `patch('debate_explore._load_credentials')`).
2. [RISK] [ADVISORY]: **Namespace Pollution**. Creating a generic `scripts/_common.py` introduces ambiguity for other scripts (e.g., `research.py`, `enrich_context.py`). Proceed with your parenthetical suggestion to name it `debate_common.py` to maintain explicit scoping.

## Concessions
1. Correctly identifies that the current lazy-import sibling pattern has hit its architectural ceiling and actively introduces `sys.modules` test fragility.
2. The "Simplest Version" increment is perfectly right-sized: it validates the highest-risk extraction (credentials and LLM dispatch) without committing to moving all 4,000 lines at once.
3. Pragmatically defers unnecessary directory restructuring (like creating a `scripts/debate/` package) to focus purely on untangling the shared state.

## Verdict
APPROVE. The extraction solves a real, proven testing fragility (L39) and removes ongoing cognitive tax, provided the test patching strategy is adjusted for Python's import binding rules.

---
