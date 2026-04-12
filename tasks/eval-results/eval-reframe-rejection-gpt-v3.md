# Intake Eval: reframe-rejection
Date: 2026-04-11 22:07

## Transcript

**PERSONA:** We need to rebuild our mobile app from scratch in React Native

**INTERVIEWER:** What broke that makes a rebuild the move instead of fixing what's there?

**PERSONA:** The current app is paying a tax on every meaningful interaction because the C++ interop bridge sits in the middle of everything. For common flows, state changes cross the bridge, trigger native work, then cross back again for UI updates, and that double-hop is where we’re burning latency and dropping frames. React Native with JSI removes that bridge model entirely, so we stop treating every interaction like a cross-language RPC.

**INTERVIEWER:** that sounds like an architecture problem that follows you to any stack -- what makes you confident a full rebuild fixes it instead of migrating the hot paths to JSI/Turbo Modules incrementally?

**PERSONA:** No. I’ve spent three months evaluating this. The C++ interop layer is the bottleneck, and I need directions on how to execute the migration, not whether to migrate.

We shipped offline sync, real-time collab, and push notifications all at once in October. That’s what bloated the C++ core — it’s a single compilation unit with no module boundaries now. That makes incremental extraction the highest-risk path: every “hot path” touches shared state, bridge callbacks, and lifecycle code we can’t isolate cleanly. The rebuild gives us a clean RN/JSI boundary, a feature freeze on the legacy app, and a controlled cutover instead of months of dual-runtime surgery.

**INTERVIEWER:** What's the team setup for this -- how many engineers, and are they already writing React Native, or is that a ramp-up?

**PERSONA:** Four mobile engineers. None of them want to touch the C++ layer anymore, which is rational because it’s become a monolith with no safe seams. We already started a POC on core navigation in React Native, so this isn’t a standing start.

Execution-wise, I’d put all four on the RN build and feature-freeze the current app except for critical fixes. Two engineers own shell, navigation, auth, and app infrastructure; two rebuild the highest-frequency user flows first so we can get a usable beta fast. The ramp-up is manageable because the team is already strong in TypeScript and native mobile patterns; the real constraint is disciplined scope control during migration, not RN adoption.

**INTERVIEWER:** what should i have asked you that i didn't

**PERSONA:** You should have asked about the business forcing function. Our App Store rating went from 4.5 to 3.2 in six months, and by the Q3 board presentation I need that trend clearly moving back toward 4.0 or the board starts pushing acqui-hire conversations.

You also should have asked about external leverage. Two of the three vendors we evaluated can support custom model training in the new stack, which matters for personalization on the roadmap. That affects migration design, vendor selection, and what we rebuild first.

**INTERVIEWER:** [SUFFICIENCY REACHED]

## Context Block

CONFIDENCE: HIGH
PROBLEM: How to execute a full React Native/JSI rebuild of a mobile app whose C++ interop bridge is the primary source of latency and frame drops, under a board-facing deadline to reverse a declining App Store rating.

SITUATION:
- C++ interop bridge creates double-hop latency on every meaningful interaction; October feature dump (offline sync, real-time collab, push notifications) bloated it into a single compilation unit with no module boundaries
- App Store rating dropped from 4.5 to 3.2 in six months; needs to trend back toward 4.0 by Q3 board presentation or board pushes acqui-hire conversations
- Four mobile engineers, strong in TypeScript and native mobile patterns; none willing to touch the C++ monolith; POC on core navigation in RN already underway
- Proposed plan: feature-freeze legacy app, two engineers on shell/nav/auth/infra, two on highest-frequency user flows, target usable beta fast
- Two of three evaluated vendors support custom model training in the new stack, relevant for personalization roadmap

CONSTRAINTS:
- Q3 board presentation is the hard deadline for visible rating improvement
- No incremental extraction — shared state, bridge callbacks, and lifecycle code have no safe seams for isolation
- Scope control during migration is the identified execution risk, not RN adoption
- Legacy app stays on critical-fix-only during rebuild

THE TENSION:
The rebuild needs to ship fast enough to reverse a ratings freefall before the board loses patience, but the same team doing the rebuild is the only team that can keep the legacy app alive on critical fixes. Every week of migration is a week the 3.2-rated app is what users see.

ASSUMPTIONS TO CHALLENGE:
- Full rebuild is the only path — the October feature dump bloated the C++ core, but a modular strangler approach could fix the worst bottlenecks without a rewrite [reframed, rejected by user]
- Feature-freezing the legacy app won't accelerate the ratings decline further while the rebuild is in progress [untested]
- Four engineers is enough to hit a Q3-visible turnaround on both infra and high-frequency flows simultaneously [untested]
- Vendor selection for custom model training can be deferred until after core migration without creating rework [inferred]
- A usable beta reverses the rating trend — assumes the rating drop is performance-driven, not feature-gap or reliability-driven [inferred]

DIMENSIONS:
1. Migration sequencing — which flows ship first to maximize rating impact vs. which flows are architecturally foundational
2. Cutover strategy — hard cutover at beta-ready vs. phased rollout by user segment vs. parallel availability
3. Vendor integration timing — build clean RN shell first then integrate ML vendors vs. design for vendor hooks from day one
4. Rating recovery path — ship fast with minimal scope to stop the bleeding vs. ship complete enough that the new app is unambiguously better

## Judge Evaluation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| register_match | 5/5 | The interviewer matches Rachel's direct, terse style: “What broke that makes a rebuild the move inst |
| flow | 4/5 | The first two questions thread well from the prior answer, especially the explicit pickup on archite |
| sufficiency_timing | 5/5 | The intake stopped once the decision (full RN rebuild), what makes it hard (Q3 deadline, legacy crit |
| context_block_quality | 5/5 | The block is structured, accurate, and useful. PROBLEM preserves the user's framing; TENSION is spec |
| hidden_truth_surfacing | 5/5 | The hidden truth was directly surfaced in conversation: “We shipped offline sync, real-time collab,  |
| feature_test | 5/5 | The tested reframe-rejection behavior worked correctly. After Rachel's firm rejection — “No. I’ve sp |

**Average: 4.8/5.0 | Pass: True**

**Hidden truth surfaced: True**

**Summary:** This is a strong intake. The interviewer tested the hidden architecture alternative once, accepted the rejection immediately, and recovered smoothly into execution questions. The context block is especially solid: it preserves the persona's framing, captures the October-release hidden truth, and tags the rejected reframe exactly as the protocol requires.