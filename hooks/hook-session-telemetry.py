#!/usr/bin/env python3.11
# hook-class: advisory
"""Session telemetry observer hook.

Routes three hook events:
  - SessionStart       -> emit session_start (cwd + branch + topic-stub)
  - PostToolUse:Read   -> if file in watchlist, emit context_read
  - SessionEnd         -> emit minimal session_outcome with outcome_source='session-end'
                          (skipped if /wrap already wrote one for this session_id)

Observer-only. Never emits a permission decision. Always exits 0.
Never breaks a session — every exception is swallowed.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:
    from telemetry import log_event  # type: ignore
except Exception:
    def log_event(*args, **kwargs):  # fallback no-op
        return

WATCHLIST_PREFIXES = (
    "docs/current-state.md",
    "docs/project-prd.md",
    "tasks/handoff.md",
    "tasks/lessons.md",
    "tasks/session-log.md",
)
WATCHLIST_SUFFIX_PLAN = "-plan.md"
WATCHLIST_PLAN_DIR = "tasks/"

STORE = REPO_ROOT / "stores" / "session-telemetry.jsonl"


def _session_id() -> str:
    sid = os.environ.get("CLAUDE_SESSION_ID")
    return sid if sid else f"pid-{os.getppid()}"


def _rel(path: str) -> str:
    try:
        p = Path(path).resolve()
        return str(p.relative_to(REPO_ROOT))
    except Exception:
        return path


def _is_watched(rel: str) -> bool:
    if rel in WATCHLIST_PREFIXES:
        return True
    if rel.startswith(WATCHLIST_PLAN_DIR) and rel.endswith(WATCHLIST_SUFFIX_PLAN):
        return True
    return False


def _git_branch() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=2, cwd=str(REPO_ROOT),
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return ""


def _read_payload() -> dict:
    try:
        raw = sys.stdin.read()
        if not raw:
            return {}
        return json.loads(raw)
    except Exception:
        return {}


def _wrap_outcome_exists(session_id: str) -> bool:
    """Tail the JSONL for a session_outcome event matching this session_id."""
    try:
        if not STORE.exists():
            return False
        size = STORE.stat().st_size
        with open(STORE, "rb") as f:
            offset = max(0, size - 64 * 1024)
            f.seek(offset)
            tail = f.read().decode("utf-8", errors="replace")
        for line in reversed(tail.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            if (
                ev.get("event_type") == "session_outcome"
                and ev.get("session_id") == session_id
                and ev.get("outcome_source") == "wrap"
            ):
                return True
        return False
    except Exception:
        return False


def _commits_since(ts: float) -> list[str]:
    try:
        r = subprocess.run(
            ["git", "log", "--format=%H", f"--since=@{int(ts)}"],
            capture_output=True, text=True, timeout=3, cwd=str(REPO_ROOT),
        )
        if r.returncode != 0:
            return []
        return [h for h in r.stdout.strip().splitlines() if h]
    except Exception:
        return []


def _session_start_ts(session_id: str) -> float:
    """Scan recent JSONL for this session's session_start ts."""
    try:
        if not STORE.exists():
            return 0.0
        size = STORE.stat().st_size
        with open(STORE, "rb") as f:
            offset = max(0, size - 256 * 1024)
            f.seek(offset)
            tail = f.read().decode("utf-8", errors="replace")
        for line in reversed(tail.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            if (
                ev.get("event_type") == "session_start"
                and ev.get("session_id") == session_id
            ):
                return float(ev.get("ts") or 0)
    except Exception:
        pass
    return 0.0


def handle_session_start(payload: dict) -> None:
    sid = _session_id()
    topic = (payload.get("prompt") or payload.get("first_prompt") or "")[:200]
    log_event(
        "session_start",
        session_id=sid,
        cwd=str(REPO_ROOT),
        branch=_git_branch(),
        topic=topic,
    )


def handle_post_tool_read(payload: dict) -> None:
    tool_name = payload.get("tool_name", "")
    if tool_name != "Read":
        return
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""
    if not file_path:
        return
    rel = _rel(file_path)
    if not _is_watched(rel):
        return
    log_event("context_read", session_id=_session_id(), file_path=rel)


def handle_session_end(payload: dict) -> None:
    sid = _session_id()
    if _wrap_outcome_exists(sid):
        return
    start_ts = _session_start_ts(sid)
    commits = _commits_since(start_ts) if start_ts else []
    log_event(
        "session_outcome",
        session_id=sid,
        ts_end=time.time(),
        commits=commits,
        review_findings_count=0,
        lessons_created_count=0,
        shipped=False,
        outcome_source="session-end",
    )


def main() -> None:
    try:
        payload = _read_payload()
        event = (
            payload.get("hook_event_name")
            or os.environ.get("CLAUDE_HOOK_EVENT")
            or ""
        )
        if event == "SessionStart":
            handle_session_start(payload)
        elif event == "SessionEnd":
            handle_session_end(payload)
        elif event == "PostToolUse":
            handle_post_tool_read(payload)
        else:
            if payload.get("tool_name") == "Read" and payload.get("tool_input"):
                handle_post_tool_read(payload)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
