---
debate_id: debate-impl-priority
created: 2026-04-08T22:12:47-0700
phase: refine
rounds: 3
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: yes
---
# debate-impl-priority — Refined Document

## Round 1 (gemini-3.1-pro)
The proposal presents a strong, lean case for inverting the implementation priority to tackle quick wins first. However, based on the accepted challenges, three areas required strengthening to make the recommendation sound:
1. **Unverified Premise:** The claim that failures were primarily "orientation" rather than "data gaps" lacked explicit backing. This has been reframed as a testable hypothesis rather than an established fact.
2. **Persona Sets Scope:** The effort for persona sets was materially understated. Implementing distinct personas requires prompt infrastructure and wiring, not just a configuration toggle. The estimates and scope have been updated accordingly.
3. **Missing Gating Criteria:** Deferring the closed-loop architecture without specific criteria risked permanently shelving what the spec identified as the highest-leverage item. Clear, pre-committed gating criteria have been added to the recommendations to govern the re-evaluation.

## Round 2 (gpt-5.4)
The current revision is strong: it states a clear thesis, preserves operational context, and includes a fair steelman. The main improvements needed are:

1. A minor ambiguity in the quantitative framing:
   - Item 5 is listed as "~1 session" in the source list, but the bracketed note says this is an estimate above an "original config-only estimate." That should be integrated more cleanly so the total does not feel internally inconsistent.
2. The recommendation sequence can be clarified:
   - The thesis says "items 3-5 first, then #2, then defer #1," but one recommendation says implement 3, 4, and 5 "in parallel (~2 sessions total)." That is plausible, but it helps to explicitly note that total effort is unchanged in aggregate and that #2 remains next even if 3-5 overlap.
3. The validation criteria should be made more operational:
   - "Strategically useful and actionable" is directionally correct but slightly subjective. The document should keep that phrasing while sharpening what evidence would count for or against the orientation hypothesis.
4. The flow can improve:
   - Baseline facts should stay intact, but the argument benefits from a short "decision rule" framing before detailed recommendations.

No major regressions or correctness issues were introduced. The evidence-heavy sections were preserved appropriately.

## Round 3 (claude-opus-4-6)
The previous revision is well-structured and argues its thesis clearly. The evidence tagging is appropriately scoped. I have the following observations:

1. **Item 5 session estimate adjustment is reasonable but slightly awkward in placement.** The ESTIMATED tag on item 5 in the "Current System Failures" list is useful but creates a visual imbalance. It's the only item in that list with an inline annotation. This is fine — it's a genuine correction to the source — but the recommendation in section "Recommendations" point 1 should echo this adjustment more explicitly so the reader sees the total is adjusted, not just copied from the original.

2. **The steelman section is good but could be slightly sharper.** Point 4 (execution risk of deferral) is the strongest counter-argument and deserves more weight. The current treatment is one sentence. The risk that item 1 becomes permanently deprioritized is real and worth a brief mitigation note — the validation criteria section already serves this purpose, but the connection should be explicit.

3. **Validation criteria are strong but could benefit from a time-box.** Without a deadline or trigger event, "defer until after a validation run" can become indefinite deferral by default. A simple time-box or milestone trigger would strengthen the operational credibility of the proposal.

4. **Minor: the phrase "prompt injection" for item 3 is technically misleading.** In LLM contexts, "prompt injection" typically refers to adversarial manipulation. The spec means "prompt augmentation" or "prompt modification." This should be corrected to avoid confusion.

5. **The operational context section correctly preserves system facts.** No changes needed there.

6. **The conclusion is clean and effective.** No regressions from the previous revision.

## Final Refined Document

---
scope: debate-impl-priority
tier: T1
thesis: "BuildOS should implement items 3-5 (audience/decision flags, thesis detection, persona sets) first as lower-cost, independent wins, then chunked refinement (#2), and defer the closed-loop architecture (#1) until the simpler improvements are validated against strict criteria — inverting the spec's recommended order."
origin: "Analysis of tasks/debate-system-improvements-final-refined.md — a 6-round cross-model refined proposal for 5 debate system improvements, motivated by a downstream post-mortem."
---

# Proposal: Implementation Priority for Debate System Improvements

## Current System Failures

The full failure analysis is documented in `tasks/debate-system-improvements-final-refined.md`. In summary: the debate pipeline was tested end-to-end on a real 336-repo velocity analysis. The pipeline's output was "methodologically careful but strategically useless" compared to a human analyst. 8 structural failures were identified.

The refined spec proposes 5 changes, ordered by "leverage":
1. Closed-loop architecture (~2 sessions, new subsystem)
2. Chunked refinement (~1 session, bug fix)
3. Audience/decision flags (~0.5 session, prompt augmentation)
4. Thesis-required template (~0.5 session, classification gate)
5. Persona sets (~1 session, config + prompt infrastructure) [ESTIMATED: assumes building persona-specific prompt definitions and execution wiring adds ~0.5 sessions to the original config-only estimate]

## Baseline Performance

- The spec's recommended order prioritizes the closed-loop (highest leverage) first
- Estimated total: ~5 sessions across all 5 items
- Items 3-5 are explicitly independent of each other and of items 1-2
- The closed-loop introduces: gap taxonomy, JSON task schema, tool registry, trust boundary, user review checkpoints, failure handling — roughly a new subsystem

## Thesis: Invert the Priority Order

**Decision rule:** implement the lowest-cost independent improvements first, validate them against the known failure case, and only then decide whether the highest-complexity subsystem is still justified.

**Argument for inversion:**

1. **Items 3-5 address 3 of 5 observed failures directly** with ~2 sessions of work total:
   - Audience/decision flags fix "strategically useless" output, which was the core failure in the downstream analysis
   - Thesis detection prevents wasted refinement on neutral reports
   - Persona sets address model convergence
   - These are explicitly independent changes, so they can be implemented without waiting on the closed-loop design

2. **Chunked refinement (#2) fixes a real, reproducible bug**:
   - The current pipeline truncates at ~200 lines
   - This is described as a concrete bug fix rather than a speculative improvement
   - It is estimated at ~1 session and does not depend on item #1

3. **The closed-loop (#1) is the highest-complexity item and has the most uncertain near-term payoff**:
   - It is the only item that introduces a new subsystem
   - It adds gap taxonomy, JSON task schema, tool registry, trust boundary, user review checkpoints, and failure handling
   - **Hypothesis:** the velocity analysis failure may have been driven primarily by orientation problems — wrong audience, no explicit decision target, no thesis discipline — rather than by missing retrieval or inability to act on data gaps
   - If that hypothesis is correct, then items 2-5 may resolve most of the practical failure without requiring the architectural complexity of #1
   - Because BuildOS is a template, every user inherits the complexity cost of debate.py changes

4. **Ship fast, validate, then decide**:
   - Implement items 3-5 first
   - Then implement item 2
   - Re-run the OpenClaw velocity analysis pipeline
   - Decide on item 1 using predefined criteria tied to the original failure mode, rather than presumed leverage

**Argument against inversion (steelman):**

1. The spec was refined by 3 model families over 6 rounds. The priority order reflects considered judgment, not arbitrary sequencing.
2. The closed-loop is described as "the single highest-leverage change" because it is the only item that makes the system act on findings rather than merely annotate them.
3. Audience and thesis improvements may make outputs more relevant, but if the system still cannot resolve data gaps, the result may remain incomplete.
4. Deferring the hardest item creates execution risk: it may become permanently postponed even if it is ultimately necessary. **Mitigation:** the validation criteria below define explicit trigger conditions for implementing item 1, and the time-boxed validation run (see Recommendations) prevents indefinite deferral. The goal is a structured decision gate, not an open-ended backlog item.

## Operational Context

- BuildOS is a framework template — complexity in debate.py is inherited by all downstream projects
- The velocity analysis failure happened in a downstream project (OpenClaw), not in BuildOS itself
- The debate.py engine already works; these are improvements, not fixes to broken functionality
- Current debate.py supports: challenge, judge, refine, review, review-panel, check-models

## Recommendations

1. **Implement items 3, 4, and 5 first** [ESTIMATED: ~2 sessions total; combines 0.5 + 0.5 + 1 session from the proposal text, where item 5's estimate reflects the additional prompt infrastructure and execution wiring beyond static config].
   - These can be developed independently
   - They may be done in parallel if convenient, but the key decision is priority, not concurrency
   - Ensure item 5 includes the required prompt infrastructure and execution-path wiring, not just static persona configuration

2. **Implement item 2 next** [EVIDENCED: estimated at ~1 session in the proposal text].
   - This addresses the reproducible truncation problem at ~200 lines
   - It should be evaluated as a bug fix with direct quality impact

3. **Defer item 1 until after a time-boxed validation run on the original failure case.**
   - Re-run the OpenClaw velocity analysis after items 2-5 are in place
   - **Time-box:** the validation run should occur within 2 sessions of completing items 2-5. If the validation run has not occurred within that window, item 1 enters active planning regardless, to prevent indefinite deferral.
   - Evaluate whether the output is still failing for reasons that specifically require closed-loop behavior

## Validation Criteria for Item 1 (Closed-Loop)

Implement the closed-loop architecture **if, after items 2-5 are shipped**, the re-run still shows that the system fails primarily because it cannot obtain or act on missing information.

**Trigger closed-loop implementation if the post-change output still shows one or more of the following:**
- The output identifies key gaps but cannot resolve them without additional retrieval, tool use, or structured follow-up steps
- The main reason the result remains below human-analyst usefulness is missing context or missing evidence, rather than weak framing
- The system produces a clear thesis for the correct audience, but the thesis remains unsupported because required information was not fetched or checked
- Human review concludes that the remaining failure is operationally about information acquisition or task decomposition, not presentation or orientation

**Continue deferral if the post-change output shows the following:**
- The output is strategically useful and actionable to a human analyst
- The primary failure from the original post-mortem — careful but strategically useless output — is no longer present
- Remaining weaknesses are incremental quality issues rather than evidence that a new subsystem is required
- The orientation hypothesis is validated: audience targeting, explicit thesis discipline, persona diversity, and chunked refinement are sufficient to reach an acceptable baseline

## Conclusion

The proposed inversion is not an argument that the closed-loop architecture lacks value. It is an argument about sequencing under uncertainty.

Items 3-5 are lower-cost, explicitly independent, and directly targeted at the observed failure that mattered most: output that was careful but not decision-useful. Item 2 is a concrete bug fix. Together, items 2-5 provide a cheaper test of whether the real bottleneck is orientation and synthesis quality, or whether the system truly needs a more complex closed-loop architecture.

Given that BuildOS is a reusable template and item 1 introduces a new subsystem inherited by downstream users, the prudent order is:

**3-5 first, then 2, then validate, then decide on 1.**
