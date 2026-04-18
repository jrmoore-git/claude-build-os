---
debate_id: streamline-rules-v4
created: 2026-04-18T11:23:24-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# streamline-rules-v4 — Refined Document

## Round 1 (gemini-3.1-pro)
The document is exceptionally strong. It identifies specific contradictions, provides exact file paths, quotes the current state, and writes the literal replacement text. It understands the difference between reducing rules (which weakens governance) and compressing text (which improves LLM adherence). 

No frame defects were found. The document is highly executable. Minor edits were made to standardize the formatting of the actions (using consistent "Action:" prefixes) and to ensure the imperative mood is used throughout.

### Frame Check
Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The proposal is already strong: it is concrete, preserves governance intent, and specifies exactly what to change file-by-file. The main improvements needed were:
- tighten a few claims that were presented as certain without direct evidence in the document,
- make the execution standard more explicit so “same governance” is verifiable after edits,
- improve flow by separating contradictions, deduplication, and terseness from the validation criteria.

I did not weaken any recommendation. I preserved all original action items and made the acceptance criteria sharper.

### Frame Check
- Unstated load-bearing assumption: The proposal assumes the cited files are all Claude-facing at runtime and that token savings in those files materially affect model behavior. If that assumption is false, the compression rationale weakens. This cannot be fully resolved from the document alone.

## Final Refined Document

# Proposal: Streamline BuildOS Rule Files

## Problem

BuildOS rule files (`CLAUDE.md` + 10 rule files + 4 reference files) contain duplication, ambiguity, and verbosity that reduce governance effectiveness:

1. **Diluted Context:** Repeating the same rules across multiple Claude-facing files consumes context without adding enforcement. The proposal assumes fewer repeated instructions improves instruction clarity; that behavioral effect is plausible but not measured in this document.
2. **Contradictions:** Conflicting statements between files force the model to reconcile instructions at runtime, which creates avoidable ambiguity.
3. **Verbosity:** Explanations such as origin tags, preambles, and over-explained rules obscure the operative directive.

Current footprint: ~12,810 tokens across 15 Claude-facing files.  
Recoverable footprint: ~1,200-1,500 tokens (~10-12%).  
- EVIDENCED: current footprint and recoverable footprint are stated in the proposal text.

## Constraint

Same governance, same enforcement, same rules. This is compression, not reduction.

- No rules removed.
- No hooks changed.
- No enforcement weakened.
- Canonicalization is allowed only when the canonical file remains Claude-facing or the replaced text becomes a direct reference to an always-available canonical source.
- Every removed duplicate must map to an existing canonical rule with unchanged normative meaning.

## Phase 1: Fix Ambiguity (4 contradictions)

### 1A. Document before or after implementation?

**Current state (contradiction):**
- `CLAUDE.md`: "Update decisions.md **after** material decisions"
- `session-discipline.md`: "Every correction must be persisted **BEFORE** implementation"
- `workflow.md`: "Document first, execute second"

**Action:** Align all three to **before**.

Change `CLAUDE.md` to:
> "Update decisions.md before implementing material decisions."

### 1B. Which docs to read at session start?

**Current state (different lists):**
- `CLAUDE.md`: "Read handoff.md and current-state.md before starting work. Read relevant lessons and decisions before touching risky areas."
- `workflow.md`: "read docs/project-prd.md + docs/project-map.md + docs/current-state.md + tasks/lessons.md (relevant domain) + tasks/session-log.md (last entry) before proposing any plan."

**Action:** Make `workflow.md` the canonical list.

Change `CLAUDE.md` to:
> "Read handoff.md and current-state.md before starting work. See workflow.md for the full orient-before-planning checklist."

### 1C. When to skip `/challenge`?

**Current state (inconsistent skip conditions):**
- `CLAUDE.md`: "Skip both for: bugfixes, test-only changes, docs, `[TRIVIAL]` (<=2 files, no new abstractions, one-sentence scope)."
- `review-protocol.md`: "When to skip: Bugfixes, test additions, docs, trivial refactors -> `/plan --skip-challenge`."
- `workflow.md`: T2/standard tier implies challenge is skipped for bugfixes, small features, docs.

**Action:** Make `CLAUDE.md` the canonical source because it is always loaded.

Update `review-protocol.md` to reference `CLAUDE.md` for skip conditions instead of restating them. Leave `workflow.md` unchanged because its tier table is compatible.

### 1D. Essential eight — 6 or 8 apply?

**Current state (contradiction):**
- `CLAUDE.md`: "6 of 8 apply to BuildOS" (strikes through approval gating, state machine validation, exactly-once scheduling)
- `review-protocol.md`: "The essential eight invariants apply to every change" (lists all 8, no strikethrough)

**Action:** Update `review-protocol.md` to:
> "The essential eight invariants (6 applicable to BuildOS — see `CLAUDE.md`) guide every change. Add domain-specific invariants on top."

---

## Phase 2: Deduplicate Claude-Facing Files (7 duplications)

For each item below, one file is designated canonical. Redundant files should replace duplicated content with a one-line reference.

### 2A. Simplicity / no overengineering
- **Canonical:** `code-quality.md` (contains the required "don't add docstrings" bullet).
- **Action:** Cut from `CLAUDE.md`.
- **Replacement text in `CLAUDE.md`:**
  > "### Simplicity is the override rule  
  > See `code-quality.md`. The simplest version wins unless there's evidence otherwise."

### 2B. No commit without review
- **Canonical:** `review-protocol.md` ("HARD RULE: No commit without the appropriate review.")
- **Action:** Keep the one-line bullet in `CLAUDE.md` hard-rules list.
- **Action:** Cut from `session-discipline.md`: remove the "Review requirement" paragraph entirely; retain only the plan-gate specifics unique to that section.

### 2C. Verify before done
- **Canonical:** `review-protocol.md` (Definition of Done section).
- **Action:** Keep the one-liner in `CLAUDE.md`:
  > "Prove it works. Tests, logs, evidence."
- **Action in `session-discipline.md`:**
  Replace the Verification section with:
  > "## Verification  
  > See `review-protocol.md` Definition of Done. Additionally: sanity-check data volumes, not just success codes."
- **Action in `workflow.md`:**
  Replace line 3 with:
  > "Verify before done — see `review-protocol.md`."

### 2D. Pipeline tiers (full table)
- **Canonical:** `CLAUDE.md` (always-loaded reference).
- **Action:** Cut from `workflow.md`.
- **Replacement in `workflow.md`:**
  > "Pipeline tiers: see `CLAUDE.md`. Decision logic:"
  Retain only the workflow-specific guidance.
- **Action:** Cut from `review-protocol.md`.
- **Replacement:** Replace "Typical paths by change type" with a reference to `CLAUDE.md`.

### 2E. Fix-forward rule
- **Canonical:** `bash-failures.md` (contains hook enforcement, diagnostic sequences, prohibited patterns).
- **Action:** Cut from `workflow.md`.
- **Replacement in `workflow.md`:**
  > "## Fix-Forward Rule  
  > See `bash-failures.md`. Never silently work around the same infrastructure failure twice."

### 2F. LLM boundary / model may decide
- **Canonical:** `security.md` (covers invocation layer, structured output validation, the test).
- **Action:** Cut from `CLAUDE.md`.
- **Retain only the one-line principle:**
  > "LLMs classify, summarize, and draft. Deterministic code performs state transitions. If the LLM can cause irreversible state changes, it must not be the actor."

### 2G. Document results
- **Canonical:** `session-discipline.md` (the "Document First, Execute Second" section).
- **Action:** Cut from `CLAUDE.md`.
- **Replacement in `CLAUDE.md`:**
  > "### Document results  
  > Update `decisions.md`, `lessons.md`, and `handoff.md` before implementing. See `session-discipline.md` for the full what-goes-where table."
- **Action in `workflow.md`:**
  Replace "Document first, execute second" with a reference to `session-discipline.md`.

---

## Phase 3: Tighten Verbosity

### 3A. Remove all origin tags
**Action:** Delete all lines matching `*Origin: ...*` from:
- `code-quality.md`
- `bash-failures.md`
- `code-quality-detail.md`
- `skill-authoring.md`

### 3B. Remove preambles before self-explanatory sections
**Action:** Delete the following instructional padding:
- `design.md`: "Watch for these anti-patterns in generated UI and content. Any match = rewrite."
- `natural-language-routing.md`: "Don't wait for the user to ask. Watch for these signals during a session and suggest the appropriate skill:"
- `code-quality-detail.md`: "These rules apply when working in specific domains. They are NOT loaded by default..."

### 3C. Tighten over-explained rules
**Action:** Compress the following paragraphs into exact directives:

- **`security.md` (allowlist check):**
  > "Allowlist: `if allowlist is not None and value not in allowlist` — NOT `if allowlist and value...` (empty string and None bypass)."

- **`security.md` (CSV formula injection):**
  > "CSV formula injection: prefix cells starting with `=+\-@` with single quote, or use `csv.QUOTE_ALL`."

- **`orchestration.md` (decomposition gate):**
  > "Count independent components. 3+: decompose (one agent per component, worktree isolation). 1-2: bypass. User says 'skip': bypass immediately."

- **`orchestration.md` (file references):**
  > "Worktree agent prompts: relative paths only (`src/file.py`, not `/home/.../src/file.py`). Absolute paths bypass isolation."

### 3D. Tighten compaction protocol in `session-discipline.md`
**Action:** Replace the 3 multi-sentence paragraphs with:
> "55%: write state to disk proactively. 55-70%: compact at natural breakpoint. 70%: hard compact immediately (write thoughts to disk first)."

### 3E. Tighten "Root Cause First" in `workflow.md`
**Action:** Compress the 18-line section to about 8 lines.
- Retain the 5 steps.
- Reduce each step to a single line.
- Retain the anti-patterns list.
- Delete "The test" paragraph entirely.

### 3F. Tighten "How to Route" in `natural-language-routing.md`
**Action:** Replace the 5 numbered principles with:
> "Match intent, not keywords. Invoke directly — don't explain the skill first. Chain skills automatically when one outputs another's input. One suggestion per pattern per session."

---

## Execution Standard

Apply the changes above with these invariants:

1. **Normative parity:** replacement text must preserve directive force, not summarize it into a weaker suggestion.
2. **Single canonical source per rule:** once a rule has a canonical home, all other copies become references unless they contain unique operational detail.
3. **Always-loaded precedence:** if a rule is critical during every session, its canonical source must remain in an always-loaded file or be referenced from one.
4. **No silent semantic edits:** if wording changes alter applicability, thresholds, or obligation level, that is out of scope for this compression pass.
5. **Reference quality:** references must point to the exact file and section that now owns the rule.

## Acceptance Criteria

This proposal is complete only if all of the following are true after the edits:

1. All 4 listed contradictions are resolved exactly once, with one canonical interpretation.
2. All 7 listed duplications are collapsed to one canonical source plus references.
3. All Phase 3 cuts preserve the same directive meaning.
4. No hook behavior changes.
5. No rule count decreases due to accidental deletion.
6. A reader can determine the authoritative source for each moved rule in one hop.
7. The resulting docs still support the same review, planning, verification, and safety behavior.

## Expected Impact

- **Tokens recovered:** ~1,200-1,500 from Claude-facing files (~10-12%)  
  - EVIDENCED: stated in the proposal text.
- **Ambiguities resolved:** 4 contradictions eliminated  
  - EVIDENCED: four contradiction groups are enumerated in Phase 1.
- **Rules removed:** 0  
  - EVIDENCED: stated as a constraint.
- **Hooks changed:** 0  
  - EVIDENCED: stated as a constraint.
- **Enforcement weakened:** None  
  - This is the target outcome of the proposal, to be verified against the acceptance criteria rather than assumed.
- **Net effect:** Same governance, less noise, clearer signal.
