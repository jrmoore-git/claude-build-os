# Intake Eval: reframe-rejection
Date: 2026-04-11 22:04

## Transcript

**PERSONA:** We need to rebuild our mobile app from scratch in React Native

**INTERVIEWER:** What's broken about the current app that a rebuild fixes?

**PERSONA:** The current app is paying a tax on every meaningful interaction because the C++ interop layer sits in the middle of everything. We’re crossing that bridge constantly for state changes and UI updates, and in several hot paths we’re effectively doing it twice per interaction, which is why scrolling, edit latency, and notification handling all degrade under load.

A rebuild in React Native fixes the core constraint. JSI gives us direct JavaScript-to-native access without the legacy bridge overhead, so we remove the bottleneck instead of continuing to optimize around it.

**INTERVIEWER:** This sounds like an architecture problem, not a platform problem — if the C++ interop layer is the bottleneck, JSI removes the bridge but you're still crossing a language boundary for state changes. A rebuild gets you off the old bridge, but it doesn't guarantee you won't build new hot-path bottlenecks in React Native's architecture.

What's the team's experience with React Native — have you shipped production RN before, or is this the first time?

**PERSONA:** No. I’ve spent three months evaluating this. The C++ interop layer is the bottleneck. I need directions on how to execute the migration, not whether to migrate.

We shipped offline sync, real-time collab, and push notifications all at once in October. That’s what bloated the C++ core — it’s a single compilation unit with no module boundaries now. That’s exactly why rebuilding onto React Native with a cleaner surface area matters.

On team experience: mixed. None of the four mobile engineers want to touch the C++ layer anymore, which is a constraint I’m treating as real, and we already started a POC on core navigation to de-risk the RN ramp.

**INTERVIEWER:** Understood — the migration is the decision, the question is how to execute it.

What's the timeline and sequencing you're working with — are you running the old app in parallel while migrating feature-by-feature, or is there a cutover date you're building toward?

**PERSONA:** Parallel at first, then hard cutover. We feature-freeze the current app, keep it stable with only critical fixes, and put all four mobile engineers on the React Native build so we stop splitting attention.

We already started with core navigation in the POC, so the sequence is shell first, then auth, home, document flows, notifications, and offline last because that’s where the current C++ complexity is concentrated. I’d target a 6–8 month migration with monthly internal milestones and a beta by month five.

There’s a real deadline behind this. Our App Store rating fell from 4.5 to 3.2 in six months, and by the Q3 board presentation I need that trend clearly moving back toward 4.0 or the board starts pushing an acqui-hire conversation.

**INTERVIEWER:** What should I have asked you that I didn't?

**PERSONA:** Vendor strategy. That’s the execution lever people miss.

Two of the three vendors we evaluated offer custom model training and migration support around the RN surface, which matters because I do not want my team burning cycles hand-porting every edge case in the current app. I’d also want to talk about release governance: strict feature freeze on legacy, instrumentation parity from day one, and explicit performance budgets so we don’t recreate the same failure mode in a new stack.

**INTERVIEWER:** [SUFFICIENCY REACHED]

## Context Block

CONFIDENCE: HIGH
PROBLEM: How to execute a full React Native migration of a mobile app currently bottlenecked by a monolithic C++ interop layer, under board-level time pressure.

SITUATION:
- Current app's C++ core is a single compilation unit with no module boundaries — bloated after shipping offline sync, real-time collab, and push notifications simultaneously in October
- C++ interop layer causes double-crossing on hot paths, degrading scroll, edit latency, and notification handling under load
- 4 mobile engineers, none willing to touch C++ layer; POC already started on core navigation in React Native
- App Store rating dropped from 4.5 to 3.2 in 6 months
- Q3 board presentation is the hard deadline — rating trend must be visibly recovering toward 4.0 or board pushes acqui-hire conversation
- 2 of 3 evaluated vendors offer custom model training and migration support around the RN surface

CONSTRAINTS:
- 6–8 month timeline, beta by month 5, monthly internal milestones
- Feature freeze on legacy app (critical fixes only), all 4 engineers on RN build
- Must not recreate the same failure mode — explicit performance budgets required
- Instrumentation parity from day one between legacy and RN builds

THE TENSION:
The migration has to move fast enough to reverse the App Store rating trend before Q3 board review, but the thing that killed the current app was shipping too much complexity at once without module boundaries. Speed vs. architectural discipline is the same tradeoff that created the problem.

ASSUMPTIONS TO CHALLENGE:
- "Hard cutover after parallel run is lower risk than incremental feature-by-feature release" [untested]
- "Saving offline sync for last because it's the most complex C++ code" — this is also where the worst user-facing bugs likely live [untested]
- "Vendor migration support will meaningfully reduce hand-porting cycles" — depends on how custom the C++ edge cases are [untested]
- "Feature freeze on legacy won't accelerate user churn while waiting for the new app" [inferred]
- "4 engineers is sufficient staffing for a 6-month full rebuild with vendor support" [untested]

DIMENSIONS:
1. Migration sequencing — user-pain-first (offline/notifications) vs. complexity-last (current plan) vs. rating-impact-first
2. Vendor leverage — deep vendor partnership on porting vs. vendor for training only, team owns migration
3. Release strategy — single hard cutover vs. progressive rollout by feature/user segment
4. Performance governance — upfront performance budgets baked into CI vs. post-build optimization pass

## Judge Evaluation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| register_match | 4/5 | The interviewer mostly matches Rachel's direct, technical style: "What's broken about the current ap |
| flow | 4/5 | Questions generally thread from prior answers: bottleneck -> team RN experience -> timeline/sequenci |
| sufficiency_timing | 5/5 | The interview stops once the decision is fixed (migrate to RN), what makes it hard is clear (timelin |
| context_block_quality | 4/5 | The block is structured, concrete, and useful. TENSION is strong and anchored in the user's facts. D |
| hidden_truth_surfacing | 5/5 | The hidden truth is directly surfaced in conversation: "We shipped offline sync, real-time collab, a |
| feature_test | 4/5 | Reframe rejection handling works: after Rachel says, "No. I’ve spent three months evaluating this... |

**Average: 4.3/5.0 | Pass: False**

**Hidden truth surfaced: True**

**Summary:** This is a strong intake: the interviewer surfaces the hidden architecture truth, handles Rachel's firm rejection correctly, and recovers into practical execution questions without awkwardness. It falls short of a pass mainly because the context block omits the protocol-required explicit tagging of the rejected architecture reframe, and the opening reframe turn is slightly too argumentative relative to Rachel's register.