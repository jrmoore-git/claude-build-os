#!/usr/bin/env python3
"""
tier_classify.py — Deterministic review tier classifier.

Consolidates tier logic from hook-tier-gate.sh and hook-review-gate.sh.

Loads project-specific patterns from config/tier-patterns.json if present.
Falls back to sensible defaults (PRD, schema, security, toolbelt scripts).

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

try:
    PROJECT_ROOT = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
    ).strip()
except (subprocess.CalledProcessError, FileNotFoundError):
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Load config ──────────────────────────────────────────────────────────────

_DEFAULT_TIER1 = [
    r"^docs/.*PRD",
    r"^docs/project-prd\.md$",
    r"schema.*\.sql$",
    r"migration.*\.sql$",
    r"^\.claude/rules/security\.md$",
    r"^stores/.*\.db$",
]

_DEFAULT_TIER15 = [
    r"^scripts/[a-z]+_tool\.py$",
    r"^scripts/debate\.py$",
    r"^scripts/hook-.*\.sh$",
]

_DEFAULT_EXEMPT = [
    r"^tasks/",
    r"^docs/(?!.*PRD|project-prd\.md)",
    r"^tests/",
    r"^config/",
    r"^stores/(?!.*\.db$)",
]

_DEFAULT_REASONS = {
    "PRD": "PRD change",
    "schema|migration": "database schema",
    "security.md": "security rules",
    ".db$": "direct DB file edit",
    "SKILL.md": "core skill",
    "_tool.py": "toolbelt script",
    "debate.py": "debate tooling",
    "hook-": "hook script",
}


def _load_config():
    """Load tier patterns from config/tier-patterns.json, falling back to defaults."""
    config_path = os.path.join(PROJECT_ROOT, "config", "tier-patterns.json")
    if os.path.isfile(config_path):
        with open(config_path) as f:
            cfg = json.load(f)
        tier1 = cfg.get("tier1_patterns", _DEFAULT_TIER1)
        tier15 = cfg.get("tier15_patterns", _DEFAULT_TIER15)
        exempt = cfg.get("exempt_patterns", _DEFAULT_EXEMPT)
        reasons = cfg.get("reasons", _DEFAULT_REASONS)

        # Expand core_skills into tier1.5 pattern if provided
        core_skills = cfg.get("core_skills", "")
        if core_skills:
            tier15 = [rf"^skills/({core_skills})/SKILL\.md$"] + tier15

        return tier1, tier15, exempt, reasons
    return _DEFAULT_TIER1, _DEFAULT_TIER15, _DEFAULT_EXEMPT, _DEFAULT_REASONS


TIER1_PATTERNS, TIER15_PATTERNS, EXEMPT_PATTERNS, REASONS = _load_config()


def classify_file(rel_path):
    """Classify a single file. Returns (tier, reason)."""
    for pat in EXEMPT_PATTERNS:
        if re.search(pat, rel_path):
            return "exempt", "exempt path"

    for pat in TIER1_PATTERNS:
        if re.search(pat, rel_path):
            # Check reasons map for specific match
            for pattern, reason in REASONS.items():
                if re.search(pattern, rel_path):
                    return 1, reason
            return 1, "trust boundary"

    for pat in TIER15_PATTERNS:
        if re.search(pat, rel_path):
            for pattern, reason in REASONS.items():
                if re.search(pattern, rel_path):
                    return 1.5, reason
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
