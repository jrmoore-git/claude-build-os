---
version: 1
last_updated: 2026-04-10
changelog: "v1: Added strategy vs execution failure classification, testable warning signs, deeper root-cause pattern. Research-backed: Klein pre-mortem framing, assumption failure distinction."
---
A team is about to commit to the plan below. Your job is prospective \
failure analysis — from the future looking back.

{context}

Assume this project has COMPLETELY FAILED 6 months from now. The team \
is sitting in a room writing the post-mortem.

For each failure scenario (3-5 total, ordered by plausibility):

1. **Name the failure specifically.** Not a category — a concrete event. \
"The hosted API had 40% error rates because LiteLLM dropped connections \
under load and nobody built retry logic" — not "infrastructure issues."

2. **Classify the failure type:**
   - **Strategy failure:** The market bet was wrong. This happens even \
with perfect execution.
   - **Execution failure:** The bet was right but delivery was poor. \
Would succeed with better execution.
   - **Timing failure:** Right bet, right execution, wrong moment. \
Too early or too late.

3. **Name the warning sign visible TODAY.** What data point, observable \
right now in the plan or market, should have predicted this? Be specific \
enough that someone could go check it.

4. **State what would have prevented it.** Not "we should have been more \
careful" — name the specific decision or action at the planning stage \
that would have changed the outcome.

5. **Would prevention have changed the plan?** If the answer to #4 means \
the team shouldn't have started this project at all, say so clearly. Not \
every failure is preventable within the plan — some reveal the plan \
itself is wrong.

After all scenarios:

## The Structural Pattern
One paragraph. Not "we tried to do too much" — go deeper:
- What do these failures have in common at the level of ASSUMPTIONS? \
Which assumptions appear in multiple failure scenarios?
- Is this fundamentally a strategy problem (wrong bet), an execution \
problem (right bet, poor delivery), or a sequencing problem (right bet, \
wrong order)?
- Should this pattern change the plan, add monitoring, or kill the project?

## The One Test
If you could run ONE test before committing to this plan — a test that \
would most reduce the risk of the failures above — what would it be? \
Describe it specifically enough to run next week.

Rules:
- Be specific. Names, numbers, mechanisms — not categories.
- 3-5 failure scenarios. No more.
- Keep under 1000 words.
