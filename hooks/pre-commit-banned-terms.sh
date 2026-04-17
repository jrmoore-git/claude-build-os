#!/usr/bin/env bash
# hook-class: enforcement-low
# pre-commit-banned-terms.sh — Block commits containing secrets or AI-slop vocabulary
# Install: ln -sf ../../hooks/pre-commit-banned-terms.sh .git/hooks/pre-commit
#
# Scans all staged files for (1) leaked API-key prefixes, (2) AI-slop words or
# phrases. Hard block — commit is rejected if any match found.

set -uo pipefail

# Secrets / API-key prefixes that must never be committed.
BANNED_PATTERN='sk-ant-|xoxb-|xapp-'

# AI-slop vocabulary (case-insensitive, word-boundary enforced via grep -inE).
# Evidence source: tasks/llm-slop-vocabulary-research.md
# Edit the word list in .claude/rules/code-quality.md to keep rule and hook in sync.
SLOP_PATTERN='\b(delve|cutting-edge|state-of-the-art|seamless|innovative|synergy|paradigm|holistic|empower|transformative)\b'

# AI-slop phrases (case-insensitive). Whitespace via POSIX [[:space:]]+ — \s is a
# GNU extension that silently matches literal 's' on strict POSIX ERE (BSD grep).
SLOP_PHRASES='(a[[:space:]]+testament[[:space:]]+to|at[[:space:]]+its[[:space:]]+core)'

# Files/patterns to skip (these legitimately mention banned terms)
SKIP_PATTERNS=(
  "hooks/pre-commit-banned-terms.sh"   # this file
  ".claude/rules/code-quality.md"      # documents the slop list
  ".github/workflows/*"                # CI workflow (contains the pattern)
  ".env.example"                       # contains example API key placeholders
  "*.sample"
  ".git/*"
  "tasks/*"                            # generated debate/review/research artifacts
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

SLOP_OUTPUT=""
SLOP_FAILED=0

while IFS= read -r file; do
  _should_skip "$file" && continue

  # Only scan text files
  if file --brief "$file" 2>/dev/null | grep -q "text"; then
    # Pattern 1: API-key prefixes (secrets)
    MATCHES="$(grep -inE "$BANNED_PATTERN" "$file" 2>/dev/null || true)"
    if [[ -n "$MATCHES" ]]; then
      FAILED=1
      OUTPUT+="  $file:"$'\n'
      while IFS= read -r line; do
        OUTPUT+="    $line"$'\n'
      done <<< "$MATCHES"
    fi

    # Pattern 2: AI-slop words
    SLOP_WORDS="$(grep -inE "$SLOP_PATTERN" "$file" 2>/dev/null || true)"
    if [[ -n "$SLOP_WORDS" ]]; then
      SLOP_FAILED=1
      SLOP_OUTPUT+="  $file (slop words):"$'\n'
      while IFS= read -r line; do
        SLOP_OUTPUT+="    $line"$'\n'
      done <<< "$SLOP_WORDS"
    fi

    # Pattern 3: AI-slop phrases
    SLOP_PHRASE_MATCHES="$(grep -inE "$SLOP_PHRASES" "$file" 2>/dev/null || true)"
    if [[ -n "$SLOP_PHRASE_MATCHES" ]]; then
      SLOP_FAILED=1
      SLOP_OUTPUT+="  $file (slop phrases):"$'\n'
      while IFS= read -r line; do
        SLOP_OUTPUT+="    $line"$'\n'
      done <<< "$SLOP_PHRASE_MATCHES"
    fi
  fi
done <<< "$STAGED_FILES"

if [[ "$FAILED" -eq 1 ]]; then
  echo "BLOCKED — project-specific terms / secrets found in staged files:"
  echo ""
  echo "$OUTPUT"
  echo "This repo must stay generic. Remove these references before committing."
  echo "If this is a false positive, add the file to SKIP_PATTERNS in this hook."
  exit 1
fi

if [[ "$SLOP_FAILED" -eq 1 ]]; then
  echo "BLOCKED — AI slop vocabulary found in staged files:"
  echo ""
  echo "$SLOP_OUTPUT"
  echo "Banned words/phrases per .claude/rules/code-quality.md."
  echo "Rewrite in plain direct language. Evidence source:"
  echo "tasks/llm-slop-vocabulary-research.md"
  exit 1
fi

exit 0
