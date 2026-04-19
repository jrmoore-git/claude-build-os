# Cross-Model Review Prompt — Arm-Comparison Metric-Fix Stack

You are reviewing a diff that implements a 6-item methodology upgrade for an arm-comparison study. The study compares two arms of a `/challenge` pipeline — Arm A (all Claude-opus-4-6) vs Arm B (production multi-model mix) — on the same proposals, using a verifier-grounded catch_rate and judge-graded secondary dimensions.

The 6 items:
1. Per-dim primary verdicts + quality-weighted accuracy (catch_rate gets weighted by judge quality density).
2. Split FALSIFIED by source — Source field regex classifies FALSIFIED as "hallucination" (challenger asserted X, X false) vs "caught_misquote" (challenger quoted proposal's false claim). Mixed source → caught_misquote by heuristic.
3. Promote direction_improvement / nuance_caught / net_new_ideas to primary signals with quality-weighted substantive score (substantive×3 + marginal×1 + superficial×0.5 + harmful×−1).
4. Surface full quality distribution per dim in markdown.
5. miss_rate independent issue-discoverer — LLM with code tools produces reference issue list per proposal; token-overlap matcher (≥60% tokens) scores each arm's coverage.
6. plan_quality_delta retrospective scorer — LLM compares arm challenge output vs downstream plan/refined/judgment artifact and classifies each item as LANDED / PARTIAL / NOT_LANDED.

Thresholds pre-registered:
- Catch_rate accuracy delta ≥ 5pp
- Hallucination guardrail: winner may not regress > 2pp on hallucination rate
- Substantive-score delta ≥ 5.0
- miss_rate delta ≥ 15pp
- plan_quality_delta landing-rate delta ≥ 15pp
- Min sample for directional: n=3; confident: n=5
- Harmful regression cap: 2 harmful items absolute

## Your task

Review the diff below with three questions in mind, in order of priority:

1. **Contract bugs.** Any function signature mismatch, wrong flag name, key missing on one side of a producer/consumer pair, silent error swallow? (Prior session found exactly this class of bug — `arm_study_scorer.py` was calling `debate.py judge --input` but `judge` requires `--proposal --challenge --output`. Stderr + exit_code were dropped in the failure store, so the bug was invisible. Commits f8f9c65 and 96142ab fix and extend. Look for similar patterns.)

2. **Methodology leakage.** Does any score calculation inadvertently favor one arm for structural reasons unrelated to arm quality? Example concerns:
   - Does the quality-weighted accuracy formula get gamed if one arm produces more items in easy categories (substantive volume-pumping)?
   - Does the FALSIFIED source classifier's "mixed source → caught_misquote" heuristic systematically credit one arm?
   - Does the 0.6 token threshold on the miss-rate matcher have a known failure mode where synonym-heavy arms score artificially low?
   - Does the retrospective landing-rate formula (landed + 0.5×partial) privilege arms whose items are easier to locate as text-matches in the downstream doc?
   - Does the miss_rate reference-issue generator produce issues that look more like Arm B's phrasing than Arm A's?

3. **Silent-failure modes.** What data shapes would cause a verdict to be silently wrong rather than flagged? Examples:
   - Empty quality_distribution on one arm dim
   - verify_claims.stats disagreeing with falsified_classification parsed totals (truncation)
   - miss_reference_issues.json with 0 issues after LLM failure
   - retrospective.json with `status: scored` but empty per_arm

Emit findings as a structured list. For each finding:
- **Category**: one of {contract-bug, methodology-leak, silent-failure, spec-drift, minor}
- **Severity**: one of {MATERIAL, MINOR}
- **Location**: file:line or symbol
- **What's wrong** in one sentence
- **Evidence** (quote the line or cite the pattern)
- **Suggested fix** in one sentence

Rate the overall stack: ACCEPT (no blockers), REVISE (MATERIAL findings must be addressed), or REJECT (structural problem with the approach).

Output format: plain markdown, no JSON wrapper, no code fences around the final report.
