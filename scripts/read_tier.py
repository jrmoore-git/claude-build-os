#!/usr/bin/env python3.11
"""Read the declared BuildOS tier from CLAUDE.md.

Usage:
    python3.11 scripts/read_tier.py          # prints tier (0-3)
    python3.11 scripts/read_tier.py --check 2  # exit 0 if declared tier >= 2, else exit 1

Looks for <!-- buildos-tier: N --> in CLAUDE.md at the project root.
Default: 3 (fail closed to maximum governance if no declaration).
"""
import os
import re
import sys


def read_tier(project_root=None):
    if project_root is None:
        project_root = os.environ.get("PLAN_GATE_PROJECT", ".")
    claude_md = os.path.join(project_root, "CLAUDE.md")
    try:
        with open(claude_md) as f:
            # Only check first 5 lines — tier declaration should be at the top
            for _ in range(5):
                line = f.readline()
                if not line:
                    break
                m = re.search(r"<!--\s*buildos-tier:\s*(\d)\s*-->", line)
                if m:
                    return int(m.group(1))
    except OSError:
        pass
    return 3  # no declaration = fail closed


if __name__ == "__main__":
    tier = read_tier()
    if len(sys.argv) >= 3 and sys.argv[1] == "--check":
        required = int(sys.argv[2])
        sys.exit(0 if tier >= required else 1)
    print(tier)
