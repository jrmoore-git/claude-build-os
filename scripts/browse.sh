#!/usr/bin/env bash
# Thin wrapper around gstack's headless browser binary.
# Used by /design review, /design consult, /design variants.
#
# Usage: bash scripts/browse.sh <command> [args...]
# Examples:
#   bash scripts/browse.sh goto "http://localhost:3000"
#   bash scripts/browse.sh screenshot /tmp/screenshot.png
#   bash scripts/browse.sh snapshot -i -a

set -euo pipefail

# Locate the browse binary: env var > default gstack install path
BROWSE_BIN="${BROWSE_CLI:-$HOME/.claude/skills/gstack/browse/dist/browse}"

if [ ! -x "$BROWSE_BIN" ]; then
  echo "ERROR: browse binary not found at $BROWSE_BIN" >&2
  echo "Install gstack or set BROWSE_CLI to the browse binary path." >&2
  echo "Run: bash scripts/setup-design-tools.sh" >&2
  exit 1
fi

exec "$BROWSE_BIN" "$@"
