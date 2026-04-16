#!/usr/bin/env python3
"""sim_pipeline.py — Thin orchestrator for the sim generalization pipeline.

Chains: compile IR → load/generate personas → load/generate rubric → run simulations → aggregate scores.

Usage:
    # Full pipeline with anchor personas and existing rubric
    python3.11 scripts/sim_pipeline.py --skill explore \
        --persona-source anchor \
        --rubric-source fixtures/sim_compiler/explore/rubric.json \
        --output-dir logs/sim-pipeline/explore/

    # Full pipeline with generated personas and generated rubric
    python3.11 scripts/sim_pipeline.py --skill explore \
        --persona-source generate --persona-count 5 \
        --rubric-source generate \
        --output-dir logs/sim-pipeline/explore/

    # Dry-run (compile IR + load personas + load rubric, no simulations)
    python3.11 scripts/sim_pipeline.py --skill explore \
        --persona-source anchor \
        --rubric-source fixtures/sim_compiler/explore/rubric.json \
        --dry-run
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sim_compiler import extract_ir, validate_ir, find_skill_path
from sim_persona_gen import load_anchor_personas, generate_personas, validate_persona, load_ir as load_persona_ir
from sim_rubric_gen import build_rubric, load_ir as load_rubric_ir
from sim_driver import run_simulation, write_result


def compile_ir(skill_name, model="claude-opus-4-6"):
    """Step 1: Extract and validate IR from a skill."""
    skill_path = find_skill_path(skill_name)
    if not skill_path:
        print(f"ERROR: Skill '{skill_name}' not found", file=sys.stderr)
        sys.exit(1)
    skill_content = skill_path.read_text()

    print(f"[pipeline] Compiling IR for /{skill_name}...", file=sys.stderr)
    ir = extract_ir(skill_content, model=model)
    errors = validate_ir(ir)
    if errors:
        print(f"ERROR: IR validation failed: {errors}", file=sys.stderr)
        sys.exit(1)

    return ir, skill_content


def load_personas(ir_path, source, count=3, model="gemini-3.1-pro"):
    """Step 2: Load anchor or generate personas."""
    if source == "anchor":
        print(f"[pipeline] Loading {count} anchor personas...", file=sys.stderr)
        personas = load_anchor_personas(str(ir_path), count)
    elif source == "generate":
        print(f"[pipeline] Generating {count} personas...", file=sys.stderr)
        ir_data = load_persona_ir(str(ir_path))
        personas = generate_personas(ir_data, count, model)
    else:
        print(f"ERROR: Unknown persona source: {source}", file=sys.stderr)
        sys.exit(1)

    # Validate all personas
    all_errors = []
    for i, p in enumerate(personas):
        errs = validate_persona(p, i)
        all_errors.extend(errs)
    if all_errors:
        print(f"WARNING: Persona validation issues: {all_errors}", file=sys.stderr)

    return personas


def load_rubric(source, ir_data=None, model="claude-sonnet-4-6"):
    """Step 3: Load rubric from file or generate from IR."""
    if source == "generate":
        if ir_data is None:
            print("ERROR: --rubric-source generate requires IR data", file=sys.stderr)
            sys.exit(1)
        print("[pipeline] Generating rubric from IR...", file=sys.stderr)
        return build_rubric(ir_data, model)
    else:
        path = Path(source)
        if not path.exists():
            print(f"ERROR: Rubric file not found: {source}", file=sys.stderr)
            sys.exit(1)
        print(f"[pipeline] Loading rubric from {source}...", file=sys.stderr)
        with open(path) as f:
            return json.load(f)


def run_pipeline(skill_name, personas, rubric, skill_content, output_dir=None,
                 executor_model="claude-opus-4-6", persona_model="gemini-3.1-pro",
                 judge_model="gpt-5.4", max_turns=15, dry_run=False):
    """Step 4: Run simulations and aggregate scores."""
    results = []
    for persona in personas:
        pid = persona.get("persona_id", "unknown")
        print(f"[pipeline] Simulating: {skill_name} x {pid}...", file=sys.stderr)

        t0 = time.time()
        result = run_simulation(
            skill_name=skill_name,
            skill_content=skill_content,
            persona_card=persona,
            rubric=rubric,
            executor_model=executor_model,
            persona_model=persona_model,
            judge_model=judge_model,
            max_turns=max_turns,
            dry_run=dry_run,
        )
        elapsed = time.time() - t0

        results.append(result)

        scores_str = ", ".join(f"{k}={v}" for k, v in result.get("judge_scores", {}).items())
        print(f"  {pid}: {result['final_status']} [{elapsed:.1f}s] {scores_str or 'N/A'}", file=sys.stderr)

        if output_dir and not dry_run:
            out_path = Path(output_dir) / "runs.jsonl"
            write_result(result, str(out_path))

    return results


def aggregate_scores(results):
    """Compute per-dimension averages across all runs."""
    dim_totals = {}
    dim_counts = {}
    for r in results:
        for dim, score in r.get("judge_scores", {}).items():
            dim_totals[dim] = dim_totals.get(dim, 0) + score
            dim_counts[dim] = dim_counts.get(dim, 0) + 1

    averages = {}
    for dim in sorted(dim_totals):
        averages[dim] = round(dim_totals[dim] / dim_counts[dim], 2)

    return averages


def main():
    parser = argparse.ArgumentParser(description="Sim Generalization Pipeline")
    parser.add_argument("--skill", required=True, help="Skill name (e.g., 'explore')")
    parser.add_argument("--persona-source", required=True, choices=["anchor", "generate"],
                        help="Persona source: 'anchor' (load from fixtures) or 'generate' (LLM)")
    parser.add_argument("--persona-count", type=int, default=3, help="Number of personas (default: 3)")
    parser.add_argument("--rubric-source", required=True,
                        help="Rubric source: path to JSON file, or 'generate'")
    parser.add_argument("--ir-path", help="Path to pre-compiled IR (skip compilation)")
    parser.add_argument("--output-dir", help="Output directory for run results")
    parser.add_argument("--executor-model", default="claude-opus-4-6")
    parser.add_argument("--persona-model", default="gemini-3.1-pro")
    parser.add_argument("--judge-model", default="gpt-5.4")
    parser.add_argument("--max-turns", type=int, default=15)
    parser.add_argument("--dry-run", action="store_true", help="Compile + load only, no simulations")
    args = parser.parse_args()

    if args.output_dir:
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Step 1: Get IR
    if args.ir_path:
        ir_path = Path(args.ir_path)
        with open(ir_path) as f:
            ir_data = json.load(f)
        skill_path = find_skill_path(args.skill)
        skill_content = skill_path.read_text() if skill_path else ""
        print(f"[pipeline] Using pre-compiled IR from {args.ir_path}", file=sys.stderr)
    else:
        ir_data, skill_content = compile_ir(args.skill)
        # Save compiled IR
        if args.output_dir:
            ir_out = Path(args.output_dir) / "compiled_ir.json"
            ir_out.write_text(json.dumps(ir_data, indent=2) + "\n")
            print(f"[pipeline] IR saved to {ir_out}", file=sys.stderr)
            ir_path = ir_out
        else:
            ir_path = None

    # Step 2: Get personas
    # For anchor personas, we need the IR fixture path (adjacent personas/ dir)
    if args.persona_source == "anchor":
        # Use the reference IR path in fixtures for anchor loading
        fixture_ir = Path(f"fixtures/sim_compiler/{args.skill}/reference_ir.json")
        if not fixture_ir.exists():
            print(f"ERROR: No fixture IR for anchor personas: {fixture_ir}", file=sys.stderr)
            sys.exit(1)
        personas = load_personas(fixture_ir, "anchor", args.persona_count)
    else:
        if ir_path is None:
            print("ERROR: generate personas requires IR on disk (use --output-dir)", file=sys.stderr)
            sys.exit(1)
        personas = load_personas(ir_path, "generate", args.persona_count, args.persona_model)

    # Step 3: Get rubric
    rubric = load_rubric(args.rubric_source, ir_data)

    if args.dry_run:
        print(f"\n[pipeline] DRY RUN complete.", file=sys.stderr)
        print(f"  IR fields: {list(ir_data.keys())}", file=sys.stderr)
        print(f"  Personas: {len(personas)}", file=sys.stderr)
        print(f"  Rubric dimensions: {len(rubric.get('dimensions', []))}", file=sys.stderr)
        summary = {"ir_fields": list(ir_data.keys()), "persona_count": len(personas),
                    "rubric_dimensions": len(rubric.get("dimensions", []))}
        print(json.dumps(summary, indent=2))
        return

    # Step 4: Run simulations
    results = run_pipeline(
        skill_name=args.skill,
        personas=personas,
        rubric=rubric,
        skill_content=skill_content,
        output_dir=args.output_dir,
        executor_model=args.executor_model,
        persona_model=args.persona_model,
        judge_model=args.judge_model,
        max_turns=args.max_turns,
    )

    # Step 5: Aggregate and report
    averages = aggregate_scores(results)
    total_runs = len(results)
    passed = sum(1 for r in results if r.get("objective_achieved"))

    report = {
        "skill": args.skill,
        "total_runs": total_runs,
        "objectives_achieved": passed,
        "average_scores": averages,
        "persona_source": args.persona_source,
        "rubric_source": args.rubric_source,
    }

    if args.output_dir:
        report_path = Path(args.output_dir) / "pipeline_report.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        print(f"\n[pipeline] Report saved to {report_path}", file=sys.stderr)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
