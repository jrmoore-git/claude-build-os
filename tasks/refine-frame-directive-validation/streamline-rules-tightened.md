---
debate_id: streamline-rules-tightened
created: 2026-04-18T09:56:39-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# streamline-rules-tightened — Refined Document

## Round 1 (gemini-3.1-pro)
The document is exceptionally strong. It identifies a clear problem (context bloat and instruction conflict) and provides a highly specific, file-by-file execution plan to resolve it without degrading governance. 

### Frame Check
Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The revision is already strong: it preserves the original recommendation structure, makes the actions concrete, and keeps the scope constrained to compression rather than policy change. The main remaining issues are:

- A few recommendations imply “identical governance” while also changing which file is canonical. That can preserve intent, but only if cross-references remain explicit enough that no requirement becomes easier to miss. I tightened wording to make “replace duplicated text with direct references” operational rather than interpretive.
- The proposal uses exact contradiction counts and token-savings ranges without explaining their basis. Because those figures are already in the document, I preserved them, but I tightened nearby language so the recommendation does not depend on precision beyond what the text supports.
- Phase 3 mixed style edits with governance-sensitive compression. I kept all entries but clarified that compaction must preserve normative content and examples where those examples carry enforcement meaning.
- Some phrasing was slightly repetitive or soft around canonical-source selection; I simplified it for faster execution.

### Frame Check
Frame check: document's frame is sound.

## Final Refined Document

# Proposal: Streamline BuildOS Rule Files

## Problem

BuildOS rule files (`CLAUDE.md`, 10 rule files, and 4 reference files) contain duplication, ambiguity, and verbosity that reduce governance efficiency:

1. **Instruction conflict:** Contradictory statements across files force the model to reconcile competing directives, which weakens compliance.
2. **Context dilution:** Repeating the same rule across multiple files consumes context tokens without adding enforcement value.
3. **Verbose explanations:** Origin tags, preambles, and over-explained rules use tokens that should be reserved for short, actionable directives.

Current load: ~12,810 tokens across 15 Claude-facing files.  
Opportunity: Recover ~1,200-1,500 tokens (~10-12%) with no intended governance change.

## Constraint

Maintain the same governance and enforcement. This is a compression and canonicalization pass, not a policy reduction:

- Zero rules removed
- Zero hooks changed
- Zero enforcement weakened

Where duplicate text is removed, the replacement must be an explicit reference to the canonical rule file so the requirement remains present and discoverable.

---

## Phase 1: Resolve Ambiguity (4 Contradictions)

Execute these standardizations to eliminate conflicting directives.

### 1A. Documentation Timing
**Current state:** `CLAUDE.md` says "after"; `session-discipline.md` and `workflow.md` say "before".  
**Action:** Standardize on "before." Change `CLAUDE.md` to:  
"Update `decisions.md` before implementing material decisions."

### 1B. Session Start Reading List
**Current state:** `CLAUDE.md` and `workflow.md` define different required reading lists.  
**Action:** Make `workflow.md` the canonical list. Change `CLAUDE.md` to:  
"Read `handoff.md` and `current-state.md` before starting work. See `workflow.md` for the full orient-before-planning checklist."

### 1C. Challenge Skip Conditions
**Current state:** `CLAUDE.md`, `review-protocol.md`, and `workflow.md` define inconsistent skip conditions.  
**Action:** Make `CLAUDE.md` the canonical source. Update `review-protocol.md` to reference `CLAUDE.md` for skip conditions instead of restating them. Keep the `workflow.md` tier table unchanged because it remains compatible.

### 1D. Essential Eight Invariants
**Current state:** `CLAUDE.md` strikes through two invariants; `review-protocol.md` enforces all eight.  
**Action:** Update `review-protocol.md` to:  
"The essential eight invariants (6 applicable to BuildOS — see `CLAUDE.md`) guide every change. Add domain-specific invariants on top."

---

## Phase 2: Deduplicate Claude-Facing Files (7 Duplications)

Assign one canonical file per rule. In secondary files, replace duplicated text with a one-line directive that points to the canonical source.

### 2A. Simplicity / No Overengineering
- **Canonical:** `code-quality.md`
- **Action:** Replace the 6-line "Simplicity is the override rule" section in `CLAUDE.md` with:  
  "### Simplicity is the override rule  
  See `code-quality.md`. The simplest version wins unless there's evidence otherwise."

### 2B. Commit Review Requirement
- **Canonical:** `review-protocol.md`
- **Action:** Keep the one-line bullet in `CLAUDE.md`. Remove the redundant "Review requirement" paragraph from `session-discipline.md`, preserving only the plan-gate specifics that are unique to that file.

### 2C. Verify Before Done
- **Canonical:** `review-protocol.md` under Definition of Done
- **Action:** Keep the one-line requirement in `CLAUDE.md`. Replace the Verification section in `session-discipline.md` with:  
  "## Verification  
  See `review-protocol.md` Definition of Done. Additionally: sanity-check data volumes, not just success codes."  
  Replace line 3 in `workflow.md` with:  
  "Verify before done — see `review-protocol.md`."

### 2D. Pipeline Tiers Table
- **Canonical:** `CLAUDE.md`
- **Action:** Replace the full tier table in `workflow.md` with:  
  "Pipeline tiers: see `CLAUDE.md`. Decision logic:"  
  Retain only workflow-specific guidance below that line. Replace "Typical paths by change type" in `review-protocol.md` with a reference to `CLAUDE.md`.

### 2E. Fix-Forward Rule
- **Canonical:** `bash-failures.md`
- **Action:** Replace the 8-line "Fix-Forward Rule" section in `workflow.md` with:  
  "## Fix-Forward Rule  
  See `bash-failures.md`. Never silently work around the same infrastructure failure twice."

### 2F. LLM Boundary
- **Canonical:** `security.md`
- **Action:** Keep the one-line principle in `CLAUDE.md` ("LLMs classify, summarize, and draft..."). Remove the expanded section text and defer to `security.md` for the full rule.

### 2G. Document Results
- **Canonical:** `session-discipline.md` under "Document First, Execute Second"
- **Action:** Replace the "Document results" section in `CLAUDE.md` with:  
  "### Document results  
  Update `decisions.md`, `lessons.md`, and `handoff.md` before implementing. See `session-discipline.md` for the full what-goes-where table."  
  Replace the "Document first, execute second" bullet in `workflow.md` with a reference to `session-discipline.md`.

---

## Phase 3: Tighten Verbosity

Apply the following compactions to recover tokens without changing rule meaning.

### 3A. Strip Origin Tags
Remove all lines matching `*Origin: ...*` from:
- `code-quality.md`
- `bash-failures.md`
- `code-quality-detail.md`
- `skill-authoring.md`

### 3B. Strip Preambles
Remove introductory filler text that adds no rule content:

- `design.md`: Delete "Watch for these anti-patterns in generated UI and content. Any match = rewrite."
- `natural-language-routing.md`: Delete "Don't wait for the user to ask. Watch for these signals during a session and suggest the appropriate skill:"
- `code-quality-detail.md`: Delete "These rules apply when working in specific domains. They are NOT loaded by default..."

### 3C. Compress Over-Explained Rules
Rewrite these sections to the following short forms while preserving the enforcement meaning:

- **`security.md` (Allowlist):**  
  "Allowlist: `if allowlist is not None and value not in allowlist` — NOT `if allowlist and value...` (empty string and None bypass)."

- **`security.md` (CSV Injection):**  
  "CSV formula injection: prefix cells starting with `=+\-@` with single quote, or use `csv.QUOTE_ALL`."

- **`orchestration.md` (Decomposition):**  
  "Count independent components. 3+: decompose (one agent per component, worktree isolation). 1-2: bypass. User says 'skip': bypass immediately."

- **`orchestration.md` (File References):**  
  "Worktree agent prompts: relative paths only (`src/file.py`, not `/home/.../src/file.py`). Absolute paths bypass isolation."

### 3D. Compress Compaction Protocol
In `session-discipline.md`, reduce three paragraphs to:  
"55%: write state to disk proactively. 55-70%: compact at natural breakpoint. 70%: hard compact immediately (write thoughts to disk first)."

### 3E. Compress Root Cause First
In `workflow.md`, reduce the 18-line section to about 8 lines:
- compress the five steps to one line each
- keep the anti-patterns list intact
- delete "The test" paragraph

### 3F. Compress Routing Principles
In `natural-language-routing.md`, reduce the five numbered principles to:  
"Match intent, not keywords. Invoke directly — don't explain the skill first. Chain skills automatically when one outputs another's input. One suggestion per pattern per session."

---

## Expected Impact

- **Tokens recovered:** ~1,200-1,500 from Claude-facing files (~10-12%)
- **Ambiguities resolved:** 4 direct contradictions eliminated
- **Rules removed:** 0
- **Hooks changed:** 0
- **Enforcement weakened:** None

## Success Criteria

The change is complete only if all of the following are true:

1. Every duplicated rule now has exactly one canonical source.
2. Every secondary mention is replaced by an explicit reference to that canonical source.
3. No file retains contradictory wording on documentation timing, reading requirements, skip conditions, or invariant count.
4. All Phase 3 compressions preserve the same normative instruction, examples, and enforcement behavior.
5. Total Claude-facing token load decreases materially from the current ~12,810-token baseline.
