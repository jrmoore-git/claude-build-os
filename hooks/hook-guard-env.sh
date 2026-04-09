#!/bin/bash
# PreToolUse hook: Block .env writes and credential management commands
# Fires on: Write|Edit (file_path check + content check)
#            Bash (command check)

INPUT=$(cat)

RESULT=$(python3 -c "
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

# Check 2: Forbidden credential management commands in Bash
# Add patterns for any credential CLI tools your project uses
forbidden_patterns = [
    r'auth (remove|add|login|logout)',
]
for pat in forbidden_patterns:
    if re.search(pat, command):
        print('BLOCK_CRED')
        sys.exit(0)

# For Write/Edit on skill files only: check content for credential commands
if 'SKILL.md' in file_path:
    for pat in forbidden_patterns:
        if re.search(pat, content):
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
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"block","permissionDecisionReason":"BLOCKED: Credential management commands are forbidden from skills and automated contexts. Auth is owned exclusively by the user and the health daemon."}}\n'
    exit 2
    ;;
  *)
    exit 0
    ;;
esac
