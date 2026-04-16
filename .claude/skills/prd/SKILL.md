---
name: prd
description: "Generate or validate a PRD from a design doc. Use after /think discover produces a design doc, or standalone when a PRD needs creating/updating. Defers to: /think (problem discovery), /plan (implementation spec)."
version: 1.0.0
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Write
  - Edit
  - AskUserQuestion
---

# /prd — PRD Generation and Validation

Generate or validate a Product Requirements Document from a design doc and conversation context.

## Safety Rules

- NEVER fabricate requirements the user didn't discuss or imply.
- NEVER silently drop open questions — unresolved items go to an Open Questions appendix.
- Use the user's own words from Q&A — do not rephrase into marketing language.

## OUTPUT SILENCE -- HARD RULE

Between tool calls, emit ZERO text to the chat. The ONLY user-visible output is the formatted blocks before AskUserQuestion calls and the final status report.

**Exception:** Text immediately preceding an AskUserQuestion call is permitted.

## Procedure

### Step 1: Find the design doc

Search for the most recent design doc:

```bash
ls -t tasks/*-design.md 2>/dev/null | head -5
```

If multiple exist, pick the most recent. If none exist:
- Check if the user specified a file path — use that.
- Otherwise: report "No design doc found. Run `/think discover` first or specify a file." and stop.

Read the design doc.

### Step 2: Check PRD state

Read `docs/project-prd.md` if it exists.

**Route based on PRD state:**

**A) PRD is blank or template-only** (contains placeholder text like `[One paragraph`
or `[Target users`):

Output as markdown text before asking:

> **Your PRD is empty. How do you want to create it?**
>
> - **A) Generate from this conversation** (Recommended) -- I'll map the design doc
>   into PRD format and ask a few follow-up questions to fill gaps
> - **B) Validate a draft** -- paste or point me to a PRD you've already written
>   and I'll check it against the design doc
> - **C) Skip** -- I'll fill it in manually later

Then call AskUserQuestion with the same options.

- If A: proceed to **Step 3: PRD Generation**.
- If B: proceed to **Step 4: PRD Validation**.
- If C: report DONE and stop.

**B) PRD already has real content**: check whether the design doc expands scope
beyond what the PRD covers.

Output as markdown text before asking:

> **Your PRD already exists. The design doc covers: {1-line summary}.**
>
> - **A) Update the PRD** -- add new scope to the existing PRD
> - **B) Skip** -- PRD is fine as-is

Then call AskUserQuestion. If A: update relevant sections (append to requirements,
add acceptance criteria for new features, update scope). If B: report DONE and stop.

**C) No PRD file exists**: Create from template. Proceed to Step 3.

### Step 3: PRD Generation (from design doc)

**Step 3a: Map what we already have.**

| Design doc source | PRD section |
|---|---|
| Problem Statement | **1. What we're building** -- rewrite as "what it is, what it solves, and why" in one paragraph |
| Target User / Desperate Specificity (Q3) | **2. Who it's for** -- specific person with role, not a category |
| Narrowest Wedge (Q4) + recommended approach | **3. Core requirements** -- numbered, each starts with "Users can..." or "The system..." |
| Rejected approaches + explicit scope boundaries | **6. Out of scope** -- what this does NOT do, including things AI might add |
| Recommended Approach + key technical choices | **7. Technical decisions** -- link to design doc for detail. Fold Distribution Plan here if present. |
| Success Criteria from design doc | **8. Success criteria** -- measurable and time-bound, not aspirational |

**Open Questions handling:** If the design doc has an "Open Questions" section with
unresolved items, surface each one during PRD Q1-Q3 follow-ups where relevant. Any
open questions that remain unresolved after follow-ups go into a `## Open Questions`
appendix at the end of the PRD -- do not silently drop them.

**Step 3b: Ask follow-up questions for gaps.** Ask ONE AT A TIME via AskUserQuestion.
Prefix each with `[PRD Q N/3]`. Smart-skip any question the design doc already answers.

**PRD Q1 -- Acceptance criteria:**
"For each core requirement, what proves it works? I need specific, testable criteria.
For example: 'Given a logged-in user, when they click Send, then the email is delivered
within 30 seconds' -- not 'email sending works'. Here are the requirements I extracted:

{list the 3-5 core requirements from the design doc}

What are the acceptance criteria for each?"

If the user gives vague criteria, push once: "'{criterion}' isn't testable -- what
specific outcome would a test check for?" If still vague after one push, accept and
note in the PRD as needing refinement.

**PRD Q2 -- Constraints:**
"What constraints should Claude respect when building this? Things it can't infer
from the requirements -- for example:
- Performance: 'API must respond in < 200ms'
- Security: 'All user data encrypted at rest'
- Compatibility: 'Must work in Safari 17+'
- Scale: 'Must handle 1000 concurrent users'
- Don't touch: 'Do not modify the auth system'

What are your constraints? Say 'none' if the defaults are fine."

If the user says "none" or "whatever": write sensible defaults based on the project
type and note them as assumed, not stated.

**PRD Q3 -- Verification:**
"How should Claude prove each requirement works before declaring done? Options include:
- Automated tests (unit, integration, e2e)
- Manual checks ('open the page and verify X appears')
- Screenshots
- Expected output ('running X should print Y')

I can draft a verification plan from the acceptance criteria. Want me to draft it, or
do you have specific verification methods in mind?"

If "draft it": generate verification entries from the acceptance criteria. Each
acceptance criterion maps to a verification method (prefer automated tests, fall
back to manual checks).

**Step 3c: Generate the PRD.** Write all 9 sections to `docs/project-prd.md`.

### Step 4: PRD Validation (user brings a draft)

1. Ask the user to paste the PRD content or provide a file path.
2. Read the draft.
3. Check it against the design doc and the PRD template. For each section:
   - **Present**: check that content is specific and testable, not vague.
   - **Missing**: flag it and draft the section from the design doc.
   - **Contradicts design doc**: flag the contradiction and ask which is correct.
4. Output a validation report:

   ```
   PRD Validation:
   - Section 1 (What we're building): PASS
   - Section 2 (Who it's for): WEAK -- says "developers" not a specific person
   - Section 3 (Core requirements): PASS -- 5 requirements, all testable
   - Section 4 (Acceptance criteria): MISSING -- need to add
   - Section 5 (Constraints): MISSING -- need to add
   ...
   ```

5. Ask via AskUserQuestion: "Want me to fix the flagged sections? I'll keep your
   language and fill gaps from the design doc."
6. If yes: apply fixes, ask the gap-filling questions (PRD Q1-Q3) for any sections
   that can't be inferred, and write to `docs/project-prd.md`.

### PRD Rules (apply to both generation and validation)

- Extract the project name from the design doc title and replace `[Project Name]` in the PRD header.
- Requirements must be concrete and testable -- "Users can X" not "Support for X".
- Acceptance criteria must be quantified where possible -- "responds within 200ms" not
  "responds quickly". Use Given/When/Then or `- [ ]` checkbox format.
- Constraints must include things the AI cannot infer from omission.
- Out of scope must include at least 2 items.
- Success criteria must be measurable.
- Builder mode designs may have lighter demand evidence -- constraints and verification
  can be lighter but must still exist.
- Use the user's own words from the Q&A -- do not rephrase into marketing language.

## Completion

Report status:
- **DONE** -- PRD written to `docs/project-prd.md`. State which sections were generated vs. mapped.
- **DONE_WITH_CONCERNS** -- PRD written with gaps noted. List sections that need user refinement.
- **BLOCKED** -- No design doc found. State what's needed.
- **NEEDS_CONTEXT** -- Missing information to generate specific sections.
