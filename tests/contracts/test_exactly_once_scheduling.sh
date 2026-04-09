#!/usr/bin/env bash
# Contract 8: Exactly-once scheduling — duplicate scheduler fires produce exactly one outbox entry
#
# Scheduled cron jobs use date-windowed idempotency keys (e.g., "daily-task-2026-03-07").
# If the cron fires twice in the same window (service restart, retry, clock drift), the second
# fire must not create a duplicate outbox row or audit entry.
#
# This tests the outbox-layer idempotency mechanism that underpins scheduled actions.
# Application-layer dedup (skill-level audit-log checks) is separate and tested in skill unit tests.
set -uo pipefail
source "$(dirname "$0")/helpers.sh"
echo "=== Contract 8: Exactly-Once Scheduling ==="
setup_test_dbs
trap teardown_test_dbs EXIT

TODAY=$(python3 -c "
from datetime import datetime
from zoneinfo import ZoneInfo
print(datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d'))
")
YESTERDAY=$(python3 -c "
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
print((datetime.now(ZoneInfo('America/Los_Angeles')) - timedelta(days=1)).strftime('%Y-%m-%d'))
")

KEY_TODAY="daily-task-$TODAY"
KEY_YESTERDAY="daily-task-$YESTERDAY"

# --- Test A: First fire for today's window creates the entry ---
OUT1=$(printf '{"idempotency_key":"%s","action_type":"email_fyi","target":"notification","content":"Daily summary","tier":1,"account":"sender@example.com"}' "$KEY_TODAY" | $TOOL outbox_create)
assert "first fire: status ok"      "$(json_field "$OUT1" status)"  "ok"
assert "first fire: created true"   "$(json_field "$OUT1" created)" "True"
ID=$(json_field "$OUT1" id)
assert "first fire: numeric id"     "$(echo "$ID" | grep -c '^[0-9]*$')" "1"

# --- Test B: Second fire for same window (duplicate cron) returns existing entry ---
OUT2=$(printf '{"idempotency_key":"%s","action_type":"email_fyi","target":"notification","content":"Daily summary","tier":1,"account":"sender@example.com"}' "$KEY_TODAY" | $TOOL outbox_create)
assert "second fire: status ok"     "$(json_field "$OUT2" status)"  "ok"
assert "second fire: created false" "$(json_field "$OUT2" created)" "False"
assert "second fire: same id"       "$(json_field "$OUT2" id)"      "$ID"

# --- Test C: Exactly one outbox row for this window ---
ROW_COUNT=$(db_count "$OUTBOX_DB" outbox "idempotency_key='$KEY_TODAY'")
assert "exactly one row for today's window"   "$ROW_COUNT" "1"

# --- Test D: Exactly one audit entry (not two) ---
AUDIT_COUNT=$(db_count "$AUDIT_DB" audit_log "action_type='outbox_create'")
assert "exactly one audit entry from double fire" "$AUDIT_COUNT" "1"

# --- Test E: Yesterday's window is a separate entry (not blocked by today's) ---
OUT3=$(printf '{"idempotency_key":"%s","action_type":"email_fyi","target":"notification","content":"Daily summary","tier":1,"account":"sender@example.com"}' "$KEY_YESTERDAY" | $TOOL outbox_create)
assert "prior window creates new entry"       "$(json_field "$OUT3" created)" "True"
assert "prior window gets different id"       "$([ "$(json_field "$OUT3" id)" != "$ID" ] && echo yes || echo no)" "yes"

TOTAL_ROWS=$(db_count "$OUTBOX_DB" outbox)
assert "two total rows (today + yesterday window)" "$TOTAL_ROWS" "2"

TOTAL_AUDIT=$(db_count "$AUDIT_DB" audit_log "action_type='outbox_create'")
assert "two audit entries total (one per window)"  "$TOTAL_AUDIT" "2"

report
