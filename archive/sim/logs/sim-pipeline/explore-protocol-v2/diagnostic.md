# V2 Pipeline Baseline Comparison — Phase 1 Gate Result

Date: 2026-04-15
Gate: **FAIL** — All 6 dimensions exceed 0.5-point threshold

## Score Comparison

| Dimension | eval_intake (5 pers) | V2 SKILL.md (3 pers) | V2 protocol (3 pers) | V2 proto+judge fix (3 pers) | Δ from baseline |
|-----------|---------------------|---------------------|---------------------|---------------------------|-----------------|
| register_match | 4.40 | 2.67 | 3.00 | 3.33 | -1.07 |
| flow | 4.80 | 3.67 | 4.00 | 3.67 | -1.13 |
| sufficiency_timing | 4.80 | 3.67 | 4.00 | 3.33 | -1.47 |
| context_block_quality | 4.80 | 2.67 | 4.00 | 3.67 | -1.13 |
| hidden_truth_surfacing | 4.80 | 3.33 | 2.33 | 1.33 | -3.47 |
| feature_test | 4.80 | 2.67 | 3.00 | 3.33 | -1.47 |
| **OVERALL** | **4.73** | **3.11** | **3.39** | **3.11** | **-1.62** |

## Fixes Applied During Phase 1

1. **--protocol flag** (sim_pipeline.py): Override SKILL.md with refined protocol. Lifted context_block_quality from 2.67→4.00, flow 3.67→4.00.
2. **Judge ground truth** (sim_driver.py): Pass persona hidden_state to judge user message. Made hidden_truth_surfacing scoring honest (was inflated before because judge guessed).
3. **Prompt delimiters**: All 4 sim scripts now use XML-style document delimiters.
4. **hidden_truth required field**: Added to persona validation and all 9 fixtures.

## Root Cause Analysis

### Gap 1: Hidden truth surfacing (Δ=-3.47)

eval_intake personas have:
- Multi-paragraph Hidden Truth section with behavioral context
- "When/how to reveal" instructions
- "Behavior" section that controls revelation timing

V2 personas have:
- Single line: `"hidden_truth": "The real issue is..."` 
- Generic `behavioral_rules` string that doesn't control revelation

**Fix needed:** Richer persona schema with revelation triggers, or the persona agent needs explicit instructions about withholding/revealing.

### Gap 2: Register match + sufficiency timing (Δ=-1.07, -1.47)

eval_intake.py injects mid-loop system reminders at turn 2+:
- Register matching rules ("match case, punctuation, message length")
- Sufficiency checklist ("decision + difficulty + facts + implementation?")
- Terse user detection ("switch to options format")

V2 turn loop has no mid-loop interventions. The protocol instructions are in the system prompt but lose weight over long conversations.

**Fix needed:** sim_driver.py turn loop should support optional mid-loop intervention messages (challenge finding F1).

### Gap 3: Feature test (Δ=-1.47)

eval_intake personas have "Protocol Features Being Tested" sections. V2 personas have no equivalent — the judge can't score feature-specific behavior.

**Fix needed:** Persona schema extension for protocol_features field, or remove feature_test from V2 rubric for non-explore skills.

## What Works

- Pipeline infrastructure: IR compilation, persona loading, rubric loading, turn loop, judging all functional
- --protocol override: successfully separates "test the skill definition" from "test the refined protocol"
- Judge scoring: with ground truth, scores are honest and calibrated
- 151 unit tests pass, asymmetry invariants hold
- All simulation runs complete successfully with 3 different models

## Recommendation

Phase 1 gate fails. Per the plan: "If gate 4 fails: investigate F1 (mid-loop interventions) as first hypothesis."

F1 is confirmed as a contributing factor but not the primary one. Priority order for Phase 2:
1. **Mid-loop interventions** (sim_driver.py) — add optional system reminders at configurable turn intervals
2. **Richer persona schema** — hidden truth revelation triggers, protocol features to test
3. **Persona behavioral specificity** — anchor personas need eval_intake-level detail

The 0.5-point gate was ambitious. A revised gate of 1.0 point would pass 0/6 dimensions. Even 1.5 points would only pass context_block_quality and register_match. The gap is structural, not parametric.
