# Resolution: Four Additions to the Build OS Repo

**Author:** Claude Opus (Round 3)
**Date:** 2026-03-13
**Responding to:** Challenger A (7 challenges, 5 MATERIAL) + Challenger B (3 challenges, 3 MATERIAL)

---

## Responses to Challenger A

### 1. [ASSUMPTION] [MATERIAL]: hooks-guide.md will drift as Anthropic changes the hook API

**CONCEDE.** Both challengers raised this. A full hooks guide that documents API specifics (matcher syntax, tool names, settings.json schema) will go stale. Anthropic's docs are the canonical reference for hook mechanics.

**Revised approach:** Don't create `docs/hooks-guide.md`. Instead:
- Add a **"Getting Started with Hooks"** section to the existing `examples/` directory as a README (`examples/README.md`, ~30 lines)
- It covers: what hooks are (one paragraph), link to Anthropic's official hook docs for API specifics, explanation of the two existing example scripts, and a starter `settings.json` that uses the examples
- This is a trailhead, not a reference. The repo's value-add is WHEN and WHY to use hooks (already in the Build OS enforcement ladder), not HOW the API works.

### 2. [ALTERNATIVE] [MATERIAL]: toolbelt-example.py is Python-specific for a language-agnostic repo

**CONCEDE.** Both challengers raised this. A Python script implies Python is the recommended stack and creates maintenance burden for executable code.

**Revised approach:** Replace `examples/toolbelt-example.py` with a **commented pseudocode block inside the Build OS** (Part IX, after the operator scars). Add a new subsection "The LLM Boundary in Practice" showing the pattern as language-neutral pseudocode:

```
# 1. DETERMINISTIC FETCH — code fetches verified data
record = db.query("SELECT * FROM drafts WHERE id = ?", [draft_id])

# 2. LLM REASONS — model classifies, summarizes, or drafts
llm_output = call_model(prompt=f"Classify this draft: {record.text}")

# 3. SCHEMA VALIDATE — code validates the model's output
if not valid_json(llm_output) or llm_output.action not in ALLOWED_ACTIONS:
    log_error("Invalid LLM output", llm_output)
    return  # Fail safe: do nothing

# 4. DETERMINISTIC APPLY — code performs the state change
db.execute("UPDATE drafts SET status = ? WHERE id = ?",
           [llm_output.action, draft_id])

# 5. AUDIT — code logs what happened
db.execute("INSERT INTO audit_log (action, draft_id, result) VALUES (?, ?, ?)",
           [llm_output.action, draft_id, "applied"])
```

This is 15 lines inside an existing doc, not a new file. It teaches the principle without language bias or maintenance burden.

### 3. [RISK] [MATERIAL]: A 60-line toy script may normalize weak validation

**CONCEDE.** Addressed by the move to pseudocode (Challenge 2). Pseudocode can show the right abstractions without toy implementations of schema validation.

### 4. [UNDER-ENGINEERED] [MATERIAL]: Persona growth note is too weak

**COMPROMISE.** The challenger is right that a single paragraph won't change behavior. But a full PERSONAS.md template would be over-engineering for a starter repo — most teams won't need it until Tier 2+.

**Revised approach:** Keep the paragraph but add concrete triggers:

> **Growing your review protocol:** Start expanding your persona questions when: (1) the same type of issue escapes review twice, (2) your project crosses into Tier 2, or (3) your team has domain-specific risks (financial data, PII, autonomous actions) that the starter questions don't cover. Create a `PERSONAS.md` file with detailed checklists per persona. Example: a Security persona for a system handling PII might add "Are all personal data fields encrypted at rest?" and "Is there a data retention policy enforced in code?"

### 5. [ASSUMPTION] [ADVISORY]: "Promote after second violation" is presented as universal

**CONCEDE.** The threshold should be contextual, not fixed.

**Revised approach:** The promotion example will show the mechanic (how to mark a promotion) without prescribing a fixed violation count. The Build OS already covers escalation speed matching blast radius (Part V). The lessons template will reference that section.

### 6. [OVER-ENGINEERED] [ADVISORY]: Four additions may chip away at minimalism

**COMPROMISE.** The revised plan reduces from 2 new files + 2 edits to 1 new file + 3 edits:
- ~~`docs/hooks-guide.md`~~ → `examples/README.md` (trailhead, not guide)
- ~~`examples/toolbelt-example.py`~~ → pseudocode block in existing `docs/the-build-os.md`
- Persona growth note → edit to existing `templates/review-protocol.md`
- Promotion example → edit to existing `templates/lessons.md`

One new file (examples README), three edits to existing files. No new docs.

### 7. [RISK] [MATERIAL]: Topic ownership may regress

**REBUT.** The revised plan does not create topic overlap:
- `examples/README.md` explains the example scripts — it doesn't redefine enforcement ladder concepts
- The pseudocode block goes in Build OS Part IX (Patterns Worth Knowing) — the canonical home for concrete demonstrations of principles
- Template edits add examples to templates, not to docs

Topic ownership is preserved: Build OS owns the concepts, templates own the starting structures, examples own the practical demonstrations.

---

## Responses to Challenger B

### 1. [RISK] [MATERIAL]: hooks-guide.md duplicates Anthropic's docs and will drift

**CONCEDE.** Same conclusion as Challenger A, Challenge 1. No standalone hooks guide. An `examples/README.md` trailhead with a link to official docs instead.

### 2. [ALTERNATIVE] [MATERIAL]: toolbelt-example.py is language-specific

**CONCEDE.** Same conclusion as Challenger A, Challenge 2. Pseudocode in the Build OS instead of a standalone Python file.

### 3. [UNDER-ENGINEERED] [MATERIAL]: Struck-through lessons bloat context

**CONCEDE.** Good catch — struck-through entries waste tokens. Promoted lessons should be removed from the active file, not left as struck-through ghosts.

**Revised approach:** The promotion example will show:
1. The lesson being removed from `tasks/lessons.md`
2. A note at the bottom of lessons.md: "Promoted: L12 → `.claude/rules/security.md` (2026-03-01)"
3. The rule file containing the promoted content

One line of provenance (where did it go), not a struck-through copy of the full lesson.

---

## Revised Plan Summary

### 1. `examples/README.md` (NEW — ~30 lines)
- What hooks are (one paragraph)
- Link to Anthropic's official hook documentation
- What each example script does and when to use it
- A starter `settings.json` that wires up both examples

### 2. Edit: `docs/the-build-os.md` — add "The LLM Boundary in Practice" subsection
- 15-line pseudocode block in Part IX showing the 5-step pattern
- Language-neutral, no maintenance burden, teaches the principle

### 3. Edit: `templates/review-protocol.md` — add persona growth note
- One paragraph with concrete triggers (same issue escapes twice, crosses Tier 2, domain-specific risks)
- One example of an expanded Security persona question

### 4. Edit: `templates/lessons.md` — add promotion example
- Show a lesson being removed and a one-line provenance note
- Reference Build OS Part V for escalation speed guidance
- No struck-through entries, no fixed violation count
