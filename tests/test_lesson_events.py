"""Unit tests for scripts/lesson_events.py.

Tests event logging, loading, and velocity metric computation.
Uses tmp_path to isolate from production event log.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import lesson_events  # noqa: E402

TZ = ZoneInfo("America/Los_Angeles")


@pytest.fixture
def events_file(tmp_path, monkeypatch):
    """Redirect EVENTS_FILE to a temp location."""
    ef = tmp_path / "lesson-events.jsonl"
    monkeypatch.setattr(lesson_events, "EVENTS_FILE", ef)
    return ef


# ── log_event ──────────────────────────────────────────────────────────────


class TestLogEvent:
    def test_creates_file_and_writes_event(self, events_file):
        result = lesson_events.log_event("L99", "created", "test event")
        assert result["lesson_id"] == "L99"
        assert result["status"] == "created"
        assert result["detail"] == "test event"
        assert events_file.exists()
        lines = events_file.read_text().strip().splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["lesson_id"] == "L99"

    def test_appends_multiple_events(self, events_file):
        lesson_events.log_event("L1", "created")
        lesson_events.log_event("L1", "resolved", "fix shipped")
        lines = events_file.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_normalizes_id_to_uppercase(self, events_file):
        result = lesson_events.log_event("l42", "created")
        assert result["lesson_id"] == "L42"

    def test_no_detail_omits_key(self, events_file):
        result = lesson_events.log_event("L5", "created")
        assert "detail" not in result

    def test_invalid_status_exits(self, events_file):
        with pytest.raises(SystemExit):
            lesson_events.log_event("L5", "invalid_status")

    def test_all_valid_statuses(self, events_file):
        for status in lesson_events.VALID_STATUSES:
            result = lesson_events.log_event("L1", status, f"test {status}")
            assert result["status"] == status


# ── load_events ────────────────────────────────────────────────────────────


class TestLoadEvents:
    def test_empty_file(self, events_file):
        events_file.touch()
        assert lesson_events.load_events() == []

    def test_missing_file(self, events_file):
        assert lesson_events.load_events() == []

    def test_loads_written_events(self, events_file):
        lesson_events.log_event("L1", "created")
        lesson_events.log_event("L2", "created")
        events = lesson_events.load_events()
        assert len(events) == 2
        assert events[0]["lesson_id"] == "L1"
        assert events[1]["lesson_id"] == "L2"

    def test_skips_malformed_lines(self, events_file):
        events_file.write_text('{"lesson_id": "L1", "status": "created"}\nnot json\n{"lesson_id": "L2", "status": "created"}\n')
        events = lesson_events.load_events()
        assert len(events) == 2


# ── compute_metrics ────────────────────────────────────────────────────────


class TestComputeMetrics:
    def _make_event(self, lid, status, days_ago=0, detail=""):
        ts = (datetime.now(TZ) - timedelta(days=days_ago)).isoformat()
        e = {"timestamp": ts, "lesson_id": lid, "status": status}
        if detail:
            e["detail"] = detail
        return e

    def test_empty_events(self):
        result = lesson_events.compute_metrics([])
        assert "Learning Velocity" in result

    def test_resolution_time(self):
        events = [
            self._make_event("L1", "created", days_ago=10),
            self._make_event("L1", "resolved", days_ago=0),
        ]
        result = lesson_events.compute_metrics(events)
        assert "10 days" in result or "Avg time to resolution" in result

    def test_recurrence_rate(self):
        events = [
            self._make_event("L1", "created", days_ago=5),
            self._make_event("L1", "violated", days_ago=3),
            self._make_event("L1", "violated", days_ago=1),
        ]
        result = lesson_events.compute_metrics(events)
        # L1 is active with 2+ violations
        assert "100%" in result or "1/1" in result

    def test_stale_rate(self):
        events = [
            self._make_event("L1", "created", days_ago=60),
        ]
        result = lesson_events.compute_metrics(events)
        assert "Stale rate" in result

    def test_json_output(self):
        events = [
            self._make_event("L1", "created", days_ago=5),
            self._make_event("L1", "resolved", days_ago=0),
        ]
        result = lesson_events.compute_metrics(events, as_json=True)
        parsed = json.loads(result)
        assert "avg_resolution_days" in parsed
        assert "recurrence_rate_pct" in parsed
        assert "total_active" in parsed
        assert parsed["total_active"] == 0  # L1 resolved, not active

    def test_recent_counts(self):
        events = [
            self._make_event("L1", "created", days_ago=5),
            self._make_event("L2", "created", days_ago=3),
            self._make_event("L1", "promoted", days_ago=1),
        ]
        result = lesson_events.compute_metrics(events, as_json=True)
        parsed = json.loads(result)
        assert parsed["recent_created_30d"] == 2
        assert parsed["recent_promotions_30d"] == 1

    def test_archived_not_active(self):
        events = [
            self._make_event("L1", "created", days_ago=10),
            self._make_event("L1", "archived", days_ago=5),
        ]
        result = lesson_events.compute_metrics(events, as_json=True)
        parsed = json.loads(result)
        assert parsed["total_active"] == 0
