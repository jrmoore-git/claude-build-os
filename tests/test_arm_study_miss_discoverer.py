"""Unit tests for scripts/arm_study_miss_discoverer.py.

Covers the parser (JSON / code-fence / bare object / malformed) and the
token-coverage matcher (all-match, majority-match, under-threshold,
no-tokens edge case).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

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


# ── REDESIGN B: ensemble + matcher v2 + adjudicator + credential scan ────


def _issue(id_: str, tokens: list[str], category: str = "gap") -> dict:
    return {
        "id": id_, "category": category, "description": f"desc-{id_}",
        "key_tokens": tokens, "severity": "material",
        "rationale": f"rat-{id_}",
    }


def test_dedup_ensemble_majority_vote():
    """Issue surfaced by 2 of 3 → majority + union; intersection only on 3/3."""
    per_model = [
        {"model": "m1", "parsed": {"issues": [
            _issue("a", ["foo", "bar"]),
            _issue("b", ["baz", "qux"]),
        ]}, "stats": None},
        {"model": "m2", "parsed": {"issues": [
            _issue("a2", ["foo", "bar"]),  # same as a
        ]}, "stats": None},
        {"model": "m3", "parsed": {"issues": [
            _issue("c", ["alpha", "beta"]),
        ]}, "stats": None},
    ]
    agg = mrd.dedup_ensemble(per_model)
    union_ids = {i["id"] for i in agg["union"]}
    majority_ids = {i["id"] for i in agg["majority"]}
    intersection_ids = {i["id"] for i in agg["intersection"]}
    assert union_ids == {"a", "b", "c"}
    assert "a" in majority_ids
    assert "b" not in majority_ids and "c" not in majority_ids
    assert intersection_ids == set()


def test_dedup_ensemble_unanimous_in_intersection():
    """Issue surfaced by all 3 models → intersection ∩ majority ∩ union."""
    per_model = [
        {"model": f"m{i}", "parsed": {"issues": [
            _issue(f"x{i}", ["foo", "bar"]),
        ]}, "stats": None}
        for i in range(3)
    ]
    agg = mrd.dedup_ensemble(per_model)
    assert len(agg["intersection"]) == 1
    assert len(agg["majority"]) == 1
    assert len(agg["union"]) == 1
    assert sorted(agg["intersection"][0]["models_surfaced"]) == ["m0", "m1", "m2"]


def test_dedup_ensemble_jaccard_threshold():
    """Issues with token-jaccard at threshold → same; below → different."""
    per_model = [
        {"model": "m1", "parsed": {"issues": [_issue("i1", ["a", "b", "c"])]},
         "stats": None},
        {"model": "m2", "parsed": {"issues": [_issue("i2", ["a", "b", "d"])]},
         "stats": None},
        {"model": "m3", "parsed": {"issues": [_issue("i3", ["x", "y", "z"])]},
         "stats": None},
    ]
    agg = mrd.dedup_ensemble(per_model)
    assert agg["n_clusters"] == 2
    assert len(agg["majority"]) == 1


def test_match_v2_caught_above_threshold():
    """Overlap ratio ≥ 0.6 → caught, no adjudicator call."""
    called = {"n": 0}

    def stub_adj(**kwargs):
        called["n"] += 1
        return {"decision": "YES", "rationale": "", "parse_ok": True,
                "cache_hit": False, "error": None}

    issues = [_issue("i1", ["foo", "bar", "baz", "qux"])]
    text = "foo bar baz are all here"
    out = mrd.match_reference_issues_v2(
        issues, text, _adjudicator_fn=stub_adj,
    )
    assert out["caught_count"] == 1
    assert called["n"] == 0
    assert out["caught"][0]["_adjudicated"] is False


def test_match_v2_borderline_calls_adjudicator_yes():
    called = {"n": 0}

    def stub_adj(**kwargs):
        called["n"] += 1
        return {"decision": "YES", "rationale": "yes-r", "parse_ok": True,
                "cache_hit": False, "error": None}

    # 2/4 = 0.5 in [0.3, 0.6) borderline range
    issues = [_issue("i1", ["foo", "bar", "missing1", "missing2"])]
    text = "foo and bar appear"
    out = mrd.match_reference_issues_v2(
        issues, text, _adjudicator_fn=stub_adj,
    )
    assert called["n"] == 1
    assert out["caught_count"] == 1
    assert out["borderline_count"] == 1
    assert out["caught"][0]["_adjudicated"] is True


def test_match_v2_borderline_calls_adjudicator_no():
    def stub_adj(**kwargs):
        return {"decision": "NO", "rationale": "no-r", "parse_ok": True,
                "cache_hit": False, "error": None}

    issues = [_issue("i1", ["foo", "bar", "x", "y"])]
    text = "foo bar nothing else"
    out = mrd.match_reference_issues_v2(
        issues, text, _adjudicator_fn=stub_adj,
    )
    assert out["missed_count"] == 1
    assert out["missed"][0]["_adjudicated"] is True


def test_match_v2_below_borderline_skips_adjudicator():
    """Overlap < 0.3 → missed without LLM call."""
    called = {"n": 0}

    def stub_adj(**kwargs):
        called["n"] += 1
        return {"decision": "YES", "rationale": "", "parse_ok": True,
                "cache_hit": False, "error": None}

    issues = [_issue("i1", ["foo", "missing1", "missing2", "missing3"])]
    text = "foo only"
    out = mrd.match_reference_issues_v2(
        issues, text, _adjudicator_fn=stub_adj,
    )
    assert called["n"] == 0
    assert out["missed_count"] == 1


def test_match_v2_word_boundary_no_partial_match():
    """v2 word-boundary tokenization — 'test' ≠ 'testing' (vs v1 substring)."""
    issues = [_issue("i1", ["test"])]
    text = "we are testing things"
    out = mrd.match_reference_issues_v2(
        issues, text,
        _adjudicator_fn=lambda **kw: {"decision": "NO", "rationale": "",
                                      "parse_ok": True, "cache_hit": False,
                                      "error": None},
        skip_adjudication=True,
    )
    assert out["missed_count"] == 1


def test_credential_scan_blocks_egress(tmp_path):
    """challenge_text containing credential pattern raises before LLM call."""
    issue = _issue("i1", ["any"])
    bad_text = "secret in here: sk-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    with pytest.raises(mrd.CredentialEgressError):
        mrd.adjudicate_borderline(
            challenge_text=bad_text, issue=issue,
            cache=None,
            cache_path=tmp_path / "cache.jsonl",
            log_path=tmp_path / "log.jsonl",
            _llm_call_json=lambda **kw: {"decision": "YES", "rationale": ""},
        )


def test_match_v2_credential_scan_marks_missed(tmp_path):
    """Borderline match in credential-tainted text → missed (not crash)."""
    def real_adj(**kwargs):
        # Override cache/log paths to per-test tmp_path; matcher passes
        # adjudicator_cache_path=None which we replace before delegating.
        kwargs["cache_path"] = tmp_path / "c.jsonl"
        kwargs["log_path"] = tmp_path / "l.jsonl"
        return mrd.adjudicate_borderline(
            _llm_call_json=lambda **kw: {"decision": "YES", "rationale": ""},
            **kwargs,
        )

    issues = [
        _issue("i1", ["foo", "bar", "missing1", "missing2"]),
        _issue("i2", ["other"]),
    ]
    bad_text = "foo bar leak: AKIAABCDEFGHIJKLMNOP and other things"
    out = mrd.match_reference_issues_v2(
        issues, bad_text, _adjudicator_fn=real_adj,
    )
    missed_i1 = next(m for m in out["missed"] if m["id"] == "i1")
    assert "credential-egress-blocked" in missed_i1["_match_reason"]
    assert out["caught_count"] == 1


def test_adjudicate_borderline_cache_hit(tmp_path):
    """Second adjudication with identical inputs returns cached decision."""
    cache: dict = {}
    calls = {"n": 0}

    def stub(*, system, user, model, temperature, max_tokens, timeout):
        calls["n"] += 1
        return {"decision": "YES", "rationale": "first"}

    issue = _issue("i1", ["foo"])
    args = dict(
        challenge_text="foo here", issue=issue, cache=cache,
        cache_path=tmp_path / "c.jsonl", log_path=tmp_path / "l.jsonl",
    )
    r1 = mrd.adjudicate_borderline(**args, _llm_call_json=stub)
    assert calls["n"] == 1
    assert r1["cache_hit"] is False

    r2 = mrd.adjudicate_borderline(
        **args,
        _llm_call_json=lambda **kw: {"decision": "NO"},
    )
    assert calls["n"] == 1
    assert r2["cache_hit"] is True
    assert r2["decision"] == "YES"


def test_run_ensemble_returns_per_model_outputs():
    def stub(text, model, **kw):
        return (
            f'{{"issues": [{{"id": "i-{model}", "key_tokens": ["t"]}}]}}',
            {"model": model, "tool_calls": 0},
        )

    out = mrd.run_ensemble(
        "proposal", models=("m1", "m2", "m3"),
        _run_discoverer_fn=stub,
    )
    assert [e["model"] for e in out] == ["m1", "m2", "m3"]
    assert all(e["parsed"]["issues"] for e in out)


def test_run_ensemble_handles_one_model_failure():
    def stub(text, model, **kw):
        if model == "m2":
            return None, None
        return (
            f'{{"issues": [{{"id": "i-{model}", "key_tokens": ["t"]}}]}}',
            {"model": model, "tool_calls": 0},
        )

    out = mrd.run_ensemble(
        "proposal", models=("m1", "m2", "m3"),
        _run_discoverer_fn=stub,
    )
    by_model = {e["model"]: e for e in out}
    assert "parse_error" in by_model["m2"]["parsed"]
    assert by_model["m1"]["parsed"]["issues"]
    assert by_model["m3"]["parsed"]["issues"]
