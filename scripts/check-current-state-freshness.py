#!/usr/bin/env python3.11
"""Check whether docs/current-state.md is stale relative to recent git activity."""

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")
REPO = Path(__file__).resolve().parent.parent
CURRENT_STATE = REPO / "docs" / "current-state.md"


def main():
    try:
        # 1. Read current-state.md and extract the date from the header
        if not CURRENT_STATE.exists():
            # Silent-on-success: no current-state.md means nothing to compare against.
            return

        text = CURRENT_STATE.read_text()
        match = re.search(r"^# Current State\s*[—–-]\s*(\d{4}-\d{2}-\d{2})", text, re.MULTILINE)
        if not match:
            # Silent-on-success: unparseable header is not a staleness signal.
            return

        cs_date_str = match.group(1)
        cs_date = datetime.strptime(cs_date_str, "%Y-%m-%d").replace(tzinfo=PACIFIC)

        # 2. Get latest git commit date
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci"],
            cwd=REPO, capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return

        commit_dt_str = result.stdout.strip()
        # git %ci format: 2026-03-31 17:24:00 -0700
        commit_dt = datetime.strptime(commit_dt_str, "%Y-%m-%d %H:%M:%S %z").astimezone(PACIFIC)
        commit_date_str = commit_dt.strftime("%Y-%m-%d")

        # 3. Compare: stale if latest commit is >24h after current-state date
        cs_end_of_day = cs_date.replace(hour=23, minute=59, second=59)
        delta = commit_dt - cs_end_of_day
        days_behind = max(0, delta.days)

        is_stale = delta > timedelta(hours=24)

        if not is_stale:
            # Silent-on-success: healthy state emits no stdout.
            return

        # 4. Get 5 most recent commit subjects (only needed for the stale report)
        result = subprocess.run(
            ["git", "log", "-5", "--format=%h %s"],
            cwd=REPO, capture_output=True, text=True, timeout=10,
        )
        recent_commits = [line for line in result.stdout.strip().splitlines() if line]

        msg_parts = []
        if days_behind > 0:
            msg_parts.append(
                f"current-state.md date ({cs_date_str}) is {days_behind} day(s) behind "
                f"latest commit ({commit_date_str})."
            )
        msg_parts.append(
            "Do NOT trust 'Next Action' — check recent commits and session-log instead."
        )

        print(json.dumps({
            "is_stale": True,
            "current_state_date": cs_date_str,
            "latest_commit_date": commit_date_str,
            "days_behind": days_behind,
            "recent_commits": recent_commits,
            "message": " ".join(msg_parts),
        }))

    except Exception as e:
        print(json.dumps({"is_stale": False, "error": str(e)}))


if __name__ == "__main__":
    main()
