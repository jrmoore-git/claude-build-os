#!/usr/bin/env /opt/homebrew/bin/python3.11
"""Lesson lifecycle event logger and velocity metrics.

Appends structured events to stores/lesson-events.jsonl.
Computes learning velocity metrics from the event log.

Usage:
  # Log an event
  python3.11 scripts/lesson_events.py log L17 created
  python3.11 scripts/lesson_events.py log L17 resolved --detail "fix shipped in audit-batch2"
  python3.11 scripts/lesson_events.py log L12 promoted --detail "promoted to rules/security.md"
  python3.11 scripts/lesson_events.py log L19 violated --detail "same pattern in /think Phase 5.5"

  # Compute velocity metrics
  python3.11 scripts/lesson_events.py metrics
  python3.11 scripts/lesson_events.py metrics --json

  # Seed from current lessons.md state (run once to bootstrap)
  python3.11 scripts/lesson_events.py seed
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

EVENTS_FILE = Path(__file__).parent.parent / "stores" / "lesson-events.jsonl"
LESSONS_FILE = Path(__file__).parent.parent / "tasks" / "lessons.md"
TZ = ZoneInfo("America/Los_Angeles")

VALID_STATUSES = {"created", "resolved", "promoted", "archived", "violated", "updated"}


def log_event(lesson_id: str, status: str, detail: str = "") -> dict:
    """Append a lifecycle event to the JSONL log."""
    if status not in VALID_STATUSES:
        print(f"ERROR: Invalid status '{status}'. Valid: {', '.join(sorted(VALID_STATUSES))}", file=sys.stderr)
        sys.exit(1)

    event = {
        "timestamp": datetime.now(TZ).isoformat(),
        "lesson_id": lesson_id.upper(),
        "status": status,
    }
    if detail:
        event["detail"] = detail

    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(EVENTS_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")

    return event


def load_events() -> list[dict]:
    """Load all events from the JSONL log."""
    if not EVENTS_FILE.exists():
        return []
    events = []
    for line in EVENTS_FILE.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def compute_metrics(events: list[dict], as_json: bool = False) -> str:
    """Compute learning velocity metrics from events."""
    now = datetime.now(TZ)
    thirty_days_ago = now - timedelta(days=30)

    # Group events by lesson
    by_lesson: dict[str, list[dict]] = {}
    for e in events:
        lid = e.get("lesson_id", "")
        by_lesson.setdefault(lid, []).append(e)

    # --- Metric 1: Resolution time ---
    # For lessons with both 'created' and 'resolved' events, compute avg time
    resolution_times = []
    for lid, lesson_events in by_lesson.items():
        created = None
        resolved = None
        for e in sorted(lesson_events, key=lambda x: x.get("timestamp", "")):
            if e["status"] == "created" and created is None:
                created = e["timestamp"]
            if e["status"] in ("resolved", "promoted"):
                resolved = e["timestamp"]
        if created and resolved:
            try:
                c = datetime.fromisoformat(created)
                r = datetime.fromisoformat(resolved)
                resolution_times.append((r - c).days)
            except (ValueError, TypeError):
                continue

    avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else None

    # --- Metric 2: Recurrence rate ---
    # Lessons with 2+ violated events
    recurrence_count = 0
    total_active = 0
    for lid, lesson_events in by_lesson.items():
        statuses = [e["status"] for e in lesson_events]
        # Active = has 'created' but no 'resolved'/'promoted'/'archived'
        if "created" in statuses and not any(s in statuses for s in ("resolved", "promoted", "archived")):
            total_active += 1
            violations = sum(1 for s in statuses if s == "violated")
            if violations >= 2:
                recurrence_count += 1

    recurrence_rate = (recurrence_count / total_active * 100) if total_active > 0 else 0

    # --- Metric 3: Promotions and resolutions in last 30 days ---
    recent_promotions = 0
    recent_resolutions = 0
    recent_created = 0
    for e in events:
        try:
            ts = datetime.fromisoformat(e["timestamp"])
        except (ValueError, KeyError):
            continue
        if ts >= thirty_days_ago:
            if e["status"] == "promoted":
                recent_promotions += 1
            elif e["status"] == "resolved":
                recent_resolutions += 1
            elif e["status"] == "created":
                recent_created += 1

    # --- Metric 4: Stale rate ---
    # Active lessons with no events in last 30 days
    stale_count = 0
    for lid, lesson_events in by_lesson.items():
        statuses = [e["status"] for e in lesson_events]
        if "created" in statuses and not any(s in statuses for s in ("resolved", "promoted", "archived")):
            latest = max(e.get("timestamp", "") for e in lesson_events)
            try:
                if datetime.fromisoformat(latest) < thirty_days_ago:
                    stale_count += 1
            except (ValueError, TypeError):
                stale_count += 1

    stale_rate = (stale_count / total_active * 100) if total_active > 0 else 0

    if as_json:
        return json.dumps({
            "avg_resolution_days": avg_resolution,
            "recurrence_rate_pct": round(recurrence_rate, 1),
            "recent_promotions_30d": recent_promotions,
            "recent_resolutions_30d": recent_resolutions,
            "recent_created_30d": recent_created,
            "stale_rate_pct": round(stale_rate, 1),
            "total_active": total_active,
            "total_events": len(events),
        }, indent=2)

    lines = ["## Learning Velocity"]
    if avg_resolution is not None:
        lines.append(f"- Avg time to resolution: {avg_resolution:.0f} days")
    else:
        lines.append("- Avg time to resolution: insufficient data")
    lines.append(f"- Recurrence rate: {recurrence_rate:.0f}% ({recurrence_count}/{total_active} active lessons with 2+ violations)")
    lines.append(f"- Last 30 days: {recent_created} created, {recent_resolutions} resolved, {recent_promotions} promoted")
    lines.append(f"- Stale rate: {stale_rate:.0f}% ({stale_count}/{total_active} active with no events in 30d)")
    return "\n".join(lines)


def seed_from_lessons():
    """Bootstrap events from current lessons.md state. Run once."""
    if not LESSONS_FILE.exists():
        print("ERROR: tasks/lessons.md not found", file=sys.stderr)
        sys.exit(1)

    if EVENTS_FILE.exists() and EVENTS_FILE.stat().st_size > 0:
        print("WARNING: lesson-events.jsonl already has data. Seeding will add duplicates.", file=sys.stderr)
        print("Delete the file first if you want a clean seed.", file=sys.stderr)
        sys.exit(1)

    content = LESSONS_FILE.read_text()
    now = datetime.now(TZ).isoformat()
    events_written = 0

    for line in content.splitlines():
        if not line.startswith("| L"):
            continue

        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue

        lesson_id = parts[1].strip()
        lesson_text = parts[2] if len(parts) > 2 else ""

        # Log creation event
        event = {"timestamp": now, "lesson_id": lesson_id, "status": "created", "detail": "seeded from current state"}

        # Check for resolved/promoted status in text
        if "[Resolved" in lesson_text:
            log_event(lesson_id, "created", "seeded from current state")
            log_event(lesson_id, "resolved", f"seeded — {lesson_text[:80]}")
            events_written += 2
        elif "[PROMOTED" in lesson_text:
            log_event(lesson_id, "created", "seeded from current state")
            log_event(lesson_id, "promoted", f"seeded — {lesson_text[:80]}")
            events_written += 2
        else:
            log_event(lesson_id, "created", "seeded from current state")
            events_written += 1

    # Check promoted lessons table
    in_promoted = False
    for line in content.splitlines():
        if "## Promoted lessons" in line:
            in_promoted = True
            continue
        if in_promoted and line.startswith("| L"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                lesson_id = parts[1].strip()
                log_event(lesson_id, "created", "seeded from promoted table")
                log_event(lesson_id, "promoted", f"seeded — {parts[2][:80] if len(parts) > 2 else ''}")
                events_written += 2

    print(f"Seeded {events_written} events from tasks/lessons.md")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "log":
        if len(sys.argv) < 4:
            print("Usage: lesson_events.py log <LESSON_ID> <STATUS> [--detail <text>]", file=sys.stderr)
            sys.exit(1)
        lesson_id = sys.argv[2]
        status = sys.argv[3]
        detail = ""
        if "--detail" in sys.argv:
            idx = sys.argv.index("--detail")
            if idx + 1 < len(sys.argv):
                detail = sys.argv[idx + 1]
        event = log_event(lesson_id, status, detail)
        print(json.dumps(event))

    elif cmd == "metrics":
        events = load_events()
        if not events:
            print("No events recorded yet. Run 'seed' to bootstrap from lessons.md.")
            sys.exit(0)
        as_json = "--json" in sys.argv
        print(compute_metrics(events, as_json=as_json))

    elif cmd == "seed":
        seed_from_lessons()

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
