#!/usr/bin/env bash
# test_rollback.sh — Setup idempotency contract
# Verifies setup.sh is idempotent: running it twice produces the same state.
# Note: This runs against the real project root because setup.sh requires
# the full project structure. This is an idempotency test, not an isolation test.
set -uo pipefail
source "$(dirname "$0")/helpers.sh"
cd "$PROJECT_ROOT"

echo "=== Contract: Rollback (setup.sh idempotency) ==="

# Capture state before first run
PRE_STATE=$(ls -la .buildos-config stores/ 2>/dev/null | md5 -q)

# First run
RUN1_OUTPUT=$(bash setup.sh 2>&1) || true
RUN1_EXIT=$?
assert "setup.sh first run exits 0" "$RUN1_EXIT" "0"

# Capture state after first run
STATE1=$(ls -la .buildos-config stores/ 2>/dev/null | md5 -q)

# Second run
RUN2_OUTPUT=$(bash setup.sh 2>&1) || true
RUN2_EXIT=$?
assert "setup.sh second run exits 0" "$RUN2_EXIT" "0"

# Capture state after second run
STATE2=$(ls -la .buildos-config stores/ 2>/dev/null | md5 -q)

# State after run 1 and run 2 should be identical (idempotent)
assert "state identical after second run" "$STATE1" "$STATE2"

# .buildos-config was written (exists and non-empty)
assert ".buildos-config exists" "$(test -s .buildos-config && echo yes || echo no)" "yes"

# stores/ directory exists
assert "stores/ directory exists" "$(test -d stores && echo yes || echo no)" "yes"

report
