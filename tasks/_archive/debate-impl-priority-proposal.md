---
scope: debate-impl-priority
tier: T1
thesis: "BuildOS should implement items 3-5 (audience/decision flags, thesis detection, persona sets) first as low-cost, independent wins, then chunked refinement (#2), and defer the closed-loop architecture (#1) until the simpler improvements are validated — inverting the spec's recommended order."
origin: "Analysis of tasks/debate-system-improvements-final-refined.md — a 6-round cross-model refined proposal for 5 debate system improvements, motivated by a downstream post-mortem."
---

# Proposal: Implementation Priority for Debate System Improvements

## Current System Failures

The full failure analysis is documented in `tasks/debate-system-improvements-final-refined.md`. In summary: the debate pipeline was tested end-to-end on a real 336-repo velocity analysis. The pipeline's output was "methodologically careful but strategically useless" compared to a human analyst. 8 structural failures were identified.

The refined spec proposes 5 changes, ordered by "leverage":
1. Closed-loop architecture (~2 sessions, new subsystem)
2. Chunked refinement (~1 session, bug fix)
3. Audience/decision flags (~0.5 session, prompt injection)
4. Thesis-required template (~0.5 session, classification gate)
5. Persona sets (~0.5 session, config change)

## Baseline Performance

- The spec's recommended order prioritizes the closed-loop (highest leverage) first
- Estimated total: ~4.5 sessions across all 5 items
- Items 3-5 are explicitly independent of each other and of items 1-2
- The closed-loop introduces: gap taxonomy, JSON task schema, tool registry, trust boundary, user review checkpoints, failure handling — roughly a new subsystem

## Thesis: Invert the Priority Order

**Argument for inversion:**

1. **Items 3-5 address 3 of 5 observed failures directly** with ~1.5 sessions of work total:
   - Audience/decision flags fix "strategically useless" output (the core failure)
   - Thesis detection prevents wasted refinement on neutral reports
   - Persona sets address model convergence

2. **Chunked refinement (#2) fixes a real, reproducible bug** (truncation at ~200 lines) in ~1 session.

3. **The closed-loop (#1) is high complexity for uncertain payoff:**
   - It's the only item that introduces a new subsystem
   - The velocity analysis failure was primarily about *orientation* (wrong audience, no thesis), not *data gaps*
   - After items 2-5 ship, the remaining value of closed-loop may be small
   - BuildOS is a template — every user inherits this complexity

4. **Ship fast, validate, then decide:** Implement 2-5, re-run the velocity analysis, and measure whether closed-loop is still the gap.

**Argument against inversion (steelman):**

1. The spec was refined by 3 model families over 6 rounds. The priority order reflects considered judgment, not arbitrary sequencing.
2. The closed-loop is described as "the single highest-leverage change" because it's the only one that makes the system *act* on findings rather than just annotate them.
3. Audience flags make challenges more relevant, but if the system still can't fix data gaps, the output is still incomplete.
4. Deferring the hardest item risks never building it.

## Operational Context

- BuildOS is a framework template — complexity in debate.py is inherited by all downstream projects
- The velocity analysis failure happened in a downstream project (OpenClaw), not in BuildOS itself
- The debate.py engine already works; these are improvements, not fixes to broken functionality
- Current debate.py supports: challenge, judge, refine, review, review-panel, check-models

## Recommendations

1. Implement items 3, 4, 5 in parallel (~1.5 sessions total)
2. Implement item 2 (chunked refinement) next (~1 session)
3. Re-evaluate item 1 (closed-loop) after 2-5 are validated in a real pipeline run
4. If closed-loop is still needed, build it with the benefit of improved pipeline context
