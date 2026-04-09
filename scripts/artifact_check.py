#!/usr/bin/env python3
"""
artifact_check.py — Artifact integrity and staleness checker.

Checks for plan, challenge, judgment, and review artifacts for a given topic.
Validates frontmatter, staleness relative to source files, and open findings.

Usage:
    python3 scripts/artifact_check.py --scope <topic> [--base <ref>]
"""
import argparse
import json
import os
import re
import subprocess
import sys

try:
    PROJECT_ROOT = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
    ).strip()
except (subprocess.CalledProcessError, FileNotFoundError):
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_DIR = os.path.join(PROJECT_ROOT, "tasks")


def _file_mtime(path):
    """Get file mtime or None if missing."""
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def _read_file(path):
    """Read file contents or return None."""
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return None


def _parse_frontmatter(text):
    """Parse YAML frontmatter from markdown. Returns dict."""
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    meta = {}
    for line in match.group(1).splitlines():
        if ": " in line and not line.startswith("  "):
            key, _, val = line.partition(": ")
            meta[key.strip()] = val.strip()
    return meta


def _newest_scope_mtime(base_ref):
    """Get mtime of newest file changed since base_ref, or current time."""
    if not base_ref:
        return None
    result = subprocess.run(
        ["git", "-C", PROJECT_ROOT, "diff", "--name-only", f"{base_ref}..HEAD"],
        capture_output=True, text=True,
    )
    newest = 0
    for rel in result.stdout.splitlines():
        rel = rel.strip()
        if not rel:
            continue
        full = os.path.join(PROJECT_ROOT, rel)
        mt = _file_mtime(full)
        if mt and mt > newest:
            newest = mt
    return newest if newest > 0 else None


def _check_artifact(name, path, scope_mtime):
    """Check a single artifact file. Returns dict with status info."""
    info = {"path": path, "exists": False}
    content = _read_file(path)
    if content is None:
        return info

    info["exists"] = True
    mtime = _file_mtime(path)

    # Staleness: artifact older than newest scope file
    if scope_mtime and mtime and mtime < scope_mtime:
        info["stale"] = True
    else:
        info["stale"] = False

    fm = _parse_frontmatter(content)

    if name == "plan":
        # Valid if has required frontmatter fields
        required = {"scope", "review_tier"}
        info["valid"] = bool(required.intersection(set(fm.keys())))

    elif name == "challenge":
        info["has_material"] = bool(re.search(r"MATERIAL", content))
        has_fm = bool(re.match(r"^---\n.*?debate_id:", content, re.DOTALL))
        info["valid"] = has_fm

    elif name == "debate":
        info["has_material"] = bool(re.search(r"MATERIAL", content))
        has_fm = bool(re.match(r"^---\n.*?debate_id:", content, re.DOTALL))
        info["valid"] = has_fm

    elif name == "judgment":
        accepted = len(re.findall(r"Decision:\s*ACCEPT", content, re.IGNORECASE))
        dismissed = len(re.findall(r"Decision:\s*DISMISS", content, re.IGNORECASE))
        escalated = len(re.findall(r"Decision:\s*ESCALATE", content, re.IGNORECASE))
        info["accepted"] = accepted
        info["dismissed"] = dismissed
        info["escalated"] = escalated

    elif name == "review":
        info["status"] = fm.get("status", "unknown")
        info["review_tier"] = fm.get("review_tier", "unknown")

    return info


def _count_open_material(artifacts, scope=None):
    """Count open material findings. Review status > finding_tracker > judgment fallback."""
    # If review exists and passed, findings are resolved
    review = artifacts.get("review", {})
    if review.get("exists") and review.get("status") == "passed":
        return 0

    judgment = artifacts.get("judgment", {})
    if not judgment.get("exists"):
        return None  # No judgment yet

    # Try finding_tracker.py for per-finding state
    if scope:
        tracker_path = os.path.join(PROJECT_ROOT, "stores/findings.jsonl")
        if os.path.exists(tracker_path):
            try:
                result = subprocess.run(
                    [sys.executable, os.path.join(PROJECT_ROOT, "scripts/finding_tracker.py"),
                     "summary", "--debate-id", scope],
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    summary = json.loads(result.stdout)
                    return summary.get("open", 0)
            except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
                pass  # Fall through to simple count

    # Fallback: count ACCEPT lines in judgment
    return judgment.get("accepted", 0)


def main():
    parser = argparse.ArgumentParser(description="Check artifact integrity")
    parser.add_argument("--scope", required=True, help="Topic name (artifact prefix)")
    parser.add_argument("--base", default=None, help="Git ref for staleness check")
    args = parser.parse_args()

    scope = args.scope
    scope_mtime = _newest_scope_mtime(args.base)

    # Get current git HEAD
    head_result = subprocess.run(
        ["git", "-C", PROJECT_ROOT, "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    )
    git_head = head_result.stdout.strip() or "unknown"

    # Check each artifact type
    artifact_names = {
        "plan": f"tasks/{scope}-plan.md",
        "challenge": f"tasks/{scope}-challenge.md",
        "debate": f"tasks/{scope}-debate.md",
        "judgment": f"tasks/{scope}-judgment.md",
        "review": f"tasks/{scope}-review.md",
    }

    artifacts = {}
    for name, rel_path in artifact_names.items():
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        artifacts[name] = _check_artifact(name, full_path, scope_mtime)

    open_material = _count_open_material(artifacts, scope=scope)

    output = {
        "scope": scope,
        "git_head": git_head,
        "artifacts": artifacts,
        "open_material_findings": open_material,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
