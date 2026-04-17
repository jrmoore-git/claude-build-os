---
debate_id: debate-common-findings
created: 2026-04-16T18:49:26-0700
mapping:
  Judge: claude-sonnet-4-6
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# debate-common-findings — Independent Judgment

Judge model: claude-sonnet-4-6 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gpt-5.4', 'C': 'gemini-3.1-pro'}
Consolidation: 19 raw → 11 unique findings (from 3 challengers, via claude-sonnet-4-6 via local)

## Judgment

### Challenge 1: `_common.py` naming inconsistent with `debate_*` convention
- Challenger: A, B, C (all three)
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.88
- Rationale: Tool-verified that the sibling naming convention is `debate_*` (debate_explore.py, debate_verdict.py, etc.), that `scripts/` has no `__init__.py` (making underscore-prefix semantically misleading), and that `research.py` and `enrich_context.py` coexist in the directory (making a generic `_common.py` a namespace pollution risk). The proposal itself acknowledges the alternative but doesn't commit. The fix is trivial and the concern is substantive.
- Evidence Grade: A (tool-verified via check_code_presence for both sibling naming and absence of __init__.py)
- Required change: Name the file `debate_common.py` rather than `_common.py`. All import references in the proposal should reflect this name.

---

### Challenge 2: `del sys.modules` glob must be Step 0, not Step 4
- Challenger: A, B, C (all three)
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.92
- Rationale: Tool-verified that `test_debate_commands.py` lines 22-23 contain the glob pattern `for mod in [k for k in sys.modules if k.startswith("debate")]: del sys.modules[mod]` and that `del sys.modules` appears 4 times in tests. Once `debate_common` is imported, this glob will purge it too, recreating the exact L39-class split the proposal aims to eliminate. The proposal places this audit at Step 4; placing it after the migration begins means tests could silently break during the transition. This is a concrete, verified ordering risk.
- Evidence Grade: A (tool-verified via read_file_snippet and check_code_presence)
- Required change: Add an explicit Step 0 (before any code moves): audit and narrow all `del sys.modules` patterns in tests so they do not glob-match `debate_common`. The glob at test_debate_commands.py lines 22-23 must be replaced with an explicit list of module names or removed entirely.

---

### Challenge 3: `from debate_common import foo` binding breaks monkeypatching
- Challenger: B, C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.85
- Rationale: This is a real Python namespace binding issue. Tool-verified that `debate._call_litellm` is patched in 2 places in tests and `debate._call_with_model_fallback` in 1 place. Once these move to `debate_common` and consuming modules bind via `from debate_common import _call_litellm`, patching `debate_common._call_litellm` will not affect already-bound local references. The proposal does not specify a consistent import style. This is not speculative — it's a known Python behavior that will produce silent mock failures.
- Evidence Grade: A (tool-verified patch locations; B for the binding mechanism reasoning which is well-established Python semantics)
- Required change: The proposal must specify a consistent import style for all consuming modules. Recommended: use `import debate_common` and call `debate_common.foo()` in all extracted sibling modules (preserving late binding for testability). Alternatively, document that every test must patch the local binding in each consuming module (e.g., `patch('debate_explore._call_litellm')`). The transition plan must specify which approach and apply it atomically.

---

### Challenge 4: Mutable cost-tracking state creates split-accumulator hazard; ordering not explicit
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.87
- Rationale: Tool-verified that `_session_costs_lock`, `_session_costs`, and the three dependent functions (`get_session_costs`, `_track_cost`, `_cost_delta_since`) exist and are module-level singletons. During a transition where some callers use `debate._track_cost()` and others use `debate_common._track_cost()`, two independent accumulator instances exist, silently corrupting cost accounting. The "simplest version" wisely avoids moving cost tracking first, but the full proposal doesn't call out this ordering constraint explicitly. This is a verified structural hazard, not speculation.
- Evidence Grade: A (tool-verified via check_function_exists and read_file_snippet at line 848)
- Required change: Add an explicit sequencing constraint: cost-tracking state (`_session_costs`, `_session_costs_lock`, and all three dependent functions) must be migrated atomically in a single step, with a verification checkpoint confirming no remaining `debate._track_cost` / `debate._cost_delta_since` / `debate.get_session_costs` call sites exist before that step is considered complete.

---

### Challenge 5: No compatibility shim plan and no CI gate for module-identity invariant
- Challenger: A, B
- Materiality: MATERIAL
- Decision: ACCEPT (partially)
- Confidence: 0.72
- Rationale: The concern about missing shims during transition is valid — if debate.py re-exports symbols from debate_common via `from debate_common import foo`, callers patching `debate.foo` will get stale bindings. However, the CI gate recommendation (an assertion test) is advisory-level — it's a good idea but not a blocking deficiency. The shim concern is real and material; the CI gate is a best-practice enhancement.
- Evidence Grade: B (supported by verified patch patterns in tests; shim gap is a structural inference, not directly tool-verified)
- Required change: The migration plan must specify that `debate.py` re-exports symbols via `debate_common.foo()` calls (module-level reference style, not `from debate_common import foo` re-export) so that existing `debate.foo` patches continue to work during the transition window. A post-migration cleanup step should remove the re-exports once all patch targets are updated.

---

### Challenge 6: `_load_dotenv()` placement and import-time side effects [ADVISORY]
- Challenger: A
- Materiality: ADVISORY
- Decision: (noted, not judged)
- Rationale: Tool-verified single call site. The risk of import-time `.env` loading as a test side effect is real but the resolution is straightforward (keep `_load_dotenv()` in `debate.py`'s `main()`). This is a good implementation note but doesn't block the proposal.
- Evidence Grade: A (tool-verified single call site)

---

### Challenge 7: `LLMError` should remain re-exported from `llm_client.py` [ADVISORY]
- Challenger: A
- Materiality: ADVISORY
- Decision: (noted, not judged)
- Rationale: Tool-verified that `LLMError` originates from `llm_client.py` and is imported at debate.py line 66. The recommendation not to duplicate it in `debate_common.py` is sound and easy to follow.
- Evidence Grade: A (tool-verified)

---

### Challenge 8: "Structurally eliminated" overstates the guarantee [ADVISORY]
- Challenger: B, C
- Materiality: ADVISORY
- Decision: (noted, not judged)
- Rationale: Technically correct — removing lazy `import debate` from 6 sibling modules eliminates the specific L39 trigger but not the class of bug. The `from ... import` binding issue (Challenge 3) can recreate a functional split without any `sys.modules` manipulation. The proposal should use more precise language. This is an editorial concern, not a blocking deficiency.
- Evidence Grade: C (reasoning-based, but well-grounded in Python semantics)

---

## Spike Recommendations
None — all material challenges are resolvable with specification changes, not empirical tests.

---

## Evidence Quality Summary
- Grade A: 5 (Challenges 1, 2, 3, 4, 6, 7 — multiple tool-verified)
- Grade B: 1 (Challenge 5 — partially tool-verified, partially structural inference)
- Grade C: 1 (Challenge 8 — reasoning-based)
- Grade D: 0

---

## Summary
- Accepted: 5 (Challenges 1, 2, 3, 4, 5)
- Dismissed: 0
- Escalated: 0
- Spiked: 0
- Advisory (noted): 3 (Challenges 6, 7, 8)

**Overall: REVISE with accepted changes**

The proposal's diagnosis is sound and the staged approach is correct. The four accepted material changes are all specification additions, not architectural reversals:

1. **Name the file `debate_common.py`** (not `_common.py`)
2. **Add Step 0**: Audit and narrow `del sys.modules` glob patterns in tests before any code moves
3. **Specify import style**: Choose `import debate_common; debate_common.foo()` (late-binding) vs. `from debate_common import foo` + patch-local-binding, and apply it consistently across all consuming modules and tests
4. **Sequence cost-tracking migration atomically**: Treat `_session_costs` + lock + three dependent functions as an indivisible migration unit with an explicit verification checkpoint
5. **Specify transition shims**: `debate.py` must re-export via module-reference style (not `from` import) during the transition window so existing `debate.foo` patch targets remain valid

None of these changes alter the fundamental architecture or scope. The "simplest version" (credential + LLM dispatch first) remains the right entry point. Once the above are incorporated into the plan, the proposal is ready to execute.
