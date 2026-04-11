#!/usr/bin/env bash
# test_version_pinning.sh — Version pinning contract
# Verifies model configs and dependency files pin explicit versions (no "latest").
set -euo pipefail
source "$(dirname "$0")/helpers.sh"
cd "$PROJECT_ROOT"

echo "=== Contract: Version Pinning ==="

# 1. debate-models.json exists and is valid JSON
MODELS_FILE="config/debate-models.json"
assert "debate-models.json exists" "$(test -f "$MODELS_FILE" && echo yes || echo no)" "yes"

PARSE_RESULT=$(python3.11 -c "import json; json.load(open('$MODELS_FILE')); print('valid')" 2>&1 || true)
assert "debate-models.json is valid JSON" "$PARSE_RESULT" "valid"

# 2. All model strings contain version identifiers (date suffix or version number)
NO_VERSION=$(python3.11 -c "
import json, re, sys
cfg = json.load(open('$MODELS_FILE'))
bad = []
for key in ('persona_model_map', 'refine_rotation'):
    val = cfg.get(key, {})
    models = val.values() if isinstance(val, dict) else val
    for m in models:
        if not re.search(r'-\d', m):
            bad.append(m)
for key in ('judge_default', 'compare_default', 'single_review_default', 'verifier_default'):
    m = cfg.get(key, '')
    if m and not re.search(r'-\d', m):
        bad.append(m)
print(','.join(bad) if bad else 'none')
" 2>&1 || echo "error")
assert "all model strings have version identifiers" "$NO_VERSION" "none"

# 3. No "latest" tags in model names
HAS_LATEST=$(python3.11 -c "
import json
cfg = json.load(open('$MODELS_FILE'))
text = json.dumps(cfg)
print('found' if 'latest' in text.lower() else 'none')
" 2>&1 || echo "error")
assert "no 'latest' tags in model names" "$HAS_LATEST" "none"

# 4. Docker compose — skip gracefully if not present
if [ -f "docker/docker-compose.yml" ]; then
    DOCKER_LATEST=$(grep -c ':latest' docker/docker-compose.yml 2>/dev/null || echo "0")
    assert "no :latest tags in docker-compose.yml" "$DOCKER_LATEST" "0"
else
    echo "  SKIP: docker/docker-compose.yml not found (no Docker in BuildOS)"
fi

# 5. Requirements files — skip gracefully if not present
REQ_FILES=$(ls requirements*.txt 2>/dev/null || true)
if [ -n "$REQ_FILES" ]; then
    UNPINNED=$(python3.11 -c "
import sys, glob
bad = []
for f in glob.glob('requirements*.txt'):
    for line in open(f):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('-'):
            continue
        if '==' not in line:
            bad.append(f'{f}:{line}')
print(','.join(bad) if bad else 'none')
" 2>&1 || echo "error")
    assert "all requirements pinned with ==" "$UNPINNED" "none"
else
    echo "  SKIP: no requirements*.txt found (BuildOS uses stdlib only)"
fi

report
