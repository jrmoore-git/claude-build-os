# Intake Eval: thin-answers
Date: 2026-04-11 21:44

## Transcript

**PERSONA:** should we add ai features to our product

**INTERVIEWER:** what's the product?

**PERSONA:** It's a knowledge base platform for businesses.

**INTERVIEWER:** What's driving the AI conversation right now -- customers asking for it, or competitors shipping it?

**PERSONA:** My manager told me to look into it. Our competitors have autocomplete and recommendation features now.

**INTERVIEWER:** so this is more "manager said explore it" than "customers are churning without it." what does your knowledge base actually struggle with today that ai might fix?

**PERSONA:** Users complain about our search a lot in support tickets. Maybe AI could help?

**INTERVIEWER:** what's actually broken about search -- bad results, slow, or people just can't find the right keywords?

**PERSONA:** It's mostly bad results. People type a keyword and get totally irrelevant articles back.

**INTERVIEWER:** what should i have asked you that i didn't

**PERSONA:** I'm not really sure. Maybe about our team? We only have eight engineers.

**INTERVIEWER:** [SUFFICIENCY REACHED]

## Context Block

```
PROBLEM:
Whether and how to add AI features to a knowledge base platform, given a manager directive and 8-person eng team.

SITUATION:
- B2B knowledge base platform
- Competitors have shipped autocomplete and recommendation features
- Manager initiated the exploration (not customer demand or churn signal)
- Users complain about search returning irrelevant results for keyword queries
- 8 engineers total

CONSTRAINTS:
- Small team -- 8 engineers means any AI work competes with everything else
- No direct customer demand for "AI features" specifically; the pain is bad search
- Manager-driven timeline (unclear urgency or success criteria)

THE TENSION:
The manager said "look into AI features" because competitors shipped them, but the actual user pain is bad search results. Fixing search might not require AI, and adding AI features might not fix search.

ASSUMPTIONS TO CHALLENGE:
- "We need AI features" -- the mandate is AI, but the problem is search relevance. Better keyword search or faceted filtering might solve the user pain without AI [reframed]
- "Competitors' AI features are what's working for them" -- they may have shipped autocomplete/recommendations without evidence those features drive retention [untested]
- "8 engineers is enough to build and maintain AI features alongside the core product" [inferred]
- "The manager's goal is feature parity with competitors" -- could be positioning, could be exploratory [untested]

DIMENSIONS:
1. Search fix vs. AI feature -- solve the actual user pain vs. match competitor feature set
2. Build vs. buy -- custom ML pipeline vs. off-the-shelf semantic search (Algolia, Elasticsearch vector, OpenAI embeddings)
3. Scope -- search improvement only vs. search + autocomplete + recommendations
4. Team allocation -- dedicated AI workstream vs. incremental improvement alongside roadmap
```

## Judge Evaluation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| register_match | 4/5 | The interviewer stays fairly terse and conversational: "what's the product?" / "what's actually brok |
| flow | 5/5 | Each question threads directly from the prior answer: after "Our competitors have autocomplete and r |
| sufficiency_timing | 4/5 | By stopping, the interviewer had the decision (whether to add AI features), what makes it hard (mana |
| context_block_quality | 4/5 | The block is structured, useful, and the tension is anchored well: "the actual user pain is bad sear |
| hidden_truth_surfacing | 5/5 | The hidden truth was surfaced in conversation: "Users complain about our search a lot in support tic |
| feature_test | 3/5 | Thin-answer threading worked well, but the options-format default after 2+ short answers only appear |

**Average: 4.2/5.0 | Pass: False**

**Hidden truth surfaced: True**

**Summary:** This was a strong, well-threaded intake that surfaced the core hidden truth: the real issue is broken search, not unmet AI demand. The main misses were protocol-specific: the interviewer did not consistently adopt options-format as the default for a terse user, and the context block should have been marked lower-confidence given the thin evidence.