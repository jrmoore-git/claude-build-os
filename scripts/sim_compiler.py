#!/usr/bin/env python3
"""
sim_compiler.py — Skill Compiler for the Skill Compiler Simulator.

Extracts an Interaction Representation (IR) from a SKILL.md file via LLM,
and provides comparison tools for IR validation.

Usage:
    # Extract IR from a skill
    python3.11 scripts/sim_compiler.py --skill explore [--output fixtures/sim_compiler/explore/extracted_ir.json]

    # Dry-run (print to stdout)
    python3.11 scripts/sim_compiler.py --skill explore --dry-run

    # Compare extracted IR against reference IR
    python3.11 scripts/sim_compiler.py --compare \
        fixtures/sim_compiler/explore/reference_ir.json \
        fixtures/sim_compiler/explore/extracted_ir.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm_client import llm_call_json, LLMError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"

VALID_ARCHETYPES = ["intake", "diagnosis", "planning", "critique", "synthesis", "coaching"]

IR_SCHEMA_FIELDS = [
    "objective",
    "decision_points",
    "ask_nodes",
    "success_criteria",
    "failure_criteria",
    "interaction_archetype",
]

EXTRACTION_PROMPT = """You are a skill compiler. Your job is to extract a structured Interaction Representation (IR) from a SKILL.md file.

Read the SKILL.md content below and extract the following fields as a JSON object:

{
  "objective": "One sentence: what user outcome does this skill produce?",
  "decision_points": [
    {
      "location": "Which step/phase this occurs in",
      "decision": "What is being decided",
      "branches": ["branch 1 description", "branch 2 description"]
    }
  ],
  "ask_nodes": [
    {
      "location": "Which step/phase",
      "question": "What is asked",
      "condition": "When this question is asked (e.g., 'only if topic not provided')"
    }
  ],
  "success_criteria": ["criterion 1", "criterion 2"],
  "failure_criteria": ["failure mode 1", "failure mode 2"],
  "interaction_archetype": "One of: intake, diagnosis, planning, critique, synthesis, coaching"
}

Rules:
- Extract ALL decision points where the skill branches based on user input or conditions.
- Extract ALL moments where the skill asks the user a question (AskUserQuestion or equivalent).
- Success criteria: what does a good outcome look like from the user's perspective?
- Failure criteria: what are the known ways this skill breaks?
- Archetype must be exactly one of: intake, diagnosis, planning, critique, synthesis, coaching.
- Be thorough. Missing a decision point or ask node means the simulation won't test that path.
- Return ONLY valid JSON, no markdown fences, no commentary."""


def find_skill_path(skill_name):
    """Find the SKILL.md file for a given skill name."""
    skill_dir = SKILLS_DIR / skill_name
    skill_file = skill_dir / "SKILL.md"
    if skill_file.exists():
        return skill_file
    # Try without directory nesting
    for path in SKILLS_DIR.glob("*/SKILL.md"):
        if path.parent.name == skill_name:
            return path
    return None


def extract_ir(skill_content, model="claude-opus-4-6"):
    """Extract IR from SKILL.md content using an LLM."""
    user_msg = f"SKILL.md content:\n\n<document type=\"skill_procedure\">\n{skill_content}\n</document>"
    result = llm_call_json(
        EXTRACTION_PROMPT, user_msg,
        model=model, temperature=0.1, timeout=120
    )
    return result


def validate_ir(ir_data):
    """Validate that an IR has all required fields and correct types."""
    errors = []
    for field in IR_SCHEMA_FIELDS:
        if field not in ir_data:
            errors.append(f"Missing required field: {field}")

    if "objective" in ir_data and not isinstance(ir_data["objective"], str):
        errors.append("'objective' must be a string")

    if "decision_points" in ir_data:
        if not isinstance(ir_data["decision_points"], list):
            errors.append("'decision_points' must be a list")
        else:
            for i, dp in enumerate(ir_data["decision_points"]):
                if not isinstance(dp, dict):
                    errors.append(f"decision_points[{i}] must be an object")
                else:
                    for key in ["location", "decision", "branches"]:
                        if key not in dp:
                            errors.append(f"decision_points[{i}] missing '{key}'")

    if "ask_nodes" in ir_data:
        if not isinstance(ir_data["ask_nodes"], list):
            errors.append("'ask_nodes' must be a list")
        else:
            for i, an in enumerate(ir_data["ask_nodes"]):
                if not isinstance(an, dict):
                    errors.append(f"ask_nodes[{i}] must be an object")
                else:
                    for key in ["location", "question"]:
                        if key not in an:
                            errors.append(f"ask_nodes[{i}] missing '{key}'")

    for field in ["success_criteria", "failure_criteria"]:
        if field in ir_data and not isinstance(ir_data[field], list):
            errors.append(f"'{field}' must be a list")

    if "interaction_archetype" in ir_data:
        if ir_data["interaction_archetype"] not in VALID_ARCHETYPES:
            errors.append(
                f"'interaction_archetype' must be one of {VALID_ARCHETYPES}, "
                f"got '{ir_data['interaction_archetype']}'"
            )

    return errors


def compare_ir(reference_path, extracted_path):
    """Compare extracted IR against reference IR using a 6-field checklist.

    Returns a dict with per-field ratings and an overall pass/fail.
    """
    with open(reference_path) as f:
        reference = json.load(f)
    with open(extracted_path) as f:
        extracted = json.load(f)

    checklist = {}

    # 1. Objective
    checklist["objective"] = _compare_text_field(
        reference.get("objective", ""),
        extracted.get("objective", ""),
        "Matches the skill's primary user outcome"
    )

    # 2. Decision points
    checklist["decision_points"] = _compare_list_coverage(
        reference.get("decision_points", []),
        extracted.get("decision_points", []),
        key_field="decision",
        criteria="All critical decision points present"
    )

    # 3. Ask nodes
    checklist["ask_nodes"] = _compare_list_coverage(
        reference.get("ask_nodes", []),
        extracted.get("ask_nodes", []),
        key_field="question",
        criteria="All required ask nodes present"
    )

    # 4. Success criteria
    checklist["success_criteria"] = _compare_criteria_list(
        reference.get("success_criteria", []),
        extracted.get("success_criteria", []),
        "Present and materially correct"
    )

    # 5. Failure criteria
    checklist["failure_criteria"] = _compare_criteria_list(
        reference.get("failure_criteria", []),
        extracted.get("failure_criteria", []),
        "Present and materially correct"
    )

    # 6. Interaction archetype
    ref_arch = reference.get("interaction_archetype", "")
    ext_arch = extracted.get("interaction_archetype", "")
    if ref_arch == ext_arch:
        checklist["interaction_archetype"] = {
            "criteria": "Correctly assigned",
            "rating": "pass",
            "notes": f"Both: {ref_arch}"
        }
    else:
        checklist["interaction_archetype"] = {
            "criteria": "Correctly assigned",
            "rating": "fail",
            "notes": f"Reference: {ref_arch}, Extracted: {ext_arch}"
        }

    # Overall
    ratings = [v["rating"] for v in checklist.values()]
    all_pass = all(r == "pass" for r in ratings)

    return {
        "checklist": checklist,
        "all_pass": all_pass,
        "summary": {
            "pass": sum(1 for r in ratings if r == "pass"),
            "partial": sum(1 for r in ratings if r == "partial"),
            "fail": sum(1 for r in ratings if r == "fail"),
        }
    }


def _compare_text_field(reference, extracted, criteria):
    """Compare two text fields. Pass if both non-empty and semantically similar."""
    if not reference and not extracted:
        return {"criteria": criteria, "rating": "pass", "notes": "Both empty"}
    if not extracted:
        return {"criteria": criteria, "rating": "fail", "notes": "Extracted is empty"}
    if not reference:
        return {"criteria": criteria, "rating": "pass", "notes": "Reference empty, extracted present"}
    # Both present — heuristic: pass if they share key words
    ref_words = set(reference.lower().split())
    ext_words = set(extracted.lower().split())
    overlap = len(ref_words & ext_words) / max(len(ref_words), 1)
    if overlap >= 0.3:
        return {"criteria": criteria, "rating": "pass", "notes": f"Word overlap: {overlap:.0%}"}
    return {"criteria": criteria, "rating": "partial", "notes": f"Low word overlap: {overlap:.0%}"}


def _compare_list_coverage(reference_items, extracted_items, key_field, criteria):
    """Compare two lists of dicts by a key field. Check coverage of reference items."""
    if not reference_items:
        return {"criteria": criteria, "rating": "pass", "notes": "No reference items"}

    ref_keys = [item.get(key_field, "").lower() for item in reference_items if isinstance(item, dict)]
    ext_keys = [item.get(key_field, "").lower() for item in extracted_items if isinstance(item, dict)]

    matched = 0
    for rk in ref_keys:
        rk_words = set(rk.split())
        for ek in ext_keys:
            ek_words = set(ek.split())
            if len(rk_words & ek_words) / max(len(rk_words), 1) >= 0.3:
                matched += 1
                break

    coverage = matched / len(ref_keys) if ref_keys else 1.0
    if coverage >= 0.8:
        rating = "pass"
    elif coverage >= 0.5:
        rating = "partial"
    else:
        rating = "fail"

    return {
        "criteria": criteria,
        "rating": rating,
        "notes": f"Coverage: {matched}/{len(ref_keys)} ({coverage:.0%}). Extracted has {len(ext_keys)} items."
    }


def _compare_criteria_list(reference_list, extracted_list, criteria):
    """Compare two lists of strings by word overlap."""
    if not reference_list:
        return {"criteria": criteria, "rating": "pass", "notes": "No reference criteria"}

    matched = 0
    for ref_item in reference_list:
        ref_words = set(ref_item.lower().split())
        for ext_item in extracted_list:
            ext_words = set(ext_item.lower().split())
            if len(ref_words & ext_words) / max(len(ref_words), 1) >= 0.25:
                matched += 1
                break

    coverage = matched / len(reference_list)
    if coverage >= 0.8:
        rating = "pass"
    elif coverage >= 0.5:
        rating = "partial"
    else:
        rating = "fail"

    return {
        "criteria": criteria,
        "rating": rating,
        "notes": f"Coverage: {matched}/{len(reference_list)} ({coverage:.0%})"
    }


def main():
    parser = argparse.ArgumentParser(description="Skill Compiler — extract IR from SKILL.md")
    parser.add_argument("--skill", help="Skill name (e.g., 'explore')")
    parser.add_argument("--output", help="Output path for extracted IR JSON")
    parser.add_argument("--dry-run", action="store_true", help="Print IR to stdout without writing")
    parser.add_argument("--model", default="claude-opus-4-6", help="Model for IR extraction")
    parser.add_argument("--compare", nargs=2, metavar=("REFERENCE", "EXTRACTED"),
                        help="Compare reference IR against extracted IR")
    args = parser.parse_args()

    if args.compare:
        ref_path, ext_path = args.compare
        if not Path(ref_path).exists():
            print(f"ERROR: Reference file not found: {ref_path}", file=sys.stderr)
            sys.exit(1)
        if not Path(ext_path).exists():
            print(f"ERROR: Extracted file not found: {ext_path}", file=sys.stderr)
            sys.exit(1)

        result = compare_ir(ref_path, ext_path)
        print(json.dumps(result, indent=2))
        if not result["all_pass"]:
            print("\nGATE: FAIL — not all fields pass.", file=sys.stderr)
            sys.exit(1)
        else:
            print("\nGATE: PASS — all fields pass.", file=sys.stderr)
        return

    if not args.skill:
        parser.error("--skill is required when not using --compare")

    skill_path = find_skill_path(args.skill)
    if not skill_path:
        print(f"ERROR: Skill '{args.skill}' not found in {SKILLS_DIR}", file=sys.stderr)
        sys.exit(1)

    skill_content = skill_path.read_text()
    print(f"Compiling IR from {skill_path} ({len(skill_content)} chars)...", file=sys.stderr)

    try:
        ir_data = extract_ir(skill_content, model=args.model)
    except LLMError as e:
        print(f"ERROR: IR extraction failed: {e}", file=sys.stderr)
        sys.exit(1)

    errors = validate_ir(ir_data)
    if errors:
        print("WARNING: IR validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)

    if args.dry_run:
        print(json.dumps(ir_data, indent=2))
        return

    output_path = args.output
    if not output_path:
        output_path = str(
            PROJECT_ROOT / "fixtures" / "sim_compiler" / args.skill / "extracted_ir.json"
        )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(ir_data, f, indent=2)
        f.write("\n")
    print(f"IR written to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
