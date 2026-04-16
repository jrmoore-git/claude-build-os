"""Tests for hooks/hook-decompose-gate.py (advisory decomposition gate)."""

import json
import os
import subprocess
import uuid
from pathlib import Path

import pytest

HOOK_PATH = os.path.join(
    os.path.dirname(__file__), "..", "hooks", "hook-decompose-gate.py"
)


def run_hook(tool_name, file_path, session_id, flag_contents=None, env_override=None):
    """Invoke the hook with a synthetic tool call; return parsed stdout and rc."""
    env = os.environ.copy()
    env["CLAUDE_SESSION_ID"] = session_id
    # Force main-session context so worktree detection doesn't short-circuit
    env.setdefault("ORCHESTRATION_CONTEXT", "main")
    if env_override:
        env.update(env_override)

    flag_path = Path(f"/tmp/claude-decompose-{session_id}.json")
    if flag_contents is not None:
        flag_path.write_text(json.dumps(flag_contents))
    else:
        flag_path.unlink(missing_ok=True)

    payload = {
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path},
    }
    result = subprocess.run(
        ["/opt/homebrew/bin/python3.11", HOOK_PATH],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
    )
    stdout = result.stdout.strip()
    parsed = json.loads(stdout) if stdout else {}
    return parsed, result.returncode


def fresh_session():
    """Unique session ID, with per-session artifacts cleaned up on request."""
    return f"pytest-{uuid.uuid4()}"


def clean_session(sid):
    for suffix in ("json", "writes", "nudged", "plan-nudged", "pending"):
        Path(f"/tmp/claude-decompose-{sid}.{suffix}").unlink(missing_ok=True)


# --- Silent cases ---

class TestSilentAllow:
    def test_non_write_tool(self):
        sid = fresh_session()
        try:
            out, rc = run_hook("Bash", "/tmp/x.py", sid)
            assert rc == 0
            assert out == {}
        finally:
            clean_session(sid)

    def test_first_write(self):
        sid = fresh_session()
        try:
            out, rc = run_hook("Write", "/tmp/a.py", sid)
            assert rc == 0
            assert out == {}
        finally:
            clean_session(sid)

    def test_same_file_second_write(self):
        sid = fresh_session()
        try:
            run_hook("Write", "/tmp/a.py", sid)
            out, rc = run_hook("Edit", "/tmp/a.py", sid)
            assert rc == 0
            assert out == {}
        finally:
            clean_session(sid)

    def test_bypass_flag_suppresses(self):
        sid = fresh_session()
        try:
            run_hook("Write", "/tmp/a.py", sid)
            out, rc = run_hook(
                "Write", "/tmp/b.py", sid,
                flag_contents={"bypass": True, "reason": "sequential"},
            )
            assert rc == 0
            assert out == {}
        finally:
            clean_session(sid)

    def test_worktree_agent_is_silent(self):
        sid = fresh_session()
        try:
            run_hook("Write", "/tmp/a.py", sid)
            out, rc = run_hook(
                "Write", "/tmp/b.py", sid,
                env_override={"ORCHESTRATION_CONTEXT": "worktree-abc"},
            )
            assert rc == 0
            assert out == {}
        finally:
            clean_session(sid)


# --- Nudge cases ---

class TestNudge:
    def _assert_advisory(self, out):
        """Gate must be advisory: allow + additionalContext, never deny."""
        hso = out.get("hookSpecificOutput", {})
        assert hso.get("permissionDecision") == "allow"
        assert "additionalContext" in hso
        assert "deny" not in json.dumps(out).lower()

    def test_second_unique_file_nudges_once(self):
        sid = fresh_session()
        try:
            run_hook("Write", "/tmp/a.py", sid)
            out1, rc1 = run_hook("Write", "/tmp/b.py", sid)
            assert rc1 == 0
            self._assert_advisory(out1)
            assert "second distinct file" in out1["hookSpecificOutput"]["additionalContext"]

            # Third unique file: already nudged → silent
            out2, rc2 = run_hook("Write", "/tmp/c.py", sid)
            assert rc2 == 0
            assert out2 == {}
        finally:
            clean_session(sid)

    def test_plan_submitted_in_main_session_nudges_once(self):
        sid = fresh_session()
        try:
            out1, _ = run_hook(
                "Write", "/tmp/a.py", sid,
                flag_contents={"plan_submitted": True},
            )
            self._assert_advisory(out1)
            assert "plan_submitted" in out1["hookSpecificOutput"]["additionalContext"] \
                or "parallel plan" in out1["hookSpecificOutput"]["additionalContext"]

            # Second write under the same flag → silent (nudge already fired)
            out2, _ = run_hook(
                "Write", "/tmp/b.py", sid,
                flag_contents={"plan_submitted": True},
            )
            assert out2 == {}
        finally:
            clean_session(sid)


# --- Corrupt flag ---

class TestCorruptFlag:
    def test_corrupt_flag_does_not_deny(self):
        sid = fresh_session()
        flag_path = Path(f"/tmp/claude-decompose-{sid}.json")
        try:
            flag_path.write_text("not-valid-json{")
            # Should not deny under advisory posture. Either silent or nudged, never deny.
            out, rc = run_hook("Write", "/tmp/a.py", sid)
            assert rc == 0
            if "hookSpecificOutput" in out:
                assert out["hookSpecificOutput"]["permissionDecision"] == "allow"
        finally:
            clean_session(sid)
