#!/usr/bin/env python3
"""
tier_classify.py — Deterministic review tier classifier.

Consolidates tier logic for commit-time review gates.

Usage:
    python3 scripts/tier_classify.py [file1 file2 ...]
    python3 scripts/tier_classify.py --stdin
    python3 scripts/tier_classify.py --diff-base main
"""
import argparse
import json
import os
import re
import subprocess
import sys


def _detect_project_root():
    """Detect project root via git."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


PROJECT_ROOT = _detect_project_root()

# ── Tier 1: Architecture docs, database schema, security rules ──────────
# Customize: add your project's trust-boundary files here.
TIER1_PATTERNS = [
    r"^docs/.*PRD",           # product requirements docs
    r"^docs/project-prd\.md$",
    r"schema.*\.sql$",        # database schema
    r"migration.*\.sql$",     # database migrations
    r"^\.claude/rules/security\.md$",
    r"^stores/.*\.db$",       # direct DB file edits
]

# ── Tier 1.5: core skills, toolbelt scripts, hooks ──────────────────────
# Customize: list your project's core skill names.
CORE_SKILLS = ""  # e.g., "morning-briefing|email-triage|approval-queue"

TIER15_PATTERNS = [
    *(
        [rf"^skills/({CORE_SKILLS})/SKILL\.md$"]
        if CORE_SKILLS else []
    ),
    r"^scripts/[a-z]+_tool\.py$",  # toolbelt scripts
    r"^scripts/debate\.py$",       # debate engine
    r"^scripts/hook-.*\.sh$",      # hook scripts
]

# ── Exempt paths ─────────────────────────────────────────────────────────
EXEMPT_PATTERNS = [
    r"^tasks/",
    r"^docs/(?!.*PRD|project-prd\.md)",
    r"^tests/",
    r"^config/",
    r"^stores/(?!.*\.db$)",
]


def classify_file(rel_path):
    """Classify a single file. Returns (tier, reason)."""
    for pat in EXEMPT_PATTERNS:
        if re.search(pat, rel_path):
            return "exempt", "exempt path"

    for pat in TIER1_PATTERNS:
        if re.search(pat, rel_path):
            if "PRD" in rel_path or "project-prd" in rel_path:
                return 1, "PRD change"
            if re.search(r"schema|migration", rel_path):
                return 1, "database schema"
            if "security.md" in rel_path:
                return 1, "security rules"
            if rel_path.endswith(".db"):
                return 1, "direct DB file edit"
            return 1, "trust boundary"

    for pat in TIER15_PATTERNS:
        if re.search(pat, rel_path):
            if "SKILL.md" in rel_path:
                return 1.5, "core skill"
            if "_tool.py" in rel_path:
                return 1.5, "toolbelt script"
            if "debate.py" in rel_path:
                return 1.5, "debate tooling"
            if "hook-" in rel_path:
                return 1.5, "hook script"
            return 1.5, "core infrastructure"

    return 2, "standard change"


def normalize_path(path):
    """Normalize to relative path from project root."""
    path = path.strip()
    if path.startswith(PROJECT_ROOT + "/"):
        path = path[len(PROJECT_ROOT) + 1:]
    if path.startswith("./"):
        path = path[2:]
    return path


def main():
    parser = argparse.ArgumentParser(description="Classify review tier for files")
    parser.add_argument("files", nargs="*", help="File paths to classify")
    parser.add_argument("--stdin", action="store_true",
                        help="Read newline-separated paths from stdin")
    parser.add_argument("--diff-base", metavar="REF",
                        help="Use git diff REF..HEAD for file list")
    args = parser.parse_args()

    paths = []

    if args.diff_base:
        result = subprocess.run(
            ["git", "-C", PROJECT_ROOT, "diff", "--name-only",
             f"{args.diff_base}..HEAD"],
            capture_output=True, text=True,
        )
        paths = [p.strip() for p in result.stdout.splitlines() if p.strip()]

    if args.stdin:
        paths.extend(p.strip() for p in sys.stdin if p.strip())

    if args.files:
        paths.extend(args.files)

    if not paths:
        print("ERROR: no files provided", file=sys.stderr)
        sys.exit(1)

    # Severity ordering: lower number = stricter review. 1 > 1.5 > 2.
    def severity(tier):
        """Map tier to severity rank (lower = stricter)."""
        if tier == "exempt":
            return 999
        return tier  # 1, 1.5, 2 — natural ordering works

    files = {}
    strictest_tier = None
    strictest_reason = ""

    for raw_path in paths:
        rel = normalize_path(raw_path)
        tier, reason = classify_file(rel)
        files[rel] = {"tier": tier, "reason": reason}

        if tier == "exempt":
            continue

        if strictest_tier is None or severity(tier) < severity(strictest_tier):
            strictest_tier = tier
            strictest_reason = f"{rel} -> {reason}"

    # If all exempt, overall tier is exempt
    if strictest_tier is None:
        overall_tier = "exempt"
        tier_label = "Exempt — no review needed"
    else:
        overall_tier = strictest_tier

        labels = {
            1: "Tier 1 — Cross-model debate",
            1.5: "Tier 1.5 — Quality review",
            2: "Tier 2 — Log only",
        }
        tier_label = labels.get(overall_tier, f"Tier {overall_tier}")

    # Ambiguous: multiple different non-exempt tiers present
    tiers_present = {f["tier"] for f in files.values() if f["tier"] != "exempt"}
    ambiguous = len(tiers_present) > 1

    output = {
        "tier": overall_tier,
        "tier_label": tier_label,
        "reason": strictest_reason,
        "files": files,
        "ambiguous": ambiguous,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
