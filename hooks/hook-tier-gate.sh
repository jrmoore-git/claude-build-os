#!/bin/bash
# hook-class: enforcement-high
# PreToolUse hook: Classify task tier BEFORE first file edit.
# Fires on: Write|Edit
#
# Tier 1 (debate required): PRD, database schema, trust boundary code, security rules
# Tier 1.5 (quality review): core skills, toolbelt scripts
# Tier 2 (log only): everything else
#
# Behavior:
#   - On first Tier 1 file edit in a session, BLOCKS unless debate artifacts exist
#   - On first Tier 1.5 file edit, WARNS (advisory, not blocking)
#   - Tracks "already classified" via a session marker file to avoid re-firing every edit
#   - [TRIVIAL] files (CLAUDE.md comments, typo fixes) are never Tier 1

INPUT=$(cat)

# Tier gate: requires tier >= 2
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
/opt/homebrew/bin/python3.11 "$PROJECT_ROOT/scripts/read_tier.py" --check 2 2>/dev/null || exit 0

RESULT=$(PLAN_GATE_PROJECT="$PROJECT_ROOT" /opt/homebrew/bin/python3.11 -c "
import sys, json, os, re, subprocess, time

PROJECT = os.environ.get('PLAN_GATE_PROJECT', '.')
TASKS = os.path.join(PROJECT, 'tasks')
MARKER_DIR = '/tmp/tier-gate'
os.makedirs(MARKER_DIR, exist_ok=True)

try:
    d = json.load(sys.stdin)
except json.JSONDecodeError:
    print('ALLOW')
    sys.exit(0)

ti = d.get('tool_input', {})
file_path = ti.get('file_path', '')

if not file_path:
    print('ALLOW')
    sys.exit(0)

# Normalize to relative path
rel = file_path
if rel.startswith(PROJECT + '/'):
    rel = rel[len(PROJECT) + 1:]

# ── Tier classification via tier_classify.py ──────────────────────────────
try:
    result = subprocess.run(
        ['/opt/homebrew/bin/python3.11', os.path.join(PROJECT, 'scripts/tier_classify.py'), rel],
        capture_output=True, text=True, timeout=5
    )
    tier_data = json.loads(result.stdout)
    raw_tier = tier_data.get('tier', 2)
except Exception:
    raw_tier = 2

if raw_tier == 'exempt' or raw_tier == 2:
    print('ALLOW')
    sys.exit(0)

tier = 15 if raw_tier == 1.5 else int(raw_tier)

# ── Session dedup — don't fire on every single edit ──────────────────────
# Use a marker keyed on tier level. If we already passed this tier's gate
# in this session, allow. Marker expires after 4 hours.
marker_file = os.path.join(MARKER_DIR, f'tier{tier}_passed')
if os.path.exists(marker_file):
    age = time.time() - os.path.getmtime(marker_file)
    if age < 14400:  # 4 hours
        print('ALLOW')
        sys.exit(0)

# ── Check for valid debate artifacts (Tier 1 only) ───────────────────────
if tier == 1:
    # Session start marker: created on first Tier 1 check, used as baseline
    session_marker = os.path.join(MARKER_DIR, 'session_start')
    if not os.path.exists(session_marker):
        with open(session_marker, 'w') as sm:
            sm.write(str(time.time()))
        session_start = time.time()
    else:
        session_start = os.path.getmtime(session_marker)

    # Require an artifact created AFTER this session started
    # (old debates for different topics don't count)
    found_artifact = False
    for f in os.listdir(TASKS):
        path = os.path.join(TASKS, f)
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue
        if mtime < session_start:
            continue  # pre-session artifact — doesn't count

        if f.endswith('-challenge.md'):
            try:
                content = open(path).read()
            except OSError:
                continue
            has_frontmatter = bool(re.match(r'^---\n.*?debate_id:', content, re.DOTALL))
            has_material = bool(re.search(r'MATERIAL', content))
            if has_frontmatter and has_material:
                found_artifact = True
                break

        if f.endswith('-judgment.md') or f.endswith('-resolution.md'):
            found_artifact = True
            break

    if found_artifact:
        # Artifact exists for this session — mark as passed and allow
        with open(marker_file, 'w') as mf:
            mf.write(f'artifact_found:{rel}')
        print('ALLOW')
        sys.exit(0)

    # No artifact — BLOCK
    print(f'BLOCK_TIER1:{rel}')
    sys.exit(0)

# ── Tier 1.5: advisory warning ───────────────────────────────────────────
if tier == 15:
    with open(marker_file, 'w') as mf:
        mf.write(f'warned:{rel}')
    print(f'WARN_TIER15:{rel}')
    sys.exit(0)

print('ALLOW')
" <<< "$INPUT" 2>/dev/null)

case "$RESULT" in
  BLOCK_TIER1:*)
    FILE="${RESULT#BLOCK_TIER1:}"
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"block","permissionDecisionReason":"BLOCKED: %s is a Tier 1 file (PRD/schema/trust boundary). Cross-model debate required BEFORE editing. Write a proposal to tasks/<topic>-proposal.md, then run: python3.11 scripts/debate.py challenge --proposal tasks/<topic>-proposal.md --models gpt-5.4,gemini-3.1-pro --output tasks/<topic>-challenge.md. See .claude/rules/review-protocol.md."}}\n' "$FILE"
    exit 2
    ;;
  WARN_TIER15:*)
    FILE="${RESULT#WARN_TIER15:}"
    echo "NOTICE: $FILE is Tier 1.5 (core skill/toolbelt). Consider running a quality review (1 round, 1 challenger). Proceeding — this is advisory."
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
