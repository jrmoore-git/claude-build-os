#!/usr/bin/env python3
"""
sim_persona_gen.py — Persona generator for the Skill Compiler Simulator.

Generates diverse simulated user personas from a validated IR JSON file.
Two modes: 'anchor' loads from fixture directory, 'generated' creates via LLM.

Usage:
    # Generate 5 personas via LLM
    python3.11 scripts/sim_persona_gen.py --ir fixtures/sim_compiler/explore/extracted_ir.json --count 5 --type generated

    # Dry-run (print to stdout)
    python3.11 scripts/sim_persona_gen.py --ir fixtures/sim_compiler/explore/extracted_ir.json --count 5 --type generated --dry-run

    # Load anchor personas from fixture directory
    python3.11 scripts/sim_persona_gen.py --ir fixtures/sim_compiler/explore/extracted_ir.json --count 2 --type anchor

    # Override model
    python3.11 scripts/sim_persona_gen.py --ir fixtures/sim_compiler/explore/extracted_ir.json --count 3 --type generated --model gemini-3.1-pro
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm_client import llm_call_json, LLMError

PROJECT_ROOT = Path(__file__).resolve().parent.parent

HIDDEN_STATE_FIELDS = ["knowledge", "urgency", "patience", "trust", "cooperativeness"]
VALID_LEVELS = {"low", "medium", "high"}
VALID_KNOWLEDGE = {"novice", "intermediate", "expert"}
KNOWLEDGE_AS_LEVELS = {"novice": "low", "intermediate": "medium", "expert": "high"}

PERSONA_SCHEMA_FIELDS = ["persona_id", "persona_type", "hidden_state", "opening_input", "behavioral_rules"]
HIDDEN_STATE_REQUIRED = ["goal", "knowledge", "urgency", "patience", "trust", "cooperativeness", "hidden_truth"]

GENERATION_PROMPT = """You are a persona generator for a skill simulation system. Given an Interaction Representation (IR) of a skill, generate diverse simulated user personas that would exercise different paths through the skill.

Each persona represents a user who will interact with this skill. They have hidden behavioral state that drives how they respond.

Generate exactly {count} persona(s) as a JSON array. Each persona must have this structure:

{{
  "persona_id": "generated-N",
  "persona_type": "generated",
  "hidden_state": {{
    "goal": "what the user is trying to accomplish (specific to this skill)",
    "knowledge": "novice|intermediate|expert",
    "urgency": "low|medium|high",
    "patience": "low|medium|high",
    "trust": "low|medium|high",
    "cooperativeness": "low|medium|high",
    "hidden_truth": "a fact or constraint the persona knows but won't volunteer unless the skill draws it out"
  }},
  "opening_input": "what the user types first to invoke this skill",
  "behavioral_rules": "1-3 sentences describing how this persona behaves during the interaction"
}}

Rules:
- Each persona must exercise DIFFERENT decision points or ask nodes from the IR.
- DIVERSITY IS REQUIRED: each persona must differ from every other persona on at least 2 of the 6 hidden_state fields (goal counts as different if substantially different).
- Opening input should be realistic — what a real user would type.
- Behavioral rules should be concrete and actionable, not vague personality descriptions.
- Return ONLY a JSON array, no commentary."""


def load_ir(ir_path):
    """Load and minimally validate an IR JSON file."""
    with open(ir_path) as f:
        ir_data = json.load(f)

    required = ["objective", "decision_points", "ask_nodes"]
    missing = [f for f in required if f not in ir_data]
    if missing:
        print(f"ERROR: IR missing required fields: {missing}", file=sys.stderr)
        sys.exit(1)
    return ir_data


def build_ir_context(ir_data):
    """Build the IR context for the LLM prompt, excluding success/failure criteria."""
    context = {
        "objective": ir_data["objective"],
        "decision_points": ir_data["decision_points"],
        "ask_nodes": ir_data["ask_nodes"],
        "interaction_archetype": ir_data.get("interaction_archetype", "unknown"),
    }
    return json.dumps(context, indent=2)


def validate_persona(persona, index):
    """Validate a single persona card against the schema. Returns list of errors."""
    errors = []
    for field in PERSONA_SCHEMA_FIELDS:
        if field not in persona:
            errors.append(f"persona[{index}] missing '{field}'")

    hs = persona.get("hidden_state", {})
    if not isinstance(hs, dict):
        errors.append(f"persona[{index}] hidden_state must be an object")
        return errors

    for field in HIDDEN_STATE_REQUIRED:
        if field not in hs:
            errors.append(f"persona[{index}] hidden_state missing '{field}'")

    if hs.get("knowledge") not in VALID_KNOWLEDGE:
        errors.append(f"persona[{index}] knowledge must be one of {sorted(VALID_KNOWLEDGE)}, got '{hs.get('knowledge')}'")

    for field in HIDDEN_STATE_FIELDS:
        if field == "knowledge":
            continue
        if hs.get(field) not in VALID_LEVELS:
            errors.append(f"persona[{index}] {field} must be one of {sorted(VALID_LEVELS)}, got '{hs.get(field)}'")

    if "opening_input" in persona and not isinstance(persona["opening_input"], str):
        errors.append(f"persona[{index}] opening_input must be a string")

    if "behavioral_rules" in persona and not isinstance(persona["behavioral_rules"], str):
        errors.append(f"persona[{index}] behavioral_rules must be a string")

    return errors


def _state_vector(persona):
    """Extract comparable state vector from a persona's hidden_state."""
    hs = persona.get("hidden_state", {})
    return {
        "knowledge": KNOWLEDGE_AS_LEVELS.get(hs.get("knowledge", ""), hs.get("knowledge", "")),
        "urgency": hs.get("urgency", ""),
        "patience": hs.get("patience", ""),
        "trust": hs.get("trust", ""),
        "cooperativeness": hs.get("cooperativeness", ""),
    }


def check_diversity(personas):
    """Check that each pair of personas differs on at least 2 hidden_state fields.
    Returns list of violation descriptions.
    """
    violations = []
    for i in range(len(personas)):
        for j in range(i + 1, len(personas)):
            vec_i = _state_vector(personas[i])
            vec_j = _state_vector(personas[j])
            diffs = sum(1 for k in vec_i if vec_i[k] != vec_j[k])
            if diffs < 2:
                violations.append(
                    f"personas {i} and {j} differ on only {diffs} field(s)"
                )
    return violations


def generate_personas(ir_data, count, model):
    """Generate personas via LLM."""
    ir_context = build_ir_context(ir_data)
    system_prompt = GENERATION_PROMPT.format(count=count)
    user_msg = f"Interaction Representation (IR):\n\n<document type=\"interaction_ir\">\n{ir_context}\n</document>"

    result = llm_call_json(
        system_prompt, user_msg,
        model=model, temperature=0.8, timeout=120
    )

    if isinstance(result, dict) and "personas" in result:
        result = result["personas"]
    if not isinstance(result, list):
        raise LLMError(f"Expected JSON array, got {type(result).__name__}", category="parse")

    # Assign IDs and type
    for i, persona in enumerate(result):
        persona["persona_id"] = f"generated-{i + 1}"
        persona["persona_type"] = "generated"

    return result


def load_anchor_personas(ir_path, count):
    """Load anchor personas from the fixture directory adjacent to the IR file."""
    ir_dir = Path(ir_path).parent
    anchor_dir = ir_dir / "personas"

    if not anchor_dir.exists():
        print(f"ERROR: Anchor persona directory not found: {anchor_dir}", file=sys.stderr)
        sys.exit(1)

    personas = []
    for path in sorted(anchor_dir.glob("anchor-*.json")):
        with open(path) as f:
            personas.append(json.load(f))
        if len(personas) >= count:
            break

    if not personas:
        print(f"ERROR: No anchor-*.json files found in {anchor_dir}", file=sys.stderr)
        sys.exit(1)

    return personas


def main():
    parser = argparse.ArgumentParser(description="Persona generator for Skill Compiler Simulator")
    parser.add_argument("--ir", required=True, help="Path to validated IR JSON file")
    parser.add_argument("--count", type=int, default=5, help="Number of personas to generate (default: 5)")
    parser.add_argument("--type", choices=["anchor", "generated"], default="generated",
                        help="Persona type: anchor (from fixtures) or generated (via LLM)")
    parser.add_argument("--output-dir", help="Output directory for persona JSON files")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout without writing files")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Model for persona generation (default: claude-sonnet-4-6)")
    args = parser.parse_args()

    ir_path = Path(args.ir)
    if not ir_path.exists():
        print(f"ERROR: IR file not found: {ir_path}", file=sys.stderr)
        sys.exit(1)

    ir_data = load_ir(ir_path)

    if args.type == "anchor":
        personas = load_anchor_personas(args.ir, args.count)
        print(f"Loaded {len(personas)} anchor persona(s) from fixtures.", file=sys.stderr)
    else:
        print(f"Generating {args.count} persona(s) via {args.model}...", file=sys.stderr)
        try:
            personas = generate_personas(ir_data, args.count, args.model)
        except LLMError as e:
            print(f"ERROR: Persona generation failed: {e}", file=sys.stderr)
            sys.exit(1)

    # Validate all personas
    all_errors = []
    for i, persona in enumerate(personas):
        all_errors.extend(validate_persona(persona, i))

    if all_errors:
        print("WARNING: Persona validation errors:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)

    # Check diversity for generated personas
    if args.type == "generated" and len(personas) > 1:
        violations = check_diversity(personas)
        if violations:
            print("WARNING: Diversity violations:", file=sys.stderr)
            for v in violations:
                print(f"  - {v}", file=sys.stderr)

    if args.dry_run:
        print(json.dumps(personas, indent=2))
        return

    # Write persona files
    output_dir = Path(args.output_dir) if args.output_dir else ir_path.parent / "personas"
    output_dir.mkdir(parents=True, exist_ok=True)

    for persona in personas:
        filename = f"{persona['persona_id']}.json"
        out_path = output_dir / filename
        with open(out_path, "w") as f:
            json.dump(persona, f, indent=2)
            f.write("\n")
        print(f"Wrote {out_path}", file=sys.stderr)

    print(f"Done. {len(personas)} persona(s) written to {output_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
