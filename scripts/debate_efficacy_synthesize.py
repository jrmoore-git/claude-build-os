#!/usr/bin/env python3.11
"""Compute per-arm metrics from blinded adjudication output + apply decision matrix.

Reads:
- tasks/debate-efficacy-study-adjudication/<topic>.md (judge output)
- tasks/debate-efficacy-study-mapping/<topic>.json (arm identity per finding)

Writes:
- tasks/debate-efficacy-study-results.md (final study writeup)
- tasks/debate-efficacy-study-metrics.json (machine-readable metrics)

Usage: python3.11 scripts/debate_efficacy_synthesize.py
"""

import json
import re
from pathlib import Path

STUDY_ROOT = Path("/Users/justinmoore/buildos/framework/tasks")
TOPICS = ["autobuild", "explore-intake", "learning-velocity", "streamline-rules", "litellm-fallback"]


def parse_judge_output(filepath: Path) -> tuple[list[dict], dict]:
    """Extract JSON lines from judge output. Returns (per_finding_verdicts, summary)."""
    text = filepath.read_text()
    verdicts = []
    summary = None
    # Judge output should contain JSON lines. They may be mixed with review-wrapper prose.
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{") or not line.endswith("}"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "summary" in obj:
            summary = obj["summary"]
        elif "finding" in obj and "verdict" in obj:
            verdicts.append(obj)
    return verdicts, summary or {}


def compute_metrics(topic: str) -> dict:
    """Load judge verdicts + arm mapping, compute per-arm metrics."""
    verdicts, summary = parse_judge_output(STUDY_ROOT / "debate-efficacy-study-adjudication" / f"{topic}.md")
    mapping = json.loads((STUDY_ROOT / "debate-efficacy-study-mapping" / f"{topic}.json").read_text())
    # Index mapping by finding number
    by_number = {m["finding_number"]: m for m in mapping}

    # Bucket findings by arm and verdict
    arm_metrics = {"C": {"valid": 0, "unvalidated": 0, "invalid": 0, "duplicate": 0, "total": 0},
                   "D": {"valid": 0, "unvalidated": 0, "invalid": 0, "duplicate": 0, "total": 0}}
    unique_valid = {"C": [], "D": []}
    duplicate_pairs = []  # findings that duplicate each other

    # First pass: record verdict per finding
    verdict_by_number = {}
    for v in verdicts:
        n = v.get("finding")
        if not isinstance(n, int) or n not in by_number:
            continue
        verdict_by_number[n] = v

    # Second pass: bucket
    for n, m in by_number.items():
        arm = m["arm"]
        v = verdict_by_number.get(n)
        arm_metrics[arm]["total"] += 1
        if v is None:
            # Judge didn't produce verdict — treat as unvalidated
            arm_metrics[arm]["unvalidated"] += 1
            continue
        verdict_str = v["verdict"]
        if verdict_str == "VALID_IN_EVIDENCE":
            arm_metrics[arm]["valid"] += 1
            unique_valid[arm].append({"finding": n, "text_preview": m["text_preview"], "evidence": v.get("evidence", "")})
        elif verdict_str == "UNVALIDATED":
            arm_metrics[arm]["unvalidated"] += 1
        elif verdict_str == "INVALID":
            arm_metrics[arm]["invalid"] += 1
        elif verdict_str.startswith("DUPLICATE_OF_"):
            arm_metrics[arm]["duplicate"] += 1
            try:
                ref_num = int(verdict_str.split("_")[-1])
                ref_arm = by_number.get(ref_num, {}).get("arm")
                duplicate_pairs.append({"finding": n, "arm": arm, "duplicate_of": ref_num, "of_arm": ref_arm})
            except ValueError:
                pass

    # Precision: valid / (valid + invalid) — ignoring unvalidated and duplicates
    for arm in ("C", "D"):
        m = arm_metrics[arm]
        denom = m["valid"] + m["invalid"]
        m["precision"] = round(m["valid"] / denom, 3) if denom > 0 else None

    return {
        "topic": topic,
        "arm_metrics": arm_metrics,
        "unique_valid": unique_valid,
        "duplicate_pairs": duplicate_pairs,
        "verdicts_parsed": len(verdicts),
        "findings_mapped": len(by_number),
        "judge_summary": summary,
    }


def apply_decision_matrix(per_topic: list[dict], intra_arm_variance: dict) -> dict:
    """Apply the pre-registered decision matrix from the plan."""
    # For each topic, compute unique-valid count difference (D - C)
    gaps = []
    for t in per_topic:
        c_valid = t["arm_metrics"]["C"]["valid"]
        d_valid = t["arm_metrics"]["D"]["valid"]
        gap = d_valid - c_valid
        gaps.append({"topic": t["topic"], "C_valid": c_valid, "D_valid": d_valid, "gap_D_minus_C": gap})
    # Count proposals where |gap| >= 2
    d_wins = sum(1 for g in gaps if g["gap_D_minus_C"] >= 2)
    c_wins = sum(1 for g in gaps if g["gap_D_minus_C"] <= -2)
    ties = sum(1 for g in gaps if abs(g["gap_D_minus_C"]) < 2)
    avg_gap = sum(g["gap_D_minus_C"] for g in gaps) / len(gaps) if gaps else 0

    variance_findings = intra_arm_variance.get("gap_findings", None)

    # Decision logic from the plan
    if d_wins >= 3 and variance_findings is not None and avg_gap > variance_findings:
        verdict = "keep-cross-model"
    elif c_wins >= 3 and variance_findings is not None and (-avg_gap) > variance_findings:
        verdict = "drop-cross-model"  # cross-model actively worse
    elif abs(avg_gap) < 2 and (variance_findings is None or abs(avg_gap) < variance_findings):
        verdict = "drop-cross-model"  # equivalence — save the spend
    else:
        verdict = "escalate-to-b"  # inconclusive

    # Precision flip: if arm C has >2x arm D invalid rate, keep cross-model
    c_invalid = sum(t["arm_metrics"]["C"]["invalid"] for t in per_topic)
    d_invalid = sum(t["arm_metrics"]["D"]["invalid"] for t in per_topic)
    c_valid_total = sum(t["arm_metrics"]["C"]["valid"] for t in per_topic)
    d_valid_total = sum(t["arm_metrics"]["D"]["valid"] for t in per_topic)
    c_prec = c_valid_total / (c_valid_total + c_invalid) if (c_valid_total + c_invalid) > 0 else None
    d_prec = d_valid_total / (d_valid_total + d_invalid) if (d_valid_total + d_invalid) > 0 else None
    if c_prec is not None and d_prec is not None and d_prec > 2 * c_prec:
        verdict = "keep-cross-model"

    return {
        "verdict": verdict,
        "per_topic_gap": gaps,
        "d_wins": d_wins,
        "c_wins": c_wins,
        "ties": ties,
        "avg_gap_D_minus_C": round(avg_gap, 2),
        "variance_findings_gap": variance_findings,
        "overall_precision": {"C": round(c_prec, 3) if c_prec else None, "D": round(d_prec, 3) if d_prec else None},
    }


def compute_variance(variance_output_path: Path, arm_d_autobuild_path: Path) -> dict:
    """Compare arm D autobuild original vs rerun. Count MATERIAL-tagged findings as rough signal."""
    material_re = re.compile(r"\[MATERIAL\]", re.IGNORECASE)
    a = len(material_re.findall(arm_d_autobuild_path.read_text())) if arm_d_autobuild_path.exists() else None
    b = len(material_re.findall(variance_output_path.read_text())) if variance_output_path.exists() else None
    return {
        "arm_d_autobuild_material_count": a,
        "variance_rerun_material_count": b,
        "gap_findings": abs(a - b) if (a is not None and b is not None) else None,
    }


def main():
    per_topic = [compute_metrics(t) for t in TOPICS]

    variance = compute_variance(
        STUDY_ROOT / "debate-efficacy-study-variance.md",
        STUDY_ROOT / "debate-efficacy-study-arm-d" / "autobuild.md",
    )

    decision = apply_decision_matrix(per_topic, variance)

    # Write machine-readable metrics
    (STUDY_ROOT / "debate-efficacy-study-metrics.json").write_text(
        json.dumps({"per_topic": per_topic, "variance": variance, "decision": decision}, indent=2)
    )

    # Write human-readable results
    lines = []
    lines.append("---")
    lines.append("topic: debate-efficacy-study")
    lines.append(f"verdict: {decision['verdict']}")
    lines.append(f"n_proposals: {len(TOPICS)}")
    lines.append(f"avg_gap_D_minus_C: {decision['avg_gap_D_minus_C']}")
    lines.append(f"overall_precision_C: {decision['overall_precision']['C']}")
    lines.append(f"overall_precision_D: {decision['overall_precision']['D']}")
    lines.append(f"intra_arm_variance_findings_gap: {variance['gap_findings']}")
    lines.append("judge_model: gemini-3.1-pro")
    lines.append("judge_overlap_note: \"Gemini 3.1 Pro used as judge; also appears in production /challenge's pm persona — partial independence\"")
    lines.append("generated: 2026-04-17")
    lines.append("---")
    lines.append("")
    lines.append("# Debate Efficacy Study — Results")
    lines.append("")
    lines.append(f"## Verdict: {decision['verdict'].upper()}")
    lines.append("")
    lines.append(f"- Average gap (arm D valid findings − arm C valid findings) across n=5: **{decision['avg_gap_D_minus_C']}**")
    lines.append(f"- Arm D wins (≥2 more valid): {decision['d_wins']}/5")
    lines.append(f"- Arm C wins (≥2 more valid): {decision['c_wins']}/5")
    lines.append(f"- Ties (|gap| < 2): {decision['ties']}/5")
    lines.append(f"- Intra-arm variance (|D autobuild original − D variance rerun| MATERIAL findings): {variance['gap_findings']}")
    lines.append(f"- Overall precision: arm C = {decision['overall_precision']['C']}, arm D = {decision['overall_precision']['D']}")
    lines.append("")

    lines.append("## Per-Proposal Finding Matrix")
    lines.append("")
    lines.append("| Proposal | Arm C total / valid / invalid / unval / dup | Arm D total / valid / invalid / unval / dup | Gap (D−C valid) |")
    lines.append("|---|---|---|---|")
    for t in per_topic:
        cm, dm = t["arm_metrics"]["C"], t["arm_metrics"]["D"]
        c_str = f"{cm['total']} / {cm['valid']} / {cm['invalid']} / {cm['unvalidated']} / {cm['duplicate']}"
        d_str = f"{dm['total']} / {dm['valid']} / {dm['invalid']} / {dm['unvalidated']} / {dm['duplicate']}"
        gap = dm['valid'] - cm['valid']
        lines.append(f"| {t['topic']} | {c_str} | {d_str} | {gap:+d} |")
    lines.append("")

    lines.append("## Decision Matrix Applied")
    lines.append("")
    lines.append("Per pre-registered rules from `tasks/debate-efficacy-study-plan.md`:")
    lines.append("")
    lines.append(f"- d_wins = {decision['d_wins']} (need ≥3 for KEEP)")
    lines.append(f"- c_wins = {decision['c_wins']} (need ≥3 for DROP-cross-model-actively-worse)")
    lines.append(f"- avg_gap = {decision['avg_gap_D_minus_C']} (need > {variance['gap_findings']} for KEEP to clear noise)")
    lines.append(f"- overall precision gap: arm D {decision['overall_precision']['D']} vs arm C {decision['overall_precision']['C']}")
    lines.append("")
    lines.append(f"→ **Verdict: {decision['verdict']}**")
    lines.append("")

    lines.append("## Caveats")
    lines.append("")
    lines.append("- **n=5 is the L44-mandated minimum, not a statistical power floor.** Small-effect differences may not be detected.")
    lines.append("- **Retrospective design.** Every proposal has been in the codebase — Claude has prior exposure via session history and training. The blinded adjudication (F1 per challenge artifact) partially mitigates but does not eliminate this.")
    lines.append("- **Gemini 3.1 Pro judge overlaps** with production /challenge's pm persona. Independence is partial.")
    lines.append("- **Judge tool calls** may introduce verification noise. L33 documented a case where cross-model + tools produced a 0.98-confidence false claim.")
    lines.append("- **Arm C Claude-only config** used opus/sonnet mix. A pure-opus arm C might behave differently.")
    lines.append("")

    lines.append("## Artifacts")
    lines.append("")
    lines.append("- `tasks/debate-efficacy-study-proposal.md` — study proposal")
    lines.append("- `tasks/debate-efficacy-study-challenge.md` — /challenge gate artifact")
    lines.append("- `tasks/debate-efficacy-study-plan.md` — execution plan with F1-F6 fixes")
    lines.append("- `tasks/debate-efficacy-study-ground-truth-v2.md` — lightweight outcome reference (NOT authoritative ground truth, per methodology-note)")
    lines.append("- `tasks/debate-efficacy-study-methodology-note.md` — why ground truth pivoted to on-the-fly adjudication")
    lines.append("- `tasks/debate-efficacy-study-arm-c/*.md` — arm C (Claude-only) raw challenger outputs")
    lines.append("- `tasks/debate-efficacy-study-arm-d/*.md` — arm D (multi-model) raw challenger outputs")
    lines.append("- `tasks/debate-efficacy-study-variance.md` — arm D rerun on autobuild for intra-arm variance")
    lines.append("- `tasks/debate-efficacy-study-anonymized/*.md` — arm-anonymized pooled findings (judge input)")
    lines.append("- `tasks/debate-efficacy-study-mapping/*.json` — arm identity per anonymized finding (judge does not see)")
    lines.append("- `tasks/debate-efficacy-study-adjudication/*.md` — judge verdict per finding")
    lines.append("- `tasks/debate-efficacy-study-metrics.json` — machine-readable metrics")
    lines.append("")
    (STUDY_ROOT / "debate-efficacy-study-results.md").write_text("\n".join(lines))
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
