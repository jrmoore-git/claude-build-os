#!/usr/bin/env python3
"""
hook-agent-isolation.py — PreToolUse hook that enforces worktree isolation
on write-capable Agent dispatches when a parallel plan is active.

When session flag is plan_submitted: true, blocks Agent calls that:
- Have a write-capable subagent_type (general-purpose or unspecified)
- Do NOT specify isolation: "worktree"

Also warns (non-blocking) when worktree agents receive absolute repo paths
in their prompts, which bypasses isolation entirely (L23).

Read-only subagent types are exempt (Explore, Plan, claude-code-guide, statusline-setup).
If no flag file or flag is bypass: allow everything.
"""

import json
import os
import re
import sys
from pathlib import Path

READ_ONLY_TYPES = frozenset({
    "Explore",
    "Plan",
    "claude-code-guide",
    "statusline-setup",
})

REPO_ROOT = os.environ.get(
    "PROJECT_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

DENY_MESSAGE = (
    "AGENT ISOLATION GATE: Your session plan declared parallel decomposition "
    "(plan_submitted: true), but this Agent dispatch does not specify "
    'isolation: "worktree". Write-capable parallel agents MUST use worktree '
    "isolation to prevent file collisions and index.lock contention. "
    "Fix: add `isolation: \"worktree\"` to this Agent call, "
    "or use a read-only subagent_type (Explore, Plan, claude-code-guide)."
)

ABS_PATH_MESSAGE = (
    "WORKTREE PATH WARNING: This worktree agent's prompt contains absolute "
    "paths to the main checkout ({repo_root}/...). Absolute paths bypass "
    "worktree isolation — the agent will write to the MAIN checkout, not its "
    "worktree copy. Use relative paths instead:\n"
    "  Wrong: {repo_root}/primitives/synthesis.py\n"
    "  Right: primitives/synthesis.py\n"
    "Found {count} absolute repo path(s) in the prompt. "
    "Rewrite the prompt with relative paths."
)


def get_session_id():
    sid = os.environ.get("CLAUDE_SESSION_ID", "")
    if sid:
        return sid
    return str(os.getppid())


def get_flag_path(session_id):
    return Path(f"/tmp/claude-decompose-{session_id}.json")


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
    if tool_name != "Agent":
        print("{}")
        return

    session_id = get_session_id()
    flag_path = get_flag_path(session_id)

    # No flag file — gate hasn't fired yet, allow
    if not flag_path.exists():
        print("{}")
        return

    try:
        flag_data = json.loads(flag_path.read_text())
    except (json.JSONDecodeError, OSError):
        # Corrupt flag — fail closed (deny to prevent bypass via corruption)
        result = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"AGENT ISOLATION GATE: Flag file at {flag_path} is corrupt "
                    "or unreadable. Delete it and re-create: "
                    f"rm {flag_path} && echo '{{\"bypass\": true, "
                    f"\"reason\": \"<why>\"}}' > {flag_path}"
                ),
            }
        }
        print(json.dumps(result))
        return

    # Only enforce when plan_submitted is true (not bypass)
    if not flag_data.get("plan_submitted"):
        print("{}")
        return

    tool_input = data.get("tool_input", {})
    subagent_type = tool_input.get("subagent_type", "")
    isolation = tool_input.get("isolation", "")

    # Read-only subagent types are exempt
    if subagent_type in READ_ONLY_TYPES:
        print("{}")
        return

    # Write-capable agent must have worktree isolation
    if isolation == "worktree":
        # Check for absolute repo paths in the prompt (L23)
        prompt = tool_input.get("prompt", "")
        abs_path_pattern = re.escape(REPO_ROOT) + r"/\S+"
        abs_matches = re.findall(abs_path_pattern, prompt)
        if abs_matches:
            result = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": ABS_PATH_MESSAGE.format(
                        repo_root=REPO_ROOT,
                        count=len(abs_matches),
                    ),
                }
            }
            print(json.dumps(result))
            return
        print("{}")
        return

    # Deny — missing worktree isolation on write-capable agent
    result = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": DENY_MESSAGE,
        }
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
