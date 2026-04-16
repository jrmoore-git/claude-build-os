#!/usr/bin/env python3
"""critique_spike.py — Manual directive injection spike test.

Tests whether hand-crafted directives injected via turn_hooks improve sim scores,
especially hidden_truth. Zero changes to sim_driver or sim_pipeline.

Runs 3 trials with directives and 3 without, same persona, compares mean scores.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sim_driver import run_simulation, sufficiency_reminder_hook

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = PROJECT_ROOT / "fixtures" / "sim_compiler"
LOGS_DIR = PROJECT_ROOT / "logs" / "critique-spike"


# Hand-crafted directives based on anchor-1 transcript analysis.
# The executor's failure: accepted "rotten architecture" framing, jumped to HOW
# (framework choice, team composition) without probing WHY the rebuild is happening
# NOW. Never surfaced the hidden truth (senior iOS devs quit).
DIRECTIVES = [
    "When the user insists on a full rebuild, probe what changed RECENTLY to make this urgent now — not just the technical symptoms. Ask: 'What happened in the last 3 months that made this go from annoying to must-fix?'",
    "When a reframe is rejected, don't give up. Try a different angle — if architecture reframe fails, try a people/team angle: 'Setting aside the code — has anything changed on the team side that's making this harder?'",
    "Do not accept 'the whole thing is rotten' as sufficient diagnosis. Push for specifics: which modules crash most? When did crashes start getting worse? What changed?",
    "Before declaring sufficiency, verify you've explored the PEOPLE dimension: who built the current system, who maintains it now, has the team changed recently? Team changes often drive rebuild decisions more than technical debt.",
    "If the user has low patience and gives short answers, use options format to probe hidden context: 'The urgency — is that (a) the crashes got worse recently, (b) something changed on the team, or (c) a business deadline is forcing the decision?'",
]


def directive_hook(turn, max_turns, executor_history, transcript):
    """Inject hand-crafted directives as a system reminder at every turn."""
    if turn < 1:
        return None
    directive_text = "\n".join(f"{i+1}. {d}" for i, d in enumerate(DIRECTIVES))
    return (
        f"\n\n[CRITIQUE DIRECTIVES — apply these throughout the conversation:\n"
        f"{directive_text}\n"
        f"These directives override your default behavior when they conflict.]"
    )


def run_trial(skill_name, persona_card, rubric, skill_content, with_directives, trial_num):
    """Run a single trial."""
    hooks = [sufficiency_reminder_hook]
    if with_directives:
        hooks.append(directive_hook)

    label = "WITH" if with_directives else "WITHOUT"
    print(f"  Trial {trial_num} ({label} directives)...", file=sys.stderr, flush=True)

    t0 = time.time()
    result = run_simulation(
        skill_name=skill_name,
        skill_content=skill_content,
        persona_card=persona_card,
        rubric=rubric,
        executor_model="claude-opus-4-6",
        persona_model="gemini-3.1-pro",
        judge_model="gpt-5.4",
        max_turns=15,
        turn_hooks=hooks,
    )
    elapsed = time.time() - t0

    scores = result.get("judge_scores", {})
    scores_str = ", ".join(f"{k}={v}" for k, v in sorted(scores.items()))
    print(f"    {scores_str}  [{elapsed:.1f}s]", file=sys.stderr, flush=True)

    return result


def main():
    TRIALS_PER_CONDITION = 3
    skill_name = "explore"

    # Load skill
    skill_path = PROJECT_ROOT / ".claude" / "skills" / skill_name / "SKILL.md"
    skill_content = skill_path.read_text()

    # Load anchor-1 persona (lowest scorer)
    persona_path = FIXTURES_DIR / skill_name / "personas" / "anchor-1.json"
    with open(persona_path) as f:
        persona_card = json.load(f)

    # Load rubric
    rubric_path = FIXTURES_DIR / skill_name / "rubric.json"
    with open(rubric_path) as f:
        rubric = json.load(f)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Run baseline trials (without directives)
    print("\n=== BASELINE (no directives) ===", file=sys.stderr, flush=True)
    baseline_results = []
    for i in range(1, TRIALS_PER_CONDITION + 1):
        result = run_trial(skill_name, persona_card, rubric, skill_content, False, i)
        baseline_results.append(result)

    # Run critique trials (with directives)
    print("\n=== CRITIQUE (with directives) ===", file=sys.stderr, flush=True)
    critique_results = []
    for i in range(1, TRIALS_PER_CONDITION + 1):
        result = run_trial(skill_name, persona_card, rubric, skill_content, True, i)
        critique_results.append(result)

    # Save all results
    all_results = {
        "directives": DIRECTIVES,
        "persona": "anchor-1",
        "trials_per_condition": TRIALS_PER_CONDITION,
        "baseline": [{"scores": r["judge_scores"], "status": r["final_status"]} for r in baseline_results],
        "critique": [{"scores": r["judge_scores"], "status": r["final_status"]} for r in critique_results],
    }

    # Compute stats
    def compute_stats(results):
        dims = {}
        for r in results:
            for dim, score in r.get("judge_scores", {}).items():
                dims.setdefault(dim, []).append(score)
        stats = {}
        for dim, scores in sorted(dims.items()):
            mean = sum(scores) / len(scores)
            variance = sum((s - mean) ** 2 for s in scores) / len(scores)
            std = variance ** 0.5
            stats[dim] = {"mean": round(mean, 2), "std": round(std, 2), "raw": scores}
        return stats

    baseline_stats = compute_stats(baseline_results)
    critique_stats = compute_stats(critique_results)

    all_results["baseline_stats"] = baseline_stats
    all_results["critique_stats"] = critique_stats

    # Compute deltas
    deltas = {}
    for dim in baseline_stats:
        if dim in critique_stats:
            delta = critique_stats[dim]["mean"] - baseline_stats[dim]["mean"]
            deltas[dim] = round(delta, 2)
    all_results["deltas"] = deltas

    # Save
    out_path = LOGS_DIR / "spike_results.json"
    out_path.write_text(json.dumps(all_results, indent=2) + "\n")

    # Save full transcripts
    for i, r in enumerate(baseline_results):
        p = LOGS_DIR / f"baseline_{i+1}.json"
        p.write_text(json.dumps(r, indent=2) + "\n")
    for i, r in enumerate(critique_results):
        p = LOGS_DIR / f"critique_{i+1}.json"
        p.write_text(json.dumps(r, indent=2) + "\n")

    # Print comparison table
    print("\n" + "=" * 70, file=sys.stderr)
    print("RESULTS: Directive Injection Spike", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print(f"{'Dimension':<28} {'Baseline':>12} {'Critique':>12} {'Delta':>8}", file=sys.stderr)
    print("-" * 60, file=sys.stderr)

    for dim in sorted(baseline_stats):
        b = baseline_stats[dim]
        c = critique_stats.get(dim, {"mean": 0, "std": 0})
        d = deltas.get(dim, 0)
        marker = " **" if abs(d) >= 0.5 else ""
        print(f"{dim:<28} {b['mean']:>5.2f}±{b['std']:<5.2f} {c['mean']:>5.2f}±{c['std']:<5.2f} {d:>+6.2f}{marker}", file=sys.stderr)

    # Overall
    b_all = [s for r in baseline_results for s in r.get("judge_scores", {}).values()]
    c_all = [s for r in critique_results for s in r.get("judge_scores", {}).values()]
    b_avg = sum(b_all) / len(b_all) if b_all else 0
    c_avg = sum(c_all) / len(c_all) if c_all else 0
    print("-" * 60, file=sys.stderr)
    print(f"{'OVERALL':<28} {b_avg:>5.2f}{'':>7} {c_avg:>5.2f}{'':>7} {c_avg - b_avg:>+6.2f}", file=sys.stderr)
    print(f"\nResults saved to {out_path}", file=sys.stderr)

    # Print JSON summary to stdout
    print(json.dumps({
        "baseline_stats": {d: s["mean"] for d, s in baseline_stats.items()},
        "critique_stats": {d: s["mean"] for d, s in critique_stats.items()},
        "deltas": deltas,
        "overall_baseline": round(b_avg, 2),
        "overall_critique": round(c_avg, 2),
        "overall_delta": round(c_avg - b_avg, 2),
    }, indent=2))


if __name__ == "__main__":
    main()
