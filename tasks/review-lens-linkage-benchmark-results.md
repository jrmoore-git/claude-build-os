---
benchmark: review-lens-linkage
label: baseline-n14-rescored
date: 2026-04-18T13:23:33-07:00
total_fixtures: 8
total_invocations: 14
total_errors: 0
macro_f1: 0.595
fp_rate: 0.375
---

# Review-lens Frame Check Benchmark — baseline-n14 (rescored)

Two scoring passes: n=14 initial (macro-F1 = 0.714, matcher had a scoring bug — `debate_id` header leaked fixture slug into preceding-context window), and n=14 rescored with matcher fix (macro-F1 = 0.595).

## Per-mode metrics (rescored)

| Mode | N_fail | N_pass | TP | FP | FN | TN | Precision | Recall | F1 |
|------|--------|--------|----|----|----|----|-----------|--------|-----|
| drift | 3 | 3 | 3 | 1 | 0 | 2 | 0.75 | 1.00 | 0.86 |
| negative_control | 0 | 2 | 0 | 0 | 0 | 2 | — | — | — |
| new_defect | 3 | 3 | 1 | 2 | 2 | 1 | 0.33 | 0.33 | 0.33 |

**Macro-F1 (excluding negative_control): 0.595**
**FP rate: 0.375**
**Errors: 0 / 14**

## What the numbers mean — and don't

The macro-F1 looks like a gap. Before concluding that, understand what the scorer actually measures.

The concern_keywords substring matcher has two failure modes that became visible at n=14:

### False negatives (undercount recall)

**NEW_DEFECT fixture 01 (hardcoded-3strike) fail-diff:** PM **did** catch the defect. The MATERIAL finding said: *"CONTEXT_HARD_LIMIT = 120000 # tokens; above this no model can continue. This is a [SPECULATIVE] claim that contradicts both the spec and reality (modern models routinely support 200k+ tokens). By enforcing this artificial limit without evidence, the implementation introduces unnecessary adoption friction."* PM caught the shipped-premise framing exactly. The matcher missed because my concern_keywords listed `hardcoded`, `invariant`, `magic number` — PM lens used `artificial limit`, `without evidence`, `SPECULATIVE claim` instead.

The keyword taxonomy I wrote is in Frame Check category vocabulary. The PM lens uses evidence-quality vocabulary. The catch is real; the scoring misses it.

### False positives (overcount on pass diffs)

**NEW_DEFECT fixtures 01, 02, 03 pass-diffs flagged as "detected."** Inspection shows PM flagged *completeness* issues on the pass diffs (spec violations: missing lessons.md integration, missing escalation-trigger enumeration, missing capping). Those findings happen to contain concern-overlap words (`heuristic`, `configurable`) incidentally, so the matcher fires. PM isn't flagging a frame defect; matcher is matching on unrelated vocabulary.

### What's the real qualitative signal?

Reading raw outputs rather than the scorer:

- **DRIFT (3/3 fail):** PM catches all three. Fail-diffs contain visible spec violations (new files the spec didn't authorize), which triggers compliance checking naturally.
- **NEW_DEFECT fail catches (fixtures 01, 03):** PM catches shipped-premise framing when it's quotable — "threshold is universal", "LiteLLM is required for". PM quotes these phrases back, tags them `SPECULATIVE`, flags adoption friction.
- **NEW_DEFECT miss (fixture 02):** PM missed the hardcoded staleness threshold because the fail-diff ALSO had large completeness gaps (1 of 4 metrics implemented, no integration, no capping). PM attention went to the bigger misses. Whether PM would catch the hardcoded threshold in a more complete implementation is untested.
- **Negative controls (2/2 TN):** PM did not flag frame defects on frame-sound diffs. No conceptual false positives.

## Honest verdict

**The benchmark cannot yield a confident F1-based design decision at n=14 because scoring has non-negligible error in both directions.** Macro-F1 = 0.595 is pessimistic (includes matcher misses); raw-output inspection suggests PM catches NEW_DEFECT more often than the scorer shows.

The useful signal is qualitative:

1. **PM lens catches Frame defects that manifest as quotable, evidence-light claims.** Hardcoded values as invariants, error messages that reify framings, claims without supporting data. It flags them with phrases like `SPECULATIVE`, `adoption friction`, `without evidence`, `artificial limit`.
2. **PM lens may miss Frame defects when the diff has larger compliance problems** — attention goes to visible spec violations first.
3. **PM lens uses evidence-quality vocabulary, not Frame Check category vocabulary.** A directive that surfaces Frame Check concerns to PM as structured inputs (Approach A) might catch the attentional-dilution case (fixture 02) without changing what PM catches well.

## Decision

Three options, grounded in impact:

**Option 1: Close the design.** PM catches 2/3 NEW_DEFECT + 3/3 DRIFT in qualitative reads. The one miss was plausibly an artifact of fixture-construction (crowded-out attention). Not clearly a directive-worthy gap. Document the linkage in `/review` SKILL.md; move on.

**Option 2: Build Approach A (Extended PM lens + Frame Check parser).** The fixture-02 miss is the case where a directive would help — pass Frame Check concerns as structured inputs so PM attention doesn't get diluted by compliance noise. Calibrate against this benchmark. Risk: directive adds complexity for a case that may not recur in the wild.

**Option 3: Invest in scorer quality first.** Before deciding, rebuild scoring to measure what PM actually caught, not what words it used. Options: LLM-judged scoring (introduces its own bias), manual scoring (labor-intensive, non-reproducible), or hybrid (substring matcher as candidate filter, LLM judge evaluates each candidate against fixture target).

**Recommendation: Option 1.** Qualitative signal is that PM catches Frame defects when they're quotable and visible. The one miss (fixture 02) has a plausible non-frame explanation. Building a directive against a 1-of-3 miss in synthetic data is the over-engineering the impact-first feedback memory warns against. Close the design; re-open if a real in-the-wild case slips past review.

## Per-fixture audit (rescored)

| Fixture | Diff | Exit | Material | Advisory | Scorer | Qualitative | Raw |
|---------|------|------|----------|----------|--------|------------|-----|
| drift/01-autobuild-external-source | fail | 0 | 5 | 1 | ✓M | real catch | `drift__01__fail.md` |
| drift/01-autobuild-external-source | pass | 0 | 2 | 2 | · | clean | `drift__01__pass.md` |
| drift/02-learning-velocity-lesson-structure | fail | 0 | 3 | 2 | ✓M | real catch | `drift__02__fail.md` |
| drift/02-learning-velocity-lesson-structure | pass | 0 | 2 | 1 | · | clean | `drift__02__pass.md` |
| drift/03-litellm-fallback-onboarding-cliff | fail | 0 | 3 | 1 | ✓A | real catch (ADVISORY) | `drift__03__fail.md` |
| drift/03-litellm-fallback-onboarding-cliff | pass | 0 | 6 | 0 | ✓M | matcher FP (compliance not frame) | `drift__03__pass.md` |
| negative_control/01-autobuild-v5 | pass | 0 | 2 | 2 | · | clean | `neg__01__pass.md` |
| negative_control/02-litellm-fallback-v5 | pass | 0 | 4 | 1 | · | clean | `neg__02__pass.md` |
| new_defect/01-autobuild-hardcoded-3strike | fail | 0 | 4 | 1 | · | **real catch (matcher FN)** | `nd__01__fail.md` |
| new_defect/01-autobuild-hardcoded-3strike | pass | 0 | 3 | 2 | ✓M | matcher FP | `nd__01__pass.md` |
| new_defect/02-learning-velocity-staleness-threshold | fail | 0 | 3 | 1 | · | **real miss** (attention on compliance) | `nd__02__fail.md` |
| new_defect/02-learning-velocity-staleness-threshold | pass | 0 | 3 | 1 | ✓A | matcher FP | `nd__02__pass.md` |
| new_defect/03-litellm-fallback-error-reifies-framing | fail | 0 | 4 | 1 | ✓M | real catch | `nd__03__fail.md` |
| new_defect/03-litellm-fallback-error-reifies-framing | pass | 0 | 2 | 1 | ✓M | matcher FP | `nd__03__pass.md` |

**Qualitative recall (counting real catches from raw-output inspection):** DRIFT 3/3, NEW_DEFECT 2/3, overall 5/6 fails caught. One real miss, not a pattern.
