#!/usr/bin/env python3
"""
enrich_context.py — Pull relevant lessons/decisions into debate proposals.

Extracts keywords from a proposal, searches governance files via recall_search.py,
and returns structured JSON for challengers to consume.

Usage:
    python3 scripts/enrich_context.py --proposal tasks/<topic>-proposal.md [--top-k 5]
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
PYTHON = sys.executable
RECALL = os.path.join(PROJECT_ROOT, "scripts/recall_search.py")


def extract_keywords(text, max_keywords=8):
    """Extract keywords from proposal title, scope, and first paragraph."""
    lines = text.splitlines()
    important_text = []

    # Frontmatter scope field
    in_frontmatter = False
    for line in lines:
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter and line.startswith("scope:"):
            important_text.append(line.partition(":")[2].strip().strip('"'))

    # First heading
    for line in lines:
        if line.startswith("# "):
            important_text.append(line.lstrip("# ").strip())
            break

    # First non-empty, non-frontmatter paragraph
    past_frontmatter = False
    fm_count = 0
    for line in lines:
        if line.strip() == "---":
            fm_count += 1
            if fm_count >= 2:
                past_frontmatter = True
            continue
        if not past_frontmatter:
            continue
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            important_text.append(stripped)
            break

    combined = " ".join(important_text).lower()
    # Remove common words
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                 "have", "has", "had", "do", "does", "did", "will", "would",
                 "could", "should", "may", "might", "can", "shall", "to",
                 "of", "in", "for", "on", "with", "at", "by", "from", "as",
                 "into", "through", "during", "before", "after", "and", "or",
                 "but", "not", "no", "if", "then", "than", "that", "this",
                 "it", "its", "all", "each", "every", "both", "few", "more"}
    tokens = re.findall(r"[a-z][a-z0-9_-]+", combined)
    keywords = [t for t in tokens if t not in stopwords and len(t) > 2]
    # Deduplicate preserving order
    seen = set()
    unique = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    return unique[:max_keywords]


def search_governance(keywords, sources, top_k=5):
    """Run recall_search.py with --json and return parsed results."""
    if not keywords:
        return []
    cmd = [PYTHON, RECALL] + keywords + ["--files", sources, "--json", "--top-k", str(top_k)]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            cwd=PROJECT_ROOT, timeout=10)
    if result.returncode != 0:
        return []
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return []


def main():
    parser = argparse.ArgumentParser(description="Enrich proposal with prior context")
    parser.add_argument("--proposal", required=True, help="Path to proposal file")
    parser.add_argument("--top-k", type=int, default=5, help="Max results per source")
    args = parser.parse_args()

    proposal_path = args.proposal
    if not os.path.isabs(proposal_path):
        proposal_path = os.path.join(PROJECT_ROOT, proposal_path)

    try:
        text = open(proposal_path).read()
    except OSError as e:
        print(json.dumps({"error": str(e), "lessons": [], "decisions": []}))
        sys.exit(1)

    keywords = extract_keywords(text)
    if not keywords:
        print(json.dumps({"keywords": [], "lessons": [], "decisions": []}))
        sys.exit(0)

    lessons = search_governance(keywords, "lessons", args.top_k)
    decisions = search_governance(keywords, "decisions", args.top_k)

    output = {
        "keywords": keywords,
        "lessons": lessons,
        "decisions": decisions,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
