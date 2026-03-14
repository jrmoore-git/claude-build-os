# CLAUDE.md

## What this project is
<!-- Replace this section with a one-paragraph description of what you're building and why. -->
[Describe your project here. What are you building? Who is it for? What problem does it solve?]

## Operating rules

### Simplicity is the override rule
<!-- Why: Claude over-engineers by default. This phrase is from Anthropic's own docs and Claude responds to it reliably. Remove only if you want Claude to build speculatively. -->
Avoid over-engineering. Only make changes that are directly requested or clearly necessary. Keep solutions simple and focused.
- Don't add features, refactor code, or make "improvements" beyond what was asked.
- Don't add error handling, fallbacks, or validation for scenarios that can't happen.
- Don't create helpers, utilities, or abstractions for one-time operations.
- Don't design for hypothetical future requirements.

### The model may decide; software must act
<!-- Why: Prevents the most dangerous class of AI bugs — LLM-driven state changes. Remove only if your project has no state mutations. -->
LLMs classify, summarize, and draft. Deterministic code performs state transitions, API calls, and data mutations.
If the LLM can cause irreversible state changes, it must not be the actor.

### Retrieve before planning
<!-- Why: Loading everything into context creates drift, not safety. This rule keeps sessions focused. -->
Read handoff.md and current-state.md before starting work. Read relevant lessons and decisions before touching risky areas. Don't load everything — load what's relevant.

### Plan before building (when it matters)
<!-- Why: Plans written to disk prevent wasted work and survive session compaction. Skip for trivial edits. -->
Write a plan to disk if: more than 3 files change, auth/security is involved, user-facing behavior changes, or multiple tracks need coordination.
Skip for: one-line fixes, obvious edits, trivial config.

### Document results
<!-- Why: Decisions and lessons that stay in conversation history are lost on the next session. Disk is durable memory. -->
Update decisions.md after material decisions.
Update lessons.md after surprises or mistakes.
Update handoff.md before ending incomplete work.

### Verify before declaring done
<!-- Why: "It should work" is not evidence. Claude will claim completion confidently even when things are broken. -->
Prove it works. Tests, logs, evidence. A claim of completion is not evidence.

## Project-specific rules
<!-- Add rules specific to your project as you discover them. Examples: -->
<!-- - "All API responses must be validated against the schema before processing" -->
<!-- - "Never modify the payments table directly — use the payments service" -->
<!-- - "Run pytest after any change to src/" -->
