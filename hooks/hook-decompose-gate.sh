#!/bin/bash
# hook-decompose-gate.sh — Advisory decomposition reminder for Agent tool calls
# PreToolUse hook, matcher: "Agent"
# Always exits 0 (advisory, never blocks). Stderr warning shown to Claude.
# Exempts lightweight agent types (Explore, claude-code-guide, statusline-setup).
#
# Escalation path: if compliance drops below 90% over 2 weeks,
# escalate to blocking (exit 2) per three-strikes policy.

INPUT=$(cat)

# Extract subagent_type from tool input
SUBTYPE=$(python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('input', {}).get('subagent_type', ''))
except:
    print('')
" <<< "$INPUT" 2>/dev/null)

# Exempt lightweight/research agent types — these don't need decomposition
case "$SUBTYPE" in
    Explore|claude-code-guide|statusline-setup|Plan)
        exit 0
        ;;
esac

# Advisory warning for work agents (general-purpose or unspecified)
echo "DECOMPOSITION REMINDER (workflow rule #4): Before spawning work agents, list subtasks with deliverables, mark file-level dependencies, and run dependent subtasks sequentially. Skip if this is a simple lookup or <3 tool calls." >&2
exit 0
