#!/bin/bash
# PostToolUse hook: Run pytest for the corresponding test when a scripts/*_tool.py is written/edited

INPUT=$(cat)

# Tier gate: requires tier >= 2
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
/opt/homebrew/bin/python3.11 "$PROJECT_ROOT/scripts/read_tier.py" --check 2 2>/dev/null || exit 0

FILE_PATH=$(printf '%s' "$INPUT" | /opt/homebrew/bin/python3.11 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# Only act on scripts/*_tool.py files
case "$FILE_PATH" in
  */scripts/*_tool.py)
    PROJECT="$(git rev-parse --show-toplevel)"
    NAME=$(basename "$FILE_PATH" | sed 's/_tool\.py$//')
    TEST_FILE="$PROJECT/tests/test_${NAME}.py"
    if [ -f "$TEST_FILE" ]; then
      echo "Running pytest for ${NAME}..."
      cd "$PROJECT"
      /opt/homebrew/bin/python3.11 -m pytest "$TEST_FILE" -q --tb=short
      exit $?
    else
      echo "No test file for ${NAME} (expected ${TEST_FILE})"
    fi
    ;;
esac

exit 0
