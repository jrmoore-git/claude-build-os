#!/usr/bin/env python3.11
"""
finding_tracker.py — Per-finding state machine for debate findings.

Tracks individual findings through: open → addressed | waived | obsolete.
Store: stores/findings.jsonl (append-only, last-write-wins per finding_id).

Usage:
    python3.11 scripts/finding_tracker.py import --judgment tasks/<topic>-judgment.md
    python3.11 scripts/finding_tracker.py list --debate-id <topic> [--state open]
    python3.11 scripts/finding_tracker.py transition --finding-id <topic>:3 --to addressed --reason "Fixed in abc123"
    python3.11 scripts/finding_tracker.py summary --debate-id <topic>
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

try:
    PROJECT_ROOT = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
    ).strip()
except (subprocess.CalledProcessError, FileNotFoundError):
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE_PATH = os.path.join(PROJECT_ROOT, "stores/findings.jsonl")

VALID_STATES = {"open", "addressed", "waived", "obsolete"}
VALID_TRANSITIONS = {
    ("open", "addressed"),
    ("open", "waived"),
    ("open", "obsolete"),
}


def _load_findings():
    """Load all findings, last-write-wins per finding_id."""
    findings = {}
    if not os.path.exists(STORE_PATH):
        return findings
    with open(STORE_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            fid = record.get("finding_id")
            if fid:
                findings[fid] = record
    return findings


def _append_record(record):
    """Append a record to the store."""
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def cmd_import(args):
    """Import accepted findings from a judgment file."""
    judgment_path = args.judgment
    if not os.path.isabs(judgment_path):
        judgment_path = os.path.join(PROJECT_ROOT, judgment_path)

    try:
        text = open(judgment_path).read()
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract debate_id from frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    debate_id = None
    if fm_match:
        for line in fm_match.group(1).splitlines():
            if line.startswith("debate_id:"):
                debate_id = line.partition(":")[2].strip().strip('"')
    if not debate_id:
        # Infer from filename: tasks/<topic>-judgment.md
        basename = os.path.basename(judgment_path)
        debate_id = basename.replace("-judgment.md", "")

    # Parse findings: look for "Challenge N" or "Finding N" sections with ACCEPT
    # Pattern: ### Challenge N or ## Challenge N followed by decision line
    findings = []
    # Split into challenge blocks
    blocks = re.split(r"(?=###?\s+Challenge\s+\d+)", text)
    for block in blocks:
        header = re.match(r"###?\s+Challenge\s+(\d+)", block)
        if not header:
            continue
        num = int(header.group(1))
        decision_match = re.search(r"Decision:\s*(ACCEPT|DISMISS|ESCALATE)", block, re.IGNORECASE)
        if not decision_match:
            continue
        decision = decision_match.group(1).upper()
        if decision != "ACCEPT":
            continue

        # Extract summary (first non-empty line after header)
        lines = block.splitlines()
        summary = ""
        for line in lines[1:]:
            stripped = line.strip()
            if stripped and not stripped.startswith("Decision:") and not stripped.startswith("Confidence:"):
                summary = stripped[:200]
                break

        # Extract confidence
        conf_match = re.search(r"Confidence:\s*([\d.]+)", block)
        confidence = float(conf_match.group(1)) if conf_match else None

        finding_id = f"{debate_id}:{num}"
        record = {
            "finding_id": finding_id,
            "debate_id": debate_id,
            "challenge_num": num,
            "summary": summary,
            "decision": "ACCEPT",
            "confidence": confidence,
            "state": "open",
            "state_history": [{"state": "open", "timestamp": _now_iso(),
                               "reason": "judge accepted"}],
        }
        findings.append(record)

    # Write findings
    existing = _load_findings()
    imported = 0
    for record in findings:
        if record["finding_id"] in existing:
            continue  # Don't re-import
        _append_record(record)
        imported += 1

    result = {"debate_id": debate_id, "imported": imported,
              "skipped": len(findings) - imported, "total_accepted": len(findings)}
    print(json.dumps(result, indent=2))


def cmd_list(args):
    """List findings for a debate, optionally filtered by state."""
    findings = _load_findings()
    results = []
    for fid, record in sorted(findings.items()):
        if record.get("debate_id") != args.debate_id:
            continue
        if args.state and record.get("state") != args.state:
            continue
        results.append({
            "finding_id": fid,
            "challenge_num": record.get("challenge_num"),
            "summary": record.get("summary", "")[:100],
            "state": record.get("state"),
            "confidence": record.get("confidence"),
        })
    print(json.dumps(results, indent=2))


def cmd_transition(args):
    """Transition a finding to a new state."""
    findings = _load_findings()
    fid = args.finding_id

    if fid not in findings:
        print(f"ERROR: Finding {fid} not found", file=sys.stderr)
        sys.exit(1)

    current = findings[fid]
    old_state = current.get("state", "open")
    new_state = args.to

    if new_state not in VALID_STATES:
        print(f"ERROR: Invalid state '{new_state}'. Valid: {VALID_STATES}", file=sys.stderr)
        sys.exit(1)

    if (old_state, new_state) not in VALID_TRANSITIONS:
        print(f"ERROR: Invalid transition {old_state} → {new_state}. "
              f"Valid from {old_state}: {[t[1] for t in VALID_TRANSITIONS if t[0] == old_state]}",
              file=sys.stderr)
        sys.exit(1)

    # Append updated record (last-write-wins)
    history = current.get("state_history", [])
    history.append({"state": new_state, "timestamp": _now_iso(), "reason": args.reason or ""})
    updated = dict(current)
    updated["state"] = new_state
    updated["state_history"] = history
    _append_record(updated)

    print(json.dumps({"finding_id": fid, "old_state": old_state,
                       "new_state": new_state, "reason": args.reason or ""}))


def cmd_summary(args):
    """Summary counts for a debate."""
    findings = _load_findings()
    counts = {"open": 0, "addressed": 0, "waived": 0, "obsolete": 0}
    for fid, record in findings.items():
        if record.get("debate_id") != args.debate_id:
            continue
        state = record.get("state", "open")
        if state in counts:
            counts[state] += 1

    output = {"debate_id": args.debate_id}
    output.update(counts)
    print(json.dumps(output))


def main():
    parser = argparse.ArgumentParser(description="Per-finding state machine")
    sub = parser.add_subparsers(dest="command")

    p_import = sub.add_parser("import", help="Import findings from judgment")
    p_import.add_argument("--judgment", required=True)

    p_list = sub.add_parser("list", help="List findings")
    p_list.add_argument("--debate-id", required=True)
    p_list.add_argument("--state", default=None)

    p_trans = sub.add_parser("transition", help="Transition a finding")
    p_trans.add_argument("--finding-id", required=True)
    p_trans.add_argument("--to", required=True)
    p_trans.add_argument("--reason", default="")

    p_summary = sub.add_parser("summary", help="Summary counts")
    p_summary.add_argument("--debate-id", required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {"import": cmd_import, "list": cmd_list,
            "transition": cmd_transition, "summary": cmd_summary}
    cmds[args.command](args)


if __name__ == "__main__":
    main()
