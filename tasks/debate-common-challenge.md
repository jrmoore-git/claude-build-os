---
topic: debate-common
created: 2026-04-16
debate_id: debate-common-findings
judge: claude-sonnet-4-6
challengers: claude-opus-4-6, gpt-5.4, gemini-3.1-pro
recommendation: PROCEED-WITH-FIXES
complexity: medium
review_backend: cross-model
---
# debate-common — Challenge Synthesis

## Recommendation

**PROCEED-WITH-FIXES.** The diagnosis is sound and the staged approach is correct. Five MATERIAL findings accepted; all are specification-level, not architectural. The "simplest version" entry point (credential + LLM dispatch first) remains the right starting move. Incorporate the 5 fixes into the plan, then execute.

Signal strength: all 3 challengers independently flagged findings 1 and 2 (naming + sys.modules glob); findings 3, 4, 5 were raised by 1–2 models and cross-verified by the judge via tool calls. Evidence grade A on findings 1–4; B on finding 5. No blocking spikes, no escalations.

## Prior Context

- Original F1 audit (`tasks/audit-2026-04-16-fresh-eyes.md`) recommended the package split; estimate ("half a day") was off 3–5x, and the actual execution diverged to sibling-leaf pattern. This proposal course-corrects.
- L36 lesson claimed "zero behavior change by construction" for the sibling pattern. L39 today refined that with the boundary condition — cross-module lazy imports + test-side `sys.modules` manipulation produce silent failures.
- 6 sibling extractions already shipped (commits b818579..6bbde96); today's commit c993edf fixed 3 of 4 `sys.modules` offenders. The challenge surfaced the 4th.
- D2 (`tasks/decisions.md`): all multi-model calls route through LiteLLM proxy. `debate_common` must preserve this policy.

## Material Findings (all accepted)

### F1 — File name: `debate_common.py`, not `_common.py`
- **Source:** A, B, C (unanimous), confidence 0.88, evidence A
- **Finding:** `scripts/` has no `__init__.py`, so underscore-prefix semantics don't apply. Existing sibling convention is `debate_*.py` (`debate_explore.py`, `debate_verdict.py`, etc.). `research.py` and `enrich_context.py` also live in `scripts/` — a generic `_common.py` pollutes the shared namespace.
- **Inline fix (~0 lines of code — spec change):** Name the file `debate_common.py`. Update all references in the plan. Proposal already flagged "name negotiable"; commit to the convention-matching option.

### F2 — Step 0: purge `del sys.modules` globs BEFORE any migration
- **Source:** A, B, C (unanimous), confidence 0.92, evidence A
- **Finding:** `tests/test_debate_commands.py` lines 22-23 still contain `for mod in [k for k in sys.modules if k.startswith("debate")]: del sys.modules[mod]`. Today's c993edf fix removed this pattern from 3 test files but missed this one. Once `debate_common` is imported, this glob will purge it too, recreating the exact L39-class split the proposal aims to eliminate.
- **Inline fix (~5 lines removed):** Step 0 of the migration — delete the glob in `test_debate_commands.py:22-23`. Also inspect:
  - `tests/test_debate_tools.py:18-19` (`startswith("debate_tools")` — narrower, but same cargo-cult; remove for consistency)
  - `tests/test_debate_smoke.py:35,77` (exact-match `"debate"` — safe against `debate_common` but still cargo-cult)
- **Verification:** `grep -rn 'del sys\.modules\|sys\.modules\[' tests/` must return zero matches against any debate* module before migration begins.

### F3 — Import style: `import debate_common; debate_common.foo()` (late binding)
- **Source:** B, C, confidence 0.85, evidence A for patch locations / B for binding mechanism
- **Finding:** `debate._call_litellm` is patched in 2 test locations; `debate._call_with_model_fallback` in 1. If consuming modules use `from debate_common import foo`, the local binding is captured at import time. Patching `debate_common.foo` afterward does not retroactively update the already-bound local reference in the consuming module. Silent mock failure.
- **Inline fix (~0 new code — spec choice, one import-style rule):** All consuming modules (debate.py and the 11 sibling modules) use `import debate_common` and call `debate_common.foo()` at call sites. Tests patch `debate_common.foo` once; late binding at call-time picks up the patch across all consumers.
- **Rejected alternative:** `from debate_common import foo` + patching every consuming module's local binding (`patch('debate_explore._call_litellm')`, `patch('debate_judge._call_litellm')`, …). Brittle — every new caller is a test-update obligation. Don't.

### F4 — Cost-tracking state: migrate atomically
- **Source:** A, confidence 0.87, evidence A
- **Finding:** `_session_costs`, `_session_costs_lock`, and the three dependent functions (`get_session_costs`, `_track_cost`, `_cost_delta_since`) are module-level singletons. During a transition where some callers use `debate._track_cost()` and others use `debate_common._track_cost()`, two independent accumulator instances exist. Cost accounting silently fragments — `get_session_costs()` returns one accumulator's view while the other accumulator's deltas are invisible.
- **Inline fix (~0 lines — sequencing constraint):** Cost-tracking (`_session_costs`, lock, 3 dependent functions) migrates atomically in one commit. Before that commit is considered complete: `grep -n 'debate\._track_cost\|debate\._cost_delta_since\|debate\.get_session_costs' scripts/` must return zero matches (verification checkpoint, added to the plan's `verification_commands`).

### F5 — Transition shims: use module-reference style in debate.py
- **Source:** A, B, confidence 0.72, evidence B (partial)
- **Finding:** If `debate.py` re-exports via `from debate_common import foo` during transition, callers patching `debate.foo` patch a stale local binding that doesn't forward to `debate_common.foo`. Existing tests that patch `debate.foo` will silently no-op on the migrated helper.
- **Inline fix (~0 lines — naming convention for transition window):** During transition, `debate.py` exposes helpers via `debate_common.foo()` at call sites, not via `from debate_common import foo`. Post-migration cleanup step removes any lingering `debate.foo` patch targets in tests (migrates them to `debate_common.foo`), then drops the `import debate_common` from debate.py if it's no longer needed as a dispatch entry point.

## Advisory (noted, not blocking)

### A1 — Keep `_load_dotenv()` in `main()` only
Tool-verified single call site. Move `_load_dotenv` into `debate_common` but only invoke it from `debate.py`'s `main()`. Import-time `.env` loading as a test side effect is a well-known footgun.

### A2 — `LLMError` stays in `llm_client.py`
Tool-verified `LLMError` originates in `llm_client.py` (imported at debate.py:66). `debate_common` re-exports it as `from llm_client import LLMError` for consumer convenience; do NOT duplicate the definition.

### A3 — "Structurally eliminated" overstates
The proposal claimed module-identity split was "structurally eliminated." Technically only the lazy-`import debate` trigger is eliminated. The `from X import foo` binding pattern (F3) can recreate a functional split without any `sys.modules` manipulation. Use more precise language: "the specific L39 trigger is removed; the binding-style family of issues is addressed by the F3 import rule."

## Scope Impact Summary

| Fix | Cost | Scope Change |
|---|---|---|
| F1 rename | 0 lines | None |
| F2 Step 0 (delete glob) | ~5 lines deleted | None |
| F3 import rule | 0 net new — one spec rule applied consistently | None |
| F4 atomic migration | 0 lines — sequencing + verification | Adds one checkpoint to plan |
| F5 shim style | 0 net new — applies F3 rule to transition window | None |

**Total new code from fixes: 0 lines. Net deletions: ~5 lines (the glob).** All fixes are specifications, not implementation. None alter the staged approach or the "simplest version" starting move.

## Revised Plan Entry Conditions

Before `/plan` is executed, the proposal text should be updated in a `-refined.md` OR the plan should carry these fixes as frontmatter constraints:
1. File name: `scripts/debate_common.py`
2. Migration Step 0: audit and delete `del sys.modules` globs in tests
3. Import style: `import debate_common; debate_common.foo()` everywhere (no `from debate_common import …`)
4. Atomic migration units: credentials+dispatch (simplest version), then cost-tracking (atomic), then other helpers, then cmd_* extractions
5. Verification gate: `grep -n 'debate\.foo|debate\.bar|...' scripts/` returns zero matches before each step is marked complete
6. Advisory: `_load_dotenv` called from main() only; `LLMError` not duplicated; language cleanup on "structurally eliminated"

## Next Steps

1. Update the proposal — either in-place edits to `tasks/debate-common-proposal.md` or a new `tasks/debate-common-refined.md` — incorporating F1–F5.
2. Run `/plan debate-common` to produce the executable spec with `allowed_paths`, `verification_commands`, `rollback`, `review_tier`, `surfaces_affected`.
3. Execute the plan. Expect `/review --qa` before commit (security-adjacent surface: credential loading move).
