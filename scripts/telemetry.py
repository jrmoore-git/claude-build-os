"""Session telemetry emitter. One function: log_event.

Silent-on-error: telemetry must never break a session. stdlib only.
Store: stores/session-telemetry.jsonl (append-only, one JSON object per line).
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

_STORE = Path(__file__).resolve().parent.parent / "stores" / "session-telemetry.jsonl"


def _session_id() -> str:
    sid = os.environ.get("CLAUDE_SESSION_ID")
    if sid:
        return sid
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
