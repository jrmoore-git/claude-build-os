---
type: proposal
topic: debate-tools-fix
status: draft
---

# Proposal: Fix debate_tools.py Search/Discovery Gap

## Problem

In session 18, challenger models (Claude Opus, GPT-5.4) falsely concluded BuildOS hooks don't exist. Root cause: `ALLOWED_FILE_SETS` in `debate_tools.py` only includes `scripts`, `skills`, `config`. The `check_code_presence` and `check_function_exists` tools expose this as an enum — models literally cannot request `file_set="hooks"`. Meanwhile, `read_file_snippet` already allows reading from `hooks/` and `tests/` — the tools are internally inconsistent.

Opus ran 54 tool calls searching every allowed file set, found nothing, and concluded hooks don't exist. GPT-5.4 made the same error in 8 calls. The judge accepted the false claim at 0.98 confidence.

## Operational Evidence

- L33: `--enable-tools` produced false verification claims with high confidence
- Session 18 challenge: 20 minutes wall-clock, ~100K tokens, 2 of 5 MATERIAL findings were factually wrong
- The false "hooks don't exist" claim cascaded through judge evaluation, producing a REJECT recommendation based on false evidence
- `read_file_snippet` already sends source code to external models (GPT, Gemini) — search/discovery tools return strictly less sensitive data (paths, booleans)

## Proposed Changes

All changes in `scripts/debate_tools.py` only. Single file change + tests.

### Change 1: Align ALLOWED_FILE_SETS with ALLOWED_SNIPPET_PATHS

Current:
```python
ALLOWED_FILE_SETS = {
    "scripts": "scripts/*.py",
    "skills": ".claude/skills/*/SKILL.md",
    "config": "config/*.json",
}
```

Proposed:
```python
ALLOWED_FILE_SETS = {
    "scripts": "scripts/*.py",
    "skills": ".claude/skills/*/SKILL.md",
    "config": "config/*.json",
    "hooks": "hooks/*.py",
    "tests": "tests/*.py",
    "rules": ".claude/rules/*.md",
    "docs": "docs/*.md",
}
```

This makes `check_code_presence` and `check_function_exists` searchable across all directories that `read_file_snippet` can already read, plus `rules/` and `docs/` which challengers frequently need to verify governance claims.

### Change 2: Add list_files tool

New tool: `list_files(directory, pattern)` — returns file paths matching a glob within allowed directories. Returns paths only, no content.

Purpose: Discovery. Prevents the "I don't know what directories exist" blind spot. A challenger can list the project root and see `hooks/`, `tests/`, `scripts/`, etc. before searching.

Constraints:
- Only list within allowed directories (same set as ALLOWED_SNIPPET_PATHS + rules, docs)
- Returns paths only, max 50 results
- No secret-pattern files returned
- No recursive traversal beyond one level

### Change 3: Add docs/ and rules/ to ALLOWED_SNIPPET_PATHS

Current ALLOWED_SNIPPET_PATHS: scripts/, config/, tests/, hooks/
Proposed: add docs/, .claude/rules/

These are markdown files — less sensitive than code. Challengers need to verify governance and documentation claims ("does a rule exist for X?", "does the PRD mention Y?").

## What This Does NOT Change

- `read_file_snippet` limit stays at 50 lines — sufficient for fact-checking
- Security model unchanged: no secrets, no writes, structured metadata for search tools
- No new external API surface: `read_file_snippet` already sends code to external models
- `get_recent_commits` unchanged — commit messages only, no diffs
- `read_config_value` unchanged — still limited to debate-models.json keys
- No new tools beyond `list_files`

## Expected Impact

- Challengers can verify claims about hooks, tests, rules, and docs
- The session 18 failure (false "hooks don't exist" claim) would not recur
- `list_files` prevents future blind spots when new directories are added
- Tool call count may decrease — models find what they need faster instead of exhausting wrong file sets

## Risks

- More directories searchable = more code sent to external models via read_file_snippet (already the case for hooks/ and tests/)
- list_files could return a lot of paths — capped at 50 results
- Adding docs/ means proposal text visible to challengers (but proposals are already passed as input)
