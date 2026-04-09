#!/usr/bin/env bash
# pre-commit-banned-terms.sh — Block commits containing project-specific terms
# Install: ln -sf ../../hooks/pre-commit-banned-terms.sh .git/hooks/pre-commit
#
# Scans all staged files for leaked project-specific terms.
# Hard block — commit is rejected if any match found.

set -uo pipefail

# Same banned pattern as buildos-sync.sh in the downstream project.
# Keep in sync — if you add terms there, add them here.
BANNED_PATTERN='Justin|Jarvis|jarvis|openclaw|OpenClaw|innovius|Innovius|cloudzero|CloudZero|/Users/macmini|@innovius|@cloudzero|TELEGRAM_BOT_TOKEN|JUSTIN_TELEGRAM|8387329260|6507037822|6503803830|9256395873|sk-ant-|xoxb-|xapp-|GOG_KEYRING|AFFINITY_API|innoviuscapital|nicole_filter|Nicole|Meaghan|Granola|WebChat'

# Files/patterns to skip (these legitimately mention banned terms)
SKIP_PATTERNS=(
  "hooks/pre-commit-banned-terms.sh"   # this file
  ".github/workflows/*"                # CI workflow (contains the pattern)
  ".env.example"                       # contains example API key placeholders
  "*.sample"
  ".git/*"
)

_should_skip() {
  local file="$1"
  for pattern in "${SKIP_PATTERNS[@]}"; do
    case "$file" in
      $pattern) return 0 ;;
    esac
  done
  return 1
}

# Get staged files (excludes deleted files)
STAGED_FILES="$(git diff --cached --name-only --diff-filter=d 2>/dev/null)"

if [[ -z "$STAGED_FILES" ]]; then
  exit 0
fi

FAILED=0
OUTPUT=""

while IFS= read -r file; do
  _should_skip "$file" && continue

  # Only scan text files
  if file --brief "$file" 2>/dev/null | grep -q "text"; then
    MATCHES="$(grep -inE "$BANNED_PATTERN" "$file" 2>/dev/null || true)"
    if [[ -n "$MATCHES" ]]; then
      FAILED=1
      OUTPUT+="  $file:"$'\n'
      while IFS= read -r line; do
        OUTPUT+="    $line"$'\n'
      done <<< "$MATCHES"
    fi
  fi
done <<< "$STAGED_FILES"

if [[ "$FAILED" -eq 1 ]]; then
  echo "BLOCKED — project-specific terms found in staged files:"
  echo ""
  echo "$OUTPUT"
  echo "This repo must stay generic. Remove these references before committing."
  echo "If this is a false positive, add the file to SKIP_PATTERNS in this hook."
  exit 1
fi

exit 0
