#!/usr/bin/env bash
# helpers.sh — Shared setup/teardown for contract tests
# Source this from each test: source "$(dirname "$0")/helpers.sh"

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TOOL="python3 $PROJECT_ROOT/scripts/outbox_tool.py"
SQLITE="sqlite3"

# --- DB setup ---

setup_test_dbs() {
    TEST_DIR="$(mktemp -d)"
    export OUTBOX_DB="$TEST_DIR/outbox.db"
    export AUDIT_DB="$TEST_DIR/audit.db"
    export PREFS_DB="$TEST_DIR/prefs.db"
    export METRICS_DB="$TEST_DIR/metrics.db"

    $SQLITE "$OUTBOX_DB" <<'SQL'
CREATE TABLE outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idempotency_key TEXT NOT NULL UNIQUE,
    action_type TEXT NOT NULL,
    target TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    tier INTEGER NOT NULL,
    account TEXT,
    state TEXT NOT NULL DEFAULT 'draft_created',
    approval_requested_at TIMESTAMP,
    approval_channel TEXT,
    approved_by TEXT,
    approved_at TIMESTAMP,
    send_attempted_at TIMESTAMP,
    sent_at TIMESTAMP,
    external_id TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    promise_id INTEGER,
    requested_by TEXT,
    request_source TEXT,
    grace_period_seconds INTEGER DEFAULT 30,
    send_after TIMESTAMP,
    recalled BOOLEAN DEFAULT 0,
    recalled_at TIMESTAMP,
    defer_count INTEGER DEFAULT 0,
    original_content_hash TEXT,
    original_content TEXT,
    draft_reply TEXT,
    source_url TEXT,
    snooze_until TEXT,
    dismissed_at TIMESTAMP,
    dismiss_reason TEXT,
    auto_resolvable BOOLEAN DEFAULT 0,
    subject TEXT,
    cc TEXT,
    bcc TEXT
);
CREATE TRIGGER outbox_updated_at AFTER UPDATE ON outbox FOR EACH ROW
    BEGIN UPDATE outbox SET updated_at = datetime('now') WHERE id = NEW.id; END;
SQL

    $SQLITE "$AUDIT_DB" <<'SQL'
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_type TEXT NOT NULL,
    target TEXT,
    content_hash TEXT,
    summary TEXT NOT NULL,
    tier INTEGER,
    autonomy_level INTEGER,
    triggered_by TEXT,
    context_tokens_used INTEGER,
    model_used TEXT,
    api_cost_usd REAL
);
SQL

    $SQLITE "$PREFS_DB" <<'SQL'
CREATE TABLE preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    source TEXT NOT NULL,
    approved_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    previous_value TEXT,
    UNIQUE(category, key)
);
CREATE TABLE email_allowlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    name TEXT,
    source TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Pre-populate test email addresses used by test_item() fixture
INSERT INTO email_allowlist (email, source) VALUES ('contract-test@testdomain.internal', 'test');
CREATE TABLE IF NOT EXISTS send_routing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_pattern TEXT NOT NULL UNIQUE,
    send_as_account TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO send_routing (domain_pattern, send_as_account, priority) VALUES ('testdomain.internal', 'sender@example.com', 10);
CREATE TABLE IF NOT EXISTS confirmed_recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    normalized_address TEXT NOT NULL,
    send_as_account TEXT NOT NULL,
    confirmed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(normalized_address, send_as_account)
);
INSERT INTO confirmed_recipients (normalized_address, send_as_account) VALUES ('contract-test@testdomain.internal', 'sender@example.com');
SQL

    $SQLITE "$METRICS_DB" <<'SQL'
CREATE TABLE learning_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_type TEXT NOT NULL CHECK(signal_type IN ('approved','rejected','edited','tier_override')),
    category TEXT NOT NULL,
    tier INTEGER,
    account TEXT,
    source_outbox_id INTEGER,
    edit_distance REAL,
    original_text_hash TEXT,
    replacement_text_hash TEXT,
    override_from_tier INTEGER,
    override_to_tier INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_outbox_id, signal_type)
);
SQL
}

teardown_test_dbs() {
    [ -n "$TEST_DIR" ] && rm -rf "$TEST_DIR"
}

# --- Standard test item JSON ---
# Usage: test_item [idempotency_key]
test_item() {
    local key="${1:-test-contract-001}"
    printf '{"idempotency_key":"%s","action_type":"email_reply","target":"contract-test@testdomain.internal","content":"Subject: Test\\n\\nHello world","tier":3,"account":"sender@example.com","original_content":"Original email from sender.","draft_reply":"Hello world"}' "$key"
}

# Mock send binary for contract tests (send always succeeds, search returns empty)
setup_mock_send() {
    MOCK_BIN="$TEST_DIR/bin"
    mkdir -p "$MOCK_BIN"
    cat > "$MOCK_BIN/send-email" <<'MOCK'
#!/bin/bash
if [[ "$*" == *"send"* ]]; then
    echo '{"id": "mock-msg-001"}'
    exit 0
elif [[ "$*" == *"search"* ]]; then
    echo '[]'
    exit 0
fi
exit 1
MOCK
    chmod +x "$MOCK_BIN/send-email"
    export PATH="$MOCK_BIN:$PATH"
}

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
    python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d.get('$field',''))" "$json" 2>/dev/null
}

db_count() {
    local db="$1"
    local table="$2"
    local where="${3:-1=1}"
    $SQLITE "$db" "SELECT COUNT(*) FROM $table WHERE $where;" 2>/dev/null
}

db_value() {
    local db="$1"
    local query="$2"
    $SQLITE "$db" "$query" 2>/dev/null
}

report() {
    echo ""
    echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
    if [ "$FAIL_COUNT" -gt 0 ]; then
        exit 1
    fi
    exit 0
}
