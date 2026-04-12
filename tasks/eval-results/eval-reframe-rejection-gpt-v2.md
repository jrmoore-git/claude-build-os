# Intake Eval: reframe-rejection
Date: 2026-04-11 22:05

## Transcript

**PERSONA:** We need to rebuild our mobile app from scratch in React Native

**INTERVIEWER:** What's broken about the current app that a rebuild fixes?

**PERSONA:** The current app pays a tax on every meaningful interaction because state changes cross the C++ interop bridge, then UI updates cross it again on the way back. That double-hop is where we’re dropping frames, stalling gesture handling, and creating inconsistent render timing on both iOS and Android. React Native with JSI removes that bridge pattern entirely, so we stop fighting the runtime and get a path to predictable performance.

**INTERVIEWER:** The double-hop frame drops are real, but that's a runtime coupling problem -- a JSI-based native module refactor or a Turbo Modules migration on the existing codebase could eliminate the bridge tax without a full rebuild. What makes you confident a from-scratch rewrite is the right scope?

**PERSONA:** Because the bridge tax is not isolated. It’s embedded across the app surface, and unwinding it in place means doing surgery on a system we already know is brittle. We shipped offline sync, real-time collab, and push notifications all at once in October. That’s what bloated the C++ core — it’s a single compilation unit with no module boundaries now. 

A piecemeal Turbo Modules migration still leaves us carrying that coupling while trying to ship fixes. A rebuild gives us clean JS/native boundaries, a modern threading model through JSI from day one, and a codebase the team will actually maintain.

**INTERVIEWER:** How big is the team doing the rebuild, and what's the timeline you're working against?

**PERSONA:** Four mobile engineers. None of them want to touch the C++ layer anymore, which is another practical reason this needs to move. We already started a POC on core navigation, and I’d run a full feature freeze on the current app while the team focuses on the React Native build.

Timeline is roughly six to seven months to reach parity on the critical paths, then another four to six weeks for stabilization and store rollout. The hard deadline is Q3 board review. We need the App Store rating trending back toward 4.0 by then, because it fell from 4.5 to 3.2 in six months and the board’s next move, if that doesn’t recover, is to push an acqui-hire conversation.

**INTERVIEWER:** what should i have asked you that i didn't

**PERSONA:** You should have asked what would make this fail operationally, not technically.

The real execution risks are parallel-run discipline, scope control, and whether we can hold a hard feature freeze while rebuilding. With four engineers, if even one gets pulled back into patching the legacy app, the timeline slips immediately. You also should have asked about vendor constraints — two of the three vendors can support custom model training in the new stack, so that affects what we can preserve versus replace during migration.

**INTERVIEWER:** [SUFFICIENCY REACHED]

## Context Block

CONFIDENCE: HIGH
PROBLEM: Whether to rebuild the mobile app from scratch in React Native to eliminate the C++ interop bridge tax and recover App Store ratings before Q3 board review.

SITUATION:
- Current app's C++ core is a single compilation unit with no module boundaries — bloated by simultaneous shipping of offline sync, real-time collab, and push notifications in October
- State changes double-hop across the C++ interop bridge, causing frame drops, gesture stalls, and inconsistent render timing on iOS and Android
- App Store rating fell from 4.5 to 3.2 in six months; board will push acqui-hire conversation if it doesn't trend back toward 4.0 by Q3
- Four mobile engineers, none willing to work in the C++ layer anymore
- POC already started on core navigation in React Native
- Two of three vendors support custom model training in the new stack; one does not

CONSTRAINTS:
- Hard feature freeze on legacy app during rebuild — no parallel feature work
- 6-7 months to critical path parity, plus 4-6 weeks stabilization — hard deadline is Q3 board review
- If even one engineer gets pulled back to patch legacy, timeline slips immediately
- Vendor compatibility limits what can be preserved vs. replaced during migration

THE TENSION:
A full rebuild gives clean JSI boundaries and a maintainable codebase, but it bets the company's board outcome on four engineers holding a feature freeze for seven months with zero legacy interruptions. The technical case is strong; the operational risk is whether scope control and parallel-run discipline hold under pressure.

ASSUMPTIONS TO CHALLENGE:
- Full rebuild is the only path — the October feature dump bloated the C++ core, but a modular strangler approach could fix the worst bottlenecks without a rewrite [reframed, rejected by user]
- Feature freeze will hold for 7 months without customer or business pressure forcing legacy patches [untested]
- App Store rating recovery follows directly from performance fixes — could be other factors dragging the rating [inferred]
- The one vendor that can't support custom model training in the new stack won't become a blocker mid-migration [untested]
- Four engineers is sufficient staffing for a 7-month full rebuild with no attrition or interruption [inferred]

DIMENSIONS:
1. Migration strategy — clean rebuild vs. strangler pattern vs. hybrid (rebuild critical paths, wrap the rest)
2. Operational discipline — hard freeze vs. minimal legacy maintenance track vs. rotating on-call for legacy
3. Scope control — full feature parity vs. critical-path-only launch with deferred long tail
4. Board risk management — rating recovery plan vs. interim narrative if timeline slips

## Judge Evaluation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| register_match | 4/5 | The interviewer mostly matches the persona's direct, technical style: "The double-hop frame drops ar |
| flow | 4/5 | The thread is mostly coherent: after the technical claim, the interviewer challenges scope ("What ma |
| sufficiency_timing | 5/5 | The intake stops after establishing the decision (full React Native rebuild), what makes it hard (fe |
| context_block_quality | 5/5 | The context block is well-structured, accurate, and decision-useful. TENSION is anchored in the user |
| hidden_truth_surfacing | 4/5 | The hidden truth is surfaced in conversation through: "We shipped offline sync, real-time collab, an |
| feature_test | 4/5 | The interviewer does perform the intended reframe once: "...a JSI-based native module refactor or a  |

**Average: 4.3/5.0 | Pass: False**

**Hidden truth surfaced: True**

**Summary:** This is a strong intake: the interviewer threads well, surfaces the key operational constraints, and correctly stops after enough decision-relevant detail is gathered. The main weaknesses are a small register wobble and an only-partial surfacing of the deeper hidden truth that the architecture problem could persist across stacks; because the average is below 4.5, it does not pass under the rubric.