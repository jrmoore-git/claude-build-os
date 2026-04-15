#!/usr/bin/env python3
"""sim_rubric_gen.py -- Generate scoring rubrics from validated IRs for the Skill Compiler Simulator.

Reads a validated IR JSON file, produces a rubric with 3 universal dimensions
plus archetype-specific dimensions generated via LLM.

Usage:
    python3.11 scripts/sim_rubric_gen.py --ir <ir.json> [--output <rubric.json>]
    python3.11 scripts/sim_rubric_gen.py --ir <ir.json> --dry-run
    python3.11 scripts/sim_rubric_gen.py --compare-rubric <generated.json> <reference.md>
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm_client import llm_call_json, LLMError

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RUBRIC_VERSION = "0.1.0-pilot"

UNIVERSAL_DIMENSIONS = [
    {
        "name": "task_completion",
        "description": "Did the skill accomplish its stated objective?",
        "category": "universal",
        "scale_min": 1,
        "scale_max": 5,
    },
    {
        "name": "register_match",
        "description": "Did the skill's communication style match the user's?",
        "category": "universal",
        "scale_min": 1,
        "scale_max": 5,
    },
    {
        "name": "turn_efficiency",
        "description": "Was the interaction appropriately concise?",
        "category": "universal",
        "scale_min": 1,
        "scale_max": 5,
    },
]

ARCHETYPE_PROMPT_SYSTEM = """\
You are a test design expert. Given an interaction archetype and success/failure \
criteria for a skill, generate scoring dimensions for evaluating skill execution quality.

Return a JSON array of 3-5 dimension objects. Each object has:
- "name": snake_case identifier (no spaces)
- "description": one-sentence description of what this dimension measures
- "scale_min": 1
- "scale_max": 5

Focus on dimensions that distinguish good from bad execution for THIS specific \
archetype and these specific criteria. Do not duplicate universal dimensions \
(task_completion, register_match, turn_efficiency).

Return ONLY the JSON array, no other text."""


def load_ir(ir_path):
    """Load and validate an IR JSON file. Returns parsed dict."""
    path = Path(ir_path)
    if not path.exists():
        print(f"ERROR: IR file not found: {ir_path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        ir = json.load(f)
    required = ["objective", "success_criteria", "failure_criteria", "interaction_archetype"]
    missing = [k for k in required if k not in ir]
    if missing:
        print(f"ERROR: IR missing required fields: {missing}", file=sys.stderr)
        sys.exit(1)
    return ir


def generate_archetype_dimensions(ir, model):
    """Prompt the LLM to generate archetype-specific scoring dimensions."""
    user_prompt = (
        f"Interaction archetype: {ir['interaction_archetype']}\n\n"
        f"Objective: {ir.get('objective', 'N/A')}\n\n"
        f"Success criteria:\n{json.dumps(ir['success_criteria'], indent=2)}\n\n"
        f"Failure criteria:\n{json.dumps(ir['failure_criteria'], indent=2)}"
    )
    result = llm_call_json(
        ARCHETYPE_PROMPT_SYSTEM,
        user_prompt,
        model=model,
        temperature=0.0,
        max_tokens=1024,
    )
    if not isinstance(result, list):
        raise LLMError("LLM returned non-array for archetype dimensions", category="parse")
    dimensions = []
    for dim in result:
        dimensions.append({
            "name": dim["name"],
            "description": dim["description"],
            "category": "archetype",
            "scale_min": dim.get("scale_min", 1),
            "scale_max": dim.get("scale_max", 5),
        })
    return dimensions


def build_rubric(ir, model):
    """Build a complete rubric from a validated IR."""
    archetype_dims = generate_archetype_dimensions(ir, model)
    rubric = {
        "rubric_version": RUBRIC_VERSION,
        "interaction_archetype": ir["interaction_archetype"],
        "dimensions": UNIVERSAL_DIMENSIONS + archetype_dims,
    }
    # Validate universal dimensions are present
    dim_names = {d["name"] for d in rubric["dimensions"]}
    for ud in UNIVERSAL_DIMENSIONS:
        if ud["name"] not in dim_names:
            raise ValueError(f"Universal dimension missing: {ud['name']}")
    return rubric


def parse_reference_rubric(ref_path):
    """Extract dimension names from a reference rubric markdown file.

    Looks for ### headings with numbered dimensions (e.g., "### 1. Register Match")
    and returns a list of snake_case dimension names.
    """
    path = Path(ref_path)
    if not path.exists():
        print(f"ERROR: Reference rubric not found: {ref_path}", file=sys.stderr)
        sys.exit(1)
    text = path.read_text()
    # Match "### N. Dimension Name" pattern
    matches = re.findall(r'^###\s+\d+\.\s+(.+)$', text, re.MULTILINE)
    dimensions = []
    for name in matches:
        snake = re.sub(r'[^a-z0-9]+', '_', name.strip().lower()).strip('_')
        dimensions.append(snake)
    return dimensions


# Concept similarity pairs for partial matching
_CONCEPT_ALIASES = {
    "register_match": {"register", "style", "tone", "communication"},
    "flow": {"flow", "threading", "conversation", "thread"},
    "sufficiency_timing": {"sufficiency", "timing", "stop", "enough"},
    "context_block_quality": {"context", "block", "quality", "output"},
    "hidden_truth_surfacing": {"hidden", "truth", "surfacing", "surface"},
    "feature_test": {"feature", "test", "specific", "protocol"},
    "task_completion": {"task", "completion", "accomplish", "objective"},
    "turn_efficiency": {"turn", "efficiency", "concise", "brevity"},
}


def _concept_overlap(name_a, name_b):
    """Check if two dimension names refer to the same concept. Returns 1.0, 0.5, or 0.0."""
    if name_a == name_b:
        return 1.0
    tokens_a = set(name_a.split('_'))
    tokens_b = set(name_b.split('_'))
    # Direct token overlap
    if tokens_a & tokens_b:
        return 0.5
    # Check alias groups
    for aliases in _CONCEPT_ALIASES.values():
        if (tokens_a & aliases) and (tokens_b & aliases):
            return 0.5
    return 0.0


def compare_rubric(generated_path, reference_path):
    """Compare a generated rubric against a reference rubric markdown.

    Returns (coverage_score, details) where coverage_score is weighted and
    details is a list of dicts with match info per reference dimension.
    """
    with open(generated_path) as f:
        generated = json.load(f)
    gen_names = [d["name"] for d in generated.get("dimensions", [])]
    ref_names = parse_reference_rubric(reference_path)

    if not ref_names:
        return 0.0, [{"reference": "(none)", "match": "no dimensions found in reference"}]

    details = []
    total_score = 0.0
    for ref_name in ref_names:
        best_score = 0.0
        best_match = None
        for gen_name in gen_names:
            overlap = _concept_overlap(ref_name, gen_name)
            if overlap > best_score:
                best_score = overlap
                best_match = gen_name
        total_score += best_score
        if best_score >= 1.0:
            details.append({"reference": ref_name, "generated": best_match, "match": "exact", "weight": 1.0})
        elif best_score >= 0.5:
            details.append({"reference": ref_name, "generated": best_match, "match": "partial", "weight": 0.5})
        else:
            details.append({"reference": ref_name, "generated": None, "match": "missing", "weight": 0.0})

    coverage = total_score / len(ref_names)
    return coverage, details


def main():
    parser = argparse.ArgumentParser(description="Generate scoring rubrics from validated IRs")
    parser.add_argument("--ir", help="Path to validated IR JSON file")
    parser.add_argument("--output", help="Output rubric JSON path")
    parser.add_argument("--dry-run", action="store_true", help="Print rubric to stdout instead of writing")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Model for dimension generation")
    parser.add_argument("--compare-rubric", nargs=2, metavar=("GENERATED", "REFERENCE"),
                        help="Compare generated rubric against reference markdown")
    args = parser.parse_args()

    if args.compare_rubric:
        coverage, details = compare_rubric(args.compare_rubric[0], args.compare_rubric[1])
        passed = coverage >= 0.80
        result = {"coverage": round(coverage, 3), "passed": passed, "threshold": 0.80, "details": details}
        print(json.dumps(result, indent=2))
        sys.exit(0 if passed else 1)

    if not args.ir:
        parser.error("--ir is required when not using --compare-rubric")

    ir = load_ir(args.ir)
    rubric = build_rubric(ir, args.model)

    output_json = json.dumps(rubric, indent=2)
    if args.dry_run:
        print(output_json)
    else:
        out_path = Path(args.output) if args.output else Path(args.ir).with_suffix('.rubric.json')
        out_path.write_text(output_json + "\n")
        print(f"Rubric written to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
