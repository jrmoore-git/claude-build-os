#!/usr/bin/env python3.11
"""
hook-decompose-gate.py — PreToolUse hook that nudges toward worktree
fan-out when a session starts editing multiple distinct files.

Advisory, not blocking. Emits a prompt hint via `additionalContext`;
does not deny. The agent receives the nudge and decides whether to
fan out or proceed.

Reads tool call JSON from stdin. Returns JSON to allow (with or
without additionalContext).

Four informational states:
  1. Worktree agent     → silent allow
  2. Flag has bypass    → silent allow
  3. Flag has plan+main → advisory nudge (declared fan-out but writing from main)
  4. 2nd unique file    → advisory nudge (consider fan-out)
Otherwise silent.

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
    ctx = os.environ.get("ORCHESTRATION_CONTEXT", "")
    if ctx.startswith("worktree"):
        return True
    if ctx == "main":
        return False

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

    return False


NUDGE_MESSAGES = {
    "escalated": (
        "Decomposition nudge: this session has now edited a second distinct file. "
        "If the work breaks into 2+ independent components, consider dispatching "
        "worktree agents instead of editing from the main session. If components "
        "share state, proceed and note the reason in the current plan artifact."
    ),
    "plan_declared": (
        "Decomposition nudge: a parallel plan was declared this session (plan_submitted), "
        "but this Write|Edit is happening in the main session instead of a worktree agent. "
        "If fan-out is still the intent, dispatch the agents; if the plan changed, clear "
        "the flag and proceed."
    ),
}


def _with_context(kind):
    """Return a PreToolUse allow-with-additionalContext payload."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "additionalContext": NUDGE_MESSAGES[kind],
        }
    }


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

    # Worktree agents are the goal state — never nudge them.
    if is_worktree_agent():
        print("{}")
        return

    session_id = get_session_id()
    flag_path = get_flag_path(session_id)

    # Explicit bypass or plan-submitted flag → honor it
    if flag_path.exists():
        sentinel = Path(f"/tmp/claude-decompose-{session_id}.pending")
        sentinel.unlink(missing_ok=True)

        try:
            flag_data = json.loads(flag_path.read_text())
        except (json.JSONDecodeError, OSError):
            # Corrupt flag — silent allow, the next clean write resets the state
            print("{}")
            return

        if flag_data.get("bypass"):
            print("{}")
            return
        if flag_data.get("plan_submitted"):
            # Plan declared parallel work but we're in the main session.
            # Nudge once per session via the writes log; don't spam every write.
            nudge_marker = Path(f"/tmp/claude-decompose-{session_id}.plan-nudged")
            if nudge_marker.exists():
                print("{}")
                return
            try:
                nudge_marker.touch()
            except OSError:
                pass
            print(json.dumps(_with_context("plan_declared")))
            return

    # Track writes to detect the 2nd-unique-file moment
    writes_log = Path(f"/tmp/claude-decompose-{session_id}.writes")
    tool_input = data.get("tool_input", {})
    current_file = tool_input.get("file_path", "unknown")

    written_files = set()
    if writes_log.exists():
        try:
            written_files = set(json.loads(writes_log.read_text()))
        except (json.JSONDecodeError, OSError):
            written_files = set()

    # First write or same file as before — silent allow
    if len(written_files) == 0 or (written_files == {current_file}):
        written_files.add(current_file)
        try:
            writes_log.write_text(json.dumps(list(written_files)))
        except OSError:
            pass
        print("{}")
        return

    # Second unique file — nudge once, then stay silent
    nudge_marker = Path(f"/tmp/claude-decompose-{session_id}.nudged")
    already_nudged = nudge_marker.exists()

    written_files.add(current_file)
    try:
        writes_log.write_text(json.dumps(list(written_files)))
    except OSError:
        pass

    if already_nudged:
        print("{}")
        return

    try:
        nudge_marker.touch()
    except OSError:
        pass

    print(json.dumps(_with_context("escalated")))


if __name__ == "__main__":
    main()
