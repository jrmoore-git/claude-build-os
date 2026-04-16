#!/usr/bin/env python3.11
"""
hook-memory-size-gate.py — PreToolUse hook that blocks MEMORY.md writes
when the file is already at or above the line limit.

Prevents MEMORY.md bloat by requiring pruning before adding new content.
Fires on Write|Edit targeting any path ending in memory/MEMORY.md.

Line limit: 150 lines. If the file is at or above 150 lines AND the
edit/write would add lines, the hook blocks with a pruning message.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Tier gate: requires tier >= 2
_project = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True
).stdout.strip()
_tier_result = subprocess.run(
    ["/opt/homebrew/bin/python3.11", os.path.join(_project, "scripts/read_tier.py"), "--check", "2"],
    capture_output=True
)
if _tier_result.returncode != 0:
    sys.exit(0)

LINE_LIMIT = 150


def count_lines(filepath):
    """Count lines in a file. Returns 0 if file doesn't exist."""
    try:
        return len(Path(filepath).read_text().splitlines())
    except (OSError, UnicodeDecodeError):
        return 0


def would_add_lines(tool_name, tool_input, current_lines):
    """Check if the tool operation would increase the line count."""
    if tool_name == "Write":
        content = tool_input.get("content", "")
        new_lines = len(content.splitlines())
        return new_lines > current_lines
    elif tool_name == "Edit":
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        old_count = len(old_string.splitlines())
        new_count = len(new_string.splitlines())
        return new_count > old_count
    return False


def main():
    try:
        raw = sys.stdin.read()
    except Exception:
        print("{}")
        return

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        print("{}")
        return

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        print("{}")
        return

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only gate MEMORY.md writes
    if not file_path.endswith("memory/MEMORY.md"):
        print("{}")
        return

    current_lines = count_lines(file_path)

    # Under limit — allow
    if current_lines < LINE_LIMIT:
        print("{}")
        return

    # At or above limit — check if adding lines
    if not would_add_lines(tool_name, tool_input, current_lines):
        # Edit that removes or keeps same line count — allow (pruning)
        print("{}")
        return

    # Block: file is at limit and edit would add lines
    message = (
        f"MEMORY.md is at {current_lines} lines (limit: {LINE_LIMIT}). "
        "Prune old entries before adding new ones. "
        "Remove resolved projects, archive historical status, "
        "or move detail into topic files."
    )
    result = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
