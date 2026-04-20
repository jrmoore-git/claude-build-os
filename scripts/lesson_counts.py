#!/usr/bin/env python3.11
"""Count active lesson rows in tasks/lessons.md — canonical source of truth.

Active rows are table rows starting with `| L<digits>` that appear BEFORE the
`## Promoted lessons` section heading. Rows in `## Promoted lessons` and
`## Archived lessons` tables are excluded.

Usage:
    lesson_counts.py --active    # prints integer count, e.g. "27"

Silent-on-error: prints "0" if tasks/lessons.md is missing or unreadable.
Callers should treat the output as a best-effort count, not an assertion.

Why this exists: skills (start, wrap, healthcheck) previously improvised
counts via inline grep/awk. Improvisations over-counted by including the
Promoted + Archived tables (typical miscount: 52 vs actual 27). This script
centralizes the boundary logic so every skill reports the same number.
"""

import re
import sys
from pathlib import Path

LESSONS_MD = Path(__file__).resolve().parent.parent / "tasks" / "lessons.md"
ROW_PATTERN = re.compile(r"^\| L\d+")


def count_active(path: Path = LESSONS_MD) -> int:
    if not path.exists():
        return 0
    count = 0
    try:
        with open(path) as f:
            for line in f:
                if line.startswith("## Promoted"):
                    break
                if ROW_PATTERN.match(line):
                    count += 1
    except OSError:
        return 0
    return count


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] != "--active":
        print("Usage: lesson_counts.py --active", file=sys.stderr)
        sys.exit(2)
    print(count_active())


if __name__ == "__main__":
    main()
