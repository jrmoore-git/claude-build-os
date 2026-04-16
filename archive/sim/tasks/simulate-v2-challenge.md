---
topic: simulate-v2
created: 2026-04-15
review_backend: standard
models: claude-opus-4-6, gpt-5.4, claude-sonnet-4-6
judge: gpt-5.4
refine_rounds: 3
refine_models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
recommendation: PROCEED-WITH-FIXES
complexity: medium
---
# Challenge Result: PROCEED-WITH-FIXES

The problem is real (all 3 challengers concede), the 3-agent architecture is validated by eval_intake.py, and the pilot scope is well-bounded. Seven material findings were accepted by the independent judge — all have concrete fixes that the 3-round cross-model refine has already incorporated into the refined proposal.

## MATERIAL Findings (7 accepted, 0 dismissed)

### F1: IR extraction has no ground truth — human gate required
- **Challengers:** A/B/C (unanimous) | **Judge confidence:** 0.95
- **Cost:** MEDIUM (adds ~1 hour per pilot skill)
- **Fix:** Hand-author reference IR for each pilot skill. Second reviewer compares extracted vs. reference using a 6-field checklist. Hard gate: simulation blocked until all fields pass.
- **Status:** Incorporated in refined proposal (Section 1, Phase 1).

### F2: V2 is greenfield, not an extension of V1
- **Challengers:** A | **Judge confidence:** 0.93
- **Cost:** TRIVIAL (reframe only)
- **Fix:** Reframe as net-new "Skill Compiler Simulator" project. Explicitly list what reuses eval_intake.py vs. net-new. Defer `/simulate` CLI integration to post-pilot.
- **Status:** Incorporated in refined proposal (Status Quo section, Implementation Scope).

### F3: Convergence stopping criterion is undefined
- **Challengers:** A/B/C (unanimous) | **Judge confidence:** 0.94
- **Cost:** TRIVIAL (descope)
- **Fix:** Remove convergence from pilot. Commit to fixed-N (10 runs per skill). Defer convergence logic to post-pilot iteration with pilot failure data as input.
- **Status:** Incorporated in refined proposal (Non-Goals, Pilot Plan).

### F4: OCEAN + 8 fields is over-engineered for pilot
- **Challengers:** A/B/C (unanimous) | **Judge confidence:** 0.85
- **Cost:** TRIVIAL (descope)
- **Fix:** Drop OCEAN entirely. Reduce to 6 behavioral fields (goal, knowledge, urgency, patience, trust, cooperativeness). Add dimensions only when pilot data shows the simpler model misses failure classes.
- **Status:** Incorporated in refined proposal (Section 2).

### F5: Score-matching success criterion is circular
- **Challengers:** B/C | **Judge confidence:** 0.88
- **Cost:** SMALL (~20 lines to implement rubric comparison)
- **Fix:** Primary metric: rubric dimension coverage >= 80% weighted overlap against hand-authored eval_intake.py rubric. Score comparison demoted to secondary calibration (not a gate).
- **Status:** Incorporated in refined proposal (Section 4, Success Criteria).

### F6: 3-agent loop lacks mechanical specification
- **Challengers:** A/B | **Judge confidence:** 0.90
- **Cost:** SMALL (spec writing, not code)
- **Fix:** Specify prompt wiring, turn structure, termination conditions, tool/file policy, judge timing. Explicit reuse of eval_intake.py mechanics via llm_client.py.
- **Status:** Incorporated in refined proposal (Section 3).

### F7: No output schema for V2 results
- **Challengers:** C | **Judge confidence:** 0.87
- **Cost:** TRIVIAL (~30 lines)
- **Fix:** JSONL schema defined with per-run fields: run_id, persona_state, transcript, judge_scores, termination_reason, rubric_metadata. Storage: `logs/sim_compiler_runs.jsonl`.
- **Status:** Incorporated in refined proposal (Section 5).

## ADVISORY Findings (noted, not gating)

- **Model contamination risk:** Gemini serves as both persona model and refine rotation model. Not a pilot blocker but track before generalizing.
- **debate.py maintainability:** 4136 lines with no tests. New simulator should be a separate module.
- **Token cost is ESTIMATED:** ~1.5-2M for pilot, ~4-5.5M for 10-skill production. Measure during pilot.
- **Alternative: templatize eval_intake.py:** Plausible lower-risk path. The compiler approach is riskier but higher ceiling. Pilot will validate whether the risk is justified.

## Artifacts

- `tasks/simulate-v2-proposal.md` — input proposal
- `tasks/simulate-v2-findings.md` — raw 3-model challenge output
- `tasks/simulate-v2-judgment.md` — independent GPT-5.4 judgment (7 accepted)
- `tasks/simulate-v2-refined.md` — 3-round cross-model refined proposal

## Next

The refined proposal (`tasks/simulate-v2-refined.md`) is the build-ready spec. All 7 material findings are addressed.

-> `/plan simulate-v2` to create the implementation plan from the refined proposal
