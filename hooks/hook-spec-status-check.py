#!/usr/bin/env python3
"""PostToolUse hook: warn when reading spec docs with untagged recommendations.

Fires on Read of tasks/*-refined.md and tasks/*-proposal.md.
If the file has a Recommendations/Recommendation section but no
implementation_status in frontmatter, prints an advisory warning.
"""

import json
import os
import re
import subprocess
import sys

# Tier gate: requires tier >= 1
_project = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True
).stdout.strip()
_tier_result = subprocess.run(
    ["/opt/homebrew/bin/python3.11", os.path.join(_project, "scripts/read_tier.py"), "--check", "1"],
    capture_output=True
)
if _tier_result.returncode != 0:
    sys.exit(0)


SPEC_PATTERN = re.compile(r'tasks/[^/]+-(refined|proposal)\.md$')
RECOMMENDATION_PATTERN = re.compile(
    r'^#{1,3}\s.*(Recommendation|Implementation Priority|Implementation Tracks)',
    re.IGNORECASE | re.MULTILINE,
)
STATUS_PATTERN = re.compile(r'^implementation_status:', re.MULTILINE)
FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)


def main():
    tool_input = os.environ.get("TOOL_INPUT", "")
    if not tool_input:
        return

    try:
        data = json.loads(tool_input)
    except (json.JSONDecodeError, TypeError):
        return

    file_path = data.get("file_path", "")
    if not file_path:
        return

    if not SPEC_PATTERN.search(file_path):
        return

    if not os.path.exists(file_path):
        return

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except OSError:
        return

    # Does it have recommendation sections?
    if not RECOMMENDATION_PATTERN.search(content):
        return

    # Does it have implementation_status in frontmatter?
    fm_match = FRONTMATTER_PATTERN.match(content)
    if fm_match:
        frontmatter = fm_match.group(1)
        if STATUS_PATTERN.search(frontmatter):
            return  # Status field exists — no warning needed

    basename = os.path.basename(file_path)
    print(f"SPEC STATUS WARNING: {basename} has recommendations but no implementation_status in frontmatter.")
    print("Verify implementation state before reporting what's shipped vs. pending.")
    print("Check: git log --oneline -- <target files> or read the actual skill/script files.")


if __name__ == "__main__":
    main()
