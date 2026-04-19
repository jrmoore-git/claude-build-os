"""Unit tests for scripts/arm_study_miss_discoverer.py.

Covers the parser (JSON / code-fence / bare object / malformed) and the
token-coverage matcher (all-match, majority-match, under-threshold,
no-tokens edge case).
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import arm_study_miss_discoverer as mrd  # noqa: E402


# ── Parser ──────────────────────────────────────────────────────────────────


def test_parser_handles_bare_object():
    raw = '{"issues": [{"id": "i1", "description": "foo"}]}'
    out = mrd.parse_discoverer_output(raw)
    assert len(out["issues"]) == 1
    assert out["issues"][0]["id"] == "i1"


def test_parser_handles_fenced_json():
    raw = '```json\n{"issues": [{"id": "i1"}]}\n```'
    out = mrd.parse_discoverer_output(raw)
    assert out["issues"][0]["id"] == "i1"


def test_parser_handles_untyped_fence():
    raw = '```\n{"issues": [{"id": "i1"}]}\n```'
    out = mrd.parse_discoverer_output(raw)
    assert out["issues"][0]["id"] == "i1"


def test_parser_normalizes_tokens_to_lowercase():
    raw = '{"issues": [{"id": "i1", "key_tokens": ["FOO.py", "BarFunc"]}]}'
    out = mrd.parse_discoverer_output(raw)
    assert out["issues"][0]["key_tokens"] == ["foo.py", "barfunc"]


def test_parser_empty_returns_parse_error():
    out = mrd.parse_discoverer_output("")
    assert out["issues"] == []
    assert "parse_error" in out


def test_parser_garbage_returns_parse_error():
    out = mrd.parse_discoverer_output("not json at all")
    assert out["issues"] == []
    assert "parse_error" in out


# ── Matcher ────────────────────────────────────────────────────────────────


def test_matcher_all_tokens_present_is_caught():
    issues = [{"id": "i1", "key_tokens": ["foo.py", "barfunc"]}]
    text = "The file FOO.py has a bug in barfunc that needs fixing"
    out = mrd.match_reference_issues(issues, text)
    assert out["caught_count"] == 1
    assert out["missed_count"] == 0


def test_matcher_majority_threshold_catches_partial_matches():
    """V2 relaxed matcher: ≥60% of tokens must appear, not all."""
    issues = [{"id": "i1", "key_tokens": ["foo.py", "barfunc", "not-mentioned", "either"]}]
    text = "The file foo.py has a bug in barfunc"
    out = mrd.match_reference_issues(issues, text)
    # 2 of 4 tokens = 50%, under 60% threshold → missed
    assert out["missed_count"] == 1

    issues = [{"id": "i1", "key_tokens": ["foo.py", "barfunc", "another-hit", "missing"]}]
    text = "file foo.py, function barfunc, also another-hit described here"
    out = mrd.match_reference_issues(issues, text)
    # 3 of 4 = 75% ≥ 60% → caught
    assert out["caught_count"] == 1


def test_matcher_threshold_arg_overrides_default():
    issues = [{"id": "i1", "key_tokens": ["a", "b", "c"]}]
    text = "only a and b here"
    strict = mrd.match_reference_issues(issues, text, threshold=1.0)
    loose = mrd.match_reference_issues(issues, text, threshold=0.5)
    assert strict["caught_count"] == 0
    assert loose["caught_count"] == 1


def test_matcher_no_tokens_is_missed():
    issues = [{"id": "i1", "key_tokens": []}]
    text = "anything at all"
    out = mrd.match_reference_issues(issues, text)
    assert out["missed_count"] == 1
    assert out["missed"][0]["_match_reason"] == "no key_tokens"


def test_matcher_reports_miss_rate():
    issues = [
        {"id": "i1", "key_tokens": ["foo.py"]},
        {"id": "i2", "key_tokens": ["bar.py"]},
        {"id": "i3", "key_tokens": ["baz.py"]},
    ]
    text = "foo.py and bar.py mentioned"
    out = mrd.match_reference_issues(issues, text)
    assert out["caught_count"] == 2
    assert out["missed_count"] == 1
    assert abs(out["miss_rate"] - 1 / 3) < 1e-9


def test_matcher_case_insensitive():
    issues = [{"id": "i1", "key_tokens": ["foo.py"]}]
    text = "FOO.py"
    out = mrd.match_reference_issues(issues, text)
    assert out["caught_count"] == 1


def test_matcher_empty_issue_list():
    out = mrd.match_reference_issues([], "any text")
    assert out["total_reference_issues"] == 0
    assert out["miss_rate"] is None
