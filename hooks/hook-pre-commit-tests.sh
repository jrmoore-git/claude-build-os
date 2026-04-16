#!/bin/bash
# PreToolUse hook: Block git commit if pytest fails

INPUT=$(cat)

# Tier gate: requires tier >= 2
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
/opt/homebrew/bin/python3.11 "$PROJECT_ROOT/scripts/read_tier.py" --check 2 2>/dev/null || exit 0

COMMAND=$(printf '%s' "$INPUT" | /opt/homebrew/bin/python3.11 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

case "$COMMAND" in
  git\ commit*)
    echo "Running tests before commit..."
    cd "$(git rev-parse --show-toplevel)"
    bash tests/run_all.sh
    if [ $? -ne 0 ]; then
      echo "BLOCKED: pytest failed — fix tests before committing"
      exit 2
    fi
    ;;
esac

exit 0
