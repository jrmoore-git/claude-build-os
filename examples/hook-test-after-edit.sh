#!/bin/sh
# Hook: Run tests after source file edits
# Install: Add to .claude/settings.json under hooks.PostToolUse
#
# Example settings.json:
# {
#   "hooks": {
#     "PostToolUse": [
#       {
#         "matcher": "Write|Edit",
#         "hooks": [
#           {
#             "type": "command",
#             "command": "sh examples/hook-test-after-edit.sh $CLAUDE_FILE_PATH"
#           }
#         ]
#       }
#     ]
#   }
# }

FILE="$1"

# Only run tests for source files, not docs or config
case "$FILE" in
  *.py)
    echo "Running Python tests..."
    python3 -m pytest tests/ -q 2>&1 | tail -5
    ;;
  *.ts|*.tsx|*.js|*.jsx)
    echo "Running JS/TS tests..."
    npm test -- --silent 2>&1 | tail -5
    ;;
  *.go)
    echo "Running Go tests..."
    go test ./... 2>&1 | tail -5
    ;;
  *)
    # No tests for non-source files
    exit 0
    ;;
esac
