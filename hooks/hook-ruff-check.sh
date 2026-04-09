#!/bin/bash
# PostToolUse hook: ruff C901 (complexity) + E501 (line length) on edited Python files.
# Non-blocking — exits 0 always. Violations are printed to stdout so Claude sees them.

TMPFILE=$(mktemp /tmp/hook-ruff-check-XXXXXX.json)
cat > "$TMPFILE"

FILE=$(/opt/homebrew/bin/python3.11 -c "
import sys, json
with open(sys.argv[1]) as f:
    data = json.load(f)
path = data.get('tool_input', {}).get('file_path', '')
print(path)
" "$TMPFILE" 2>/dev/null)

rm -f "$TMPFILE"

# Only run on .py files
case "$FILE" in
  *.py) ;;
  *) exit 0 ;;
esac

[ -f "$FILE" ] || exit 0

RESULT=$(/opt/homebrew/bin/ruff check --select C901,E501 --line-length 120 "$FILE" 2>&1)

if [ -n "$RESULT" ]; then
    echo "ruff: $FILE"
    echo "$RESULT"
fi

exit 0
