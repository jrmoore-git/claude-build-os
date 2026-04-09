# CLAUDE.md

<!-- Target: under 200 lines. Every line loads into every turn and consumes context. -->

## What this project is

Bookmark CLI — a command-line tool for saving, tagging, and searching web bookmarks. Built in Python 3.11 with SQLite storage. Used by a solo developer who saves ~20 bookmarks/day and needs fast tag-based search.

## Operating rules

### Simplicity is the override rule
Avoid over-engineering. Only make changes that are directly requested or clearly necessary. Keep solutions simple and focused.
- Don't add features, refactor code, or make "improvements" beyond what was asked.
- Don't add error handling for scenarios that can't happen.
- Don't create abstractions for one-time operations.

### The model may decide; software must act
LLMs classify, summarize, and draft. Deterministic code performs state transitions, API calls, and data mutations.

### Retrieve before planning
Read handoff.md and current-state.md before starting work. Check lessons.md before touching the database layer.

### Challenge before planning, plan before building
If work introduces new abstractions, dependencies, infrastructure, generalization, or scope expansion — run `/challenge` first.
Write a plan to disk if more than 3 files change or user-facing behavior changes.
Skip both for: bugfixes, test-only changes, docs, `[TRIVIAL]`.

### Document results
Update decisions.md after material decisions. Update lessons.md after surprises. Update handoff.md before ending incomplete work.

### Verify before declaring done
Run `python -m pytest tests/` after any change to `src/`. A claim of completion is not evidence.

## Project-specific rules

- All bookmark URLs must be validated before INSERT — reject malformed URLs at the CLI boundary, not in the database layer.
- Never modify the `bookmarks` table schema without updating `src/migrations.py`. Direct ALTER TABLE statements break the migration chain.
- The `--export` flag outputs JSON to stdout. Never mix progress messages with JSON output — use stderr for progress.
- SQLite WAL mode is required. Any new database connection must set `PRAGMA journal_mode=WAL`.
- Run `python -m pytest tests/ -x` after any change to `src/`. The `-x` flag stops on first failure.
