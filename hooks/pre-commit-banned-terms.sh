#!/usr/bin/env bash
# pre-commit-banned-terms.sh — Block commits containing project-specific terms
# Install: ln -sf ../../hooks/pre-commit-banned-terms.sh .git/hooks/pre-commit
#
# Scans all staged files for leaked project-specific terms.
# Hard block — commit is rejected if any match found.

set -uo pipefail

# Add project-specific terms that must never appear in BuildOS upstream.
# Example: 'MyApp|myapp|specific-customer|/Users/myuser|sk-ant-|xoxb-'
# Keep empty if no downstream project terms need blocking.
BANNED_PATTERN='sk-ant-|xoxb-|xapp-'

# Files/patterns to skip (these legitimately mention banned terms)
SKIP_PATTERNS=(
  "hooks/pre-commit-banned-terms.sh"   # this file
  ".github/workflows/*"                # CI workflow (contains the pattern)
  ".env.example"                       # contains example API key placeholders
  "*.sample"
  ".git/*"
  "tasks/*"                            # generated debate/review artifacts
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
