#!/bin/bash
# hook-class: enforcement-high
# PreToolUse hook: Block commits to protected paths without a valid plan artifact.
#
# Protected paths defined in config/protected-paths.json.
# Exempt paths (tasks/, docs/, tests/, config/, stores/) always pass.
#
# Accepts:
#   1. [EMERGENCY] in commit message — bypass with stderr warning (logged)
#   2. tasks/*-plan.md with complete YAML frontmatter (all required_plan_fields)
#      AND verification_evidence != "PENDING"
#
# Rejects:
#   1. [TRIVIAL] on protected paths — Claude misclassifies complexity
#   2. Missing or incomplete plan artifacts
#   3. Plan with verification_evidence: PENDING
#
# Missing config = fail-open (exit 0).

INPUT=$(cat)

# Tier gate: requires tier >= 2
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
/opt/homebrew/bin/python3.11 "$PROJECT_ROOT/scripts/read_tier.py" --check 2 2>/dev/null || exit 0

COMMAND=$(printf '%s' "$INPUT" | /opt/homebrew/bin/python3.11 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

case "$COMMAND" in
  git\ commit*)
    PROJECT="$(git rev-parse --show-toplevel)"
    CONFIG="$PROJECT/config/protected-paths.json"
    TASKS="$PROJECT/tasks"

    # Fail-open if config missing
    [ ! -f "$CONFIG" ] && exit 0

    STAGED=$(cd "$PROJECT" && git diff --cached --name-only 2>/dev/null)
    [ -z "$STAGED" ] && exit 0

    # Check if any staged files match protected globs (minus exempt patterns)
    PROTECTED_HIT=$(PLAN_GATE_CONFIG="$CONFIG" PLAN_GATE_STAGED="$STAGED" /opt/homebrew/bin/python3.11 <<'PYEOF'
import json, os, re, sys

config_path = os.environ["PLAN_GATE_CONFIG"]
try:
    with open(config_path) as f:
        config = json.load(f)
except (OSError, json.JSONDecodeError):
    sys.exit(0)

protected_globs = config.get("protected_globs", [])
exempt_patterns = config.get("exempt_patterns", [])

def glob_to_regex(pattern):
    parts = pattern.split("**")
    converted = []
    for part in parts:
        segment = ""
        for ch in part:
            if ch == "*":
                segment += "[^/]*"
            elif ch == "?":
                segment += "[^/]"
            elif ch in r"\.+^${}()|[]":
                segment += "\\" + ch
            else:
                segment += ch
        converted.append(segment)
    return "^" + ".*".join(converted) + "$"

def matches_any(path, patterns):
    for pat in patterns:
        regex = glob_to_regex(pat)
        if re.match(regex, path):
            return True
    return False

staged = os.environ.get("PLAN_GATE_STAGED", "").strip().splitlines()
for path in staged:
    path = path.strip()
    if not path:
        continue
    if matches_any(path, exempt_patterns):
        continue
    if matches_any(path, protected_globs):
        print("yes")
        sys.exit(0)

print("no")
PYEOF
    )

    [ "$PROTECTED_HIT" != "yes" ] && exit 0

    # --- Protected files staged. Check for [TRIVIAL] (BLOCKED on protected paths) ---
    if printf '%s' "$COMMAND" | grep -q '\[TRIVIAL\]'; then
      "$PROJECT/scripts/telemetry.sh" hook_fire hook_name=plan-gate tool_name=Bash decision=block reason=trivial-on-protected
      printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"block","permissionDecisionReason":"BLOCKED: [TRIVIAL] bypass not allowed for protected paths (skills, tools, rules). Write a plan to tasks/<topic>-plan.md first. See config/protected-paths.json for protected paths."}}\n'
      exit 2
    fi

    # --- Check for [EMERGENCY] bypass ---
    if printf '%s' "$COMMAND" | grep -q '\[EMERGENCY\]'; then
      "$PROJECT/scripts/telemetry.sh" hook_fire hook_name=plan-gate tool_name=Bash decision=warn reason=emergency-bypass
      echo "WARNING: [EMERGENCY] bypass — plan gate skipped for protected paths. This will be audited in weekly review." >&2
      exit 0
    fi

    # --- Check for valid plan artifact ---
    PLAN_VALID=$(PLAN_GATE_CONFIG="$CONFIG" PLAN_GATE_TASKS="$TASKS" /opt/homebrew/bin/python3.11 <<'PYEOF'
import json, os, re, sys

config_path = os.environ["PLAN_GATE_CONFIG"]
tasks_dir = os.environ["PLAN_GATE_TASKS"]

try:
    with open(config_path) as f:
        config = json.load(f)
except (OSError, json.JSONDecodeError):
    print("yes")  # fail-open
    sys.exit(0)

required_fields = config.get("required_plan_fields", [])

for f in sorted(os.listdir(tasks_dir)):
    if not f.endswith("-plan.md"):
        continue
    path = os.path.join(tasks_dir, f)
    try:
        content = open(path).read()
    except OSError:
        continue

    # Must have YAML frontmatter
    if not content.startswith("---"):
        continue
    fm_end = content.find("---", 3)
    if fm_end < 0:
        continue
    frontmatter = content[3:fm_end]

    # Check all required fields present
    all_present = True
    for field in required_fields:
        if not re.search(r"^" + re.escape(field) + r"\s*:", frontmatter, re.MULTILINE):
            all_present = False
            break
    if not all_present:
        continue

    # Check verification_evidence is not PENDING
    ve_match = re.search(r"^verification_evidence\s*:\s*(.+)", frontmatter, re.MULTILINE)
    if ve_match:
        val = ve_match.group(1).strip().strip('"').strip("'")
        if val.upper() == "PENDING":
            continue

    print("yes")
    sys.exit(0)

print("no")
PYEOF
    )

    if [ "$PLAN_VALID" = "yes" ]; then
      "$PROJECT/scripts/telemetry.sh" hook_fire hook_name=plan-gate tool_name=Bash decision=allow reason=plan-valid
      exit 0
    fi

    # --- No valid plan found ---
    "$PROJECT/scripts/telemetry.sh" hook_fire hook_name=plan-gate tool_name=Bash decision=block reason=no-plan
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"block","permissionDecisionReason":"BLOCKED: Protected files staged without a valid plan artifact. Create tasks/<topic>-plan.md with YAML frontmatter containing: scope, surfaces_affected, verification_commands, rollback, review_tier. verification_evidence must not be PENDING. See config/protected-paths.json."}}\n'
    exit 2
    ;;
esac

exit 0
