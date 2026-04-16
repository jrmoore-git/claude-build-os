#!/usr/bin/env python3.11
"""
hook-decompose-gate.py — PreToolUse hook that gates Write|Edit until a
decomposition plan exists for the session.

Reads tool call JSON from stdin. Returns JSON to allow or deny.

Four states:
  1. No flag file + write tool → DENY with decomposition prompt
  2. Flag file with plan_submitted + main session → DENY (dispatch agents first)
  3. Flag file with plan_submitted + worktree agent → ALLOW
  4. Flag file with bypass → ALLOW

Flag file: /tmp/claude-decompose-{session_id}.json
Session ID: $CLAUDE_SESSION_ID env var, fallback to parent PID.
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

REPO_ROOT = os.environ.get(
    "PROJECT_ROOT",
    str(Path(__file__).resolve().parent.parent),
)


def get_session_id():
    sid = os.environ.get("CLAUDE_SESSION_ID", "")
    if sid:
        return sid
    return str(os.getppid())


def get_flag_path(session_id):
    return Path(f"/tmp/claude-decompose-{session_id}.json")


def is_worktree_agent():
    """Detect if running inside a git worktree (not the main repo)."""
    # Explicit env var set by orchestration (preferred)
    ctx = os.environ.get("ORCHESTRATION_CONTEXT", "")
    if ctx.startswith("worktree"):
        return True
    if ctx == "main":
        return False

    # Fallback: check if git toplevel differs from known repo root
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=2,
        )
        if result.returncode == 0:
            toplevel = result.stdout.strip()
            return toplevel != REPO_ROOT
    except (subprocess.TimeoutExpired, OSError):
        pass

    # Can't determine — fail closed (treat as main session)
    return False


USER_MESSAGES = {
    "escalated": (
        "Decomposition check: this session is about to edit a second distinct file. "
        "If the work breaks into 3+ independent components, dispatch worktree agents "
        "instead of editing from the main session. Otherwise, say 'skip decomposition' "
        "and I'll proceed."
    ),
    "plan_declared": (
        "Decomposition check: a parallel plan was declared this session. Dispatch the "
        "worktree agents before editing from the main session, or say 'skip decomposition' "
        "to proceed here."
    ),
    "missing_reason": (
        "Decomposition bypass is missing a reason — add one so the audit trail stays complete."
    ),
    "corrupt": (
        "The session's decomposition flag file is corrupt. Clear it and set a fresh bypass "
        "with a reason."
    ),
}


def _reason(kind, flag_path):
    """Compose user-readable message + trailing agent-only bypass hint."""
    agent_hint = (
        f"\n\n[agent: bypass via Bash → "
        f"echo '{{\"bypass\": true, \"reason\": \"<why>\"}}' > {flag_path}]"
    )
    return USER_MESSAGES[kind] + agent_hint


def main():
    try:
        raw = sys.stdin.read()
    except Exception:
        # Can't read stdin — allow to avoid blocking
        print("{}")
        return

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        print("{}")
        return

    tool_name = data.get("tool_name", "")

    # Only gate Write and Edit tools
    if tool_name not in ("Write", "Edit"):
        print("{}")
        return

    session_id = get_session_id()
    flag_path = get_flag_path(session_id)

    # Check if plan or bypass already submitted
    if flag_path.exists():
        # Clean up the pending sentinel now that the real flag exists
        sentinel = Path(f"/tmp/claude-decompose-{session_id}.pending")
        sentinel.unlink(missing_ok=True)

        try:
            flag_data = json.loads(flag_path.read_text())
            if flag_data.get("bypass"):
                # Bypass requires a reason for audit trail
                if not flag_data.get("reason"):
                    result = {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": _reason("missing_reason", flag_path),
                        }
                    }
                    print(json.dumps(result))
                    return
                print("{}")
                return
            if flag_data.get("plan_submitted"):
                # Plan declared parallel work — block main-session writes
                if is_worktree_agent():
                    print("{}")
                    return
                # Main session trying to write after declaring parallel plan
                result = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": _reason("plan_declared", flag_path),
                    }
                }
                print(json.dumps(result))
                return
        except (json.JSONDecodeError, OSError):
            # Corrupt flag file — deny with recovery message
            result = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": _reason("corrupt", flag_path),
                }
            }
            print(json.dumps(result))
            return

    # No flag file — track writes and escalate progressively.
    # First write: allow with a warning (most tasks are single-file).
    # Second write to a DIFFERENT file: deny and require decomposition assessment.
    writes_log = Path(f"/tmp/claude-decompose-{session_id}.writes")

    # Parse the file path from the tool input
    tool_input = data.get("tool_input", {})
    current_file = tool_input.get("file_path", "unknown")

    # Load existing writes log
    written_files = set()
    if writes_log.exists():
        try:
            written_files = set(json.loads(writes_log.read_text()))
        except (json.JSONDecodeError, OSError):
            written_files = set()

    # First write or same file as before — allow with advisory
    if len(written_files) == 0 or (written_files == {current_file}):
        written_files.add(current_file)
        try:
            writes_log.write_text(json.dumps(list(written_files)))
        except OSError:
            pass
        # Allow but remind about decomposition
        print("{}")
        return

    # Second+ unique file without a plan — deny and require assessment
    written_files.add(current_file)
    try:
        writes_log.write_text(json.dumps(list(written_files)))
    except OSError:
        pass

    result = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": _reason("escalated", flag_path),
        }
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
