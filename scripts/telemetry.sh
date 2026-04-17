#!/bin/bash
# Fast telemetry emitter for shell hooks. jq-based; ~8ms per call.
# Usage: scripts/telemetry.sh <event_type> key=value [key=value ...]
# Values are JSON-stringified as-is; booleans pass "true"/"false" literally via --argjson keys:
#   scripts/telemetry.sh hook_fire hook_name=plan-gate tool_name=Bash decision=block reason=no-plan
# Never fails out: any error silently drops the event.

set +e

EVENT_TYPE="$1"
shift || exit 0

[ -z "$EVENT_TYPE" ] && exit 0

SID="${CLAUDE_SESSION_ID:-pid-$PPID}"
TS=$(date +%s.%N)
STORE="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}/stores/session-telemetry.jsonl"
[ -z "$STORE" ] && exit 0

mkdir -p "$(dirname "$STORE")" 2>/dev/null

ARGS=(--arg event_type "$EVENT_TYPE" --arg session_id "$SID" --arg ts "$TS")
FIELDS='{event_type:$event_type,session_id:$session_id,ts:($ts|tonumber)'

for kv in "$@"; do
  key="${kv%%=*}"
  val="${kv#*=}"
  [ -z "$key" ] && continue
  ARGS+=(--arg "$key" "$val")
  FIELDS+=",$key:\$$key"
done
FIELDS+='}'

jq -nc "${ARGS[@]}" "$FIELDS" >> "$STORE" 2>/dev/null || true
