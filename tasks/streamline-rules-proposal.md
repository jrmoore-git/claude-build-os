---
scope: "Streamline BuildOS rule files — eliminate duplication, resolve ambiguity, reduce verbosity"
surfaces_affected: "CLAUDE.md, .claude/rules/*.md, .claude/rules/reference/*.md"
review_tier: "challenge → refine"
---

# Proposal: Streamline BuildOS Rule Files

## Problem

BuildOS rule files (CLAUDE.md + 10 rule files + 4 reference files) contain duplication, ambiguity, and verbosity that reduces governance effectiveness:

1. **Same rules stated in multiple Claude-facing files** — wastes context tokens without increasing compliance. Research shows instruction compliance decreases as instruction count grows.
2. **Contradictory statements** between files — forces Claude to reconcile conflicting instructions.
3. **Verbose explanations** where terse rules would carry the same directive — origin tags, preambles, over-explained rules.

Estimated total: ~12,810 tokens across 15 Claude-facing files. ~1,200-1,500 tokens recoverable (~10-12%) with zero governance impact.

## Constraint

Same governance, same enforcement, same rules. This is compression, not reduction. No rules removed, no hooks changed, no enforcement weakened.

---

## Phase 1: Fix Ambiguity (4 contradictions)

### 1A. "Document before or after implementation?"

**Current state (contradiction):**
- CLAUDE.md: "Update decisions.md **after** material decisions"
- session-discipline.md: "Every correction must be persisted **BEFORE** implementation"
- workflow.md: "Document first, execute second"

**Fix:** Align all three to "before." CLAUDE.md line changes from "Update decisions.md after material decisions" to "Update decisions.md before implementing material decisions." The word "after" in CLAUDE.md is the outlier.

### 1B. "Which docs to read at session start?"

**Current state (different lists):**
- CLAUDE.md: "Read handoff.md and current-state.md before starting work. Read relevant lessons and decisions before touching risky areas."
- workflow.md: "read docs/project-prd.md + docs/project-map.md + docs/current-state.md + tasks/lessons.md (relevant domain) + tasks/session-log.md (last entry) before proposing any plan."

**Fix:** Canonical list lives in workflow.md (it's more complete). CLAUDE.md changes to: "Read handoff.md and current-state.md before starting work. See workflow.md for the full orient-before-planning checklist."

### 1C. "When to skip /challenge?"

**Current state (inconsistent skip conditions):**
- CLAUDE.md: "Skip both for: bugfixes, test-only changes, docs, `[TRIVIAL]` (<=2 files, no new abstractions, one-sentence scope)."
- review-protocol.md: "When to skip: Bugfixes, test additions, docs, trivial refactors -> `/plan --skip-challenge`."
- workflow.md: T2/standard tier implies challenge is skipped for bugfixes, small features, docs.

**Fix:** Canonical skip conditions live in CLAUDE.md (always loaded). review-protocol.md references CLAUDE.md for skip conditions instead of restating them. workflow.md tier table is compatible — no change needed.

### 1D. "Essential eight — 6 or 8 apply?"

**Current state (contradiction):**
- CLAUDE.md: "6 of 8 apply to BuildOS" (strikes through approval gating, state machine validation, exactly-once scheduling)
- review-protocol.md: "The essential eight invariants apply to every change" (lists all 8, no strikethrough)

**Fix:** review-protocol.md changes to: "The essential eight invariants (6 applicable to BuildOS — see CLAUDE.md) guide every change. Add domain-specific invariants on top."

---

## Phase 2: Deduplicate Claude-Facing Files (7 duplications)

For each, one file is designated canonical. The other file(s) replace the duplicated content with a one-line reference.

### 2A. Simplicity / no overengineering

- **Canonical:** code-quality.md (has the extra "don't add docstrings" bullet)
- **Cut from:** CLAUDE.md — replace 6-line "Simplicity is the override rule" section with: "### Simplicity is the override rule\nSee code-quality.md. The simplest version wins unless there's evidence otherwise."

### 2B. "No commit without review"

- **Canonical:** review-protocol.md ("HARD RULE: No commit without the appropriate review.")
- **Keep in:** CLAUDE.md hard-rules list (one-line bullet is fine as a headline)
- **Cut from:** session-discipline.md — remove the restated "Review requirement" paragraph; keep only the plan gate specifics that are unique to that section.

### 2C. Verify before done

- **Canonical:** review-protocol.md (Definition of Done section)
- **Keep in:** CLAUDE.md (one-liner: "Prove it works. Tests, logs, evidence.")
- **Cut from:** session-discipline.md — replace Verification section with: "## Verification\nSee review-protocol.md Definition of Done. Additionally: sanity-check data volumes, not just success codes."
- **Cut from:** workflow.md — replace line 3 with: "Verify before done — see review-protocol.md."

### 2D. Pipeline tiers (full table)

- **Canonical:** CLAUDE.md (always-loaded, appropriate for quick reference)
- **Cut from:** workflow.md — replace the full tier table with: "Pipeline tiers: see CLAUDE.md. Decision logic:" then keep only the workflow-specific guidance (when to enter plan mode, when to decompose, the /think and /elevate mode explanations).
- **Cut from:** review-protocol.md — replace "Typical paths by change type" with a reference to CLAUDE.md.

### 2E. Fix-forward rule

- **Canonical:** bash-failures.md (has hook enforcement, diagnostic sequences, prohibited patterns)
- **Cut from:** workflow.md — replace 8-line "Fix-Forward Rule" section with: "## Fix-Forward Rule\nSee bash-failures.md. Never silently work around the same infrastructure failure twice."

### 2F. LLM boundary / model may decide

- **Canonical:** security.md (more complete: covers invocation layer, structured output validation, the test)
- **Cut from:** CLAUDE.md — keep the one-liner principle ("LLMs classify, summarize, and draft. Deterministic code performs state transitions. If the LLM can cause irreversible state changes, it must not be the actor.") but remove the section heading expansion that security.md covers better.

### 2G. Document results

- **Canonical:** session-discipline.md (the "Document First, Execute Second" section)
- **Cut from:** CLAUDE.md — replace "Document results" section with: "### Document results\nUpdate decisions.md, lessons.md, and handoff.md before implementing. See session-discipline.md for the full what-goes-where table."
- **Cut from:** workflow.md — replace "Document first, execute second" bullet with reference to session-discipline.md.

---

## Phase 3: Tighten Verbosity

### 3A. Remove all origin tags (~50 tokens)

Delete lines matching `*Origin: ...*` from: code-quality.md, bash-failures.md, code-quality-detail.md, skill-authoring.md. These explain history, not rules.

### 3B. Remove preambles before self-explanatory sections (~100 tokens)

- design.md: Delete "Watch for these anti-patterns in generated UI and content. Any match = rewrite."
- natural-language-routing.md: Delete "Don't wait for the user to ask. Watch for these signals during a session and suggest the appropriate skill:"
- code-quality-detail.md: Delete "These rules apply when working in specific domains. They are NOT loaded by default..."

### 3C. Tighten over-explained rules (~150 tokens)

**security.md — allowlist check:** From paragraph to: "Allowlist: `if allowlist is not None and value not in allowlist` — NOT `if allowlist and value...` (empty string and None bypass)."

**security.md — CSV formula injection:** From paragraph to: "CSV formula injection: prefix cells starting with `=+\-@` with single quote, or use `csv.QUOTE_ALL`."

**orchestration.md — decomposition gate:** Tighten the 4-step explanation to: "Count independent components. 3+: decompose (one agent per component, worktree isolation). 1-2: bypass. User says 'skip': bypass immediately."

**orchestration.md — file references:** From anecdote to: "Worktree agent prompts: relative paths only (`src/file.py`, not `/home/.../src/file.py`). Absolute paths bypass isolation."

### 3D. Tighten compaction protocol in session-discipline.md (~40 tokens)

From 3 multi-sentence paragraphs to: "55%: write state to disk proactively. 55-70%: compact at natural breakpoint. 70%: hard compact immediately (write thoughts to disk first)."

### 3E. Tighten "Root Cause First" in workflow.md (~35 tokens)

From 18 lines to ~8 lines: keep the 5 steps but compress each to one line. Keep the anti-patterns list (it's high-value). Cut "The test" paragraph — the anti-patterns already make the point.

### 3F. Tighten "How to Route" in natural-language-routing.md (~30 tokens)

From 5 numbered principles to: "Match intent, not keywords. Invoke directly — don't explain the skill first. Chain skills automatically when one outputs another's input. One suggestion per pattern per session."

---

## Expected Impact

- **Tokens recovered:** ~1,200-1,500 from Claude-facing files (~10-12%)
- **Ambiguities resolved:** 4 contradictions that currently force Claude to reconcile conflicting instructions
- **Rules removed:** 0
- **Hooks changed:** 0
- **Enforcement weakened:** None
- **Net effect:** Same governance, less noise, clearer signal
