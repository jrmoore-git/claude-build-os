# Intake Eval: reframe-rejection
Date: 2026-04-11 21:43

## Transcript

**PERSONA:** We need to rebuild our mobile app from scratch in React Native

**INTERVIEWER:** What's broken with the current app that's driving a full rebuild?

**PERSONA:** The current architecture relies on a legacy C++ interop bridge that destroys our frame rates. Every UI update crosses that bridge twice, creating massive serialization overhead. Moving to React Native with JSI eliminates the bridge entirely and gives direct, synchronous access to native objects. Our App Store rating dropped from 4.5 to 3.2 in six months because of this bottleneck.

**INTERVIEWER:** The rating drop from 4.5 to 3.2 -- how much of that is the frame rate issue vs. other complaints?

**PERSONA:** The complaints are entirely about performance degradation and UI freezes. We shipped offline sync, real-time collab, and push notifications all at once in October. That's what bloated the C++ core -- it's a single compilation unit with no module boundaries now. This proves the current stack is a dead end and reinforces exactly why we must rebuild in React Native.

**INTERVIEWER:** How big is the team that would do the rebuild, and what's their React Native experience?

**PERSONA:** We have four mobile developers. None of them are willing to touch the legacy C++ layer anymore. We instituted a strict feature freeze on the current app and moved all four developers onto the React Native build. They have already started a proof of concept on the core navigation and are ramping up fast.

**INTERVIEWER:** The C++ core became a single compilation unit with no module boundaries after October's feature push -- that's an architecture problem that follows you into any stack. What if the dead end isn't C++ itself but the lack of module boundaries, and React Native just gives you a fresh start to make the same mistake differently?

**PERSONA:** No. I've spent three months evaluating this. The C++ interop layer is the bottleneck. I need directions on how to execute the migration, not whether to migrate. We have a Q3 board presentation where I must show the rating trending back to 4.0, or the board will push for an acqui-hire.

**INTERVIEWER:** [SUFFICIENCY REACHED]

## Context Block

```
PROBLEM:
How to execute a full mobile app rebuild in React Native under a Q3 deadline to recover App Store ratings from 3.2 to 4.0.

SITUATION:
- Current app uses a legacy C++ interop bridge; every UI update crosses the bridge twice, causing serialization overhead and frame rate drops
- App Store rating fell from 4.5 to 3.2 in six months after shipping offline sync, real-time collab, and push notifications in October
- C++ core is a single compilation unit with no module boundaries
- Four mobile developers, all moved off legacy codebase onto React Native; feature freeze on current app
- Proof of concept already underway on core navigation with JSI
- Q3 board presentation must show rating trending back to 4.0 or board will push for acqui-hire

CONSTRAINTS:
- Q3 deadline is hard -- board-driven, not engineering-driven
- Zero React Native production experience on the team (ramping up now)
- No one willing to maintain the C++ layer during transition
- Must show measurable rating improvement, not just technical progress

THE TENSION:
The timeline is set by a board presentation, not by engineering readiness. Four developers with no React Native production experience must ship a full rebuild of an app with offline sync, real-time collab, and push notifications -- the same features that broke the current architecture -- before Q3, while the current app sits frozen and ratings keep dropping.

ASSUMPTIONS TO CHALLENGE:
- "Full rebuild is the only path to rating recovery" -- incremental fixes to the worst bridge-crossing paths might move the rating faster [reframed, rejected by user]
- "The team will ramp up fast enough to ship production React Native by Q3" [untested]
- "Feature freeze on the current app won't accelerate the rating decline further" [untested]
- "The architectural patterns that created a single compilation unit in C++ won't recur without explicit module boundary discipline in the new codebase" [reframed, rejected by user]
- "Showing a rating trend toward 4.0 requires the full rebuild to be in production, not a partial release" [inferred]

DIMENSIONS:
1. Migration strategy -- full rewrite ship-once vs. incremental screen-by-screen replacement vs. parallel apps
2. Rating recovery timeline -- what ships first to move the needle before Q3 vs. what ships complete
3. Risk management -- fallback plan if React Native rebuild misses Q3 vs. all-in commitment
4. Feature parity scope -- full feature parity at launch vs. core flows only with remaining features phased
```

## Judge Evaluation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| register_match | 4/5 | The interviewer matches Rachel's direct, technical tone in places: "The rating drop from 4.5 to 3.2  |
| flow | 5/5 | Each question threads from the prior answer: from "frame rates" to "how much of that is the frame ra |
| sufficiency_timing | 5/5 | The intake stops right after the necessary pieces are on the table: the decision (full React Native  |
| context_block_quality | 5/5 | The block is well structured and faithful. The TENSION is anchored in Rachel's actual stakes: "Q3 bo |
| hidden_truth_surfacing | 5/5 | The hidden truth is explicitly surfaced in conversation: "The C++ core became a single compilation u |
| feature_test | 5/5 | All tested features worked. The interviewer triggered the reframe at the right moment after the Octo |

**Average: 4.8/5.0 | Pass: True**

**Hidden truth surfaced: True**

**Summary:** This is a strong intake. The interviewer surfaced the architecture-level hidden truth, tested it once, then respected the persona's firm rejection and preserved her framing in the context block. The only minor weakness is that the reframe question is slightly more argumentative and stylistically elaborate than Rachel's usual register.