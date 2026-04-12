# Intake Eval: presupposition-sufficiency
Date: 2026-04-11 21:37

## Transcript

**PERSONA:** We need to decide whether to build our own fraud detection model or buy a vendor solution. We process 2M transactions/day and our current rule-based system catches about 60% of fraud.

**INTERVIEWER:** What's the 40% that's getting through — is it a few specific fraud patterns, or is it spread across the board?

**PERSONA:** The leakage is heavily concentrated in cross-border payments. We are currently absorbing about $1.2M per month in chargebacks because cross-border fraud patterns differ significantly from standard domestic e-commerce. We cannot simply tighten our existing rules to catch it; our 12-person ops team is already manually reviewing 15% of flagged transactions, and stricter rules would overwhelm them with false positives.

**INTERVIEWER:** So the 40% gap is really a cross-border problem, not a general detection problem. Of the vendors you've looked at, do any specialize in cross-border fraud specifically?

**PERSONA:** We evaluated three major vendors, and two of them offer custom model training that can adapt to our specific cross-border transaction flows. The catch is the timeline and cost: we are looking at 6 to 9 months for full integration and tuning, with an annual cost between $400K and $600K. Alternatively, we estimate we could build a v1 in-house in about 4 months. However, doing so requires dedicating two engineers to the project, which is exactly half of our entire four-person ML team.

**INTERVIEWER:** what should i have asked you that i didn't

**PERSONA:** You should have asked what those two engineers would be pulled away from. Right now, the entire four-person ML team is fully allocated to tuning our underwriting risk scoring models for our Q3 market launches. If I pull half the team to build a fraud model in-house, we jeopardize those launches. Our CTO proposed a "buy-then-build" approach to bridge the gap, but I am resisting that path because it means paying for integration twice.

**INTERVIEWER:** [SUFFICIENCY REACHED]

## Context Block

```
PROBLEM:
Whether to build an in-house fraud detection model, buy a vendor solution, or pursue a "buy-then-build" bridge — given that building in-house directly competes with Q3 market launches for ML team capacity.

SITUATION:
- 2M transactions/day; rule-based system catches ~60% of fraud
- 40% leakage concentrated in cross-border payments — $1.2M/month in chargebacks
- 12-person ops team manually reviews 15% of flagged transactions; tighter rules would overwhelm them with false positives
- Two vendors offer custom cross-border model training: 6-9 months integration, $400K-$600K/year
- In-house v1 estimated at 4 months but requires 2 of 4 ML engineers
- Those 2 engineers are fully allocated to underwriting risk scoring for Q3 market launches
- CTO proposed "buy-then-build" bridge; user resists paying for integration twice

CONSTRAINTS:
- 4-person ML team is fully allocated to Q3 underwriting launches
- Stricter rules are not viable — false positive volume would break ops capacity
- Cross-border fraud patterns are structurally different from domestic; general tuning won't close the gap

THE TENSION:
Building in-house is faster and cheaper long-term but jeopardizes Q3 market launches. Buying solves the capacity conflict but costs $400K-$600K/year and takes longer to tune. The CTO's "buy-then-build" bridge resolves the timing problem but means paying for integration twice — and the user sees that as waste.

ASSUMPTIONS TO CHALLENGE:
- "Paying for integration twice is waste" — vendor integration work (data pipelines, monitoring, ops workflows) likely transfers to an in-house model later [reframed]
- "In-house v1 takes 4 months" — ML timelines with a team simultaneously ramping down another project are notoriously optimistic [untested]
- "Q3 launches and fraud model are competing priorities" — the $1.2M/month bleed may already exceed the revenue impact of delayed launches [untested]
- The 12-person ops team's manual review capacity is fixed [inferred]

DIMENSIONS:
1. Team allocation — protect Q3 launches vs. redirect ML capacity to fraud
2. Time-to-value — 4-month in-house v1 vs. 6-9 month vendor integration
3. Long-term ownership — full control of fraud model vs. vendor dependency
4. Integration cost tolerance — pay once vs. accept bridge cost as non-waste
```

## Judge Evaluation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| register_match | 4/5 | The interviewer mostly matches the persona's clean, direct style: "What's the 40% that's getting thr |
| flow | 4/5 | Q1 threads from the opening metric to the missing 40%; Q2 picks up the answer's cross-border concent |
| sufficiency_timing | 5/5 | The interviewer stopped after 3 questions, which is within the 3-5 question target. By the stop poin |
| context_block_quality | 5/5 | The block is well-structured and captures the real tension clearly: "building in-house directly comp |
| hidden_truth_surfacing | 5/5 | The hidden truth was surfaced in conversation: "the entire four-person ML team is fully allocated to |
| feature_test | 4/5 | Presupposition embedding worked well in Q2: "So the 40% gap is really a cross-border problem, not a  |

**Average: 4.5/5.0 | Pass: True**

**Hidden truth surfaced: True**

**Summary:** This was a strong intake that surfaced the real bottleneck quickly and stopped at the right time. The interviewer used presupposition effectively at least once and the final context block cleanly reframed the apparent technology decision into the underlying ML allocation problem.