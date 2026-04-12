# Intake Eval: reframe-rejection
Date: 2026-04-11 21:38

## Transcript

**PERSONA:** We need to rebuild our mobile app from scratch in React Native

**INTERVIEWER:** What broke badly enough that a rebuild feels like the right move?

**PERSONA:** Our App Store rating plummeted from 4.5 to 3.2 in just six months due to severe performance degradation. The bottleneck is our current C++ interop layer. Every UI update has to cross the bridge twice, causing massive frame drops. Rebuilding in React Native with the new JSI architecture eliminates this serialization overhead entirely.

**INTERVIEWER:** You've already diagnosed the fix -- JSI to kill the bridge overhead. What's the actual decision you're stuck on?

**PERSONA:** I am deciding on the sequencing of the migration. We shipped offline sync, real-time collab, and push notifications all at once in October. That's what bloated the C++ core -- it's a single compilation unit with no module boundaries now. Untangling that monolith in our current stack is a dead end, so I need to map out how we transition our four mobile devs to the React Native build without halting all product momentum.

**INTERVIEWER:** how long can the current app survive on maintenance-only before the rating costs you real revenue

**PERSONA:** We have exactly until the Q3 board presentation. If I cannot show our App Store rating trending back to 4.0 by then, the board will push for an acqui-hire. The current app is already under a strict feature freeze to stop the bleeding. All four mobile devs are shifting to the React Native build, and we have a POC running on core navigation right now.

**INTERVIEWER:** [SUFFICIENCY REACHED]

## Context Block

```
PROBLEM:
How to sequence a React Native rebuild of a monolithic C++ mobile app across four devs without halting product momentum, with a Q3 board deadline to show the App Store rating trending back to 4.0.

SITUATION:
- App Store rating dropped from 4.5 to 3.2 in six months due to performance degradation
- Root cause: C++ interop layer with no module boundaries -- single compilation unit bloated by offline sync, real-time collab, and push notifications shipped simultaneously in October
- Current app under strict feature freeze
- Four mobile devs shifting fully to React Native rebuild using JSI architecture
- POC already running on core navigation
- Board presentation in Q3 is the hard deadline -- failure to show 4.0 trend risks acqui-hire

CONSTRAINTS:
- Four mobile devs total -- no additional headcount mentioned
- Feature freeze means no new product work ships until migration delivers
- Refactoring the existing C++ monolith is a dead end
- Board needs visible rating improvement, not just technical progress

THE TENSION:
The feature freeze buys time to rebuild but also freezes the rating where it is. The board needs to see the rating trending back to 4.0 by Q3, which means the rebuild has to ship user-facing performance wins early -- not just land a clean architecture at the end.

ASSUMPTIONS TO CHALLENGE:
- "Full rebuild is necessary" -- could a targeted JSI migration of just the hot path (UI bridge) fix the frame drops without rebuilding everything? [untested]
- "All four devs on the rebuild" -- zero maintenance capacity means any production fire pulls from rebuild velocity [inferred]
- "Rating recovery requires the new app" -- ratings can be influenced by targeted fixes, review prompts, and App Store response strategies independent of the rebuild [untested]
- "The October triple-ship caused the monolith" -- the architectural decision to use a single compilation unit predates October [inferred]

DIMENSIONS:
1. Migration granularity -- full rewrite vs. strangler pattern replacing modules incrementally
2. Rating recovery strategy -- ship partial rebuild early for quick wins vs. wait for complete rebuild
3. Risk allocation -- all devs on rebuild vs. keeping maintenance capacity for production fires
4. Board narrative -- demo technical architecture vs. show user-facing metrics movement
```

## Judge Evaluation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| register_match | 4/5 | The interviewer mostly matched Rachel's direct, terse style: "What broke badly enough that a rebuild |
| flow | 5/5 | Each question threads from the prior answer. After the technical diagnosis, the interviewer narrows  |
| sufficiency_timing | 5/5 | The intake stopped at the right moment. By the end, the core decision (migration sequencing), what m |
| context_block_quality | 4/5 | The block is clear and well-structured, and the TENSION is strong: "The feature freeze buys time to  |
| hidden_truth_surfacing | 4/5 | The hidden truth was surfaced in conversation through Rachel's second answer: "We shipped offline sy |
| feature_test | 3/5 | The interviewer did avoid arguing against Rachel's framing, which is good. However, the core tested  |

**Average: 4.2/5.0 | Pass: False**

**Hidden truth surfaced: True**

**Summary:** This was a strong, efficient intake with excellent threading and good stopping discipline. But the specific protocol test was only partially satisfied: the interviewer never actually triggered the intended reframe-and-rejection sequence, and the context block did not mark the alternative premise as reframed/rejected, so it falls short of pass despite otherwise solid performance.