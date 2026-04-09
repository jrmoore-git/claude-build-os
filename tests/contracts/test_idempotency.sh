#!/usr/bin/env bash
# Contract 1: Idempotency — duplicate inputs never produce duplicate outputs
set -uo pipefail
source "$(dirname "$0")/helpers.sh"
echo "=== Contract 1: Idempotency ==="
setup_test_dbs
trap teardown_test_dbs EXIT

# First create
OUT1=$(test_item "test-idem-001" | $TOOL outbox_create)
assert "first create returns status ok"      "$(json_field "$OUT1" status)"  "ok"
assert "first create returns created:true"   "$(json_field "$OUT1" created)" "True"
ID=$(json_field "$OUT1" id)
assert "first create returns a numeric id"   "$(echo "$ID" | grep -c '^[0-9]*$')" "1"

# Second create — same key
OUT2=$(test_item "test-idem-001" | $TOOL outbox_create)
assert "second create returns status ok"     "$(json_field "$OUT2" status)"  "ok"
assert "second create returns created:false" "$(json_field "$OUT2" created)" "False"
assert "second create returns same id"       "$(json_field "$OUT2" id)"      "$ID"

# DB has exactly one row
ROW_COUNT=$(db_count "$OUTBOX_DB" outbox "idempotency_key='test-idem-001'")
assert "exactly one row in outbox"           "$ROW_COUNT" "1"

# Audit has exactly one outbox_create entry (not two)
AUDIT_COUNT=$(db_count "$AUDIT_DB" audit_log "action_type='outbox_create'")
assert "exactly one audit entry for create" "$AUDIT_COUNT" "1"

report
