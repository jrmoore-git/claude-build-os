---
debate_id: sim-generalization-findings-v2
created: 2026-04-15T19:43:57-0700
mapping:
  Judge: gpt-5.4
  A: claude-opus-4-6
  B: gemini-3.1-pro
  C: gemini-3.1-pro
---
# sim-generalization-findings-v2 — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gemini-3.1-pro', 'C': 'gemini-3.1-pro'}
Consolidation: 22 raw → 10 unique findings (from 3 challengers, via claude-sonnet-4-6 via local)

## Judgment

### Challenge 1: Proposal over-interprets the quality gap; missing features should be added and tested before abandoning generalization
- Challenger: A/B
- Materiality: MATERIAL
- Decision: SPIKE
- Confidence: 0.82
- Rationale: This concern is substantially valid and well-supported by tool-verified evidence: the generic driver lacks any hook/intervention mechanism, and eval_intake.py does inject turn-2+ reminders that are absent from sim_driver.py. The proposal's own evidence supports the challengers' framing that the remaining gap is structural rather than proof that generalization is impossible; however, "straightforward to add" and "bounded" are still engineering judgments, so the right response is to test the known missing features rather than mandate continued investment outright.
- Evidence Grade: A (tool-verified absence of hooks; tool-verified sufficiency reminder in eval_intake.py; proposal’s run deltas)
- Spike recommendation: Implement a minimal `turn_hooks`/intervention callback in `run_simulation()`, add one hook that reproduces eval_intake-style sufficiency/register reminders at turn 2+, and run an A/B on /explore with the existing refined protocol and current personas, then with enriched personas. Sample size: at least 5 runs per condition with fixed persona set plus 5 varied-seed runs. Success criteria: mean overall score improves by ≥0.75 and hidden_truth_surfacing improves by ≥1.0 while variance remains acceptable; BLOCKING: YES

### Challenge 2: Option C smoke-test framing is invalid because the current simulator is not calibrated and may produce untrustworthy false positives
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.91
- Rationale: This is the strongest challenge. The proposal itself shows the system scoring a known-good skill far below baseline across all dimensions, especially on hidden truth surfacing; without thresholds, calibration, or evidence of correlation with real defects, using it as a smoke-test alert mechanism would create ambiguous failures and likely erode trust. The challengers engaged directly with the proposal’s evidence rather than ignoring it.
- Required change: Do not position or deploy Option C as a smoke-test gate or alerting mechanism until calibrated against known-good and known-bad interactive skills, with explicit thresholds and estimated false-positive/false-negative behavior.
- Evidence Grade: A (directly grounded in proposal’s own measured failures)

### Challenge 3: The current 4-stage multi-agent pipeline is overbuilt for a mere smoke-test objective
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.84
- Rationale: If the objective is reduced to "catch gross failures," the challengers are right that the full generalized stack is not yet justified; the proposal itself says the simplest viable continuation is just to see whether it finds bugs, and challengers reasonably point out cheaper deterministic or fixture-based approaches for that narrower goal. This is also a conservative-bias check on the proposal: a broad infrastructure investment only makes sense if pursuing higher-fidelity simulation, not if the goal is merely coarse smoke coverage.
- Required change: If pursuing only smoke-test coverage, descoped implementation should remove dynamic generation from the critical path where possible—e.g., pre-authored persona fixtures and deterministic scenarios—rather than continuing to invest in the full generalized pipeline unchanged.
- Evidence Grade: B (supported by proposal cost/objective mismatch plus some tool-verified repo facts, though "same gross-failure-detection goal" remains partly inferential)

### Challenge 4: Token-cost estimate may be understated; total suite cost could be 4M–8M+ tokens for an unvalidated signal
- Challenger: A/B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.79
- Rationale: The cost-risk concern is valid enough to require revision. Tool-verified defaults show 15 turns in sim_driver.py versus 8 in eval_intake.py, and the proposal already admits 500K–800K tokens per skill; while the exact 4M–8M figure is extrapolative, the core point stands that the current cost model is uncertain and likely optimistic relative to longer contexts and more turns. Because this is spend/operational efficiency, the challenge clears the bar.
- Required change: Add a measured cost model from actual token accounting per stage and per skill archetype, cap max turns or make them explicit per protocol, and do not approve multi-skill runs until the calibrated cost range is documented.
- Evidence Grade: B (tool-verified turn-limit difference; extrapolated total cost is estimated rather than directly measured)

### Challenge 5: A protocol-overlay path is missing from the option set and is cheaper to validate than A/B/C
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.76
- Rationale: This is a valid omission. The proposal’s own diagnosis says protocol-specific tuning drives quality, and tool verification confirms a `--protocol` flag already exists while the driver lacks intervention hooks; challengers therefore identify a concrete middle path the proposal did not seriously evaluate. This also addresses cost of inaction: rejecting generalization entirely would leave 8–10 skills with no interactive validation, while overlay preserves useful infrastructure and acknowledges the need for skill-specific recipes.
- Required change: Add an explicit Option D/protocol-overlay path to the decision set, including optional per-skill executor overlays, intervention hooks, and persona enrichment rules, and evaluate it before deciding to stop or repurpose the system as smoke-test-only.
- Evidence Grade: A (tool-verified `--protocol` presence and hook absence; directly aligned with proposal root-cause analysis)

### Challenge 6: sim_pipeline.py has zero orchestration-layer tests
- Challenger: A
- Materiality: ADVISORY
- Decision: Not judged
- Confidence: 0.94
- Rationale: Advisory only. The absence of orchestration tests is verified and worth addressing, but it is not material to the strategic decision of whether to continue, stop, or pivot.

## Spike Recommendations
- **Blocking SPIKE for Challenge 1**
  - Measure: incremental score lift from (1) adding turn-hook reminders only, and (2) adding enriched persona format on top.
  - Sample size: 5 repeated runs per condition on /explore with same persona set, plus 5 varied-seed/persona-generation runs to assess variance.
  - Success criteria: overall mean improves by ≥0.75 from current 3.11; hidden_truth_surfacing improves by ≥1.0; at least 4/6 dimensions close to within 0.5 of eval_intake baseline.
  - BLOCKING: YES

## Evidence Quality Summary
- Grade A: 3
- Grade B: 2
- Grade C: 0
- Grade D: 0

## Summary
- Accepted: 4
- Dismissed: 0
- Escalated: 0
- Spiked: 1
- Overall: SPIKE (test first) if any blocking spikes

The challengers generally engaged well with the proposal’s actual evidence rather than hand-waving. The key balanced conclusion is:

- They are **right** that Option C is currently uncalibrated and should not be trusted as a smoke-test product.
- They are **also right** that the proposal may be too quick to treat the current failure as evidence against generalization, because the proposal itself identified two concrete missing features that were not tested.
- So the correct path is **not** "approve as-is" and **not** "abandon immediately." It is:
  1. reject Option C in its current form,
  2. require an explicit protocol-overlay option,
  3. run one blocking experiment on hooks/persona enrichment,
  4. then decide whether the system deserves continued investment or should be narrowed/abandoned.
