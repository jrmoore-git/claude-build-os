#!/usr/bin/env bash
# Contract 5: State machine — no invalid transitions accepted
set -uo pipefail
source "$(dirname "$0")/helpers.sh"
echo "=== Contract 5: State Machine ==="
setup_test_dbs
trap teardown_test_dbs EXIT

# Enable send token so state check is the gating factor
$SQLITE "$PREFS_DB" "INSERT INTO preferences (category,key,value,source) VALUES ('autonomy','send_token_enabled','1','test');"
setup_mock_send

# --- Test A: draft_created → sent (must be rejected; skips approved) ---
OUT=$(test_item "test-sm-001" | $TOOL outbox_create)
ID=$(json_field "$OUT" id)

EXIT_SEND=0
OUT_SEND=$($TOOL outbox_send --id "$ID" 2>&1) || EXIT_SEND=$?
assert_exit "draft→sent rejected (exit code)"       "$EXIT_SEND" "1"
assert_contains "draft→sent error mentions state"   "$OUT_SEND" "Cannot send"
assert_contains "draft→sent error cites state name" "$OUT_SEND" "draft_created"

STATE_AFTER=$(db_value "$OUTBOX_DB" "SELECT state FROM outbox WHERE id=$ID;")
assert "state unchanged after illegal send"         "$STATE_AFTER" "draft_created"

# --- Test B: approved → approved (double-approve) ---
OUT2=$(test_item "test-sm-002" | $TOOL outbox_create)
ID2=$(json_field "$OUT2" id)
$TOOL outbox_approve --id "$ID2" > /dev/null

EXIT_APPROVE2=0
OUT_APPROVE2=$($TOOL outbox_approve --id "$ID2" 2>&1) || EXIT_APPROVE2=$?
assert_exit "approved→approved rejected (exit code)"     "$EXIT_APPROVE2" "1"
assert_contains "approved→approved error mentions state" "$OUT_APPROVE2" "Cannot approve"
assert_contains "approved→approved cites state name"     "$OUT_APPROVE2" "approved"

# --- Test C: sent → approve (terminal state) ---
OUT3=$(test_item "test-sm-003" | $TOOL outbox_create)
ID3=$(json_field "$OUT3" id)
$TOOL outbox_approve --id "$ID3" > /dev/null
$TOOL outbox_send --id "$ID3" > /dev/null   # now in 'sent'

EXIT_APPROVE3=0
OUT_APPROVE3=$($TOOL outbox_approve --id "$ID3" 2>&1) || EXIT_APPROVE3=$?
assert_exit "sent→approve rejected (exit code)"    "$EXIT_APPROVE3" "1"
assert_contains "sent→approve error mentions state" "$OUT_APPROVE3" "Cannot approve"
assert_contains "sent→approve cites state name"    "$OUT_APPROVE3" "sent"

# --- Test D: double-recall ---
OUT4=$(test_item "test-sm-004" | $TOOL outbox_create)
ID4=$(json_field "$OUT4" id)
$TOOL outbox_approve --id "$ID4" > /dev/null
$TOOL outbox_recall --id "$ID4" > /dev/null

EXIT_RECALL2=0
OUT_RECALL2=$($TOOL outbox_recall --id "$ID4" 2>&1) || EXIT_RECALL2=$?
assert_exit "recalled→recall rejected (exit code)" "$EXIT_RECALL2" "1"
assert_contains "recalled→recall error"            "$OUT_RECALL2" "Cannot recall"
assert_contains "double-recall cites already recalled" "$OUT_RECALL2" "already recalled"

report
