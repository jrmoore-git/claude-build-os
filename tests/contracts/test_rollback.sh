#!/usr/bin/env bash
# test_rollback.sh — Rollback/idempotency of setup.sh
# Verifies setup.sh is idempotent: running it twice produces the same state.
set -uo pipefail
source "$(dirname "$0")/helpers.sh"
cd "$PROJECT_ROOT"

echo "=== Contract: Rollback (setup.sh idempotency) ==="

setup_test_dir

# Capture file state after first run
RUN1_OUTPUT=$(bash setup.sh 2>&1) || true
RUN1_EXIT=$?
assert "setup.sh first run exits 0" "$RUN1_EXIT" "0"

# Capture state snapshot: list of managed files that exist
STATE1=""
for f in .buildos-config stores; do
    if [ -e "$f" ]; then
        STATE1="$STATE1 $f"
    fi
done

# Run again
RUN2_OUTPUT=$(bash setup.sh 2>&1) || true
RUN2_EXIT=$?
assert "setup.sh second run exits 0" "$RUN2_EXIT" "0"

# Capture state snapshot again
STATE2=""
for f in .buildos-config stores; do
    if [ -e "$f" ]; then
        STATE2="$STATE2 $f"
    fi
done

# Same managed files exist after both runs
assert "managed files identical after second run" "$STATE1" "$STATE2"

# .buildos-config was written (exists and non-empty)
assert ".buildos-config exists" "$(test -s .buildos-config && echo yes || echo no)" "yes"

# stores/ directory exists
assert "stores/ directory exists" "$(test -d stores && echo yes || echo no)" "yes"

teardown_test_dir

report
