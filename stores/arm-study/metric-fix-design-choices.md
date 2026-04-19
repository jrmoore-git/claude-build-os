# Arm-Comparison Study — Design Choices to Pressure-Test

The study compares two `/challenge` pipeline arms on shared proposals:
- **Arm A**: all roles = claude-opus-4-6 (Claude self-debate)
- **Arm B**: production multi-model mix (Opus architect, GPT-5.4 security, Gemini-3.1-pro PM, Sonnet-4-6 frame-structural, GPT-5.4 frame-factual, GPT-5.4 judge)

Scoring pipeline produces a per-dimension verdict across 7 dimensions. Pre-registered parameter choices are below. Please pressure-test each and flag systematic biases, edge cases, and empirical calibration concerns.

## 1. Quality weights (judge-graded substantive score)

```
quality_score = sum(count[cat] * weight[cat]) for cat in categories
  weight = {substantive: 3.0, marginal: 1.0, superficial: 0.5, harmful: -1.0}
```

Used for: direction_improvement, nuance_caught, net_new_ideas, catch_rate quality density.

**Questions:**
- Is 3:1:0.5:-1 defensible, or does it leak bias (e.g., an arm that produces many "marginal" items gets inflated vs an arm that produces fewer "substantive" items)?
- Should "harmful" be more negative (e.g., -3) given the asymmetric cost of harmful review output?
- Are judges actually using the "superficial" and "harmful" categories? (Observation: on n=3 runs, 100% of items landed in substantive or marginal — 0% superficial or harmful. Is the rubric failing or is the review output genuinely higher quality than the rubric expects?)

## 2. FALSIFIED source classifier (post-hoc regex on verifier output)

The verifier emits per-claim blocks with a `**Source**` field like:
```
Source: Proposal (1A), Challenger A
```

Classifier:
- Source names Challenger only → **hallucination** (bad for arm)
- Source names Proposal (only or mixed) → **caught_misquote** (good for arm)
- No source → **unclear**

**Questions:**
- The "mixed source → caught_misquote" heuristic assumes the challenger quoted the proposal in a critique context. Is this defensible? What fraction of mixed cases would be better classified as "challenger repeated proposal's wrong claim without flagging"?
- If a challenger independently asserts X that happens to also be in the proposal, Source lists both → heuristic says caught_misquote. Is this the right call?
- Empirical split on n=3: Arm A has 17 hallucinations + 6 caught-misquotes. Arm B has 1 hallucination + 7 caught-misquotes. Classified accuracy 62.2% vs 97.4%. Is this magnitude suspicious — could the classifier be systematically misattributing Arm A's claims to "Challenger only" while Arm B's sit in "Proposal + Challenger"?

## 3. Token-coverage matcher (miss_rate)

For each reference issue (with 2-5 lowercase `key_tokens`), the arm is scored as "caught" if ≥60% of tokens appear in the challenger output text (case-insensitive substring).

**Questions:**
- 60% is arbitrary. Sensitivity analysis: would 50% flip any per-dim verdicts? 75%?
- Token-overlap is a PRECISION proxy for semantic match. What's the false-negative rate when an arm catches an issue but with different phrasing? Can you estimate without a semantic matcher?
- The reference-issue generator (claude-sonnet-4-6) produces tokens. Could its token choices be systematically aligned with one arm's phrasing (e.g., Claude-family arm)?

## 4. Retrospective landing-rate formula

```
landing_rate = (landed + 0.5 * partial) / total
```

Classification by LLM: each challenger item → LANDED / PARTIAL / NOT_LANDED based on whether the downstream artifact (plan.md > refined.md > judgment.md) reflects the item.

**Questions:**
- 0.5 weight on PARTIAL is a guess. Is there prior art (review-effectiveness literature) suggesting a different weight?
- The downstream priority is plan > refined > judgment. Is this ordering defensible? Plans are concrete commitments; judgments are decisions about which challenges to accept. Does scoring against judgment give different-shaped credit than scoring against plan?
- With only 1-of-3 proposals having a real plan (others fall back to refined/judgment), is the aggregate landing-rate comparable across proposals?

## 5. Verdict promotion thresholds

- catch_rate accuracy delta ≥ 5pp
- Hallucination guardrail: winner regresses ≤ 2pp on hallucination rate
- Substantive-score delta ≥ 5.0 (absolute weighted-score units, not ratio)
- miss_rate delta ≥ 15pp
- plan_quality_delta landing-rate delta ≥ 15pp
- MIN_SAMPLE_FOR_DIRECTIONAL = 3
- MIN_SAMPLE_FOR_CONFIDENT = 5
- Harmful regression cap: 2 harmful items absolute

**Questions:**
- Do these thresholds scale together? With n=10 and small per-run variance, 5pp accuracy delta is tight; with n=3 and large variance, 5pp is loose. Should thresholds scale with sample size?
- 5.0 substantive-score units is an absolute threshold. An arm with 30 total items has far more opportunity for a 5-point delta than an arm with 10 items. Should this be relative (e.g., 15% of total)?
- Harmful regression cap of 2 absolute items — is this defensible across n=3 to n=10? At n=10, Arm B could easily accumulate 5 harmful items in normal operation while still being the better arm.

## 6. Overall verdict composition

From per-dim verdicts, the overall verdict votes:
- Each dim with `directional-favor-X` or `confident-favor-X` contributes 1 vote.
- inconclusive / regression-blocked / not-yet-measured / mixed-on-quality abstain.
- If only one arm gets votes → directional/confident favor that arm.
- If both get votes → mixed-directional.
- If neither gets votes → inconclusive.

**Questions:**
- Voting treats catch_rate (verifier-grounded) equal to nuance_caught (judge-graded). Should ground-truthed dims be weighted higher?
- A supermajority (e.g., 3 of 4 voting dims agree) doesn't automatically favor that arm — it still requires ALL voting dims to agree. Is "mixed-directional" the right label when 3 strongly favor one arm and 1 weakly favors the other?
- With n=3 and 7 dims (of which only 4 are voting: catch_rate + 3 judge-graded), is the voting resolution sufficient to overcome per-proposal noise?

## 7. Independent issue-discoverer model choice

The miss_rate reference-issue generator uses claude-sonnet-4-6 (same model as the verifier).

**Questions:**
- Claude-family model for reference-issue generation — is this independent enough? Arm A is Claude-only, so if the discoverer shares Claude's reasoning patterns, the reference list might implicitly align with Arm A's catches (inflating Arm A's coverage).
- Alternative: discover from non-Claude model (e.g., gpt-5.4). Would this materially change the reference issue list?
- Reference issues are discovered with tool access. Would a different tool-enabled model produce a materially different issue set? If so, the reference set is model-dependent, not "ground truth."

---

Review each design choice and flag any that you think has a STRUCTURAL problem (systematically biases the verdict) vs MINOR problems (tunable parameters that could be better-calibrated). Rate each section ACCEPT / TUNE / REDESIGN.

Output format: per-section response. No JSON.
