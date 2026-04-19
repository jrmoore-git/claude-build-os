---
topic: arm-study-b-prereg
created: 2026-04-19
phase: pre-registration
locked_before_run_id: TBD-n10-kickoff-commit
purpose: "Lock B-variant TUNE configurations before n=10 to enforce sensitivity analysis discipline (no post-hoc selection)."
---

# B-variant pre-registration — n=10 sensitivity analysis

## Context

Cross-model `/review` on the metric-fix stack flagged 6 design dimensions:
- **A (REDESIGN, both reviewers):** FALSIFIED classifier, miss-rate matcher, verdict thresholds. **Shipped in commits b18d97c, 128fc42, c90799b** (gated on INV-1 calibration + cross-model post-build review v1+v2).
- **B (TUNE, both reviewers):** quality-weight ratio, retrospective landing-rate stratification, overall verdict composition (supermajority + weighted dims).

A is structural — must affect data collection or pre-registered thresholds before n=10.

B is post-hoc applicable on scored.json — apply each variant after the n=10 arm runs complete and report verdict under each B configuration as a sensitivity table.

This document **freezes the B variants** before n=10 kicks off so no post-hoc selection is possible. Once the n=10 scored.json files exist, only the variants below run; no others.

## B-variant 1: Quality weights (judge-graded dims)

Current (locked in `config/study/arm_study_thresholds.json:quality_weights`): `substantive=3.0, marginal=1.0, superficial=0.5, harmful=-1.0`.

Pre-registered alternates to evaluate:

| Variant | substantive | marginal | superficial | harmful | Rationale (cross-model review) |
|---------|-------------|----------|-------------|---------|--------------------------------|
| **B1a** | 3.0 | 1.0 | 0.5 | -1.0 | Baseline (locked). |
| **B1b** | 3.0 | 1.0 | 0.5 | -2.0 | gpt-5.4: "harmful=-1 likely underprices downside." Test whether a stronger penalty changes verdicts when harmful items appear. |
| **B1c** | 3.0 | 1.0 | 0.5 | -3.0 | gemini: "harmful should be heavily penalized (e.g. -3 or -5)." |
| **B1d** | 3.0 | 1.0 | 0.0 | -1.0 | gpt-5.4: "Collapse or sharpen the low-end categories — if judges don't reliably distinguish superficial, remove it." Test impact of dropping superficial. |
| **B1e** | 3.0 | 0.5 | 0.0 | -1.0 | Stronger separation between substantive and marginal — test whether the 3:1 ratio is too forgiving on marginal. |

**Sensitivity output:** for each judge-graded dim (direction_improvement, nuance_caught, net_new_ideas), report verdict under B1a/b/c/d/e. If the verdict label differs across variants for a dim, that dim's signal is weight-fragile and the markdown report flags it.

## B-variant 2: Retrospective landing-rate stratification by artifact type

Current (`scripts/arm_study_retrospective.py`): `(landed + 0.5*partial) / total` regardless of artifact source (plan vs refined vs judgment).

Pre-registered alternates:

| Variant | Aggregation | Rationale |
|---------|-------------|-----------|
| **B2a** | Pool all artifact types (current) | Baseline (locked). |
| **B2b** | Stratify: report landing rate per artifact type (plan, refined, judgment) separately; verdict computed only within same artifact type, then majority-vote across types | gemini: "0.5 for partial is defensible; the bigger issue is heterogeneity in what 'landed' means across artifacts." |
| **B2c** | Restrict to single artifact type per study line — use whichever type has the most coverage; abstain on proposals with other artifact types | Most-conservative; loses sample but eliminates artifact-type confound. |

**Sensitivity output:** plan_quality_delta verdict under B2a/b/c. If the verdict label differs, the dim's signal depends on artifact-type pooling and the markdown flags it.

## B-variant 3: Overall verdict composition

Current (`scripts/arm_study_verdict.py:_compose_overall_verdict`): per-dim verdict votes 1:1; mixed-directional if any vote split; insufficient-sample if n < 3.

Pre-registered alternates:

| Variant | Rule | Rationale |
|---------|------|-----------|
| **B3a** | 1:1 votes; any split → mixed-directional (current) | Baseline (locked). |
| **B3b** | Verifier-grounded dims (catch_rate) weighted 2.0; judge-graded dims weighted 1.0; supermajority (≥75% of weighted votes) required for directional | gemini + gpt: "verifier-grounded dims shouldn't count equal to judge-graded; weight by reliability." |
| **B3c** | All dims weighted 1.0; supermajority (≥75%) required for directional; otherwise mixed | gpt: "3-to-1 vote is a clear signal, not a mixed one." Tests less-strict-than-unanimity. |
| **B3d** | Verifier-grounded weight 1.5, ground-truth coverage (miss_rate) weight 1.5, judge-graded weight 1.0; majority (>50% weighted) for directional + no harmful guardrail trip | Hybrid of B3b and B3c. |

**Sensitivity output:** overall verdict under B3a/b/c/d. Most-likely flip surface — different composition rules can swap directional for mixed when individual dim verdicts are mixed.

## Out of scope (not pre-registered)

The following were considered but not added to the locked set:
- **Bayesian posterior verdict thresholds** — would replace bootstrap CI semantics. REDESIGN C explicitly chose percentile bootstrap over Bayesian posterior (D43); revisiting in B would defeat the lock-mechanism's purpose.
- **Issue-discoverer single-model variants** — REDESIGN B's ensemble already runs Sonnet + GPT + Gemini. Logged union/intersection/majority are the relevant sensitivity signals (already in the verdict markdown). No additional B variant needed.
- **Per-proposal weighting (e.g. weight by total claims)** — would re-introduce the verbosity bias that REDESIGN C explicitly removed. Inconsistent with locked design.

## Application protocol (post-n=10)

1. Wait for n=10 scored.json files at `stores/arm-study/run-n10-*/`.
2. Verify `arm_study_thresholds.json` SHA256 matches the captured value in run artifacts (using `--expected-thresholds-sha`).
3. For each B variant 1a-e, 2a-c, 3a-d:
   - Apply variant configuration (override module constants or copy thresholds JSON to a variant-specific path).
   - Recompute verdict via `compute_verdict()`.
   - Capture per-dim and overall verdict labels.
4. Emit `stores/arm-study/sensitivity-report-n10.md` with:
   - Header: which baseline variant the study report uses.
   - Per-dim table: verdict under each variant (rows = dims, columns = variants).
   - Flag each dim where the verdict label differs across variants ("weight-fragile", "stratification-fragile", "composition-fragile").
5. Final verdict report includes the baseline + sensitivity table. If any dim is flagged fragile, the verdict explicitly states the fragility.

## Lock confirmation

This document is committed before any n=10 scored.json file lands. Editing this file after n=10 kickoff invalidates the sensitivity report — a new study line must be opened (with a new pre-registration doc) instead of editing this one. The hash of `arm_study_thresholds.json` at n=10 kickoff time (captured in scored.json) is the contract anchor.

## Cross-references

- `tasks/arm-study-redesigns-{refined,challenge}.md` — A REDESIGN spec.
- `tasks/decisions.md` D41/D42/D43 — A REDESIGN decisions.
- `stores/arm-study/verdict-n3-v7-vs-v8-comparison.md` — Step 5 sanity-rerun result demonstrating REDESIGN C methodology.
- `stores/arm-study/metric-fix-{code,design}-review.md` — original cross-model review motivating B variants.
- `stores/arm-study/arm_study_thresholds.json` (path: `config/study/arm_study_thresholds.json`) — locked thresholds, SHA256 captured per-run.
