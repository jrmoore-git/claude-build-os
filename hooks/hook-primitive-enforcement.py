#!/usr/bin/env python3
"""
hook-primitive-enforcement.py — PreToolUse hook that blocks direct DB access
outside of primitives/ and scripts/*_tool.py.

Prevents regression to N×M wiring by catching:
  - `import sqlite3` / `from sqlite3 import` / `import sqlite3 as` in non-primitive code
  - `__import__("sqlite3")` / `__import__('sqlite3')` dynamic imports
  - `sqlite3.connect` in non-primitive code
  - Direct references to stores/*.db paths in non-primitive code
  - `aiosqlite` usage in non-primitive code
  - `APP_STORE_DIR` combined with `.db` in non-primitive code

Allowed paths:
  - primitives/*.py (they own the DB tables)
  - scripts/*_tool.py (existing toolbelt — migrating in Session 3)
  - tests/*.py (need DB access for test fixtures)
  - scripts/db_inspect.py (diagnostic tool)
  - scripts/hook-*.py, scripts/verify_state.py (infrastructure)
  - scripts/deploy_*.sh, scripts/export-*.sh (deployment)

This hook reads the file being written/edited and checks for violations.
"""

import json
import os
import re
import sys

# Paths allowed to use direct DB access
ALLOWED_PATTERNS = [
    r"^primitives/",
    r"^scripts/[a-z_]+_tool\.py$",
    r"^tests/",
    r"^scripts/db_inspect\.py$",
    r"^scripts/hook-",
    r"^scripts/verify_state\.py$",
    r"^scripts/deploy_",
    r"^scripts/export-",
    r"^scripts/recall_search\.py$",
    r"^scripts/update-handoff\.py$",
    r"^scripts/baseline_extraction_test\.py$",
    r"^scripts/debate\.py$",
    r"^scripts/debate_tools\.py$",
    r"^scripts/pipeline_cost\.py$",
    r"^(?!skills/).*\.md$",  # Markdown docs may quote code snippets — but not skills/ (executable)
]

# Patterns that indicate direct DB access
VIOLATION_PATTERNS = [
    (r"\bimport\s+sqlite3\b", "direct sqlite3 import"),
    (r"\bfrom\s+sqlite3\s+import\b", "from sqlite3 import (use primitive instead)"),
    (r"\bimport\s+sqlite3\s+as\b", "aliased sqlite3 import (use primitive instead)"),
    (r"\bsqlite3\.connect\b", "direct sqlite3.connect call"),
    (r'__import__\s*\(\s*["\']sqlite3', "dynamic sqlite3 import via __import__"),
    (r"stores/promises\.db", "direct path to promises.db (use open_loop primitive)"),
    (r"stores/context\.db", "direct path to context.db (use person/event/signal primitives)"),
    (r"stores/audit\.db", "direct path to audit.db (use primitive audit helpers)"),
    (r'["\']promises\.db["\']', "promises.db string literal (use open_loop primitive)"),
    (r'["\']context\.db["\']', "context.db string literal (use person/event/signal primitives)"),
    (r"\baiosqlite\b", "aiosqlite usage (use primitive instead of direct DB access)"),
    (r"\bAPP_STORE_DIR\b.*\.db", "APP_STORE_DIR + .db reference (use primitive instead)"),
]

REPO_ROOT = os.environ.get(
    "PROJECT_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def is_allowed(file_path):
    """Check if a file is in the allowed list for direct DB access."""
    rel = os.path.relpath(file_path, REPO_ROOT)
    # Strip worktree prefix so allowlist patterns match correctly
    # e.g. .claude/worktrees/<id>/scripts/hook-foo.py -> scripts/hook-foo.py
    worktree_match = re.match(r"\.claude/worktrees/[^/]+/(.*)", rel)
    if worktree_match:
        rel = worktree_match.group(1)
    for pattern in ALLOWED_PATTERNS:
        if re.search(pattern, rel):
            return True
    return False


def check_content(content, file_path):
    """Check file content for direct DB access violations."""
    violations = []
    rel = os.path.relpath(file_path, REPO_ROOT)
    # Strip worktree prefix for display
    worktree_match = re.match(r"\.claude/worktrees/[^/]+/(.*)", rel)
    if worktree_match:
        rel = worktree_match.group(1)
    for pattern, desc in VIOLATION_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            violations.append(f"{rel}: {desc} ({len(matches)} occurrence{'s' if len(matches) > 1 else ''})")
    return violations


def main():
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    # Skip allowed paths
    if is_allowed(file_path):
        sys.exit(0)

    # For Write tool: check the content being written
    # For Edit tool: check the new_string being inserted
    content_to_check = ""
    if tool_name == "Write":
        content_to_check = tool_input.get("content", "")
    elif tool_name == "Edit":
        content_to_check = tool_input.get("new_string", "")

    if not content_to_check:
        sys.exit(0)

    violations = check_content(content_to_check, file_path)
    if violations:
        msg = (
            "PRIMITIVE ENFORCEMENT: Direct DB access detected outside primitives/.\n"
            "Use the appropriate primitive instead:\n"
            "  - promises.db → from primitives import open_loop\n"
            "  - context.db (dossiers, contact_*) → from primitives import person\n"
            "  - context.db (meeting_*) → from primitives import event\n"
            "  - context.db (people_signals_v2) → from primitives import signal\n"
            "\nViolations:\n" + "\n".join(f"  - {v}" for v in violations)
        )
        result = {"decision": "block", "reason": msg}
        json.dump(result, sys.stdout)
        sys.exit(0)

    # No violations — allow
    sys.exit(0)


if __name__ == "__main__":
    main()
