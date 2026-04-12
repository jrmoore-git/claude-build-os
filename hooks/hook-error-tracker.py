#!/usr/bin/env python3.11
"""PostToolUse hook (Bash): track recurring errors for proactive /investigate routing.

Watches Bash tool calls for failure patterns. When the same error class
appears 2+ times in a session, sets a flag that hook-intent-router.py
reads on the next UserPromptSubmit to suggest /investigate.

Tracks by error signature (command pattern + exit status), not exact output.
This catches "same thing keeps failing" without needing exact output matching.

Output: empty (this hook observes only, never blocks).
"""
import hashlib
import json
import os
import re
import sys

SESSION_ID = os.environ.get("CLAUDE_SESSION_ID", str(os.getppid()))
ERROR_TRACKER_FILE = f"/tmp/claude-error-tracker-{SESSION_ID}.json"


def load_tracker():
    if not os.path.exists(ERROR_TRACKER_FILE):
        return {}
    try:
        with open(ERROR_TRACKER_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_tracker(data):
    try:
        with open(ERROR_TRACKER_FILE, "w") as f:
            json.dump(data, f)
    except OSError:
        pass


def normalize_command(cmd):
    """Extract the core command pattern, stripping variable parts.

    Groups by base command + subcommand (e.g., 'npm test', 'git push').
    Ignores flags so 'npm test' and 'npm test --verbose' are the same class.
    """
    cmd = cmd.strip()
    # Extract just the first command (before pipes/chains)
    first_cmd = re.split(r'[|;&]', cmd)[0].strip()
    parts = first_cmd.split()
    if not parts:
        return ""
    base = os.path.basename(parts[0])
    # Include first 1-2 positional args (subcommands), skip flags
    subcommands = [p for p in parts[1:] if not p.startswith('-')][:2]
    return f"{base} {' '.join(subcommands)}".strip()


def make_signature(cmd, exit_code):
    """Create a stable signature for this error class."""
    pattern = normalize_command(cmd)
    sig_input = f"{pattern}:exit{exit_code}"
    return hashlib.md5(sig_input.encode()).hexdigest()[:12]


def extract_error_info(data):
    """Extract command and error indicators from PostToolUse hook input."""
    tool_input = data.get("tool_input", {})
    cmd = tool_input.get("command", "")

    # Try multiple fields for output/exit code
    # Claude Code PostToolUse may provide these in different locations
    result = data.get("tool_result", data.get("result", {}))
    if isinstance(result, str):
        output = result
        # Infer failure from output content
        exit_code = 1 if any(
            kw in output.lower()
            for kw in ["error", "traceback", "failed", "not found", "permission denied"]
        ) else 0
    elif isinstance(result, dict):
        output = result.get("stdout", "") + result.get("stderr", "")
        exit_code = result.get("exit_code", result.get("exitCode", 0))
    else:
        output = ""
        exit_code = data.get("tool_result_exit_code", 0)

    return cmd, output, exit_code


def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return

    cmd, output, exit_code = extract_error_info(data)
    if not cmd:
        return

    # Only track failures (non-zero exit or error-like output)
    is_error = False
    if exit_code and exit_code != 0:
        is_error = True
    elif output and any(
        kw in output.lower()
        for kw in ["error:", "traceback", "failed", "fatal:", "exception"]
    ):
        is_error = True

    if not is_error:
        return

    # Track this error
    sig = make_signature(cmd, exit_code)
    tracker = load_tracker()

    if sig in tracker:
        tracker[sig]["count"] = tracker[sig].get("count", 0) + 1
    else:
        # Summarize the error for the intent router
        summary = normalize_command(cmd)
        if exit_code:
            summary += f" (exit {exit_code})"
        tracker[sig] = {
            "count": 1,
            "summary": summary,
            "command": cmd[:200],  # truncate for safety
        }

    save_tracker(tracker)


if __name__ == "__main__":
    main()
