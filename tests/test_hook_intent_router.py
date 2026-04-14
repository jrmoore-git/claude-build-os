"""Tests for hooks/hook-intent-router.py — intent classification and routing."""
import json
import os
import sys
import time

import pytest

# Add hooks/ to sys.path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import importlib

hook_intent_router = importlib.import_module("hook-intent-router")

INTENT_PATTERNS = hook_intent_router.INTENT_PATTERNS


# ── Helper ──────────────────────────────────────────────────────────────────

def match_intent(text):
    """Return (skill, message) for the first matching pattern, or (None, None)."""
    for pattern, skill, message in INTENT_PATTERNS:
        if pattern.search(text):
            return (skill, message)
    return (None, None)


# ── 1. INTENT_PATTERNS regex matching ───────────────────────────────────────

class TestIntentPatterns:
    def test_investigate_broke(self):
        skill, _ = match_intent("something broke")
        assert skill == "investigate"

    def test_investigate_not_working(self):
        skill, _ = match_intent("the API is not working")
        assert skill == "investigate"

    def test_investigate_bug(self):
        skill, _ = match_intent("I found a bug in the parser")
        assert skill == "investigate"

    def test_investigate_debug(self):
        skill, _ = match_intent("can you debug this?")
        assert skill == "investigate"

    def test_investigate_why_happening(self):
        skill, _ = match_intent("why is the server crashing happening")
        # "crashing" matches investigate via "crash"
        assert skill == "investigate"

    def test_investigate_keeps_failing(self):
        skill, _ = match_intent("the build keeps failing")
        assert skill == "investigate"

    def test_drift_used_to_work(self):
        skill, _ = match_intent("this used to work fine")
        assert skill == "investigate-drift"

    def test_drift_worked_before(self):
        skill, _ = match_intent("it worked before the update")
        assert skill == "investigate-drift"

    def test_drift_broke_after(self):
        # "broke" matches investigate first (first-match-wins), not drift
        skill, _ = match_intent("it broke after the last deploy")
        assert skill == "investigate"

    def test_drift_regression(self):
        skill, _ = match_intent("this looks like a regression")
        assert skill == "investigate-drift"

    def test_drift_wasnt_like_this(self):
        skill, _ = match_intent("it wasn't like this before")
        assert skill == "investigate-drift"

    def test_think_build(self):
        skill, _ = match_intent("I want to build a dashboard")
        assert skill == "think"

    def test_think_new_feature(self):
        skill, _ = match_intent("we need a new feature for auth")
        assert skill == "think"

    def test_think_add_support(self):
        skill, _ = match_intent("add support for webhooks")
        assert skill == "think"

    def test_think_implement(self):
        skill, _ = match_intent("implement the caching layer")
        assert skill == "think"

    def test_think_build_me(self):
        skill, _ = match_intent("build me a CLI tool")
        assert skill == "think"

    def test_plan(self):
        skill, _ = match_intent("plan this out")
        assert skill == "plan"

    def test_plan_how_should_we_build(self):
        skill, _ = match_intent("how should we build the API?")
        assert skill == "plan"

    def test_plan_break_down(self):
        skill, _ = match_intent("break this down into steps")
        assert skill == "plan"

    def test_review(self):
        skill, _ = match_intent("review this code")
        assert skill == "review"

    def test_review_check_code(self):
        skill, _ = match_intent("check my code please")
        assert skill == "review"

    def test_review_is_ready(self):
        skill, _ = match_intent("is this ready to merge?")
        assert skill == "review"

    def test_ship(self):
        skill, _ = match_intent("ship it!")
        assert skill == "ship"

    def test_ship_deploy(self):
        skill, _ = match_intent("deploy to production")
        assert skill == "ship"

    def test_ship_lets_ship(self):
        skill, _ = match_intent("let's ship this feature")
        assert skill == "ship"

    def test_explore(self):
        skill, _ = match_intent("explore options for the database")
        assert skill == "explore"

    def test_explore_choices(self):
        skill, _ = match_intent("what are our choices here?")
        assert skill == "explore"

    def test_explore_brainstorm(self):
        skill, _ = match_intent("let's brainstorm ideas")
        assert skill == "explore"

    def test_challenge_worth_building(self):
        skill, _ = match_intent("is this worth building?")
        assert skill == "challenge"

    def test_challenge_should_we_build(self):
        skill, _ = match_intent("should we build this?")
        assert skill == "challenge"

    def test_challenge_should_we_really_do(self):
        skill, _ = match_intent("should we really do this?")
        assert skill == "challenge"

    def test_challenge_evaluate(self):
        skill, _ = match_intent("evaluate this proposal")
        assert skill == "challenge"

    def test_challenge_do_we_really_need(self):
        skill, _ = match_intent("do we really need this?")
        assert skill == "challenge"

    def test_pressure_test_what_could_go_wrong(self):
        skill, _ = match_intent("what could go wrong with this?")
        assert skill == "pressure-test"

    def test_pressure_test_devils_advocate(self):
        skill, _ = match_intent("play devil's advocate")
        assert skill == "pressure-test"

    def test_pressure_test_premortem(self):
        skill, _ = match_intent("run a pre-mortem on this plan")
        assert skill == "pressure-test"

    def test_pressure_test_stress_test(self):
        skill, _ = match_intent("stress test this design")
        assert skill == "pressure-test"

    def test_pressure_test_poke_holes(self):
        skill, _ = match_intent("poke holes in this approach")
        assert skill == "pressure-test"

    def test_ambiguous_good_idea(self):
        skill, _ = match_intent("is this a good idea?")
        assert skill == "challenge-or-pressure-test"

    def test_ambiguous_sanity_check(self):
        skill, _ = match_intent("can you do a sanity check?")
        assert skill == "challenge-or-pressure-test"

    def test_ambiguous_does_this_make_sense(self):
        skill, _ = match_intent("does this make sense?")
        assert skill == "challenge-or-pressure-test"

    def test_ambiguous_risks(self):
        skill, _ = match_intent("what are the risks?")
        assert skill == "challenge-or-pressure-test"

    def test_ambiguous_gut_check(self):
        skill, _ = match_intent("gut check on this approach")
        assert skill == "challenge-or-pressure-test"

    def test_design(self):
        skill, _ = match_intent("design this page")
        assert skill == "design"

    def test_design_ui(self):
        skill, _ = match_intent("the UI needs work")
        assert skill == "design"

    def test_design_wireframe(self):
        # "create a wireframe" matches think first ("create a" pattern)
        # — first-match-wins. "wireframe" alone matches design.
        skill, _ = match_intent("create a wireframe")
        assert skill == "think"
        skill2, _ = match_intent("need a wireframe for the homepage")
        assert skill2 == "design"

    def test_research(self):
        skill, _ = match_intent("research the best approach for caching")
        assert skill == "research"

    def test_research_find_out(self):
        skill, _ = match_intent("find out about OAuth2 PKCE flow")
        assert skill == "research"

    def test_research_what_do_we_know(self):
        skill, _ = match_intent("what do we know about rate limiting?")
        assert skill == "research"

    def test_wrap(self):
        skill, _ = match_intent("wrap up the session")
        assert skill == "wrap"

    def test_wrap_done(self):
        skill, _ = match_intent("I'm done for today")
        assert skill == "wrap"

    def test_wrap_save_and_quit(self):
        skill, _ = match_intent("save and quit")
        assert skill == "wrap"

    def test_guide_lost(self):
        skill, _ = match_intent("I'm lost, what should I do?")
        assert skill == "guide"

    def test_guide_help(self):
        skill, _ = match_intent("help me understand this")
        assert skill == "guide"

    def test_guide_whats_available(self):
        skill, _ = match_intent("what's available?")
        assert skill == "guide"

    def test_guide_where_do_i_start(self):
        skill, _ = match_intent("where do I start?")
        assert skill == "guide"

    def test_no_match(self):
        skill, msg = match_intent("hello world")
        assert skill is None
        assert msg is None

    def test_no_match_ordinary_sentence(self):
        skill, msg = match_intent("the weather is nice today")
        assert skill is None

    def test_case_insensitive(self):
        skill, _ = match_intent("SHIP IT")
        assert skill == "ship"

    def test_case_insensitive_mixed(self):
        skill, _ = match_intent("Something Broke badly")
        assert skill == "investigate"

    def test_first_match_wins_broke_vs_drift(self):
        # "broke" matches investigate first in the pattern list
        skill, _ = match_intent("it broke")
        assert skill == "investigate"

    def test_drift_only_when_distinct(self):
        # "used to work" only matches drift, not investigate
        skill, _ = match_intent("used to work perfectly")
        assert skill == "investigate-drift"

    def test_challenge_dynamic_message_is_none(self):
        # Challenge patterns have message=None (filled dynamically)
        _, msg = match_intent("is this worth building?")
        assert msg is None

    def test_pressure_test_dynamic_message_is_none(self):
        _, msg = match_intent("what could go wrong?")
        assert msg is None

    def test_ambiguous_dynamic_message_is_none(self):
        _, msg = match_intent("is this a good idea?")
        assert msg is None

    def test_investigate_has_static_message(self):
        _, msg = match_intent("something broke")
        assert msg is not None
        assert "ROUTING SUGGESTION" in msg

    def test_ship_has_static_message(self):
        _, msg = match_intent("ship it")
        assert msg is not None
        assert "ROUTING SUGGESTION" in msg


# ── 2. detect_pipeline_state() ──────────────────────────────────────────────

class TestDetectPipelineState:
    def test_empty_tasks_dir(self, tmp_path, monkeypatch):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        monkeypatch.setattr(hook_intent_router, "TASKS_DIR", str(tasks))
        state = hook_intent_router.detect_pipeline_state()
        assert state["has_proposal"] is False
        assert state["has_challenge"] is False
        assert state["has_plan"] is False
        assert state["has_pressure_test"] is False
        assert state["has_premortem"] is False
        assert state["topic"] is None

    def test_no_tasks_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(hook_intent_router, "TASKS_DIR", str(tmp_path / "nonexistent"))
        state = hook_intent_router.detect_pipeline_state()
        assert state["topic"] is None
        assert state["has_proposal"] is False

    def test_proposal_only(self, tmp_path, monkeypatch):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "foo-proposal.md").write_text("proposal content")
        monkeypatch.setattr(hook_intent_router, "TASKS_DIR", str(tasks))
        state = hook_intent_router.detect_pipeline_state()
        assert state["has_proposal"] is True
        assert state["topic"] == "foo"
        assert state["has_challenge"] is False
        assert state["has_plan"] is False

    def test_proposal_and_challenge(self, tmp_path, monkeypatch):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "foo-proposal.md").write_text("proposal")
        (tasks / "foo-challenge.md").write_text("challenge")
        monkeypatch.setattr(hook_intent_router, "TASKS_DIR", str(tasks))
        state = hook_intent_router.detect_pipeline_state()
        assert state["has_proposal"] is True
        assert state["has_challenge"] is True
        assert state["topic"] == "foo"

    def test_plan_only(self, tmp_path, monkeypatch):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "bar-plan.md").write_text("plan")
        monkeypatch.setattr(hook_intent_router, "TASKS_DIR", str(tasks))
        state = hook_intent_router.detect_pipeline_state()
        assert state["has_plan"] is True
        assert state["topic"] == "bar"

    def test_multiple_topics_most_recent_wins(self, tmp_path, monkeypatch):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        old = tasks / "old-proposal.md"
        old.write_text("old proposal")
        # Set old mtime to the past
        old_time = time.time() - 100
        os.utime(str(old), (old_time, old_time))
        new = tasks / "new-proposal.md"
        new.write_text("new proposal")
        monkeypatch.setattr(hook_intent_router, "TASKS_DIR", str(tasks))
        state = hook_intent_router.detect_pipeline_state()
        assert state["topic"] == "new"

    def test_full_pipeline_artifacts(self, tmp_path, monkeypatch):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "xyz-plan.md").write_text("plan")
        (tasks / "xyz-pressure-test.md").write_text("pressure test")
        (tasks / "xyz-premortem.md").write_text("premortem")
        monkeypatch.setattr(hook_intent_router, "TASKS_DIR", str(tasks))
        state = hook_intent_router.detect_pipeline_state()
        assert state["has_plan"] is True
        assert state["has_pressure_test"] is True
        assert state["has_premortem"] is True
        assert state["topic"] == "xyz"

    def test_proposal_takes_precedence_over_plan_for_topic(self, tmp_path, monkeypatch):
        """When proposals exist, topic comes from most recent proposal, not plan."""
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        plan = tasks / "alpha-plan.md"
        plan.write_text("plan")
        plan_time = time.time() - 200
        os.utime(str(plan), (plan_time, plan_time))
        prop = tasks / "beta-proposal.md"
        prop.write_text("proposal")
        monkeypatch.setattr(hook_intent_router, "TASKS_DIR", str(tasks))
        state = hook_intent_router.detect_pipeline_state()
        # proposals checked first, so topic = beta
        assert state["topic"] == "beta"

    def test_plan_used_when_no_proposals(self, tmp_path, monkeypatch):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        (tasks / "gamma-plan.md").write_text("plan")
        monkeypatch.setattr(hook_intent_router, "TASKS_DIR", str(tasks))
        state = hook_intent_router.detect_pipeline_state()
        assert state["topic"] == "gamma"
        assert state["has_plan"] is True


# ── 3. resolve_challenge_vs_pressure_test() ─────────────────────────────────

class TestResolveChallengeVsPressureTest:
    def _pipeline(self, **overrides):
        base = {
            "has_proposal": False,
            "has_challenge": False,
            "has_plan": False,
            "has_pressure_test": False,
            "has_premortem": False,
            "topic": "test-topic",
        }
        base.update(overrides)
        return base

    # -- skill="challenge" --

    def test_challenge_no_existing_challenge(self):
        skill, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "challenge", self._pipeline(has_challenge=False)
        )
        assert skill == "challenge"
        assert "go/no-go" in msg

    def test_challenge_existing_challenge_redirects(self):
        skill, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "challenge", self._pipeline(has_challenge=True)
        )
        assert skill == "pressure-test"
        assert "already exists" in msg

    # -- skill="pressure-test" --

    def test_pressure_test_with_plan(self):
        skill, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "pressure-test", self._pipeline(has_plan=True)
        )
        assert skill == "pressure-test"
        assert "premortem" in msg.lower() or "pre-mortem" in msg.lower()

    def test_pressure_test_with_plan_and_premortem(self):
        skill, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "pressure-test", self._pipeline(has_plan=True, has_premortem=True)
        )
        assert skill == "pressure-test"
        assert "premortem already exists" in msg

    def test_pressure_test_with_plan_and_pressure_test(self):
        skill, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "pressure-test", self._pipeline(has_plan=True, has_pressure_test=True)
        )
        assert skill == "pressure-test"
        assert "pressure-test already exists" in msg

    def test_pressure_test_proposal_no_challenge(self):
        skill, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "pressure-test", self._pipeline(has_proposal=True, has_challenge=False)
        )
        assert skill == "pressure-test"
        assert "no /challenge artifact" in msg

    def test_pressure_test_generic(self):
        skill, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "pressure-test", self._pipeline()
        )
        assert skill == "pressure-test"
        assert "adversarial" in msg.lower()

    # -- skill="challenge-or-pressure-test" (ambiguous) --

    def test_ambiguous_with_plan(self):
        skill, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "challenge-or-pressure-test", self._pipeline(has_plan=True)
        )
        assert skill == "pressure-test"
        assert "premortem" in msg.lower() or "pre-mortem" in msg.lower()

    def test_ambiguous_with_plan_and_premortem(self):
        skill, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "challenge-or-pressure-test", self._pipeline(has_plan=True, has_premortem=True)
        )
        assert skill == "pressure-test"
        assert "premortem already exists" in msg

    def test_ambiguous_challenge_exists_no_plan(self):
        skill, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "challenge-or-pressure-test",
            self._pipeline(has_challenge=True, has_plan=False),
        )
        assert skill == "pressure-test"
        assert "stress-test" in msg

    def test_ambiguous_proposal_no_challenge(self):
        skill, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "challenge-or-pressure-test",
            self._pipeline(has_proposal=True, has_challenge=False),
        )
        assert skill == "challenge"
        assert "go/no-go" in msg

    def test_ambiguous_no_artifacts(self):
        skill, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "challenge-or-pressure-test", self._pipeline()
        )
        assert skill == "challenge"
        assert "first gate" in msg

    # -- unrecognized skill --

    def test_unrecognized_skill(self):
        skill, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "unknown-skill", self._pipeline()
        )
        assert skill is None
        assert msg is None

    # -- topic label in messages --

    def test_challenge_includes_topic_label(self):
        _, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "challenge", self._pipeline(has_challenge=True, topic="auth-redesign")
        )
        assert "auth-redesign" in msg

    def test_challenge_no_topic_still_works(self):
        _, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "challenge", self._pipeline(has_challenge=False, topic=None)
        )
        assert "go/no-go" in msg

    def test_ambiguous_plan_includes_topic(self):
        _, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "challenge-or-pressure-test",
            self._pipeline(has_plan=True, topic="cache-layer"),
        )
        assert "cache-layer" in msg

    def test_pressure_test_plan_includes_topic(self):
        _, msg = hook_intent_router.resolve_challenge_vs_pressure_test(
            "pressure-test",
            self._pipeline(has_plan=True, topic="api-v2"),
        )
        assert "api-v2" in msg


# ── 4. check_proactive_pipeline_routing() ───────────────────────────────────

class TestCheckProactivePipelineRouting:
    def _pipeline(self, **overrides):
        base = {
            "has_proposal": False,
            "has_challenge": False,
            "has_plan": False,
            "has_pressure_test": False,
            "has_premortem": False,
            "topic": None,
        }
        base.update(overrides)
        return base

    def test_no_topic_returns_empty(self):
        result = hook_intent_router.check_proactive_pipeline_routing(
            self._pipeline(topic=None)
        )
        assert result == []

    def test_proposal_without_challenge(self):
        result = hook_intent_router.check_proactive_pipeline_routing(
            self._pipeline(topic="foo", has_proposal=True, has_challenge=False)
        )
        assert len(result) == 1
        skill_key, msg = result[0]
        assert skill_key == "challenge-proactive"
        assert "foo-proposal.md" in msg

    def test_proposal_with_challenge_no_suggestion(self):
        result = hook_intent_router.check_proactive_pipeline_routing(
            self._pipeline(topic="foo", has_proposal=True, has_challenge=True)
        )
        challenge_suggestions = [s for s in result if s[0] == "challenge-proactive"]
        assert len(challenge_suggestions) == 0

    def test_plan_without_pressure_test(self):
        result = hook_intent_router.check_proactive_pipeline_routing(
            self._pipeline(topic="bar", has_plan=True)
        )
        assert len(result) == 1
        skill_key, msg = result[0]
        assert skill_key == "pressure-test-proactive"
        assert "bar-plan.md" in msg

    def test_plan_with_premortem_no_suggestion(self):
        result = hook_intent_router.check_proactive_pipeline_routing(
            self._pipeline(topic="bar", has_plan=True, has_premortem=True)
        )
        pt_suggestions = [s for s in result if s[0] == "pressure-test-proactive"]
        assert len(pt_suggestions) == 0

    def test_plan_with_pressure_test_no_suggestion(self):
        result = hook_intent_router.check_proactive_pipeline_routing(
            self._pipeline(topic="bar", has_plan=True, has_pressure_test=True)
        )
        pt_suggestions = [s for s in result if s[0] == "pressure-test-proactive"]
        assert len(pt_suggestions) == 0

    def test_both_gaps_returns_two(self):
        result = hook_intent_router.check_proactive_pipeline_routing(
            self._pipeline(
                topic="baz",
                has_proposal=True,
                has_challenge=False,
                has_plan=True,
            )
        )
        assert len(result) == 2
        keys = [s[0] for s in result]
        assert "challenge-proactive" in keys
        assert "pressure-test-proactive" in keys


# ── 5. check_recurring_errors() ─────────────────────────────────────────────

class TestCheckRecurringErrors:
    def test_empty_tracker(self, tmp_path, monkeypatch):
        tracker_path = str(tmp_path / "error-tracker.json")
        monkeypatch.setattr(hook_intent_router, "ERROR_TRACKER_FILE", tracker_path)
        result = hook_intent_router.check_recurring_errors()
        assert result == []

    def test_missing_tracker_file(self, tmp_path, monkeypatch):
        tracker_path = str(tmp_path / "nonexistent.json")
        monkeypatch.setattr(hook_intent_router, "ERROR_TRACKER_FILE", tracker_path)
        result = hook_intent_router.check_recurring_errors()
        assert result == []

    def test_count_below_threshold(self, tmp_path, monkeypatch):
        tracker_path = str(tmp_path / "error-tracker.json")
        with open(tracker_path, "w") as f:
            json.dump({"sig1": {"count": 1, "summary": "one error"}}, f)
        monkeypatch.setattr(hook_intent_router, "ERROR_TRACKER_FILE", tracker_path)
        result = hook_intent_router.check_recurring_errors()
        assert result == []

    def test_count_at_threshold(self, tmp_path, monkeypatch):
        tracker_path = str(tmp_path / "error-tracker.json")
        with open(tracker_path, "w") as f:
            json.dump({"sig1": {"count": 2, "summary": "recurring error"}}, f)
        monkeypatch.setattr(hook_intent_router, "ERROR_TRACKER_FILE", tracker_path)
        result = hook_intent_router.check_recurring_errors()
        assert len(result) == 1
        assert "recurring error" in result[0]

    def test_count_above_threshold(self, tmp_path, monkeypatch):
        tracker_path = str(tmp_path / "error-tracker.json")
        with open(tracker_path, "w") as f:
            json.dump({"sig1": {"count": 5, "summary": "lots of errors"}}, f)
        monkeypatch.setattr(hook_intent_router, "ERROR_TRACKER_FILE", tracker_path)
        result = hook_intent_router.check_recurring_errors()
        assert len(result) == 1

    def test_multiple_recurring(self, tmp_path, monkeypatch):
        tracker_path = str(tmp_path / "error-tracker.json")
        data = {
            "sig1": {"count": 3, "summary": "error A"},
            "sig2": {"count": 2, "summary": "error B"},
            "sig3": {"count": 1, "summary": "not recurring"},
        }
        with open(tracker_path, "w") as f:
            json.dump(data, f)
        monkeypatch.setattr(hook_intent_router, "ERROR_TRACKER_FILE", tracker_path)
        result = hook_intent_router.check_recurring_errors()
        assert len(result) == 2
        summaries = set(result)
        assert "error A" in summaries
        assert "error B" in summaries

    def test_fallback_to_sig_key(self, tmp_path, monkeypatch):
        """When summary is missing, uses the signature key as fallback."""
        tracker_path = str(tmp_path / "error-tracker.json")
        with open(tracker_path, "w") as f:
            json.dump({"my-sig-key": {"count": 3}}, f)
        monkeypatch.setattr(hook_intent_router, "ERROR_TRACKER_FILE", tracker_path)
        result = hook_intent_router.check_recurring_errors()
        assert len(result) == 1
        assert result[0] == "my-sig-key"

    def test_non_dict_entries_skipped(self, tmp_path, monkeypatch):
        """Non-dict tracker entries (e.g. string values) are skipped."""
        tracker_path = str(tmp_path / "error-tracker.json")
        with open(tracker_path, "w") as f:
            json.dump({"sig1": "not a dict", "sig2": 42}, f)
        monkeypatch.setattr(hook_intent_router, "ERROR_TRACKER_FILE", tracker_path)
        result = hook_intent_router.check_recurring_errors()
        assert result == []


# ── 6. load_tracker() and save_tracker() ────────────────────────────────────

class TestTrackerIO:
    def test_load_missing_file(self, tmp_path):
        path = str(tmp_path / "missing.json")
        result = hook_intent_router.load_tracker(path)
        assert result == {}

    def test_load_corrupt_json(self, tmp_path):
        path = str(tmp_path / "corrupt.json")
        with open(path, "w") as f:
            f.write("{not valid json")
        result = hook_intent_router.load_tracker(path)
        assert result == {}

    def test_load_valid_json(self, tmp_path):
        path = str(tmp_path / "valid.json")
        with open(path, "w") as f:
            json.dump({"key": "value", "count": 3}, f)
        result = hook_intent_router.load_tracker(path)
        assert result == {"key": "value", "count": 3}

    def test_save_and_load_roundtrip(self, tmp_path):
        path = str(tmp_path / "roundtrip.json")
        data = {"skill1": 2, "skill2": 1, "nested": {"a": True}}
        hook_intent_router.save_tracker(path, data)
        loaded = hook_intent_router.load_tracker(path)
        assert loaded == data

    def test_save_overwrites(self, tmp_path):
        path = str(tmp_path / "overwrite.json")
        hook_intent_router.save_tracker(path, {"old": 1})
        hook_intent_router.save_tracker(path, {"new": 2})
        loaded = hook_intent_router.load_tracker(path)
        assert loaded == {"new": 2}

    def test_load_empty_dict(self, tmp_path):
        path = str(tmp_path / "empty.json")
        with open(path, "w") as f:
            json.dump({}, f)
        result = hook_intent_router.load_tracker(path)
        assert result == {}


# ── 7. already_suggested() and record_suggestion() ─────────────────────────

class TestSuggestionTracking:
    def test_not_yet_suggested(self, tmp_path, monkeypatch):
        tracker_path = str(tmp_path / "suggestions.json")
        monkeypatch.setattr(hook_intent_router, "SUGGESTION_TRACKER_FILE", tracker_path)
        assert hook_intent_router.already_suggested("investigate") is False

    def test_after_recording(self, tmp_path, monkeypatch):
        tracker_path = str(tmp_path / "suggestions.json")
        monkeypatch.setattr(hook_intent_router, "SUGGESTION_TRACKER_FILE", tracker_path)
        hook_intent_router.record_suggestion("investigate")
        assert hook_intent_router.already_suggested("investigate") is True

    def test_multiple_recordings_increment(self, tmp_path, monkeypatch):
        tracker_path = str(tmp_path / "suggestions.json")
        monkeypatch.setattr(hook_intent_router, "SUGGESTION_TRACKER_FILE", tracker_path)
        hook_intent_router.record_suggestion("review")
        hook_intent_router.record_suggestion("review")
        hook_intent_router.record_suggestion("review")
        tracker = hook_intent_router.load_tracker(tracker_path)
        assert tracker["review"] == 3

    def test_different_skills_independent(self, tmp_path, monkeypatch):
        tracker_path = str(tmp_path / "suggestions.json")
        monkeypatch.setattr(hook_intent_router, "SUGGESTION_TRACKER_FILE", tracker_path)
        hook_intent_router.record_suggestion("review")
        assert hook_intent_router.already_suggested("review") is True
        assert hook_intent_router.already_suggested("investigate") is False
