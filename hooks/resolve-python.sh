#!/usr/bin/env bash
# resolve-python.sh — Find python3 (3.11+) and ruff on this system.
# Source this from any hook: source "$(dirname "$0")/resolve-python.sh"
#
# Exports:
#   PYTHON3  — absolute path to python3 (3.11+)
#   RUFF     — absolute path to ruff (or empty if not found)

# Source cached config from setup.sh if available
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$HOOK_DIR")"
if [[ -f "$PROJECT_ROOT/.buildos-config" ]]; then
  source "$PROJECT_ROOT/.buildos-config"
fi

if [[ -n "$BUILDOS_PYTHON3" ]]; then
  PYTHON3="$BUILDOS_PYTHON3"
elif [[ -z "$PYTHON3" ]]; then
  # Try candidates in order of preference
  for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" > /dev/null 2>&1; then
      # Verify version >= 3.11
      version=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
      major=${version%%.*}
      minor=${version#*.}
      if [[ "$major" -ge 3 ]] && [[ "$minor" -ge 11 ]]; then
        PYTHON3="$(command -v "$candidate")"
        break
      fi
    fi
  done

  if [[ -z "$PYTHON3" ]]; then
    echo "ERROR: Python 3.11+ not found. Run ./setup.sh or install Python 3.11+." >&2
    # Don't exit — let the calling hook decide how to handle this
    PYTHON3="python3"  # fallback, will fail with a clear error
  fi
fi

if [[ -z "$RUFF" ]]; then
  if [[ -n "$BUILDOS_RUFF" ]]; then
    RUFF="$BUILDOS_RUFF"
  elif command -v ruff > /dev/null 2>&1; then
    RUFF="$(command -v ruff)"
  else
    RUFF=""
  fi
fi

export PYTHON3 RUFF
