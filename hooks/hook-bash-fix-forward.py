#!/usr/bin/env python3.11
"""PreToolUse hook: block common bash bandaid patterns, force investigation first.

Reads JSON from stdin (Claude Code hook contract), checks for known
bandaid commands, returns {"permissionDecision":"ask","message":"..."}
to prompt, or {} to allow.

Patterns blocked:
  - rm .git/index.lock (without investigating what holds it)
  - kill -9 / pkill (without identifying the process)
  - rm *.lock / *.pid glob deletions (without checking lsof/fuser)
"""
import json
import re
import sys


def check_command(cmd):
    """Return a warning message if cmd matches a bandaid pattern, else None."""

    # 1. rm .git/index.lock (any path variant)
    if re.search(r'\brm\s+(-[a-zA-Z]*\s+)*[^\s]*\.git/index\.lock\b', cmd):
        return (
            "[fix-forward] Do not blindly delete git locks. "
            "Investigate first: lsof .git/index.lock, pgrep git, "
            "or ps aux | grep git. Remove only after confirming "
            "no git process holds the lock."
        )

    # 2. kill -9 / kill -KILL / kill -SIGKILL
    if re.search(r'\bkill\s+-(9|KILL|SIGKILL)\b', cmd):
        return (
            "[fix-forward] Do not force-kill blindly. "
            "Identify the process and why it is stuck first: "
            "ps aux | grep <name>, lsof, or launchctl list. "
            "A graceful kill (without -9) after identification is acceptable."
        )

    # 3. pkill (any invocation)
    if re.search(r'\bpkill\s+', cmd):
        return (
            "[fix-forward] Do not pkill blindly. "
            "Identify what is running and why first: "
            "ps aux | grep <name>, pgrep -a <name>. "
            "Then kill the specific PID gracefully."
        )

    # 4. rm *.lock or rm *.pid (glob deletion of lock/pid files)
    if re.search(r'\brm\s+(-[a-zA-Z]*\s+)*\S*\*\.(lock|pid)\b', cmd):
        return (
            "[fix-forward] Do not delete lock/pid files blindly. "
            "Check whether the file is still in use: "
            "lsof <file> or fuser <file>."
        )

    return None


def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        print("{}")
        return

    cmd = data.get("tool_input", {}).get("command", "")
    if not cmd:
        print("{}")
        return

    warning = check_command(cmd)
    if warning:
        result = {"permissionDecision": "ask", "message": warning}
        print(json.dumps(result))
    else:
        print("{}")


if __name__ == "__main__":
    main()
