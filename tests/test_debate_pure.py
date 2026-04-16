import json
import os
import random
import sys
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

for mod in [k for k in sys.modules if k.startswith("debate")]:
    del sys.modules[mod]

import debate


# ── _estimate_cost ────────────────────────────────────────────────────────


class TestEstimateCost:
    def test_claude_opus_prefix_match(self):
        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        cost = debate._estimate_cost("claude-opus-4-6", usage)
        assert cost == pytest.approx(0.0525)

    def test_claude_sonnet_prefix_match(self):
        usage = {"prompt_tokens": 1000, "completion_tokens": 1000}
        cost = debate._estimate_cost("claude-sonnet-4-6", usage)
        assert cost == pytest.approx(0.018)

    def test_claude_haiku_prefix_match(self):
        usage = {"prompt_tokens": 10000, "completion_tokens": 1000}
        cost = debate._estimate_cost("claude-haiku-4-some-version", usage)
        # 10000 * 0.80 / 1M + 1000 * 4.0 / 1M = 0.008 + 0.004 = 0.012
        assert cost == pytest.approx(0.012)

    def test_gpt_54(self):
        usage = {"prompt_tokens": 10000, "completion_tokens": 2000}
        cost = debate._estimate_cost("gpt-5.4", usage)
        assert cost == pytest.approx(0.045)

    def test_gpt_41(self):
        usage = {"prompt_tokens": 1000000, "completion_tokens": 0}
        cost = debate._estimate_cost("gpt-4.1", usage)
        assert cost == pytest.approx(2.0)

    def test_gemini_31_pro(self):
        usage = {"prompt_tokens": 0, "completion_tokens": 1000000}
        cost = debate._estimate_cost("gemini-3.1-pro", usage)
        assert cost == pytest.approx(10.0)

    def test_gemini_25_flash(self):
        usage = {"prompt_tokens": 1000, "completion_tokens": 1000}
        cost = debate._estimate_cost("gemini-2.5-flash", usage)
        # 1000 * 0.15 / 1M + 1000 * 0.60 / 1M = 0.00015 + 0.0006 = 0.00075
        assert cost == pytest.approx(0.00075)

    def test_empty_usage_dict(self):
        assert debate._estimate_cost("claude-opus-4-6", {}) == 0.0

    def test_none_usage(self):
        assert debate._estimate_cost("claude-opus-4-6", None) == 0.0

    def test_unknown_model(self):
        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        assert debate._estimate_cost("totally-unknown-model", usage) == 0.0

    def test_zero_tokens(self):
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
        assert debate._estimate_cost("claude-opus-4-6", usage) == 0.0

    def test_missing_keys_in_usage(self):
        assert debate._estimate_cost("claude-opus-4-6", {"irrelevant": 42}) == 0.0

    def test_none_token_values_treated_as_zero(self):
        usage = {"prompt_tokens": None, "completion_tokens": None}
        assert debate._estimate_cost("claude-opus-4-6", usage) == 0.0

    def test_prefix_match_picks_first(self):
        # "claude-opus-4" is the pricing key; "claude-opus-4-6" matches it
        usage = {"prompt_tokens": 1000, "completion_tokens": 0}
        cost = debate._estimate_cost("claude-opus-4-6", usage)
        expected = 1000 * 15.0 / 1_000_000
        assert cost == pytest.approx(expected)

    def test_result_is_rounded(self):
        usage = {"prompt_tokens": 1, "completion_tokens": 1}
        cost = debate._estimate_cost("claude-opus-4-6", usage)
        # 1 * 15 / 1M + 1 * 75 / 1M = 0.000090
        assert cost == round(cost, 6)


# ── _challenger_temperature ───────────────────────────────────────────────


class TestChallengerTemperature:
    def test_gemini_31_pro_gets_1_0(self):
        assert debate._challenger_temperature("gemini-3.1-pro") == 1.0

    def test_claude_model_gets_default(self):
        default = debate.LLM_CALL_DEFAULTS["challenger_temperature_default"]
        assert debate._challenger_temperature("claude-opus-4-6") == default

    def test_gpt_model_gets_default(self):
        default = debate.LLM_CALL_DEFAULTS["challenger_temperature_default"]
        assert debate._challenger_temperature("gpt-5.4") == default

    def test_unknown_model_gets_default(self):
        default = debate.LLM_CALL_DEFAULTS["challenger_temperature_default"]
        assert debate._challenger_temperature("mystery-model-v9") == default

    def test_default_is_zero(self):
        assert debate.LLM_CALL_DEFAULTS["challenger_temperature_default"] == 0.0


# ── _is_timeout_error ─────────────────────────────────────────────────────


class TestIsTimeoutError:
    def test_llm_error_timeout(self):
        exc = debate.LLMError("timed out", category="timeout")
        assert debate._is_timeout_error(exc) is True

    def test_llm_error_rate_limit(self):
        exc = debate.LLMError("rate limited", category="rate_limit")
        assert debate._is_timeout_error(exc) is False

    def test_llm_error_unknown(self):
        exc = debate.LLMError("something", category="unknown")
        assert debate._is_timeout_error(exc) is False

    def test_builtin_timeout_error(self):
        assert debate._is_timeout_error(TimeoutError("conn timeout")) is True

    def test_value_error(self):
        assert debate._is_timeout_error(ValueError("bad")) is False

    def test_os_error(self):
        assert debate._is_timeout_error(OSError("disk")) is False

    def test_generic_exception(self):
        assert debate._is_timeout_error(Exception("generic")) is False


# ── _build_frontmatter ────────────────────────────────────────────────────


class TestBuildFrontmatter:
    @patch("debate.datetime")
    def test_structure(self, mock_dt):
        from datetime import datetime
        mock_dt.now.return_value = datetime(2026, 1, 15, 8, 30, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        result = debate._build_frontmatter("d-001", {"A": "model-a", "B": "model-b"})
        assert result.startswith("---")
        assert result.endswith("---")
        assert "debate_id: d-001" in result
        assert "mapping:" in result
        assert "  A: model-a" in result
        assert "  B: model-b" in result

    @patch("debate.datetime")
    def test_with_extras(self, mock_dt):
        from datetime import datetime
        mock_dt.now.return_value = datetime(2026, 1, 1, 0, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        result = debate._build_frontmatter(
            "d-002", {"A": "m"}, extras={"phase": "judge", "posture": "5"}
        )
        assert "phase: judge" in result
        assert "posture: 5" in result

    @patch("debate.datetime")
    def test_no_extras(self, mock_dt):
        from datetime import datetime
        mock_dt.now.return_value = datetime(2026, 1, 1, 0, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        result = debate._build_frontmatter("d-003", {"A": "m"})
        lines = result.strip().split("\n")
        assert lines[0] == "---"
        assert lines[-1] == "---"

    @patch("debate.datetime")
    def test_created_timestamp_format(self, mock_dt):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        mock_dt.now.return_value = datetime(2026, 4, 15, 14, 30, 45, tzinfo=ZoneInfo("America/Los_Angeles"))
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        result = debate._build_frontmatter("d-ts", {"A": "m"})
        assert "created: 2026-04-15T14:30:45" in result

    @patch("debate.datetime")
    def test_empty_mapping(self, mock_dt):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        mock_dt.now.return_value = datetime(2026, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        result = debate._build_frontmatter("d-empty", {})
        assert "mapping:" in result
        assert "debate_id: d-empty" in result


# ── _redact_author ────────────────────────────────────────────────────────


class TestRedactAuthor:
    def test_redacts_in_frontmatter(self):
        text = "---\nauthor: John Smith\ntitle: Test\n---\nBody"
        result = debate._redact_author(text)
        assert "author: anonymous" in result
        assert "John Smith" not in result

    def test_preserves_body_content(self):
        text = "---\nauthor: Alice\n---\nBody with author: Bob"
        result = debate._redact_author(text)
        assert "author: Bob" in result
        assert "author: anonymous" in result

    def test_no_frontmatter_unchanged(self):
        text = "Just text\nauthor: Someone"
        assert debate._redact_author(text) == text

    def test_no_author_field_unchanged(self):
        text = "---\ntitle: Test\n---\nBody"
        assert debate._redact_author(text) == text

    def test_unclosed_frontmatter_unchanged(self):
        text = "---\nauthor: X\nno closing delimiter"
        assert debate._redact_author(text) == text

    def test_author_with_extra_spaces(self):
        text = "---\nauthor:   Spacey Name  \n---\nBody"
        result = debate._redact_author(text)
        assert "author: anonymous" in result
        assert "Spacey Name" not in result

    def test_author_with_email(self):
        text = "---\nauthor: user@example.com\n---\nBody"
        result = debate._redact_author(text)
        assert "author: anonymous" in result
        assert "user@example.com" not in result

    def test_multiple_frontmatter_fields_preserved(self):
        text = "---\ntitle: Proposal\nauthor: Bob\ndate: 2026-04-15\n---\nBody"
        result = debate._redact_author(text)
        assert "title: Proposal" in result
        assert "date: 2026-04-15" in result
        assert "author: anonymous" in result


# ── _parse_frontmatter ────────────────────────────────────────────────────


class TestParseFrontmatter:
    def test_basic_with_mapping(self):
        text = "---\ndebate_id: abc\nphase: challenge\nmapping:\n  A: model-a\n  B: model-b\n---\nBody text"
        meta, body = debate._parse_frontmatter(text)
        assert meta["debate_id"] == "abc"
        assert meta["phase"] == "challenge"
        assert meta["mapping"]["A"] == "model-a"
        assert meta["mapping"]["B"] == "model-b"
        assert "Body text" in body

    def test_no_frontmatter(self):
        text = "Plain text only"
        meta, body = debate._parse_frontmatter(text)
        assert meta is None
        assert body == text

    def test_empty_mapping(self):
        text = "---\ndebate_id: xyz\n---\nBody"
        meta, body = debate._parse_frontmatter(text)
        assert meta["debate_id"] == "xyz"
        assert meta["mapping"] == {}

    def test_extra_fields_after_mapping(self):
        text = "---\ndebate_id: d1\nmapping:\n  A: m-a\nphase: refine\n---\nBody"
        meta, body = debate._parse_frontmatter(text)
        assert meta["mapping"]["A"] == "m-a"
        assert meta["phase"] == "refine"

    def test_body_returned_correctly(self):
        text = "---\nid: 1\n---\nLine 1\nLine 2"
        meta, body = debate._parse_frontmatter(text)
        assert "Line 1" in body
        assert "Line 2" in body

    def test_no_closing_delimiter(self):
        text = "---\nid: 1\nno closing"
        meta, body = debate._parse_frontmatter(text)
        assert meta is None


# ── _validate_challenge ───────────────────────────────────────────────────


class TestValidateChallenge:
    def test_valid_tags_no_warnings(self):
        text = (
            "## Challenges\n"
            "1. RISK [MATERIAL]: Something bad\n"
            "2. ASSUMPTION [ADVISORY]: Unstated premise\n"
            "3. ALTERNATIVE [MATERIAL]: Different approach\n"
        )
        warnings = debate._validate_challenge(text)
        assert len(warnings) == 0

    def test_missing_tag_produces_warning(self):
        text = (
            "## Challenges\n"
            "1. This has no type tag at all\n"
            "2. RISK [MATERIAL]: This is fine\n"
        )
        warnings = debate._validate_challenge(text)
        assert len(warnings) == 1
        assert "Missing type tag" in warnings[0]

    def test_all_type_tags_recognized(self):
        text = (
            "1. RISK: r\n"
            "2. ASSUMPTION: a\n"
            "3. ALTERNATIVE: alt\n"
            "4. OVER-ENGINEERED: o\n"
            "5. UNDER-ENGINEERED: u\n"
        )
        warnings = debate._validate_challenge(text)
        assert len(warnings) == 0

    def test_bold_items_without_tags_no_warning(self):
        text = "**This is a bold item without a tag**\n"
        warnings = debate._validate_challenge(text)
        assert len(warnings) == 0

    def test_empty_text(self):
        assert debate._validate_challenge("") == []

    def test_no_numbered_items(self):
        text = "Just some prose without numbered items."
        assert debate._validate_challenge(text) == []

    def test_multiple_missing_tags(self):
        text = (
            "1. No tag here\n"
            "2. No tag either\n"
            "3. Still no tag\n"
        )
        warnings = debate._validate_challenge(text)
        assert len(warnings) == 3


# ── _shuffle_challenger_sections ──────────────────────────────────────────


class TestShuffleChallengerSections:
    def test_preserves_all_sections(self):
        body = (
            "## Challenger A\nContent A here\n"
            "## Challenger B\nContent B here\n"
            "## Challenger C\nContent C here\n"
        )
        mapping = {"A": "model-a", "B": "model-b", "C": "model-c"}
        random.seed(42)
        shuffled, new_map = debate._shuffle_challenger_sections(body, mapping)
        assert "## Challenger A" in shuffled
        assert "## Challenger B" in shuffled
        assert "## Challenger C" in shuffled
        assert len(new_map) == 3

    def test_relabels_correctly(self):
        body = (
            "## Challenger A\nA stuff\n"
            "## Challenger B\nB stuff\n"
        )
        mapping = {"A": "model-a", "B": "model-b"}
        random.seed(99)
        shuffled, new_map = debate._shuffle_challenger_sections(body, mapping)
        # All new labels should be A or B
        assert set(new_map.keys()) == {"A", "B"}
        # All original models should be preserved
        assert set(new_map.values()) == {"model-a", "model-b"}

    def test_mapping_tracks_models(self):
        body = (
            "## Challenger A\nA data\n"
            "## Challenger B\nB data\n"
            "## Challenger C\nC data\n"
        )
        mapping = {"A": "claude", "B": "gpt", "C": "gemini"}
        random.seed(7)
        _, new_map = debate._shuffle_challenger_sections(body, mapping)
        assert set(new_map.values()) == {"claude", "gpt", "gemini"}

    def test_single_section_unchanged(self):
        body = "## Challenger A\nOnly one\n"
        mapping = {"A": "model-a"}
        result, new_map = debate._shuffle_challenger_sections(body, mapping)
        assert result == body
        assert new_map == mapping

    def test_no_sections_unchanged(self):
        body = "No challenger headers\n"
        mapping = {}
        result, new_map = debate._shuffle_challenger_sections(body, mapping)
        assert result == body

    def test_deterministic_with_seed(self):
        body = (
            "## Challenger A\nA\n"
            "## Challenger B\nB\n"
            "## Challenger C\nC\n"
        )
        mapping = {"A": "m-a", "B": "m-b", "C": "m-c"}
        random.seed(123)
        r1, m1 = debate._shuffle_challenger_sections(body, mapping)
        random.seed(123)
        r2, m2 = debate._shuffle_challenger_sections(body, mapping)
        assert r1 == r2
        assert m1 == m2


# ── _parse_explore_direction ──────────────────────────────────────────────


class TestParseExploreDirection:
    def test_extracts_name(self):
        text = "## Direction: The Bold Pivot\nSome description"
        assert debate._parse_explore_direction(text) == "The Bold Pivot"

    def test_unknown_when_no_header(self):
        assert debate._parse_explore_direction("No header") == "Unknown direction"

    def test_strips_whitespace(self):
        text = "## Direction:   Spaced Out   \nDetails"
        assert debate._parse_explore_direction(text) == "Spaced Out"

    def test_empty_string(self):
        assert debate._parse_explore_direction("") == "Unknown direction"

    def test_direction_mid_text(self):
        text = "Some preamble\n## Direction: Late Entry\nMore text"
        assert debate._parse_explore_direction(text) == "Late Entry"


# ── _parse_refine_response ────────────────────────────────────────────────


class TestParseRefineResponse:
    def test_both_sections(self):
        text = "## Review Notes\nNotes content\n## Revised Document\nDoc content"
        notes, doc = debate._parse_refine_response(text)
        assert notes == "Notes content"
        assert doc == "Doc content"

    def test_fallback_no_sections(self):
        text = "Unstructured response text"
        notes, doc = debate._parse_refine_response(text)
        assert notes == text.strip()
        assert doc == ""

    def test_multiline_notes_and_doc(self):
        text = (
            "## Review Notes\n"
            "Note line 1\nNote line 2\n"
            "## Revised Document\n"
            "Doc line 1\nDoc line 2"
        )
        notes, doc = debate._parse_refine_response(text)
        assert "Note line 1" in notes
        assert "Note line 2" in notes
        assert "Doc line 1" in doc
        assert "Doc line 2" in doc

    def test_only_review_notes(self):
        text = "## Review Notes\nJust notes, no revised doc"
        notes, doc = debate._parse_refine_response(text)
        assert notes == text.strip()
        assert doc == ""

    def test_only_revised_document(self):
        text = "## Revised Document\nJust the doc"
        notes, doc = debate._parse_refine_response(text)
        # No Review Notes section means the regex won't match notes_match
        assert notes == text.strip()
        assert doc == ""

    def test_whitespace_stripped(self):
        text = "## Review Notes\n  Padded notes  \n## Revised Document\n  Padded doc  "
        notes, doc = debate._parse_refine_response(text)
        assert notes == "Padded notes"
        assert doc == "Padded doc"


# ── _load_config ──────────────────────────────────────────────────────────


class TestLoadConfig:
    def test_missing_file_returns_defaults(self, tmp_path):
        config = debate._load_config(config_path=str(tmp_path / "nonexistent.json"))
        assert "persona_model_map" in config
        assert config["judge_default"] == debate._DEFAULT_JUDGE
        assert config["refine_rotation"] == list(debate._DEFAULT_REFINE_ROTATION)

    def test_malformed_json_returns_defaults(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid json!!!")
        config = debate._load_config(config_path=str(bad_file))
        assert config["judge_default"] == debate._DEFAULT_JUDGE

    def test_valid_config(self, tmp_path):
        cfg = {
            "persona_model_map": {"architect": "custom-model", "security": "sec-model"},
            "judge_default": "judge-model",
            "refine_rotation": ["m1", "m2"],
            "version": "test-1",
        }
        f = tmp_path / "config.json"
        f.write_text(json.dumps(cfg))
        config = debate._load_config(config_path=str(f))
        assert config["persona_model_map"]["architect"] == "custom-model"
        assert config["persona_model_map"]["security"] == "sec-model"
        assert config["judge_default"] == "judge-model"
        assert config["refine_rotation"] == ["m1", "m2"]
        assert config["version"] == "test-1"

    def test_unknown_personas_filtered(self, tmp_path):
        cfg = {
            "persona_model_map": {
                "architect": "good-model",
                "hacker": "bad-model",
                "wizard": "bad-model",
            }
        }
        f = tmp_path / "config.json"
        f.write_text(json.dumps(cfg))
        config = debate._load_config(config_path=str(f))
        assert "hacker" not in config["persona_model_map"]
        assert "wizard" not in config["persona_model_map"]
        assert "architect" in config["persona_model_map"]

    def test_all_unknown_personas_falls_back_to_defaults(self, tmp_path):
        cfg = {"persona_model_map": {"hacker": "m1", "wizard": "m2"}}
        f = tmp_path / "config.json"
        f.write_text(json.dumps(cfg))
        config = debate._load_config(config_path=str(f))
        # All filtered out -> falls back to defaults
        assert config["persona_model_map"] == dict(debate._DEFAULT_PERSONA_MODEL_MAP)

    def test_missing_keys_use_defaults(self, tmp_path):
        cfg = {"version": "v2"}
        f = tmp_path / "config.json"
        f.write_text(json.dumps(cfg))
        config = debate._load_config(config_path=str(f))
        assert config["version"] == "v2"
        assert config["judge_default"] == debate._DEFAULT_JUDGE
        assert config["persona_model_map"] == dict(debate._DEFAULT_PERSONA_MODEL_MAP)

    def test_empty_json_object(self, tmp_path):
        f = tmp_path / "empty.json"
        f.write_text("{}")
        config = debate._load_config(config_path=str(f))
        assert config["persona_model_map"] == dict(debate._DEFAULT_PERSONA_MODEL_MAP)
        assert config["judge_default"] == debate._DEFAULT_JUDGE


# ── _resolve_reviewers ────────────────────────────────────────────────────


class TestResolveReviewers:
    @pytest.fixture
    def config(self):
        return {
            "persona_model_map": {
                "architect": "claude-sonnet-4-6",
                "staff": "gemini-3.1-pro",
                "security": "gpt-5.4",
                "pm": "gemini-3.1-pro",
            }
        }

    def _args(self, persona=None, personas=None, model=None, models=None):
        return Namespace(persona=persona, personas=personas, model=model, models=models)

    def test_single_persona(self, config):
        result = debate._resolve_reviewers(self._args(persona="architect"), config)
        assert result == [("architect", "claude-sonnet-4-6", True)]

    def test_single_persona_case_insensitive(self, config):
        result = debate._resolve_reviewers(self._args(persona=" SECURITY "), config)
        assert result == [("security", "gpt-5.4", True)]

    def test_unknown_persona_returns_none(self, config):
        result = debate._resolve_reviewers(self._args(persona="hacker"), config)
        assert result is None

    def test_multiple_personas(self, config):
        result = debate._resolve_reviewers(self._args(personas="architect,security"), config)
        assert len(result) == 2
        assert result[0] == ("architect", "claude-sonnet-4-6", True)
        assert result[1] == ("security", "gpt-5.4", True)

    def test_multiple_personas_with_unknown(self, config):
        result = debate._resolve_reviewers(self._args(personas="architect,hacker"), config)
        assert result is None

    def test_empty_personas_string(self, config):
        result = debate._resolve_reviewers(self._args(personas=""), config)
        assert result is None

    def test_single_model(self, config):
        result = debate._resolve_reviewers(self._args(model="custom-model"), config)
        assert result == [("reviewer", "custom-model", False)]

    def test_single_model_strips_whitespace(self, config):
        result = debate._resolve_reviewers(self._args(model="  my-model  "), config)
        assert result == [("reviewer", "my-model", False)]

    def test_multiple_models(self, config):
        result = debate._resolve_reviewers(self._args(models="m1,m2,m3"), config)
        assert len(result) == 3
        assert result[0] == ("model-1", "m1", False)
        assert result[1] == ("model-2", "m2", False)
        assert result[2] == ("model-3", "m3", False)

    def test_empty_models_string(self, config):
        result = debate._resolve_reviewers(self._args(models=""), config)
        assert result is None

    def test_no_flags_returns_none(self, config):
        result = debate._resolve_reviewers(self._args(), config)
        assert result is None

    def test_personas_with_spaces(self, config):
        result = debate._resolve_reviewers(self._args(personas=" pm , staff "), config)
        assert len(result) == 2
        assert result[0][0] == "pm"
        assert result[1][0] == "staff"


# ── _count_recommendation_slots ───────────────────────────────────────────


class TestCountRecommendationSlots:
    def test_numbered_list(self):
        text = (
            "## Recommendations\n"
            "1. First thing\n"
            "2. Second thing\n"
            "3. Third thing\n"
        )
        result = debate._count_recommendation_slots(text)
        assert result["recommendations"] == 3
        assert result["cannot_recommend"] == 0
        assert result["total"] == 3

    def test_bullet_list(self):
        text = (
            "## Recommendations\n"
            "- First\n"
            "- Second\n"
            "* Third\n"
        )
        result = debate._count_recommendation_slots(text)
        assert result["recommendations"] == 3

    def test_cannot_recommend_anywhere(self):
        text = (
            "## Recommendations\n"
            "1. Good one\n"
            "\n"
            "## Other Section\n"
            "CANNOT RECOMMEND: Bad one\n"
            "CANNOT RECOMMEND: Another bad\n"
        )
        result = debate._count_recommendation_slots(text)
        assert result["recommendations"] == 1
        assert result["cannot_recommend"] == 2
        assert result["total"] == 3

    def test_no_recommendations_heading(self):
        text = "## Analysis\n1. Not counted\n2. Also not counted\n"
        result = debate._count_recommendation_slots(text)
        assert result["recommendations"] == 0
        assert result["total"] == 0

    def test_empty_text(self):
        result = debate._count_recommendation_slots("")
        assert result == {"recommendations": 0, "cannot_recommend": 0, "total": 0}

    def test_subheader_recommendations(self):
        text = (
            "## Recommendations\n"
            "### 1. First priority\n"
            "Details here\n"
            "### 2. Second priority\n"
            "More details\n"
        )
        result = debate._count_recommendation_slots(text)
        assert result["recommendations"] == 2

    def test_section_ends_at_same_level_heading(self):
        text = (
            "## Recommendations\n"
            "1. Counted\n"
            "## Next Section\n"
            "1. Not counted\n"
        )
        result = debate._count_recommendation_slots(text)
        assert result["recommendations"] == 1

    def test_recommended_header_variant(self):
        text = (
            "### Recommended\n"
            "1. Item one\n"
            "2. Item two\n"
        )
        result = debate._count_recommendation_slots(text)
        assert result["recommendations"] == 2

    def test_proposed_changes_header(self):
        text = (
            "## Proposed Changes\n"
            "- Change A\n"
            "- Change B\n"
        )
        result = debate._count_recommendation_slots(text)
        assert result["recommendations"] == 2

    def test_mixed_numbered_and_bullets(self):
        text = (
            "## Recommendations\n"
            "1. First\n"
            "- Also counted\n"
            "2. Second numbered\n"
        )
        result = debate._count_recommendation_slots(text)
        assert result["recommendations"] == 3


# ── _load_prompt ──────────────────────────────────────────────────────────


class TestLoadPrompt:
    def test_missing_file_returns_fallback(self, tmp_path):
        with patch.object(debate, "PROMPTS_DIR", str(tmp_path)):
            text, version = debate._load_prompt("nonexistent.md", "FALLBACK_TEXT")
        assert text == "FALLBACK_TEXT"
        assert version is None

    def test_file_without_frontmatter(self, tmp_path):
        prompt_file = tmp_path / "test.md"
        prompt_file.write_text("This is the prompt text.")
        with patch.object(debate, "PROMPTS_DIR", str(tmp_path)):
            text, version = debate._load_prompt("test.md", "FALLBACK")
        assert text == "This is the prompt text."
        assert version is None

    def test_file_with_frontmatter_and_version(self, tmp_path):
        content = "---\nversion: 3\ntitle: Test\n---\nThe actual prompt"
        prompt_file = tmp_path / "test.md"
        prompt_file.write_text(content)
        with patch.object(debate, "PROMPTS_DIR", str(tmp_path)):
            text, version = debate._load_prompt("test.md", "FALLBACK")
        assert text == "The actual prompt"
        assert version == 3

    def test_frontmatter_stripped(self, tmp_path):
        content = "---\nversion: 1\n---\nPrompt body here"
        prompt_file = tmp_path / "test.md"
        prompt_file.write_text(content)
        with patch.object(debate, "PROMPTS_DIR", str(tmp_path)):
            text, version = debate._load_prompt("test.md", "FALLBACK")
        assert "---" not in text
        assert "version" not in text
        assert text == "Prompt body here"

    def test_non_integer_version(self, tmp_path):
        content = "---\nversion: not-a-number\n---\nPrompt"
        prompt_file = tmp_path / "test.md"
        prompt_file.write_text(content)
        with patch.object(debate, "PROMPTS_DIR", str(tmp_path)):
            text, version = debate._load_prompt("test.md", "FALLBACK")
        assert text == "Prompt"
        assert version is None

    def test_frontmatter_no_version_field(self, tmp_path):
        content = "---\ntitle: No Version\n---\nBody"
        prompt_file = tmp_path / "test.md"
        prompt_file.write_text(content)
        with patch.object(debate, "PROMPTS_DIR", str(tmp_path)):
            text, version = debate._load_prompt("test.md", "FALLBACK")
        assert text == "Body"
        assert version is None

    def test_unclosed_frontmatter_returned_as_is(self, tmp_path):
        content = "---\nversion: 5\nNo closing delimiter"
        prompt_file = tmp_path / "test.md"
        prompt_file.write_text(content)
        with patch.object(debate, "PROMPTS_DIR", str(tmp_path)):
            text, version = debate._load_prompt("test.md", "FALLBACK")
        # No closing --- means frontmatter isn't stripped
        assert "version: 5" in text
        assert version is None
