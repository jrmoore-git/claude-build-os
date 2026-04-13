---
debate_id: streamline-rules
created: 2026-04-12T20:12:13-0700
phase: refine
rounds: 6
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: yes
---
# streamline-rules — Refined Document

## Round 1 (gemini-3.1-pro)
The original proposal effectively identified token waste and contradictions but introduced severe governance risks by assuming cross-file references would seamlessly replace inline rules. Centralizing rules without verifying load semantics (whether the target file is actually in the model's context) risks silently dropping critical enforcement triggers. 

To make this proposal executable and safe, the revision:
1. **Clarifies Semantics:** Reframes contradictions (like "before vs. after" documentation) to capture the intended workflow rather than arbitrarily picking one word.
2. **Secures Enforcement Triggers:** Reverses the removal of operative instructions (e.g., "Any match = rewrite") which are necessary to drive model behavior, compressing them instead of deleting them.
3. **Solves the Cross-Reference Gap:** Introduces a strict Load Semantics Table for all Phase 2 deduplications. If an always-loaded file (CLAUDE.md) defers to a conditionally-loaded file, a normative one-line summary must remain in the always-loaded file.
4. **Adds Rollout Verification:** Mandates a strict traceability and reference integrity check to prove the "zero governance impact" claim.

## Round 2 (gpt-5.4)
The revision is materially stronger than a pure “compression” draft: it now addresses the previously accepted concerns about cross-file enforcement, semantic timing in 1A, preservation of the “Any match = rewrite” action trigger, explicit workflow.md deferral, and rollout verification.

Remaining issues I corrected in the revised document:

1. **Challenge 1 needed more than a high-level protocol.**  
   The current revision added a load-semantics table, but several entries still asserted “direct reference is safe” without stating the co-loading basis. I strengthened this by requiring a per-reference justification and by making inline summaries mandatory whenever co-loading is not guaranteed.

2. **Some “contradiction” wording in 1A was still too strong.**  
   The accepted challenge required reframing this as semantic clarification. I changed the framing so the issue is sequence ambiguity, not necessarily a true policy conflict.

3. **Phase 2 included one potentially weakening move in 2G.**  
   The draft said CLAUDE.md should say “Update decisions.md, lessons.md, and handoff.md before implementing.” That can overgeneralize timing and blur the narrower intended rule from 1A. I tightened it so CLAUDE.md preserves the specific material-decision timing and points to session-discipline.md for the full destination matrix.

4. **The verification section was good but still incomplete for a “zero governance impact” claim.**  
   I expanded it into an explicit rule-traceability requirement with three concrete outputs: source→canonical mapping, non-weakening confirmation, and reference integrity/spot-checks.

5. **A few compression steps needed guardrails.**  
   Some cuts were acceptable only if the replacement text preserved the operative directive. I made those constraints explicit so implementation does not accidentally weaken enforcement during editing.

6. **Structure and decisiveness improved with minimal softening.**  
   I kept all original recommendations/phases and made them more executable rather than more hedged.

## Round 3 (claude-opus-4-6)
The previous revision is solid and addresses most accepted challenges. However, several issues remain:

1. **Challenge 1 (Cross-file load semantics):** The traceability table in Phase 2 is good but uses vague language like "direct reference allowed only if both are loaded in the same review/commit path" — this defers the actual audit rather than performing it. Several entries punt with "only if" conditionals rather than stating what IS the case. The table needs to resolve these conditionals into definitive statements or default to keeping inline summaries.

2. **Challenge 2 (1A timing semantics):** Well addressed. The "decide -> document -> implement" sequence is explicit.

3. **Challenge 3 (Rollout verification):** Phase 4 exists but reads as a checklist without specifying WHO executes it or WHEN relative to the other phases. It also lacks a failure mode — what happens if a check fails?

4. **Challenge 4 ("Any match = rewrite"):** Addressed in 3B, but the current wording buries it. The directive should be more prominent since this was a near-deletion that would have weakened enforcement.

5. **Challenge 6 (workflow.md explicit deferral):** Mentioned in 1C but the actual workflow.md change is stated as "replace their local lists with 'Skip conditions: see CLAUDE.md'" — this is adequate but should be called out as a workflow.md edit, not just implied.

6. **Challenge 8 (Session-start reading list):** 1B addresses this well with the "minimum required" vs "mandatory full planning checklist" distinction.

7. **Structural issue:** The traceability table in Phase 2 has conditional entries that contradict the proposal's own rule ("Pure indirection is allowed only where enforcement is preserved"). Items 2B, 2C, 2E, and 2G have unresolved conditionals. These must be resolved to definitive postures.

8. **Token estimates:** The "~12,810 tokens across 15 Claude-facing files" and "~1,200-1,500 tokens recoverable" figures carry no measurement methodology. They should be tagged.

## Round 4 (gemini-3.1-pro)
The previous revision successfully integrated the accepted challenges, adding the required traceability table, rollout verification safeguards, and semantic clarifications. The structure is highly actionable and avoids hedge words. I have polished the execution language slightly to ensure the directives are absolute and the verification steps are strictly gated. No recommendations were removed; all 17 items across the 4 phases are preserved as explicit, executable directives.

## Round 5 (gpt-5.4)
The revision is materially stronger than a simple compression plan: it now distinguishes always-loaded vs conditional files, preserves inline summaries where co-loading is not guaranteed, reframes 1A as a semantic clarification, restores the explicit “Any listed anti-pattern detected ⇒ rewrite” enforcement trigger, and adds a concrete verification phase. Those changes correctly address the accepted challenges.

Remaining issues and refinements made in the revised document below:

1. **Challenge 6 needed one more step from proposal to file-level action.**  
   The current draft says workflow.md should defer to CLAUDE.md on skip conditions, but it presents this as part of 1C rather than making clear that this is a required file change. The revision makes that explicit.

2. **Some “zero governance impact” language was too absolute without preserving the stated condition.**  
   The proposal already correctly says non-weakening holds “provided Phase 4 verification passes.” The revision keeps that conditional consistently wherever needed, instead of implying unconditional certainty.

3. **Cross-reference enforcement posture needed slightly tighter wording.**  
   In a few places, “pure reference safe” or “inline summary retained” could still be read as editorial intent rather than merge criteria. The revision makes these implementation requirements, not just descriptions.

4. **Phase 4 was good but could be made more executable.**  
   The revised version turns Phase 4 into merge-blocking acceptance criteria with explicit outputs: a rule traceability matrix, a load audit, and a dangling-reference check.

5. **Flow improvement.**  
   The revised document keeps all recommendations but sharpens the order: problem → constraint → execution rule for cross-references → ambiguity fixes → deduplication with traceability → verbosity cuts → verification.

No verified operational measurements were removed. Estimated quantitative claims remain tagged as estimated.

## Round 6 (claude-opus-4-6)
The previous revision is strong. It addressed most challenges competently: the cross-reference traceability table (Challenge 1), the reframing of 1A (Challenge 2), Phase 4 verification (Challenge 3), the design.md anti-pattern trigger preservation (Challenge 4), the workflow.md deferral in 1C (Challenge 6), and the CLAUDE.md minimum-required vs. full-checklist distinction in 1B (Challenge 8).

**Remaining issues I'm fixing:**

1. **Challenge 1 (load semantics table) — incomplete coverage.** The traceability table covers Phase 2 items but omits Phase 1 cross-references. Items 1C and 1D introduce new "per CLAUDE.md" references from conditional files to CLAUDE.md. These need entries in the table. The table also lacks a row for 3B's design.md change, which isn't a cross-reference but should be noted as not introducing one.

2. **Challenge 2 (1A reframing) — good but the workflow.md and session-discipline.md alignment is vague.** The revision says they "align to this same three-step sequence" but doesn't specify the actual text changes for those files. This is a governance change proposal — it needs to be concrete.

3. **Challenge 3 (Phase 4) — solid but "attached to the PR or change record" is ambiguous.** I'll tighten the output requirements.

4. **Challenge 4 (design.md trigger) — well handled.** The "Any listed anti-pattern detected ⇒ rewrite" text is preserved. No changes needed.

5. **Challenge 6 (workflow.md explicit deferral) — partially addressed.** Item 1C says workflow.md changes to defer, but the actual text just says "Skip conditions for /challenge: per CLAUDE.md. Tier classification still governs review depth." This is adequate but could be slightly more explicit that CLAUDE.md is authoritative. I'll sharpen the wording.

6. **Challenge 8 (session-start list) — well handled in 1B.** The "Skipping the full checklist before planning is a violation, not an optimization" line is excellent. No changes needed.

7. **Structural issue:** The "Load Semantics Context" section and the traceability table are good but should also cover Phase 1 references for completeness. I'll extend the table.

8. **Minor:** The cross-reference rule stated in the Constraint section is good but should reference the traceability table as the enforcement mechanism.

9. **Phase 3B natural-language-routing.md and code-quality-detail.md deletions** — these remove preamble text that contains no cross-references and no normative rules, so they're clean. No issue.

10. **Token estimates** — already properly tagged as ESTIMATED. No change needed.

## Final Refined Document

# Proposal: Streamline BuildOS Rule Files

## Problem

BuildOS rule files (CLAUDE.md + 10 rule files + 4 reference files) contain duplication, ambiguity, and verbosity that reduces governance effectiveness:

1. **Same rules stated in multiple Claude-facing files** — wastes context tokens without increasing compliance. Research shows instruction compliance decreases as instruction count grows.
2. **Ambiguous or apparently conflicting statements** between files — forces Claude to reconcile timing, scope, or applicability across multiple instructions.
3. **Verbose explanations** where terse rules would carry the same directive — origin tags, preambles, over-explained rules.

Estimated total: ~12,810 tokens across 15 Claude-facing files [ESTIMATED: based on tokenizer counts of current file contents; methodology not documented]. ~1,200–1,500 tokens recoverable (~10–12%) with zero governance impact if and only if the non-weakening and reference-integrity checks in Phase 4 pass [ESTIMATED: sum of per-item estimates in Phases 2–3; actual recovery depends on final wording choices].

## Constraint

Same governance, same enforcement, same rules. This is compression, not reduction. No rules removed, no hooks changed, no enforcement weakened.

**Cross-reference rule:** If a proposed cross-reference would make a rule more context-dependent because the target file is not guaranteed to be loaded with the source, the source file must retain a one-line normative summary inline. Pure indirection is allowed only where co-loading is confirmed on the actual execution path. The Phase 2 traceability table and Phase 4 verification procedure are the enforcement mechanisms for this rule.

---

## Load Semantics Context

BuildOS files fall into two categories:

- **Always-loaded:** CLAUDE.md is injected into every Claude session automatically.
- **Conditional:** All other rule files (workflow.md, session-discipline.md, review-protocol.md, code-quality.md, security.md, bash-failures.md, design.md, etc.) are loaded when relevant to the task or explicitly referenced.

The critical enforcement boundary: references **from CLAUDE.md to conditional files** must retain the operative rule inline, because the target may not be loaded. References **from conditional files to CLAUDE.md** are safe because the target is always loaded. References **between conditional files** require case-by-case analysis; if co-loading is not guaranteed, the source must keep a one-line normative summary.

---

## Master Cross-Reference Traceability Table

Every cross-reference introduced or modified in this proposal is listed below with its required enforcement posture. This table covers Phases 1 and 2. Phase 3 items do not introduce cross-references (they compress text in place). Implement exactly as specified; if implementation diverges, keep the stronger inline text.

| Item | Source File | Target File | Source Load | Target Load | Co-Loading Guaranteed? | Required Enforcement Posture |
|---|---|---|---|---|---|---|
| **1A** | CLAUDE.md | workflow.md, session-discipline.md | Always | Conditional | No | **Inline normative text required in CLAUDE.md.** The three-step sequence is stated directly. Conditional files align to the same sequence independently. |
| **1B** | CLAUDE.md | workflow.md | Always | Conditional | No | **Inline summary + explicit escalation.** CLAUDE.md states the minimum required set and names the full checklist obligation. Skipping is a stated violation. |
| **1C** | review-protocol.md | CLAUDE.md | Conditional | Always | Yes | **Pure reference allowed.** Target is always loaded. |
| **1C** | workflow.md | CLAUDE.md | Conditional | Always | Yes | **Pure reference allowed.** Target is always loaded. |
| **1D** | review-protocol.md | CLAUDE.md | Conditional | Always | Yes | **Pure reference allowed.** Target is always loaded. |
| **2A** | CLAUDE.md | code-quality.md | Always | Conditional | No | **Inline summary required.** CLAUDE.md keeps the operative rule; reference adds detail only. |
| **2B** | session-discipline.md | review-protocol.md | Conditional | Conditional | No | **Inline summary required.** session-discipline.md keeps one-line directive: "Do not commit without the appropriate review." |
| **2C** | session-discipline.md | review-protocol.md | Conditional | Conditional | No | **Inline summary required.** session-discipline.md keeps its local addendum ("sanity-check data volumes"). |
| **2C** | workflow.md | review-protocol.md | Conditional | Conditional | No | **Inline summary required.** workflow.md keeps "Verify before done" as a one-line directive. |
| **2D** | workflow.md | CLAUDE.md | Conditional | Always | Yes | **Pure reference allowed.** Target is always loaded. |
| **2D** | review-protocol.md | CLAUDE.md | Conditional | Always | Yes | **Pure reference allowed.** Target is always loaded. |
| **2E** | workflow.md | bash-failures.md | Conditional | Conditional | No | **Inline summary required.** workflow.md keeps: "Never silently work around the same infrastructure failure twice." |
| **2F** | CLAUDE.md | security.md | Always | Conditional | No | **Inline summary required.** CLAUDE.md keeps the normative LLM boundary rule; reference adds detail only. |
| **2G** | CLAUDE.md | session-discipline.md | Always | Conditional | No | **Inline summary required.** CLAUDE.md keeps timing rule and artifact list. |
| **2G** | workflow.md | session-discipline.md | Conditional | Conditional | No | **Inline summary required.** workflow.md keeps "Document before implementation" directive. |

---

## Phase 1: Fix Ambiguity and Clarify Semantics (4 items)

### 1A. "Document before or after implementation?" (Semantic Clarification)

**Current state (sequence ambiguity across three files):**
- CLAUDE.md: "Update decisions.md **after** material decisions"
- session-discipline.md: "Every correction must be persisted **BEFORE** implementation"
- workflow.md: "Document first, execute second"

These three statements describe overlapping parts of the workflow but use different temporal anchors ("after," "before," "first"), creating ambiguity about the intended sequence. The risk is that Claude reads "after" in CLAUDE.md as "after implementation" rather than "after the decision is made, before implementing it." This is a semantic clarification to make the intended three-step sequence explicit, not a contradiction fix — the original authors likely intended the same sequence but expressed it from different vantage points.

**Required change — establish the explicit sequence: decide → document → implement.**

CLAUDE.md changes to:
> "Update decisions.md after making material decisions and before implementing them."

session-discipline.md changes to:
> "Persist corrections after deciding on them and before implementing them."

workflow.md changes to:
> "Decide, then document, then implement."

All three files now state the same three-step sequence independently, so the timing is unambiguous regardless of which files are loaded.

### 1B. "Which docs to read at session start?"

**Current state (different lists, unclear which is authoritative):**
- CLAUDE.md: "Read handoff.md and current-state.md before starting work. Read relevant lessons and decisions before touching risky areas."
- workflow.md: "read docs/project-prd.md + docs/project-map.md + docs/current-state.md + tasks/lessons.md (relevant domain) + tasks/session-log.md (last entry) before proposing any plan."

**Fix:** Distinguish **minimum required orientation** from the **mandatory full planning checklist**. CLAUDE.md is the always-loaded quick-start authority; its list is the minimum required set before any work begins, but the full checklist is mandatory before planning.

CLAUDE.md changes to:
> "Minimum required at session start: read handoff.md and current-state.md. These are mandatory before any work. Before proposing a plan, you must also complete the full orient-before-planning checklist in workflow.md (which includes project-prd.md, project-map.md, lessons.md, and session-log.md). Skipping the full checklist before planning is a violation, not an optimization."

This makes CLAUDE.md explicit: its list is the minimum-required set for orientation, and the workflow.md checklist is an additional mandatory gate before planning. Both obligations are stated directly in the always-loaded file.

### 1C. "When to skip /challenge?"

**Current state (inconsistent skip conditions across three files):**
- CLAUDE.md: "Skip both for: bugfixes, test-only changes, docs, `[TRIVIAL]` (<=2 files, no new abstractions, one-sentence scope)."
- review-protocol.md: "When to skip: Bugfixes, test additions, docs, trivial refactors -> `/plan --skip-challenge`."
- workflow.md: T2/standard tier implies challenge is skipped for bugfixes, small features, docs.

**Fix:** Canonical skip conditions live in CLAUDE.md (always loaded). Both review-protocol.md and workflow.md replace their local lists with explicit deferral to prevent future drift where someone edits one file's skip conditions without updating the others.

review-protocol.md changes to:
> "Skip conditions: defined in CLAUDE.md. CLAUDE.md is authoritative for skip-condition rules; do not maintain a separate list here."

workflow.md changes to:
> "Skip conditions for /challenge: defined authoritatively in CLAUDE.md. Tier classification still governs review depth."

### 1D. "Essential eight — 6 or 8 apply?"

**Current state (apparent contradiction):**
- CLAUDE.md: "6 of 8 apply to BuildOS" (strikes through approval gating, state machine validation, exactly-once scheduling)
- review-protocol.md: "The essential eight invariants apply to every change" (lists all 8, no strikethrough)

**Fix:** review-protocol.md changes to:
> "The essential eight invariants (6 applicable to BuildOS — see CLAUDE.md for applicability) guide every change. Add domain-specific invariants on top."

CLAUDE.md remains the applicability authority. review-protocol.md retains its role as an execution guide but no longer implies all 8 are active.

---

## Phase 2: Deduplicate Claude-Facing Files (7 duplications)

### 2A. Simplicity / no overengineering
- **Canonical:** code-quality.md
- **Cut from:** CLAUDE.md — remove elaboration paragraphs
- **Retained in CLAUDE.md:**
  > "### Simplicity is the override rule  
  > The simplest version wins unless there's evidence otherwise. No speculative abstraction. No premature generalization. See code-quality.md for specific constraints."

### 2B. "No commit without review"
- **Canonical:** review-protocol.md ("HARD RULE: No commit without the appropriate review.")
- **Keep in:** CLAUDE.md hard-rules list as a one-line bullet
- **Cut from:** session-discipline.md — remove the restated "Review requirement" paragraph
- **Retained in session-discipline.md:**
  > "Do not commit without the appropriate review. See review-protocol.md for review types and thresholds."

### 2C. Verify before done
- **Canonical:** review-protocol.md (Definition of Done section)
- **Keep in:** CLAUDE.md — "Prove it works. Tests, logs, evidence."
- **Cut from:** session-discipline.md — replace Verification section with:
  > "## Verification  
  > Prove it works before calling it done. See review-protocol.md Definition of Done. Additionally: sanity-check data volumes, not just success codes."
- **Cut from:** workflow.md — replace with:
  > "Verify before done. See review-protocol.md Definition of Done."

### 2D. Pipeline tiers (full table)
- **Canonical:** CLAUDE.md (always-loaded)
- **Cut from:** workflow.md — replace the full tier table with:
  > "Pipeline tiers: see CLAUDE.md. Decision logic follows:"
  then keep only workflow-specific routing guidance
- **Cut from:** review-protocol.md — replace "Typical paths by change type" with:
  > "Tier definitions and thresholds: see CLAUDE.md."

### 2E. Fix-forward rule
- **Canonical:** bash-failures.md
- **Cut from:** workflow.md — replace 8-line "Fix-Forward Rule" section with:
  > "## Fix-Forward Rule  
  > Never silently work around the same infrastructure failure twice. See bash-failures.md for the full fix-forward protocol."

### 2F. LLM boundary / model may decide
- **Canonical:** security.md
- **Cut from:** CLAUDE.md — remove expansion paragraphs
- **Retained in CLAUDE.md:**
  > "LLMs classify, summarize, and draft. Deterministic code performs state transitions. If the LLM can cause irreversible state changes, it must not be the actor. See security.md for the full boundary specification."

### 2G. Document results
- **Canonical:** session-discipline.md
- **Cut from:** CLAUDE.md — replace the current longer "Document results" section with:
  > "### Document results  
  > Record material decisions after deciding them and before implementing them. Update the appropriate session artifacts before ending work. See session-discipline.md for the full what-goes-where table."
- **Cut from:** workflow.md — replace "Document first, execute second" bullet with:
  > "Decide, then document, then implement. See session-discipline.md for destination rules."

---

## Phase 3: Tighten Verbosity

### 3A. Remove all origin tags (~50 tokens)
Delete lines matching `*Origin: ...*` from:
- code-quality.md
- bash-failures.md
- code-quality-detail.md
- skill-authoring.md

### 3B. Compress preambles (~100 tokens)

- **design.md:** Preserve the action trigger explicitly. Rewrite the preamble to:
  > "Watch for these anti-patterns. **Any listed anti-pattern detected ⇒ rewrite.**"

- **natural-language-routing.md:** Delete:
  > "Don't wait for the user to ask. Watch for these signals during a session and suggest the appropriate skill:"

- **code-quality-detail.md:** Delete:
  > "These rules apply when working in specific domains. They are NOT loaded by default..."

### 3C. Tighten over-explained rules (~150 tokens)

**security.md — allowlist check:**
From paragraph to:
> "Allowlist: `if allowlist is not None and value not in allowlist` — NOT `if allowlist and value...` (empty string and None bypass)."

**security.md — CSV formula injection:**
From paragraph to:
> "CSV formula injection: prefix cells starting with `=+\-@` with single quote, or use `csv.QUOTE_ALL`."

**orchestration.md — decomposition gate:**
Tighten to:
> "Count independent components. 3+: decompose (one agent per component, worktree isolation). 1–2: bypass. User says 'skip': bypass immediately."

**orchestration.md — file references:**
From anecdote to:
> "Worktree agent prompts: relative paths only (`src/file.py`, not `/home/.../src/file.py`). Absolute paths bypass isolation."

### 3D. Tighten compaction protocol in session-discipline.md (~40 tokens)
From 3 multi-sentence paragraphs to:
> "55%: write state to disk proactively. 55–70%: compact at natural breakpoint. 70%: hard compact immediately (write thoughts to disk first)."

### 3E. Tighten "Root Cause First" in workflow.md (~35 tokens)
Compress from 18 lines to ~8 lines:
- keep the 5 steps
- compress each to one line
- keep the anti-patterns list
- delete "The test" paragraph

### 3F. Tighten "How to Route" in natural-language-routing.md (~30 tokens)
Compress from 5 numbered principles to:
> "Match intent, not keywords. Invoke directly — don't explain the skill first. Chain skills automatically when one outputs another's input. One suggestion per pattern per session."

---

## Phase 4: Rollout Verification (Merge-Blocking Safeguard)

To guarantee zero governance impact, the person merging this change must execute the following checks. Do not merge until all four pass. If any check fails, revert the failing item to its pre-change text until the issue is resolved.

### 4A. Rule Traceability Matrix
For every touched normative rule, produce a source→canonical mapping showing:
- original file and section
- revised file and section
- whether the rule text is preserved inline, centralized, or split between inline summary + canonical detail
- confirmation that the rule's obligation, timing, and scope did not weaken

**Required output:** A completed rule traceability matrix, included in the PR description (not a separate document that can be skipped). One row per normative rule touched. Reviewer must sign off on each row.

### 4B. Context-Dependency / Load Audit
For every introduced cross-reference, verify the entries in the Master Cross-Reference Traceability Table:
- the source and target file load categories (always vs. conditional) match the actual system behavior
- the required enforcement posture (inline summary retained vs. pure reference) matches the implemented text
- no inline summary was accidentally omitted during editing

**Required output:** A checked copy of the Master Cross-Reference Traceability Table with pass/fail per row, included in the PR.

### 4C. Reference Integrity Check
For every new "See X.md" or "defined in X.md" reference:
- confirm the target file exists at the referenced path
- confirm the referenced section exists with matching heading text (where a section is named)
- confirm no renamed or removed section breaks the link

**Required output:** A reference integrity checklist covering every introduced reference, with pass/fail per reference.

### 4D. Non-Weakening Spot Check
For each touched file, manually verify at least one moved rule:
- the action directive still exists in the destination
- trigger conditions are unchanged
- the inline summary (where required) carries normative force, not just a pointer

**Required output:** One recorded spot-check result per touched file, identifying which rule was checked and confirming the three criteria above.

**Failure mode:** Any check failure blocks the merge for the affected item only. Items that pass may proceed independently.

---

## Expected Impact

- **Tokens recovered:** ~1,200–1,500 from Claude-facing files (~10–12%) [ESTIMATED: sum of per-item estimates; actual depends on final wording]
- **Ambiguities resolved:** 4 timing/applicability ambiguities that currently force Claude to reconcile multiple phrasings
- **Rules removed:** 0
- **Hooks changed:** 0
- **Enforcement weakened:** None, if and only if Phase 4 verification passes
- **Net effect:** Same governance, less noise, clearer signal
