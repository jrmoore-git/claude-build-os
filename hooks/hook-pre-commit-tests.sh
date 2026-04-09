#!/bin/bash
# PreToolUse hook: Block git commit if tests fail

INPUT=$(cat)
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"

COMMAND=$(printf '%s' "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

case "$COMMAND" in
  git\ commit*)
    echo "Running tests before commit..."
    cd "$PROJECT_ROOT"
    bash tests/run_all.sh
    if [ $? -ne 0 ]; then
      echo "BLOCKED: tests failed — fix tests before committing"
      exit 2
    fi
    ;;
esac

exit 0
