---
debate_id: debate-common-findings
created: 2026-04-18T09:13:36-0700
mapping:
  Judge: gpt-5.4
---
# debate-common-findings — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {}
## Frame Critique
- Category: inflated-problem
- Finding: The proposal overstates the “module-identity split risk” as a broad latent production risk when the demonstrated failure is a test-harness pathology caused by `sys.modules` manipulation.
- Why this changes the verdict: This does not negate the refactor, but it weakens the proposal’s strongest “must do now” justification. The concrete harm shown is test fragility and refactor friction, not a demonstrated runtime/user-facing defect.
- Severity: MATERIAL

## Judgment

### Challenge 1: Rename `_common.py` to `debate_common.py`
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.92
- Evidence Grade: A (tool-verified via repository/file-layout checks cited in the challenge synthesis)
- Rationale: This is a concrete naming/collision concern grounded in the existing `scripts/` convention. The proposal itself says the name is negotiable, so adopting the convention-matching name has near-zero cost and avoids an unnecessary generic top-level helper filename.
- Required change: Change the proposed target file from `scripts/_common.py` to `scripts/debate_common.py` and update all plan references accordingly.

### Challenge 2: Add Step 0 to remove `sys.modules` deletion globs before migration
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.96
- Evidence Grade: A (tool-verified specific file/line references)
- Rationale: This directly engages the proposal’s core evidence from L39 and identifies a remaining repository instance that would recreate the same class of test failure after migration. It is not generic skepticism; it is a specific precondition for the refactor to actually reduce the observed failure mode.
- Required change: Add a Step 0 before migration to remove remaining `sys.modules` manipulation against debate-related modules, including the cited `test_debate_commands.py` glob and the other noted cargo-cult patterns, with a verification grep.

### Challenge 3: Use `import debate_common; debate_common.foo()` rather than `from debate_common import foo`
- Challenger: B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.88
- Evidence Grade: B (tool-verified patch locations; binding-risk reasoning is language/runtime based)
- Rationale: This challenge is strong because it connects the proposal’s own testing/patching concerns to Python import binding behavior. The proposal did not specify import style, and the challenger identified a real way to recreate silent mock failures even after removing lazy `import debate`.
- Required change: Specify a migration-wide import rule: consumers use `import debate_common` and call helpers as `debate_common.foo()`; tests patch `debate_common.foo`.

### Challenge 4: Migrate cost-tracking state atomically
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Evidence Grade: A (tool-verified singleton/module-state structure)
- Rationale: This is a real correctness risk during transition. The proposal groups cost-tracking items together but does not explicitly require atomic migration, and split module singletons would silently fragment accounting.
- Required change: Make cost-tracking an atomic migration unit: move `_session_costs`, `_session_costs_lock`, `get_session_costs`, `_track_cost`, and `_cost_delta_since` together, and add a verification check that no `debate._track_cost`/related references remain after that step.

### Challenge 5: In transition, debate.py should call through module references rather than re-export stale bindings
- Challenger: A/B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.8
- Evidence Grade: B (partial tool verification plus import-binding reasoning)
- Rationale: This is effectively the transition-window corollary of Challenge 3. If ignored, the proposal could preserve old patch points in a way that makes tests silently patch the wrong object, undermining the stated “pure refactor” goal.
- Required change: During the migration window, have `debate.py` call helpers as `debate_common.foo()` rather than rebinding helper names with `from debate_common import foo`; update tests to patch the canonical module.

### Challenge 6: JUDGE-FRAME — the proposal inflates a test-fragility issue into a broader systemic risk
- Challenger: JUDGE-FRAME
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.84
- Evidence Grade: C (supported by proposal text and framing, but not tool-verified)
- Rationale: The proposal has solid evidence for refactor friction, noisy imports, and a real test failure. But it overreaches when presenting L39 as a broad latent architectural risk without evidence of production/runtime failures outside tests that mutate `sys.modules`. The right frame is maintainability/testability improvement, not urgent elimination of a generalized defect class.
- Required change: Rewrite the motivation to distinguish clearly between: (a) proven test fragility and refactor overhead, and (b) speculative broader module-identity risk. Do not present the latter as established systemic failure without additional evidence.

## Spike Recommendations
None

## Evidence Quality Summary
- Grade A: 3
- Grade B: 2
- Grade C: 1
- Grade D: 0

## Summary
- Accepted: 6
- Dismissed: 0
- Escalated: 0
- Spiked: 0
- Frame-added: 1
- Overall: REVISE with accepted changes
