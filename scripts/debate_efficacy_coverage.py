#!/usr/bin/env python3.11
"""Compute per-arm coverage of decision drivers.

Reads:
- tasks/debate-efficacy-study-coverage/<topic>.md (judge output — DD → [finding_numbers])
- tasks/debate-efficacy-study-mapping/<topic>.json (finding → arm identity)

Writes:
- tasks/debate-efficacy-study-coverage-metrics.json

Outputs to stdout: per-proposal and aggregated coverage tables.
"""

import json
import re
from pathlib import Path

STUDY = Path("/Users/justinmoore/buildos/framework/tasks")
TOPICS = ["autobuild", "explore-intake", "learning-velocity", "streamline-rules", "litellm-fallback"]


def parse_coverage(filepath: Path) -> list[dict]:
    text = filepath.read_text()
    results = []
    for line in text.splitlines():
        line = line.strip()
        if not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "dd" in obj and "surfaced_by" in obj:
            results.append(obj)
    return results


def analyze(topic: str) -> dict:
    mapping = json.loads((STUDY / "debate-efficacy-study-mapping" / f"{topic}.json").read_text())
    arm_by_finding = {m["finding_number"]: m["arm"] for m in mapping}
    coverage = parse_coverage(STUDY / "debate-efficacy-study-coverage" / f"{topic}.md")

    per_dd = []
    for entry in coverage:
        dd = entry["dd"]
        finding_nums = entry.get("surfaced_by", [])
        # Normalize: sometimes judge outputs "Finding 5" as string or other formats
        ints = []
        for n in finding_nums:
            if isinstance(n, int):
                ints.append(n)
            elif isinstance(n, str):
                m = re.search(r"\d+", n)
                if m:
                    ints.append(int(m.group(0)))
        arms_hit = set()
        for n in ints:
            if n in arm_by_finding:
                arms_hit.add(arm_by_finding[n])
        per_dd.append({
            "dd": dd,
            "finding_numbers": ints,
            "arms_surfacing": sorted(arms_hit),
            "surfaced_by_C": "C" in arms_hit,
            "surfaced_by_D": "D" in arms_hit,
        })

    c_count = sum(1 for d in per_dd if d["surfaced_by_C"])
    d_count = sum(1 for d in per_dd if d["surfaced_by_D"])
    both = sum(1 for d in per_dd if d["surfaced_by_C"] and d["surfaced_by_D"])
    only_c = sum(1 for d in per_dd if d["surfaced_by_C"] and not d["surfaced_by_D"])
    only_d = sum(1 for d in per_dd if d["surfaced_by_D"] and not d["surfaced_by_C"])
    neither = sum(1 for d in per_dd if not d["surfaced_by_C"] and not d["surfaced_by_D"])

    return {
        "topic": topic,
        "dds_total": len(per_dd),
        "c_surface_count": c_count,
        "d_surface_count": d_count,
        "both": both,
        "only_c": only_c,
        "only_d": only_d,
        "neither": neither,
        "per_dd": per_dd,
    }


def main():
    per_topic = [analyze(t) for t in TOPICS]
    totals = {
        "dds_total": sum(r["dds_total"] for r in per_topic),
        "c_surface_count": sum(r["c_surface_count"] for r in per_topic),
        "d_surface_count": sum(r["d_surface_count"] for r in per_topic),
        "both": sum(r["both"] for r in per_topic),
        "only_c": sum(r["only_c"] for r in per_topic),
        "only_d": sum(r["only_d"] for r in per_topic),
        "neither": sum(r["neither"] for r in per_topic),
    }
    totals["c_coverage_pct"] = round(100 * totals["c_surface_count"] / totals["dds_total"], 1) if totals["dds_total"] else 0
    totals["d_coverage_pct"] = round(100 * totals["d_surface_count"] / totals["dds_total"], 1) if totals["dds_total"] else 0

    out = {"per_topic": per_topic, "totals": totals}
    (STUDY / "debate-efficacy-study-coverage-metrics.json").write_text(json.dumps(out, indent=2))

    print("Per-proposal decision-driver coverage:")
    print(f"{'Proposal':<22} {'DDs':>4} {'C':>3} {'D':>3} {'both':>5} {'only-C':>7} {'only-D':>7} {'miss':>5}")
    for r in per_topic:
        print(f"{r['topic']:<22} {r['dds_total']:>4} {r['c_surface_count']:>3} {r['d_surface_count']:>3} {r['both']:>5} {r['only_c']:>7} {r['only_d']:>7} {r['neither']:>5}")
    print()
    print(f"TOTAL: {totals['dds_total']} DDs across 5 proposals")
    print(f"  Arm C surfaced: {totals['c_surface_count']} ({totals['c_coverage_pct']}%)")
    print(f"  Arm D surfaced: {totals['d_surface_count']} ({totals['d_coverage_pct']}%)")
    print(f"  Both: {totals['both']}  Only-C: {totals['only_c']}  Only-D: {totals['only_d']}  Neither: {totals['neither']}")


if __name__ == "__main__":
    main()
