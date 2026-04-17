"""Tests for hooks/hook-post-build-review.py (advisory post-build review gate)."""

import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

HOOK_PATH = os.path.join(
    os.path.dirname(__file__), "..", "hooks", "hook-post-build-review.py"
)


@pytest.fixture
def staging(tmp_path):
    """Isolated PROJECT_ROOT with tasks/ dir and a unique session id."""
    tasks = tmp_path / "tasks"
    tasks.mkdir()

    sid = f"pytest-review-{uuid.uuid4()}"

    yield {
        "root": tmp_path,
        "tasks": tasks,
        "sid": sid,
    }

    Path(f"/tmp/claude-review-{sid}.json").unlink(missing_ok=True)


def write_plan(tasks_dir, slug, shipped=False, topic=None, mtime=None):
    path = tasks_dir / f"{slug}-plan.md"
    lines = [
        "---",
        'scope: "test"',
        'surfaces_affected: "test"',
        'verification_commands: "true"',
        'rollback: "git revert"',
        'review_tier: "Tier 2"',
        'verification_evidence: "PENDING"',
    ]
    if shipped:
        lines.append("implementation_status: shipped")
    if topic:
        lines.append(f'topic: "{topic}"')
    lines.append("---")
    path.write_text("\n".join(lines) + "\n\n# plan body\n")
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def run_hook(staging, tool_name, telemetry_store=None):
    env = os.environ.copy()
    env["CLAUDE_SESSION_ID"] = staging["sid"]
    env["PROJECT_ROOT"] = str(staging["root"])

    # Isolate telemetry store so we can inspect it
    if telemetry_store is not None:
        # Point telemetry at a test-local path by overriding the store location
        # via env — but the telemetry module uses a module-level path. Instead,
        # let telemetry write to the real store; we just verify exit codes.
        pass

    payload = {"tool_name": tool_name, "tool_input": {"file_path": "/tmp/x.py"}}
    result = subprocess.run(
        ["/opt/homebrew/bin/python3.11", HOOK_PATH],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
    )
    return result


def load_state(sid):
    path = Path(f"/tmp/claude-review-{sid}.json")
    if not path.exists():
        return None
    return json.loads(path.read_text())


# ── Core behavior tests ─────────────────────────────────────────────────────


class TestNoActivePlan:
    def test_no_plan_no_counter(self, staging):
        # No tasks/*-plan.md → no counter maintained
        result = run_hook(staging, "Write")
        assert result.returncode == 0
        state = load_state(staging["sid"])
        # state file may or may not exist; if it does, edit_count is 0
        if state is not None:
            assert state["edit_count"] == 0
            assert state["plan_topic"] is None

    def test_shipped_plan_is_not_active(self, staging):
        write_plan(staging["tasks"], "done", shipped=True)
        result = run_hook(staging, "Write")
        assert result.returncode == 0
        state = load_state(staging["sid"])
        if state is not None:
            assert state["edit_count"] == 0


class TestCounting:
    def test_under_threshold_increments(self, staging):
        write_plan(staging["tasks"], "feat")
        for _ in range(5):
            r = run_hook(staging, "Write")
            assert r.returncode == 0
        state = load_state(staging["sid"])
        assert state is not None
        assert state["edit_count"] == 5
        assert state["flag"] == "clear"

    def test_threshold_sets_flag(self, staging):
        write_plan(staging["tasks"], "feat")
        for _ in range(10):
            run_hook(staging, "Write")
        state = load_state(staging["sid"])
        assert state["edit_count"] == 10
        assert state["flag"] == "needs_review"
        assert state["plan_topic"] == "feat"

    def test_re_fire_at_15_edits(self, staging):
        write_plan(staging["tasks"], "feat")
        for _ in range(15):
            run_hook(staging, "Write")
        state = load_state(staging["sid"])
        assert state["edit_count"] == 15
        assert state["flag"] == "needs_review"
        assert state["re_fire_count"] == 1

    def test_re_fire_at_20_edits(self, staging):
        write_plan(staging["tasks"], "feat")
        for _ in range(20):
            run_hook(staging, "Write")
        state = load_state(staging["sid"])
        assert state["edit_count"] == 20
        assert state["re_fire_count"] == 2


class TestReviewArtifact:
    def test_review_artifact_clears_flag(self, staging):
        plan = write_plan(staging["tasks"], "feat")
        for _ in range(12):
            run_hook(staging, "Write")
        state = load_state(staging["sid"])
        assert state["flag"] == "needs_review"

        # Create the review artifact AFTER plan mtime
        review = staging["tasks"] / "feat-review.md"
        review.write_text("# review\n")
        future = time.time() + 10
        os.utime(review, (future, future))

        run_hook(staging, "Write")
        state = load_state(staging["sid"])
        assert state["flag"] == "clear"
        assert state["edit_count"] == 0
        assert state["re_fire_count"] == 0


class TestNonEditTool:
    def test_read_does_not_increment(self, staging):
        write_plan(staging["tasks"], "feat")
        run_hook(staging, "Write")  # prime
        run_hook(staging, "Read")
        run_hook(staging, "Bash")
        state = load_state(staging["sid"])
        # Only the single Write should have incremented
        assert state["edit_count"] == 1


class TestResilience:
    def test_malformed_state_regenerates(self, staging):
        write_plan(staging["tasks"], "feat")
        state_path = Path(f"/tmp/claude-review-{staging['sid']}.json")
        state_path.write_text("not-valid-json{")
        # Should not crash; should regenerate fresh state
        result = run_hook(staging, "Write")
        assert result.returncode == 0
        state = load_state(staging["sid"])
        assert state is not None
        assert state["edit_count"] == 1


class TestTelemetry:
    def test_hook_fire_emitted_on_each_invocation(self, staging, tmp_path):
        """Verify telemetry log_event is called. We check the real store for
        a hook_fire event with hook_name=post-build-review after invocation."""
        from pathlib import Path as _Path
        # Read tail of real telemetry store before/after
        store = _Path(__file__).resolve().parent.parent / "stores" / "session-telemetry.jsonl"
        before_size = store.stat().st_size if store.exists() else 0

        write_plan(staging["tasks"], "feat")
        run_hook(staging, "Write")

        assert store.exists()
        after_size = store.stat().st_size
        assert after_size > before_size, "telemetry store should have grown"

        # Read new lines and confirm at least one is from this hook
        with open(store, "rb") as f:
            f.seek(before_size)
            tail = f.read().decode("utf-8", errors="replace")
        found = False
        for line in tail.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            if (
                ev.get("event_type") == "hook_fire"
                and ev.get("hook_name") == "post-build-review"
                and ev.get("session_id") == staging["sid"]
            ):
                found = True
                break
        assert found, "expected hook_fire event from post-build-review"


class TestSelftest:
    def test_selftest_passes(self):
        result = subprocess.run(
            ["/opt/homebrew/bin/python3.11", HOOK_PATH, "--selftest"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"selftest failed: {result.stderr}"
        assert "selftest OK" in result.stdout
