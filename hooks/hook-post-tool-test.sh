#!/bin/bash
# PostToolUse hook: Run pytest for the corresponding test when a scripts/*_tool.py is written/edited

source "$(dirname "$0")/resolve-python.sh"

INPUT=$(cat)
FILE_PATH=$(printf '%s' "$INPUT" | "$PYTHON3" -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# Only act on scripts/*_tool.py files
case "$FILE_PATH" in
  */scripts/*_tool.py)
    PROJECT="$(git rev-parse --show-toplevel)"
    NAME=$(basename "$FILE_PATH" | sed 's/_tool\.py$//')
    TEST_FILE="$PROJECT/tests/test_${NAME}.py"
    if [ -f "$TEST_FILE" ]; then
      echo "Running pytest for ${NAME}..."
      cd "$PROJECT"
      "$PYTHON3" -m pytest "$TEST_FILE" -q --tb=short
      exit $?
    else
      echo "No test file for ${NAME} (expected ${TEST_FILE})"
    fi
    ;;
esac

exit 0
