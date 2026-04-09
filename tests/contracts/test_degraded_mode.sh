#!/usr/bin/env bash
# Contract 4: Degraded mode surfaced — failures always return structured errors
# Note: pre-DB parse errors surface via JSON stdout, not audit log.
set -uo pipefail
source "$(dirname "$0")/helpers.sh"
echo "=== Contract 4: Degraded Mode ==="
setup_test_dbs
trap teardown_test_dbs EXIT

# Invalid JSON → structured error, non-zero exit
EXIT1=0
OUT1=$(echo 'not valid json {{{' | $TOOL outbox_create 2>&1) || EXIT1=$?
assert_exit "invalid JSON exits non-zero"         "$EXIT1" "1"
assert_contains "error response has status field" "$OUT1" '"status"'
assert_contains "error response has error status" "$OUT1" '"error"'
assert_contains "error message is meaningful"     "$OUT1" "Invalid JSON"

# Missing required field → structured error
EXIT2=0
OUT2=$(echo '{"idempotency_key":"test-deg-002","action_type":"email_reply"}' | $TOOL outbox_create 2>&1) || EXIT2=$?
assert_exit "missing field exits non-zero"        "$EXIT2" "1"
assert_contains "missing field error"             "$OUT2" '"error"'
assert_contains "error names the missing field"   "$OUT2" "target"

# Invalid tier (out of range) → structured error
EXIT3=0
OUT3=$(echo '{"idempotency_key":"test-deg-003","action_type":"email_reply","target":"t@t.com","content":"x","tier":9,"account":"sender@example.com"}' | $TOOL outbox_create 2>&1) || EXIT3=$?
assert_exit "invalid tier exits non-zero"         "$EXIT3" "1"
assert_contains "tier error is structured"        "$OUT3" '"error"'

# Approve non-existent item → structured error
EXIT4=0
OUT4=$($TOOL outbox_approve --id 99999 2>&1) || EXIT4=$?
assert_exit "approve missing item exits non-zero" "$EXIT4" "1"
assert_contains "not-found error is structured"   "$OUT4" '"error"'
assert_contains "error references the item id"    "$OUT4" "99999"

# Verify no phantom audit entries were written for these pre-DB failures
AUDIT_COUNT=$(db_count "$AUDIT_DB" audit_log)
assert "no spurious audit entries from errors"    "$AUDIT_COUNT" "0"

report
