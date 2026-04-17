"""Tests for hooks/hook-decompose-gate.py (advisory, plan-driven)."""

import json
import os
import subprocess
import time
import uuid
from pathlib import Path

import pytest

HOOK_PATH = os.path.join(
    os.path.dirname(__file__), "..", "hooks", "hook-decompose-gate.py"
)


@pytest.fixture
def staging(tmp_path, monkeypatch):
    """Isolated PROJECT_ROOT with a tasks/ dir; unique session id per test."""
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    (tmp_path / ".git").mkdir()  # make is_worktree_agent's git call succeed

    sid = f"pytest-{uuid.uuid4()}"

    yield {
        "root": tmp_path,
        "tasks": tasks,
        "sid": sid,
    }

    # Cleanup session sentinels
    for suffix in ("json", "writes", "nudged", "plan-nudged", "components-nudged", "pending"):
        Path(f"/tmp/claude-decompose-{sid}.{suffix}").unlink(missing_ok=True)


def write_plan(tasks_dir, slug, components=None, mtime=None, inline=False, malformed=False):
    """Create a tasks/<slug>-plan.md with the given components list."""
    path = tasks_dir / f"{slug}-plan.md"
    frontmatter_lines = [
        "---",
        'scope: "test plan"',
        'surfaces_affected: "test"',
        'verification_commands: "true"',
        'rollback: "git revert"',
        'review_tier: "Tier 2"',
        'verification_evidence: "PENDING"',
    ]
    if components is not None:
        if inline:
            frontmatter_lines.append(
                f"components: [{', '.join(components)}]"
            )
        else:
            frontmatter_lines.append("components:")
            for c in components:
                frontmatter_lines.append(f"  - {c}")
    frontmatter_lines.append("---")
    body = "\n".join(frontmatter_lines) + "\n\n# Plan body\n"
    if malformed:
        # Break frontmatter by removing the closing `---`
        body = body.replace("---\n\n# Plan body", "# Plan body")
    path.write_text(body)
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def run_hook(staging, tool_name, file_path, flag_contents=None, env_override=None):
    env = os.environ.copy()
    env["CLAUDE_SESSION_ID"] = staging["sid"]
    env["PROJECT_ROOT"] = str(staging["root"])
    env["ORCHESTRATION_CONTEXT"] = "main"
    if env_override:
        env.update(env_override)

    flag_path = Path(f"/tmp/claude-decompose-{staging['sid']}.json")
    if flag_contents is not None:
        flag_path.write_text(json.dumps(flag_contents) if isinstance(flag_contents, dict) else flag_contents)
    else:
        flag_path.unlink(missing_ok=True)

    payload = {"tool_name": tool_name, "tool_input": {"file_path": file_path}}
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


def assert_advisory(out):
    hso = out.get("hookSpecificOutput", {})
    assert hso.get("permissionDecision") == "allow"
    assert "additionalContext" in hso
    assert "deny" not in json.dumps(out).lower()


# --- Silent cases ---

class TestSilentAllow:
    def test_non_write_tool(self, staging):
        write_plan(staging["tasks"], "x", components=["a", "b"])
        out, rc = run_hook(staging, "Bash", "/tmp/x.py")
        assert rc == 0 and out == {}

    def test_no_plan_at_all(self, staging):
        out, rc = run_hook(staging, "Write", "/tmp/x.py")
        assert rc == 0 and out == {}

    def test_plan_with_one_component(self, staging):
        write_plan(staging["tasks"], "x", components=["only-thing"])
        out, rc = run_hook(staging, "Write", "/tmp/x.py")
        assert rc == 0 and out == {}

    def test_plan_with_no_components_field(self, staging):
        write_plan(staging["tasks"], "x", components=None)
        out, rc = run_hook(staging, "Write", "/tmp/x.py")
        assert rc == 0 and out == {}

    def test_plan_older_than_24h_ignored(self, staging):
        stale = time.time() - 25 * 3600
        write_plan(staging["tasks"], "x", components=["a", "b", "c"], mtime=stale)
        out, rc = run_hook(staging, "Write", "/tmp/x.py")
        assert rc == 0 and out == {}

    def test_bypass_flag_suppresses_nudge(self, staging):
        write_plan(staging["tasks"], "x", components=["a", "b"])
        out, rc = run_hook(
            staging, "Write", "/tmp/x.py",
            flag_contents={"bypass": True, "reason": "sequential"},
        )
        assert rc == 0 and out == {}

    def test_worktree_agent_is_silent(self, staging):
        write_plan(staging["tasks"], "x", components=["a", "b"])
        out, rc = run_hook(
            staging, "Write", "/tmp/x.py",
            env_override={"ORCHESTRATION_CONTEXT": "worktree-abc"},
        )
        assert rc == 0 and out == {}

    def test_malformed_frontmatter_is_silent(self, staging):
        write_plan(staging["tasks"], "x", components=["a", "b"], malformed=True)
        out, rc = run_hook(staging, "Write", "/tmp/x.py")
        assert rc == 0 and out == {}


# --- Nudge cases ---

class TestNudge:
    def test_plan_with_two_components_nudges(self, staging):
        write_plan(staging["tasks"], "x", components=["first-thing", "second-thing"])
        out, rc = run_hook(staging, "Write", "/tmp/x.py")
        assert rc == 0
        assert_advisory(out)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "2 components" in ctx
        assert "first-thing" in ctx and "second-thing" in ctx
        assert "x-plan.md" in ctx

    def test_plan_with_four_components_shows_preview_and_count(self, staging):
        write_plan(staging["tasks"], "x", components=["a", "b", "c", "d", "e"])
        out, _ = run_hook(staging, "Write", "/tmp/x.py")
        assert_advisory(out)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "5 components" in ctx
        assert "a, b, c" in ctx
        assert "+2 more" in ctx

    def test_inline_components_form(self, staging):
        write_plan(staging["tasks"], "x", components=["alpha", "beta"], inline=True)
        out, _ = run_hook(staging, "Write", "/tmp/x.py")
        assert_advisory(out)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "2 components" in ctx

    def test_nudge_fires_only_once_per_session(self, staging):
        write_plan(staging["tasks"], "x", components=["a", "b"])
        out1, _ = run_hook(staging, "Write", "/tmp/a.py")
        assert_advisory(out1)
        out2, _ = run_hook(staging, "Write", "/tmp/b.py")
        assert out2 == {}

    def test_plan_submitted_flag_in_main_session_nudges_once(self, staging):
        # No plan file — legacy flag alone triggers the plan_declared nudge
        out1, _ = run_hook(
            staging, "Write", "/tmp/x.py",
            flag_contents={"plan_submitted": True},
        )
        assert_advisory(out1)
        ctx = out1["hookSpecificOutput"]["additionalContext"]
        assert "parallel plan" in ctx.lower() or "plan_submitted" in ctx

        out2, _ = run_hook(
            staging, "Write", "/tmp/y.py",
            flag_contents={"plan_submitted": True},
        )
        assert out2 == {}

    def test_newest_plan_wins_when_multiple_qualify(self, staging):
        older = time.time() - 3600
        write_plan(staging["tasks"], "older", components=["old-a", "old-b"], mtime=older)
        write_plan(staging["tasks"], "newer", components=["new-a", "new-b"])
        out, _ = run_hook(staging, "Write", "/tmp/x.py")
        assert_advisory(out)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "newer-plan.md" in ctx
        assert "new-a" in ctx


# --- Edge cases ---

class TestEdgeCases:
    def test_corrupt_flag_never_denies(self, staging):
        write_plan(staging["tasks"], "x", components=["a", "b"])
        out, rc = run_hook(
            staging, "Write", "/tmp/x.py",
            flag_contents="not-valid-json{",
        )
        assert rc == 0
        # Corrupt flag falls through to plan-components check → nudge
        assert_advisory(out)

    def test_tasks_dir_missing_is_silent(self, tmp_path):
        sid = f"pytest-{uuid.uuid4()}"
        # No tasks/ directory
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = sid
        env["PROJECT_ROOT"] = str(tmp_path)
        env["ORCHESTRATION_CONTEXT"] = "main"
        payload = {"tool_name": "Write", "tool_input": {"file_path": "/tmp/x.py"}}
        try:
            result = subprocess.run(
                ["/opt/homebrew/bin/python3.11", HOOK_PATH],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                timeout=5,
                env=env,
            )
            assert result.returncode == 0
            assert result.stdout.strip() in ("", "{}")
        finally:
            for suffix in ("json", "writes", "nudged", "plan-nudged", "components-nudged", "pending"):
                Path(f"/tmp/claude-decompose-{sid}.{suffix}").unlink(missing_ok=True)
