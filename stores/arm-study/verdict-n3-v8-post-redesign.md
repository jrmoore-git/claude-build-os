# Arm-comparison verdict

- **verdict**: `directional-favor-arm-b`
- **reason**: 1 dim(s) favor arm-b, 0 oppose; 6 abstain (inconclusive / not-yet-measured / regression-blocked)
- **n proposals**: 3
- **judges**: gemini-3.1-pro, gpt-5.4
- **run_ids**: run-20260419-202014, run-20260419-202137, run-20260419-202250

## Per-dimension verdicts (all 7 dimensions)

| Dim | Type | Verdict | Reason |
|---|---|---|---|
| catch_rate | verifier-grounded + source-classified + quality-weighted | `directional-favor-arm-b` | per-proposal weighted_accuracy delta +26.7pp favors arm-b, CI excludes 0; n_paired=3 |
| direction_improvement | judge-graded per-proposal mean (paired bootstrap) | `inconclusive` | per-proposal mean delta +9.33, 95% CI [-4.50, +21.00] includes 0 or |delta| < floor 1.5; n_paired=3 |
| nuance_caught | judge-graded per-proposal mean (paired bootstrap) | `inconclusive` | per-proposal mean delta -3.67, 95% CI [-10.50, +0.00] includes 0 or |delta| < floor 1.5; n_paired=3 |
| net_new_ideas | judge-graded per-proposal mean (paired bootstrap) | `inconclusive` | per-proposal mean delta +2.50, 95% CI [+0.00, +6.00] includes 0 or |delta| < floor 1.5; n_paired=3 |
| miss_rate | independent-discoverer + token-coverage matcher | `inconclusive` | per-proposal miss_rate delta -7.0pp, 95% CI [-27.8pp, +13.3pp] includes 0 or |delta| < 15pp |
| plan_quality_delta | retrospective-landing (plan > refined > judgment) | `inconclusive` | per-proposal landing-rate delta +4.0pp, 95% CI [-13.4pp, +21.5pp] includes 0 or |delta| < 15pp |
| code_review_quality_delta | not-yet-wired | `not-yet-measured` | Dim 7 requires retrospective scorer reading downstream code artifact (deferred — would need code-diff analysis linking t |

## catch_rate — verifier accuracy + quality density (source-classified (hallucination vs caught-misquote))

| Arm | Claims | Verified | Falsified | Unresolvable | Accuracy | Hallucination | Quality density | Weighted accuracy |
|---|---|---|---|---|---|---|---|---|
| arm-a | 70 | 28 | 23 | 19 | 62.2% | 24.3% | 100.0% | 62.2% |
| arm-b | 62 | 37 | 7 | 18 | 97.4% | 1.6% | 100.0% | 97.4% |

### FALSIFIED breakdown (item 2 of metric-fix plan)

| Arm | Hallucination | Caught-misquote | Unclear | Raw accuracy | Classified accuracy |
|---|---|---|---|---|---|
| arm-a | 17 | 6 | 0 | 54.9% | 62.2% |
| arm-b | 1 | 7 | 0 | 84.1% | 97.4% |

_Hallucination = challenger asserted X, X is false. Caught-misquote = challenger quoted proposal's false claim; credit to challenger, not a hallucination. Classified accuracy excludes caught-misquote from the denominator (not a claim the challenger made)._

## direction_improvement — quality-weighted substantive score

| Arm | Substantive | Marginal | Superficial | Harmful | Weighted score | Density |
|---|---|---|---|---|---|---|
| arm-a | 27.0 | 3.5 | 0.0 | 0.0 | 84.5 | 100.0% |
| arm-b | 36.0 | 4.5 | 0.0 | 0.0 | 112.5 | 100.0% |

## nuance_caught — quality-weighted substantive score

| Arm | Substantive | Marginal | Superficial | Harmful | Weighted score | Density |
|---|---|---|---|---|---|---|
| arm-a | 28.5 | 5.0 | 0.0 | 0.0 | 90.5 | 100.0% |
| arm-b | 25.0 | 4.5 | 0.0 | 0.0 | 79.5 | 100.0% |

## net_new_ideas — quality-weighted substantive score

| Arm | Substantive | Marginal | Superficial | Harmful | Weighted score | Density |
|---|---|---|---|---|---|---|
| arm-a | 19.0 | 1.0 | 0.0 | 0.0 | 58.0 | 100.0% |
| arm-b | 21.5 | 1.0 | 0.0 | 0.0 | 65.5 | 100.0% |

## Advisory — judge count convergence (not a gate per D40)

- Dims converged: 0/24 (0.0%)
- Mean |count_delta|: 8.0
- Max |count_delta|: 15

_Wide deltas indicate prompt looseness on extraction counts — per-dim primary signals above are independent._

## Decision thresholds (pre-registered)

- Primary accuracy delta to call a winner: 5pp
- Hallucination guardrail: primary winner may not regress > 5pp
- Substantive-score delta min: 1.5
- Substantive-score delta confident: 3.0
- Harmful rate per proposal max: 0.2
- Min sample for directional: 3
- Min sample for confident: 5
- Quality weights: {'substantive': 3.0, 'marginal': 1.0, 'superficial': 0.5, 'harmful': -1.0}
- Bootstrap B / seed: 10000 / 20260419
- Thresholds path: /Users/justinmoore/buildos/framework/config/study/arm_study_thresholds.json
- Thresholds SHA256: d8b2875330eadc28
- Thresholds source: locked-json

