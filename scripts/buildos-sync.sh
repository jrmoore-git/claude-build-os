#!/usr/bin/env bash
set -euo pipefail

# buildos-sync.sh — Sync framework files between downstream project and BuildOS upstream
#
# When run from a downstream project: compares framework files against BuildOS upstream.
# When run from BuildOS itself: auto-passes (nothing to sync against).
#
# Usage:
#   ./scripts/buildos-sync.sh              # dry-run (default)
#   ./scripts/buildos-sync.sh --dry-run    # explicit dry-run
#   ./scripts/buildos-sync.sh --commit     # copy + commit
#   ./scripts/buildos-sync.sh --push       # copy + commit + push

# --- Mode parsing ---
MODE="${1:---dry-run}"
case "$MODE" in
  --dry-run|--commit|--push) ;;
  *) echo "Usage: $0 [--dry-run|--commit|--push]"; exit 1 ;;
esac

# --- Repo detection ---
SOURCE_DIR="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
TARGET_DIR="${BUILDOS_DIR:-$HOME/claude-build-os}"

# If we ARE the BuildOS repo, auto-pass
SOURCE_REMOTE=$(git -C "$SOURCE_DIR" remote get-url origin 2>/dev/null || echo "")
if [[ "$SOURCE_REMOTE" == *"claude-build-os"* ]]; then
  echo "Summary: 0 changed, 0 new, 0 missing from source, 0 unchanged, 0 expected divergences"
  echo ""
  echo "Running from BuildOS itself — nothing to sync."
  exit 0
fi

echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"
echo "Mode:   $MODE"
echo ""

if [[ ! -d "$SOURCE_DIR/.git" ]]; then
  echo "ERROR: Source is not a git repo: $SOURCE_DIR"
  exit 1
fi

if [[ ! -d "$TARGET_DIR/.git" ]]; then
  echo "ERROR: Target repo not found: $TARGET_DIR"
  echo "Set BUILDOS_DIR env var or clone claude-build-os to $HOME/claude-build-os"
  exit 1
fi

# Verify target is the expected repo
TARGET_REMOTE=$(git -C "$TARGET_DIR" remote get-url origin 2>/dev/null || echo "")
if [[ -z "$TARGET_REMOTE" ]] || [[ "$TARGET_REMOTE" != *"claude-build-os"* ]]; then
  echo "ERROR: Target repo origin does not look like claude-build-os"
  echo "  Remote: ${TARGET_REMOTE:-<none>}"
  echo "  Expected: a URL containing 'claude-build-os'"
  echo "Set BUILDOS_DIR to the correct repo path."
  exit 1
fi

# --- File manifest (framework layer only) ---
MANIFEST=(
  # Rules
  .claude/rules/code-quality.md
  .claude/rules/design.md
  .claude/rules/orchestration.md
  .claude/rules/review-protocol.md
  .claude/rules/security.md
  .claude/rules/session-discipline.md
  .claude/rules/skill-authoring.md
  .claude/rules/workflow.md
  .claude/rules/bash-failures.md

  # Config
  config/debate-models.json
  config/protected-paths.json
  config/buildos-expected-divergences.json

  # Skills
  .claude/skills/audit/SKILL.md
  .claude/skills/challenge/SKILL.md
  .claude/skills/design/SKILL.md
  .claude/skills/elevate/SKILL.md
  .claude/skills/explore/SKILL.md
  .claude/skills/log/SKILL.md
  .claude/skills/plan/SKILL.md
  .claude/skills/polish/SKILL.md
  .claude/skills/pressure-test/SKILL.md
  .claude/skills/research/SKILL.md
  .claude/skills/review/SKILL.md
  .claude/skills/setup/SKILL.md
  .claude/skills/ship/SKILL.md
  .claude/skills/start/SKILL.md
  .claude/skills/sync/SKILL.md
  .claude/skills/think/SKILL.md
  .claude/skills/triage/SKILL.md
  .claude/skills/wrap/SKILL.md

  # Scripts
  scripts/debate.py
  scripts/tier_classify.py
  scripts/recall_search.py
  scripts/finding_tracker.py
  scripts/enrich_context.py
  scripts/artifact_check.py
  scripts/check-current-state-freshness.py
  scripts/detect-uncommitted.py
  scripts/verify-plan-progress.py
  scripts/check-infra-versions.py
  scripts/buildos-sync.sh
  scripts/debate_tools.py
  scripts/llm_client.py
  scripts/deploy_all.sh
  scripts/deploy_skills.sh
  scripts/managed_agent.py
  scripts/research.py
  scripts/setup-design-tools.sh

  # Reference rules
  .claude/rules/reference/code-quality-detail.md
  .claude/rules/reference/operational-context.md
  .claude/rules/reference/debate-invocations.md
  .claude/rules/reference/platform.md

  # Hooks
  hooks/hook-agent-isolation.py
  hooks/hook-bash-fix-forward.py
  hooks/hook-decompose-gate.py
  hooks/hook-guard-env.sh
  hooks/hook-plan-gate.sh
  hooks/hook-post-tool-test.sh
  hooks/hook-prd-drift-check.sh
  hooks/hook-pre-commit-tests.sh
  hooks/hook-pre-edit-gate.sh
  hooks/hook-memory-size-gate.py
  hooks/hook-review-gate.sh
  hooks/hook-ruff-check.sh
  hooks/hook-stop-autocommit.py
  hooks/hook-syntax-check-python.sh
  hooks/hook-tier-gate.sh
)

# --- Banned terms (case-insensitive) ---
# Add project-specific terms here to prevent leaking into BuildOS upstream.
# Example: BANNED_PATTERN='MyApp|myapp|specific-customer|/Users/myuser'
BANNED_PATTERN=''

# --- Load expected divergences ---
DIVERGENCE_FILE="$SOURCE_DIR/config/buildos-expected-divergences.json"
expected_divergences=()
if [[ -f "$DIVERGENCE_FILE" ]]; then
  while IFS= read -r line; do
    file_path=$(echo "$line" | sed -n 's/.*"file": *"\([^"]*\)".*/\1/p')
    if [[ -n "$file_path" ]]; then
      expected_divergences+=("$file_path")
    fi
  done < "$DIVERGENCE_FILE"
fi

_is_expected_divergence() {
  local file="$1"
  for ed in "${expected_divergences[@]+"${expected_divergences[@]}"}"; do
    if [[ "$file" == "$ed" ]]; then
      return 0
    fi
  done
  return 1
}

# --- Diff files ---
changed=()
expected_changed=()
new_files=()
missing=()
unchanged=()

echo "=== File Diff ==="
echo ""

for file in "${MANIFEST[@]}"; do
  src="$SOURCE_DIR/$file"
  tgt="$TARGET_DIR/$file"

  if [[ ! -f "$src" ]]; then
    missing+=("$file")
    echo "  MISSING (source):  $file"
  elif [[ ! -f "$tgt" ]]; then
    new_files+=("$file")
    echo "  NEW:               $file"
  elif ! diff -q "$src" "$tgt" > /dev/null 2>&1; then
    if _is_expected_divergence "$file"; then
      expected_changed+=("$file")
      echo "  EXPECTED DIVERGE:  $file"
    else
      changed+=("$file")
      echo "  CHANGED:           $file"
    fi
  else
    unchanged+=("$file")
  fi
done

echo ""
# NOTE: /ship Gate 8 parses this exact format. Update SKILL.md if you change it.
echo "Summary: ${#changed[@]} changed, ${#new_files[@]} new, ${#missing[@]} missing from source, ${#unchanged[@]} unchanged, ${#expected_changed[@]} expected divergences"
echo ""

# --- Show diffs for changed files ---
if [[ ${#changed[@]} -gt 0 ]]; then
  echo "=== Diffs ==="
  echo ""
  for file in "${changed[@]}"; do
    echo "--- $file ---"
    diff -u "$TARGET_DIR/$file" "$SOURCE_DIR/$file" 2>/dev/null || true
    echo ""
  done
fi

# --- Banned-terms scan ---
if [[ -n "$BANNED_PATTERN" ]]; then
  echo "=== Banned-Terms Security Scan (source) ==="
  scan_failed=0
  scan_output=""

  for file in "${MANIFEST[@]}"; do
    src="$SOURCE_DIR/$file"
    if [[ -f "$src" ]]; then
      matches=$(grep -inE "$BANNED_PATTERN" "$src" 2>/dev/null || true)
      if [[ -n "$matches" ]]; then
        scan_failed=1
        scan_output+="  $file:"$'\n'
        while IFS= read -r line; do
          scan_output+="    $line"$'\n'
        done <<< "$matches"
      fi
    fi
  done

  if [[ "$scan_failed" -eq 1 ]]; then
    echo "FAILED — banned terms found in source files:"
    echo ""
    echo "$scan_output"
    echo "ABORT: Clean these files before syncing."
    exit 78
  fi
  echo "PASSED — no banned terms found."
  echo ""
fi

# --- Dry-run stops here ---
if [[ "$MODE" == "--dry-run" ]]; then
  echo "Dry run complete. Use --commit to copy and commit, --push to also push."
  exit 0
fi

# --- Copy files to target ---
to_copy=()
[[ ${#changed[@]} -gt 0 ]] && to_copy+=("${changed[@]}")
[[ ${#new_files[@]} -gt 0 ]] && to_copy+=("${new_files[@]}")

if [[ ${#to_copy[@]} -eq 0 ]]; then
  echo "Nothing to copy — target is up to date."
  exit 0
fi

echo "=== Copying ${#to_copy[@]} files to target ==="
for file in "${to_copy[@]}"; do
  src="$SOURCE_DIR/$file"
  tgt="$TARGET_DIR/$file"
  tgt_dir="$(dirname "$tgt")"
  mkdir -p "$tgt_dir"
  cp "$src" "$tgt"
  echo "  Copied: $file"
done
echo ""

# --- Commit ---
echo "=== Committing to target repo ==="
cd "$TARGET_DIR"
for file in "${to_copy[@]}"; do
  git add "$file"
done
git commit -m "Sync framework files from downstream project"
echo ""
echo "Committed ${#to_copy[@]} files."

# --- Push ---
if [[ "$MODE" == "--push" ]]; then
  echo ""
  echo "=== Pushing to origin/main ==="
  git push origin main
  echo "Pushed."
fi

echo ""
echo "Done."
