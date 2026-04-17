#!/usr/bin/env python3.11
"""Query stores/session-telemetry.jsonl for hook fires, context reads, outcome correlations.

Three subcommands:
  hook-fires --window Nd          per-hook block/warn/allow counts
  context-reads --window Nd       per-watchlist-file read rate across sessions
  outcome-correlate <file_path>   bucket sessions by read-vs-skipped of file,
                                  compare avg review_findings_count (wrap sessions only)

Reads JSONL, tolerates malformed lines, emits plain-text tables.
Every output ends with the mandatory candidates footer.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

STORE = Path(__file__).resolve().parent.parent / "stores" / "session-telemetry.jsonl"

FOOTER = (
    "\n---\n"
    "Findings are candidates for investigation, not evidence for deletion. "
    "Read-of-file != file-actually-used-in-reasoning; outcome-correlate "
    "bucketing depends on /wrap completeness. Validate patterns before acting."
)


def parse_window(window: str) -> float:
    """Parse '1d', '7d', '24h' into a cutoff timestamp (now - delta)."""
    now = time.time()
    if not window:
        return 0.0
    unit = window[-1]
    try:
        value = float(window[:-1])
    except ValueError:
        return 0.0
    if unit == "d":
        return now - value * 86400
    if unit == "h":
        return now - value * 3600
    return 0.0


def read_events(cutoff: float = 0.0):
    """Yield events newer than cutoff. Track malformed lines on stderr at end."""
    malformed = 0
    if not STORE.exists():
        return [], 0
    events = []
    with open(STORE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                malformed += 1
                continue
            if cutoff and float(ev.get("ts") or 0) < cutoff:
                continue
            events.append(ev)
    return events, malformed


def bucket_sessions(events):
    """Classify each session_id into wrap-completed / session-end-backup / fully-abandoned.

    Returns: {session_id: bucket_name}. Only sessions with a session_start in the window.
    """
    starts = set()
    outcomes = {}
    for ev in events:
        et = ev.get("event_type")
        sid = ev.get("session_id")
        if not sid:
            continue
        if et == "session_start":
            starts.add(sid)
        elif et == "session_outcome":
            src = ev.get("outcome_source", "")
            if sid not in outcomes or outcomes[sid] != "wrap":
                outcomes[sid] = src

    buckets = {}
    for sid in starts:
        src = outcomes.get(sid)
        if src == "wrap":
            buckets[sid] = "wrap-completed"
        elif src == "session-end":
            buckets[sid] = "session-end-backup"
        else:
            buckets[sid] = "fully-abandoned"
    return buckets


def cmd_hook_fires(args):
    cutoff = parse_window(args.window)
    events, malformed = read_events(cutoff)
    counts = defaultdict(lambda: {"allow": 0, "block": 0, "warn": 0})
    for ev in events:
        if ev.get("event_type") != "hook_fire":
            continue
        hook = ev.get("hook_name", "?")
        decision = ev.get("decision", "?")
        if decision in counts[hook]:
            counts[hook][decision] += 1

    print(f"hook_fires (window={args.window})")
    print(f"{'hook':<24} {'allow':>8} {'block':>8} {'warn':>8} {'total':>8}")
    print("-" * 60)
    if not counts:
        print("(no fires)")
    else:
        for hook in sorted(counts):
            c = counts[hook]
            total = c["allow"] + c["block"] + c["warn"]
            print(f"{hook:<24} {c['allow']:>8} {c['block']:>8} {c['warn']:>8} {total:>8}")
    if malformed:
        print(f"\n({malformed} malformed lines skipped)", file=sys.stderr)
    print(FOOTER)


def cmd_context_reads(args):
    cutoff = parse_window(args.window)
    events, malformed = read_events(cutoff)
    buckets = bucket_sessions(events)
    total_sessions = len(buckets)

    reads_by_file = defaultdict(set)  # file -> set of session_ids that read it
    for ev in events:
        if ev.get("event_type") != "context_read":
            continue
        sid = ev.get("session_id")
        fp = ev.get("file_path")
        if sid and fp and sid in buckets:
            reads_by_file[fp].add(sid)

    print(f"context_reads (window={args.window}, total_sessions={total_sessions})")
    print(f"{'file':<40} {'sessions_read':>14} {'rate':>7}")
    print("-" * 66)
    if not reads_by_file or total_sessions == 0:
        print("(no context reads)")
    else:
        rows = sorted(
            reads_by_file.items(),
            key=lambda kv: len(kv[1]),
            reverse=True,
        )
        for fp, sids in rows:
            rate = len(sids) / total_sessions if total_sessions else 0.0
            print(f"{fp:<40} {len(sids):>14} {rate*100:>6.1f}%")
    if malformed:
        print(f"\n({malformed} malformed lines skipped)", file=sys.stderr)
    print(FOOTER)


def cmd_outcome_correlate(args):
    target_file = args.file_path
    events, malformed = read_events(cutoff=0.0)
    buckets = bucket_sessions(events)

    read_sessions = set()
    for ev in events:
        if ev.get("event_type") == "context_read" and ev.get("file_path") == target_file:
            sid = ev.get("session_id")
            if sid:
                read_sessions.add(sid)

    findings_by_sid = {}
    for ev in events:
        if ev.get("event_type") != "session_outcome":
            continue
        sid = ev.get("session_id")
        if not sid:
            continue
        if ev.get("outcome_source") != "wrap":
            continue
        findings_by_sid[sid] = int(ev.get("review_findings_count") or 0)

    wrap_sids = {sid for sid, b in buckets.items() if b == "wrap-completed"}
    read_wrap = wrap_sids & read_sessions
    skipped_wrap = wrap_sids - read_sessions
    incomplete = {sid for sid, b in buckets.items() if b != "wrap-completed"}

    def avg(sids):
        vals = [findings_by_sid.get(sid, 0) for sid in sids if sid in findings_by_sid]
        if not vals:
            return 0.0, 0
        return sum(vals) / len(vals), len(vals)

    read_avg, read_n = avg(read_wrap)
    skipped_avg, skipped_n = avg(skipped_wrap)

    print(f"outcome_correlate target={target_file}")
    print(f"{'bucket':<28} {'sessions':>10} {'avg_findings':>14}")
    print("-" * 56)
    print(f"{'read + wrap':<28} {read_n:>10} {read_avg:>14.2f}")
    print(f"{'skipped + wrap':<28} {skipped_n:>10} {skipped_avg:>14.2f}")
    print(f"{'outcome-incomplete':<28} {len(incomplete):>10} {'n/a':>14}")
    if malformed:
        print(f"\n({malformed} malformed lines skipped)", file=sys.stderr)
    print(FOOTER)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("hook-fires")
    p1.add_argument("--window", default="1d", help="time window: 1d, 7d, 24h")
    p1.set_defaults(func=cmd_hook_fires)

    p2 = sub.add_parser("context-reads")
    p2.add_argument("--window", default="7d")
    p2.set_defaults(func=cmd_context_reads)

    p3 = sub.add_parser("outcome-correlate")
    p3.add_argument("file_path", help="watchlist file path, e.g. tasks/handoff.md")
    p3.set_defaults(func=cmd_outcome_correlate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
