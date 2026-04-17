#!/bin/bash
# hook-class: enforcement-high
# PreToolUse hook: Block .env writes and credential management commands
# Fires on: Write|Edit (file_path check + SKILL.md content check)
#            Bash (command check)

INPUT=$(cat)

RESULT=$(/opt/homebrew/bin/python3.11 -c "
import sys, json, re

try:
    d = json.load(sys.stdin)
except json.JSONDecodeError:
    print('ALLOW')
    sys.exit(0)

ti = d.get('tool_input', {})
file_path = ti.get('file_path', '')
command   = ti.get('command', '')
content   = ti.get('content') or ti.get('new_string') or ''

# Check 1: .env file writes — prompt approval
if file_path.endswith('.env'):
    print('ASK_ENV:' + file_path)
    sys.exit(0)

# Check 2: Forbidden credential management commands
# For Bash: check the command string
if re.search(r'gog auth (remove|add|login|logout)', command):
    print('BLOCK_CRED')
    sys.exit(0)

# For Write/Edit on SKILL.md files only: check content
# (allows mentioning gog auth in docs/lessons — only blocks it in skills)
if 'SKILL.md' in file_path and re.search(r'gog auth (remove|add|login|logout)', content):
    print('BLOCK_CRED')
    sys.exit(0)

print('ALLOW')
" <<< "$INPUT" 2>/dev/null)

case "$RESULT" in
  ASK_ENV:*)
    FILE_PATH="${RESULT#ASK_ENV:}"
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Writing to .env file: %s — approve if this is an intentional credential change."}}\n' "$FILE_PATH"
    exit 0
    ;;
  BLOCK_CRED)
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"block","permissionDecisionReason":"BLOCKED: gog auth credential management is forbidden from skills and Claude Code. Auth is owned exclusively by the user and the health daemon. See CLAUDE.md Hard Rules."}}\n'
    exit 2
    ;;
  *)
    exit 0
    ;;
esac
