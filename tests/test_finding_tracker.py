"""Tests for scripts/finding_tracker.py — per-finding state machine."""
import json
import os
import subprocess
import sys
import tempfile

PYTHON = sys.executable
SCRIPT = "scripts/finding_tracker.py"
CWD = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True
).stdout.strip() or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REAL_STORE = os.path.join(CWD, "stores/findings.jsonl")


def _with_temp_store(func):
    """Decorator: redirect store to temp file during test."""
    def wrapper(*args, **kwargs):
        backup = None
        if os.path.exists(REAL_STORE):
            backup = REAL_STORE + ".test-backup"
            os.rename(REAL_STORE, backup)
        try:
            return func(*args, **kwargs)
        finally:
            if os.path.exists(REAL_STORE):
                os.unlink(REAL_STORE)
            if backup and os.path.exists(backup):
                os.rename(backup, REAL_STORE)
    return wrapper


def _run(*cmd_args, input_text=None):
    """Run finding_tracker.py with args."""
    result = subprocess.run(
        [PYTHON, SCRIPT, *cmd_args],
        input=input_text, capture_output=True, text=True, cwd=CWD, timeout=10,
    )
    return result


def _write_judgment(debate_id, challenges):
    """Write a temp judgment file. challenges: list of (num, decision, summary)."""
    tasks_dir = os.path.join(CWD, "tasks")
    os.makedirs(tasks_dir, exist_ok=True)
    content = f"---\ndebate_id: {debate_id}\n---\n\n"
    for num, decision, summary in challenges:
        content += f"### Challenge {num}\n\n{summary}\n\nDecision: {decision}\nConfidence: 0.85\n\n"
    path = tempfile.mktemp(suffix="-judgment.md", dir=tasks_dir)
    with open(path, "w") as f:
        f.write(content)
    return path


@_with_temp_store
def test_import_accepted_findings():
    """Import only ACCEPT findings, skip DISMISS."""
    path = _write_judgment("test-debate", [
        (1, "ACCEPT", "Security concern with auth flow"),
        (2, "DISMISS", "Minor style issue"),
        (3, "ACCEPT", "Missing rollback path"),
    ])
    try:
        result = _run("import", "--judgment", path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["imported"] == 2
        assert data["total_accepted"] == 2
        assert data["debate_id"] == "test-debate"
    finally:
        os.unlink(path)


@_with_temp_store
def test_import_idempotent():
    """Re-importing same judgment doesn't duplicate."""
    path = _write_judgment("test-idem", [(1, "ACCEPT", "Finding one")])
    try:
        _run("import", "--judgment", path)
        result = _run("import", "--judgment", path)
        data = json.loads(result.stdout)
        assert data["imported"] == 0
        assert data["skipped"] == 1
    finally:
        os.unlink(path)


@_with_temp_store
def test_list_findings():
    """List returns imported findings."""
    path = _write_judgment("test-list", [
        (1, "ACCEPT", "First finding"),
        (2, "ACCEPT", "Second finding"),
    ])
    try:
        _run("import", "--judgment", path)
        result = _run("list", "--debate-id", "test-list")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert len(data) == 2
        assert data[0]["finding_id"] == "test-list:1"
    finally:
        os.unlink(path)


@_with_temp_store
def test_list_filter_by_state():
    """List with --state filters correctly."""
    path = _write_judgment("test-filter", [
        (1, "ACCEPT", "Finding A"),
        (2, "ACCEPT", "Finding B"),
    ])
    try:
        _run("import", "--judgment", path)
        _run("transition", "--finding-id", "test-filter:1", "--to", "addressed",
             "--reason", "Fixed in abc123")
        result = _run("list", "--debate-id", "test-filter", "--state", "open")
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["finding_id"] == "test-filter:2"
    finally:
        os.unlink(path)


@_with_temp_store
def test_valid_transition():
    """open → addressed is valid."""
    path = _write_judgment("test-trans", [(1, "ACCEPT", "Test")])
    try:
        _run("import", "--judgment", path)
        result = _run("transition", "--finding-id", "test-trans:1",
                       "--to", "addressed", "--reason", "Fixed")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["old_state"] == "open"
        assert data["new_state"] == "addressed"
    finally:
        os.unlink(path)


@_with_temp_store
def test_invalid_transition():
    """addressed → open is rejected."""
    path = _write_judgment("test-invalid", [(1, "ACCEPT", "Test")])
    try:
        _run("import", "--judgment", path)
        _run("transition", "--finding-id", "test-invalid:1",
             "--to", "addressed", "--reason", "Fixed")
        result = _run("transition", "--finding-id", "test-invalid:1",
                       "--to", "open", "--reason", "Reopen")
        assert result.returncode != 0
    finally:
        os.unlink(path)


@_with_temp_store
def test_nonexistent_finding():
    """Transition on missing finding exits non-zero."""
    result = _run("transition", "--finding-id", "nope:1", "--to", "addressed", "--reason", "x")
    assert result.returncode != 0


@_with_temp_store
def test_summary_counts():
    """Summary returns correct state counts."""
    path = _write_judgment("test-summary", [
        (1, "ACCEPT", "A"),
        (2, "ACCEPT", "B"),
        (3, "ACCEPT", "C"),
    ])
    try:
        _run("import", "--judgment", path)
        _run("transition", "--finding-id", "test-summary:1",
             "--to", "addressed", "--reason", "Fixed")
        _run("transition", "--finding-id", "test-summary:2",
             "--to", "waived", "--reason", "Won't fix")
        result = _run("summary", "--debate-id", "test-summary")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["open"] == 1
        assert data["addressed"] == 1
        assert data["waived"] == 1
        assert data["obsolete"] == 0
    finally:
        os.unlink(path)


@_with_temp_store
def test_last_write_wins():
    """Multiple transitions: last record wins."""
    path = _write_judgment("test-lww", [(1, "ACCEPT", "Test")])
    try:
        _run("import", "--judgment", path)
        _run("transition", "--finding-id", "test-lww:1",
             "--to", "addressed", "--reason", "First fix")
        result = _run("summary", "--debate-id", "test-lww")
        data = json.loads(result.stdout)
        assert data["addressed"] == 1
        assert data["open"] == 0
    finally:
        os.unlink(path)
