"""Tests for scripts/sim_rubric_gen.py — rubric generation, dedup, comparison."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PYTHON = sys.executable
SCRIPT = "scripts/sim_rubric_gen.py"
CWD = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True
).stdout.strip() or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(CWD, "scripts"))
from sim_rubric_gen import (
    UNIVERSAL_DIMENSIONS, RUBRIC_VERSION, _CONCEPT_ALIASES,
    generate_archetype_dimensions, build_rubric, parse_reference_rubric,
    compare_rubric, _concept_overlap,
)
from llm_client import LLMError


# ── Test fixtures ─────────────────────────────────────────────────────────

MINIMAL_IR = {
    "objective": "Help the user explore options.",
    "decision_points": [
        {"location": "Step 1", "decision": "Is topic provided?", "branches": ["Y", "N"]}
    ],
    "ask_nodes": [
        {"location": "Step 1", "question": "What to explore?", "condition": "No topic"}
    ],
    "success_criteria": ["User gets structured report"],
    "failure_criteria": ["No report produced"],
    "interaction_archetype": "intake",
}

SAMPLE_LLM_DIMENSIONS = [
    {"name": "context_depth", "description": "How well context was gathered", "scale_min": 1, "scale_max": 5},
    {"name": "option_diversity", "description": "How diverse the options are", "scale_min": 1, "scale_max": 5},
    {"name": "evidence_grounding", "description": "Are options grounded in evidence?", "scale_min": 1, "scale_max": 5},
]


def _mock_llm_call_json(system, user, *, model=None, temperature=None, max_tokens=None):
    """Return a valid list of archetype dimensions."""
    return SAMPLE_LLM_DIMENSIONS


# ── UNIVERSAL_DIMENSIONS constant tests ───────────────────────────────────

def test_universal_dimensions_count():
    assert len(UNIVERSAL_DIMENSIONS) == 3


def test_universal_dimension_names():
    names = {d["name"] for d in UNIVERSAL_DIMENSIONS}
    assert names == {"task_completion", "register_match", "turn_efficiency"}


def test_universal_dimensions_have_required_keys():
    for dim in UNIVERSAL_DIMENSIONS:
        assert "name" in dim
        assert "description" in dim
        assert "category" in dim
        assert dim["category"] == "universal"
        assert dim["scale_min"] == 1
        assert dim["scale_max"] == 5


# ── generate_archetype_dimensions tests ───────────────────────────────────

def test_generate_archetype_dimensions_returns_list(monkeypatch):
    monkeypatch.setattr("sim_rubric_gen.llm_call_json", _mock_llm_call_json)
    dims = generate_archetype_dimensions(MINIMAL_IR, "test-model")
    assert isinstance(dims, list)
    assert len(dims) == 3


def test_generate_archetype_dimensions_sets_category(monkeypatch):
    monkeypatch.setattr("sim_rubric_gen.llm_call_json", _mock_llm_call_json)
    dims = generate_archetype_dimensions(MINIMAL_IR, "test-model")
    for dim in dims:
        assert dim["category"] == "archetype"


def test_generate_archetype_dimensions_preserves_names(monkeypatch):
    monkeypatch.setattr("sim_rubric_gen.llm_call_json", _mock_llm_call_json)
    dims = generate_archetype_dimensions(MINIMAL_IR, "test-model")
    names = [d["name"] for d in dims]
    assert names == ["context_depth", "option_diversity", "evidence_grounding"]


def test_generate_archetype_dimensions_defaults_scale(monkeypatch):
    """scale_min/scale_max default to 1/5 when missing from LLM response."""
    def mock_no_scale(system, user, *, model=None, temperature=None, max_tokens=None):
        return [{"name": "bare_dim", "description": "No scale provided"}]

    monkeypatch.setattr("sim_rubric_gen.llm_call_json", mock_no_scale)
    dims = generate_archetype_dimensions(MINIMAL_IR, "test-model")
    assert dims[0]["scale_min"] == 1
    assert dims[0]["scale_max"] == 5


def test_generate_archetype_dimensions_rejects_non_array(monkeypatch):
    def mock_non_array(system, user, *, model=None, temperature=None, max_tokens=None):
        return {"not": "an array"}

    monkeypatch.setattr("sim_rubric_gen.llm_call_json", mock_non_array)
    try:
        generate_archetype_dimensions(MINIMAL_IR, "test-model")
        assert False, "Should have raised LLMError"
    except LLMError as e:
        assert "non-array" in str(e)


def test_generate_archetype_dimensions_propagates_llm_error(monkeypatch):
    def mock_error(system, user, *, model=None, temperature=None, max_tokens=None):
        raise LLMError("API timeout", category="timeout")

    monkeypatch.setattr("sim_rubric_gen.llm_call_json", mock_error)
    try:
        generate_archetype_dimensions(MINIMAL_IR, "test-model")
        assert False, "Should have raised LLMError"
    except LLMError as e:
        assert "timeout" in str(e)


# ── build_rubric tests ────────────────────────────────────────────────────

def test_build_rubric_schema(monkeypatch):
    monkeypatch.setattr("sim_rubric_gen.llm_call_json", _mock_llm_call_json)
    rubric = build_rubric(MINIMAL_IR, "test-model")
    assert "rubric_version" in rubric
    assert "interaction_archetype" in rubric
    assert "dimensions" in rubric


def test_build_rubric_version(monkeypatch):
    monkeypatch.setattr("sim_rubric_gen.llm_call_json", _mock_llm_call_json)
    rubric = build_rubric(MINIMAL_IR, "test-model")
    assert rubric["rubric_version"] == RUBRIC_VERSION


def test_build_rubric_archetype_from_ir(monkeypatch):
    monkeypatch.setattr("sim_rubric_gen.llm_call_json", _mock_llm_call_json)
    rubric = build_rubric(MINIMAL_IR, "test-model")
    assert rubric["interaction_archetype"] == "intake"


def test_build_rubric_contains_universal_dimensions(monkeypatch):
    monkeypatch.setattr("sim_rubric_gen.llm_call_json", _mock_llm_call_json)
    rubric = build_rubric(MINIMAL_IR, "test-model")
    dim_names = {d["name"] for d in rubric["dimensions"]}
    assert "task_completion" in dim_names
    assert "register_match" in dim_names
    assert "turn_efficiency" in dim_names


def test_build_rubric_contains_archetype_dimensions(monkeypatch):
    monkeypatch.setattr("sim_rubric_gen.llm_call_json", _mock_llm_call_json)
    rubric = build_rubric(MINIMAL_IR, "test-model")
    dim_names = {d["name"] for d in rubric["dimensions"]}
    assert "context_depth" in dim_names
    assert "option_diversity" in dim_names
    assert "evidence_grounding" in dim_names


def test_build_rubric_dimension_count(monkeypatch):
    monkeypatch.setattr("sim_rubric_gen.llm_call_json", _mock_llm_call_json)
    rubric = build_rubric(MINIMAL_IR, "test-model")
    assert len(rubric["dimensions"]) == 6  # 3 universal + 3 archetype


def test_build_rubric_serializes_to_json(monkeypatch):
    monkeypatch.setattr("sim_rubric_gen.llm_call_json", _mock_llm_call_json)
    rubric = build_rubric(MINIMAL_IR, "test-model")
    serialized = json.dumps(rubric)
    parsed = json.loads(serialized)
    assert parsed["rubric_version"] == RUBRIC_VERSION


# ── _concept_overlap tests (dedup logic) ──────────────────────────────────

def test_concept_overlap_exact_match():
    assert _concept_overlap("task_completion", "task_completion") == 1.0


def test_concept_overlap_no_match():
    assert _concept_overlap("xyz_abc", "def_ghi") == 0.0


def test_concept_overlap_token_overlap():
    assert _concept_overlap("task_quality", "task_speed") == 0.5


def test_concept_overlap_alias_match():
    """register_match and style_tone should match via alias group."""
    assert _concept_overlap("register_match", "style_tone") == 0.5


def test_concept_overlap_alias_flow():
    assert _concept_overlap("flow_quality", "threading_depth") == 0.5


def test_concept_overlap_asymmetric_tokens():
    """No shared tokens and no alias group -> 0.0."""
    assert _concept_overlap("evidence_grounding", "option_diversity") == 0.0


def test_concept_overlap_single_token_dimension():
    """Single-token names still work with token splitting."""
    assert _concept_overlap("flow", "conversation_flow") == 0.5


# ── parse_reference_rubric tests ──────────────────────────────────────────

def test_parse_reference_rubric_extracts_names():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Rubric\n### 1. Task Completion\n### 2. Register Match\n### 3. Flow\n")
        f.flush()
        try:
            names = parse_reference_rubric(f.name)
            assert names == ["task_completion", "register_match", "flow"]
        finally:
            os.unlink(f.name)


def test_parse_reference_rubric_handles_special_chars():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("### 1. Context-Block Quality\n### 2. Hidden Truth Surfacing\n")
        f.flush()
        try:
            names = parse_reference_rubric(f.name)
            assert names == ["context_block_quality", "hidden_truth_surfacing"]
        finally:
            os.unlink(f.name)


def test_parse_reference_rubric_empty_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Just a title\nNo dimensions here.\n")
        f.flush()
        try:
            names = parse_reference_rubric(f.name)
            assert names == []
        finally:
            os.unlink(f.name)


def test_parse_reference_rubric_missing_file():
    """Should sys.exit(1) for missing file."""
    try:
        parse_reference_rubric("/nonexistent/rubric.md")
        assert False, "Should have called sys.exit"
    except SystemExit as e:
        assert e.code == 1


# ── compare_rubric tests ─────────────────────────────────────────────────

def _write_rubric(tmp_dir, filename, rubric_data):
    path = os.path.join(tmp_dir, filename)
    with open(path, "w") as f:
        json.dump(rubric_data, f)
    return path


def _write_reference_md(tmp_dir, filename, dimension_names):
    path = os.path.join(tmp_dir, filename)
    lines = ["# Reference Rubric\n"]
    for i, name in enumerate(dimension_names, 1):
        title = name.replace("_", " ").title()
        lines.append(f"### {i}. {title}\nDescription of {name}.\n")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path


def test_compare_rubric_perfect_match():
    rubric = {
        "dimensions": [
            {"name": "task_completion", "category": "universal"},
            {"name": "register_match", "category": "universal"},
            {"name": "flow", "category": "archetype"},
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        gen = _write_rubric(tmp, "gen.json", rubric)
        ref = _write_reference_md(tmp, "ref.md", ["task_completion", "register_match", "flow"])
        coverage, details = compare_rubric(gen, ref)
        assert coverage == 1.0
        assert all(d["match"] == "exact" for d in details)


def test_compare_rubric_partial_match():
    rubric = {
        "dimensions": [
            {"name": "task_completion", "category": "universal"},
            {"name": "style_tone", "category": "archetype"},  # partial match to register_match
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        gen = _write_rubric(tmp, "gen.json", rubric)
        ref = _write_reference_md(tmp, "ref.md", ["task_completion", "register_match"])
        coverage, details = compare_rubric(gen, ref)
        # task_completion exact (1.0) + register_match partial via alias (0.5) = 1.5/2 = 0.75
        assert 0.5 < coverage < 1.0


def test_compare_rubric_no_match():
    rubric = {
        "dimensions": [
            {"name": "xyz_abc", "category": "archetype"},
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        gen = _write_rubric(tmp, "gen.json", rubric)
        ref = _write_reference_md(tmp, "ref.md", ["task_completion", "register_match"])
        coverage, details = compare_rubric(gen, ref)
        assert coverage == 0.0
        assert all(d["match"] == "missing" for d in details)


def test_compare_rubric_empty_reference():
    rubric = {"dimensions": [{"name": "task_completion", "category": "universal"}]}
    with tempfile.TemporaryDirectory() as tmp:
        gen = _write_rubric(tmp, "gen.json", rubric)
        ref_path = os.path.join(tmp, "ref.md")
        with open(ref_path, "w") as f:
            f.write("# No dimensions\nJust text.\n")
        coverage, details = compare_rubric(gen, ref_path)
        assert coverage == 0.0
        assert details[0]["match"] == "no dimensions found in reference"


def test_compare_rubric_details_structure():
    rubric = {
        "dimensions": [
            {"name": "task_completion", "category": "universal"},
            {"name": "flow", "category": "archetype"},
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        gen = _write_rubric(tmp, "gen.json", rubric)
        ref = _write_reference_md(tmp, "ref.md", ["task_completion", "flow"])
        coverage, details = compare_rubric(gen, ref)
        for d in details:
            assert "reference" in d
            assert "match" in d
            assert "weight" in d


# ── CLI tests ─────────────────────────────────────────────────────────────

def test_cli_compare_rubric_pass():
    rubric = {
        "dimensions": [
            {"name": "task_completion", "category": "universal"},
            {"name": "register_match", "category": "universal"},
            {"name": "flow", "category": "archetype"},
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        gen = _write_rubric(tmp, "gen.json", rubric)
        ref = _write_reference_md(tmp, "ref.md", ["task_completion", "register_match", "flow"])
        result = subprocess.run(
            [PYTHON, SCRIPT, "--compare-rubric", gen, ref],
            capture_output=True, text=True, cwd=CWD,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["passed"] is True
        assert output["coverage"] == 1.0


def test_cli_compare_rubric_fail():
    rubric = {
        "dimensions": [
            {"name": "xyz_abc", "category": "archetype"},
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        gen = _write_rubric(tmp, "gen.json", rubric)
        ref = _write_reference_md(tmp, "ref.md", ["task_completion", "register_match", "flow"])
        result = subprocess.run(
            [PYTHON, SCRIPT, "--compare-rubric", gen, ref],
            capture_output=True, text=True, cwd=CWD,
        )
        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert output["passed"] is False
        assert output["coverage"] < 0.80


def test_cli_missing_ir_arg():
    """CLI with no --ir and no --compare-rubric should error."""
    result = subprocess.run(
        [PYTHON, SCRIPT],
        capture_output=True, text=True, cwd=CWD,
    )
    assert result.returncode != 0


# ── load_ir negative tests ────────────────────────────────────────────────

def test_load_ir_missing_file():
    """load_ir sys.exit(1) for missing file."""
    from sim_rubric_gen import load_ir
    try:
        load_ir("/nonexistent/ir.json")
        assert False, "Should have called sys.exit"
    except SystemExit as e:
        assert e.code == 1


def test_load_ir_missing_fields():
    """load_ir sys.exit(1) when required fields are absent."""
    from sim_rubric_gen import load_ir
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"objective": "test"}, f)
        f.flush()
        try:
            load_ir(f.name)
            assert False, "Should have called sys.exit"
        except SystemExit as e:
            assert e.code == 1
        finally:
            os.unlink(f.name)


def test_load_ir_valid():
    from sim_rubric_gen import load_ir
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(MINIMAL_IR, f)
        f.flush()
        try:
            ir = load_ir(f.name)
            assert ir["objective"] == MINIMAL_IR["objective"]
            assert ir["interaction_archetype"] == "intake"
        finally:
            os.unlink(f.name)


# ── _CONCEPT_ALIASES coverage ─────────────────────────────────────────────

def test_concept_aliases_keys_are_strings():
    for key in _CONCEPT_ALIASES:
        assert isinstance(key, str)


def test_concept_aliases_values_are_sets():
    for key, val in _CONCEPT_ALIASES.items():
        assert isinstance(val, set)
        assert len(val) > 0
