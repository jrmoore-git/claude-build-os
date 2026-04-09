---
description: Code quality standards, review rules, and input validation requirements
---

# Code Quality

Avoid over-engineering. Only make changes that are directly requested or clearly necessary:
- Don't add features, refactor code, or make "improvements" beyond what was asked.
- Don't add docstrings, comments, or type annotations to code you didn't change.
- Don't add error handling or validation for scenarios that can't happen.
- Don't create helpers, utilities, or abstractions for one-time operations.
- Don't design for hypothetical future requirements.
- No nesting deeper than 3 levels. Use guard clauses.
- Write boring code. Explicit loops over nested comprehensions. Named variables over inline expressions.

**Core principles:** Simplicity first. No laziness — root causes only. Senior developer standards. Don't over-engineer.

## Anti-Slop Vocabulary

Never use these words in output, docs, commit messages, or generated content: delve, crucial, robust, comprehensive, nuanced, leverage, facilitate, utilize, streamline, cutting-edge, state-of-the-art, paradigm, synergy, holistic, empower, innovative, seamless, transformative. Use plain, direct language instead.

## Exceptions

- Toolbelt scripts (`scripts/*_tool.py`) validate everything at entry points. Internal code trusts validated inputs.
- Interface contracts between parallel components: define before building.

## Input Validation — Human-Provided IDs

Human-provided IDs (external document IDs, calendar event IDs, resource IDs) must be cross-referenced against a known-good reference before extraction runs.

**Pattern:** Given a human-provided ID `A` and a retrieved record from `A`, verify that `A` shares ≥1 key attribute (e.g., attendee email, date range) with independently sourced context (e.g., calendar event, stated meeting name). If no overlap → STOP and ask for confirmation.

**Rationale:** Wrong document ID passed by human → data misattributed to wrong people. The validation cost is trivial; the misattribution cost is high.

This applies to any skill that accepts IDs from humans and retrieves records by ID.

## Identity Resolution — No Heuristic Aliasing

Don't build identity resolution on heuristics. An email address is a lookup key — use it exactly as given. Alias tables that pick "canonical" emails via shortest-string or domain-priority heuristics silently remap to wrong addresses. If someone queries `alice@example.com`, look up that exact address. The cost of duplicate cache entries is negligible; the cost of wrong lookups is high.

*Origin: alias-table heuristics returned wrong email addresses for contact lookups.*

## Domain-Specific Rules

For bulk data mutations, SQLite pitfalls, database queries, and testing patterns, see `.claude/rules/reference/code-quality-detail.md`. Read it when working with databases, pipelines, or test infrastructure.

**WARNING:** Never modify or delete >10 database records without first reading the bulk mutation rules in `reference/code-quality-detail.md`. Human confirmation is required.
