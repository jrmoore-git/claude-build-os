#!/usr/bin/env python3
"""
verify_state.py — parallel health checks with per-check timeouts.

Reads config/health-checks.json, runs all checks concurrently,
writes /tmp/verify-state-output.json, prints summary.

Design:
- All checks run in parallel (ThreadPoolExecutor)
- Per-check timeout of 10s (configurable via check.timeout_s)
- JSON parsing done in Python, not shell subprocesses

health-checks.json format:
{
  "checks": [
    {
      "id": "db_accessible",
      "name": "Database accessible",
      "cmd": "sqlite3 stores/your_database.db 'SELECT 1;'",
      "ok_text": "Database responds",
      "fail_text": "Database not accessible",
      "timeout_s": 5
    }
  ]
}
"""

import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHECKS_FILE = PROJECT_ROOT / "config" / "health-checks.json"
OUTPUT_FILE = Path("/tmp/verify-state-output.json")
DEFAULT_TIMEOUT = 10  # seconds per check


def run_check(check):
    """Run a single health check. Returns (check_dict, status, detail)."""
    check_id = check["id"]
    timeout_s = check.get("timeout_s", DEFAULT_TIMEOUT)

    cmd = check["cmd"]
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, timeout=timeout_s,
        )
        if result.returncode == 0:
            return (check, "ok", check["ok_text"])
        return (check, "fail", check["fail_text"])
    except subprocess.TimeoutExpired:
        return (check, "fail", f"TIMEOUT ({timeout_s}s) — {check['fail_text']}")
    except Exception as e:
        return (check, "fail", f"ERROR: {e}")


def main():
    include_tests = "--include-tests" in sys.argv

    if not CHECKS_FILE.exists():
        print(f"ERROR: {CHECKS_FILE} not found", file=sys.stderr)
        sys.exit(1)

    config = json.loads(CHECKS_FILE.read_text())
    checks = config["checks"]

    # Filter out test suite unless explicitly requested
    if not include_tests:
        checks = [c for c in checks if c["id"] != "tests"]

    total = len(checks)

    # Run all checks in parallel
    results = []
    with ThreadPoolExecutor(max_workers=total) as pool:
        futures = {
            pool.submit(run_check, c): c["id"]
            for c in checks
        }
        for future in as_completed(futures):
            check, status, detail = future.result()
            results.append({
                "id": check["id"],
                "name": check["name"],
                "status": status,
                "detail": detail,
            })

    # Sort results to match config order
    id_order = {c["id"]: i for i, c in enumerate(checks)}
    results.sort(key=lambda r: id_order.get(r["id"], 999))

    pass_count = sum(1 for r in results if r["status"] == "ok")
    fail_count = total - pass_count

    # Write output atomically
    output = {
        "timestamp": datetime.now().isoformat(),
        "pass": pass_count,
        "fail": fail_count,
        "total": total,
        "checks": results,
    }
    fd, tmp = tempfile.mkstemp(dir="/tmp", suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(output, f, indent=2)
    os.replace(tmp, str(OUTPUT_FILE))

    # Print summary
    if fail_count == 0:
        print(f"verify-state: {pass_count}/{total} OK")
    else:
        print(f"verify-state: {pass_count}/{total} OK, {fail_count} FAILING")
        for r in results:
            if r["status"] != "ok":
                print(f"  x {r['name']}: {r['detail']}")

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
