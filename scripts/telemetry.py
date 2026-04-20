"""Session telemetry emitter. One function: log_event.

Silent-on-error: telemetry must never break a session. stdlib only.
Store: stores/session-telemetry.jsonl (append-only, one JSON object per line).
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

_STORE = Path(__file__).resolve().parent.parent / "stores" / "session-telemetry.jsonl"


def _find_claude_pid() -> int | None:
    """Walk the process tree to find the nearest `claude` CLI ancestor.

    Returns the PID of the `claude` process that started this session, or None
    if no such ancestor exists within 20 hops. Callers use this to derive a
    stable session_id across invocation paths: hooks (spawned by claude, so
    immediate parent) and Bash-tool-invoked scripts (where the immediate
    parent is a transient shell and `os.getppid()` does NOT equal the claude
    pid). Exact `comm == "claude"` match avoids colliding with macOS desktop
    app helpers ("Claude Helper", etc.).
    """
    pid = os.getpid()
    for _ in range(20):
        try:
            result = subprocess.run(
                ["ps", "-o", "ppid=,comm=", "-p", str(pid)],
                capture_output=True, text=True, timeout=1,
            )
        except (subprocess.SubprocessError, OSError):
            return None
        line = result.stdout.strip()
        if not line:
            return None
        parts = line.split(None, 1)
        if len(parts) < 2:
            return None
        try:
            ppid = int(parts[0])
        except ValueError:
            return None
        comm = parts[1].strip()
        if comm == "claude":
            return pid
        if ppid <= 1:
            return None
        pid = ppid
    return None


def _session_id() -> str:
    sid = os.environ.get("CLAUDE_SESSION_ID")
    if sid:
        return sid
    claude_pid = _find_claude_pid()
    if claude_pid is not None:
        return f"pid-{claude_pid}"
    return f"pid-{os.getppid()}"


def log_event(event_type: str, **fields) -> None:
    try:
        _STORE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "event_type": event_type,
            "session_id": fields.pop("session_id", _session_id()),
            "ts": fields.pop("ts", time.time()),
            **fields,
        }
        line = json.dumps(payload, separators=(",", ":")) + "\n"
        fd = os.open(str(_STORE), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
    except Exception:
        pass
