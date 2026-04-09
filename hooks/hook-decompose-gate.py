#!/usr/bin/env python3
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


DECOMPOSE_MESSAGE = (
    "DECOMPOSITION GATE: This is your first write operation this session. "
    "Before proceeding, assess whether this task involves multiple independent subtasks. "
    "If YES (3+ independent files/subtasks): output a decomposition plan listing each subtask, "
    "its file scope, and whether it runs parallel or sequential. Then write the flag "
    "(use Bash tool, NOT Write tool): "
    'echo \'{"plan_submitted": true}\' > FLAG_PATH — then proceed with parallel agents. '
    "If NO (single file or tightly coupled): write the bypass flag "
    "(use Bash tool, NOT Write tool): "
    'echo \'{"bypass": true, "reason": "<why>"}\' > FLAG_PATH — then proceed normally. '
    "If the user said 'skip' or 'just do it': write the bypass flag and proceed."
)


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
                    no_reason_msg = (
                        "EXECUTION GATE: Bypass flag found but missing 'reason' field. "
                        "All bypasses must include a stated reason for audit. "
                        "Update the flag (use Bash tool): "
                        f"echo '{{\"bypass\": true, \"reason\": \"<why>\"}}' > {flag_path}"
                    )
                    result = {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": no_reason_msg,
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
                block_msg = (
                    "EXECUTION GATE: Your session declared a parallel plan "
                    "(plan_submitted: true), but you are writing directly from "
                    "the main session. Dispatch worktree-isolated agents for "
                    "the planned subtasks, or update the flag to bypass with a "
                    "reason (use Bash tool): "
                    f"echo '{{\"bypass\": true, \"reason\": \"<why>\"}}' > {flag_path}"
                )
                result = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": block_msg,
                    }
                }
                print(json.dumps(result))
                return
        except (json.JSONDecodeError, OSError):
            # Corrupt flag file — deny with recovery message
            recover_msg = (
                f"DECOMPOSITION GATE: Flag file at {flag_path} is corrupt or unreadable. "
                "Delete it and re-create: "
                f"rm {flag_path} && echo '{{\"bypass\": true, \"reason\": \"<why>\"}}' > {flag_path}"
            )
            result = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": recover_msg,
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

    message = DECOMPOSE_MESSAGE.replace("FLAG_PATH", str(flag_path))
    escalated_msg = (
        f"DECOMPOSITION GATE: You have now written to {len(written_files)} different files "
        f"({', '.join(os.path.basename(f) for f in sorted(written_files))}) without a "
        "decomposition assessment. " + message
    )
    result = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": escalated_msg,
        }
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
