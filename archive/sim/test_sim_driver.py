"""Tests for scripts/sim_driver.py — 3-agent simulation loop."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

PYTHON = sys.executable
CWD = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True
).stdout.strip() or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(CWD, "scripts"))
from sim_driver import (
    check_termination, build_executor_system, build_persona_system,
    build_judge_system, run_simulation, COMPLETION_SIGNALS, ABANDONMENT_SIGNALS,
)
from sim_persona_gen import validate_persona
from sim_rubric_gen import UNIVERSAL_DIMENSIONS


# ── Test fixtures ──────────────────────────────────────────────────────────

SAMPLE_SKILL_CONTENT = """# Test Skill
## Procedure
### Step 1: Ask the user what they need
### Step 2: Provide the answer
### Step 3: Confirm satisfaction
"""

SAMPLE_PERSONA = {
    "persona_id": "test-1",
    "persona_type": "anchor",
    "hidden_state": {
        "goal": "Get help with a test task",
        "knowledge": "intermediate",
        "urgency": "medium",
        "patience": "high",
        "trust": "medium",
        "cooperativeness": "high"
    },
    "opening_input": "I need help with testing",
    "behavioral_rules": "Be cooperative and answer questions directly."
}

SAMPLE_RUBRIC = {
    "rubric_version": "0.1.0-pilot",
    "interaction_archetype": "intake",
    "dimensions": [
        {
            "name": "task_completion",
            "description": "Did the skill accomplish its stated objective?",
            "category": "universal",
            "scale_min": 1,
            "scale_max": 5,
        },
        {
            "name": "register_match",
            "description": "Did the skill match the user's register?",
            "category": "universal",
            "scale_min": 1,
            "scale_max": 5,
        },
        {
            "name": "turn_efficiency",
            "description": "Was the interaction concise?",
            "category": "universal",
            "scale_min": 1,
            "scale_max": 5,
        },
    ]
}


# ── check_termination tests ───────────────────────────────────────────────

def test_completion_signal_detected():
    for signal in COMPLETION_SIGNALS:
        should_stop, reason, status = check_termination(
            f"Here is the result. {signal}", "thanks", 1, 15
        )
        assert should_stop is True, f"Signal '{signal}' not detected"
        assert status == "success"


def test_abandonment_signal_detected():
    for signal in ABANDONMENT_SIGNALS:
        should_stop, reason, status = check_termination(
            "How can I help?", signal, 1, 15
        )
        assert should_stop is True, f"Abandonment '{signal}' not detected"
        assert status == "abandoned"


def test_blocked_signal():
    should_stop, reason, status = check_termination(
        "[BLOCKED] Need file access", "ok", 1, 15
    )
    assert should_stop is True
    assert status == "blocked_environment"


def test_max_turns_reached():
    should_stop, reason, status = check_termination(
        "Here's my analysis", "thanks", 15, 15
    )
    assert should_stop is True
    assert status == "max_turns"


def test_no_termination():
    should_stop, reason, status = check_termination(
        "What's your budget?", "About $5000", 3, 15
    )
    assert should_stop is False
    assert reason is None
    assert status is None


def test_abandonment_case_insensitive():
    should_stop, _, status = check_termination(
        "Can you tell me more?", "I'M DONE", 2, 15
    )
    assert should_stop is True
    assert status == "abandoned"


def test_none_persona_response():
    """Persona response can be None (e.g., first turn check)."""
    should_stop, _, _ = check_termination(
        "Welcome! How can I help?", None, 1, 15
    )
    assert should_stop is False


# ── System prompt builder tests ────────────────────────────────────────────

def test_executor_system_contains_skill():
    prompt = build_executor_system(SAMPLE_SKILL_CONTENT, "test-skill")
    assert "test-skill" in prompt
    assert "Step 1" in prompt
    assert "[COMPLETE]" in prompt
    assert "[BLOCKED]" in prompt


def test_persona_system_contains_hidden_state():
    prompt = build_persona_system(SAMPLE_PERSONA)
    assert "intermediate" in prompt
    assert "medium" in prompt
    assert "cooperative" in prompt.lower() or "cooperativeness" in prompt.lower()


def test_persona_system_does_not_contain_skill():
    """Persona must NOT see skill procedure (data leakage prevention)."""
    prompt = build_persona_system(SAMPLE_PERSONA)
    assert "SKILL PROCEDURE" not in prompt
    assert "Step 1: Ask the user" not in prompt


def test_judge_system_contains_dimensions():
    prompt = build_judge_system(SAMPLE_RUBRIC)
    assert "task_completion" in prompt
    assert "register_match" in prompt
    assert "turn_efficiency" in prompt


# ── run_simulation tests (mocked LLM) ─────────────────────────────────────

def _mock_llm_call(system, user, *, model=None, temperature=None, timeout=None):
    """Simple mock that returns different responses based on system prompt content."""
    if "executing the BuildOS skill" in system:
        # Executor — complete after first response
        return "I can help with that. Let me analyze your request.\n\n[COMPLETE]\n\n## Output\nHere is your result."
    elif "playing a user" in system:
        # Persona
        return "Thanks, that looks good."
    return "Generic response"


def _mock_llm_call_json(system, user, *, model=None, temperature=None, timeout=None):
    """Mock for judge calls."""
    return {
        "scores": {"task_completion": 4, "register_match": 4, "turn_efficiency": 5},
        "rationale": "Good interaction. Executor completed efficiently.",
        "objective_achieved": True,
    }


@patch("sim_driver.llm_call", side_effect=_mock_llm_call)
@patch("sim_driver.llm_call_json", side_effect=_mock_llm_call_json)
def test_simulation_completes(mock_json, mock_call):
    result = run_simulation(
        skill_name="test",
        skill_content=SAMPLE_SKILL_CONTENT,
        persona_card=SAMPLE_PERSONA,
        rubric=SAMPLE_RUBRIC,
        executor_model="claude-opus-4-6",
        persona_model="gemini-3.1-pro",
        judge_model="gpt-5.4",
        max_turns=15,
    )
    assert result["final_status"] == "success"
    assert result["objective_achieved"] is True
    assert result["skill"] == "test"
    assert len(result["transcript"]) >= 2  # opening + at least 1 executor turn
    assert result["judge_scores"]["task_completion"] == 4


@patch("sim_driver.llm_call", side_effect=_mock_llm_call)
@patch("sim_driver.llm_call_json", side_effect=_mock_llm_call_json)
def test_simulation_dry_run(mock_json, mock_call):
    result = run_simulation(
        skill_name="test",
        skill_content=SAMPLE_SKILL_CONTENT,
        persona_card=SAMPLE_PERSONA,
        rubric=SAMPLE_RUBRIC,
        executor_model="claude-opus-4-6",
        persona_model="gemini-3.1-pro",
        judge_model="gpt-5.4",
        max_turns=15,
        dry_run=True,
    )
    assert result["final_status"] == "dry_run"
    assert result["judge_scores"] == {}  # judge skipped in dry-run


def _mock_llm_call_no_completion(system, user, *, model=None, temperature=None, timeout=None):
    """Executor that never signals completion."""
    if "executing the BuildOS skill" in system:
        return "Let me ask you another question. What else do you need?"
    elif "playing a user" in system:
        return "I also need help with X."
    return "Generic response"


@patch("sim_driver.llm_call", side_effect=_mock_llm_call_no_completion)
@patch("sim_driver.llm_call_json", side_effect=_mock_llm_call_json)
def test_simulation_hits_max_turns(mock_json, mock_call):
    result = run_simulation(
        skill_name="test",
        skill_content=SAMPLE_SKILL_CONTENT,
        persona_card=SAMPLE_PERSONA,
        rubric=SAMPLE_RUBRIC,
        executor_model="claude-opus-4-6",
        persona_model="gemini-3.1-pro",
        judge_model="gpt-5.4",
        max_turns=3,
    )
    assert result["final_status"] == "max_turns"
    assert "3" in result["termination_reason"]


def _mock_llm_call_blocked(system, user, *, model=None, temperature=None, timeout=None):
    """Executor that hits a block."""
    if "executing the BuildOS skill" in system:
        return "[BLOCKED] I need access to the filesystem to proceed."
    elif "playing a user" in system:
        return "OK"
    return "Generic response"


@patch("sim_driver.llm_call", side_effect=_mock_llm_call_blocked)
@patch("sim_driver.llm_call_json", side_effect=_mock_llm_call_json)
def test_simulation_blocked(mock_json, mock_call):
    result = run_simulation(
        skill_name="test",
        skill_content=SAMPLE_SKILL_CONTENT,
        persona_card=SAMPLE_PERSONA,
        rubric=SAMPLE_RUBRIC,
        executor_model="claude-opus-4-6",
        persona_model="gemini-3.1-pro",
        judge_model="gpt-5.4",
        max_turns=15,
    )
    assert result["final_status"] == "blocked_environment"


def _mock_llm_call_persona_abandons(system, user, *, model=None, temperature=None, timeout=None):
    """Persona that abandons."""
    if "executing the BuildOS skill" in system:
        return "Let me help you with that. What's your goal?"
    elif "playing a user" in system:
        return "forget it, this isn't working"
    return "Generic response"


@patch("sim_driver.llm_call", side_effect=_mock_llm_call_persona_abandons)
@patch("sim_driver.llm_call_json", side_effect=_mock_llm_call_json)
def test_simulation_persona_abandons(mock_json, mock_call):
    result = run_simulation(
        skill_name="test",
        skill_content=SAMPLE_SKILL_CONTENT,
        persona_card=SAMPLE_PERSONA,
        rubric=SAMPLE_RUBRIC,
        executor_model="claude-opus-4-6",
        persona_model="gemini-3.1-pro",
        judge_model="gpt-5.4",
        max_turns=15,
    )
    assert result["final_status"] == "abandoned"


# ── LLM error handling ────────────────────────────────────────────────────

from llm_client import LLMError

def _mock_llm_call_executor_error(system, user, *, model=None, temperature=None, timeout=None):
    if "executing the BuildOS skill" in system:
        raise LLMError("Connection timeout", category="timeout")
    elif "playing a user" in system:
        return "Hi"
    return "Generic"


@patch("sim_driver.llm_call", side_effect=_mock_llm_call_executor_error)
@patch("sim_driver.llm_call_json", side_effect=_mock_llm_call_json)
def test_simulation_executor_error(mock_json, mock_call):
    result = run_simulation(
        skill_name="test",
        skill_content=SAMPLE_SKILL_CONTENT,
        persona_card=SAMPLE_PERSONA,
        rubric=SAMPLE_RUBRIC,
        executor_model="claude-opus-4-6",
        persona_model="gemini-3.1-pro",
        judge_model="gpt-5.4",
        max_turns=15,
    )
    assert result["final_status"] == "failure"
    assert "timeout" in result["termination_reason"].lower() or "error" in result["termination_reason"].lower()


# ── Output schema validation ──────────────────────────────────────────────

REQUIRED_RESULT_FIELDS = [
    "run_id", "timestamp", "simulator_version", "skill",
    "persona_state", "execution_config", "transcript",
    "final_status", "termination_reason", "objective_achieved",
    "judge_scores", "judge_rationale", "rubric_metadata",
]


@patch("sim_driver.llm_call", side_effect=_mock_llm_call)
@patch("sim_driver.llm_call_json", side_effect=_mock_llm_call_json)
def test_output_schema_has_all_fields(mock_json, mock_call):
    result = run_simulation(
        skill_name="test",
        skill_content=SAMPLE_SKILL_CONTENT,
        persona_card=SAMPLE_PERSONA,
        rubric=SAMPLE_RUBRIC,
        executor_model="claude-opus-4-6",
        persona_model="gemini-3.1-pro",
        judge_model="gpt-5.4",
        max_turns=15,
    )
    for field in REQUIRED_RESULT_FIELDS:
        assert field in result, f"Missing output field: {field}"


@patch("sim_driver.llm_call", side_effect=_mock_llm_call)
@patch("sim_driver.llm_call_json", side_effect=_mock_llm_call_json)
def test_output_serializes_to_json(mock_json, mock_call):
    """Result must be JSON-serializable for JSONL output."""
    result = run_simulation(
        skill_name="test",
        skill_content=SAMPLE_SKILL_CONTENT,
        persona_card=SAMPLE_PERSONA,
        rubric=SAMPLE_RUBRIC,
        executor_model="claude-opus-4-6",
        persona_model="gemini-3.1-pro",
        judge_model="gpt-5.4",
        max_turns=15,
    )
    serialized = json.dumps(result)
    parsed = json.loads(serialized)
    assert parsed["run_id"] == result["run_id"]


@patch("sim_driver.llm_call", side_effect=_mock_llm_call)
@patch("sim_driver.llm_call_json", side_effect=_mock_llm_call_json)
def test_transcript_entries_have_required_fields(mock_json, mock_call):
    result = run_simulation(
        skill_name="test",
        skill_content=SAMPLE_SKILL_CONTENT,
        persona_card=SAMPLE_PERSONA,
        rubric=SAMPLE_RUBRIC,
        executor_model="claude-opus-4-6",
        persona_model="gemini-3.1-pro",
        judge_model="gpt-5.4",
        max_turns=15,
    )
    for entry in result["transcript"]:
        assert "turn" in entry
        assert "role" in entry
        assert "content" in entry
        assert "timestamp" in entry
        assert entry["role"] in ("persona", "executor", "system")


@patch("sim_driver.llm_call", side_effect=_mock_llm_call)
@patch("sim_driver.llm_call_json", side_effect=_mock_llm_call_json)
def test_execution_config_recorded(mock_json, mock_call):
    result = run_simulation(
        skill_name="test",
        skill_content=SAMPLE_SKILL_CONTENT,
        persona_card=SAMPLE_PERSONA,
        rubric=SAMPLE_RUBRIC,
        executor_model="claude-opus-4-6",
        persona_model="gemini-3.1-pro",
        judge_model="gpt-5.4",
        max_turns=10,
    )
    cfg = result["execution_config"]
    assert cfg["executor_model"] == "claude-opus-4-6"
    assert cfg["persona_model"] == "gemini-3.1-pro"
    assert cfg["judge_model"] == "gpt-5.4"
    assert cfg["max_turns"] == 10


# ── Persona fixture validation ─────────────────────────────────────────────

def test_anchor_personas_valid():
    """All hand-authored anchor personas pass schema validation."""
    fixtures_dir = os.path.join(CWD, "fixtures", "sim_compiler")
    for skill in ["explore", "investigate", "plan"]:
        personas_dir = os.path.join(fixtures_dir, skill, "personas")
        if not os.path.exists(personas_dir):
            continue
        for fname in sorted(os.listdir(personas_dir)):
            if not fname.startswith("anchor-") or not fname.endswith(".json"):
                continue
            path = os.path.join(personas_dir, fname)
            with open(path) as f:
                persona = json.load(f)
            errors = validate_persona(persona, 0)
            assert errors == [], f"{skill}/{fname} validation errors: {errors}"


# ── Information-asymmetry invariant tests ─────────────────────────────────

# Realistic persona card with hidden_truth for asymmetry tests
ASYMMETRY_PERSONA = {
    "persona_id": "anchor-1",
    "persona_type": "anchor",
    "hidden_state": {
        "goal": "Evaluate whether to rebuild their mobile app's native modules or migrate to a cross-platform framework",
        "knowledge": "expert",
        "urgency": "high",
        "patience": "low",
        "trust": "medium",
        "cooperativeness": "low",
        "hidden_truth": "The real driver is that two senior iOS developers just quit and hiring replacements would take 6 months"
    },
    "opening_input": "thinking about rebuilding our mobile stack",
    "behavioral_rules": "Gives short answers (5-15 words). Won't elaborate unless given options. Has a hidden assumption that a full rebuild is the only path."
}

ASYMMETRY_RUBRIC = {
    "rubric_version": "0.1.0-pilot",
    "interaction_archetype": "intake",
    "dimensions": [
        {
            "name": "task_completion",
            "description": "Did the skill accomplish its stated objective?",
            "category": "universal",
            "scale_min": 1,
            "scale_max": 5,
        },
        {
            "name": "hidden_truth_surfacing",
            "description": "Did the skill surface the hidden truth the persona is withholding?",
            "category": "archetype",
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
}

ASYMMETRY_SKILL_CONTENT = """# Explore Skill
## Procedure
### Step 1: Ask what question the user wants to explore
### Step 2: Pre-flight discovery — ask 2-4 questions to understand context
### Step 3: Generate 3+ divergent directions via cross-model synthesis
### Step 4: Present directions with evidence and trade-offs
"""


def test_executor_prompt_contains_skill_not_hidden_state():
    """Executor sees skill procedure but NOT persona hidden state."""
    prompt = build_executor_system(ASYMMETRY_SKILL_CONTENT, "explore")
    # Executor MUST see the skill procedure
    assert "Pre-flight discovery" in prompt
    assert "divergent directions" in prompt
    assert "explore" in prompt
    # Executor MUST NOT see any hidden_state fields
    assert "hidden_truth" not in prompt
    assert "two senior iOS developers just quit" not in prompt
    assert ASYMMETRY_PERSONA["hidden_state"]["goal"] not in prompt
    assert "cooperativeness" not in prompt
    assert "patience" not in prompt
    assert "urgency" not in prompt


def test_executor_prompt_excludes_hidden_truth_value():
    """Executor prompt must not contain the actual hidden_truth string."""
    prompt = build_executor_system(ASYMMETRY_SKILL_CONTENT, "explore")
    hidden_truth = ASYMMETRY_PERSONA["hidden_state"]["hidden_truth"]
    assert hidden_truth not in prompt
    # Also check partial matches
    assert "iOS developers just quit" not in prompt
    assert "hiring replacements" not in prompt


def test_persona_prompt_contains_hidden_state():
    """Persona sees their own card including hidden_state fields."""
    prompt = build_persona_system(ASYMMETRY_PERSONA)
    assert "expert" in prompt  # knowledge
    assert "high" in prompt  # urgency
    assert "low" in prompt  # patience
    assert "medium" in prompt  # trust


def test_persona_prompt_excludes_skill_procedure():
    """Persona must NOT see the skill procedure."""
    prompt = build_persona_system(ASYMMETRY_PERSONA)
    assert "SKILL PROCEDURE" not in prompt
    assert "Pre-flight discovery" not in prompt
    assert "divergent directions" not in prompt
    assert "cross-model synthesis" not in prompt


def test_persona_prompt_excludes_rubric():
    """Persona must NOT see rubric dimensions or scoring criteria."""
    prompt = build_persona_system(ASYMMETRY_PERSONA)
    assert "hidden_truth_surfacing" not in prompt
    assert "task_completion" not in prompt
    assert "turn_efficiency" not in prompt
    assert "SCORING DIMENSIONS" not in prompt
    assert "scale_min" not in prompt
    assert "scale_max" not in prompt


def test_judge_prompt_contains_rubric_not_hidden_state():
    """Judge sees rubric dimensions but NOT persona hidden state."""
    prompt = build_judge_system(ASYMMETRY_RUBRIC)
    # Judge MUST see rubric dimensions
    assert "task_completion" in prompt
    assert "hidden_truth_surfacing" in prompt
    assert "turn_efficiency" in prompt
    # Judge MUST NOT see hidden_state fields
    assert "two senior iOS developers just quit" not in prompt
    assert ASYMMETRY_PERSONA["hidden_state"]["goal"] not in prompt
    assert "cooperativeness" not in prompt
    assert "patience" not in prompt


def test_judge_prompt_excludes_hidden_truth_value():
    """Judge prompt must not contain the actual hidden_truth string."""
    prompt = build_judge_system(ASYMMETRY_RUBRIC)
    hidden_truth = ASYMMETRY_PERSONA["hidden_state"]["hidden_truth"]
    assert hidden_truth not in prompt


def test_judge_prompt_excludes_skill_procedure():
    """Judge must NOT see the skill procedure (only rubric + transcript)."""
    prompt = build_judge_system(ASYMMETRY_RUBRIC)
    assert "SKILL PROCEDURE" not in prompt
    assert "Pre-flight discovery" not in prompt
    assert "divergent directions" not in prompt


def test_executor_and_persona_have_disjoint_knowledge():
    """Executor and persona prompts share no domain-specific content."""
    executor_prompt = build_executor_system(ASYMMETRY_SKILL_CONTENT, "explore")
    persona_prompt = build_persona_system(ASYMMETRY_PERSONA)
    # Skill content should not appear in persona prompt
    for phrase in ["Pre-flight discovery", "divergent directions", "cross-model synthesis"]:
        assert phrase in executor_prompt
        assert phrase not in persona_prompt
    # Hidden state values should not appear in executor prompt
    for field_val in ["cooperativeness", "patience", "urgency"]:
        assert field_val in persona_prompt.lower()
        assert field_val not in executor_prompt.lower()
