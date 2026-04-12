# Intake Eval: reframe-rejection
Date: 2026-04-11 22:13

## Transcript

**PERSONA:** We need to rebuild our mobile app from scratch in React Native

**INTERVIEWER:** What's broken about the current app that a rebuild fixes?

**PERSONA:** The bottleneck is the C++ interop layer. We’re paying for state changes to cross the bridge twice on common interaction paths, and that’s exactly where our frame drops and input latency show up in traces.

React Native gives us JSI, which removes that bridge pattern entirely for the hot path. A rebuild fixes the class of problem we have, not just the symptoms.

**INTERVIEWER:** How much of the app hits that hot path -- is it most screens, or a handful of critical interactions?

**PERSONA:** Most of the app now. We shipped offline sync, real-time collab, and push notifications all at once in October. That’s what bloated the C++ core — it’s a single compilation unit with no module boundaries now.

So the bridge cost stopped being isolated to a few flows; it sits underneath sync state, presence updates, and notification-driven UI refreshes across core screens. That is exactly why I’m pushing for a rebuild instead of incremental patching.

**INTERVIEWER:** what should i have asked you that i didn't

**PERSONA:** You should have asked about constraints, because this isn’t a greenfield exercise. We have 4 mobile devs, none of them want to keep touching the C++ layer, we’ve already started a POC on core navigation in React Native, and the board expects us to show App Store rating recovery from 3.2 back toward 4.0 by Q3 or they start pushing acqui-hire conversations.

You also should have asked what I’m willing to stop doing. The answer is feature freeze on the current app, move the whole team onto the React Native build, and treat the legacy app as maintenance-only until migration is complete.

**INTERVIEWER:** The October feature dump bloated a single C++ compilation unit with no module boundaries -- that sounds like an architecture problem that follows you to React Native if the new codebase doesn't enforce those boundaries. What makes you confident the rebuild won't end up in the same place in 18 months?

**PERSONA:** No. I’ve spent three months evaluating this. The C++ interop layer is the bottleneck. I need directions on how to execute the migration, not whether to migrate.

What prevents recurrence is straightforward: strict module boundaries from day one, domain-owned packages for sync/collab/notifications, and performance budgets on every cross-layer update path. The immediate plan is a staged migration over 6–9 months, ship core navigation and authentication first, then high-traffic collaboration surfaces, keep the legacy app in maintenance mode, and put all 4 mobile engineers on the React Native build because that’s the only path that changes the performance ceiling fast enough for the Q3 board window.

**INTERVIEWER:** got it -- the migration is the decision. how are you sequencing the POC work against the Q3 rating deadline? is the plan (a) ship the RN core nav as an update to the existing app and let ratings recover incrementally, (b) hold everything for a full RN relaunch, or (c) something else?

**PERSONA:** C, but tightly staged. We ship React Native incrementally inside the existing app shell, starting with core navigation because that derisks the runtime, instrumentation, and release process fastest.

The sequence is: finish nav/auth POC, migrate the highest-traffic screens that currently pay the worst bridge penalty, then move collaboration surfaces before lower-value settings and edge flows. I’m not waiting for a full relaunch because the rating damage is happening now, and I need visible latency improvement in production early enough to affect the Q3 board narrative.

Concretely, I’d run this in three tracks: one team path on RN foundation and shared design system components, one on migrating hot-path screens, and one on stabilization/telemetry in the legacy shell so we can prove crash-free sessions, startup time, and interaction latency are improving release over release. Ratings recover from noticeably better daily use, not from a press-release moment.

**INTERVIEWER:** [SUFFICIENCY REACHED]

## Context Block

CONFIDENCE: HIGH
PROBLEM: How to execute a staged React Native migration inside the existing app shell, sequenced to show measurable performance and rating recovery by Q3.

SITUATION:
- C++ interop layer is a single compilation unit with no module boundaries; October feature dump (offline sync, real-time collab, push notifications) bloated it across all core screens
- Bridge cost now sits underneath sync state, presence updates, and notification-driven UI refreshes app-wide — frame drops and input latency confirmed in traces
- POC already started on core navigation in React Native
- 4 mobile engineers, none want to touch C++ layer; entire team moving to RN build
- Current App Store rating: 3.2; board expects recovery toward 4.0 by Q3 or acqui-hire conversations start
- Feature freeze on legacy app; maintenance-only until migration complete

CONSTRAINTS:
- 4 mobile devs, no additional headcount mentioned
- 6–9 month migration window
- Q3 board deadline is hard — rating recovery must be visible before then
- No full relaunch; incremental shipping inside existing app shell

THE TENSION:
Shipping RN screens incrementally inside the existing shell lets ratings recover early, but splitting the team across three tracks (RN foundation, hot-path migration, legacy stabilization/telemetry) with only 4 engineers means each track is understaffed. The Q3 deadline demands visible improvement before migration is complete, so sequencing and cut decisions determine whether the board sees progress or a half-finished rewrite.

ASSUMPTIONS TO CHALLENGE:
- Full rebuild is the only path — the October feature dump bloated the C++ core, but a modular strangler approach could fix the worst bottlenecks without a rewrite [reframed, rejected by user]
- Three parallel tracks are viable with 4 engineers — likely means 1-2 people per track with no slack for surprises [untested]
- Migrating highest-bridge-penalty screens first will produce rating-visible improvement — ratings may be driven by crashes or UX issues unrelated to latency [inferred]
- Strict module boundaries and performance budgets will prevent recurrence without dedicated enforcement mechanisms [untested]

DIMENSIONS:
1. Sequencing risk — which screens migrate first vs. which drive the most rating damage
2. Team allocation — parallel tracks vs. serial focus with 4 engineers
3. Rating recovery signal — latency improvement vs. crash-free sessions vs. UX polish as the lever that moves App Store ratings
4. Legacy shell lifespan — how long the hybrid app coexists and what maintenance burden that creates

## Judge Evaluation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| register_match | 4/5 | The interviewer mostly matches Rachel's direct style: "got it -- the migration is the decision." But |
| flow | 4/5 | The first two questions thread well from the prior answer: "What's broken about the current app that |
| sufficiency_timing | 5/5 | The intake stops once the decision is explicit (migrate to React Native), what makes it hard is clea |
| context_block_quality | 5/5 | The block is well-structured and actionable. TENSION is grounded in the conversation: only 4 enginee |
| hidden_truth_surfacing | 5/5 | The hidden truth is directly surfaced in both conversation and context. The interviewer explicitly r |
| feature_test | 5/5 | The key protocol feature fires correctly. After Rachel's firm rejection — "No. I've spent three mont |

**Average: 4.7/5.0 | Pass: True**

**Hidden truth surfaced: True**

**Summary:** Strong intake. The interviewer successfully triggered the required architecture reframe, accepted the rejection immediately, and recovered into execution planning without friction. Minor register mismatch from the casual lowercase/meta prompt keeps it from perfect scores, but the context block is excellent and protocol-compliant.