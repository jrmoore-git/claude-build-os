"""Unit tests for pure utility functions in scripts/debate.py.

Tests functions that require no LLM calls or external state:
- _is_timeout_error
- _challenger_temperature
- _estimate_cost
- _build_frontmatter
- _redact_author
- _parse_frontmatter
- _parse_explore_direction
- _parse_refine_response
- _validate_challenge (partial — tag detection)
- _shuffle_challenger_sections
- SECURITY_POSTURE_* dicts
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import debate
import debate_common


# ── _is_timeout_error ──────────────────────────────────────────────────────


class TestIsTimeoutError:
    def test_llm_error_timeout_category(self):
        exc = debate.LLMError("timed out", category="timeout")
        assert debate._is_timeout_error(exc) is True

    def test_llm_error_non_timeout_category(self):
        exc = debate.LLMError("rate limited", category="rate_limit")
        assert debate._is_timeout_error(exc) is False

    def test_builtin_timeout_error(self):
        exc = TimeoutError("connection timed out")
        assert debate._is_timeout_error(exc) is True

    def test_generic_exception(self):
        exc = ValueError("bad value")
        assert debate._is_timeout_error(exc) is False

    def test_llm_error_unknown_category(self):
        exc = debate.LLMError("unknown", category="unknown")
        assert debate._is_timeout_error(exc) is False


# ── _challenger_temperature ────────────────────────────────────────────────


class TestChallengerTemperature:
    def test_gemini_gets_1_0(self):
        assert debate._challenger_temperature("gemini-3.1-pro") == 1.0

    def test_claude_gets_default(self):
        default = debate.LLM_CALL_DEFAULTS["challenger_temperature_default"]
        assert debate._challenger_temperature("claude-opus-4-6") == default

    def test_gpt_gets_default(self):
        default = debate.LLM_CALL_DEFAULTS["challenger_temperature_default"]
        assert debate._challenger_temperature("gpt-5.4") == default

    def test_unknown_model_gets_default(self):
        default = debate.LLM_CALL_DEFAULTS["challenger_temperature_default"]
        assert debate._challenger_temperature("totally-new-model") == default


# ── _estimate_cost ─────────────────────────────────────────────────────────


class TestEstimateCost:
    def test_claude_opus_cost(self):
        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        cost = debate_common._estimate_cost("claude-opus-4-6", usage)
        # 1000 * 15.0 / 1M + 500 * 75.0 / 1M = 0.015 + 0.0375 = 0.0525
        assert cost == 0.0525

    def test_gpt_cost(self):
        usage = {"prompt_tokens": 10000, "completion_tokens": 2000}
        cost = debate_common._estimate_cost("gpt-5.4", usage)
        # 10000 * 2.5 / 1M + 2000 * 10.0 / 1M = 0.025 + 0.02 = 0.045
        assert cost == 0.045

    def test_empty_usage_returns_zero(self):
        assert debate_common._estimate_cost("claude-opus-4-6", {}) == 0.0
        assert debate_common._estimate_cost("claude-opus-4-6", None) == 0.0

    def test_unknown_model_returns_zero(self):
        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        assert debate_common._estimate_cost("unknown-model-xyz", usage) == 0.0

    def test_zero_tokens(self):
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
        assert debate_common._estimate_cost("claude-opus-4-6", usage) == 0.0

    def test_missing_token_keys(self):
        usage = {"some_other_key": 42}
        assert debate_common._estimate_cost("claude-opus-4-6", usage) == 0.0

    def test_none_token_values(self):
        usage = {"prompt_tokens": None, "completion_tokens": None}
        assert debate_common._estimate_cost("claude-opus-4-6", usage) == 0.0


# ── _build_frontmatter ────────────────────────────────────────────────────


class TestBuildFrontmatter:
    @patch("debate.datetime")
    def test_basic_frontmatter(self, mock_dt):
        from datetime import datetime
        fake_now = datetime(2026, 4, 14, 10, 30, 0)
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        result = debate._build_frontmatter(
            "test-123",
            {"A": "claude-opus-4-6", "B": "gpt-5.4"},
        )
        assert "debate_id: test-123" in result
        assert "A: claude-opus-4-6" in result
        assert "B: gpt-5.4" in result
        assert result.startswith("---")
        assert result.endswith("---")

    @patch("debate.datetime")
    def test_with_extras(self, mock_dt):
        from datetime import datetime
        mock_dt.now.return_value = datetime(2026, 4, 14, 10, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        result = debate._build_frontmatter(
            "test-456",
            {"A": "model-a"},
            extras={"phase": "challenge", "posture": "3"},
        )
        assert "phase: challenge" in result
        assert "posture: 3" in result


# ── _redact_author ─────────────────────────────────────────────────────────


class TestRedactAuthor:
    def test_redacts_author_in_frontmatter(self):
        text = "---\nauthor: John Smith\ntitle: Test\n---\nBody here"
        result = debate._redact_author(text)
        assert "author: anonymous" in result
        assert "John Smith" not in result
        assert "Body here" in result

    def test_preserves_body(self):
        text = "---\nauthor: Alice\n---\nThe body\nauthor: Bob in body"
        result = debate._redact_author(text)
        assert "author: anonymous" in result
        # Body "author:" should NOT be redacted (only frontmatter)
        assert "author: Bob in body" in result

    def test_no_frontmatter(self):
        text = "Just plain text\nauthor: Someone"
        result = debate._redact_author(text)
        assert result == text

    def test_no_author_field(self):
        text = "---\ntitle: Test\n---\nBody"
        result = debate._redact_author(text)
        assert result == text

    def test_unclosed_frontmatter(self):
        text = "---\nauthor: X\nno closing"
        result = debate._redact_author(text)
        assert result == text


# ── _parse_frontmatter ─────────────────────────────────────────────────────


class TestParseFrontmatter:
    def test_basic_parse(self):
        text = "---\ndebate_id: abc\nphase: challenge\nmapping:\n  A: model-a\n  B: model-b\n---\nBody text"
        meta, body = debate._parse_frontmatter(text)
        assert meta is not None
        assert meta["debate_id"] == "abc"
        assert meta["phase"] == "challenge"
        assert meta["mapping"]["A"] == "model-a"
        assert meta["mapping"]["B"] == "model-b"
        assert "Body text" in body

    def test_no_frontmatter(self):
        text = "Just body text"
        meta, body = debate._parse_frontmatter(text)
        assert meta is None
        assert body == text

    def test_empty_mapping(self):
        text = "---\ndebate_id: xyz\n---\nBody"
        meta, body = debate._parse_frontmatter(text)
        assert meta is not None
        assert meta["debate_id"] == "xyz"
        assert meta["mapping"] == {}


# ── _parse_explore_direction ───────────────────────────────────────────────


class TestParseExploreDirection:
    def test_extracts_direction_name(self):
        text = "## Direction: The Bold Pivot\nSome description"
        assert debate._parse_explore_direction(text) == "The Bold Pivot"

    def test_unknown_when_no_match(self):
        text = "No direction header here"
        assert debate._parse_explore_direction(text) == "Unknown direction"

    def test_strips_whitespace(self):
        text = "## Direction:   Spaced Out   \nDetails"
        assert debate._parse_explore_direction(text) == "Spaced Out"


# ── _parse_refine_response ─────────────────────────────────────────────────


class TestParseRefineResponse:
    def test_parses_both_sections(self):
        text = "## Review Notes\nNotes here\n## Revised Document\nDoc here"
        notes, doc = debate._parse_refine_response(text)
        assert notes == "Notes here"
        assert doc == "Doc here"

    def test_fallback_on_no_sections(self):
        text = "Just some text without headers"
        notes, doc = debate._parse_refine_response(text)
        assert notes == text.strip()
        assert doc == ""


# ── Security posture dicts ─────────────────────────────────────────────────


class TestSecurityPosture:
    def test_challenger_modifier_keys(self):
        for level in [1, 2, 3, 4, 5]:
            assert level in debate.SECURITY_POSTURE_CHALLENGER_MODIFIER

    def test_judge_modifier_keys(self):
        for level in [1, 2, 3, 4, 5]:
            assert level in debate.SECURITY_POSTURE_JUDGE_MODIFIER

    def test_level_3_is_empty(self):
        assert debate.SECURITY_POSTURE_CHALLENGER_MODIFIER[3] == ""
        assert debate.SECURITY_POSTURE_JUDGE_MODIFIER[3] == ""

    def test_low_posture_mentions_advisory(self):
        assert "ADVISORY" in debate.SECURITY_POSTURE_CHALLENGER_MODIFIER[1]
        assert "ADVISORY" in debate.SECURITY_POSTURE_CHALLENGER_MODIFIER[2]

    def test_high_posture_mentions_maximum_weight(self):
        text = debate.SECURITY_POSTURE_JUDGE_MODIFIER[5].lower()
        assert "maximum weight" in text or "blocking" in text

    def test_labels_all_present(self):
        for level in [1, 2, 3, 4, 5]:
            assert level in debate.SECURITY_POSTURE_LABELS


# ── _shuffle_challenger_sections ───────────────────────────────────────────


class TestShuffleChallenger:
    def test_shuffles_sections(self):
        body = (
            "## Challenger A\nContent A\n"
            "## Challenger B\nContent B\n"
            "## Challenger C\nContent C\n"
        )
        mapping = {"A": "model-a", "B": "model-b", "C": "model-c"}
        # Run many times to verify it produces valid output
        for _ in range(5):
            shuffled, new_mapping = debate._shuffle_challenger_sections(body, mapping)
            assert "## Challenger A" in shuffled
            assert "## Challenger B" in shuffled
            assert "## Challenger C" in shuffled
            assert len(new_mapping) == 3

    def test_single_section_unchanged(self):
        body = "## Challenger A\nOnly one\n"
        mapping = {"A": "model-a"}
        result, new_mapping = debate._shuffle_challenger_sections(body, mapping)
        assert result == body
        assert new_mapping == mapping

    def test_no_sections_unchanged(self):
        body = "No challenger headers here\n"
        mapping = {}
        result, new_mapping = debate._shuffle_challenger_sections(body, mapping)
        assert result == body


# ── LLM_CALL_DEFAULTS shape ───────────────────────────────────────────────


class TestDefaults:
    def test_llm_call_defaults_keys(self):
        required = [
            "timeout", "max_tokens", "judge_temperature",
            "challenger_temperature_default", "challenger_temperature_per_model",
            "consolidation_max_tokens", "explore_temperature",
            "pressure_test_temperature",
        ]
        for key in required:
            assert key in debate.LLM_CALL_DEFAULTS, f"Missing key: {key}"

    def test_model_timeouts_gemini(self):
        assert "gemini-3.1-pro" in debate.MODEL_TIMEOUTS
        assert debate.MODEL_TIMEOUTS["gemini-3.1-pro"] == 120

    def test_tool_loop_defaults_keys(self):
        for key in ("timeout", "max_tokens", "max_turns"):
            assert key in debate.TOOL_LOOP_DEFAULTS
