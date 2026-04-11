#!/usr/bin/env bash
# test_audit_completeness.sh — debate-log.jsonl operational log contract
# Verifies the debate log exists, contains valid JSON lines, and has required fields.
set -euo pipefail
source "$(dirname "$0")/helpers.sh"
cd "$PROJECT_ROOT"

echo "=== Contract: Audit Completeness (debate-log.jsonl) ==="

LOG_FILE="stores/debate-log.jsonl"

# 1. File exists
assert "debate-log.jsonl exists" "$(test -f "$LOG_FILE" && echo yes || echo no)" "yes"

if [ ! -f "$LOG_FILE" ]; then
    echo "  SKIP: remaining checks (file missing)"
    report
fi

# 2. Count entries
LINE_COUNT=$(wc -l < "$LOG_FILE" | tr -d ' ')
echo "  INFO: $LINE_COUNT entries in debate-log.jsonl"

# 3. All lines are valid JSON with required fields
# debate-log.jsonl uses 'phase' (the debate mode) and 'timestamp' as core fields
VALIDATION=$(python3.11 -c "
import json, sys
bad_json = 0
missing_fields = 0
total = 0
required = {'timestamp', 'phase'}
for i, line in enumerate(open('$LOG_FILE'), 1):
    line = line.strip()
    if not line:
        continue
    total += 1
    try:
        entry = json.loads(line)
        present = set(entry.keys())
        if not required.issubset(present):
            missing_fields += 1
    except json.JSONDecodeError:
        bad_json += 1
print(f'{bad_json},{missing_fields},{total}')
" 2>&1 || echo "error,error,error")

BAD_JSON=$(echo "$VALIDATION" | cut -d, -f1)
MISSING_FIELDS=$(echo "$VALIDATION" | cut -d, -f2)
TOTAL=$(echo "$VALIDATION" | cut -d, -f3)

assert "all lines are valid JSON" "$BAD_JSON" "0"
assert "all entries have timestamp and phase" "$MISSING_FIELDS" "0"
echo "  INFO: $TOTAL valid entries parsed"

report
