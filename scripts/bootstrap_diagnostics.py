#!/usr/bin/env python3.11
"""bootstrap_diagnostics.py — Owns session-start diagnostic output.

Runs each registered diagnostic script in parallel, collects any non-silent
results, and emits one consolidated JSON object on stdout. Individual scripts
are silent-on-success; this wrapper is the only user-visible surface.

Healthy state: no stdout, exit 0.
Issue state: one JSON object like:
    {
      "uncommitted": { ...detect-uncommitted.py output... },
      "current_state": { ...check-current-state-freshness.py output... }
    }

To add a new session-start diagnostic:
  1. Write a script that exits silent when healthy and emits one JSON object
     to stdout when there is something to report.
  2. Append (key, filename) to CHECKS below.

The convention is enforced here: new diagnostics flow through this wrapper,
they do not add new Bash calls to the /start skill.
"""

import concurrent.futures
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PYTHON = "python3.11"
TIMEOUT_SECONDS = 30

CHECKS = [
    ("uncommitted", "detect-uncommitted.py"),
    ("plan_progress", "verify-plan-progress.py"),
    ("current_state", "check-current-state-freshness.py"),
    ("infra_versions", "check-infra-versions.py"),
]


def run_check(name, script):
    path = REPO / "scripts" / script
    if not path.exists():
        return name, {"error": f"script missing: {script}"}
    try:
        result = subprocess.run(
            [PYTHON, str(path)],
            capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
            cwd=REPO,
        )
    except subprocess.TimeoutExpired:
        return name, {"error": f"timeout after {TIMEOUT_SECONDS}s"}
    except Exception as e:
        return name, {"error": str(e)}

    out = result.stdout.strip()
    if not out:
        return name, None
    try:
        return name, json.loads(out)
    except json.JSONDecodeError:
        return name, {"error": "non-json output", "raw": out[:500]}


def main():
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(CHECKS)) as ex:
        futures = {ex.submit(run_check, name, script): name for name, script in CHECKS}
        for f in concurrent.futures.as_completed(futures):
            name, data = f.result()
            if data is not None:
                results[name] = data

    if not results:
        return

    json.dump(results, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
