---
topic: sim-generalization
created: 2026-04-15
version: 2
---
# Should We Continue Building a Generalized Skill Simulation Harness?

## Project Context
Build OS is a governance framework for building with Claude Code — 22 skills, cross-model debate engine, 17 hooks. Skills are SKILL.md files defining procedures. eval_intake.py (485 lines) is a bespoke 3-agent evaluation harness that took /explore's intake protocol from 3.3→4.8/5 over 17 iterations.

The proposal was to generalize eval_intake.py into a reusable pipeline that could evaluate any skill, using 4 scripts: sim_compiler.py (IR extraction), sim_persona_gen.py, sim_rubric_gen.py, sim_driver.py (3-agent loop).

## What We Actually Built (Phase 1)

Over the current session, we built and tested the complete Phase 1:

| Component | Lines | Tests | Status |
|---|---|---|---|
| sim_compiler.py | 376 | 26 | Working, reviewed |
| sim_persona_gen.py | 270 | 54 | Working, reviewed, hidden_truth required |
| sim_rubric_gen.py | 246 | 40 | Working, reviewed |
| sim_driver.py | 463 | 31 | Working, reviewed, asymmetry tests, judge fix |
| sim_pipeline.py (orchestrator) | 165 | 0 (dry-run verified) | Working, --protocol flag added |
| Total | ~1,520 | 151 | All passing |

Additional: prompt delimiters in all 4 scripts, 9 fixture updates, rubric.json for /explore.

## The Phase 1 Gate Result: FAIL

We ran the V2 pipeline against eval_intake.py's baseline on /explore. Three runs were performed:

### Run 1: V2 with raw SKILL.md (what the generalized pipeline would use by default)

| Dimension | eval_intake baseline | V2 (SKILL.md) | Delta |
|---|---|---|---|
| register_match | 4.40 | 2.67 | -1.73 |
| flow | 4.80 | 3.67 | -1.13 |
| sufficiency_timing | 4.80 | 3.67 | -1.13 |
| context_block_quality | 4.80 | 2.67 | -2.13 |
| hidden_truth_surfacing | 4.80 | 3.33 | -1.47 |
| feature_test | 4.80 | 2.67 | -2.13 |
| **OVERALL** | **4.73** | **3.11** | **-1.62** |

### Run 2: V2 with eval_intake's refined protocol (cheating — uses the bespoke protocol)

| Dimension | eval_intake | V2 (protocol) | Delta |
|---|---|---|---|
| register_match | 4.40 | 3.00 | -1.40 |
| flow | 4.80 | 4.00 | -0.80 |
| sufficiency_timing | 4.80 | 4.00 | -0.80 |
| context_block_quality | 4.80 | 4.00 | -0.80 |
| hidden_truth_surfacing | 4.80 | 2.33 | -2.47 |
| feature_test | 4.80 | 3.00 | -1.80 |
| **OVERALL** | **4.73** | **3.39** | **-1.35** |

### Run 3: V2 with refined protocol + judge ground truth fix

| Dimension | eval_intake | V2 (fixed) | Delta |
|---|---|---|---|
| register_match | 4.40 | 3.33 | -1.07 |
| flow | 4.80 | 3.67 | -1.13 |
| sufficiency_timing | 4.80 | 3.33 | -1.47 |
| context_block_quality | 4.80 | 3.67 | -1.13 |
| hidden_truth_surfacing | 4.80 | 1.33 | -3.47 |
| feature_test | 4.80 | 3.33 | -1.47 |
| **OVERALL** | **4.73** | **3.11** | **-1.62** |

**All 6 dimensions fail the 0.5-point gate in all 3 runs.**

## Root Causes Identified

1. **eval_intake.py's quality comes from the refined protocol, not the pipeline.** The SKILL.md is a skill *definition*. eval_intake feeds the executor a 24K-char refined *conversation protocol* with 10+ register rules, sufficiency mechanics, reframe triggers. The V2 pipeline feeds the 8.5K-char skill definition.

2. **V2 persona cards are structurally weaker.** eval_intake's markdown personas have multi-paragraph behavioral scripts, hidden truth revelation triggers, and "Protocol Features Being Tested" sections. V2 JSON personas have a single `hidden_truth` string and a generic `behavioral_rules` field.

3. **No mid-loop interventions.** eval_intake injects system reminders at turn 2+ (sufficiency checklist, register matching). V2 has a bare turn loop.

4. **The gap is structural, not parametric.** Even with the exact same protocol as executor input, V2 scores 1.35 points below. The persona format and turn loop mechanics account for the remaining gap.

## The Hard Question

We've spent a full session building 1,520 lines of code and 151 tests. The pipeline infrastructure works — IR compilation, persona loading, rubric generation, turn loop, judging all function correctly. But it produces 3.1/5 quality vs eval_intake's 4.7/5.

**Option A: Keep going.** Fix the persona format, add mid-loop interventions, iterate until scores converge. This is more engineering on top of what's already built.

**Option B: Stop.** The gap proves that simulation quality comes from protocol-specific tuning, not generic infrastructure. The value of eval_intake.py was the 17 rounds of iteration on /explore's specific protocol, not the 3-agent architecture. Generalizing the architecture without the protocol-specific work is like copying a restaurant's kitchen equipment without their recipes.

**Option C: Pivot.** Use the V2 infrastructure for a different purpose — not matching eval_intake quality, but as a fast smoke test for interactive skills. A 3.1/5 score still catches gross failures. Lower the bar from "match eval_intake" to "catch broken skills."

## Current System Failures

1. ~8-10 interactive skills have zero interactive quality validation today.
2. Building a bespoke eval_*.py per skill costs ~2 days per skill.
3. Structural lint catches formatting issues but not interactive quality problems.

## Operational Context

- eval_intake.py runs manually during /explore protocol development. Not automated.
- The V2 pipeline costs ~500K-800K tokens per skill (3 personas × ~150K per simulation run + IR compilation + rubric generation).
- This session's 3 pipeline runs consumed roughly the same tokens as one /challenge --deep.
- 22 skills total, ~8-10 interactive, ~12 non-interactive (procedural/classification).

## Baseline Performance

- eval_intake.py on /explore: 4.73/5 average, 5/5 personas passing
- V2 pipeline on /explore: 3.11/5 average, 1/3 objectives achieved
- V1 /simulate smoke-test: catches structural bugs only
- Structural linter: 22/22 skills passing, no interactive coverage

## Simplest Version

If we continue at all, the simplest version is Option C: run the V2 pipeline against 5 untested skills to see if the 3.1/5-quality simulations surface any real problems. No score matching, no feature parity with eval_intake. Just: does this find bugs?
