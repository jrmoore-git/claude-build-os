#!/usr/bin/env python3.11
"""
debate_outcome.py — `debate.py outcome-update` subcommand.

Extracted from debate.py. Logs an outcome record (append-only) for a prior
debate recommendation. Shared helpers (session cost snapshot, log writer,
project timezone) still live in debate.py; imported lazily to avoid cycles.
"""
import json
from datetime import datetime


def cmd_outcome_update(args):
    """Record an outcome for a debate recommendation (append-only)."""
    import debate  # lazy: debate.py owns _log_debate_event, PROJECT_TZ
    import debate_common

    _cost_snapshot = debate_common.get_session_costs()
    now = datetime.now(debate.PROJECT_TZ)
    outcome = {
        "recommendation_index": args.recommendation,
        "implementation_status": args.implementation_status,
        "validation_status": args.validation_status,
        "reversal": args.reversal,
        "downstream_issues": args.downstream_issues,
        "notes": args.notes or "",
        "updated_at": now.strftime("%Y-%m-%dT%H:%M:%S%z")[:25],
    }
    debate._log_debate_event({
        "phase": "outcome",
        "debate_id": args.debate_id,
        "outcome": outcome,
    }, cost_snapshot=_cost_snapshot)
    print(json.dumps({"status": "ok", "debate_id": args.debate_id, "outcome": outcome}))
    return 0
