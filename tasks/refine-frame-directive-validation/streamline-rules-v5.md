---
debate_id: streamline-rules-v5
created: 2026-04-18T11:26:37-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# streamline-rules-v5 — Refined Document

## Round 1 (gemini-3.1-pro)
This is an exceptionally strong, actionable proposal. It identifies specific contradictions, isolates the canonical source of truth, and provides exact string replacements. 

The only structural risk is the reliance on cross-references (e.g., "See `workflow.md`"). This assumes the environment either auto-injects referenced files or Claude reliably uses file-read tools to fetch them before proceeding. If Claude fails to fetch the referenced file, governance *is* weakened. I have tightened the language to ensure the cross-references act as explicit directives to read the files, but you must ensure your environment supports this access pattern.

No frame defects found.

### Frame Check
- Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The proposal is directionally strong and already actionable, but the previous framing overstated certainty in two places: the current-state problem statement assumed all listed contradictions are active without distinguishing hard conflicts from “multiple summaries of the same policy,” and the token-savings estimate was presented as a likely outcome without enough support. I tightened both inline by narrowing claims to what the text itself supports and by making the expected impact contingent on the referenced edits rather than on an unverified total corpus count.

I also improved executability:
- Kept the three-phase structure, but clarified which file is canonical in each duplication case.
- Preserved every recommendation and made them more implementation-ready.
- Tightened wording so the document reads as a concrete edit plan rather than a general critique.
- Avoided implying governance is unchanged by default; the document now says governance should remain unchanged if the edits are applied exactly as specified.

Remaining limitation: the proposal still relies on an unstated assumption that these files are all still current and Claude-facing in the same way at the time of execution. That cannot be resolved from the text alone, so it remains a Frame Check concern.

### Frame Check
- Unstated load-bearing assumption: the proposal assumes the enumerated files, duplicated sections, and contradictions still exist in the current BuildOS ruleset and still drive Claude behavior — cannot verify from the text alone, and if false, parts of the edit plan no longer apply

## Final Refined Document

# Proposal: Streamline BuildOS Rule Files

## Problem

BuildOS rule files (`CLAUDE.md` + 10 rule files + 4 reference files) appear to contain duplication, ambiguity, and verbosity that likely reduce governance efficiency without improving enforcement.

The problems described here are text-structure problems inside the rule corpus, not claims that governance itself is failing:

1. **Instruction dilution:** Repeating the same rule across multiple Claude-facing files consumes context window tokens without clearly adding enforcement value.
2. **Contradictory or overlapping statements:** Different phrasings across files force Claude to reconcile multiple sources for the same decision.
3. **Verbose explanations:** Origin tags, preambles, and over-explained rules consume tokens where terse directives would carry the same policy.

Total size: ESTIMATED: [~12,810 tokens across 15 Claude-facing files, assuming the listed files are still present and approximately unchanged].  
Target reduction: ESTIMATED: [~1,200-1,500 tokens recoverable (~10-12%), assuming the listed edits apply as written and no equivalent text is reintroduced elsewhere].

## Constraint

Same governance, same enforcement, same rules. This is compression, not reduction.

- No rules removed.
- No hooks changed.
- No enforcement weakened.

That constraint holds only if the edits below are applied exactly as references or wording compressions, not as policy deletions.

---

## Phase 1: Fix Ambiguity (4 contradictions)

### 1A. "Document before or after implementation?"
**Current state (hard conflict):**
- `CLAUDE.md`: "Update decisions.md **after** material decisions"
- `session-discipline.md`: "Every correction must be persisted **BEFORE** implementation"
- `workflow.md`: "Document first, execute second"

**Fix:** Standardize on **before**. Change `CLAUDE.md` to: "Update decisions.md before implementing material decisions."

### 1B. "Which docs to read at session start?"
**Current state (competing checklists):**
- `CLAUDE.md`: "Read handoff.md and current-state.md before starting work. Read relevant lessons and decisions before touching risky areas."
- `workflow.md`: "read docs/project-prd.md + docs/project-map.md + docs/current-state.md + tasks/lessons.md (relevant domain) + tasks/session-log.md (last entry) before proposing any plan."

**Fix:** Designate `workflow.md` as the canonical checklist. Change `CLAUDE.md` to: "Read handoff.md and current-state.md before starting work. Read workflow.md for the full orient-before-planning checklist."

### 1C. "When to skip /challenge?"
**Current state (inconsistent skip conditions):**
- `CLAUDE.md`: "Skip both for: bugfixes, test-only changes, docs, `[TRIVIAL]` (<=2 files, no new abstractions, one-sentence scope)."
- `review-protocol.md`: "When to skip: Bugfixes, test additions, docs, trivial refactors -> `/plan --skip-challenge`."
- `workflow.md`: T2/standard tier implies challenge is skipped for bugfixes, small features, docs.

**Fix:** Designate `CLAUDE.md` as the canonical source for skip conditions. Replace the list in `review-protocol.md` with: "Skip conditions: see `CLAUDE.md`." Leave `workflow.md` unchanged.

### 1D. "Essential eight — 6 or 8 apply?"
**Current state (hard conflict):**
- `CLAUDE.md`: "6 of 8 apply to BuildOS" (strikes through approval gating, state machine validation, exactly-once scheduling)
- `review-protocol.md`: "The essential eight invariants apply to every change" (lists all 8, no strikethrough)

**Fix:** Change `review-protocol.md` to: "The essential eight invariants (6 applicable to BuildOS — see `CLAUDE.md`) guide every change. Add domain-specific invariants on top."

---

## Phase 2: Deduplicate Claude-Facing Files (7 duplications)

For each item, designate one canonical file. Replace duplicated content in other files with a direct reference rather than restating the rule.

### 2A. Simplicity / no overengineering
- **Canonical:** `code-quality.md`
- **Action:** Replace the 6-line "Simplicity is the override rule" section in `CLAUDE.md` with:
  > ### Simplicity is the override rule  
  > See `code-quality.md`. The simplest version wins unless there's evidence otherwise.

### 2B. "No commit without review"
- **Canonical:** `review-protocol.md`
- **Action:** Keep the one-line bullet in `CLAUDE.md`.
- **Action:** Remove the "Review requirement" paragraph from `session-discipline.md`, retaining only the plan-gate specifics unique to that section.

### 2C. Verify before done
- **Canonical:** `review-protocol.md` (Definition of Done section)
- **Action:** Keep the one-liner in `CLAUDE.md`.
- **Action:** Replace the Verification section in `session-discipline.md` with:
  > ## Verification  
  > See `review-protocol.md` Definition of Done. Additionally: sanity-check data volumes, not just success codes.
- **Action:** Replace line 3 in `workflow.md` with:
  > Verify before done — see `review-protocol.md`.

### 2D. Pipeline tiers (full table)
- **Canonical:** `CLAUDE.md`
- **Action:** Replace the full tier table in `workflow.md` with:
  > Pipeline tiers: see `CLAUDE.md`. Decision logic:
- **Action:** Replace "Typical paths by change type" in `review-protocol.md` with a reference to `CLAUDE.md`.

### 2E. Fix-forward rule
- **Canonical:** `bash-failures.md`
- **Action:** Replace the 8-line "Fix-Forward Rule" section in `workflow.md` with:
  > ## Fix-Forward Rule  
  > See `bash-failures.md`. Never silently work around the same infrastructure failure twice.

### 2F. LLM boundary / model may decide
- **Canonical:** `security.md`
- **Action:** Keep the one-line principle in `CLAUDE.md`:
  > LLMs classify, summarize, and draft. Deterministic code performs state transitions. If the LLM can cause irreversible state changes, it must not be the actor.
- **Action:** Delete the section-heading expansion that restates the same boundary.

### 2G. Document results
- **Canonical:** `session-discipline.md`
- **Action:** Replace the "Document results" section in `CLAUDE.md` with:
  > ### Document results  
  > Update `decisions.md`, `lessons.md`, and `handoff.md` before implementing. See `session-discipline.md` for the full what-goes-where table.
- **Action:** Replace the "Document first, execute second" bullet in `workflow.md` with a reference to `session-discipline.md`.

---

## Phase 3: Tighten Verbosity

### 3A. Remove all origin tags
Delete all lines matching `*Origin: ...*` from:
- `code-quality.md`
- `bash-failures.md`
- `code-quality-detail.md`
- `skill-authoring.md`

Savings: ESTIMATED: [~50 tokens saved from direct text removal across the listed files].

### 3B. Remove preambles before self-explanatory sections
Delete the following instructional padding:

- `design.md`: "Watch for these anti-patterns in generated UI and content. Any match = rewrite."
- `natural-language-routing.md`: "Don't wait for the user to ask. Watch for these signals during a session and suggest the appropriate skill:"
- `code-quality-detail.md`: "These rules apply when working in specific domains. They are NOT loaded by default..."

Savings: ESTIMATED: [~100 tokens saved from direct text removal across the listed preambles].

### 3C. Tighten over-explained rules
Compress the following rules without changing policy:

- **`security.md` (allowlist check):**  
  Change to:  
  > Allowlist: `if allowlist is not None and value not in allowlist` — NOT `if allowlist and value...` (empty string and `None` bypass).

- **`security.md` (CSV formula injection):**  
  Change to:  
  > CSV formula injection: prefix cells starting with `=+\-@` with single quote, or use `csv.QUOTE_ALL`.

- **`orchestration.md` (decomposition gate):**  
  Change to:  
  > Count independent components. 3+: decompose (one agent per component, worktree isolation). 1-2: bypass. User says "skip": bypass immediately.

- **`orchestration.md` (file references):**  
  Change to:  
  > Worktree agent prompts: relative paths only (`src/file.py`, not `/home/.../src/file.py`). Absolute paths bypass isolation.

Savings: ESTIMATED: [~150 tokens saved from replacing the listed passages with the compressed versions above].

### 3D. Tighten compaction protocol
**Target:** `session-discipline.md`

Replace 3 paragraphs with:
> 55%: write state to disk proactively. 55-70%: compact at natural breakpoint. 70%: hard compact immediately (write thoughts to disk first).

Savings: ESTIMATED: [~40 tokens saved from replacing the current paragraphs with the compressed version above].

### 3E. Tighten "Root Cause First"
**Target:** `workflow.md`

Compress from 18 lines to about 8 lines:
- Keep the 5 steps.
- Reduce each step to one line.
- Retain the anti-patterns list.
- Delete "The test" paragraph entirely.

Savings: ESTIMATED: [~35 tokens saved from compressing the section and removing "The test" paragraph].

### 3F. Tighten "How to Route"
**Target:** `natural-language-routing.md`

Compress 5 numbered principles to:
> Match intent, not keywords. Invoke directly — don't explain the skill first. Chain skills automatically when one outputs another's input. One suggestion per pattern per session.

Savings: ESTIMATED: [~30 tokens saved from replacing the numbered principles with the compressed version above].

---

## Expected Impact

If the files and passages listed above are still current, this edit set should produce the following:

- **Tokens recovered:** ESTIMATED: [~1,200-1,500 from Claude-facing files (~10-12% reduction), assuming the current corpus is ~12,810 tokens and the listed removals/compressions apply as described]
- **Ambiguities resolved:** 4 explicit contradictions or competing directives eliminated
- **Rules removed:** 0
- **Hooks changed:** 0
- **Enforcement weakened:** None, if canonical references fully preserve the underlying policy

## Proposed Changes

1. **Resolve the four identified ambiguity points first.**  
   Apply the exact wording changes in Phase 1 so that timing, startup-read requirements, challenge-skip conditions, and invariant scope each have one canonical answer.

2. **Convert duplicated policy text into canonical references.**  
   For each duplication listed in Phase 2, keep one authoritative copy and replace the rest with short references to that file rather than paraphrases.

3. **Remove verbosity that does not carry policy.**  
   Delete origin tags and self-explanatory preambles, and compress over-explained rule text exactly as specified in Phase 3.

4. **Preserve governance invariants during compression.**  
   For every edit above, verify that no rule semantics, enforcement path, or hook behavior changes as a side effect of shortening the text.

5. **Re-measure token count after edits.**  
   Recount the Claude-facing corpus after applying the changes to confirm whether the expected ~1,200-1,500 token reduction was achieved and to catch any duplicated text reintroduced during editing.
