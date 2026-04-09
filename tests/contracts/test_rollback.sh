#!/usr/bin/env bash
# Contract 6: Rollback — every change can be reverted within the grace window
set -uo pipefail
source "$(dirname "$0")/helpers.sh"
echo "=== Contract 6: Rollback ==="
setup_test_dbs
trap teardown_test_dbs EXIT

# --- Test A: recall within grace window succeeds ---
OUT=$(echo '{"idempotency_key":"test-roll-001","action_type":"email_reply","target":"contract-test@testdomain.internal","content":"Hello","tier":3,"account":"sender@example.com","grace_period_seconds":60}' | $TOOL outbox_create)
ID=$(json_field "$OUT" id)
assert "item created" "$(json_field "$OUT" status)" "ok"

$TOOL outbox_approve --id "$ID" > /dev/null

STATE_PRE=$(db_value "$OUTBOX_DB" "SELECT state FROM outbox WHERE id=$ID;")
assert "state is approved before recall" "$STATE_PRE" "approved"

OUT_RECALL=$($TOOL outbox_recall --id "$ID")
assert "recall returns ok"     "$(json_field "$OUT_RECALL" status)"  "ok"
assert "recall rowcount is 1"  "$(json_field "$OUT_RECALL" updated)" "1"

RECALLED=$(db_value "$OUTBOX_DB" "SELECT recalled FROM outbox WHERE id=$ID;")
assert "recalled flag is set"  "$RECALLED" "1"

RECALLED_AT=$(db_value "$OUTBOX_DB" "SELECT recalled_at FROM outbox WHERE id=$ID;")
assert "recalled_at timestamp recorded" "$([ -n "$RECALLED_AT" ] && echo yes || echo no)" "yes"

AUDIT_COUNT=$(db_count "$AUDIT_DB" audit_log "action_type='approval_recall'")
assert "recall audit entry exists"       "$AUDIT_COUNT" "1"

# --- Test B: recall after grace window fails ---
OUT2=$(echo '{"idempotency_key":"test-roll-002","action_type":"email_reply","target":"contract-test@testdomain.internal","content":"Hello","tier":3,"account":"sender@example.com","grace_period_seconds":1}' | $TOOL outbox_create)
ID2=$(json_field "$OUT2" id)
$TOOL outbox_approve --id "$ID2" > /dev/null

sleep 2   # wait for 1-second grace to expire

EXIT_RECALL2=0
OUT_RECALL2=$($TOOL outbox_recall --id "$ID2" 2>&1) || EXIT_RECALL2=$?
assert_exit "recall after grace window fails"         "$EXIT_RECALL2" "1"
assert_contains "expired grace window error message"  "$OUT_RECALL2" "Recall window expired"

RECALLED2=$(db_value "$OUTBOX_DB" "SELECT recalled FROM outbox WHERE id=$ID2;")
assert "item not recalled after window expires"       "$RECALLED2" "0"

# --- Test C: recall requires approved state ---
OUT3=$(test_item "test-roll-003" | $TOOL outbox_create)
ID3=$(json_field "$OUT3" id)

EXIT_RECALL3=0
OUT_RECALL3=$($TOOL outbox_recall --id "$ID3" 2>&1) || EXIT_RECALL3=$?
assert_exit "recall of non-approved item fails"       "$EXIT_RECALL3" "1"
assert_contains "recall on draft error"               "$OUT_RECALL3" "Cannot recall"

report
