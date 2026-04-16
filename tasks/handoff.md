# Handoff — 2026-04-15 (session 15)

## Session Focus
Built full Phase 1 of sim generalization, ran baseline comparison (FAIL), ran fresh cross-model challenge with failure data — verdict: PAUSE for one spike experiment.

## Decided
- Phase 1 gate FAILS: V2 pipeline scores 3.11/5 vs eval_intake's 4.73/5, all 6 dimensions exceed 0.5-point threshold
- Root causes: no mid-loop interventions, thin JSON persona cards, SKILL.md ≠ refined protocol
- Panel + judge: PAUSE. Option C (smoke test 5 skills) rejected as uncalibrated. Option D (protocol overlays) identified as missing path.
- Spike experiment required before deciding to continue or stop

## Implemented
- scripts/sim_pipeline.py — thin orchestrator with --protocol override, --dry-run
- tests/test_sim_persona_gen.py — 54 tests (validation, diversity, loading)
- tests/test_sim_rubric_gen.py — 40 tests (universal dims, dedup, CLI)
- tests/test_sim_driver.py — 10 asymmetry invariant tests added (31 total)
- Prompt delimiters in all 4 sim scripts (XML-style document boundaries)
- hidden_truth as required field in sim_persona_gen.py + 9 fixture updates
- Judge ground truth fix in sim_driver.py (persona hidden_state in judge user message)
- fixtures/sim_compiler/explore/rubric.json (eval_intake rubric in V2 format)
- 3 baseline comparison runs with full diagnostics in logs/sim-pipeline/
- Fresh challenge: proposal-v2, findings-v2, judgment-v2, challenge-v2

## NOT Finished
- Spike experiment: add turn_hooks to sim_driver.py, test on /explore
- sim_pipeline.py has zero orchestration-level tests
- lessons.md and decisions.md not updated this session

## Next Session Should
1. Read `tasks/sim-generalization-challenge-v2.md` for spike criteria
2. Add `turn_hooks` callback to `run_simulation()` in sim_driver.py (~30 lines)
3. Write one hook reproducing eval_intake's sufficiency/register reminders (~20 lines)
4. Run 5 /explore sims with hook. Success: overall ≥3.86, hidden_truth ≥2.33, 4/6 dims within 0.5 of baseline
5. If spike passes → Option D (protocol overlays). If fails → stop, keep eval_intake.

## Key Files Changed
- scripts/sim_pipeline.py (new orchestrator)
- scripts/sim_driver.py (judge ground truth fix)
- scripts/sim_persona_gen.py (hidden_truth required, prompt delimiters)
- tests/test_sim_persona_gen.py, test_sim_rubric_gen.py, test_sim_driver.py (new/expanded)
- fixtures/sim_compiler/*/personas/anchor-*.json (hidden_truth added)
- fixtures/sim_compiler/explore/rubric.json (new)
- tasks/sim-generalization-{proposal,findings,judgment,challenge}-v2.md (new)
- logs/sim-pipeline/ (3 baseline runs with diagnostics)

## Doc Hygiene Warnings
- ⚠ lessons.md NOT updated — should add: "V2 pipeline quality gap is structural (persona format + mid-loop interventions), not architectural"
- ⚠ decisions.md NOT updated — should add: Phase 1 gate result + PAUSE decision
