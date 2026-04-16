"""Tests for scripts/sim_persona_gen.py — persona generation, validation, and diversity."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PYTHON = sys.executable
SCRIPT = "scripts/sim_persona_gen.py"
CWD = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True
).stdout.strip() or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(CWD, "scripts"))
from sim_persona_gen import (
    validate_persona, check_diversity, load_ir, build_ir_context,
    generate_personas, load_anchor_personas, _state_vector,
    HIDDEN_STATE_FIELDS, VALID_LEVELS, VALID_KNOWLEDGE, KNOWLEDGE_AS_LEVELS,
    PERSONA_SCHEMA_FIELDS, HIDDEN_STATE_REQUIRED,
)
from llm_client import LLMError


# ── Fixtures ──────────────────────────────────────────────────────────────

VALID_PERSONA = {
    "persona_id": "test-1",
    "persona_type": "anchor",
    "hidden_state": {
        "goal": "Get help with a test task",
        "knowledge": "intermediate",
        "urgency": "medium",
        "patience": "high",
        "trust": "medium",
        "cooperativeness": "high",
        "hidden_truth": "The real issue is a performance bottleneck in the database layer",
    },
    "opening_input": "I need help with testing",
    "behavioral_rules": "Be cooperative and answer questions directly.",
}

VALID_IR = {
    "objective": "Help the user explore options and produce a structured report.",
    "decision_points": [
        {
            "location": "Step 1",
            "decision": "Is a topic provided?",
            "branches": ["Yes", "No"],
        }
    ],
    "ask_nodes": [
        {
            "location": "Step 1",
            "question": "What do you want to explore?",
            "condition": "Only if topic not provided",
        }
    ],
    "success_criteria": ["User receives a structured report"],
    "failure_criteria": ["No report produced"],
    "interaction_archetype": "intake",
}


def _write_json(tmp_dir, filename, data):
    path = os.path.join(tmp_dir, filename)
    with open(path, "w") as f:
        json.dump(data, f)
    return path


# ── validate_persona: valid input ─────────────────────────────────────────

def test_valid_persona_no_errors():
    errors = validate_persona(VALID_PERSONA, 0)
    assert errors == []


def test_valid_persona_all_knowledge_levels():
    for level in VALID_KNOWLEDGE:
        persona = {**VALID_PERSONA, "hidden_state": {**VALID_PERSONA["hidden_state"], "knowledge": level}}
        errors = validate_persona(persona, 0)
        assert errors == [], f"knowledge='{level}' should be valid but got: {errors}"


def test_valid_persona_all_urgency_levels():
    for level in VALID_LEVELS:
        persona = {**VALID_PERSONA, "hidden_state": {**VALID_PERSONA["hidden_state"], "urgency": level}}
        errors = validate_persona(persona, 0)
        assert errors == [], f"urgency='{level}' should be valid but got: {errors}"


# ── validate_persona: missing top-level fields ────────────────────────────

def test_missing_persona_id():
    persona = {k: v for k, v in VALID_PERSONA.items() if k != "persona_id"}
    errors = validate_persona(persona, 0)
    assert any("persona_id" in e for e in errors)


def test_missing_hidden_state():
    persona = {k: v for k, v in VALID_PERSONA.items() if k != "hidden_state"}
    errors = validate_persona(persona, 0)
    assert any("hidden_state" in e for e in errors)


def test_missing_opening_input():
    persona = {k: v for k, v in VALID_PERSONA.items() if k != "opening_input"}
    errors = validate_persona(persona, 0)
    assert any("opening_input" in e for e in errors)


def test_missing_behavioral_rules():
    persona = {k: v for k, v in VALID_PERSONA.items() if k != "behavioral_rules"}
    errors = validate_persona(persona, 0)
    assert any("behavioral_rules" in e for e in errors)


def test_missing_multiple_top_level_fields():
    persona = {"hidden_state": VALID_PERSONA["hidden_state"]}
    errors = validate_persona(persona, 0)
    missing_count = sum(1 for e in errors if "missing" in e)
    assert missing_count >= 3  # persona_id, persona_type, opening_input, behavioral_rules


# ── validate_persona: hidden_state field validation ───────────────────────

def test_hidden_state_not_dict():
    persona = {**VALID_PERSONA, "hidden_state": "not a dict"}
    errors = validate_persona(persona, 0)
    assert any("must be an object" in e for e in errors)


def test_hidden_state_missing_goal():
    hs = {k: v for k, v in VALID_PERSONA["hidden_state"].items() if k != "goal"}
    persona = {**VALID_PERSONA, "hidden_state": hs}
    errors = validate_persona(persona, 0)
    assert any("goal" in e for e in errors)


def test_hidden_state_missing_knowledge():
    hs = {k: v for k, v in VALID_PERSONA["hidden_state"].items() if k != "knowledge"}
    persona = {**VALID_PERSONA, "hidden_state": hs}
    errors = validate_persona(persona, 0)
    assert any("knowledge" in e for e in errors)


def test_hidden_state_missing_all_required():
    persona = {**VALID_PERSONA, "hidden_state": {}}
    errors = validate_persona(persona, 0)
    for field in HIDDEN_STATE_REQUIRED:
        assert any(field in e for e in errors), f"Expected error for missing '{field}'"


def test_invalid_knowledge_value():
    hs = {**VALID_PERSONA["hidden_state"], "knowledge": "genius"}
    persona = {**VALID_PERSONA, "hidden_state": hs}
    errors = validate_persona(persona, 0)
    assert any("knowledge" in e and "genius" in e for e in errors)


def test_invalid_urgency_value():
    hs = {**VALID_PERSONA["hidden_state"], "urgency": "extreme"}
    persona = {**VALID_PERSONA, "hidden_state": hs}
    errors = validate_persona(persona, 0)
    assert any("urgency" in e and "extreme" in e for e in errors)


def test_invalid_patience_value():
    hs = {**VALID_PERSONA["hidden_state"], "patience": "infinite"}
    persona = {**VALID_PERSONA, "hidden_state": hs}
    errors = validate_persona(persona, 0)
    assert any("patience" in e and "infinite" in e for e in errors)


def test_invalid_trust_value():
    hs = {**VALID_PERSONA["hidden_state"], "trust": "none"}
    persona = {**VALID_PERSONA, "hidden_state": hs}
    errors = validate_persona(persona, 0)
    assert any("trust" in e and "none" in e for e in errors)


def test_invalid_cooperativeness_value():
    hs = {**VALID_PERSONA["hidden_state"], "cooperativeness": "hostile"}
    persona = {**VALID_PERSONA, "hidden_state": hs}
    errors = validate_persona(persona, 0)
    assert any("cooperativeness" in e and "hostile" in e for e in errors)


# ── validate_persona: type checks ────────────────────────────────────────

def test_opening_input_not_string():
    persona = {**VALID_PERSONA, "opening_input": 42}
    errors = validate_persona(persona, 0)
    assert any("opening_input must be a string" in e for e in errors)


def test_behavioral_rules_not_string():
    persona = {**VALID_PERSONA, "behavioral_rules": ["rule1", "rule2"]}
    errors = validate_persona(persona, 0)
    assert any("behavioral_rules must be a string" in e for e in errors)


# ── validate_persona: hidden_truth field ──────────────────────────────────

def test_persona_with_hidden_truth_passes():
    """Persona cards that include hidden_truth should pass validation."""
    hs = {**VALID_PERSONA["hidden_state"], "hidden_truth": "The user already decided but is testing the skill"}
    persona = {**VALID_PERSONA, "hidden_state": hs}
    errors = validate_persona(persona, 0)
    assert errors == []


# ── _state_vector ─────────────────────────────────────────────────────────

def test_state_vector_normalizes_knowledge():
    persona = {**VALID_PERSONA}
    vec = _state_vector(persona)
    # "intermediate" should map to "medium" via KNOWLEDGE_AS_LEVELS
    assert vec["knowledge"] == "medium"


def test_state_vector_expert_maps_to_high():
    persona = {**VALID_PERSONA, "hidden_state": {**VALID_PERSONA["hidden_state"], "knowledge": "expert"}}
    vec = _state_vector(persona)
    assert vec["knowledge"] == "high"


def test_state_vector_novice_maps_to_low():
    persona = {**VALID_PERSONA, "hidden_state": {**VALID_PERSONA["hidden_state"], "knowledge": "novice"}}
    vec = _state_vector(persona)
    assert vec["knowledge"] == "low"


def test_state_vector_preserves_other_fields():
    vec = _state_vector(VALID_PERSONA)
    assert vec["urgency"] == "medium"
    assert vec["patience"] == "high"
    assert vec["trust"] == "medium"
    assert vec["cooperativeness"] == "high"


def test_state_vector_empty_hidden_state():
    persona = {"hidden_state": {}}
    vec = _state_vector(persona)
    assert vec["knowledge"] == ""
    assert vec["urgency"] == ""


# ── check_diversity ───────────────────────────────────────────────────────

def test_diversity_identical_personas_violates():
    personas = [VALID_PERSONA, VALID_PERSONA]
    violations = check_diversity(personas)
    assert len(violations) == 1
    assert "0 and 1" in violations[0]
    assert "0 field" in violations[0]


def test_diversity_one_field_different_violates():
    p1 = VALID_PERSONA
    p2 = {**VALID_PERSONA, "hidden_state": {**VALID_PERSONA["hidden_state"], "urgency": "low"}}
    violations = check_diversity([p1, p2])
    assert len(violations) == 1
    assert "1 field" in violations[0]


def test_diversity_two_fields_different_passes():
    p1 = VALID_PERSONA
    p2 = {**VALID_PERSONA, "hidden_state": {
        **VALID_PERSONA["hidden_state"],
        "urgency": "low",
        "patience": "low",
    }}
    violations = check_diversity([p1, p2])
    assert violations == []


def test_diversity_single_persona_no_violations():
    violations = check_diversity([VALID_PERSONA])
    assert violations == []


def test_diversity_empty_list_no_violations():
    violations = check_diversity([])
    assert violations == []


def test_diversity_three_personas_checks_all_pairs():
    """With 3 identical personas, there should be 3 violations (pairs 0-1, 0-2, 1-2)."""
    personas = [VALID_PERSONA, VALID_PERSONA, VALID_PERSONA]
    violations = check_diversity(personas)
    assert len(violations) == 3


def test_diversity_knowledge_normalization():
    """'expert' and 'high' should be equivalent after normalization."""
    p1 = {**VALID_PERSONA, "hidden_state": {
        **VALID_PERSONA["hidden_state"],
        "knowledge": "expert",  # maps to "high"
    }}
    p2 = {**VALID_PERSONA, "hidden_state": {
        **VALID_PERSONA["hidden_state"],
        "knowledge": "novice",  # maps to "low" — different from "high"
        "urgency": "high",     # different from "medium"
    }}
    violations = check_diversity([p1, p2])
    assert violations == []


# ── load_ir ───────────────────────────────────────────────────────────────

def test_load_ir_valid():
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_json(tmp, "ir.json", VALID_IR)
        ir_data = load_ir(path)
        assert ir_data["objective"] == VALID_IR["objective"]


def test_load_ir_missing_field(monkeypatch):
    """load_ir exits with error when required fields are missing."""
    ir_without_objective = {k: v for k, v in VALID_IR.items() if k != "objective"}
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_json(tmp, "ir.json", ir_without_objective)
        import pytest
        with pytest.raises(SystemExit):
            load_ir(path)


def test_load_ir_missing_multiple_fields():
    ir_minimal = {"objective": "test"}
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_json(tmp, "ir.json", ir_minimal)
        import pytest
        with pytest.raises(SystemExit):
            load_ir(path)


# ── build_ir_context ──────────────────────────────────────────────────────

def test_build_ir_context_includes_required_fields():
    context_str = build_ir_context(VALID_IR)
    context = json.loads(context_str)
    assert "objective" in context
    assert "decision_points" in context
    assert "ask_nodes" in context
    assert "interaction_archetype" in context


def test_build_ir_context_excludes_criteria():
    context_str = build_ir_context(VALID_IR)
    context = json.loads(context_str)
    assert "success_criteria" not in context
    assert "failure_criteria" not in context


def test_build_ir_context_default_archetype():
    ir_no_archetype = {k: v for k, v in VALID_IR.items() if k != "interaction_archetype"}
    context_str = build_ir_context(ir_no_archetype)
    context = json.loads(context_str)
    assert context["interaction_archetype"] == "unknown"


# ── generate_personas (mocked LLM) ───────────────────────────────────────

def _make_generated_personas(count):
    """Build a list of generated persona dicts as an LLM would return them."""
    levels = ["low", "medium", "high"]
    knowledge = ["novice", "intermediate", "expert"]
    personas = []
    for i in range(count):
        personas.append({
            "hidden_state": {
                "goal": f"Goal for persona {i + 1}",
                "knowledge": knowledge[i % 3],
                "urgency": levels[i % 3],
                "patience": levels[(i + 1) % 3],
                "trust": levels[(i + 2) % 3],
                "cooperativeness": levels[i % 3],
            },
            "opening_input": f"I want to do thing {i + 1}",
            "behavioral_rules": f"Behavior rules for persona {i + 1}.",
        })
    return personas


def test_generate_personas_returns_list(monkeypatch):
    mock_result = _make_generated_personas(3)
    monkeypatch.setattr(
        "sim_persona_gen.llm_call_json",
        lambda system, user, **kwargs: mock_result,
    )
    result = generate_personas(VALID_IR, 3, "test-model")
    assert isinstance(result, list)
    assert len(result) == 3


def test_generate_personas_assigns_ids(monkeypatch):
    mock_result = _make_generated_personas(2)
    monkeypatch.setattr(
        "sim_persona_gen.llm_call_json",
        lambda system, user, **kwargs: mock_result,
    )
    result = generate_personas(VALID_IR, 2, "test-model")
    assert result[0]["persona_id"] == "generated-1"
    assert result[1]["persona_id"] == "generated-2"


def test_generate_personas_assigns_type(monkeypatch):
    mock_result = _make_generated_personas(1)
    monkeypatch.setattr(
        "sim_persona_gen.llm_call_json",
        lambda system, user, **kwargs: mock_result,
    )
    result = generate_personas(VALID_IR, 1, "test-model")
    assert result[0]["persona_type"] == "generated"


def test_generate_personas_unwraps_dict_with_personas_key(monkeypatch):
    """LLM may return {"personas": [...]} instead of bare list."""
    inner = _make_generated_personas(2)
    monkeypatch.setattr(
        "sim_persona_gen.llm_call_json",
        lambda system, user, **kwargs: {"personas": inner},
    )
    result = generate_personas(VALID_IR, 2, "test-model")
    assert len(result) == 2


def test_generate_personas_raises_on_non_list(monkeypatch):
    monkeypatch.setattr(
        "sim_persona_gen.llm_call_json",
        lambda system, user, **kwargs: "not a list or dict",
    )
    import pytest
    with pytest.raises(LLMError, match="Expected JSON array"):
        generate_personas(VALID_IR, 1, "test-model")


def test_generate_personas_raises_on_dict_without_personas_key(monkeypatch):
    monkeypatch.setattr(
        "sim_persona_gen.llm_call_json",
        lambda system, user, **kwargs: {"result": "something"},
    )
    import pytest
    with pytest.raises(LLMError, match="Expected JSON array"):
        generate_personas(VALID_IR, 1, "test-model")


# ── load_anchor_personas ──────────────────────────────────────────────────

def test_load_anchor_personas_from_fixtures():
    """Load anchor personas from the explore fixture directory."""
    ir_path = os.path.join(CWD, "fixtures", "sim_compiler", "explore", "reference_ir.json")
    if not os.path.exists(ir_path):
        import pytest
        pytest.skip("explore fixtures not present")
    personas = load_anchor_personas(ir_path, 10)
    assert len(personas) >= 1
    for p in personas:
        errors = validate_persona(p, 0)
        assert errors == [], f"Anchor persona validation errors: {errors}"


def test_load_anchor_personas_respects_count():
    ir_path = os.path.join(CWD, "fixtures", "sim_compiler", "explore", "reference_ir.json")
    if not os.path.exists(ir_path):
        import pytest
        pytest.skip("explore fixtures not present")
    personas = load_anchor_personas(ir_path, 1)
    assert len(personas) == 1


def test_load_anchor_personas_missing_dir():
    with tempfile.TemporaryDirectory() as tmp:
        ir_path = os.path.join(tmp, "ir.json")
        with open(ir_path, "w") as f:
            json.dump(VALID_IR, f)
        import pytest
        with pytest.raises(SystemExit):
            load_anchor_personas(ir_path, 1)


def test_load_anchor_personas_empty_dir():
    with tempfile.TemporaryDirectory() as tmp:
        ir_path = os.path.join(tmp, "ir.json")
        with open(ir_path, "w") as f:
            json.dump(VALID_IR, f)
        os.makedirs(os.path.join(tmp, "personas"))
        import pytest
        with pytest.raises(SystemExit):
            load_anchor_personas(ir_path, 1)


def test_load_anchor_personas_sorted_order():
    """Anchor files are loaded in sorted order."""
    with tempfile.TemporaryDirectory() as tmp:
        ir_path = os.path.join(tmp, "ir.json")
        with open(ir_path, "w") as f:
            json.dump(VALID_IR, f)
        personas_dir = os.path.join(tmp, "personas")
        os.makedirs(personas_dir)

        p1 = {**VALID_PERSONA, "persona_id": "anchor-1"}
        p2 = {**VALID_PERSONA, "persona_id": "anchor-2"}
        with open(os.path.join(personas_dir, "anchor-2.json"), "w") as f:
            json.dump(p2, f)
        with open(os.path.join(personas_dir, "anchor-1.json"), "w") as f:
            json.dump(p1, f)

        result = load_anchor_personas(ir_path, 10)
        assert result[0]["persona_id"] == "anchor-1"
        assert result[1]["persona_id"] == "anchor-2"


# ── Fixture validation ────────────────────────────────────────────────────

def test_all_anchor_fixtures_pass_validation():
    """All hand-authored anchor personas in all skill fixtures pass schema validation."""
    fixtures_dir = os.path.join(CWD, "fixtures", "sim_compiler")
    if not os.path.exists(fixtures_dir):
        import pytest
        pytest.skip("fixtures directory not present")
    found = 0
    for skill in os.listdir(fixtures_dir):
        personas_dir = os.path.join(fixtures_dir, skill, "personas")
        if not os.path.isdir(personas_dir):
            continue
        for fname in sorted(os.listdir(personas_dir)):
            if not fname.startswith("anchor-") or not fname.endswith(".json"):
                continue
            path = os.path.join(personas_dir, fname)
            with open(path) as f:
                persona = json.load(f)
            errors = validate_persona(persona, 0)
            assert errors == [], f"{skill}/{fname} validation errors: {errors}"
            found += 1
    assert found > 0, "Expected at least one anchor persona fixture"


# ── Empty / edge-case inputs ─────────────────────────────────────────────

def test_validate_completely_empty_persona():
    errors = validate_persona({}, 0)
    assert len(errors) >= len(PERSONA_SCHEMA_FIELDS)


def test_validate_persona_index_in_error_message():
    """Error messages include the persona index for debugging."""
    errors = validate_persona({}, 7)
    assert all("persona[7]" in e for e in errors)


def test_hidden_state_required_fields_constant():
    """HIDDEN_STATE_REQUIRED includes all fields that validation checks."""
    assert "goal" in HIDDEN_STATE_REQUIRED
    assert "knowledge" in HIDDEN_STATE_REQUIRED
    for field in HIDDEN_STATE_FIELDS:
        assert field in HIDDEN_STATE_REQUIRED


def test_knowledge_as_levels_maps_all_valid_knowledge():
    """Every valid knowledge level has a mapping in KNOWLEDGE_AS_LEVELS."""
    for k in VALID_KNOWLEDGE:
        assert k in KNOWLEDGE_AS_LEVELS
