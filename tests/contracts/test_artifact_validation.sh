#!/usr/bin/env bash
# test_artifact_validation.sh — artifact_check.py validates existence and staleness
# Verifies artifact_check returns structured JSON for both missing and existing topics.
set -euo pipefail
source "$(dirname "$0")/helpers.sh"
cd "$PROJECT_ROOT"

echo "=== Contract: Artifact Validation (artifact_check.py) ==="

# 1. Run against a nonexistent topic — should return valid JSON, not crash
OUTPUT=$(python3.11 scripts/artifact_check.py --scope nonexistent-topic-xyz 2>&1)
EXIT_CODE=$?
assert "artifact_check exits 0 for missing topic" "$EXIT_CODE" "0"

# 2. Output is valid JSON
JSON_VALID=$(python3.11 -c "import json,sys; json.loads(sys.argv[1]); print('valid')" "$OUTPUT" 2>&1 || echo "invalid")
assert "output is valid JSON" "$JSON_VALID" "valid"

# 3. Reports missing artifacts (none should exist for nonexistent topic)
MISSING_CHECK=$(python3.11 -c "
import json, sys
data = json.loads(sys.argv[1])
artifacts = data.get('artifacts', {})
all_missing = all(not a.get('exists', False) for a in artifacts.values())
print('yes' if all_missing else 'no')
" "$OUTPUT" 2>&1 || echo "error")
assert "reports all artifacts missing for nonexistent topic" "$MISSING_CHECK" "yes"

# 4. Has expected structure
STRUCTURE_CHECK=$(python3.11 -c "
import json, sys
data = json.loads(sys.argv[1])
has_scope = 'scope' in data
has_artifacts = 'artifacts' in data
has_git = 'git_head' in data
print('ok' if has_scope and has_artifacts and has_git else 'missing fields')
" "$OUTPUT" 2>&1 || echo "error")
assert "output has scope, artifacts, git_head" "$STRUCTURE_CHECK" "ok"

# 5. If a real topic artifact exists, run on it
REAL_TOPIC=$(ls tasks/*-plan.md 2>/dev/null | head -1 | sed 's|tasks/||;s|-plan.md||' || true)
if [ -n "$REAL_TOPIC" ]; then
    REAL_OUTPUT=$(python3.11 scripts/artifact_check.py --scope "$REAL_TOPIC" 2>&1)
    REAL_EXIT=$?
    assert "artifact_check exits 0 for real topic ($REAL_TOPIC)" "$REAL_EXIT" "0"

    REAL_JSON=$(python3.11 -c "import json,sys; json.loads(sys.argv[1]); print('valid')" "$REAL_OUTPUT" 2>&1 || echo "invalid")
    assert "real topic output is valid JSON" "$REAL_JSON" "valid"

    PLAN_EXISTS=$(python3.11 -c "
import json, sys
data = json.loads(sys.argv[1])
print('yes' if data.get('artifacts',{}).get('plan',{}).get('exists') else 'no')
" "$REAL_OUTPUT" 2>&1 || echo "error")
    assert "real topic plan artifact exists" "$PLAN_EXISTS" "yes"
else
    echo "  SKIP: no real topic artifact found in tasks/"
fi

report
