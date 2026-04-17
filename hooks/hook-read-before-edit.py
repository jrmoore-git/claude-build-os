#!/usr/bin/env python3
# hook-class: advisory
"""Dual-purpose hook enforcing read-before-edit on protected paths.

Phase 1 (PostToolUse Read): Records which files have been Read this session.
Phase 2 (PreToolUse Write|Edit): Warns if editing a protected file not yet Read.

Tracker: append-only flat text file, one canonicalized path per line.
Session key: $CLAUDE_SESSION_ID or parent PID fallback (same as decompose gate).
New files (don't exist on disk) are exempt — can't Read what doesn't exist.
Exempt paths (tasks/, docs/, tests/, config/, stores/) pass through.
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = None


def get_project_root():
    global PROJECT_ROOT
    if PROJECT_ROOT is None:
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, timeout=2,
            )
            PROJECT_ROOT = result.stdout.strip() if result.returncode == 0 else ""
        except Exception:
            PROJECT_ROOT = ""
    return PROJECT_ROOT


def get_session_id():
    sid = os.environ.get("CLAUDE_SESSION_ID", "")
    if sid:
        # Sanitize to safe filename chars
        import re
        return re.sub(r"[^A-Za-z0-9_.-]", "_", sid)
    return str(os.getppid())


def get_tracker_path():
    return Path(f"/tmp/buildos-read-tracker-{get_session_id()}.txt")


def canonicalize(file_path):
    """Resolve to absolute real path for consistent matching."""
    try:
        p = Path(file_path).resolve()
        return str(p)
    except Exception:
        return file_path


def is_exempt(rel_path):
    """Check if path is exempt from read-before-edit enforcement."""
    exempt_prefixes = ("tasks/", "docs/", "tests/", "config/", "stores/",
                       ".claude/plans/", ".claude/projects/")
    for prefix in exempt_prefixes:
        if rel_path.startswith(prefix):
            return True
    return False


def is_protected(rel_path):
    """Check if path is in protected scope (from config/protected-paths.json)."""
    config_path = Path(get_project_root()) / "config" / "protected-paths.json"
    if not config_path.exists():
        return False
    try:
        import fnmatch
        config = json.loads(config_path.read_text())
        protected_globs = config.get("protected_globs", [])
        for glob_pattern in protected_globs:
            if fnmatch.fnmatch(rel_path, glob_pattern):
                return True
    except Exception:
        pass
    return False


def record_read(file_path):
    """Append a canonicalized path to the session tracker (PostToolUse Read)."""
    canon = canonicalize(file_path)
    tracker = get_tracker_path()
    try:
        with open(tracker, "a") as f:
            f.write(canon + "\n")
    except Exception:
        pass


def was_read(file_path):
    """Check if a file was Read this session."""
    canon = canonicalize(file_path)
    tracker = get_tracker_path()
    if not tracker.exists():
        return False
    try:
        return canon in tracker.read_text().splitlines()
    except Exception:
        return False


def handle_post_read():
    """PostToolUse Read: record the file path."""
    tool_input = os.environ.get("TOOL_INPUT", "")
    if not tool_input:
        return
    try:
        data = json.loads(tool_input)
    except (json.JSONDecodeError, TypeError):
        return
    file_path = data.get("file_path", "")
    if file_path:
        record_read(file_path)


def handle_pre_edit():
    """PreToolUse Write|Edit: warn if file not Read and is protected."""
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

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        print("{}")
        return

    # Canonicalize for consistent matching across hook phases
    canon_path = canonicalize(file_path)

    # New files are exempt — can't Read what doesn't exist
    if not Path(canon_path).exists():
        print("{}")
        return

    # Get relative path for scope checks (use canonicalized path)
    root = get_project_root()
    rel_path = canon_path
    if root:
        root_resolved = str(Path(root).resolve())
        if canon_path.startswith(root_resolved + "/"):
            rel_path = canon_path[len(root_resolved) + 1:]

    # Exempt paths pass through
    if is_exempt(rel_path):
        print("{}")
        return

    # Only warn on protected paths
    if not is_protected(rel_path):
        print("{}")
        return

    # Check if file was Read this session (canon_path already resolved)
    if was_read(canon_path):
        print("{}")
        return

    # File is protected, exists, and was NOT Read — warn
    result = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                f"READ-BEFORE-EDIT: {rel_path} is a protected file that has not "
                f"been Read this session. Reading before editing prevents "
                f"confident-but-wrong changes. Consider using Read first."
            ),
        }
    }
    print(json.dumps(result))


def main():
    # Detect which phase we're in from the hook context
    # PostToolUse hooks get TOOL_INPUT env var; PreToolUse hooks get stdin
    hook_event = os.environ.get("HOOK_EVENT", "")

    if hook_event == "PostToolUse":
        handle_post_read()
    elif hook_event == "PreToolUse":
        handle_pre_edit()
    else:
        # Fallback: check if TOOL_INPUT is set (PostToolUse) or try stdin (PreToolUse)
        tool_input = os.environ.get("TOOL_INPUT", "")
        if tool_input:
            handle_post_read()
        else:
            handle_pre_edit()


if __name__ == "__main__":
    main()
