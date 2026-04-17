#!/usr/bin/env python3.11
"""
detect-uncommitted.py — Detect uncommitted session work from a prior session.

Called by /recall at session start. Checks for:
1. Untracked/modified files in session-relevant paths
2. Auto-commit entries in session-log.md that need enrichment

Output: JSON to stdout for recall to consume.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")

RELEVANT_PREFIXES = [
    "tasks/", "scripts/", "tests/", "config/", "docs/",
    ".claude/rules/", ".claude/skills/",
]

EXCLUDE_PATTERNS = [
    ".env", "__pycache__", ".claude/worktrees/",
    "node_modules/", ".DS_Store", "*.pyc", "*.log",
]


def get_repo_root():
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return Path.cwd()
    return Path(result.stdout.strip())


def git(*args):
    repo = get_repo_root()
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True, text=True, timeout=10,
    )
    return result.stdout.strip(), result.returncode


def is_relevant(path):
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path:
            return False
    for prefix in RELEVANT_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def get_uncommitted_files():
    out, _ = git("diff", "--name-only", "HEAD")
    modified = [f for f in (out or "").splitlines() if f.strip()]

    out, _ = git("diff", "--cached", "--name-only")
    staged = [f for f in (out or "").splitlines() if f.strip()]

    out, _ = git("status", "--porcelain")
    untracked = []
    for line in (out or "").splitlines():
        if line.startswith("??"):
            untracked.append(line[3:].strip())

    all_files = list(set(modified + staged + untracked))
    return sorted([f for f in all_files if is_relevant(f)])


def check_auto_commit_pending():
    repo = get_repo_root()
    session_log = repo / "tasks" / "session-log.md"
    if not session_log.exists():
        return False
    content = session_log.read_text()
    entries = content.split("---")
    if not entries:
        return False
    last = entries[-1].strip()
    return "[auto-captured:" in last


def file_age_summary(files):
    repo = get_repo_root()
    times = []
    for f in files:
        full = repo / f
        if full.exists():
            times.append(full.stat().st_mtime)
    if not times:
        return None, None
    oldest = datetime.fromtimestamp(min(times), PACIFIC)
    newest = datetime.fromtimestamp(max(times), PACIFIC)
    return oldest, newest


def main():
    files = get_uncommitted_files()
    auto_pending = check_auto_commit_pending()

    if not files and not auto_pending:
        # Silent-on-success: healthy state emits no stdout.
        return

    categories = {}
    for f in files:
        cat = f.split("/")[0] if "/" in f else "root"
        categories.setdefault(cat, []).append(f)

    oldest, newest = file_age_summary(files)
    time_range = ""
    if oldest and newest:
        if oldest.date() == newest.date():
            time_range = f" (from {oldest.strftime('%Y-%m-%d %H:%M')}-{newest.strftime('%H:%M')} PT)"
        else:
            time_range = f" (from {oldest.strftime('%Y-%m-%d %H:%M')} to {newest.strftime('%Y-%m-%d %H:%M')} PT)"

    parts = []
    if files:
        parts.append(f"{len(files)} uncommitted files from prior session{time_range}")
        for cat, cat_files in sorted(categories.items()):
            names = ", ".join(Path(f).name for f in cat_files)
            parts.append(f"  {cat}/: {names}")
    if auto_pending:
        parts.append("Last session-log entry is auto-captured and needs enrichment")

    json.dump({
        "has_uncommitted": bool(files),
        "file_count": len(files),
        "files": files,
        "categories": categories,
        "auto_commit_pending": auto_pending,
        "message": "\n".join(parts),
    }, sys.stdout, indent=2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        json.dump({
            "has_uncommitted": False,
            "error": str(e),
            "message": f"detect-uncommitted error: {e}",
        }, sys.stdout)
