#!/bin/bash
# PreToolUse hook: Block Edit/Write on protected paths without a recent plan artifact.
#
# Fires on: Write|Edit (BEFORE code is written)
#
# Protected paths are loaded from config/protected-paths.json:
#   - scripts/*_tool.py, scripts/*_pipeline.py
#   - skills/**/*.md, .claude/rules/*.md
#   - This script itself (self-check — hook must protect itself)
#
# Exempt paths (always pass):
#   - tasks/*, docs/*, tests/*, config/*, stores/*
#
# Artifact check:
#   - tasks/*-plan.md modified in last 24 hours -> ALLOW
#   - No recent artifact -> BLOCK
#
# No external dependencies beyond Python stdlib.

set -euo pipefail

INPUT=$(cat)
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"

# Extract file_path from tool input JSON
FILE_PATH=$(python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('file_path', ''))
except Exception:
    print('')
" <<< "$INPUT" 2>/dev/null)

# No file path -> allow
[ -z "$FILE_PATH" ] && exit 0

TASKS="$PROJECT_ROOT/tasks"

# Normalize to relative path
REL="$FILE_PATH"
if [[ "$REL" == "$PROJECT_ROOT/"* ]]; then
    REL="${REL#$PROJECT_ROOT/}"
fi

# -- Check exempt/protected status from config/protected-paths.json --
# Single source of truth — no hardcoded patterns.
# Self-check: this hook file is always protected regardless of config.
CONFIG="$PROJECT_ROOT/config/protected-paths.json"
HOOK_SELF="hooks/hook-pre-edit-gate.sh"

PROTECTED=$(PLAN_GATE_CONFIG="$CONFIG" PLAN_GATE_REL="$REL" PLAN_GATE_SELF="$HOOK_SELF" python3 <<'PYEOF'
import json, os, sys, fnmatch

config_path = os.environ["PLAN_GATE_CONFIG"]
rel = os.environ["PLAN_GATE_REL"]
hook_self = os.environ["PLAN_GATE_SELF"]

# Self-check: this hook is always protected
if rel == hook_self:
    print("yes")
    sys.exit(0)

try:
    with open(config_path) as f:
        config = json.load(f)
except (OSError, json.JSONDecodeError):
    # Config missing/broken — fail open (don't block all edits)
    print("no")
    sys.exit(0)

# Exempt paths — always pass
for pat in config.get("exempt_patterns", []):
    if fnmatch.fnmatch(rel, pat):
        print("no")
        sys.exit(0)

# Protected globs — block if matched
for pat in config.get("protected_globs", []):
    # fnmatch doesn't handle ** well; expand ** to match any depth
    if "**" in pat:
        base, rest = pat.split("**", 1)
        for depth in range(4):
            expanded = base + ("*/" * depth) + rest.lstrip("/")
            if fnmatch.fnmatch(rel, expanded):
                print("yes")
                sys.exit(0)
    elif fnmatch.fnmatch(rel, pat):
        print("yes")
        sys.exit(0)

print("no")
PYEOF
)

# Not protected -> allow
[ "$PROTECTED" != "yes" ] && exit 0

# -- Protected path hit. Check for matching plan artifact --
# Requirements:
#   1. Only *-plan.md files count (proposals lack structured scope metadata)
#   2. Deterministic frontmatter parser (stdlib only)
#   3. surfaces_affected must match target via exact path or fnmatch glob
#   4. Artifact must be modified within 24 hours AND match content
#   5. Fail closed: parse failure or missing surfaces_affected = no match
PLAN_MATCH=$(PLAN_GATE_TASKS="$TASKS" PLAN_GATE_REL="$REL" python3 <<'PYEOF'
import os, sys, fnmatch, re, time

tasks_dir = os.environ["PLAN_GATE_TASKS"]
rel = os.environ["PLAN_GATE_REL"]
now = time.time()
MAX_AGE = 86400  # 24 hours


def parse_frontmatter(text):
    """Parse YAML frontmatter into dict. Handles scalar values and YAML lists.
    Returns None on any parse failure (fail closed)."""
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end < 0:
        return None
    result = {}
    current_key = None
    for line in text[3:end].splitlines():
        # YAML list item under current key
        if line.startswith("  - ") and current_key is not None:
            if not isinstance(result[current_key], list):
                result[current_key] = []
            result[current_key].append(line[4:].strip().strip("'\""))
            continue
        # Key: value line
        m = re.match(r'^([a-z_]+)\s*:\s*(.*)', line)
        if m:
            current_key = m.group(1)
            val = m.group(2).strip().strip("'\"")
            result[current_key] = val if val else []
            continue
        # Anything else resets list accumulation
        if line.strip():
            current_key = None
    return result


def extract_surfaces(fm):
    """Extract surfaces_affected as a list of path strings. Returns [] on failure."""
    sa = fm.get("surfaces_affected")
    if not sa:
        return []
    if isinstance(sa, str):
        return [e.strip() for e in sa.split(",") if e.strip()]
    if isinstance(sa, list):
        return [str(e).strip() for e in sa if str(e).strip()]
    return []


if not os.path.isdir(tasks_dir):
    print("no")
    sys.exit(0)

for fname in sorted(os.listdir(tasks_dir)):
    if not fname.endswith("-plan.md"):
        continue
    path = os.path.join(tasks_dir, fname)
    if not os.path.isfile(path):
        continue

    # 24-hour modification window
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        continue
    if (now - mtime) > MAX_AGE:
        continue

    # Parse frontmatter (fail closed)
    try:
        content = open(path).read()
    except OSError:
        continue
    fm = parse_frontmatter(content)
    if fm is None:
        continue

    # Strict matching: exact path or fnmatch glob only
    for entry in extract_surfaces(fm):
        if entry == rel or fnmatch.fnmatch(rel, entry):
            print("yes")
            sys.exit(0)

print("no")
PYEOF
)

if [ "$PLAN_MATCH" = "yes" ]; then
    exit 0
fi

# -- No matching plan found -> BLOCK --
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"block","permissionDecisionReason":"BLOCKED: %s is a protected path. Write tasks/<topic>-plan.md with surfaces_affected listing this file before editing. Required frontmatter: scope, surfaces_affected, verification_commands, rollback, review_tier."}}\n' "$REL"
exit 2
