# Resolution: Recover Lost Nuggets from Original Docs

**Author:** Claude Opus (Round 3)
**Date:** 2026-03-13
**Responding to:** Challenger A (12 challenges, 6 MATERIAL) + Challenger B (3 challenges, 2 MATERIAL)

---

## Responses to Challenger A

### 1. [ASSUMPTION] [MATERIAL]: Not all "lost" items deserve reinstatement

**COMPROMISE.** Fair point. "Lost in translation" is not the same as "should be reinstated." I'll gate each fix by impact, not provenance. Cuts below.

### 2. [RISK] [MATERIAL]: 14 edits in one pass creates regression risk

**CONCEDE.** The revised plan below reduces to 10 edits (dropping 4 items) and groups them by file so each file is touched once. No new docs. Acceptance criteria: each edit must be additive (no existing content removed or reworded).

### 3. [ALTERNATIVE] [MATERIAL]: Embed only highest-signal items, not all anecdotes

**COMPROMISE.** The revised plan drops Fix 12 (research vs. planning — wording refinement, not missing concept) and Fix 10 (project-map.md — see Challenger B response). The remaining items are either operational criteria (promotion gating, review staleness, metrics bounds) or concrete examples that teach architectural principles (token reduction, cost limits). These belong in the mainline docs, not an appendix.

### 4. [OVER-ENGINEERED] [ADVISORY]: project-map.md may be premature

**CONCEDE.** Both challengers raised this. Dropping Fix 10 entirely. Teams that need a project map will create one organically.

### 5. [ASSUMPTION] [MATERIAL]: Fix 7 makes an unverified claim about training

**CONCEDE.** The challenger is right — "trained on them" is a mechanistic claim I can't verify. Revised wording: "Use this language verbatim rather than paraphrasing — in practice, Claude responds to these exact phrases more reliably than to rewrites."

### 6. [UNDER-ENGINEERED] [MATERIAL]: Fix 3 (metrics require time bounds) needs scope

**COMPROMISE.** Add scope: "This applies to any finding presented in an audit, review, cost report, or status update. Ad hoc conversation is exempt." Add one example: "Wrong: 'Daily cost is $488.' Right: 'Daily cost for March 1-7 (measured March 8, source: Postgres spend logs): $488.'"

### 7. [RISK] [MATERIAL]: Fix 5 could fragment governance

**COMPROMISE.** The challenger is right that pushing everything to `.claude/rules/` creates discoverability problems. Revised Fix 5: state the principle (CLAUDE.md loads every turn, keep it to universal rules) but add: "The tradeoff: rules in `.claude/rules/` only load when the matcher triggers. Rules that must apply to every task regardless of context belong in CLAUDE.md even at the cost of tokens. Rules that apply only to specific domains (security, auth, deployment) belong in scoped files."

### 8. [ALTERNATIVE] [ADVISORY]: Promotion should consider severity, not just frequency

**CONCEDE.** Already addressed — the Build OS has "escalation speed matches blast radius" which covers severity-based promotion. Fix 9 will reference that section explicitly.

### 9. [RISK] [MATERIAL]: Fix 4 (review staleness) is under-specified

**COMPROMISE.** The challenger wants a precise boundary rule. That's over-engineering for a general framework — different teams have different workflows. Revised: keep the principle ("review gates bind to the unit of change") and add: "At minimum, a review is stale if any file it covered has been modified since the review was written."

### 10. [OVER-ENGINEERED] [ADVISORY]: Too many war stories

**REBUT.** The stories are the most-cited part of the original docs. Justin's daughter specifically called them "nuggets of gold." The $1,949 story teaches a distinct lesson from the $724 story: routing vs. enforcement. Both stay, but Fix 6 integrates into the existing $724 story section rather than creating a new one.

### 11. [UNDER-ENGINEERED] [MATERIAL]: Fix 11 (compaction in CLAUDE.md) needs context

**CONCEDE on placement.** Both challengers flagged that HTML comments in CLAUDE.md consume tokens. Revised: remove the HTML comment from the CLAUDE.md template. Instead, add compaction guidance to the Build OS Part X (Survival Basics) with a note: "Consider adding '/compact at 50-70% context' to your CLAUDE.md if your team consistently hits context limits." The guidance exists; teams opt in.

### 12. [ASSUMPTION] [ADVISORY]: Fix 13 (research vs. planning) may not be needed

**CONCEDE.** Dropping Fix 13. The /plan command already has Phase 1: Research. The distinction exists; it's just not elevated to a separate concept. That's fine.

---

## Responses to Challenger B

### 1. [RISK] [MATERIAL]: HTML comments in CLAUDE.md consume tokens

**CONCEDE.** Good catch. No HTML comments added to CLAUDE.md template. Fix 5 will add length guidance to the Build OS only. Fix 11 drops the CLAUDE.md template edit.

### 2. [OVER-ENGINEERED] [MATERIAL]: project-map.md is unnecessary

**CONCEDE.** Same conclusion as Challenger A. Fix 10 dropped.

### 3. [UNDER-ENGINEERED] [ADVISORY]: "Periodically audit" needs a trigger

**COMPROMISE.** Add a concrete trigger: "Run a toolbelt audit when adding a new integration, after any security review, or quarterly for production systems."

---

## Revised Plan: 10 Edits to 4 Files

### File 1: `docs/the-build-os.md` (6 edits)

**Edit 1a — Part I, section 5:** Add after the verbatim quote: "Use this language verbatim rather than paraphrasing — in practice, Claude responds to these exact phrases more reliably than to rewrites."

**Edit 1b — Part III (File System):** Add after "What goes where" table: "Keep CLAUDE.md short — it loads into every session on every turn and consumes context budget. Put only rules that apply to every task in every session. The tradeoff: rules in `.claude/rules/` only load when the matcher triggers. Rules that must apply to every task belong in CLAUDE.md. Rules that apply only to specific domains (security, auth, deployment) belong in scoped files."

**Edit 1c — Part V (Enforcement Ladder):** Add after "Test your instructions": "Before promoting a lesson to a `.claude/rules/` file, state how you would catch a violation. If you cannot describe a concrete test, the rule belongs in `lessons.md` until you can — it is advisory text in a better location, not enforced governance."

**Edit 1d — Part V (Promotion lifecycle):** Add: "A lesson violated for the second time should be promoted immediately. A second entry for the same pattern is evidence that Level 1 doesn't work. For high-blast-radius failures, promote after one violation (see escalation speed above)."

**Edit 1e — Part VII (Review and Testing):** Add after review order: "A review written earlier does not gate later commits automatically. If any file the review covered has been modified since the review was written, the gate is stale. Re-review after significant changes."

**Edit 1f — Part IX (Patterns Worth Knowing):** Add three items:
- After "The LLM Boundary in Practice": "Never trust a default response shape on a cost-sensitive path. In one case, extracting plain text instead of passing raw connector output cut the payload from 582K tokens to 9K — a 63x reduction for the same data. Strip to what the model needs deterministically before it reaches the prompt."
- Integrate into "$724 Day" story: "That lesson had a sequel. A post-meeting skill had a documented 10-run daily cap. The cap was never enforced in code. It burned $1,949 in eleven days. A limit that exists only in documentation constrains nothing."
- New subsection "Toolbelt audit": "Periodically audit your system by mapping each operation to deterministic code or LLM reasoning. The dangerous gaps are where the LLM is discovering or guessing data that code should have fetched. Run this audit when adding a new integration, after security reviews, or quarterly for production systems."
- New subsection "Metrics require time bounds": "A number without a date range, recency context, and source is an incomplete finding. This applies to audits, reviews, cost reports, and status updates. Wrong: 'Daily cost is $488.' Right: 'Daily cost for March 1–7 (measured March 8, source: Postgres spend logs): $488.'"

### File 2: `docs/advanced-patterns.md` (1 edit)

**Edit 2a — Section 8 (Institutional Memory):** Add PRD reconciliation three states to the existing section (already partially there, just needs the explicit "every session ends in one of three states" framing surfaced more prominently).

### File 3: `templates/review-protocol.md` (1 edit)

**Edit 3a:** Add after the review order: "A review is only valid for the code it reviewed. If any covered file has been modified since the review, re-review before committing."

### File 4: `templates/lessons.md` (1 edit)

**Edit 4a:** Add to the promotion section: "Before promoting a lesson, state how you would catch a violation of the resulting rule. If you can't describe a concrete test, the lesson isn't ready for promotion."

### Dropped from original proposal:
- ~~Fix 10: project-map.md template~~ — both challengers: over-engineered
- ~~Fix 11: HTML comment in CLAUDE.md~~ — both challengers: consumes tokens
- ~~Fix 12: "why verbatim" in recall command~~ — already covered by Fix 7
- ~~Fix 13: research vs. planning distinction~~ — Challenger A: already adequate
