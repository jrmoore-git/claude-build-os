---
debate_id: streamline-rules-v3
created: 2026-04-18T10:01:11-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# streamline-rules-v3 — Refined Document

## Round 1 (gemini-3.1-pro)
This is an exceptionally strong proposal. It treats prompt engineering as software engineering, identifying specific contradictions, duplications, and verbosity, and providing exact diffs to fix them. The token accounting and strict adherence to the "same governance" constraint make it immediately executable. 

### Frame Check
Frame check: document's frame is sound. (The proposal correctly avoids the trap of completely removing core rules from the always-loaded `CLAUDE.md`, instead leaving terse one-liners that point to canonical deep-dive files. This preserves context locality while achieving compression).

## Round 2 (gpt-5.4)
The proposal is already fairly sharp and executable. Its strongest qualities are: a clear non-goal (“same governance, same enforcement”), concrete file-by-file edits, and preserved operational constraints. I kept that structure and made the main weak points more explicit:

- tightened the problem statement so the duplication/ambiguity claims are framed as plausible governance costs rather than assumed system-wide failure
- clarified where estimates are estimates and what they are based on
- made the “canonical file” pattern more consistent across phases
- improved a few actions so they read as exact edits rather than general intentions
- preserved all recommendation entries and kept the proposal decisive

Remaining limitation: the token-recovery estimate is still an estimate derived from the author’s stated file/token counts, not from an independently shown before/after diff. That does not block the proposal, but it should remain labeled as estimated.

### Frame Check
- Unstated load-bearing assumption: The proposal assumes the listed files are the complete set of Claude-facing governance sources that materially affect instruction behavior; if other high-priority prompts, templates, or hidden rule surfaces exist, the “same governance, lower overhead” recommendation may not hold — this is load-bearing and cannot be fixed by prose polish alone.
- Inflated problem: The document implies that duplication and contradiction are materially reducing governance effectiveness, but provides no measured compliance failures or conflict frequency; if these issues are rare, the compression still may be worthwhile, but the “governance effectiveness” framing is broader than the evidence shown — this requires reframing, not just added wording.

## Final Refined Document

# Proposal: Streamline BuildOS Rule Files

## Problem

BuildOS rule files (`CLAUDE.md` + 10 rule files + 4 reference files) appear to contain duplication, ambiguity, and verbosity that likely reduce signal-to-noise for Claude-facing governance:

1. **Rule duplication:** The same directives appear in multiple Claude-facing files, increasing prompt footprint without clearly adding enforcement value.
2. **Contradictory statements:** A small number of instruction conflicts force reconciliation at runtime instead of giving a single authoritative rule.
3. **Verbose explanations:** Origin tags, preambles, and over-explained rules consume tokens that could be used for the directives themselves.

Baseline metrics:
- Estimated total: ~12,810 tokens across 15 Claude-facing files.  
  **ESTIMATED:** based on the proposal's stated corpus size and file count.
- Recoverable: ~1,200-1,500 tokens (~10-12%) with no intended governance change.  
  **ESTIMATED:** based on the specific removals and compressions listed below, assuming no hidden rule surfaces or duplicate prompt injections outside the named files.

## Constraint

Same governance, same enforcement, same rules. This is strict compression.

- No rules removed.
- No hooks changed.
- No enforcement weakened.
- Where duplicate text exists, keep one canonical statement and replace the rest with short references that preserve the directive.

---

## Phase 1: Fix Ambiguity (4 contradictions)

### 1A. "Document before or after implementation?"
**Current state:**
- `CLAUDE.md`: "Update decisions.md **after** material decisions"
- `session-discipline.md`: "Every correction must be persisted **BEFORE** implementation"
- `workflow.md`: "Document first, execute second"

**Action:** Standardize on **before**.
- Change `CLAUDE.md` to: "Update `decisions.md` before implementing material decisions."

### 1B. "Which docs to read at session start?"
**Current state:** `CLAUDE.md` and `workflow.md` provide different reading lists.

**Action:** Designate `workflow.md` as canonical for startup orientation.
- Change `CLAUDE.md` to: "Read `handoff.md` and `current-state.md` before starting work. See `workflow.md` for the full orient-before-planning checklist."

### 1C. "When to skip /challenge?"
**Current state:** Skip conditions differ between `CLAUDE.md` and `review-protocol.md`.

**Action:** Designate `CLAUDE.md` as canonical because it is always loaded.
- Change `review-protocol.md` to reference `CLAUDE.md` for skip conditions instead of restating them.
- Leave the `workflow.md` tier table unchanged in this phase; it is already compatible.

### 1D. "Essential eight — 6 or 8 apply?"
**Current state:** `CLAUDE.md` states 6 of 8 apply; `review-protocol.md` states all 8 apply.

**Action:** Standardize on 6 for BuildOS.
- Change `review-protocol.md` to: "The essential eight invariants (6 applicable to BuildOS — see `CLAUDE.md`) guide every change. Add domain-specific invariants on top."

---

## Phase 2: Deduplicate Claude-Facing Files (7 duplications)

For each duplication, designate one canonical file. In non-canonical files, replace repeated prose with a one-line reference plus any short, file-specific directive that must remain local.

### 2A. Simplicity / no overengineering
- **Canonical:** `code-quality.md`
- **Action:** Replace the 6-line section in `CLAUDE.md` with:

  > "### Simplicity is the override rule  
  > See `code-quality.md`. The simplest version wins unless there's evidence otherwise."

### 2B. "No commit without review"
- **Canonical:** `review-protocol.md`
- **Action:** Keep the one-line hard rule in `CLAUDE.md`.
- Remove the restated "Review requirement" paragraph from `session-discipline.md`.
- Keep only the plan-gate specifics in `session-discipline.md` that are unique to that file.

### 2C. Verify before done
- **Canonical:** `review-protocol.md` under Definition of Done
- **Action:**
  - Keep the one-liner in `CLAUDE.md`: "Prove it works. Tests, logs, evidence."
  - Replace the Verification section in `session-discipline.md` with: "## Verification\nSee `review-protocol.md` Definition of Done. Additionally: sanity-check data volumes, not just success codes."
  - Replace line 3 in `workflow.md` with: "Verify before done — see `review-protocol.md`."

### 2D. Pipeline tiers
- **Canonical:** `CLAUDE.md`
- **Action:**
  - Replace the full tier table in `workflow.md` with: "Pipeline tiers: see `CLAUDE.md`. Decision logic:" and retain only workflow-specific guidance on plan mode, decomposition, and `/think`.
  - Replace "Typical paths by change type" in `review-protocol.md` with a reference to `CLAUDE.md`.

### 2E. Fix-forward rule
- **Canonical:** `bash-failures.md`
- **Action:** Replace the 8-line section in `workflow.md` with:

  > "## Fix-Forward Rule  
  > See `bash-failures.md`. Never silently work around the same infrastructure failure twice."

### 2F. LLM boundary / model may decide
- **Canonical:** `security.md`
- **Action:** Keep the one-line principle in `CLAUDE.md`:
  > "LLMs classify, summarize, and draft. Deterministic code performs state transitions. If the LLM can cause irreversible state changes, it must not be the actor."
- Remove the expanded section-heading prose around that principle from `CLAUDE.md`.

### 2G. Document results
- **Canonical:** `session-discipline.md`
- **Action:**
  - Replace the section in `CLAUDE.md` with: "### Document results\nUpdate `decisions.md`, `lessons.md`, and `handoff.md` before implementing. See `session-discipline.md` for the full what-goes-where table."
  - Replace the corresponding bullet in `workflow.md` with a reference to `session-discipline.md`.

---

## Phase 3: Tighten Verbosity

Execute the following exact prose compressions.

### 3A. Remove origin tags
Delete all lines matching `*Origin: ...*` from:
- `code-quality.md`
- `bash-failures.md`
- `code-quality-detail.md`
- `skill-authoring.md`

Estimated savings: ~50 tokens.  
**ESTIMATED:** based on the proposal's stated count for the listed lines.

### 3B. Remove preambles
Delete:
- In `design.md`: "Watch for these anti-patterns in generated UI and content. Any match = rewrite."
- In `natural-language-routing.md`: "Don't wait for the user to ask. Watch for these signals during a session and suggest the appropriate skill:"
- In `code-quality-detail.md`: "These rules apply when working in specific domains. They are NOT loaded by default..."

Estimated savings: ~100 tokens.  
**ESTIMATED:** based on the proposal's stated count for the listed deletions.

### 3C. Tighten over-explained rules
Apply these exact replacements:

- **`security.md` (Allowlist):**  
  "Allowlist: `if allowlist is not None and value not in allowlist` — NOT `if allowlist and value...` (empty string and None bypass)."

- **`security.md` (CSV injection):**  
  "CSV formula injection: prefix cells starting with `=+\-@` with single quote, or use `csv.QUOTE_ALL`."

- **`orchestration.md` (Decomposition):**  
  "Count independent components. 3+: decompose (one agent per component, worktree isolation). 1-2: bypass. User says 'skip': bypass immediately."

- **`orchestration.md` (File references):**  
  "Worktree agent prompts: relative paths only (`src/file.py`, not `/home/.../src/file.py`). Absolute paths bypass isolation."

Estimated savings: ~150 tokens.  
**ESTIMATED:** based on the proposal's stated count for the listed compressions.

### 3D. Tighten compaction protocol
In `session-discipline.md`, compress 3 paragraphs to:

> "55%: write state to disk proactively. 55-70%: compact at natural breakpoint. 70%: hard compact immediately (write thoughts to disk first)."

Estimated savings: ~40 tokens.  
**ESTIMATED:** based on the proposal's stated count for this compression.

### 3E. Tighten "Root Cause First"
In `workflow.md`, compress the 18-line section to about 8 lines:
- retain the 5 steps as single lines
- retain the anti-patterns list
- delete "The test" paragraph

Estimated savings: ~35 tokens.  
**ESTIMATED:** based on the proposal's stated count for this compression.

### 3F. Tighten "How to Route"
In `natural-language-routing.md`, compress 5 principles to:

> "Match intent, not keywords. Invoke directly — don't explain the skill first. Chain skills automatically when one outputs another's input. One suggestion per pattern per session."

Estimated savings: ~30 tokens.  
**ESTIMATED:** based on the proposal's stated count for this compression.

---

## Expected Impact

- **Tokens recovered:** ~1,200-1,500 from Claude-facing files (~10-12%).  
  **ESTIMATED:** based on the proposal's baseline total (~12,810 tokens) and the listed deletions/compressions.
- **Ambiguities resolved:** 4 contradictions eliminated.  
  **EVIDENCED:** four contradiction pairs are enumerated in Phase 1.
- **Rules removed:** 0.  
  **EVIDENCED:** stated constraint and all actions preserve a canonical directive rather than deleting policy.
- **Hooks changed:** 0.  
  **EVIDENCED:** stated constraint; no action item modifies hooks.
- **Enforcement weakened:** None intended; duplicate prose is replaced by canonical references, not policy removal.
- **Net effect:** Identical intended governance, higher signal-to-noise ratio, and lower Claude-facing context overhead, assuming the named files are the full governance surface relevant to these rules.
