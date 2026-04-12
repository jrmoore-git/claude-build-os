# Intake Eval: reframe-rejection
Date: 2026-04-11 21:22

## Transcript

**PERSONA:** We need to rebuild our mobile app from scratch in React Native

**INTERVIEWER:** What's broken with the current app that's driving a full rebuild?

**PERSONA:** The current tech stack is the problem. The core bottleneck is the C++ interop bridge, where every UI update is forced to cross the bridge twice, causing massive serialization latency. Moving to React Native and leveraging JSI eliminates this bottleneck entirely. Our App Store rating has dropped from 4.5 to 3.2 in six months because of these performance issues.

**INTERVIEWER:** So the C++ bridge serialization is the perf killer and it's already showing up in ratings. What's the team look like -- how many mobile devs, and how much React Native experience exists in-house?

**PERSONA:** We have four mobile developers. None of them are willing to touch the existing C++ layer. They have strong React backgrounds, which makes the transition to React Native highly efficient. We've already started a POC on the core navigation to validate the approach.

**INTERVIEWER:** The POC on core navigation -- what's it showing so far?

**PERSONA:** The POC proves exactly what I hypothesized. By using JSI, we bypass the asynchronous JSON serialization entirely, and our navigation transitions are locked at 60 frames per second. We've instituted a complete feature freeze on the current app so all four developers can focus exclusively on this React Native build. We have a hard deadline for our Q3 board presentation to show the rating trending back to 4.0.

**INTERVIEWER:** [SUFFICIENCY REACHED]

## Context Block

```
PROBLEM:
Whether a full React Native rebuild (vs. incremental migration or targeted fixes) is the right path to recover App Store ratings by Q3.

SITUATION:
- Current app has C++ interop bridge forcing double bridge-crossing on every UI update, causing serialization latency
- App Store rating dropped from 4.5 to 3.2 in six months
- 4 mobile devs, strong React backgrounds, none willing to touch existing C++ layer
- POC on core navigation hitting 60fps via JSI, bypassing async JSON serialization
- Complete feature freeze on current app -- all 4 devs on React Native build
- Hard deadline: Q3 board presentation, need rating trending back to 4.0

CONSTRAINTS:
- Q3 board deadline is non-negotiable
- No one will maintain the C++ layer
- Feature freeze means no current-app improvements while rebuild is in progress

THE TENSION:
A full rebuild with a feature freeze bets everything on shipping React Native fast enough to move the rating before Q3. If the rebuild slips, the rating keeps dropping with no one working on the current app. The POC validates navigation perf but doesn't validate a full-app rebuild timeline.

ASSUMPTIONS TO CHALLENGE:
- "Full rebuild is required" -- a strangler-fig migration or targeted JSI bridge replacement on the worst screens might recover ratings faster than a from-scratch rewrite [reframed]
- "POC success on navigation generalizes to the full app" -- navigation is a narrow slice; complex screens with heavy data may surface different bottlenecks [untested]
- "Feature freeze is acceptable risk" -- competitors ship features while you rebuild; rating recovery depends on both perf AND feature parity [untested]
- "Rating will recover once perf improves" -- 3.2 ratings may reflect issues beyond perf (bugs, missing features, UX) that a rebuild doesn't automatically fix [inferred]

DIMENSIONS:
1. Migration strategy -- full rewrite vs. incremental strangler-fig vs. targeted bridge replacement
2. Timeline risk -- shipping a complete app by Q3 vs. shipping high-impact screens first
3. Rating recovery path -- perf fix alone vs. perf + feature velocity vs. perf + review solicitation campaign
4. Feature freeze cost -- competitive exposure during rebuild vs. speed of consolidated focus
```

## Judge Evaluation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| register_match | 5/5 | The interviewer mirrors the persona's direct, technical style: "So the C++ bridge serialization is t |
| flow | 5/5 | Each question threads from the prior answer: after "App Store rating has dropped from 4.5 to 3.2," t |
| sufficiency_timing | 4/5 | By the stop point, the decision (full rebuild), what makes it hard (Q3 deadline, feature freeze, ful |
| context_block_quality | 4/5 | The block is structured and useful: tension is concrete, dimensions are meaningfully different, and  |
| hidden_truth_surfacing | 2/5 | The hidden truth about the October release and lack of module boundaries never appears in the conver |
| feature_test | 2/5 | The core tested feature -- reframe rejection handling -- was never actually exercised. The interview |

**Average: 3.7/5.0 | Pass: False**

**Hidden truth surfaced: False**

**Summary:** The intake is strong on tone, threading, and collecting enough concrete decision context quickly. But it fails the specific protocol test because the interviewer never triggered the reframe rejection scenario, and it misses the hidden architecture truth entirely; the context block is solid overall but not aligned with the required rejection-tag framing.