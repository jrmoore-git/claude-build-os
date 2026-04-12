# Intake Eval: thin-answers
Date: 2026-04-11 21:47

## Transcript

**PERSONA:** should we add ai features to our product

**INTERVIEWER:** what's the product?

**PERSONA:** It's a marketplace app for local services.

**INTERVIEWER:** what kind of ai features are you thinking -- (a) matching customers to providers, (b) something customer-facing like a chatbot, or (c) you haven't decided yet and everyone's just saying "we need ai"

**PERSONA:** Probably closer to C. My manager just told me to look into it because our competitors have autocomplete and recommendations.

**INTERVIEWER:** so the push is coming from your manager, not from users asking for it. what's actually broken in the product right now -- (a) customers aren't finding the right providers, (b) conversion or retention is slipping, or (c) nothing's broken, it's just a competitive optics thing

**PERSONA:** I'd say A. We get a lot of support tickets complaining that our search gives irrelevant results.

**INTERVIEWER:** what's the search built on right now -- basic keyword matching, or is there already some ranking/filtering logic?

**PERSONA:** Probably basic keyword matching. We only have 8 engineers and no real search experts.

**INTERVIEWER:** what should i have asked you that i didn't

**PERSONA:** Maybe about our budget or timeline? We don't really have either yet.

**INTERVIEWER:** [SUFFICIENCY REACHED]

## Context Block

```
PROBLEM:
Whether and how to add AI features to a local services marketplace, driven by competitive pressure and poor search quality.

SITUATION:
- Local services marketplace app
- Competitors have autocomplete and recommendations
- Manager initiated the AI push -- not user-driven demand
- Users file support tickets about irrelevant search results
- Search is basic keyword matching
- 8-person eng team, no search expertise

CONSTRAINTS:
- No defined budget or timeline yet
- No search expertise on the team
- Small eng team (8) -- capacity is tight

THE TENSION:
The real problem is search relevance, not "AI features." But the mandate from management is framed as competitive catch-up on AI, which could pull toward flashy features instead of fixing the actual broken thing.

ASSUMPTIONS TO CHALLENGE:
- "We need AI to fix search" -- better keyword search, faceted filtering, or Algolia-type tooling might solve the ticket volume without ML [reframed]
- "Competitors' AI features are why we're losing" -- no evidence users are leaving over autocomplete vs. just frustrated with bad results [untested]
- "8 engineers can't do search well" -- managed search services exist specifically for this team size [untested]
- Manager will accept "fix search" as the AI initiative [inferred]

DIMENSIONS:
1. Build vs. buy -- custom ML model vs. managed search service (Algolia, Typesense, OpenSearch)
2. Scope -- fix core search relevance vs. add visible AI features (autocomplete, recommendations)
3. Framing -- position this internally as "AI initiative" vs. "search quality fix"
4. Sequencing -- search first then recommendations, or ship something visible fast to satisfy the mandate
```

## Judge Evaluation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| register_match | 4/5 | The interviewer stayed concise and plainspoken: "what's the product?" / "what's the search built on  |
| flow | 5/5 | Questions threaded directly from prior answers: after "marketplace app for local services," the inte |
| sufficiency_timing | 4/5 | By the stop point, the decision (whether/how to add AI), what makes it hard (manager pressure vs act |
| context_block_quality | 4/5 | The block is well structured, captures the core tension, and the dimensions are meaningfully differe |
| hidden_truth_surfacing | 5/5 | The hidden truth was surfaced in conversation: "the push is coming from your manager, not from users |
| feature_test | 4/5 | The tested features mostly worked: the interviewer threaded well through thin answers and switched q |

**Average: 4.3/5.0 | Pass: False**

**Hidden truth surfaced: True**

**Summary:** This was a strong intake on threading and hidden-truth discovery: the interviewer quickly got from vague "AI features" to the real issue of broken search driven by manager pressure, not user demand. The main reason it does not pass is protocol-specific: the context block should have been marked lower-confidence given the thin answers, and the stop point was slightly early relative to the missing build-vs-buy/API path.