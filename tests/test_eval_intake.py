"""Unit tests for scripts/eval_intake.py.

Tests pure functions: extract_opening_input, format_output, prompt builders.
Does NOT test actual LLM conversation loops.
"""

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import eval_intake  # noqa: E402


# ── extract_opening_input ──────────────────────────────────────────────────


class TestExtractOpeningInput:
    def test_basic_extraction(self):
        persona = """# Test Persona

## Background
Some background.

## Opening Input
"I'm thinking about pivoting from B2B to consumer"

## Behavior
Short answers.
"""
        result = eval_intake.extract_opening_input(persona)
        assert result == "I'm thinking about pivoting from B2B to consumer"

    def test_single_quotes(self):
        persona = """## Opening Input
'We need to decide on our tech stack'

## Behavior
"""
        result = eval_intake.extract_opening_input(persona)
        assert result == "We need to decide on our tech stack"

    def test_no_quotes(self):
        persona = """## Opening Input
Just plain text here

## Behavior
"""
        result = eval_intake.extract_opening_input(persona)
        assert result == "Just plain text here"

    def test_missing_section(self):
        persona = """# Persona
## Background
No opening input section.
"""
        result = eval_intake.extract_opening_input(persona)
        assert result is None

    def test_empty_section(self):
        persona = """## Opening Input
## Behavior
Next section immediately.
"""
        result = eval_intake.extract_opening_input(persona)
        assert result is None

    def test_skips_blank_lines(self):
        persona = """## Opening Input

"After the blank line"

## Behavior
"""
        result = eval_intake.extract_opening_input(persona)
        assert result == "After the blank line"


# ── format_output ──────────────────────────────────────────────────────────


class TestFormatOutput:
    def test_basic_format(self):
        transcript = [
            ("PERSONA", "I need help with X"),
            ("INTERVIEWER", "What makes X hard?"),
            ("PERSONA", "It's complex because Y"),
        ]
        context_block = "PROBLEM: X is hard\nSITUATION:\n- Y exists"
        judge_parsed = {
            "scores": {
                "register": {"score": 4, "evidence": "Matched tone"},
                "flow": {"score": 3, "evidence": "Okay flow"},
            },
            "average": 3.5,
            "pass": True,
            "hidden_truth_surfaced": True,
            "summary": "Good intake.",
        }
        output = eval_intake.format_output(
            "test-persona", transcript, context_block, judge_parsed, ""
        )
        assert "# Intake Eval: test-persona" in output
        assert "## Transcript" in output
        assert "I need help with X" in output
        assert "What makes X hard?" in output
        assert "## Context Block" in output
        assert "PROBLEM: X is hard" in output
        assert "## Judge Evaluation" in output
        assert "register" in output
        assert "4/5" in output
        assert "Pass: True" in output

    def test_no_context_block(self):
        output = eval_intake.format_output(
            "test", [("PERSONA", "hi")], None, None, "Raw judge text"
        )
        assert "No context block composed" in output
        assert "Raw judge text" in output

    def test_no_judge_parsed(self):
        output = eval_intake.format_output(
            "test", [("PERSONA", "hi")], "Some context", None, "Unparseable judge output"
        )
        assert "Could not parse" in output
        assert "Unparseable judge output" in output

    def test_simple_score_format(self):
        """Scores can be plain numbers instead of dicts."""
        judge_parsed = {
            "scores": {"register": 4, "flow": 3},
            "average": 3.5,
            "pass": True,
            "hidden_truth_surfaced": False,
        }
        output = eval_intake.format_output(
            "test", [("PERSONA", "hi")], "ctx", judge_parsed, ""
        )
        assert "4/5" in output
        assert "3/5" in output

    def test_pipe_in_evidence_escaped(self):
        """Pipe characters in evidence should be escaped for markdown tables."""
        judge_parsed = {
            "scores": {
                "register": {"score": 4, "evidence": "A | B comparison"},
            },
            "average": 4.0,
            "pass": True,
            "hidden_truth_surfaced": True,
        }
        output = eval_intake.format_output(
            "test", [("PERSONA", "hi")], "ctx", judge_parsed, ""
        )
        assert "A \\| B" in output


# ── Prompt builders ────────────────────────────────────────────────────────


class TestPromptBuilders:
    def test_interviewer_system_includes_protocol(self):
        result = eval_intake.build_interviewer_system("PROTOCOL CONTENT HERE")
        assert "PROTOCOL CONTENT HERE" in result
        assert "SUFFICIENCY_REACHED" in result

    def test_persona_system_includes_persona(self):
        result = eval_intake.build_persona_system("CHARACTER DETAILS")
        assert "CHARACTER DETAILS" in result
        assert "Stay in character" in result

    def test_judge_system_includes_rubric(self):
        result = eval_intake.build_judge_system("RUBRIC CONTENT")
        assert "RUBRIC CONTENT" in result
        assert "rigorous" in result.lower()


# ── JSON extraction from judge response ────────────────────────────────────


class TestJudgeJsonExtraction:
    """Test the JSON extraction logic used in run_judge."""

    def _extract_json(self, text):
        """Replicate the JSON extraction from run_judge."""
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            try:
                return json.loads(text[json_start:json_end])
            except json.JSONDecodeError:
                return None
        return None

    def test_clean_json(self):
        text = '{"scores": {"register": 4}, "average": 4.0, "pass": true}'
        result = self._extract_json(text)
        assert result["average"] == 4.0

    def test_json_with_surrounding_text(self):
        text = 'Here is my evaluation:\n\n{"scores": {"register": 4}, "average": 4.0, "pass": true}\n\nThat concludes.'
        result = self._extract_json(text)
        assert result is not None
        assert result["pass"] is True

    def test_no_json(self):
        text = "This response has no JSON at all."
        result = self._extract_json(text)
        assert result is None

    def test_malformed_json(self):
        text = '{"scores": {bad json here}'
        result = self._extract_json(text)
        assert result is None
