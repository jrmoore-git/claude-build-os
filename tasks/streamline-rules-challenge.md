---
debate_id: streamline-rules
created: 2026-04-12T20:05:36-0700
mapping:
  A: claude-opus-4-6
  B: gemini-3.1-pro
  C: gpt-5.4
---
# streamline-rules — Challenger Reviews

## Challenger A — Challenges
## Challenges

1. **ASSUMPTION** [MATERIAL] [COST:TRIVIAL]: The fix for 1A ("document before implementation") assumes "before" is the correct resolution. But the CLAUDE.md "after" phrasing for decisions.md may be intentional — you often can't document a *decision* before you've explored the problem space enough to *make* the decision. "Document before implementing" is different from "document before deciding." The proposal collapses these into one without verifying which semantic was intended. If the original CLAUDE.md author meant "record the decision after you've made it but before you move on," forcing "before implementing" could create a nonsensical instruction (document a decision you haven't made yet). This needs confirmation from the rule author, not a unilateral alignment to "before."

2. **RISK** [MATERIAL] [COST:SMALL]: The deduplication strategy (Phase 2) creates a web of cross-file references that introduces a new failure mode: **broken indirection**. Today, if Claude loads session-discipline.md, it gets the verification rules inline. After this change, it gets "See review-protocol.md Definition of Done." If review-protocol.md isn't loaded in that session (rules are selectively loaded based on context), Claude now has a dangling pointer instead of a duplicated-but-present rule. The proposal doesn't audit which files are always-loaded vs. conditionally-loaded, and doesn't verify that every "see X" reference points to a file that will be present when the referring file is loaded. This is the central risk of the entire proposal.

3. **UNDER-ENGINEERED** [MATERIAL] [COST:SMALL]: No loading-order or co-loading constraints are specified. If 2D says "Pipeline tiers: see CLAUDE.md" in workflow.md, that's fine because CLAUDE.md is always loaded. But 2C says session-discipline.md should reference review-protocol.md, and 2E says workflow.md should reference bash-failures.md. Are those guaranteed to be co-loaded? The proposal needs a simple table: for each cross-reference introduced, confirm the target file's loading condition.

4. **RISK** [ADVISORY]: Phase 3 tightening (3A-3F) is individually low-risk but collectively introduces a subtle problem: the compressed versions lose the *reasoning* behind rules. "Allowlist: `if allowlist is not None and value not in allowlist` — NOT `if allowlist and value...`" is correct but a future editor won't understand *why* without the explanation of empty-string/None bypass. This is a maintainability trade for ~150 tokens. Acceptable, but worth noting.

5. **ALTERNATIVE** [ADVISORY]: For Phase 2 deduplication, an alternative to cross-file references is to make CLAUDE.md the single source of truth for all headline rules (it's always loaded) and strip the duplicates from subordinate files entirely rather than replacing them with references. This avoids the dangling-pointer problem from challenge #2. Subordinate files would only contain *extensions* and *details* not present in CLAUDE.md. The proposal partially does this (2D makes CLAUDE.md canonical for tiers) but inconsistently (2A makes code-quality.md canonical over CLAUDE.md for simplicity).

6. **ASSUMPTION** [ADVISORY]: The token estimate of "~1,200-1,500 tokens recoverable (~10-12%)" is tagged ESTIMATED. The proposal doesn't show per-item token counts that sum to this range. Phase 3 items are annotated (~50, ~100, ~150, ~40, ~35, ~30 = ~405 tokens), but Phase 1 and Phase 2 savings aren't itemized. The Phase 2 savings depend on how much text is replaced vs. how many reference lines are added. The net could be lower than claimed if reference lines + explanatory context around them consume more than expected.

7. **OVER-ENGINEERED** [ADVISORY]: 3B removes preambles that are described as preceding "self-explanatory sections," but the design.md preamble ("Any match = rewrite") is actually a *directive* — it tells Claude what to do when a pattern matches. Removing it changes the instruction from "match = rewrite" to an implicit list of anti-patterns with no stated action. This specific cut should be reconsidered.

## Concessions

1. The four ambiguity fixes in Phase 1 are the highest-value part of this proposal. Contradictory instructions are genuinely harmful, and three of the four (1B, 1C, 1D) have clean, obviously correct resolutions.

2. The constraint framing — "compression, not reduction" — is the right frame and the proposal is disciplined about maintaining it. No rules are actually removed.

3. The deduplication targets in Phase 2 are correctly identified. These are real duplications, not just thematic overlap, and the canonical-source selections are mostly sensible.

## Verdict

**REVISE** — The proposal is sound in intent but must address the dangling-reference risk (challenge #2/#3) before implementation. Add a co-loading verification table for every cross-reference introduced in Phase 2, and confirm the intended semantics of 1A with the rule author. These are SMALL fixes that would make the proposal safe to execute.

---

## Challenger B — Challenges
## Challenges

1. [ASSUMPTION] [MATERIAL] [COST: SMALL]: **Context Loading & Pointers.** The proposal relies on the assumption that the LLM will reliably pause to read referenced files (e.g., `See code-quality.md`) before taking action. The proposal explicitly notes in 1C and 2D that `CLAUDE.md` is "always loaded." If `CLAUDE.md` is the only guaranteed context, moving the definitions of "Simplicity" (2A) and "Document results" (2G) into auxiliary files that require an explicit tool call to read means those rules will simply be ignored in 90% of sessions. This directly violates the proposal's constraint: "no enforcement weakened." Core operational directives must live in the always-loaded context. 

2. [UNDER-ENGINEERED] [MATERIAL] [COST: TRIVIAL]: **Removing Enforcement Triggers.** Phase 3B proposes deleting the preamble from `design.md`: *"Watch for these anti-patterns in generated UI and content. Any match = rewrite."* This is not mere verbosity; "Any match = rewrite" is the explicit enforcement mechanism that instructs the LLM on how to handle a violation (self-correction). Deleting this weakens the prompt's structural enforcement, violating the primary constraint. 

3. [RISK] [ADVISORY]: **Documentation Desync.** In Phase 1A, changing `decisions.md` to strictly update "before implementing" creates a failure mode. If the AI documents a planned architectural decision that fails during implementation, it often moves on to a new approach without revising the pre-written `decisions.md` entry. "Document first" works for plans, but "Update decisions after" ensures the documented decision actually survived contact with the compiler.

4. [EVIDENCE] [ADVISORY]: The quantitative claim *"Estimated total: ~12,810 tokens across 15 Claude-facing files. ~1,200-1,500 tokens recoverable"* is [ESTIMATED]. While directionally sound, the exact recovery depends heavily on the tokenizer used (e.g., Claude's specific tokenization of markdown headers and code blocks).

## Concessions
1. Resolving the 4 contradictions in Phase 1 is high-value; forcing an LLM to reconcile conflicting systemic instructions burns inference capacity and leads to unpredictable behavior.
2. Stripping origin tags (Phase 3A) is a perfect example of removing useless token weight that provides zero behavioral steering.
3. Centralizing the skip conditions for `/challenge` (Phase 1C) prevents test-bypass loopholes.

## Verdict
**REVISE** 
The proposal successfully identifies valuable compaction targets, but fails its own "no enforcement weakened" constraint by moving critical directives out of the always-loaded context and stripping explicit self-correction triggers.

---

## Challenger C — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes cross-file references preserve behavior in an always-loaded / sometimes-loaded instruction system, but it does not verify loading semantics or whether Claude reliably follows “see X.md” indirections as strongly as inline rules. If some files are not loaded in the same contexts, replacing duplicated text with references can reduce compliance despite preserving nominal content. This directly challenges the “same governance, same enforcement” claim.

2. [RISK] [MATERIAL] [COST:SMALL]: Phase 2 increases dependency on canonical files, creating a single-point-of-failure risk: if a canonical file is omitted, stale, or ambiguously referenced, multiple surfaces lose guidance at once. The proposal does not include link integrity checks, canonical-owner rules, or a drift-prevention mechanism to keep references and targets synchronized.

3. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The recommendation in 1A picks “before” as the correct timing for updating decisions.md, but does not justify why “after material decisions” was wrong rather than describing a different event boundary. “Before implementing material decisions” and “after material decisions” are not necessarily contradictory if “decision” precedes “implementation”; the issue may be wording ambiguity, not policy conflict. This needs explicit semantic clarification before rewriting governance text.

4. [RISK] [MATERIAL] [COST:SMALL]: The “docs to read at session start” change preserves a shortened list in CLAUDE.md while moving the fuller checklist into workflow.md, but this undercuts the stated goal of reducing ambiguity in the always-loaded file. A model that stops at the short list may miss PRD/project-map/session-log context. The proposal does not address the risk of partial compliance introduced by splitting “minimum required” and “full checklist” across files.

5. [ALTERNATIVE] [ADVISORY]: The proposal only considers deduplication via one-line references. It does not consider a safer middle ground: keep a one-line normative summary inline plus a reference for details. That would preserve immediate guidance while still reducing token load.

6. [UNDER-ENGINEERED] [MATERIAL] [COST:MEDIUM]: There is no acceptance test for the core claim that compression causes “zero governance impact.” You need a before/after verification pass: enumerate every normative rule, map source→canonical location, and confirm no rule became weaker, less discoverable, or context-dependent. Without a traceability matrix or diff-based rule inventory, “rules removed: 0” is not verified.

7. [ASSUMPTION] [ADVISORY]: The claim that “research shows instruction compliance decreases as instruction count grows” is invoked as justification, but no specific evidence is provided from this proposal text, nor is there evidence that a 10–12% reduction in this rule set materially improves compliance. The direction may be plausible, but the magnitude benefit is unverified.

8. [RISK] [MATERIAL] [COST:TRIVIAL]: In 1C, centralizing skip conditions in CLAUDE.md while leaving workflow.md “compatible” does not guarantee compatibility over time. If workflow tiers implicitly skip challenge for categories broader or narrower than CLAUDE.md, future readers may still infer different behavior. The proposal should require workflow.md to explicitly defer to CLAUDE.md on skip logic, not merely rely on compatibility.

9. [UNDER-ENGINEERED] [ADVISORY]: The proposal addresses risk of changing, but not enough risk of not changing. It says ambiguity reduces governance effectiveness, but does not identify observed failures caused by the current duplication/contradictions. A couple of concrete examples would help distinguish urgent cleanup from aesthetic compression.

10. [RISK] [MATERIAL] [COST:SMALL]: 1D’s fix for the “essential eight” contradiction still leaves an awkward two-level rule: “eight invariants” but only “6 applicable.” That phrasing can continue to confuse whether the two excluded items are irrelevant, prohibited, or conditionally applicable. A better fix would restate the applicable set directly in review-protocol.md or rename the concept locally (e.g., “BuildOS applicable invariants”). As written, ambiguity may persist.

11. [OVER-ENGINEERED] [ADVISORY]: The proposal is very granular about token shaving in multiple files (e.g., 30–50 token reductions), but lacks prioritization by governance value. Several micro-edits may add review burden and churn for negligible practical gain.

12. [RISK] [MATERIAL] [COST:SMALL]: Removing explanatory preambles and anecdotes may eliminate rationale that helps disambiguate terse rules in edge cases. The proposal assumes all removed text is non-normative and low value, but does not distinguish between “history” and “operational context.” This is especially relevant for security.md and orchestration.md, where terse rewrites can be read too literally or miss why the rule exists.

13. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposal changes multiple governance files but defines no rollout method for ensuring all references remain valid after edits. At minimum, it should include a grep/check script for dangling references and a manual spot-check that every “See X.md” points to an existing section name or stable anchor.

14. [ASSUMPTION] [ADVISORY]: The proposal assumes CLAUDE.md is the right canonical home for pipeline tiers because it is “always-loaded,” but that is not verified here. If “always-loaded” is not guaranteed in all entrypoints, using it as canonical may be the wrong choice.

15. [QUANTITATIVE CLAIM] [ADVISORY]: **Estimated total: ~12,810 tokens across 15 Claude-facing files** — SPECULATIVE: no token audit or file breakdown is provided in the proposal text.

16. [QUANTITATIVE CLAIM] [ADVISORY]: **~1,200–1,500 tokens recoverable (~10–12%)** — ESTIMATED: appears to sum listed reductions plus larger deduplications, but no per-file before/after counts are provided; assumptions behind the estimate are not shown.

17. [QUANTITATIVE CLAIM] [ADVISORY]: **Origin tags ~50 tokens; preambles ~100; tightened rules ~150; compaction ~40; root-cause ~35; routing ~30** — ESTIMATED: these are plausible editorial estimates, but no exact line-level counts are cited.

18. [QUANTITATIVE CLAIM] [MATERIAL] [COST:TRIVIAL]: **“zero governance impact” / “enforcement weakened: none”** — SPECULATIVE: this is the central claim, but no evidence or validation method is provided. Because it is unverified and material, it should not be accepted as stated without a traceability/behavior check.

## Concessions
- The proposal correctly identifies real inconsistencies, especially around documentation timing, session-start reading lists, skip conditions, and the “essential eight” wording.
- It generally preserves the right principle: consolidate duplicated normative text into canonical locations rather than silently deleting rules.
- It separates ambiguity fixes from verbosity trims, which is a sound structure for review.

## Verdict
REVISE — the cleanup direction is good, but the proposal overclaims “same governance, zero impact” without validating load semantics, rule traceability, and the compliance risk introduced by replacing inline rules with cross-file references.

---
