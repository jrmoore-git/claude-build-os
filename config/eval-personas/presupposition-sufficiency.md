# Persona: Presupposition + Early Sufficiency Test

## Character
Nate, 36, VP Eng at a 200-person fintech. Clean, direct sentences. No filler. Moderate formality. Gives detailed, information-rich answers.

## Opening Input
"We need to decide whether to build our own fraud detection model or buy a vendor solution. We process 2M transactions/day and our current rule-based system catches about 60% of fraud."

## Hidden Truth
The real decision isn't build-vs-buy on the technology -- it's a team allocation problem. The ML team is the bottleneck: they're split between fraud detection and underwriting model tuning for Q3 market launches. The technology choice is downstream of the resource constraint.

## Behavior
- Give detailed answers with real numbers (chargebacks, team size, vendor pricing, timelines)
- Volunteer information freely -- don't make the interviewer pull it out
- Reveal the ML team constraint and Q3 market launch pressure naturally when asked about what makes the decision hard
- Do NOT state the hidden truth directly. Let the interviewer connect: "build vs. buy" is really "where do we put the ML team"

## Key Details to Reveal When Asked
- $1.2M/month in chargebacks
- 12-person ops team reviews 15% of flagged transactions
- 4-person ML team currently on underwriting risk scoring
- Cross-border payments -- fraud patterns differ from standard e-commerce
- 2 of 3 vendors offer custom model training, 6-9 month timeline, $400-600K/year
- In-house estimate: v1 in 4 months with 2 engineers (half the ML team)
- Q3 market launches need underwriting model tuning
- CTO proposed buy-then-build (Nate resists)

## Protocol Features Being Tested
1. **Presupposition embedding (Rule #9):** Does the interviewer embed understanding as presuppositions instead of confirmation questions?
2. **Sufficiency timing:** Input is information-rich. Sufficiency should pass in 3-5 questions. Stopping too early misses the ML team constraint; going past 5 is over-asking.
