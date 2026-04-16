---
scope: "Phase 1: Review V2 sim scripts, add tests, harden boundaries, write orchestrator, validate against eval_intake.py baseline"
surfaces_affected: "scripts/sim_persona_gen.py, scripts/sim_rubric_gen.py, scripts/sim_driver.py, scripts/sim_compiler.py, scripts/sim_pipeline.py, tests/test_sim_persona_gen.py, tests/test_sim_rubric_gen.py, tests/test_sim_driver.py, fixtures/sim_compiler/explore/rubric.json"
verification_commands: "python3.11 -m pytest tests/test_sim_persona_gen.py tests/test_sim_rubric_gen.py tests/test_sim_driver.py tests/test_sim_compiler.py -v"
rollback: "git revert <sha> — all changes are additive (new test files, new orchestrator, small modifications to existing scripts)"
review_tier: "Tier 2"
verification_evidence: "PENDING"
challenge_artifact: "tasks/sim-generalization-challenge.md"
challenge_recommendation: "PROCEED-WITH-FIXES"
---
# Plan: sim-generalization Phase 1

## Objective

Validate V2 sim pipeline against eval_intake.py baseline on /explore. Phase 1 is the gate — if the generalized pipeline can't match the bespoke harness within 0.5 points on all 6 rubric dimensions, stop and investigate before Phase 2.

## Build Order

### Step 1a: Tests for sim_persona_gen.py [PARALLEL]
- **Create** `tests/test_sim_persona_gen.py`
- Test validation logic (hidden_state fields, diversity checks)
- Test schema enforcement (hidden_truth required field — challenge F2/A2)
- Test anchor persona loading from fixtures
- Negative tests: malformed IR input, missing required fields
- ~40-60 lines

### Step 1b: Tests for sim_rubric_gen.py [PARALLEL]
- **Create** `tests/test_sim_rubric_gen.py`
- Test universal dimensions always present
- Test deduplication logic (keyword sets)
- Test archetype-specific dimension generation contract
- Negative tests: empty IR, missing archetype
- ~40-60 lines

### Step 1c: Prompt delimiter hardening [PARALLEL]
- **Modify** `scripts/sim_compiler.py` — wrap SKILL.md content in XML delimiters before LLM injection (lines ~91-97)
- **Modify** `scripts/sim_driver.py` — wrap skill content in executor system prompt (lines ~87-102)
- **Modify** `scripts/sim_persona_gen.py` — wrap IR content in generation prompt (lines ~82-90)
- **Modify** `scripts/sim_rubric_gen.py` — wrap IR content in generation prompt (lines ~83-97)
- Pattern: `<document type="skill_procedure">...</document>` or `<document type="interaction_ir">...</document>`
- ~20-30 lines total across 4 files (challenge F4)

### Step 1d: Asymmetry invariant tests + hidden_truth field [PARALLEL]
- **Modify** `tests/test_sim_driver.py` — add tests asserting:
  - Executor system prompt contains skill procedure, NOT persona hidden state
  - Persona system prompt contains persona card, NOT skill procedure or rubric
  - Judge system prompt contains rubric, NOT persona hidden state
- **Modify** `scripts/sim_persona_gen.py` — add `hidden_truth` to required fields in validation (challenge F5/A2)
- ~15-20 lines tests, ~5 lines validation

### Step 2: Thin orchestrator [SEQUENTIAL, after 1a-1d]
- **Create** `scripts/sim_pipeline.py`
- Single entry point that chains: compile IR → generate/load personas → generate/load rubric → run simulations → aggregate scores
- Python API (importable functions), not just CLI
- Accepts: skill name, persona source (anchor dir or generate count), rubric source (file or generate), output dir
- Returns: aggregated scores dict + individual run results
- ~80-120 lines

### Step 3: Wire for /explore + baseline comparison [SEQUENTIAL, after 2]
- **Create** `fixtures/sim_compiler/explore/rubric.json` — convert eval_intake.py's 6-dimension rubric to the V2 JSON format (challenge A1: use exact same rubric for fair comparison)
- Run V2 pipeline on /explore using the 3 existing anchor personas (challenge A6: anchor only for baseline)
- Run eval_intake.py on /explore using the same 3 personas (subset of its 5)
- Compare scores dimension-by-dimension
- Gate: within 0.5 points on all 6 dimensions

## Execution Strategy

**Decision:** hybrid (parallel then sequential)
**Pattern:** fan-out → pipeline
**Reason:** Steps 1a-1d have non-overlapping file targets and independent logic. Steps 2-3 depend on all hardening/tests being complete.

| Subtask | Files | Depends On | Isolation |
|---------|-------|------------|-----------|
| 1a: persona_gen tests | tests/test_sim_persona_gen.py | — | worktree |
| 1b: rubric_gen tests | tests/test_sim_rubric_gen.py | — | worktree |
| 1c: prompt delimiters | scripts/sim_*.py (4 files) | — | worktree |
| 1d: asymmetry tests + hidden_truth | tests/test_sim_driver.py, scripts/sim_persona_gen.py | — | worktree |
| 2: orchestrator | scripts/sim_pipeline.py | 1a-1d merged | main |
| 3: baseline comparison | fixtures/*, run scripts | 2 | main |

**Synthesis:** After parallel agents complete, merge worktrees, run full test suite, verify no conflicts. Then proceed to steps 2-3 sequentially in main.

## Files Summary

| File | Action | Scope |
|------|--------|-------|
| tests/test_sim_persona_gen.py | create | Schema, validation, negative tests |
| tests/test_sim_rubric_gen.py | create | Universal dims, dedup, negative tests |
| tests/test_sim_driver.py | modify | Add asymmetry invariant assertions |
| scripts/sim_persona_gen.py | modify | hidden_truth required + prompt delimiters |
| scripts/sim_rubric_gen.py | modify | Prompt delimiters |
| scripts/sim_compiler.py | modify | Prompt delimiters |
| scripts/sim_driver.py | modify | Prompt delimiters |
| scripts/sim_pipeline.py | create | Thin orchestrator |
| fixtures/sim_compiler/explore/rubric.json | create | eval_intake.py rubric in V2 format |

## Phase 1 Gate Criteria

1. All existing tests pass (48 + new tests)
2. sim_persona_gen.py and sim_rubric_gen.py have test coverage
3. Asymmetry invariant tests pass (prompt composition per role)
4. V2 pipeline scores within 0.5 points of eval_intake.py on all 6 rubric dimensions
5. Same 3 anchor personas used for both runs

If gate 4 fails: investigate F1 (mid-loop interventions) as first hypothesis. Do NOT proceed to Phase 2.
