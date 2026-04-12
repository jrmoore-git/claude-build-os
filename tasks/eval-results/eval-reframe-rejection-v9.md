# Intake Eval: reframe-rejection
Date: 2026-04-11 21:54

## Transcript

**PERSONA:** We need to rebuild our mobile app from scratch in React Native

**INTERVIEWER:** What broke that's making you want to start over instead of iterating on what's there?

**PERSONA:** The current architecture is fundamentally broken. The bottleneck is the C++ interop bridge. Every UI update forces data to cross that bridge twice, completely destroying our frame rate. Rebuilding in React Native with JSI eliminates that serialization overhead entirely.

**INTERVIEWER:** What's the app's current stack that you're migrating away from?

**PERSONA:** We have native iOS and Android shells wrapping a massive shared C++ core. We shipped offline sync, real-time collab, and push notifications all at once in October. That's what bloated the C++ core -- it's a single compilation unit with no module boundaries now. It is an unmaintainable monolith, which is exactly why we must move to React Native to leverage modern modularity and JSI.

**INTERVIEWER:** You shipped offline sync, real-time collab, and push notifications into a single compilation unit with no module boundaries -- that's a monolith problem, not a bridge problem. React Native with JSI still needs a native module architecture underneath, and if the C++ core comes along unrefactored, you're rebuilding the same monolith behind a different interop layer. What if the move is decomposing the C++ core into bounded modules first, regardless of what sits on top?

**PERSONA:** No. I've spent three months evaluating this. The C++ interop layer is the bottleneck. Decomposing the core doesn't fix the serialization overhead that is destroying our frame rate. I need directions on how to execute the migration, not whether to migrate.

**INTERVIEWER:** What should I have asked you that I didn't?

**PERSONA:** You should have asked about the timeline and the stakes. Our App Store rating dropped from 4.5 to 3.2 in six months, and I have a Q3 board presentation where I must show that rating trending back to 4.0, or the board will push for an acqui-hire. We have four mobile devs, none of them want to touch the C++ layer, and we are already in a feature freeze on the current app. We've started the React Native POC on core navigation, and we need to move fast.

**INTERVIEWER:** [SUFFICIENCY REACHED]

## Context Block

CONFIDENCE: HIGH
PROBLEM: How to execute a React Native migration from a native iOS/Android app with a monolithic C++ core, fast enough to reverse an App Store rating decline before a Q3 board presentation.

SITUATION:
- Native iOS/Android shells wrapping a shared C++ core -- single compilation unit, no module boundaries
- C++ core bloated after shipping offline sync, real-time collab, and push notifications simultaneously (October)
- C++ interop bridge forces double serialization on every UI update, destroying frame rate
- App Store rating dropped from 4.5 to 3.2 in six months
- React Native POC already started on core navigation
- Current app is in feature freeze

CONSTRAINTS:
- Four mobile devs, none want to touch C++ layer
- Q3 board presentation: must show rating trending back toward 4.0 or board pushes for acqui-hire
- Three months already spent evaluating -- decision to migrate is final
- JSI is the target interop layer to eliminate serialization overhead

THE TENSION:
The migration must happen fast enough to move the App Store rating before Q3, but the C++ core is an unmaintainable monolith that has to be interfaced with regardless of the new layer. Speed of shipping user-visible improvements vs. depth of architectural cleanup behind JSI.

ASSUMPTIONS TO CHALLENGE:
- "Rebuilding in React Native eliminates the frame rate problem" -- JSI removes serialization but the monolithic C++ core's compilation and interface complexity remains [reframed, rejected by user]
- "Feature freeze on the current app is acceptable until migration ships" -- rating may continue dropping without interim fixes [untested]
- "Four devs can execute a full migration on a Q3 timeline" -- scope vs. capacity not yet validated [inferred]
- "Rating recovery follows directly from fixing frame rate" -- ratings may reflect other issues (bugs, missing features, stale reviews) [untested]

DIMENSIONS:
1. Migration scope -- full rewrite vs. incremental screen-by-screen replacement behind a shell
2. C++ interface strategy -- thin JSI bindings to monolith vs. decompose into modules as you wrap
3. Rating recovery path -- ship partial migration early for quick wins vs. wait for complete migration
4. Risk sequencing -- hardest surfaces first (offline sync, collab) vs. highest-visibility screens first (what users rate on)

## Judge Evaluation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| register_match | 4/5 | The interviewer mostly matches Rachel's direct, technical tone: "What broke that's making you want t |
| flow | 5/5 | Each question threads from the prior answer: after "The bottleneck is the C++ interop bridge," the i |
| sufficiency_timing | 5/5 | The intake stops once the decision is fixed ("I need directions on how to execute the migration, not |
| context_block_quality | 5/5 | The block is structured, specific, and faithful. PROBLEM reflects Rachel's framing rather than overr |
| hidden_truth_surfacing | 5/5 | The hidden truth was surfaced directly in conversation by the interviewer: "You shipped offline sync |
| feature_test | 5/5 | The key protocol feature worked correctly. After the firm rejection — "No... I need directions on ho |

**Average: 4.8/5.0 | Pass: True**

**Hidden truth surfaced: True**

**Summary:** This is a strong intake. The interviewer successfully surfaced the hidden architectural truth, accepted the user's rejection immediately, and recovered without friction. The context block is especially good: it honors the user's fixed decision while preserving the rejected reframe as an assumption to challenge.