#!/bin/bash
# PostToolUse hook: Syntax-check Python files after write/edit
# Reads tool input JSON from stdin, runs py_compile on .py files

source "$(dirname "$0")/resolve-python.sh"

INPUT=$(cat)
FILE_PATH=$(printf '%s' "$INPUT" | "$PYTHON3" -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# Only check .py files
case "$FILE_PATH" in
  *.py)
    if [ -f "$FILE_PATH" ]; then
      "$PYTHON3" -m py_compile "$FILE_PATH" 2>&1
      if [ $? -ne 0 ]; then
        echo "SYNTAX ERROR in $FILE_PATH — fix before continuing"
        exit 1
      fi
    fi
    ;;
esac

exit 0
