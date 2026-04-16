#!/usr/bin/env python3
"""PostToolUse hook: lint SKILL.md files after Write/Edit.

Runs scripts/lint_skills.py on the target file if it matches .claude/skills/*/SKILL.md.
Prints violations as warnings so Claude sees and fixes them.
"""

import json
import os
import re
import subprocess
import sys

# Tier gate: requires tier >= 2
_project = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True
).stdout.strip()
_tier_result = subprocess.run(
    ["/opt/homebrew/bin/python3.11", os.path.join(_project, "scripts/read_tier.py"), "--check", "2"],
    capture_output=True
)
if _tier_result.returncode != 0:
    sys.exit(0)


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

    # Only check SKILL.md files
    if not re.search(r'\.claude/skills/[^/]+/SKILL\.md$', file_path):
        return

    if not os.path.exists(file_path):
        return

    # Run the linter
    result = subprocess.run(
        [sys.executable, "scripts/lint_skills.py", file_path],
        capture_output=True,
        text=True,
        timeout=10,
    )

    if result.returncode != 0:
        skill_name = os.path.basename(os.path.dirname(file_path))
        print(f"SKILL LINT WARNING: {skill_name} has violations after edit:")
        print(result.stdout.strip())
        print("Fix these violations before committing.")


if __name__ == "__main__":
    main()
