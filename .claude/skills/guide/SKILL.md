---
name: guide
description: "Quick reference organized by what you want to do, not by skill name. Use when lost, onboarding, or unsure which skill to run next."
version: 1.0.0
tier: 1
user-invocable: true
---

# /guide — What Do You Want to Do?

Show the user a quick reference organized by intent, then offer to route them.

## Procedure

### Step 1: Show the guide

Output the following text block exactly:

```
## You don't need to memorize anything.

Just describe what you want to do. Build OS will route you to the right tool.

But if you want a map, here it is:

### I want to...

**Start a new project**
  /setup — interactive project setup, picks your governance tier

**Figure out what to build**
  /think discover — full problem discovery with forcing questions + design doc
  /think refine — quick 5-question sanity check for features

**Explore options before committing**
  /explore — 3+ divergent directions with cross-model synthesis
  /research — deep web research with citations (Perplexity Sonar)

**Check if this is worth building**
  /challenge — cross-model gate: should we build this?
  /elevate — stress-test scope and ambition (are we thinking big enough?)
  /pressure-test — counter-thesis or pre-mortem failure analysis

**Plan the implementation**
  /plan — write an implementation plan with valid frontmatter
  /plan --auto — auto-detect tier and chain the full pipeline

**Design a UI**
  /design consult — create or upgrade a design system
  /design review — visual QA with 94-item checklist
  /design variants — generate and compare multiple directions
  /design plan-check — rate a plan 0-10 on design completeness

**Improve a document or plan**
  /polish — 6-round cross-model iterative refinement

**Review code before shipping**
  /review — cross-model code review (PM + Security + Architecture)
  /review --fix — review + auto-fix mechanical issues
  /review --qa — domain-specific QA validation

**Ship it**
  /ship — pre-flight gates (tests + review + verify) then deploy

**Debug something broken**
  /investigate — structured root-cause analysis (symptom, drift, or claim)
  /audit — two-phase blind discovery audit

**End my session**
  /wrap — write handoff, session log, current state, commit
  /start — (next session) bootstrap + routing from where you left off

**Capture knowledge**
  /log — extract decisions and lessons from a conversation
  /sync — sync project docs to match what shipped
  /triage — classify incoming info and route it

### Common pipelines

  Bugfix:      /plan → build → /review → /ship
  Feature:     /think → /plan → build → /review → /ship
  New feature: /think → /challenge → /plan → build → /review → /ship
  Big bet:     /think → /elevate → /challenge → /plan → build → /review → /ship

### Or just say what you want.

"I need to add user authentication" → Claude routes you through /think → /challenge → /plan
"Something broke in the API" → Claude runs /investigate
"Is this plan good enough?" → Claude runs /review or /pressure-test
"Ship it" → Claude runs /ship

Full reference: docs/cheat-sheet.md
```

### Step 2: Ask what they want to do

After showing the guide, ask: "What are you working on?" and route them to the appropriate skill based on their answer. Use the intent mapping above.

If their answer maps to a clear skill, invoke it directly. If ambiguous, suggest 2-3 options and let them pick.

## Completion

Report status:
- **DONE** — All steps completed successfully.
- **DONE_WITH_CONCERNS** — Completed with issues to note.
- **BLOCKED** — Cannot proceed. State the blocker.
- **NEEDS_CONTEXT** — Missing information needed to continue.
