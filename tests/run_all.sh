#!/bin/bash
# Run all tests: pytest-discoverable tests + standalone test scripts.
# Exit non-zero if any test fails.
cd "$(git rev-parse --show-toplevel)"

FAILED=0

# 1. pytest-discoverable tests
if command -v pytest &>/dev/null; then
    pytest tests/ -q "$@"
    [ $? -ne 0 ] && FAILED=1
else
    echo "=========================================================================" >&2
    echo "FAIL: pytest not installed — cannot run the main test suite." >&2
    echo "      Install with: pip3.11 install -r requirements-dev.txt" >&2
    echo "      (Only 2 smoke tests below are running; most coverage is skipped.)" >&2
    echo "=========================================================================" >&2
    FAILED=1
fi

# 2. Standalone test scripts (not discovered by pytest — they use custom runners)
for script in tests/test_tool_loop_config.py tests/test_debate_smoke.py; do
    if [ -f "$script" ]; then
        python3.11 "$script"
        if [ $? -ne 0 ]; then
            echo "FAIL: $script"
            FAILED=1
        fi
    fi
done

exit $FAILED
