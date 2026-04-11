#!/usr/bin/env bash
# helpers.sh — Shared setup/teardown for BuildOS contract tests
# Source this from each test: source "$(dirname "$0")/helpers.sh"

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# --- Assertion helpers ---
PASS_COUNT=0
FAIL_COUNT=0
TEST_NAME=""

assert() {
    local desc="$1"
    local actual="$2"
    local expected="$3"
    if [ "$actual" = "$expected" ]; then
        echo "  PASS: $desc"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "  FAIL: $desc"
        echo "        expected: $expected"
        echo "        actual:   $actual"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

assert_contains() {
    local desc="$1"
    local haystack="$2"
    local needle="$3"
    if echo "$haystack" | grep -qF "$needle"; then
        echo "  PASS: $desc"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "  FAIL: $desc"
        echo "        expected to find: $needle"
        echo "        in: $haystack"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

assert_exit() {
    local desc="$1"
    local actual_code="$2"
    local expected_code="$3"
    assert "$desc (exit code)" "$actual_code" "$expected_code"
}

json_field() {
    local json="$1"
    local field="$2"
    python3.11 -c "import json,sys; d=json.loads(sys.argv[1]); print(d.get('$field',''))" "$json" 2>/dev/null
}

report() {
    echo ""
    echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
    if [ "$FAIL_COUNT" -gt 0 ]; then
        exit 1
    fi
    exit 0
}
