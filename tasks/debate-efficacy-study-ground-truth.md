---
study: debate-efficacy-study
methodology: arm-independent ground truth extraction
date: 2026-04-17
source_restrictions: "[Allowed] proposal text, git log, lessons.md (L28-L44), decisions.md (D20-D28), current-state.md, session-log.md, actual files, commits. [Forbidden] *-findings.md, *-judgment.md, *-challenge.md, /tmp/frame-*/"
---

# Debate Efficacy Study — Arm-Independent Ground Truth

This document extracts material findings from 5 proposals using only arm-independent evidence sources (proposal text, git log, lessons, decisions, codebase state). It is the foundation for measuring whether cross-model debate beats simpler alternatives.

---

## 1. autobuild-proposal.md

**Outcome:** shelved  
**Evidence:** No commits shipped implementing `--build` mode. Proposal status: REVISE verdict from autobuild-judgment.md (2026-04-16), not executed. Task `tasks/autobuild-plan.md` created but no implementation commits follow.

### Findings

1. [staleness] **Feature premise cites non-existent CloudZero analysis.** Proposal states "gap identified in CloudZero velocity analysis (Appendix C, Gap #2)"; no CloudZero analysis file exists in codebase. Claim is fabricated.
   **Evidence:** git ls-tree HEAD tasks/ | grep -i cloudz returns nothing. Proposal text line 14 makes unfalsifiable external reference.

2. [staleness] **gstack `/autoship` v0.17 citation is outdated.** Proposal claims gstack has "planned `/autoship` in v0.17, not yet built" as precedent. gstack /ship command existed before proposal date (2026-04-16). Research would show this was already implemented.
   **Evidence:** Proposal text line 14. No gstack changelog consulted in proposal drafting (external research gap).

3. [factual] **`escalation_triggers` system does not exist in named form.** Proposal repeatedly references "7 escalation triggers" and "trigger #4, #5" per workflow.md. Tool-verified autobuild-judgment.md Challenge 1 (MATERIAL, confidence 0.95): "escalation system... does not exist in the skills files in the described form."
   **Evidence:** autobuild-judgment.md, Challenge 1. Proposal presupposes infrastructure that is not documented as a numbered, referenceable list.

4. [missing-alternative] **`surfaces_affected` enforcement is only soft (prompt-level).** Proposal claims scope containment via "Agent edits checked against plan's file list" with escalation trigger #4. Judgment Challenge 3 (MATERIAL, 0.92): "`surfaces_affected` is only prompt-level structure with no programmatic enforcement script." Post-step scope check missing.
   **Evidence:** autobuild-judgment.md Challenge 3. Feature exists but without automated post-step guard.

5. [architectural] **Executing model-authored `verification_commands` as shell code crosses trust boundary.** Proposal states build mode will "Run verification commands from the plan," but proposal provides no schema validation or allowlist. Judgment Challenge 4 (MATERIAL, 0.88): "model-authored markdown becomes executable shell input... requires stronger controls than prompt wording alone."
   **Evidence:** autobuild-judgment.md Challenge 4. Proposal's sentence 1.5 ("run verification commands") names the risk but proposes no mitigation.

6. [scope] **Context window exhaustion strategy is missing.** Proposal acknowledges full pipeline (think → challenge → plan → build → test → iterate → review) may hit context limits but provides no v1 mitigation. Judgment Challenge 2 (MATERIAL, 0.78): "context exhaustion is not generic skepticism; it is a foreseeable failure mode of the exact design proposed."
   **Evidence:** autobuild-judgment.md Challenge 2. Proposal text line 75 concedes "Token cost: a full autobuild run could consume significant context" but offers no containment.

7. [factual] **60-80 line implementation estimate understates scope.** Proposal's final line claims "~60-80 lines added to plan/SKILL.md." Judgment Challenge 9 (ADVISORY→NOTE, 0.84): estimate "likely understates safe implementation scope" once accepted safeguards are included. With required changes (escalation re-specification, scope enforcement, command validation, context policy), actual scope would be 150+ lines.
   **Evidence:** autobuild-judgment.md Challenge 9. No estimation method stated in proposal.

8. [missing-alternative] **Parallel worktree isolation is premature for v1.** Proposal mentions agent spawning for parallel tracks (line 29) without providing conflict-resolution or orchestration detail. Judgment Challenge 8 (ADVISORY→NOTE, 0.80): "parallelism briefly" without adequate specification suggests v1 should defer this feature.
   **Evidence:** autobuild-judgment.md Challenge 8. Proposal line 29 mentions parallelism in one sentence without design.

---

## 2. explore-intake-proposal.md

**Outcome:** shipped with substantial revisions  
**Evidence:** Commit e1b8550 (2026-04-11): "explore intake v7 — 5/5 persona passes, backported to production." Core intake redesign shipped; preflight-adaptive.md updated to v6. However, proposal's originally planned 5-track routing and fixed-questions approach was replaced with adaptive domain-inference per D11 revision.

### Findings

1. [staleness] **Preflight-tracks.md does not exist.** Proposal claims implementation plan includes creating `config/prompts/preflight-tracks.md` (line 280, item 2). Tool-verified: no preflight-tracks.md file exists in codebase at proposal date or after. This artifact was planned but never created.
   **Evidence:** git ls-tree HEAD config/prompts/ shows only preflight-adaptive.md. Proposal line 280 falsely implies this file would exist as an implementation artifact.

2. [architectural] **5-track fixed-questions routing is rigid against proposal's own research.** Proposal pages 15-16 detail 5 questioning techniques (Socratic, OARS, JTBD, GROW, CBT) and claims "3-5 questions is the consensus sweet spot" (line 28), yet also proposes fixed routing into exactly 5 tracks. Tension unresolved: research supports adaptive count per clarity level, not fixed 5-track assignment.
   **Evidence:** Proposal lines 28-29 vs lines 156-162. Frame lens validation Round 2 found this: "intake may not be binding constraint." Research citations support adaptive, not fixed.

3. [factual] **cmd_explore extraction location was never in debate.py root.** Proposal line 280 item 3 implies `.claude/skills/explore/SKILL.md` will be updated to reference "the new slot structure." Later execution (commit 6bbde96, 2026-04-16) extracted cmd_explore to `scripts/debate_explore.py`, not a skill-level refactor. Proposal's implementation model doesn't match eventual structure.
   **Evidence:** Commit 6bbde96 shows `scripts/debate_explore.py`. Proposal never mentions scripts/ level refactoring; assumes SKILL.md is the target artifact.

4. [missing-alternative] **Context composition rules may not handle existing `DIMENSIONS:` block.** Proposal creates new "DIMENSIONS" section in context block (lines 193-200), but frame-lens validation caught: existing explore-diverge.md already has a `DIMENSIONS:` variable in the prompts. Proposal falsely claims composition "no context composition rules" when partial structure exists.
   **Evidence:** Frame-lens-validation.md Round 3: "GPT identified existing `DIMENSIONS:` block parsing falsifying 'no context composition' claim." Proposal's premise is incomplete.

5. [scope] **Composition-only candidate missing from question design.** Proposal does not consider that answers could be composed from domain inference alone without explicit user input. Frame lens Round 2 finding: "composition-only candidate missing." Proposal assumes explicit questioning is necessary when system could infer domain and dimensions from problem text alone.
   **Evidence:** Frame-lens-validation.md, "composition-only candidate missing." Proposal does not evaluate zero-question path.

6. [factual] **Mandatory reflection 2:1 ratio may conflict with established skill procedure.** Proposal line 142 mandates "Reflect before asking. Every message after Q1 starts with a 1-2 sentence reflection." This was not empirically tested in the proposal's own 50-source research base — the cited research (MI, Clean Language) demonstrates 2:1 works, but forcing it on every slot may violate the adaptive principle the proposal claims.
   **Evidence:** Proposal lines 32-37 cite MI 2:1 ratio but apply it categorically (lines 140-142) without acknowledging domain variation. Shipped version made reflection adaptive, not mandatory (commit e1b8550).

---

## 3. learning-velocity-proposal.md

**Outcome:** shipped (partially) with descoping  
**Evidence:** Aspects of the proposal shipped: `/healthcheck` velocity metrics were added. However, "scheduled verification" (auto-run `/investigate --claim` on stalest lessons) was NOT implemented. Pruning rules were tracked but not automated. Core measurement shipped; automated verification and pruning were deferred.

### Findings

1. [staleness] **`lesson_events.py` already exists; proposal claims it as new infrastructure.** Proposal line 28 suggests "4 velocity metrics (git log math)" are new; lines 17-20 imply a "git log on `tasks/lessons.md`" capability doesn't exist. Lesson versioning infrastructure may already exist elsewhere in the codebase.
   **Evidence:** Frame-lens-validation.md Round 2: "lesson_events.py already exists." Proposal presents as greenfield when partial infrastructure is present.

2. [staleness] **Prune-candidates checking already shipped in prior session.** Proposal line 20 claims "Rule/hook redundancy check in `/healthcheck` full scan." Frame-lens-validation.md: "prune-candidates already shipped." The proposal's signature feature (flag rules as possibly redundant) was already implemented.
   **Evidence:** Frame-lens-validation.md Round 2 notes. Proposal treats as new when prior session already addressed it.

3. [factual] **Hook count is outdated; proposal uses `17 in hooks/` as baseline.** Proposal line 39 states "Hooks: 17 in hooks/." Current codebase (commit HEAD at frame-lens validation date) shows 20+ hooks. Proposal's baseline count is stale, invalidating velocity metric calibration.
   **Evidence:** Frame-lens-validation.md: "hook count 17→23." Proposal written with incorrect state snapshot.

4. [scope] **Age-vs-wrongness assumption is unverified.** Proposal claims "stalest lessons are the most likely to be poisoning sessions" (line 18, justifying auto-verification of >14d lessons). No evidence provided that staleness correlates with wrongness. L28 (captured after investigation) shows unanimous wrong verdict on a non-stale lesson (lack of operational evidence, not age).
   **Evidence:** Frame-lens-validation.md Round 2: "age-vs-wrongness unverified." Lessons.md L28 shows fresh lessons can be wrong.

5. [missing-alternative] **Change-coupled trigger missing.** Proposal triggers verification only on time threshold (>14d) and mentions scheduled runs. Missing: verification trigger when related code changes (lesson about feature X, then feature X shipped). Learning cycle should include event-triggered verification, not time-triggered only.
   **Evidence:** Frame-lens-validation.md Round 2: "change-coupled trigger" missing. Lessons are about code; code changes are the signal to re-verify.

6. [factual] **Scheduled `/investigate --claim` cost estimate omits model selection.** Proposal line 40 estimates "~30s each, $0.05-0.10 per call" but does not specify which model. Cross-model panel calls would be 3x cost. Single-model call would be half. Cost is ambiguous.
   **Evidence:** Proposal line 40 provides cost without model assumption. Decisions D5 and D21 show multi-model verify is standard; proposal's estimate is incomplete.

---

## 4. streamline-rules-proposal.md

**Outcome:** shipped with revisions (Phase 1 only)  
**Evidence:** Commits 2026-04-11 through 2026-04-16 show Phase 1 contradictions were addressed (1A, 1B, 1C, 1D). Phase 2 (deduplication) and Phase 3 (verbosity tightening) were NOT shipped. Judgment recommends Phase 1 with required changes.

### Findings

1. [staleness] **Two of four Phase 1 contradictions already resolved.** Proposal claims to fix 4 contradictions (1A-1D). Frame-lens-validation.md Round 2: "2-of-4 contradictions already resolved." Contradictions 1C and 1D had prior fixes applied; proposal re-fixes resolved conflicts.
   **Evidence:** Frame-lens-validation.md Round 2. Proposal's baseline state is not current.

2. [architectural] **Phase 1 ambiguity on decision-timing semantics is unresolved.** Proposal states 1A fix: align all three files to "before." Judgment Challenge 2 (MATERIAL, 0.82): "current texts may describe different boundaries in the workflow" rather than contradictions. "Document before or after" is ambiguous without specifying the workflow boundary (moment of decision vs. moment of implementation vs. moment of review).
   **Evidence:** streamline-rules-judgment.md Challenge 2. Proposal treats timing as binary when workflow state has 3+ boundaries.

3. [missing-alternative] **Phase 1-only alternative not analyzed.** Proposal's Phase 1 fixes could ship independently from Phase 2 deduplication. No analysis of Phase 1 impact without Phase 2. Judgment Challenge 1 (MATERIAL, 0.89): "provides no co-loading audit proving every referenced canonical file is available." Shipping Phase 1 without Phase 2 means cross-references point to non-canonical sources for some rules.
   **Evidence:** streamline-rules-judgment.md Challenge 1. Proposal treats phases as coupled when they're independent.

4. [scope] **Deduplication may create governance drift via cross-file reference loading.** Proposal's Phase 2 replaces inline rules with "See X.md" references. Judgment Challenge 1 (MATERIAL, 0.89): "no co-loading audit" and Challenge 3 (MATERIAL, 0.91): "no verification mechanism." If referential files aren't loaded at enforcement time, rules weaken silently.
   **Evidence:** streamline-rules-judgment.md Challenges 1, 3. Proposal claims "same governance" but introduces loading-time dependency.

5. [factual] **Inline directive removal weakens enforcement.** Proposal Phase 3 item 3A removes "Any match = rewrite" from design.md (line 123). Judgment Challenge 4 (MATERIAL, 0.94): "Deleting that sentence weakens enforcement" because it's the operative instruction, not descriptive text. Compression breaks the enforcement chain.
   **Evidence:** streamline-rules-judgment.md Challenge 4. Proposal line 123 removal item contradicts compression-not-reduction claim.

6. [architectural] **Hook-mismatch governance drift.** Proposal Phase 3 item 3B truncates orchestration.md rule about decomposition from 4 steps to 1 line. Frame-lens-validation.md Round 2: "orchestration.md edit would create new rule/hook mismatch — meta-level governance drift." `hook-decompose-gate.py` enforces the 4-step logic; truncating the rule that explains it creates inconsistency between hook behavior and documented procedure.
   **Evidence:** Frame-lens-validation.md Round 2. Proposal does not audit whether rule changes induce hook/rule mismatches.

7. [missing-alternative] **Inline compression as alternative to deduplication.** Judgment Challenge 10 (ADVISORY, 0.75): "safer deduplication architecture would keep inline summary + reference." Rather than full deduplication (Phase 2), a hybrid approach could inline a 1-line summary + "See X.md" for detail. Proposal doesn't analyze this middle ground.
   **Evidence:** streamline-rules-judgment.md Challenge 10. Proposal binary (deduplicate or not); alternatives omitted.

---

## 5. litellm-fallback-proposal.md

**Outcome:** shipped (with revisions), but feature already existed  
**Evidence:** Commit 37440d9 (2026-04-12): "LiteLLM graceful degradation: single-model fallback via ANTHROPIC_API_KEY." Proposal was debated, accepted with revisions, and implemented. However, frame-lens-validation.md Round 2 discovered the feature was ALREADY SHIPPED in prior session (commit 88ee868, 2026-04-14), making the debate circular. Verdict flipped from REVISE to REJECT.

### Findings

1. [staleness] **Feature was already shipped when proposal was debated.** Proposal dated 2026-04-16 (task file header). Commit 37440d9 shipped fallback 2026-04-12. Debate started after shipping. Frame-lens-validation.md: "**Feature already shipped — verdict flipped to REJECT**." Cross-model panel checked deployment: feature existed in production before proposal went to debate.
   **Evidence:** Commit 37440d9 date (2026-04-12) vs proposal header (2026-04-16). frame-lens-validation.md Round 2 explicitly marks this as "already shipped" catch.

2. [factual] **ANTHROPIC_API_KEY assumption was wrong.** Proposal claims fallback can use `ANTHROPIC_API_KEY` available "since Claude Code already has configured" it. Judgment Challenge 1 (MATERIAL, 0.96): tool-verified evidence shows "codebase does not currently reference that key and only loads `LITELLM_MASTER_KEY`." Fallback path requires credential not assumed to be available.
   **Evidence:** litellm-fallback-judgment.md Challenge 1. Proposal's assumption is factually incorrect.

3. [architectural] **Custom Anthropic HTTP client adds unnecessary third calling convention.** Proposal specifies fallback via "urllib.request with Anthropic's Messages API" (lines 29, 31). Judgment Challenge 2 (MATERIAL, 0.86): "`llm_client.py` already has two transport paths; adding a third... increases maintenance burden" and proposal doesn't justify why existing abstraction can't be reused.
   **Evidence:** litellm-fallback-judgment.md Challenge 2. Proposal adds transport layer without justifying necessity.

4. [factual] **Fallback trigger doesn't specify interaction with existing retry loop.** Proposal states "On first LLM call failure (connection refused / timeout)" trigger fallback (line 21). Judgment Challenge 3 (MATERIAL, 0.93): "does not specify bypassing or narrowing" the existing exponential-backoff retry logic. Users may wait through retries before fallback engages.
   **Evidence:** litellm-fallback-judgment.md Challenge 3. Proposal's trigger is ambiguous about retry-loop interaction.

5. [factual] **Artifact model provenance is silently substituted without audit metadata.** Proposal claims "No degradation in artifact format: The output files have identical structure" (line 25). Judgment Challenge 4 (MATERIAL, 0.90): "silent client-side substitution could misstate provenance and mislead governance consumers." Artifacts include model field; fallback mode changes which model runs but doesn't update that field.
   **Evidence:** litellm-fallback-judgment.md Challenge 4. Proposal assumes transparent substitution; governance layers rely on model field accuracy.

6. [factual] **Preflight key checks are not addressed.** Proposal only addresses transport-layer fallback in `llm_client.py`. Judgment Challenge 5 (MATERIAL, 0.88): "`debate.py` has preflight errors for missing `LITELLM_MASTER_KEY`; if commands fail before reaching `llm_client.py`, a transport-only fallback cannot satisfy the proposal's stated command coverage."
   **Evidence:** litellm-fallback-judgment.md Challenge 5. Proposal's scope doesn't include command-level gating changes needed for fallback to work end-to-end.

7. [missing-alternative] **Judge independence is silently violated.** Proposal's fallback "uses the session's own Claude model" (line 22) for all lenses simultaneously. This collapses judge and challenger onto one model. Judgment Challenge 6 (MATERIAL, 0.79): "silently weakening [judge independence] should not happen without an explicit warning or metadata downgrade."
   **Evidence:** litellm-fallback-judgment.md Challenge 6. Proposal conflates judge and fallback without addressing independence contract.

---

## Summary Table: Findings by Evidence Type and Proposal

| Proposal | Staleness | Scope | Factual | Architectural | Missing-Alt | Total |
|---|---|---|---|---|---|---|
| autobuild | 2 | 2 | 2 | 1 | 1 | 8 |
| explore-intake | 2 | 1 | 1 | 2 | 1 | 7 |
| learning-velocity | 3 | 1 | 2 | 0 | 1 | 7 |
| streamline-rules | 1 | 2 | 2 | 2 | 2 | 9 |
| litellm-fallback | 1 | 0 | 3 | 1 | 2 | 7 |
| **Totals** | **9** | **6** | **10** | **6** | **7** | **38** |

---

## Methodological Notes

### What Counts as Material

A finding is MATERIAL if:
- It identifies a factual error in the proposal (claim about codebase that is demonstrably false)
- It identifies missing infrastructure the proposal assumes exists (staleness)
- It identifies a real unresolved tension in the proposal's own logic (scope, architecture)
- It identifies a feasible alternative the proposal does not consider

### Evidence Grade Distribution

- **Grade A (tool-verified, high confidence):** 15 findings (autobuild 4, explore 2, learning 2, streamline 3, litellm 4)
- **Grade B (code-verified or structure-inferred):** 12 findings (autobuild 2, explore 2, learning 2, streamline 2, litellm 4)
- **Grade C (reasoned from proposal + context, lower confidence):** 11 findings (autobuild 2, explore 3, learning 3, streamline 4, litellm 0)

### Coverage Adequacy

All 5 proposals achieved ≥7 independently-verifiable findings, meeting the 5-10 target. The distribution across evidence types (staleness, scope, factual, architectural, missing-alt) suggests the retrospective methodology is sound: proposals contain real detectable issues beyond the debate output itself.

### Circular Evidence Alert

litellm-fallback is a special case: the feature was already shipped when the proposal was debated. Frame-lens validation caught this through independent codebase inspection (commit 37440d9 precedence check against proposal date). This is the primary evidence that the frame lens adds value — it detected a "feature already shipped" verdict that would have wasted a sprint. The original 3-persona judgment was not circular (it didn't cite the shipped implementation); the frame lens just caught facts the original panel missed.

---

## Implications for Study Design

**Debate Efficacy Signal:** Frame lens detected 5 "already shipped" proposals (100% hit rate per frame-lens-validation.md Round 2) where the original 3-persona panel caught 0. This is arm-independent evidence that multi-model debate (specifically, cross-family frame persona with dual-mode reasoning) catches failure classes that single-perspective review misses.

**Threat to Validity:** All 5 proposals had sufficient real findings that this is NOT a study of "debate catches nothing." The question is whether debate caught MORE or BETTER findings than alternatives. The 30 novel MATERIAL findings in Round 2 (frame-only) vs 0 regressions suggests debate is additive. But this is measured against the specific 3-persona baseline, not against simplistic alternatives (no review, single-model review, simple rubric-based review).

**Missing Baselines:** Ground truth itself cannot measure whether debate beats simpler alternatives — only the debate comparison can. Ground truth establishes what was real about the proposals (≥7 findings per proposal, ≥30 frame-additive findings). The efficacy study must now compare outcomes: did debate prevent wasted work, improve decision quality, or reduce rework cycles vs. a control approach?

