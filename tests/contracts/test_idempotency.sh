#!/usr/bin/env bash
# test_idempotency.sh — Config loading determinism
# Verifies debate.py produces identical output on repeated runs (no LLM calls needed).
set -euo pipefail
source "$(dirname "$0")/helpers.sh"
cd "$PROJECT_ROOT"

echo "=== Contract: Idempotency (config loading determinism) ==="

# 1. challenge --help output is deterministic
HELP1=$(python3.11 scripts/debate.py challenge --help 2>&1)
HEXIT1=$?
HELP2=$(python3.11 scripts/debate.py challenge --help 2>&1)
HEXIT2=$?

assert "challenge --help exit code stable" "$HEXIT1" "$HEXIT2"
assert "challenge --help output identical" "$HELP1" "$HELP2"

# 2. Config loading is deterministic (parse debate-models.json twice)
CFG1=$(python3.11 -c "
import json, sys
sys.path.insert(0, 'scripts')
cfg = json.load(open('config/debate-models.json'))
print(json.dumps(cfg, sort_keys=True))
" 2>&1)
CFG2=$(python3.11 -c "
import json, sys
sys.path.insert(0, 'scripts')
cfg = json.load(open('config/debate-models.json'))
print(json.dumps(cfg, sort_keys=True))
" 2>&1)

assert "config loading output identical" "$CFG1" "$CFG2"

# 3. review-panel --help is deterministic
RP1=$(python3.11 scripts/debate.py review-panel --help 2>&1)
RPEXIT1=$?
RP2=$(python3.11 scripts/debate.py review-panel --help 2>&1)
RPEXIT2=$?

assert "review-panel --help exit code stable" "$RPEXIT1" "$RPEXIT2"
assert "review-panel --help output identical" "$RP1" "$RP2"

report
