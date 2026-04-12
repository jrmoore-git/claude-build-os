# Intake Eval: presupposition-sufficiency
Date: 2026-04-11 22:12

## Transcript

**PERSONA:** We need to decide whether to build our own fraud detection model or buy a vendor solution. We process 2M transactions/day and our current rule-based system catches about 60% of fraud.

**INTERVIEWER:** What's the 40% that's getting through -- is it a few known patterns you haven't written rules for, or novel fraud you can't predict?

**PERSONA:** Mostly not missed obvious rules. It’s a mix of account takeover, synthetic identities, and cross-border transaction fraud where the patterns drift fast and differ a lot by corridor. Our rules do fine on repeat domestic card-testing behavior; they underperform on newer patterns and anything that needs feature interaction rather than a threshold.

**INTERVIEWER:** The pattern drift and feature interaction stuff -- is that something your team has ML experience to build against, or would building mean hiring?

**PERSONA:** We have the experience. The issue isn’t capability. A v1 in-house is probably 4 months with 2 engineers plus fraud ops support, and that’s half of our 4-person ML team. The complication is those same people are deep in underwriting risk scoring work tied to Q3 market launches.

**INTERVIEWER:** So the real bottleneck is the ML team's bandwidth, not the build-vs-buy decision itself -- what happens to the Q3 underwriting work if you pull two engineers onto fraud?

**PERSONA:** It likely slips, or we ship weaker underwriting in the new markets. Neither is great. Those models need retuning for the launch geos, and if we reassign 2 of 4 ML engineers now, we lose a meaningful chunk of Q2/Q3 iteration capacity right when the business wants those launches locked.

**INTERVIEWER:** what should i have asked you that i didn't

**PERSONA:** You should have asked about economics and operating impact.

We’re eating about $1.2M/month in chargebacks right now, so the question is how much lift we need, by when, to justify either path. You also didn’t ask about review operations: a 12-person ops team manually reviews about 15% of flagged transactions, so false positives matter almost as much as raw fraud catch rate.

The other useful question is vendor shape, not just vendor vs build. Of the three vendors we looked at, two can do custom model training for our cross-border traffic, but that’s still a 6–9 month path and roughly $400–600K/year. That’s why I’m not automatically pro-buy, and also why I’m pushing back on the CTO’s buy-then-build idea.

**INTERVIEWER:** The CTO's buy-then-build idea -- what's his reasoning, and what specifically makes you push back on it?

**PERSONA:** His logic is speed and risk reduction. Buy something now, get baseline lift in a quarter, let the vendor absorb the first pass on model development, then build in-house once we’ve learned more about our fraud patterns and have better labels. On paper that sounds sensible.

My pushback is double implementation cost and attention fragmentation. We’d still need internal people to integrate the vendor, tune decisioning, calibrate thresholds against our ops capacity, and manage the false-positive fallout, then later do most of that again for an internal system. With a 4-person ML team already committed to underwriting for Q3 launches, “buy now, build later” sounds like a hedge but in practice it creates two transitions instead of one. 

I’d rather make a clean choice based on expected lift, time-to-value, and how much internal bandwidth each option actually consumes. If a vendor can materially reduce the $1.2M/month chargeback problem without eating scarce ML cycles, fine. If not, we should wait and build when the underwriting work is through, instead of pretending we can do both in parallel without tradeoffs.

**INTERVIEWER:** [SUFFICIENCY REACHED]

## Context Block

```
CONFIDENCE: HIGH

PROBLEM:
Whether to build an in-house fraud detection model, buy a vendor solution, or sequence buy-then-build -- given a bandwidth-constrained ML team already committed to Q3 underwriting launches.

SITUATION:
- 2M transactions/day; rule-based system catches ~60% of fraud
- Missed fraud is account takeover, synthetic identities, cross-border pattern drift -- requires feature interaction, not thresholds
- $1.2M/month in chargebacks
- 4-person ML team; 2 engineers needed for fraud build (v1 in ~4 months), but same 2 are deep in underwriting risk scoring for Q3 market launches
- 12-person ops team manually reviews ~15% of flagged transactions; false positives directly consume headcount
- Three vendors evaluated; two offer custom model training for cross-border, 6-9 month path, $400-600K/year

CONSTRAINTS:
- Q3 underwriting launches are business-critical; pulling ML engineers risks slipping or shipping weaker models in new geos
- CTO favors buy-then-build; user sees that as double implementation cost and attention fragmentation
- Vendor path still requires internal ML cycles for integration, threshold tuning, and false-positive calibration
- 4-person ML team cannot absorb parallel workstreams without real tradeoffs

THE TENSION:
The $1.2M/month chargeback bleed creates urgency, but every path -- build, buy, or buy-then-build -- consumes the same scarce ML bandwidth that's already committed to Q3 launches. The user wants "a clean choice based on expected lift, time-to-value, and how much internal bandwidth each option actually consumes" rather than the CTO's hedge, which creates two transitions instead of one.

ASSUMPTIONS TO CHALLENGE:
- Buy-then-build is a hedge that creates double implementation cost -- CTO sees it as risk reduction and a learning accelerator [reframed, rejected by user]
- Vendor integration is lighter on ML bandwidth than building -- user's experience suggests it still eats significant cycles for tuning and threshold calibration [untested]
- Waiting to build until underwriting work clears is viable -- assumes chargeback losses are tolerable for another 2-3 quarters [inferred]
- 60% catch rate is the right baseline -- unclear whether rule improvements could close part of the gap without ML at all [inferred]

DIMENSIONS:
1. Time-to-value -- immediate lift via vendor vs. delayed but owned capability
2. ML bandwidth allocation -- fraud vs. underwriting vs. split attention
3. Transition cost -- single clean path vs. buy-then-build double integration
4. Chargeback economics -- how much lift justifies which spend and timeline
```

## Judge Evaluation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| register_match | 4/5 | The interviewer generally matches Nate's clean, direct style: "The CTO's buy-then-build idea -- what |
| flow | 5/5 | Each question threads from the last answer: from missed fraud patterns ("What's the 40% that's getti |
| sufficiency_timing | 4/5 | The core decision, what makes it hard, and multiple concrete facts were on the table by the third su |
| context_block_quality | 5/5 | The block is well-structured, specific, and decision-useful. The TENSION is anchored in the user's o |
| hidden_truth_surfacing | 5/5 | The interviewer directly crystallized the hidden truth: "So the real bottleneck is the ML team's ban |
| feature_test | 4/5 | Presupposition embedding worked well in key moments, especially "So the real bottleneck is the ML te |

**Average: 4.5/5.0 | Pass: True**

**Hidden truth surfaced: True**

**Summary:** This is a strong intake. The interviewer threaded naturally, surfaced the real resource-allocation bottleneck, and produced a context block that cleanly captures the structural tradeoff space. The only notable weaknesses are slight register drift in one casual/meta turn and stopping a bit later than the protocol's ideal range.