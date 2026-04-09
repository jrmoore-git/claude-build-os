#!/usr/bin/env bash
# Contract 7: Version pinning — no unreviewed dependency or model version changes
# Does NOT require temp databases; reads config files only.
set -uo pipefail
source "$(dirname "$0")/helpers.sh"
echo "=== Contract 7: Version Pinning ==="

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
COMPOSE="$REPO_ROOT/docker/docker-compose.yml"
LITELLM_CFG="$REPO_ROOT/config/litellm-config.yaml"

# --- Docker images ---

# Hard fail: :latest tags (fully mutable, unverifiable)
LATEST_COUNT=0
LATEST_COUNT=$(grep -cF ':latest' "$COMPOSE" 2>/dev/null) || true
assert ":latest tags in docker-compose.yml (must be 0)" "$LATEST_COUNT" "0"

# Hard fail: bare image names (no tag or digest at all)
BARE_COUNT=0
BARE_COUNT=$(grep -cE '^[[:space:]]+image:[[:space:]]+[a-z][a-z0-9/._-]+$' "$COMPOSE" 2>/dev/null) || true
assert "bare image names (no tag or digest) in docker-compose.yml (must be 0)" "$BARE_COUNT" "0"

# Warning (not failing): images pinned by tag but not sha256 digest
NON_SHA_IMAGES=$(grep -E 'image:' "$COMPOSE" | grep -v '@sha256' | sed 's/.*image:[[:space:]]*//' | tr -d '"' 2>/dev/null || true)
if [ -n "$NON_SHA_IMAGES" ]; then
    echo "  WARN: images pinned by tag (not sha256 digest) — content-addressable pinning is stronger:"
    echo "$NON_SHA_IMAGES" | sed 's/^/        /'
fi

SHA_COUNT=0
SHA_COUNT=$(grep -cF '@sha256:' "$COMPOSE" 2>/dev/null) || true
echo "  INFO: $SHA_COUNT image(s) pinned by sha256 digest"

# --- Python requirements ---
REQS=$(find "$REPO_ROOT" -name "requirements*.txt" -maxdepth 3 2>/dev/null || true)
if [ -z "$REQS" ]; then
    echo "  INFO: no requirements*.txt files found (no Python deps to check)"
    PASS_COUNT=$((PASS_COUNT + 1))  # vacuously true
else
    while IFS= read -r f; do
        UNPINNED=$(grep -vE '^\s*#|^\s*$' "$f" | grep -vE '==' 2>/dev/null || true)
        if [ -n "$UNPINNED" ]; then
            echo "  FAIL: unpinned Python deps in $f:"
            echo "$UNPINNED" | sed 's/^/        /'
            FAIL_COUNT=$((FAIL_COUNT + 1))
        else
            echo "  PASS: all Python deps in $f are pinned with =="
            PASS_COUNT=$((PASS_COUNT + 1))
        fi
    done <<< "$REQS"
fi

# --- LiteLLM model names ---
# Model strings must contain a version identifier (date suffix like 20250929 or version like 4-6)
BARE_MODELS=$(grep -E '^\s+model:' "$LITELLM_CFG" | grep -vE '[0-9]{6,}|[0-9]+\.[0-9]+|[0-9]+-[0-9]+' 2>/dev/null || true)
if [ -n "$BARE_MODELS" ]; then
    echo "  FAIL: possible bare model aliases (no version) in litellm-config.yaml:"
    echo "$BARE_MODELS" | sed 's/^/        /'
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    echo "  PASS: all model strings in litellm-config.yaml include version identifiers"
    PASS_COUNT=$((PASS_COUNT + 1))
fi

MODEL_STRINGS=$(grep -E '^\s+model:' "$LITELLM_CFG" | sed 's/.*model:[[:space:]]*//' 2>/dev/null || true)
echo "  INFO: model strings found:"
echo "$MODEL_STRINGS" | sed 's/^/        /'

report
