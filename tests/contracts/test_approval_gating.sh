#!/usr/bin/env bash
# Contract 2: Approval gating — no send executes without explicit approval
set -uo pipefail
source "$(dirname "$0")/helpers.sh"
echo "=== Contract 2: Approval Gating ==="
setup_test_dbs
trap teardown_test_dbs EXIT

# Enable send token so we test state gating, not the token flag
$SQLITE "$PREFS_DB" "INSERT INTO preferences (category,key,value,source) VALUES ('autonomy','send_token_enabled','1','test');"
setup_mock_send

# Create item (state=draft_created)
OUT=$(test_item "test-gate-001" | $TOOL outbox_create)
ID=$(json_field "$OUT" id)
assert "item created" "$(json_field "$OUT" status)" "ok"

# Attempt send on non-approved item — must be rejected
EXIT_SEND=0
OUT_SEND=$($TOOL outbox_send --id "$ID" 2>&1) || EXIT_SEND=$?
assert_exit "send on draft_created exits non-zero" "$EXIT_SEND" "1"
assert_contains "send rejected with state error"   "$OUT_SEND" "Cannot send"
assert_contains "error references current state"   "$OUT_SEND" "draft_created"

# Approve it, then send succeeds (proves gate is the only blocker)
$TOOL outbox_approve --id "$ID" > /dev/null
OUT_SEND2=$($TOOL outbox_send --id "$ID")
assert "send succeeds after approval" "$(json_field "$OUT_SEND2" state)" "sent"

# Recalled item cannot be sent even if state is still 'approved'
OUT2=$(test_item "test-gate-002" | $TOOL outbox_create)
ID2=$(json_field "$OUT2" id)
$TOOL outbox_approve --id "$ID2" > /dev/null
$TOOL outbox_recall --id "$ID2" > /dev/null
EXIT_SEND3=0
OUT_SEND3=$($TOOL outbox_send --id "$ID2" 2>&1) || EXIT_SEND3=$?
assert_exit "send on recalled item exits non-zero" "$EXIT_SEND3" "1"
assert_contains "recalled item rejected"           "$OUT_SEND3" "recalled"

report
