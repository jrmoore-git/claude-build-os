# Review Protocol

## When to review

**Full review** for:
- New features or workflow changes
- State transitions or data model changes
- Auth, security, or external dependency changes
- Anything user-facing

**Log-only review** (just note in decisions.md) for:
- Config changes that don't affect behavior
- Formatting, copy edits
- Non-behavioral cleanup

**The test:** Does this change affect how the system behaves? If yes, full review. If no, log only.

## Review order

Review in this sequence:

1. **Architect** — structural issues, boundary violations, unnecessary complexity
2. **Staff Engineer + Security** — implementation quality, auth weaknesses, injection risks
3. **Product / UX** — does it solve the right problem simply enough?

**Security has blocking veto** on dependency changes, auth changes, and external code.

A review is only valid for the code it reviewed. If any covered file has been modified since the review, re-review before committing.

**Growing your review protocol:** Start expanding your persona questions when: (1) the same type of issue escapes review twice, (2) your project crosses into Tier 2, or (3) your team has domain-specific risks (financial data, PII, autonomous actions) that the starter questions don't cover. Create a `PERSONAS.md` file with detailed checklists per persona. Example: a Security persona for a system handling PII might add "Are all personal data fields encrypted at rest?" and "Is there a data retention policy enforced in code?"

## Findings format

For each persona:

- **Blocking** (max 5) — must fix before commit
- **Concerns** (max 5) — worth noting, not blocking
- **Verified** — what's correct and well-done

## Definition of done

A task is not done until:
- [ ] Behavior matches the spec
- [ ] Tests pass (or manual verification with evidence)
- [ ] Integration test verifies data flows end-to-end (or manual checklist exists for multi-process features)
- [ ] Negative cases were checked (what happens when it fails?)
- [ ] Evidence exists (not just "it should work")
- [ ] Rollback is understood
- [ ] Affected docs are updated (decisions, lessons, handoff, PRD)
