#!/usr/bin/env python3.11
# hook-class: advisory
"""Post-build review gate — counts Write|Edit calls within an active plan.

Flow (PostToolUse, generic event + JSON tool_name filter):
  - If tool_name not in {Write, Edit}: exit 0 silently.
  - If no active plan (no tasks/*-plan.md with implementation_status != shipped):
    emit telemetry reason=no-plan, exit 0.
  - Otherwise: increment edit_count in /tmp/claude-review-${SESSION_ID}.json.
  - If a matching tasks/<plan-topic>-review.md exists with mtime > plan mtime:
    set flag=clear, reset counter, emit reason=flag-clear (or already-reviewed).
  - If edit_count >= 10 and no review artifact: set flag=needs_review,
    emit reason=flag-set.
  - Re-fire: every 5 edits past threshold (15, 20, 25...) while flag still set,
    bump re_fire_count, emit reason=flag-re-fire.

State file schema:
  {
    "session_id": str,
    "plan_topic": str | null,
    "edit_count": int,
    "last_review_check_count": int,
    "flag": "clear" | "needs_review",
    "re_fire_count": int
  }

Always exits 0. Never blocks. Every external call wrapped in try/except.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# REPO_ROOT: location of this hook's parent repo, used for importing telemetry.
# PROJECT_ROOT: the working project root (may override via env for testing).
# They are usually the same but differ under pytest with a synthetic tmp_path.
_HOOK_REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = Path(os.environ.get("PROJECT_ROOT", str(_HOOK_REPO_ROOT)))
sys.path.insert(0, str(_HOOK_REPO_ROOT / "scripts"))

try:
    from telemetry import log_event  # type: ignore
except Exception:
    def log_event(*args, **kwargs):  # fallback no-op
        return

REVIEW_THRESHOLD = 10
RE_FIRE_STEP = 5


def _session_id() -> str:
    sid = os.environ.get("CLAUDE_SESSION_ID")
    return sid if sid else f"pid-{os.getppid()}"


def _state_path(sid: str) -> Path:
    return Path(f"/tmp/claude-review-{sid}.json")


def _default_state(sid: str) -> dict:
    return {
        "session_id": sid,
        "plan_topic": None,
        "edit_count": 0,
        "last_review_check_count": 0,
        "flag": "clear",
        "re_fire_count": 0,
    }


def _load_state(sid: str) -> dict:
    path = _state_path(sid)
    if not path.exists():
        return _default_state(sid)
    try:
        raw = path.read_text()
        data = json.loads(raw)
        if not isinstance(data, dict):
            return _default_state(sid)
        # Fill missing keys defensively
        base = _default_state(sid)
        base.update({k: data.get(k, base[k]) for k in base})
        return base
    except Exception:
        return _default_state(sid)


def _save_state(state: dict) -> None:
    try:
        _state_path(state["session_id"]).write_text(json.dumps(state))
    except Exception:
        pass


def _extract_plan_topic(plan_path: Path) -> str:
    """Use frontmatter `topic:` if present, else filename slug."""
    try:
        text = plan_path.read_text()
    except Exception:
        text = ""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            fm = text[4:end]
            m = re.search(r'^topic\s*:\s*"?([^"\n]+)"?\s*$', fm, re.MULTILINE)
            if m:
                return m.group(1).strip()
    return plan_path.name[: -len("-plan.md")]


def _plan_is_shipped(plan_path: Path) -> bool:
    try:
        text = plan_path.read_text()
    except Exception:
        return False
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    fm = text[4:end]
    m = re.search(r'^implementation_status\s*:\s*"?([^"\n]+)"?\s*$', fm, re.MULTILINE)
    if not m:
        return False
    return m.group(1).strip().lower() == "shipped"


def _active_plan() -> tuple[Path, str] | None:
    """Return (plan_path, topic) for newest non-shipped plan, else None."""
    tasks_dir = REPO_ROOT / "tasks"
    if not tasks_dir.exists():
        return None
    try:
        candidates = list(tasks_dir.glob("*-plan.md"))
    except Exception:
        return None
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for plan in candidates:
        try:
            if _plan_is_shipped(plan):
                continue
        except Exception:
            continue
        return plan, _extract_plan_topic(plan)
    return None


def _review_artifact_fresh(plan_path: Path, topic: str) -> bool:
    review = REPO_ROOT / "tasks" / f"{topic}-review.md"
    try:
        if not review.exists():
            return False
        return review.stat().st_mtime > plan_path.stat().st_mtime
    except Exception:
        return False


def _emit(tool_name: str, reason: str) -> None:
    try:
        log_event(
            "hook_fire",
            hook_name="post-build-review",
            tool_name=tool_name,
            decision="allow",
            reason=reason,
        )
    except Exception:
        pass


def _read_payload() -> dict:
    try:
        raw = sys.stdin.read()
        if not raw:
            return {}
        return json.loads(raw)
    except Exception:
        return {}


def process(payload: dict) -> str:
    """Run one invocation. Returns the telemetry reason string (for testing)."""
    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        return "skipped-non-edit"

    sid = _session_id()
    state = _load_state(sid)

    active = _active_plan()
    if active is None:
        # No active plan — reset counter if we were tracking one
        if state["plan_topic"] is not None:
            state = _default_state(sid)
            _save_state(state)
        _emit(tool_name, "no-plan")
        return "no-plan"

    plan_path, topic = active

    # Topic changed (new plan became active) → reset counter
    if state["plan_topic"] != topic:
        state = _default_state(sid)
        state["plan_topic"] = topic

    # Check review artifact first (clears flag + counter)
    if _review_artifact_fresh(plan_path, topic):
        already_clear = state["flag"] == "clear" and state["edit_count"] == 0
        state["flag"] = "clear"
        state["edit_count"] = 0
        state["last_review_check_count"] = 0
        state["re_fire_count"] = 0
        _save_state(state)
        reason = "already-reviewed" if already_clear else "flag-clear"
        _emit(tool_name, reason)
        return reason

    # Increment the counter
    state["edit_count"] += 1

    count = state["edit_count"]
    if count < REVIEW_THRESHOLD:
        _save_state(state)
        _emit(tool_name, "plan-active-counting")
        return "plan-active-counting"

    # count >= 10
    if state["flag"] != "needs_review":
        # First time crossing the threshold
        state["flag"] = "needs_review"
        state["last_review_check_count"] = count
        _save_state(state)
        _emit(tool_name, "flag-set")
        return "flag-set"

    # Flag already set. Check for re-fire (every RE_FIRE_STEP edits past threshold).
    over = count - REVIEW_THRESHOLD
    if over > 0 and over % RE_FIRE_STEP == 0:
        state["re_fire_count"] += 1
        state["last_review_check_count"] = count
        _save_state(state)
        _emit(tool_name, "flag-re-fire")
        return "flag-re-fire"

    _save_state(state)
    _emit(tool_name, "plan-active-counting")
    return "plan-active-counting"


def _selftest() -> int:
    """Synthetic scenarios. Returns 0 on success, nonzero on failure."""
    import tempfile

    failures: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            failures.append(msg)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tasks").mkdir()
        os.environ["PROJECT_ROOT"] = str(root)
        os.environ["CLAUDE_SESSION_ID"] = "selftest-session"
        # Rebind module-level constant via the global var used by helpers
        global REPO_ROOT
        REPO_ROOT = root

        state_file = _state_path("selftest-session")
        state_file.unlink(missing_ok=True)

        # Scenario 1: no plan → no-plan
        r = process({"tool_name": "Write"})
        check(r == "no-plan", f"[1] expected no-plan, got {r}")

        # Scenario 2: create plan, count to 9, no flag
        plan = root / "tasks" / "fake-plan.md"
        plan.write_text("---\nscope: \"x\"\n---\n# plan\n")
        for i in range(9):
            r = process({"tool_name": "Write"})
            check(r == "plan-active-counting",
                  f"[2.{i+1}] expected plan-active-counting, got {r}")
        state = _load_state("selftest-session")
        check(state["edit_count"] == 9, f"[2] edit_count=9 expected, got {state['edit_count']}")
        check(state["flag"] == "clear", f"[2] flag=clear expected, got {state['flag']}")

        # Scenario 3: 10th edit → flag-set
        r = process({"tool_name": "Edit"})
        check(r == "flag-set", f"[3] expected flag-set, got {r}")
        state = _load_state("selftest-session")
        check(state["flag"] == "needs_review", f"[3] flag=needs_review expected, got {state['flag']}")

        # Scenario 4: edits 11-14 → still counting, no re-fire
        for i in range(4):
            r = process({"tool_name": "Write"})
            check(r == "plan-active-counting",
                  f"[4.{i+1}] expected plan-active-counting, got {r}")

        # Scenario 5: 15th edit → flag-re-fire
        r = process({"tool_name": "Write"})
        check(r == "flag-re-fire", f"[5] expected flag-re-fire, got {r}")
        state = _load_state("selftest-session")
        check(state["re_fire_count"] == 1, f"[5] re_fire_count=1 expected, got {state['re_fire_count']}")

        # Scenario 6: 16-19 → counting; 20 → re-fire again
        for i in range(4):
            process({"tool_name": "Write"})
        r = process({"tool_name": "Write"})
        check(r == "flag-re-fire", f"[6] expected flag-re-fire at 20, got {r}")
        state = _load_state("selftest-session")
        check(state["re_fire_count"] == 2, f"[6] re_fire_count=2 expected, got {state['re_fire_count']}")

        # Scenario 7: review artifact created → flag clears
        import time as _time
        review = root / "tasks" / "fake-review.md"
        review.write_text("# review\n")
        # Ensure review mtime > plan mtime
        future = _time.time() + 10
        os.utime(review, (future, future))
        r = process({"tool_name": "Write"})
        check(r == "flag-clear", f"[7] expected flag-clear, got {r}")
        state = _load_state("selftest-session")
        check(state["flag"] == "clear", f"[7] flag=clear expected, got {state['flag']}")
        check(state["edit_count"] == 0, f"[7] edit_count=0 expected, got {state['edit_count']}")

        # Scenario 8: subsequent edit with fresh review → already-reviewed
        r = process({"tool_name": "Write"})
        check(r == "already-reviewed", f"[8] expected already-reviewed, got {r}")

        # Scenario 9: non-Write/Edit tool → skipped
        r = process({"tool_name": "Read"})
        check(r == "skipped-non-edit", f"[9] expected skipped-non-edit, got {r}")

        # Scenario 10: malformed state file → regenerates
        state_file.write_text("not-json{")
        fresh = _load_state("selftest-session")
        check(fresh["edit_count"] == 0, f"[10] regenerated state expected, got {fresh}")

        state_file.unlink(missing_ok=True)

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    print("selftest OK")
    return 0


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(_selftest())
    try:
        payload = _read_payload()
        process(payload)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
