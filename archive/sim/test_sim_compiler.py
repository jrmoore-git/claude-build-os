"""Tests for scripts/sim_compiler.py — IR extraction, validation, and comparison."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

PYTHON = sys.executable
SCRIPT = "scripts/sim_compiler.py"
CWD = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True
).stdout.strip() or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add scripts to path for direct imports
sys.path.insert(0, os.path.join(CWD, "scripts"))
from sim_compiler import validate_ir, compare_ir, VALID_ARCHETYPES, _compare_text_field, _compare_list_coverage, _compare_criteria_list


# ── Minimal valid IR for testing ────────────────────────────────────────────

VALID_IR = {
    "objective": "Help the user explore options and produce a structured exploration report.",
    "decision_points": [
        {
            "location": "Step 1",
            "decision": "Is a topic provided?",
            "branches": ["Yes — use it", "No — ask user"]
        }
    ],
    "ask_nodes": [
        {
            "location": "Step 1",
            "question": "What do you want to explore?",
            "condition": "Only if topic not provided"
        }
    ],
    "success_criteria": ["User receives a structured report"],
    "failure_criteria": ["No report produced"],
    "interaction_archetype": "intake"
}


# ── validate_ir tests ──────────────────────────────────────────────────────

def test_valid_ir_passes():
    errors = validate_ir(VALID_IR)
    assert errors == []


def test_missing_required_field():
    ir = {k: v for k, v in VALID_IR.items() if k != "objective"}
    errors = validate_ir(ir)
    assert any("Missing required field: objective" in e for e in errors)


def test_missing_multiple_fields():
    ir = {"objective": "test"}
    errors = validate_ir(ir)
    missing_fields = [e for e in errors if "Missing required field" in e]
    assert len(missing_fields) == 5  # all except objective


def test_invalid_archetype():
    ir = {**VALID_IR, "interaction_archetype": "unknown_type"}
    errors = validate_ir(ir)
    assert any("interaction_archetype" in e for e in errors)


def test_all_valid_archetypes():
    for archetype in VALID_ARCHETYPES:
        ir = {**VALID_IR, "interaction_archetype": archetype}
        errors = validate_ir(ir)
        assert errors == [], f"Archetype '{archetype}' should be valid but got: {errors}"


def test_objective_must_be_string():
    ir = {**VALID_IR, "objective": 42}
    errors = validate_ir(ir)
    assert any("'objective' must be a string" in e for e in errors)


def test_decision_points_must_be_list():
    ir = {**VALID_IR, "decision_points": "not a list"}
    errors = validate_ir(ir)
    assert any("'decision_points' must be a list" in e for e in errors)


def test_decision_point_missing_keys():
    ir = {**VALID_IR, "decision_points": [{"location": "Step 1"}]}
    errors = validate_ir(ir)
    assert any("decision" in e for e in errors)
    assert any("branches" in e for e in errors)


def test_ask_nodes_must_be_list():
    ir = {**VALID_IR, "ask_nodes": "not a list"}
    errors = validate_ir(ir)
    assert any("'ask_nodes' must be a list" in e for e in errors)


def test_ask_node_missing_question():
    ir = {**VALID_IR, "ask_nodes": [{"location": "Step 1"}]}
    errors = validate_ir(ir)
    assert any("question" in e for e in errors)


def test_criteria_must_be_list():
    ir = {**VALID_IR, "success_criteria": "not a list"}
    errors = validate_ir(ir)
    assert any("'success_criteria' must be a list" in e for e in errors)


# ── compare_ir tests ───────────────────────────────────────────────────────

def _write_ir(tmp_dir, filename, ir_data):
    path = os.path.join(tmp_dir, filename)
    with open(path, "w") as f:
        json.dump(ir_data, f)
    return path


def test_compare_identical_ir():
    with tempfile.TemporaryDirectory() as tmp:
        ref = _write_ir(tmp, "ref.json", VALID_IR)
        ext = _write_ir(tmp, "ext.json", VALID_IR)
        result = compare_ir(ref, ext)
        assert result["all_pass"] is True
        assert result["summary"]["pass"] == 6
        assert result["summary"]["fail"] == 0


def test_compare_mismatched_archetype():
    modified = {**VALID_IR, "interaction_archetype": "diagnosis"}
    with tempfile.TemporaryDirectory() as tmp:
        ref = _write_ir(tmp, "ref.json", VALID_IR)
        ext = _write_ir(tmp, "ext.json", modified)
        result = compare_ir(ref, ext)
        assert result["checklist"]["interaction_archetype"]["rating"] == "fail"


def test_compare_missing_decision_points():
    modified = {**VALID_IR, "decision_points": []}
    with tempfile.TemporaryDirectory() as tmp:
        ref = _write_ir(tmp, "ref.json", VALID_IR)
        ext = _write_ir(tmp, "ext.json", modified)
        result = compare_ir(ref, ext)
        assert result["checklist"]["decision_points"]["rating"] == "fail"


def test_compare_partial_coverage():
    """Extracted IR has some but not all reference decision points."""
    ref_ir = {
        **VALID_IR,
        "decision_points": [
            {"location": "Step 1", "decision": "Is topic provided?", "branches": ["Y", "N"]},
            {"location": "Step 2", "decision": "Is context sufficient?", "branches": ["Y", "N"]},
            {"location": "Step 3", "decision": "Should we expand scope?", "branches": ["Y", "N"]},
        ]
    }
    ext_ir = {
        **VALID_IR,
        "decision_points": [
            {"location": "Step 1", "decision": "Is topic provided?", "branches": ["Y", "N"]},
            {"location": "Step 2", "decision": "Is context sufficient?", "branches": ["Y", "N"]},
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        ref = _write_ir(tmp, "ref.json", ref_ir)
        ext = _write_ir(tmp, "ext.json", ext_ir)
        result = compare_ir(ref, ext)
        dp = result["checklist"]["decision_points"]
        # 2/3 = 66% — partial
        assert dp["rating"] == "partial"


# ── _compare_text_field tests ──────────────────────────────────────────────

def test_text_field_both_empty():
    result = _compare_text_field("", "", "test")
    assert result["rating"] == "pass"


def test_text_field_extracted_empty():
    result = _compare_text_field("some objective", "", "test")
    assert result["rating"] == "fail"


def test_text_field_high_overlap():
    result = _compare_text_field(
        "structured exploration report for user",
        "produce a structured exploration report",
        "test"
    )
    assert result["rating"] == "pass"


# ── _compare_criteria_list tests ───────────────────────────────────────────

def test_criteria_full_coverage():
    ref = ["plan artifact has valid YAML", "build order specified", "user approval required"]
    ext = ["YAML frontmatter valid in plan", "build order with dependencies", "user must approve plan"]
    result = _compare_criteria_list(ref, ext, "test")
    assert result["rating"] == "pass"


def test_criteria_no_coverage():
    ref = ["plan artifact has valid YAML", "build order specified"]
    ext = ["completely different criterion about testing"]
    result = _compare_criteria_list(ref, ext, "test")
    assert result["rating"] == "fail"


def test_criteria_empty_reference():
    result = _compare_criteria_list([], ["anything"], "test")
    assert result["rating"] == "pass"


# ── CLI tests ──────────────────────────────────────────────────────────────

def test_cli_compare_identical():
    """CLI --compare with identical files returns exit 0."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_ir(tmp, "ir.json", VALID_IR)
        result = subprocess.run(
            [PYTHON, SCRIPT, "--compare", path, path],
            capture_output=True, text=True, cwd=CWD,
        )
        assert result.returncode == 0
        assert "GATE: PASS" in result.stderr


def test_cli_compare_mismatched():
    """CLI --compare with mismatched archetype returns exit 1."""
    modified = {**VALID_IR, "interaction_archetype": "diagnosis"}
    with tempfile.TemporaryDirectory() as tmp:
        ref = _write_ir(tmp, "ref.json", VALID_IR)
        ext = _write_ir(tmp, "ext.json", modified)
        result = subprocess.run(
            [PYTHON, SCRIPT, "--compare", ref, ext],
            capture_output=True, text=True, cwd=CWD,
        )
        assert result.returncode == 1
        assert "GATE: FAIL" in result.stderr


def test_cli_missing_skill_arg():
    """CLI with no --skill and no --compare should error."""
    result = subprocess.run(
        [PYTHON, SCRIPT],
        capture_output=True, text=True, cwd=CWD,
    )
    assert result.returncode != 0


def test_cli_compare_missing_file():
    """CLI --compare with nonexistent file returns exit 1."""
    result = subprocess.run(
        [PYTHON, SCRIPT, "--compare", "/nonexistent/ref.json", "/nonexistent/ext.json"],
        capture_output=True, text=True, cwd=CWD,
    )
    assert result.returncode == 1
    assert "not found" in result.stderr


# ── Reference IR fixture validation ────────────────────────────────────────

def test_reference_irs_valid():
    """All hand-authored reference IRs pass schema validation."""
    fixtures_dir = os.path.join(CWD, "fixtures", "sim_compiler")
    for skill in ["explore", "investigate", "plan"]:
        path = os.path.join(fixtures_dir, skill, "reference_ir.json")
        if not os.path.exists(path):
            continue
        with open(path) as f:
            ir = json.load(f)
        errors = validate_ir(ir)
        assert errors == [], f"{skill}/reference_ir.json validation errors: {errors}"
