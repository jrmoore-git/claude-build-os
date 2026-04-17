#!/usr/bin/env python3.11
# hook-class: advisory
"""
hook-decompose-gate.py — PreToolUse hook that nudges toward worktree
fan-out when a plan artifact declares ≥2 independent components.

Advisory, not blocking. Emits a prompt hint via `additionalContext`;
does not deny. The agent receives the nudge and decides.

Signal: the newest `tasks/*-plan.md` modified within the last 24h whose
frontmatter declares a `components:` list with ≥2 entries. Fires once
per session on main-session Write|Edit; worktree agents are silent.

Legacy flags still honored for backward compatibility:
  - {"bypass": true, "reason": "..."} → suppress the nudge
  - {"plan_submitted": true}           → nudge once if main session writes

Flag file: /tmp/claude-decompose-{session_id}.json
Session ID: $CLAUDE_SESSION_ID env var, fallback to parent PID.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Tier gate: requires tier >= 2
_project = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True
).stdout.strip()
_tier_result = subprocess.run(
    ["/opt/homebrew/bin/python3.11", os.path.join(_project, "scripts/read_tier.py"), "--check", "2"],
    capture_output=True
)
if _tier_result.returncode != 0:
    sys.exit(0)

sys.path.insert(0, os.path.join(_project, "scripts"))
try:
    from telemetry import log_event  # type: ignore
except Exception:
    def log_event(*args, **kwargs):
        return

REPO_ROOT = os.environ.get(
    "PROJECT_ROOT",
    str(Path(__file__).resolve().parent.parent),
)

PLAN_RECENCY_HOURS = 24


def get_session_id():
    sid = os.environ.get("CLAUDE_SESSION_ID", "")
    if sid:
        return sid
    return str(os.getppid())


def get_flag_path(session_id):
    return Path(f"/tmp/claude-decompose-{session_id}.json")


def is_worktree_agent():
    """Detect if running inside a git worktree (not the main repo)."""
    ctx = os.environ.get("ORCHESTRATION_CONTEXT", "")
    if ctx.startswith("worktree"):
        return True
    if ctx == "main":
        return False

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=2,
        )
        if result.returncode == 0:
            toplevel = result.stdout.strip()
            return toplevel != REPO_ROOT
    except (subprocess.TimeoutExpired, OSError):
        pass

    return False


def _extract_components(plan_path):
    """Parse frontmatter for a `components:` list. Stdlib only (no PyYAML)."""
    try:
        text = plan_path.read_text()
    except OSError:
        return []
    if not text.startswith("---\n"):
        return []
    end = text.find("\n---\n", 4)
    if end == -1:
        return []
    frontmatter = text[4:end]

    lines = frontmatter.splitlines()
    items = []
    in_field = False
    for line in lines:
        # Inline array form: components: [a, b, c]
        inline = re.match(r"^components\s*:\s*\[(.*)\]\s*$", line)
        if inline:
            inner = inline.group(1).strip()
            if not inner:
                return []
            return [x.strip().strip('"\'') for x in inner.split(",") if x.strip()]
        # Block list form: components: \n  - a\n  - b
        if re.match(r"^components\s*:\s*$", line):
            in_field = True
            continue
        if in_field:
            if line.startswith("  - "):
                items.append(line[4:].strip().strip('"\''))
            elif line.strip() == "":
                continue
            elif not line.startswith(" "):
                break
    return items


def find_recent_plan_with_components(repo_root):
    """Return (path, components) for newest recent plan with ≥2 components, else None."""
    plans_dir = Path(repo_root) / "tasks"
    if not plans_dir.exists():
        return None
    cutoff = _now_timestamp() - PLAN_RECENCY_HOURS * 3600
    candidates = []
    for plan in plans_dir.glob("*-plan.md"):
        try:
            st = plan.stat()
        except OSError:
            continue
        if st.st_mtime < cutoff:
            continue
        candidates.append((st.st_mtime, plan))
    candidates.sort(reverse=True)
    for _, plan in candidates:
        components = _extract_components(plan)
        if len(components) >= 2:
            return plan, components
    return None


def _now_timestamp():
    """Hook-injection seam for testing."""
    import time
    return time.time()


NUDGE_MESSAGES = {
    "plan_declared": (
        "Decomposition nudge: a parallel plan was declared this session (plan_submitted), "
        "but this Write|Edit is happening in the main session instead of a worktree agent. "
        "If fan-out is still the intent, dispatch the agents; if the plan changed, clear "
        "the flag and proceed."
    ),
}


def _components_nudge(plan_path, components, repo_root):
    preview = ", ".join(components[:3])
    if len(components) > 3:
        preview += f", +{len(components) - 3} more"
    try:
        rel = plan_path.relative_to(repo_root)
    except ValueError:
        rel = plan_path.name
    return (
        f"Decomposition nudge: plan at {rel} declares {len(components)} components "
        f"({preview}). If they're independent, consider dispatching worktree agents "
        f"for parallel execution. If they share state, proceed — the plan's "
        f"Execution Strategy section should explain why sequential."
    )


def _allow_with_context(message):
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "additionalContext": message,
        }
    }


def main():
    try:
        raw = sys.stdin.read()
    except Exception:
        print("{}")
        return

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        print("{}")
        return

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        print("{}")
        return

    if is_worktree_agent():
        print("{}")
        return

    session_id = get_session_id()
    flag_path = get_flag_path(session_id)

    # Legacy bypass / plan_submitted flag handling
    if flag_path.exists():
        try:
            flag_data = json.loads(flag_path.read_text())
        except (json.JSONDecodeError, OSError):
            flag_data = None

        if isinstance(flag_data, dict):
            if flag_data.get("bypass"):
                print("{}")
                return
            if flag_data.get("plan_submitted"):
                plan_nudge_marker = Path(f"/tmp/claude-decompose-{session_id}.plan-nudged")
                if plan_nudge_marker.exists():
                    print("{}")
                    return
                try:
                    plan_nudge_marker.touch()
                except OSError:
                    pass
                log_event("hook_fire", hook_name="decompose-gate", tool_name=tool_name,
                          decision="warn", reason="plan-declared-nudge")
                print(json.dumps(_allow_with_context(NUDGE_MESSAGES["plan_declared"])))
                return

    # Plan-components trigger
    match = find_recent_plan_with_components(REPO_ROOT)
    if match is None:
        print("{}")
        return
    plan_path, components = match

    components_nudge_marker = Path(f"/tmp/claude-decompose-{session_id}.components-nudged")
    if components_nudge_marker.exists():
        print("{}")
        return
    try:
        components_nudge_marker.touch()
    except OSError:
        pass

    log_event("hook_fire", hook_name="decompose-gate", tool_name=tool_name,
              decision="warn", reason=f"components-nudge-n{len(components)}")
    print(json.dumps(_allow_with_context(_components_nudge(plan_path, components, REPO_ROOT))))


if __name__ == "__main__":
    main()
