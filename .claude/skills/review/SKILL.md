---
name: review
description: Run a structured review of changes before committing
user-invocable: true
---

# Staged Review

Run a structured review of the current changes before committing.

## When to use this command

Use `/review` for:
- New features or workflow changes
- State transitions or data model changes
- Auth, security, or external dependency changes
- Anything user-facing

Skip for: formatting, copy edits, config-only changes that don't affect behavior.

## Review order

Review in this sequence. Each persona has specific concerns:

### 1. Architect
- Are the boundaries clean? (LLM vs. deterministic, module vs. module)
- Is anything unnecessarily complex? What could be removed?
- Does this create new coupling or hidden state?
- Does the file structure still make sense?

### 2. Staff Engineer + Security
- Is the implementation correct and robust?
- Are there injection risks, auth weaknesses, or unvalidated inputs?
- Are error paths handled? What happens when things fail?
- Are tests adequate? What's not covered?

### 3. Product / UX
- Does this solve the right problem?
- Is it simple enough? Would a user understand it?
- Does it match the PRD or spec?
- Is there unnecessary complexity that hurts usability?

## Output format

For each persona, write findings as:

```markdown
## [Persona] Review

### Blocking
- [Issues that must be fixed before commit — max 5]

### Concerns
- [Issues worth noting but not blocking — max 5]

### Verified
- [Things that are correct and well-done]
```

## Cross-model verification (optional)

After the review is written, consider running `/review-x` for a second opinion from a different AI model. This is most valuable for:
- Security-sensitive changes
- Complex architectural decisions
- Changes where you're uncertain about your own findings

`/review-x` works with any model — no API keys needed. See `/review-x` for details.

## Rules
- Security has blocking veto on dependency changes, auth changes, and external code.
- If there are no blocking issues across all three personas, the review passes.
- If there are blocking issues, list the fixes needed and wait for them to be addressed before approving.
- Write the review to `tasks/review-[topic].md` so it persists.
- Do not rubber-stamp. If everything looks perfect, look harder.
