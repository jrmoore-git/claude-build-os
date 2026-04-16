---
scope: "Add PreToolUse hook that injects relevant context (test file, local imports, git history) before Write/Edit"
surfaces_affected: "hooks/hook-context-inject.py (new), .claude/settings.json, CLAUDE.md, docs/hooks.md, tests/"
verification_commands: "python3.11 -m pytest tests/test_hook_context_inject.py -v && python3.11 hooks/hook-context-inject.py < /tmp/test-hook-input.json"
rollback: "git revert HEAD — remove hook file, revert settings.json and CLAUDE.md changes"
review_tier: "Tier 1"
verification_evidence: "17/17 hook tests pass, 889/889 full suite passes. Manual test confirms context injection for debate.py (imports + git), tier_classify.py (test file + git), silent exit for non-Python and new files."
---

# Plan: Context Injection Hook (P1)

## Problem
Most Claude slop is context failure — Claude writes code without having loaded the target file's test file, imported module signatures, or recent change history. Current hooks catch errors after generation (syntax-check, ruff, read-before-edit). No hook prevents errors by providing context before generation.

## Design

**Hook:** `hooks/hook-context-inject.py`
**Event:** PreToolUse Write|Edit
**Tier:** T0 (always active, informational only, never blocks)
**Output:** `permissionDecision: "allow"` + `additionalContext` with gathered context

### What it injects

For Python files being edited:
1. **Test file summary** — find `tests/test_<name>.py`, extract test function/class names (max 15)
2. **Local import signatures** — resolve local imports to files, extract def/class signatures (max 5 modules, 10 sigs each)
3. **Recent git history** — last 5 commits touching this file

### What it skips
- Non-Python files (v1 scope)
- New file creation (file doesn't exist yet)
- Files outside the project root

### Constraints
- Must complete in < 2 seconds (hook timeout)
- Context capped at 3000 chars
- No external dependencies (stdlib only)
- No blocking — always returns `allow`

## Files

| File | Action |
|------|--------|
| `hooks/hook-context-inject.py` | Create — the hook |
| `tests/test_hook_context_inject.py` | Create — unit tests |
| `.claude/settings.json` | Edit — wire hook into PreToolUse:Write\|Edit |
| `CLAUDE.md` | Edit — update hook count 21→22 |
| `docs/hooks.md` | Edit — add hook documentation |
