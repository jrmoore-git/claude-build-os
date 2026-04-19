# n=3 verdict comparison — v7 (pre-REDESIGN) vs v8 (post-REDESIGN A+B+C)

## Side-by-side per-dim verdicts

| Dim | v7 verdict | v8 verdict | Change | Explanation |
|-----|------------|------------|--------|-------------|
| **Overall** | `mixed-directional` (3B / 1A / 3 abstain) | `directional-favor-arm-b` (1B / 0A / 6 abstain) | **strengthened** | Only catch_rate (verifier-grounded) survives the stricter per-proposal CI; judge-graded dims abstain. The "mixed" signal in v7 was partly summed-score volume bias. |
| **catch_rate** | `directional-favor-arm-b` (+35.1pp pooled) | `directional-favor-arm-b` (+26.7pp per-proposal mean) | **preserved direction; magnitude smaller** | Per-proposal weighted_accuracy delta is lower than the pooled delta (n=3 has one proposal where Arm A performs better, dragging the mean) but bootstrap 95% CI still excludes 0. Floor 5pp cleared. |
| **direction_improvement** | `directional-favor-arm-b` (+28.0 summed) | `inconclusive` (mean +9.33; 95% CI [-4.50, +21.00]) | **abstained** | Summed-score volume bias removed (REDESIGN C). Per-proposal CI includes 0 — three proposals' deltas are too noisy to call directional at n=3 under strict bootstrap. |
| **nuance_caught** | `directional-favor-arm-a` (-11.0 summed) | `inconclusive` (mean -3.67; 95% CI [-10.50, 0.00]) | **abstained** | Same mechanism — per-proposal mean delta closer to zero; 95% CI just barely includes 0. The v7 directional call was a summed-volume artifact. |
| **net_new_ideas** | `directional-favor-arm-b` (+7.5 summed) | `inconclusive` (mean +2.50; 95% CI [+0.00, +6.00]) | **abstained** | Per-proposal mean +2.50 exceeds the directional floor 1.5, but 95% CI lower bound is exactly 0 — bootstrap caught the noise. |
| **miss_rate** | `inconclusive` (-8.3pp pooled) | `inconclusive` (-7.0pp per-proposal) | **preserved (no flip)** | Both versions inconclusive. Per-proposal delta (-7.0pp) very close to pooled (-8.3pp); CI [-27.8pp, +13.3pp] crosses 0 widely. n=3 is too small for directional. |
| **plan_quality_delta** | `inconclusive` (+2.9pp pooled) | `inconclusive` (+4.0pp per-proposal) | **preserved (no flip)** | Per-proposal delta slightly higher than pooled; both well within floor. |
| **code_review_quality_delta** | `not-yet-measured` | `not-yet-measured` | preserved | Dim 7 still deferred. |

## Per-dim flip decoder

- **Strengthened (1):** Overall verdict tightened from mixed-directional to directional-favor-arm-b. **Cause:** judge-graded dims now abstain when the per-proposal CI is wide; the pooled-summed thresholds in v7 were too forgiving on noisy dims, conflating "wins more proposals" with "wins by a meaningful margin."
- **Preserved direction (1):** catch_rate. **Cause:** verifier-grounded signal is strong even after the per-proposal mean reframing — CI excludes 0 + delta clears floor.
- **Preserved (no flip) (3):** miss_rate, plan_quality_delta, code_review_quality_delta. **Cause:** these were already inconclusive or not-yet-measured in v7.
- **Abstained (3):** direction_improvement, nuance_caught, net_new_ideas. **Cause:** REDESIGN C's per-proposal mean + bootstrap CI replaced the summed-score thresholds. With n=3 paired samples, the per-proposal CI is wide; the prior v7 "directional" calls were artifacts of the summed-score's verbosity bias.

All shifts are **explainable by REDESIGN C's methodology change** (per-proposal mean + paired bootstrap). No unexplained flips.

## Caveats

- **REDESIGN A not exercised** in this rerun. Existing scored.json files don't have `mechanism_classification` — the verdict aggregator fell back to regex via the `classifier_source: regex` path. The 22.7pp hallucination gap (24.3% Arm A vs 1.6% Arm B) in catch_rate is therefore still partly classifier artifact in v8 — only the INV-1 calibration + a fresh n=3 rerun with the LLM classifier active will tell us whether A3 reclassifies meaningful fractions of "caught_misquote" cases.
- **REDESIGN B not exercised** in this rerun. Existing miss-discoverer outputs are single-Sonnet (not ensemble); no `aggregation_provenance` block; matcher uses v1 substring (not v2 word-boundary). The miss_rate verdict in v8 used legacy v1 coverage data threaded through the new bootstrap aggregator. A fresh rerun with the multi-model ensemble + matcher v2 would change the per-proposal coverage values.

These caveats are expected — Step 5's purpose is to confirm REDESIGN C alone doesn't regress signal on existing data, not to revalidate A and B (which need new runs to exercise).

## Verdict on the methodology shift

REDESIGN C is **doing real work**. The pre-redesign verdict (mixed-directional) was partly an artifact of summed-score volume bias on judge-graded dims. The post-redesign verdict (directional-favor-arm-b) reflects the most-trustworthy signal (verifier-grounded catch_rate) without the noise of judge-graded dims that don't actually have a CI-excludable effect at n=3.

The directional-favor-arm-b call is **not** strengthened by my pipeline change — the catch_rate signal was the same in v7 — but the overall verdict's confidence is now better-grounded because the abstaining dims removed false signal that the legacy thresholds incorrectly counted.

For n=10:
- catch_rate is the load-bearing dim. Its current 26.7pp per-proposal mean is well above the 5pp floor and 95% CI excludes 0.
- Judge-graded dims may move from inconclusive to directional with n=10 (more paired observations → tighter CI). If the per-proposal mean direction is consistent across n=10, the bootstrap CI should narrow.
- miss_rate and plan_quality_delta need REDESIGN B's ensemble + matcher v2 to produce trustworthy data. Until those run on fresh proposals, their inconclusive status is the right answer.
