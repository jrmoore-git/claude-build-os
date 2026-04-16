---
debate_id: sim-generalization-findings-v2
created: 2026-04-15T19:41:46-0700
mapping:
  A: claude-opus-4-6
  B: gemini-3.1-pro
  C: gemini-3.1-pro
---
# sim-generalization-findings-v2 — Challenger Reviews

## Challenger A — Challenges
No hook/callback mechanism exists in the driver. The turn loop is monolithic.

## Challenges

1. **ASSUMPTION** [MATERIAL] [COST:SMALL]: **The proposal frames this as a binary between "generalize" and "stop," but the actual evidence points to a specific, diagnosable gap — not a fundamental impossibility.** The 1.62-point gap between eval_intake and V2 decomposes into two parts: (a) the protocol gap (~0.27 points, visible in Run 1 vs Run 2 delta), and (b) the structural gap (~1.35 points, visible in Run 2 which *uses the same protocol* but still loses). The structural gap is dominated by two verified absences: no mid-loop interventions (confirmed: `sufficiency_reminder` exists only in eval_intake.py, `intervention`/`on_turn`/`hook_callback` absent from sim_driver.py) and thin persona cards (V2 uses a JSON `hidden_state` dict with 6 scalar fields vs eval_intake's multi-paragraph markdown behavioral scripts). These are known, bounded problems — not evidence that generalization is impossible. The proposal risks a sunk-cost-fallacy-in-reverse: abandoning 1,520 lines of working, tested infrastructure because of two missing features that are architecturally straightforward to add.

2. **UNDER-ENGINEERED** [MATERIAL] [COST:MEDIUM]: **sim_driver.py has no extensibility point for mid-loop interventions, and this is the single largest contributor to the quality gap.** eval_intake.py injects a `SYSTEM REMINDER` at turn 2+ with sufficiency checklists, register matching reminders, and terse-user triggers (lines 152-164). sim_driver.py's turn loop (lines 236-299) is a bare executor→persona→termination-check cycle with zero injection points. The proposal correctly identifies this but frames it as evidence against generalization rather than as a missing abstraction. A `turn_hooks` or `mid_turn_callback` parameter on `run_simulation()` would let skill-specific interventions be passed in without making the driver bespoke. This is the difference between "the architecture can't work" and "the architecture is missing one feature."

3. **RISK** [MATERIAL] [COST:TRIVIAL]: **The token cost claim of 500K-800K per skill is ESTIMATED and could be significantly higher for skills with longer procedures or more turns.** The proposal states 3 personas × ~150K per simulation run, but sim_driver.py defaults to `DEFAULT_MAX_TURNS = 15` (line 43) while eval_intake.py uses `max_turns=8`. With 15-turn conversations, the context window grows quadratically (each turn appends to history). For skills with longer SKILL.md files (the proposal mentions /explore's SKILL.md is 8.5K chars, but the refined protocol is 24K chars), costs could easily exceed 1M tokens per skill. This matters for the Option C "run against 5 untested skills" proposal — that's potentially 4-5M tokens for a smoke test.

4. **ALTERNATIVE** [MATERIAL] [COST:SMALL]: **The proposal doesn't consider Option D: keep the V2 infrastructure but add a `protocol_overlay` concept.** The key insight from the data is that eval_intake's quality comes from the refined protocol (24K chars of specific rules) not the SKILL.md (8.5K chars of procedure). Rather than choosing between "generalize everything" and "stop," the pipeline could accept an optional protocol overlay per skill — a file containing skill-specific executor instructions, mid-loop interventions, and persona enrichment rules. This preserves the generic infrastructure (IR compilation, persona generation, rubric generation, turn loop, judging) while acknowledging that high-quality simulation requires skill-specific tuning. The `--protocol` flag already exists in sim_pipeline.py (line 160), so the plumbing is half-built.

5. **OVER-ENGINEERED** [ADVISORY]: **The IR compilation step (sim_compiler.py, 376 lines) adds an LLM call that may not carry its weight.** The IR extracts `objective`, `decision_points`, `ask_nodes`, `success_criteria`, `failure_criteria`, and `interaction_archetype` from SKILL.md. But the executor never sees the IR — it gets the raw SKILL.md. The IR is only consumed by persona generation and rubric generation. For Option C (smoke testing), pre-authored persona fixtures and rubrics would bypass IR compilation entirely, making 376 lines of code and an LLM call unnecessary for the immediate use case.

6. **UNDER-ENGINEERED** [ADVISORY]: **sim_pipeline.py has zero tests** (confirmed via check_test_coverage). While the individual components have 151 tests, the orchestrator that chains them — including the `--protocol` override path, IR caching, persona source routing, and score aggregation — is untested. For a pipeline that costs 500K+ tokens per run, a test that validates the wiring (even with mocked LLM calls) would prevent expensive debugging cycles.

7. **RISK** [ADVISORY]: **The 3.1/5 score baseline for Option C may not be stable enough to distinguish "broken skill" from "weak simulation."** If the V2 pipeline produces 3.1/5 on a known-good skill (/explore, which scores 4.73/5 with the bespoke harness), what score would it produce on a genuinely broken skill? If broken skills score 2.0-2.5/5, the signal-to-noise ratio is thin. The proposal acknowledges this implicitly ("catches gross failures") but doesn't define what score threshold would constitute a meaningful signal.

## Concessions

1. **The diagnostic honesty is exceptional.** Running three variants (raw SKILL.md, cheating with protocol, protocol + judge fix) and reporting all six dimensions failing the 0.5-point gate in all three runs is rigorous self-assessment. Most proposals would have cherry-picked the best run.

2. **The component architecture is clean.** Four scripts with clear single responsibilities (compile, persona, rubric, drive), a thin orchestrator, prompt delimiters throughout, 151 tests across the components — this is well-built infrastructure regardless of the quality gap.

3. **The root cause analysis is correct.** The proposal accurately identifies that simulation quality comes from protocol-specific tuning (the "recipes") not the pipeline architecture (the "kitchen equipment"). This is a genuine insight about the nature of LLM evaluation.

## Verdict

**REVISE** — The proposal correctly diagnoses the quality gap but draws too strong a conclusion from it. The evidence shows two specific, fixable structural deficits (no mid-loop interventions, thin persona format) accounting for the bulk of the 1.35-point residual gap. Before choosing between "keep going toward feature parity" (Option A) and "stop" (Option B), the cheapest next step is **Option D: add a `turn_hooks` callback to `run_simulation()` (SMALL cost), run one more comparison with eval_intake's sufficiency reminders injected via that hook, and measure whether the gap closes to <0.5 on at least 3/6 dimensions.** If it does, the generalized pipeline with protocol overlays is viable. If it doesn't, Option C (smoke testing) or Option B (stop) are the right calls — but you'd be making that decision with actual evidence rather than extrapolation from a pipeline missing a known-critical feature.

---

## Challenger B — Challenges
## Challenges

1. [RISK] [MATERIAL] [COST:SMALL]: **Massive token cost for a "smoke test".** The proposal suggests adopting Option C (pivot to a smoke test) using the V2 pipeline. However, this pipeline costs [EVIDENCED] 500K-800K tokens per skill. Running this across [EVIDENCED] 8-10 interactive skills implies 4M-8M tokens per full test run. Using a heavyweight 3-agent generative loop just to "catch structural bugs" is drastically over-engineered compared to basic deterministic test cases or single-agent mocked inputs. 
2. [ASSUMPTION] [MATERIAL] [COST:MEDIUM]: **Low-quality simulations generate signal, not noise.** Option C assumes a [EVIDENCED] 3.1/5 quality simulation will "catch gross failures". However, with [EVIDENCED] hidden_truth_surfacing scoring as low as 1.33 and register_match at 2.67, the simulated users are likely acting erratically or failing to trigger the actual intended edge cases of the skills. A bad simulation is more likely to generate false-positive bug reports (hallucinated failures) than find actual skill regressions. You must prove the pipeline finds *real* bugs in those 5 skills before making this the standard.
3. [OVER-ENGINEERED] [ADVISORY]: **Generalizing the wrong thing.** The proposal correctly identifies that `eval_intake.py`'s success came from 17 iterations of protocol tuning, not its 3-agent architecture. Generalizing the architecture without the protocol tuning misses the core driver of quality. 

## Concessions
1. Accurately identifies the root causes of the quality gap (protocol vs. generic pipeline, lack of mid-loop interventions).
2. Frankly admits the 1.62-point drop in performance across all 6 dimensions.
3. Provides concrete token costs and operational constraints to inform the decision.

## Verdict
**REVISE** — Before adopting Option C and absorbing 1,500 lines of new codebase surface, run the pipeline on exactly two interactive skills and manually verify if the "bugs" it finds are real or just artifacts of the degraded 3.1/5 simulation quality.

---

## Challenger C — Challenges
## Challenges

1. [RISK] [MATERIAL] [COST:LARGE]: Using a simulator that scores known-good skills at 3.1/5 as a "smoke test" will result in an unmanageable false-positive rate. If an untested skill fails under Option C, operators will have no way to distinguish whether the skill is actually broken or if the V2 persona/loop mechanics are simply degrading the interaction again. A low-fidelity test harness cannot be safely repurposed as an alert mechanism without destroying developer trust in the signal.

2. [OVER-ENGINEERED] [MATERIAL] [COST:MEDIUM]: Running a 1,520-line, 4-stage multi-agent pipeline that costs 500K-800K tokens per run [EVIDENCED] is fundamentally mismatched for a simple "smoke test." If the new objective is merely to catch structural failures or gross interactive bugs in the 8-10 untested skills [EVIDENCED], retaining the heavy `sim_driver.py` and dynamic persona generation is unjustified. Standardizing deterministic testing or using a cheap, single-agent dry-run check would be vastly more efficient and easier to maintain.

3. [ASSUMPTION] [ADVISORY]: The proposal states that a 3.1/5 score "still catches gross failures" [SPECULATIVE]. There is no data demonstrating that the pipeline's failure modes (which currently stem from weak JSON personas and missing mid-loop interventions) actually correlate with real-world skill bugs rather than just the agents going off-script due to weak system prompts.

## Concessions
1. Accurately diagnoses the root causes of the quality gap, specifically identifying that `eval_intake`'s success comes from its highly tuned conversation protocol rather than the generic pipeline architecture.
2. Avoids the sunk-cost fallacy by openly presenting Option B (Stop) instead of automatically pushing for more engineering to salvage the 1,520 lines of code.
3. Provides excellent, transparent comparative metrics that clearly quantify the degradation across specific dimensions (register match, hidden truth surfacing).

## Verdict
REJECT because Option C retains the heavy maintenance and high token costs of a multi-agent system while delivering a notoriously noisy, low-fidelity signal; either commit to fixing the pipeline's structural gaps to achieve trustworthy scores, or delete the code and stick to bespoke evaluators for high-value skills.

---
