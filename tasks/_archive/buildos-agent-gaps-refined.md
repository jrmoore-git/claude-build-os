---
debate_id: buildos-agent-gaps
created: 2026-04-05T20:35:33-0700
phase: refine
rounds: 3
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: yes
---
# buildos-agent-gaps — Refined Document

## Round 1 (gemini-3.1-pro)
The initial proposal provided a valuable starting point by identifying potential documentation gaps, but it accepted Claude's output too credulously. The most significant improvement in this revision is shifting from a flat "10-point remediation list" to a structured triage system. By categorizing the claims into verified backlogs, already-covered features, strategic design questions, and a strict quarantine list, we protect users from the active harm of hallucinated documentation. 

I have added an explicit verification gate and a prioritization rubric to replace the unhelpful "F" grading. Gap 1 has been reclassified as already covered, Gap 4 and 5 have been split to isolate verified falsehoods (like `TeammateIdle`), and Gap 6 has been properly framed as an architectural trade-off rather than a strict omission.

## Round 2 (gpt-5.4)
The revision is materially better than a flat backlog. It correctly introduces a verification gate, separates verified work from hallucination risk, and avoids turning unverified vendor claims into documentation tasks.

Remaining issues:
1. The document ends at triage and does not clearly state the resulting action plan, ownership model, or decision flow after categorization.
2. Some categories mix “document later if verified” with “probably low priority” without stating how that affects sequencing.
3. The “Verified Backlog” label is slightly misleading because those items are not yet verified; they are better described as “candidate backlog items pending verification.”
4. The proposal would benefit from a short process section describing how a claim moves from quarantine/candidate status into actual documentation work.
5. The strategic design section is correct, but the consequence should be made explicit: no documentation change should be made for Gap 6 until product/design decides whether BuildOS wants same-platform orchestration or cross-model independence.

No major regressions were introduced. The factual distinctions around false positives and hallucination risk are useful and should be preserved.

## Round 3 (claude-opus-4-6)
The previous revision is well-structured and substantively sound. The four-bucket triage framework is the right approach, and the quarantine concept is genuinely valuable. My observations:

1. **No major errors or regressions introduced.** The previous reviewer did strong work restructuring from a flat backlog into a risk-aware triage process.

2. **The document buries its most important insight.** The core argument — that model-generated gap analyses are unreliable inputs to documentation backlogs — is the novel contribution here, but it's introduced gradually rather than stated up front with force. The executive summary should lead with the finding, not just the process recommendation.

3. **"Candidate Backlog Pending Verification" is a confusing label.** If they're pending verification, they're not yet backlog candidates. The name contradicts itself. A clearer label would signal they're in a verification queue, not a work queue.

4. **The Verification Standard section mixes gate criteria with PR policy.** These serve different audiences (the person triaging vs. the person reviewing a PR) and should be distinct.

5. **Gap numbering is inherited from the original analysis but never explained.** A reader encountering this document fresh has no idea why gaps jump from 1 to 5 to 10. A brief note would help.

6. **The Prioritization Rubric is stated but never applied.** Even a lightweight application to the Category 2 items would demonstrate the rubric's value and give readers a sense of relative priority.

7. **The Strategic Design Question (Gap 6) deserves slightly more framing.** The trade-off between review independence and orchestration convenience is correctly identified but could be sharpened — specifically, the risk of monoculture bias when replacing cross-model review with same-platform subagents.

8. **Minor structural issue:** The "Decision Rule" section repeats logic already in the Triage Workflow. These can be consolidated.

9. **The Recommended Actions section could be tightened.** Some items repeat what's already stated in the triage categories.

## Final Refined Document

# BuildOS Agent Parallelization Gap Analysis — Proposal

## Executive Summary

Claude Desktop produced a 10-point gap analysis claiming that BuildOS documentation is strong on strategic doctrine (when and why to parallelize) but has material gaps in operational how-to (how to configure and run agent-based workflows).

**Adversarial cross-model review revealed that this analysis is substantially unreliable as a documentation backlog.** Of the ten claimed gaps:

- **Three are false positives** — the features are already documented in the BuildOS repository.
- **Three are verified or likely hallucinations** — they describe platform features that do not exist.
- **Three are plausible but unverified** — they require primary evidence before any documentation work begins.
- **One is a strategic design question**, not a documentation gap.

This proposal replaces the original flat backlog with a strict evidence-first triage process. Its core recommendation: **do not treat model-generated gap analyses as work queues. Treat them as unverified claims that must pass an evidence gate before they consume documentation effort.**

---

## Why This Matters

Claude models frequently hallucinate platform features with high confidence. Documenting hallucinated features actively harms users by sending them down dead ends — creating support load, eroding trust in the documentation, and wasting contributor time on corrections. The cost of shipping a false feature description is higher than the cost of a temporarily undocumented real feature.

This proposal establishes a repeatable process for safely ingesting model-generated recommendations into the BuildOS documentation workflow.

---

## Proposal Summary

1. **Do not treat model-generated gap analyses as a backlog by default.**
2. **Separate false positives, unverified possibilities, design questions, and hallucinations into distinct categories.**
3. **Require primary evidence before any new platform feature is documented.**
4. **Only convert a claim into documentation work after it passes verification and priority review.**

---

## Verification Gate

Any feature not already evidenced in existing BuildOS documentation MUST be confirmed by at least one of the following before it can become a documentation task:

- Primary vendor documentation (official docs, changelogs, or release notes)
- Reproducible CLI or help output
- Tested and confirmed local behavior

This gate applies to all claimed capabilities, regardless of the confidence level of the source.

## PR Acceptance Criterion

Any pull request attempting to add documentation for features on the Quarantine List will be rejected unless it includes accompanying primary evidence that the feature exists and behaves as described. The standing rule is: **do not document unverified platform features.**

---

## Prioritization Rubric

Verified gaps promoted to the backlog are prioritized on three dimensions:

| Dimension | Question |
|---|---|
| **User Impact** | How many BuildOS users would benefit from this documentation? |
| **Failure Severity** | How badly would a user fail or waste time without it? |
| **Feature Stability** | Is this a stable, native capability or an experimental/fragile addition? |

Items scoring high on all three dimensions are prioritized first. Items that are low-impact or describe unstable features are deferred.

---

## Triage Workflow

Every claimed gap moves through this decision flow:

1. **Check existing BuildOS docs.**
   → If already documented: classify as **Already Covered**. No new work; consider discoverability improvements only.

2. **If not documented, check for primary evidence.**
   → If verified by vendor docs, CLI output, or tested behavior: classify as **Verification Queue**. Capture the evidence, apply the prioritization rubric, then promote to the documentation backlog.

3. **If the claim is architectural rather than factual:**
   → Classify as **Strategic Design Question**. Escalate for product/design review.

4. **If the claim lacks evidence or contradicts verified materials:**
   → Classify as **Quarantined**. Do not document. Record for future reference.

Only items that exit the Verification Queue with confirmed evidence and clear user value become documentation tasks.

---

## Triage Results

> **Note on gap numbering:** The gap numbers below (1–10) are inherited from the original Claude Desktop analysis to maintain traceability. Gaps not listed under a category appear under a different one.

### Category 1: Already Covered (Non-Gaps)

*These items were flagged as absent but are already documented. No new documentation is required.*

**Gap 1: Custom Subagent Definitions (`.claude/agents/`)**
- *Claim:* Completely absent from documentation.
- *Finding:* **False positive.** `docs/team-playbook.md` explicitly references `.claude/agents/`, and `docs/platform-features.md` has a dedicated subagents section with example YAML and documented capabilities.
- *Action:* None required. If discoverability is a concern, consider cross-linking from related pages.

**Gap 5 (Partial): Subagent Capabilities — Tool Restrictions, Worktree Isolation, Skills Access**
- *Claim:* Tool restrictions, scoped MCP servers, worktree isolation, and skills access are undocumented.
- *Finding:* **False positive.** Appendix A2 explicitly documents tool restrictions, model overrides, worktree isolation, and skills access.
- *Action:* None required.

**Gap 10: Annotated Project Tree**
- *Claim:* The project tree should include `.claude/agents/`.
- *Finding:* **Minor maintenance item**, not a material gap. The feature itself is documented; updating a tree diagram is routine upkeep.
- *Action:* File as a minor maintenance task if desired.

### Category 2: Verification Queue

*These items may reference real capabilities that are currently under-documented. They must pass the Verification Gate before any drafting begins. They are not yet approved documentation tasks.*

**Gap 2: Built-in Subagents**
- *Claim:* Claude Code ships with built-in subagents (Explore, Plan, general-purpose) with distinct roles.
- *Verification needed:* Confirm exact names, invocation methods, and whether they represent distinct capabilities or are simply prompt patterns.
- *Preliminary priority assessment:* **High user impact** if confirmed (users would want to know what's available out of the box), **moderate failure severity** (users can still define custom agents), **stability unknown**.

**Gap 3: Background Subagents**
- *Claim:* Subagents can run in background via Ctrl+B with progress tracked via `/tasks`.
- *Verification needed:* Confirm UI mechanics, task tracking behavior, and any limitations.
- *Preliminary priority assessment:* **High user impact** (background execution is central to parallelization), **high failure severity** (users may not discover this capability without documentation), **stability unknown**.

**Gap 8: Headless/Programmatic Mode**
- *Claim:* Claude Code supports headless execution (`claude -p`) for CI/CD integration.
- *Verification needed:* Confirm CLI flags, input/output behavior, and exit code semantics.
- *Preliminary priority assessment:* **Moderate user impact** (relevant to CI/CD users, which may be a subset of the BuildOS audience), **moderate failure severity** (users can find CLI help independently), **stability unknown**.

### Category 3: Quarantine List

*These claims contain hallucinated features or unverified external assertions. They are QUARANTINED and must not be documented unless independently proven to exist.*

**Gap 4: Agent Team Operational Controls**
- *Claim:* BuildOS should document display modes, plan approval workflows, direct teammate messaging, shutdown protocols, and a `TeammateIdle` hook.
- *Finding:* **Quarantined.** The `TeammateIdle` hook is a **verified hallucination** — it directly contradicts the verified hooks list in `docs/hooks.md`. The remaining claimed controls (tmux display splits, direct teammate messaging) are highly suspect and lack any supporting evidence.
- *Action:* Do not document. Reject any PR referencing these features without primary evidence.

**Gap 5 (Partial): Unsupported Subagent Capabilities**
- *Claim:* Persistent memory directories (`~/.claude/agent-memory/`), per-subagent hooks, and permission modes exist.
- *Finding:* **Quarantined.** These paths and configurations appear in no verified materials and are likely hallucinated.
- *Action:* Do not document.

**Gap 7: Scheduled Tasks and Channels**
- *Claim:* Native `/loop`, `/schedule`, and Channels features exist.
- *Finding:* **Quarantined.** Highly likely to be hallucinated or confused with custom project skills.
- *Action:* Do not document.

**Gap 9: Plugin Ecosystem**
- *Claim:* A `/plugin` system exists for distributable, installable units.
- *Finding:* **Quarantined.** No evidence this exists natively in Claude Code.
- *Action:* Do not document.

### Category 4: Strategic Design Questions

*These are architectural trade-offs requiring product and design judgment, not documentation omissions.*

**Gap 6: Review Swarm Pattern**
- *Claim:* Review personas could run in parallel using read-only subagents instead of sequentially via `debate.py`.
- *Finding:* **Escalated for design review.** This is a legitimate architectural question, but it is not a documentation gap. The current `debate.py` approach uses sequential, cross-model review to achieve model diversity and independent evaluation. Replacing this with same-platform parallel subagents would trade review independence for orchestration convenience — and would introduce **monoculture risk**, where all review perspectives share the same model's blind spots and biases. This trade-off requires a deliberate product decision before any documentation changes.
- *Action:* Escalate to product/design review. Do not modify documentation until a decision is made.

---

## Recommended Actions

### Immediate

| Action | Category | Owner |
|---|---|---|
| Close Gaps 1, 5 (partial), and 10 as non-gaps | Already Covered | Documentation lead |
| Create **verification tickets** (not documentation tickets) for Gaps 2, 3, and 8 | Verification Queue | Documentation lead + engineering |
| Record Gaps 4, 5 (partial), 7, and 9 in a standing quarantine reference list | Quarantine | Documentation lead |
| Escalate Gap 6 to product/design review | Strategic Design | Product lead |

### Process Changes

**Add a reviewer checklist** for any new platform-feature documentation PR:

- [ ] Is this feature already documented internally?
- [ ] Is there primary vendor evidence (docs, changelog, release notes)?
- [ ] Has the feature been reproduced locally?
- [ ] Does the proposed documentation describe a stable capability, not a one-off behavior?
- [ ] Is this documenting a feature, or proposing a new BuildOS workflow design?

**Establish a backlog hygiene rule:** No item from any model-generated analysis enters the documentation backlog unless:
1. The feature is verified against primary evidence.
2. User value is clear under the prioritization rubric.
3. The work is actually documentation, not product or design work.

---

## Conclusion

This proposal rejects the original framing that BuildOS has a broad operational documentation deficit around agent parallelization. The evidence shows four distinct realities:

| Reality | Count | Action |
|---|---|---|
| Already documented | 3 gaps | Close |
| Plausible but unverified | 3 gaps | Verify first, then decide |
| Likely hallucinated | 4 gaps | Quarantine |
| Architectural question | 1 gap | Escalate to design review |

The correct next step is not to draft documentation for all ten items. The correct next step is to adopt the verification gate, process the three candidate items through evidence review, and prevent unverified platform claims from entering BuildOS documentation.
