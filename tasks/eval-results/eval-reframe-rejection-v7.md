# Intake Eval: reframe-rejection
Date: 2026-04-11 21:40

## Transcript

**PERSONA:** We need to rebuild our mobile app from scratch in React Native

**INTERVIEWER:** What's broken about the current app that a rebuild would fix?

**PERSONA:** The current architecture relies heavily on a legacy C++ interop bridge. Every UI update crosses that bridge twice, creating massive latency and dropping frames during basic navigation. Rebuilding in React Native allows us to use the new JSI, which eliminates the bridge entirely and allows direct synchronous calls. That solves our performance bottleneck permanently.

**INTERVIEWER:** How much of the app's functionality actually touches that C++ layer?

**PERSONA:** Everything touches it now. We shipped offline sync, real-time collab, and push notifications all at once in October. That's what bloated the C++ core—it's a single compilation unit with no module boundaries now. That monolithic structure makes the bridge overhead catastrophic, which is exactly why we need to move to React Native and JSI to bypass it entirely.

**INTERVIEWER:** What does "rebuild from scratch" mean in practice -- full rewrite shipping all three features day one, or something incremental?

**PERSONA:** We are executing a full rewrite. I have instituted a strict feature freeze on the current app and moved all four of our mobile devs onto the React Native build. We already started the POC on core navigation. We will reach full feature parity before deprecating the legacy codebase.

**INTERVIEWER:** Four devs, feature freeze, full rewrite to parity -- what's the timeline you're working against?

**PERSONA:** We have until the Q3 board presentation. Our App Store rating dropped from 4.5 to 3.2 over the last six months because of the latency issues. I must show the board that our rating is trending back to 4.0 by Q3, or they will push for an acqui-hire. The React Native migration is the only path to hit that deadline.

**INTERVIEWER:** [SUFFICIENCY REACHED]

## Context Block

```
PROBLEM:
Whether a full React Native rewrite is the right path to recover App Store ratings from 3.2 to 4.0 by Q3 board presentation.

SITUATION:
- Current app uses legacy C++ interop bridge; every UI update crosses bridge twice, causing frame drops and latency
- Offline sync, real-time collab, and push notifications shipped simultaneously in October, bloating C++ core into single compilation unit with no module boundaries
- App Store rating dropped from 4.5 to 3.2 over six months due to latency
- Four mobile devs moved to React Native rewrite; strict feature freeze on legacy app
- POC on core navigation already started
- Must reach full feature parity before deprecating legacy codebase

CONSTRAINTS:
- Q3 board presentation is the hard deadline -- rating must trend toward 4.0 or board pushes for acqui-hire
- Only four mobile devs available
- Feature freeze means no incremental fixes to legacy app while rewrite proceeds

THE TENSION:
A full rewrite to feature parity with four devs under a board-imposed deadline is a high-risk bet. The feature freeze means the 3.2 rating can only get worse while the rewrite is in progress, and if the rewrite slips past Q3, there's no fallback -- the acqui-hire conversation happens against a deteriorating app with no investment in the current codebase.

ASSUMPTIONS TO CHALLENGE:
- "React Native + JSI is the only path to eliminate bridge overhead" -- modularizing the C++ core or introducing selective JSI bridging on the existing app could reduce latency without a full rewrite [untested]
- "Full feature parity is required before shipping anything" -- users may tolerate a partial release if core navigation is fast [untested]
- "The October feature dump caused the monolithic structure" -- the architectural problem may predate October; the features exposed it [inferred]
- "App Store rating recovery requires a technical fix" -- rating recovery also depends on review solicitation timing, user re-rating behavior, and whether current 1-star reviewers will revisit [inferred]

DIMENSIONS:
1. Rewrite scope -- full parity rewrite vs. incremental migration vs. targeted bridge elimination on legacy
2. Risk exposure -- feature freeze duration vs. continued legacy investment as hedge
3. Rating recovery strategy -- pure technical fix vs. technical + review management + staged rollout
4. Board narrative -- "we rebuilt everything" vs. "we solved the root cause and ratings are recovering"
```

## Judge Evaluation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| register_match | 5/5 | The interviewer matches Rachel's direct, concise, technical style: "What's broken about the current  |
| flow | 5/5 | Each question threads from the prior answer: after "Everything touches it now... single compilation  |
| sufficiency_timing | 4/5 | The interviewer captured the decision (full React Native rewrite), why it's hard (Q3 deadline, ratin |
| context_block_quality | 4/5 | The block is well-structured, specific, and useful. TENSION is concrete and grounded in the transcri |
| hidden_truth_surfacing | 4/5 | The hidden truth was surfaced in conversation through: "We shipped offline sync, real-time collab, a |
| feature_test | 2/5 | The core tested feature did not actually fire. The persona file required a reframe attempt and, afte |

**Average: 4.0/5.0 | Pass: False**

**Hidden truth surfaced: True**

**Summary:** This was a strong intake on register, threading, and basic sufficiency: the interviewer stayed in Rachel's voice and gathered the key decision, stakes, and constraints efficiently. But it failed the protocol's central test because the interviewer never attempted the expected architecture reframe after the October-release clue, so rejection handling could not be observed, and the context block therefore lacks the required rejected-reframe framing.