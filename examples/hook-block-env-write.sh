#!/bin/sh
# Hook: Block writes to .env files
# Prevents accidentally exposing secrets through Claude Code edits
#
# Install: Add to .claude/settings.json under hooks.PreToolUse
#
# Example settings.json:
# {
#   "hooks": {
#     "PreToolUse": [
#       {
#         "matcher": "Write|Edit",
#         "hooks": [
#           {
#             "type": "command",
#             "command": "sh examples/hook-block-env-write.sh $CLAUDE_FILE_PATH"
#           }
#         ]
#       }
#     ]
#   }
# }

FILE="$1"

case "$FILE" in
  *.env|*.env.*|.env)
    echo "BLOCKED: Cannot write to .env files through Claude Code."
    echo "Edit .env files manually to prevent secret exposure in tool output."
    exit 1
    ;;
  *)
    exit 0
    ;;
esac
