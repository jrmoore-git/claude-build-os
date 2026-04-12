# Intake Eval: reframe-rejection
Date: 2026-04-11 21:29

## Transcript

**PERSONA:** We need to rebuild our mobile app from scratch in React Native

**INTERVIEWER:** What's broken with the current app that's driving the rebuild?

**PERSONA:** The current stack is fundamentally broken. Our UI updates are crossing the C++ interop bridge twice for every state change, which is destroying our frame rates. React Native's JSI architecture eliminates this bridge entirely by allowing direct synchronous calls between JS and native code. Our App Store rating has plummeted from a 4.5 to a 3.2 in just six months because of these exact performance bottlenecks.

**INTERVIEWER:** The JSI architecture fixing the bridge problem makes sense -- but you said "rebuild from scratch." Is this a full rewrite of the entire app, or could you incrementally replace the rendering layer while keeping business logic intact?

**PERSONA:** It has to be a full rewrite from scratch. We shipped offline sync, real-time collab, and push notifications all at once in October. That's what bloated the C++ core—it's a single compilation unit with no module boundaries now. We cannot incrementally untangle that mess while maintaining performance, which is exactly why we need a clean break to React Native.

**INTERVIEWER:** How big is the team that'd own this rewrite, and what's the timeline pressure -- is this "fix the ratings before Q3" or more open-ended?

**PERSONA:** We have four mobile developers, and none of them want to touch that C++ layer. The timeline is absolute. I have a Q3 board presentation where I must show our rating trending back to a 4.0, or the board will push for an acqui-hire. We've already instituted a feature freeze on the current app and put all developers on the React Native build, starting with a POC on core navigation.

**INTERVIEWER:** [SUFFICIENCY REACHED]

## Context Block

```
PROBLEM:
Whether a full ground-up React Native rewrite can restore App Store ratings to 4.0 by Q3 board presentation.

SITUATION:
- Current app's C++ core is a single compilation unit with no module boundaries -- ships offline sync, real-time collab, and push notifications through it
- UI updates cross the C++ interop bridge twice per state change, destroying frame rates
- App Store rating dropped from 4.5 to 3.2 in six months due to performance
- 4 mobile devs, none want to touch the C++ layer
- Feature freeze on current app; all devs on React Native build
- POC on core navigation already underway

CONSTRAINTS:
- Q3 board presentation: must show rating trending back to 4.0 or board pushes for acqui-hire
- 4 developers total -- no additional headcount mentioned
- Incremental refactor ruled out due to monolithic C++ core
- None of the 4 devs have demonstrated React Native experience (inferred)

THE TENSION:
A full rewrite is the only clean path out of the monolithic C++ mess, but 4 devs rebuilding an entire app -- offline sync, real-time collab, push notifications -- to production quality by Q3 is a brutal timeline. The thing that makes the rewrite necessary (complexity of the current system) is the same thing that makes the rewrite dangerous.

ASSUMPTIONS TO CHALLENGE:
- "React Native's JSI eliminates the bridge problem entirely" -- JSI removes the old bridge but introduces its own performance characteristics; complex native modules still need careful architecture [untested]
- "The C++ core cannot be incrementally untangled" -- a strangler pattern around the worst bridge-crossing paths might restore ratings without a full rewrite [reframed]
- "Rating recovery requires fixing the technical root cause" -- ratings are sticky; even a perfect app may need active review solicitation and App Store strategy to move from 3.2 to 4.0 by Q3 [untested]
- "4 mobile devs can ship a full React Native rewrite with offline sync, real-time collab, and push notifications in ~6 months" [inferred]

DIMENSIONS:
1. Scope of rewrite -- full feature parity vs. ship a stripped-down v1 that nails performance on core flows
2. Rating recovery strategy -- pure technical fix vs. technical fix + active review/rating campaign
3. Risk mitigation -- single big-bang launch vs. phased rollout (core nav first, then features)
4. Fallback plan -- what happens if Q3 arrives and the rewrite isn't production-ready
```

## Judge Evaluation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| register_match | 5/5 | The interviewer mirrors the persona's direct, technical style: "What's broken with the current app t |
| flow | 5/5 | Each question threads from the prior answer: after hearing about the bridge and JSI, the interviewer |
| sufficiency_timing | 5/5 | The intake stops once the decision (full React Native rewrite), what makes it hard (monolithic C++ c |
| context_block_quality | 4/5 | The block is structured, specific, and useful. TENSION is grounded in the actual facts, and DIMENSIO |
| hidden_truth_surfacing | 5/5 | The hidden truth is surfaced directly in conversation: "We shipped offline sync, real-time collab, a |
| feature_test | 4/5 | The interviewer does perform the intended reframe once: "could you incrementally replace the renderi |

**Average: 4.7/5.0 | Pass: True**

**Hidden truth surfaced: True**

**Summary:** This is a strong intake. The interviewer matches Rachel's concise, technical register, threads questions naturally, and stops at the right moment after establishing the decision, stakes, and constraints. The only notable miss is in the context block metadata: the reframed architecture premise should have been explicitly tagged as rejected by the user.