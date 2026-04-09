#!/bin/bash
# PreToolUse hook: Block when >=5 decisions are unsynced to PRD.
# Also warns when decisions.md staged without PRD, and blocks new PRD without symlink update.
#
# Count-based trigger: counts "### D" entries in tasks/decisions.md added AFTER
# the PRD's last git commit. Blocks at >=5, warns at >=3.
#
# Configure PRD_FILE to match your project's PRD filename.

INPUT=$(cat)
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"

# --- CONFIGURE THESE FOR YOUR PROJECT ---
PRD_FILE="docs/PRD.md"  # Path to your PRD file (relative to project root)
# -----------------------------------------

COMMAND=$(printf '%s' "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

case "$COMMAND" in
  git\ commit*)
    STAGED=$(cd "$PROJECT_ROOT" && git diff --cached --name-only 2>/dev/null)

    # --- Count-based drift check ---
    # Find the PRD's last commit date, count decisions added after it
    DRIFT_COUNT=$(python3 -c "
import subprocess, re, sys

project_root = '$PROJECT_ROOT'
prd_file = '$PRD_FILE'

# Last commit date for the PRD file
result = subprocess.run(
    ['git', '-C', project_root, 'log', '-1', '--format=%aI', '--', prd_file],
    capture_output=True, text=True
)
prd_date_str = result.stdout.strip()
if not prd_date_str:
    print('0')  # PRD never committed — skip check
    sys.exit(0)

# Parse PRD date (just the date part)
prd_date = prd_date_str[:10]  # YYYY-MM-DD

# Count decision entries with dates AFTER the PRD's last commit date
decisions_path = project_root + '/tasks/decisions.md'
try:
    content = open(decisions_path).read()
except FileNotFoundError:
    print('0')
    sys.exit(0)

# Find all decision headers and their dates
entries = re.findall(r'### D\d+:.*?\n\*\*Date:\*\* (\d{4}-\d{2}-\d{2})', content)
unsynced = sum(1 for d in entries if d > prd_date)
print(unsynced)
" 2>/dev/null)

    if [ -n "$DRIFT_COUNT" ] && [ "$DRIFT_COUNT" -ge 5 ]; then
      echo "BLOCKED: $DRIFT_COUNT decisions in tasks/decisions.md are newer than the PRD's last commit."
      echo "Run a PRD sync pass before committing. Check D entries dated after the PRD's last update."
      echo "Use [TRIVIAL] in commit message to bypass for doc-only changes."
      # Allow [TRIVIAL] bypass
      if printf '%s' "$COMMAND" | grep -q '\[TRIVIAL\]'; then
        echo "NOTICE: [TRIVIAL] bypass — PRD drift check skipped."
      else
        exit 2
      fi
    elif [ -n "$DRIFT_COUNT" ] && [ "$DRIFT_COUNT" -ge 3 ]; then
      echo "WARNING: $DRIFT_COUNT decisions are newer than the PRD. Consider a PRD sync pass soon."
    fi

    # --- Warn if decisions staged without PRD ---
    DECISIONS_STAGED=$(printf '%s' "$STAGED" | grep -c '^tasks/decisions\.md$')
    PRD_STAGED=$(printf '%s' "$STAGED" | grep -c "$(basename "$PRD_FILE")$")
    if [ "$DECISIONS_STAGED" -gt 0 ] && [ "$PRD_STAGED" -eq 0 ]; then
      echo "WARNING: tasks/decisions.md staged but no PRD file staged. Sync if decision affects the spec."
    fi

    # --- Block new PRD without symlink update ---
    NEW_PRD=$(printf '%s' "$STAGED" | grep "^docs/.*PRD.*\.md" | tail -1)
    if [ -n "$NEW_PRD" ]; then
      CURRENT_TARGET=$(readlink "$PROJECT_ROOT/docs/project-prd.md" 2>/dev/null | xargs basename 2>/dev/null)
      NEW_PRD_BASE=$(basename "$NEW_PRD")
      if [ "$CURRENT_TARGET" != "$NEW_PRD_BASE" ]; then
        echo "ERROR: New PRD staged ($NEW_PRD_BASE) but docs/project-prd.md still points to $CURRENT_TARGET"
        echo "Fix: cd $PROJECT_ROOT/docs && ln -sf $NEW_PRD_BASE project-prd.md && git add docs/project-prd.md"
        exit 1
      fi
    fi
    ;;
esac

exit 0
