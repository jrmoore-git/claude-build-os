#!/bin/bash
# Run all tests. Exit 0 if no test runner is configured.
cd "$(git rev-parse --show-toplevel)"

if command -v pytest &>/dev/null; then
    pytest tests/ -q "$@"
else
    echo "pytest not installed — skipping tests"
    exit 0
fi
