#!/usr/bin/env python3.11
"""Check live infrastructure versions against MEMORY.md claims.

Detects drift between what memory says is running and what's actually installed.
Used by /recall step 0d to prevent stale version numbers in session briefs.

This is a template — downstream projects should add their own version checks
to the CHECKS list (e.g., app version, database version, API version).
"""

import json
import os
import re
import subprocess
from pathlib import Path


def find_memory_file():
    """Find the MEMORY.md for the current project."""
    # Check env var first
    env_dir = os.environ.get("CLAUDE_MEMORY_DIR")
    if env_dir:
        f = Path(env_dir) / "MEMORY.md"
        if f.exists():
            return f

    # Scan ~/.claude/projects/ for a match based on repo name
    repo_root = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, timeout=10,
    )
    if repo_root.returncode != 0:
        return None

    repo_name = Path(repo_root.stdout.strip()).name
    projects_dir = Path.home() / ".claude" / "projects"
    if projects_dir.exists():
        for d in projects_dir.iterdir():
            if d.is_dir() and repo_name in d.name:
                memory = d / "memory" / "MEMORY.md"
                if memory.exists():
                    return memory
                # Also check direct MEMORY.md in project dir
                memory = d / "MEMORY.md"
                if memory.exists():
                    return memory

    return None


# Version checks — downstream projects should add entries here.
# Each entry needs: label, command, memory_pattern, parse_live.
# Example for a project with a custom CLI:
#   {
#       "label": "MyApp",
#       "command": ["myapp", "--version"],
#       "memory_pattern": r"MyApp v([\d.]+)",
#       "parse_live": lambda out: re.search(r"(\d+\.\d+\.\d+)", out),
#   },
CHECKS = []


def get_memory_versions(text):
    """Extract version claims from MEMORY.md."""
    versions = {}
    for check in CHECKS:
        m = re.search(check["memory_pattern"], text)
        if m:
            versions[check["label"]] = m.group(1)
    return versions


def get_live_version(check):
    """Run a command and extract the version."""
    try:
        result = subprocess.run(
            check["command"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return None, result.stderr.strip()
        output = result.stdout.strip()
        m = check["parse_live"](output)
        return m.group(1) if m else None, output
    except Exception as e:
        return None, str(e)


def main():
    memory_file = find_memory_file()
    if not memory_file:
        print(json.dumps({"has_drift": False, "message": "No MEMORY.md found — skipping version check."}))
        return

    if not CHECKS:
        print(json.dumps({"has_drift": False, "message": "No version checks configured — add entries to CHECKS list."}))
        return

    try:
        text = memory_file.read_text(encoding="utf-8")
    except Exception as e:
        print(json.dumps({"has_drift": False, "check_failed": True,
                          "error": f"Failed to read MEMORY.md: {e}"}))
        return

    memory_versions = get_memory_versions(text)

    drifts = []
    errors = []
    live_versions = {}

    for check in CHECKS:
        label = check["label"]
        live_ver, raw = get_live_version(check)
        memory_ver = memory_versions.get(label)

        if live_ver:
            live_versions[label] = live_ver
        else:
            errors.append(f"{label}: could not determine live version ({raw})")

        if live_ver and memory_ver and live_ver != memory_ver:
            drifts.append({
                "component": label,
                "memory": memory_ver,
                "live": live_ver,
            })

    result = {"has_drift": len(drifts) > 0, "live_versions": live_versions}

    if errors:
        result["check_failed"] = True
        result["errors"] = errors

    if drifts:
        drift_lines = [
            f"{d['component']}: memory says v{d['memory']}, live is v{d['live']}"
            for d in drifts
        ]
        result["drifts"] = drifts
        result["message"] = (
            "Infrastructure version drift detected. "
            "Update MEMORY.md before using these versions in the brief.\n"
            + "\n".join(drift_lines)
        )

    print(json.dumps(result))


if __name__ == "__main__":
    main()
