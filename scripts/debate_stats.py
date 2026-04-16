#!/usr/bin/env python3.11
"""
debate_stats.py — `debate.py stats` subcommand.

Extracted from debate.py. Reads stores/debate-log.jsonl and prints
aggregates (phase counts, tool-call totals, evidence grades, costs,
outcomes). Shared constants (DEFAULT_LOG_PATH) pulled lazily.
"""
import json
import os
import sys


def cmd_stats(args):
    """Aggregate stats from debate-log.jsonl."""
    import debate  # lazy: pulls DEFAULT_LOG_PATH

    log_path = debate.DEFAULT_LOG_PATH
    if not os.path.isfile(log_path):
        print("No debate log found.", file=sys.stderr)
        return 1

    events = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))

    if args.last:
        events = events[-args.last:]

    # Aggregate by phase
    phases = {}
    tool_calls_by_model = {}
    grade_totals = {"A": 0, "B": 0, "C": 0, "D": 0}
    outcomes = []

    for ev in events:
        phase = ev.get("phase", "unknown")
        phases[phase] = phases.get(phase, 0) + 1

        # Tool delivery stats
        td = ev.get("tool_delivery", {})
        for label, info in td.items():
            model = info.get("model", "unknown")
            calls = info.get("tool_calls_made", 0)
            tool_calls_by_model[model] = tool_calls_by_model.get(model, 0) + calls

        # Evidence grades
        grades = ev.get("evidence_grades", {})
        for g in ("A", "B", "C", "D"):
            grade_totals[g] += grades.get(g, 0)

        # Outcomes
        if phase == "outcome":
            outcomes.append(ev.get("outcome", {}))

        # Verifier stats
        verifier = ev.get("verifier", {})
        if verifier:
            v_model = verifier.get("model", "unknown")
            tool_calls_by_model[v_model] = tool_calls_by_model.get(v_model, 0) + verifier.get("tool_calls", 0)

    # Cost aggregation from per-event deltas
    total_cost = 0.0
    cost_by_model = {}
    tokens_by_model = {}
    cost_by_date = {}
    events_with_costs = 0
    for ev in events:
        sc = ev.get("costs") or ev.get("session_costs")  # fallback for pre-delta events
        if not sc:
            continue
        events_with_costs += 1
        for model, info in sc.get("by_model", {}).items():
            cost_by_model[model] = cost_by_model.get(model, 0) + info.get("cost_usd", 0)
            entry = tokens_by_model.setdefault(model, {"prompt": 0, "completion": 0})
            entry["prompt"] += info.get("prompt_tokens", 0)
            entry["completion"] += info.get("completion_tokens", 0)
        total_cost += sc.get("total_usd", 0)
        day = ev.get("timestamp", "")[:10]
        if day:
            cost_by_date[day] = cost_by_date.get(day, 0) + sc.get("total_usd", 0)

    print(f"Events analyzed: {len(events)}")
    print(f"\nPhase counts: {json.dumps(phases, indent=2)}")
    print(f"\nTool calls by model: {json.dumps(tool_calls_by_model, indent=2)}")
    print(f"\nEvidence grade totals: {json.dumps(grade_totals)}")

    if events_with_costs > 0:
        print(f"\n── Cost tracking ({events_with_costs}/{len(events)} events have cost data) ──")
        print(f"Total estimated cost: ${total_cost:.4f}")
        print("\nBy model:")
        for model in sorted(cost_by_model, key=lambda m: -cost_by_model[m]):
            toks = tokens_by_model.get(model, {})
            print(f"  {model}: ${cost_by_model[model]:.4f}"
                  f"  ({toks.get('prompt', 0):,} in / {toks.get('completion', 0):,} out)")
        if cost_by_date:
            print("\nBy date:")
            for day in sorted(cost_by_date):
                print(f"  {day}: ${cost_by_date[day]:.4f}")
    else:
        print("\nNo cost data yet (pre-tracking events).")

    if outcomes:
        statuses = {}
        for o in outcomes:
            s = o.get("implementation_status", "unknown")
            statuses[s] = statuses.get(s, 0) + 1
        print(f"\nOutcome statuses: {json.dumps(statuses)}")
    else:
        print("\nNo outcomes recorded yet.")

    return 0
