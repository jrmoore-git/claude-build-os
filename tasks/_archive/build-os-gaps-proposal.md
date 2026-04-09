# Proposal: Recover Lost Nuggets from Original Docs

**Author:** Claude Opus (Round 1)
**Date:** 2026-03-13
**Debate type:** Architecture (3 rounds)
**Scope:** Evaluate 10 missing concepts and 4 thinned concepts identified by an audit comparing Justin's 4 original source docs against the published Build OS repo. All proposed fixes are edits to existing files — no new docs except one small template.

---

## Context

The Build OS repo (github.com/jrmoore-git/claude-build-os, 23 files) was published after two cross-model debates validated the 4-doc structure and a third debate validated 4 additions. A post-publication audit compared the 4 original source documents (Overview, Team Playbook, Operating Reference, CLAUDE Kernel — ~1,600 lines total) against the published repo and found concepts that were lost in translation.

The repo adequately covers ~35 major concepts. The audit identified 10 missing items and 4 significantly thinned items worth recovering.

---

## Proposed Fixes

### Fix 1: Add the 63x token reduction example
**Where:** Build OS Part IX (Patterns Worth Knowing), as a new subsection after "The LLM Boundary in Practice"
**What:** One paragraph: "Never trust a default response shape on a cost-sensitive path. In one case, extracting plain text instead of passing raw connector output cut the payload from roughly 582K tokens to about 9K — a 63x difference for the same data. Strip to what the model needs deterministically before it reaches the prompt."
**Why it matters:** The most concrete illustration of "disk over context" as an architectural practice, with a memorable quantitative example.

### Fix 2: Add the promotion gating criterion
**Where:** Build OS Part V (Enforcement Ladder), after "Test your instructions"
**What:** One sentence added: "Before promoting a lesson to a `.claude/rules/` file, state how you would catch a violation. If you cannot describe a concrete test, the rule belongs in `lessons.md` until you can — it is advisory text in a better location, not enforced governance."
**Also:** Add to the lessons template promotion section.
**Why it matters:** Turns "promote lessons to rules" from a vague suggestion into a concrete decision filter.

### Fix 3: Add "Metrics require time bounds"
**Where:** Build OS Part IX (Patterns Worth Knowing), as a one-line subsection
**What:** "A number without a date range, recency context, and source is an incomplete finding. Do not present or accept metrics — cost figures, approval rates, token counts — that lack all three."
**Why it matters:** Prevents an entire class of misleading audit and cost findings. Originally Kernel rule 18.

### Fix 4: Add "Review gates bind to the unit of change"
**Where:** Build OS Part VII (Review and Testing), after the review order section
**What:** One paragraph: "A review written earlier does not gate later commits automatically. If the code changed after the review, the gate is stale. Use commit hashes or timestamps when you need a real review boundary."
**Also:** Add to the review-protocol template.
**Why it matters:** Prevents teams from treating a morning review as a blanket approval for afternoon commits.

### Fix 5: Add CLAUDE.md length discipline
**Where:** Build OS Part III (File System), in the "What goes where" area; also in the CLAUDE.md starter template
**What:** In Build OS: "Keep CLAUDE.md short — it loads into every session on every turn and consumes context budget. A 200-line CLAUDE.md costs ~3K tokens per turn whether or not those rules are relevant. Put conditional rules in `.claude/rules/` files instead. CLAUDE.md should contain only rules that apply to every task in every session."
In CLAUDE.md template: Add a comment at the top: `<!-- Keep this file short. It loads on every turn and consumes context. Move conditional rules to .claude/rules/ files. -->`
**Why it matters:** The most common failure mode for teams adopting the framework — they dump everything into CLAUDE.md.

### Fix 6: Add the $1,949 limits-in-documentation story
**Where:** Build OS Part IX (Patterns Worth Knowing), integrated into the existing "The $724 Day" story as a follow-up paragraph
**What:** "That lesson had a sequel. A post-meeting skill had a documented 10-run daily cap in the routing guide. The cap was never enforced in code. It accumulated $1,949 in eleven days. A limit that exists only in documentation is advisory text with a number in it — it constrains nothing."
**Why it matters:** Distinct from the $724 routing story. This teaches that documented limits without code enforcement are not limits.

### Fix 7: Add "why verbatim" explanation for Anthropic language
**Where:** Build OS Part I (Philosophy), section 5 "Simplicity is risk control"
**What:** Add one sentence after the verbatim quote: "Use this language verbatim rather than paraphrasing — the model responds to these exact phrases more reliably than to rewrites, because it was trained on them."
**Why it matters:** The mechanism that convinces people to actually copy the text instead of "putting it in their own words."

### Fix 8: Add toolbelt audit as a practice
**Where:** Build OS Part IX (Patterns Worth Knowing), as a short subsection
**What:** "Periodically audit your system by mapping each operation to one of two buckets: deterministic code or LLM reasoning. The dangerous gaps are where the LLM is discovering, constructing, or guessing data that code should have fetched and validated first. This is a maintenance practice, not a one-time exercise."
**Why it matters:** A concrete, repeatable activity. Currently the repo describes the LLM boundary but doesn't tell teams to actively audit for violations.

### Fix 9: Move second-violation promotion trigger to Build OS
**Where:** Build OS Part V (Enforcement Ladder), in the promotion lifecycle section
**What:** Add: "A lesson violated for the second time should be promoted immediately. A second entry for the same pattern is evidence that Level 1 doesn't work."
**Currently:** Only in Advanced Patterns §8, which many users won't read.
**Why it matters:** This is the single most actionable trigger for the promotion system.

### Fix 10: Add project-map.md template
**Where:** New template at `templates/project-map.md` (~15 lines); add to Build OS file system tree and bootstrap checklist (Tier 1+)
**What:** A template for mapping systems, workstreams, key docs, and active areas. Not a PRD (what you're building) — a map (where things are and how they connect).
**Why it matters:** Large projects need navigation. The PRD describes intent; the project map describes structure. The original docs used both.

### Fix 11 (thinned): Strengthen compaction in CLAUDE.md template
**Where:** CLAUDE.md starter template, add as a commented rule
**What:** Add: `<!-- Optional but recommended: --> Use /compact at 50-70% context. Long sessions silently degrade quality.`
**Why it matters:** Currently only in Survival Basics. Tier 0 users who never read Survival Basics won't know about compaction.

### Fix 12 (thinned): Add "why verbatim" to recall command context
**Where:** No change needed — fix 7 covers this in the Build OS. The recall command appropriately stays mechanical.

### Fix 13 (thinned): Add research as distinct from planning
**Where:** Build OS Part IV (Operations), in the engineering operations table
**What:** Add "Research" as a distinct operation: "Read the real system before proposing changes. Research may be brief but ensures Claude inspects rather than assumes."
**Also:** Update the /plan command Phase 1 header from "Research" to clarify: "Research the system BEFORE planning. You might research without planning (for simple tasks in unfamiliar code), but never plan without researching."
**Why it matters:** Research and planning are distinct decisions with distinct triggers.

### Fix 14 (thinned): Surface PRD reconciliation three states in session loop
**Where:** Build OS Part IV, session loop step 6 (Sync)
**What:** Expand step 6: "**Sync** — update PRD and rules if behavior changed. Every session should end in one of three states: (1) no spec change — implementation matched the PRD, (2) approved delta — behavior changed and PRD was updated, (3) open question — behavior proposed but PRD awaits approval."
**Why it matters:** Forces a classification that prevents spec drift.

---

## What the challengers should evaluate

1. **Volume:** Are 14 fixes too many changes for one pass? Should they be batched?
2. **Placement:** Is each fix going to the right location? Does it respect topic ownership?
3. **Necessity:** Are all 14 genuinely needed, or are some already adequately implied?
4. **Weight:** Do any fixes add too much text to files that should stay lean?
5. **Regression risk:** Do any fixes reintroduce duplication that the prior debate eliminated?
