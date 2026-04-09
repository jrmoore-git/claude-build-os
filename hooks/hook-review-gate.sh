#!/bin/bash
# PreToolUse hook: Block/warn if high-risk files staged without valid debate artifacts.
#
# Accepts:
#   1. [TRIVIAL] in commit message — bypass for typo/doc-only commits (logged)
#   2. tasks/*-challenge.md with YAML frontmatter + MATERIAL tag + verdict line
#   3. tasks/*-resolution.md with ## PM/UX Assessment section
#   4. tasks/*-review.md (legacy compat) newer than staged files
#
# Warns: skills/, *_tool.py, .claude/rules/, hook scripts, security files.

INPUT=$(cat)
PROJECT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
COMMAND=$(printf '%s' "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

case "$COMMAND" in
  git\ commit*)
    # --- Check [TRIVIAL] bypass ---
    if printf '%s' "$COMMAND" | grep -q '\[TRIVIAL\]'; then
      echo "NOTICE: [TRIVIAL] bypass — review gate skipped. Logged."
      exit 0
    fi

    STAGED=$(cd "$PROJECT" && git diff --cached --name-only 2>/dev/null)
    [ -z "$STAGED" ] && exit 0

    # --- Classify staged files via tier_classify.py ---
    RISK_LEVEL=$(echo "$STAGED" | python3 -c "
import sys, json, subprocess

stdin_text = sys.stdin.read()
result = subprocess.run(
    [sys.executable, 'scripts/tier_classify.py', '--stdin'],
    input=stdin_text, capture_output=True, text=True,
    cwd='$PROJECT'
)
try:
    d = json.loads(result.stdout)
except (json.JSONDecodeError, ValueError):
    print('ok')
    sys.exit(0)
t = d.get('tier', 2)
if t == 1:
    print('tier1')
elif t == 1.5:
    print('warn')
elif t == 'exempt':
    print('ok')
else:
    files = d.get('files', {})
    warn = any('skill' in f or '_tool.py' in f or '.claude/rules/' in f
               or 'hook-' in f or 'security' in f for f in files)
    print('warn' if warn else 'ok')
" 2>/dev/null)

    [ "$RISK_LEVEL" = "ok" ] && exit 0

    # --- Find newest staged file mtime ---
    NEWEST_STAGED=$(python3 -c "
import os, subprocess, sys
result = subprocess.run(
    ['git', '-C', '$PROJECT', 'diff', '--cached', '--name-only'],
    capture_output=True, text=True
)
newest = 0
for rel in result.stdout.splitlines():
    rel = rel.strip()
    if not rel:
        continue
    full = os.path.join('$PROJECT', rel)
    try:
        newest = max(newest, os.path.getmtime(full))
    except OSError:
        pass
print(newest)
" 2>/dev/null)

    # --- Check for valid debate artifacts ---
    TASKS="$PROJECT/tasks"
    ARTIFACT_VALID=$(python3 -c "
import os, re, sys

tasks = '$TASKS'
newest_staged = float('$NEWEST_STAGED')
found_valid = False

if not os.path.isdir(tasks):
    print('no')
    sys.exit(0)

for f in sorted(os.listdir(tasks)):
    path = os.path.join(tasks, f)
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        continue
    if mtime <= newest_staged:
        continue

    if f.endswith('-challenge.md'):
        try:
            content = open(path).read()
        except OSError:
            continue
        has_frontmatter = bool(re.match(r'^---\n.*?debate_id:', content, re.DOTALL))
        has_material = bool(re.search(r'MATERIAL', content))
        has_verdict = bool(re.search(r'\b(APPROVE|REVISE|REJECT)\b', content))
        if has_frontmatter and has_material and has_verdict:
            found_valid = True
            break

    if f.endswith('-resolution.md'):
        try:
            content = open(path).read()
        except OSError:
            continue
        if '## PM/UX Assessment' in content:
            found_valid = True
            break

    if f.endswith('-review.md'):
        found_valid = True
        break

print('yes' if found_valid else 'no')
" 2>/dev/null)

    if [ "$ARTIFACT_VALID" = "yes" ]; then
      exit 0
    fi

    # --- No valid artifacts found ---
    if [ "$RISK_LEVEL" = "tier1" ]; then
      printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"block","permissionDecisionReason":"BLOCKED: Tier 1 files staged without debate artifacts. Run cross-model debate before committing."}}\n'
      exit 2
    fi

    # Advisory for Tier 2 files
    echo "NOTICE: High-risk files staged without debate artifacts. Log decision in tasks/decisions.md."
    ;;
esac

exit 0
