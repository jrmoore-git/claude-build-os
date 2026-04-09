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

**Core principles:** Simplicity first. No laziness -- root causes only. Senior developer standards. Don't over-engineer.

## Anti-Slop Vocabulary

Never use these words in output, docs, commit messages, or generated content: delve, crucial, robust, comprehensive, nuanced, leverage, facilitate, utilize, streamline, cutting-edge, state-of-the-art, paradigm, synergy, holistic, empower, innovative, seamless, transformative. Use plain, direct language instead.

## Exceptions

- Toolbelt scripts (`scripts/*_tool.py`) validate everything at entry points. Internal code trusts validated inputs.
- Interface contracts between parallel components: define before building.

## Input Validation -- Human-Provided IDs

Human-provided IDs (document IDs, calendar event IDs, external resource IDs) must be cross-referenced against a known-good reference before extraction runs.

**Pattern:** Given a human-provided ID `A` and a retrieved record from `A`, verify that `A` shares at least one key attribute (e.g., attendee email, date range) with independently sourced context (e.g., calendar event, stated meeting name). If no overlap, STOP and ask for confirmation.

**Rationale:** Wrong document IDs passed by humans cause data misattribution. The validation cost is trivial; the misattribution cost is high.

This applies to any skill that accepts IDs from humans and retrieves records by ID.

## Bulk Data Mutations

Before executing any operation that modifies or deletes >10 records:
1. **Dry-run first:** Run `SELECT COUNT(*)` with the same WHERE clause. Show the count to the user.
2. **Sample preview:** Show `LIMIT 5` of the rows that will be affected.
3. **Explicit confirmation:** Get the user's approval before executing.
4. **Pre-execution audit:** Log the operation to the audit database BEFORE executing (action_type, record count, WHERE clause summary).
5. **Prefer soft deletes:** Use state changes (e.g., `state='dismissed'`) over `DELETE` where schema supports it.

## Ad-hoc Database Queries

Before writing any inline Python that queries a SQLite database, inspect the schema first to get exact column names. NEVER guess column names -- schema mismatches in heredoc Python cause cascading errors that waste time.

## SQLite Pitfalls

- `DEFAULT CURRENT_TIMESTAMP` on `updated_at` only applies at INSERT. It does NOT auto-update on subsequent UPDATEs. Add an AFTER UPDATE trigger: `CREATE TRIGGER <table>_updated_at AFTER UPDATE ON <table> BEGIN UPDATE <table> SET updated_at=datetime('now') WHERE rowid=NEW.rowid; END;`
- Never use bare `except Exception: pass` in skill Python. Always log the error: `except Exception as e: print(f"ERROR: {e}", file=sys.stderr)`. Silent exceptions mask operational failures and prevent debugging.
