---
topic: sim-generalization
created: 2026-04-15
recommendation: PROCEED-WITH-FIXES
complexity: medium
review_backend: cross-model
challengers: claude-opus-4-6, gpt-5.4, gemini-3.1-pro
security_posture: 3
---
# Challenge Gate: Generalize eval_intake.py into a Reusable Simulation Harness

## Recommendation: PROCEED-WITH-FIXES

The core direction is sound — all 3 challengers agree the problem is real, the evidence is strong, and the phased approach with an explicit baseline gate is correct. Material findings cluster into missing test/validation gates and one unscoped integration decision. All fixes are SMALL or TRIVIAL. No architectural objections.

## Challenger Verdicts

| Challenger | Model | Verdict | Tool calls |
|---|---|---|---|
| A | claude-opus-4-6 | REVISE | 59 |
| B | gpt-5.4 | REVISE | 20 |
| C | gemini-3.1-pro | APPROVE | 7 |

## MATERIAL Findings

### F1: Mid-loop intervention mechanism missing [COST:MEDIUM] [STATUS:PHASE-1-DISCOVERY]
**Source:** Challenger A
**Finding:** eval_intake.py's quality comes from protocol-specific scaffolding (sufficiency reminders at turn 2, terse-user detection, register enforcement) baked into the loop. sim_driver.py has a generic executor-persona loop with no mid-conversation coaching. The baseline comparison may fail because of this gap, not because the architecture is wrong.
**Assessment:** Valid concern, but this is exactly what Phase 1 is designed to surface. The baseline comparison will reveal whether generic sim_driver.py matches eval_intake.py's scores. If it doesn't, this is the first hypothesis to investigate. Not a blocker — a Phase 1 discovery item. If needed, a `skill_hooks` callback parameter in sim_driver.py (~50-80 lines) would address it.

### F2: sim_persona_gen.py and sim_rubric_gen.py have zero tests [COST:TRIVIAL]
**Source:** Challengers A + B (independent convergence)
**Finding:** Both modules have validation and deduplication logic but no test coverage. These generate inputs consumed by other models — malformed outputs propagate.
**Fix:** Add as explicit Phase 1 gate condition. Write schema/negative tests before wiring end-to-end. ~40-60 lines of test code per module.

### F3: Pipeline integration surface undefined [COST:SMALL]
**Source:** Challenger A
**Finding:** No import relationships between the 4 scripts (`import sim_` appears 0 times). No shared interface contract. The integration layer — how scripts chain together — is the actual new work and it's unscoped.
**Fix:** Design the integration surface as first step of Phase 1. Options: thin orchestrator script, Python API layer, or CLI chaining via file I/O. Decision should be made before building, not discovered during build. ~30-50 lines for a thin orchestrator.

### F4: Prompt-boundary hardening missing [COST:SMALL]
**Source:** Challenger B
**Finding:** Raw SKILL.md content injected into LLM prompts across trust boundaries (sim_compiler.py:91-97, sim_driver.py:87-102, sim_persona_gen.py:82-90, sim_rubric_gen.py:83-97). Needs explicit delimiters and role separation.
**Fix:** Add XML/markdown delimiters around injected content in prompt templates. ~20-30 lines across 4 scripts.

### F5: Information-asymmetry invariant untested [COST:TRIVIAL]
**Source:** Challenger B
**Finding:** The key differentiator (persona never sees procedure, executor never sees hidden state) has no structural test. A wiring mistake could silently collapse this boundary.
**Fix:** Add assertion tests that check prompt composition per role. ~15-20 lines in sim_driver tests.

### F6: IR extraction telephone game [COST:SMALL]
**Source:** Challenger C
**Finding:** 3-stage LLM extraction (SKILL.md → IR → persona/rubric) may lose nuance. Alternative: pass raw SKILL.md directly to persona/rubric generators.
**Assessment:** Valid concern but premature to act on. The IR is also used for other purposes (interaction archetype classification, state tracking). Phase 1 baseline comparison will reveal whether IR quality is sufficient. If scores diverge, test the raw-SKILL.md alternative. Not a fix — a Phase 1 investigation item.

## ADVISORY Findings

| # | Finding | Source | Note |
|---|---|---|---|
| A1 | Use eval_intake.py's exact rubric for baseline comparison | A | Prevents apples-to-oranges scoring. Include as Phase 1 setup step. |
| A2 | hidden_truth should be a required field in persona schema | A | Currently validated loosely. Add to persona_gen validation. |
| A3 | Add one non-explore skill to Phase 1 | A | Tests generalization earlier. /investigate has reference IR already. |
| A4 | Model assignment per role is tunable, not fixed | A | Note for Phase 2, not Phase 1. |
| A5 | Token cost is estimated, measure on Phase 1 runs | B | Track actual token usage during Phase 1. |
| A6 | Use anchor personas only first, defer generated | B | Reduces variables during baseline comparison. |
| A7 | eval_intake.py deprecation path if Phase 1 succeeds | C | Decision to make after Phase 1, not before. |

## Inline Fixes for Build

These must ship with Phase 1, not deferred:

1. **Test coverage gate** (F2) → Write tests for sim_persona_gen.py and sim_rubric_gen.py before wiring pipeline. ~40-60 lines each.
2. **Integration surface design** (F3) → Define how the 4 scripts chain before building. Write a thin orchestrator or API layer. ~30-50 lines.
3. **Prompt delimiters** (F4) → Add boundary markers around injected content in all 4 scripts. ~20-30 lines total.
4. **Asymmetry invariant tests** (F5) → Add tests asserting prompt composition per role in sim_driver. ~15-20 lines.
5. **Use exact eval_intake.py rubric for baseline** (A1) → Don't compare generated rubric against hand-authored one. Use the same rubric for both runs.
6. **Anchor personas only for baseline** (A6) → Generated personas tested separately, after baseline parity proven.

## Cost of Inaction

If we don't build this:
- ~8-10 interactive skills have zero interactive quality validation
- Register mismatch, timing bugs, and protocol drift are invisible to lint and single-turn eval
- Each new bespoke eval_*.py costs ~2 days, doesn't scale to 8-10 skills
- The 1,355 lines of V2 code (48 tests) sit unreviewed and unwired indefinitely

## Complexity: MEDIUM

One new concept (generalized simulation harness from proven bespoke harness) with clear justification. Existing code reduces net-new work. Phase 1 gate limits blast radius.
