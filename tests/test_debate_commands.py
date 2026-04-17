"""Integration tests for debate.py command functions.

Tests cmd_challenge, cmd_judge, cmd_review, cmd_explore, cmd_pressure_test,
cmd_refine via monkeypatched LLM calls. No real API calls are made.
"""

import io
import json
import os
import sys
import tempfile
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import debate
import debate_common


# ── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_PROPOSAL = """\
---
topic: test-proposal
created: 2026-04-16
---
# Test Proposal

## Problem
We need to add a widget to the dashboard.

## Current System Failures
Dashboard lacks key metrics visibility.

## Operational Evidence
Tested with 5 users, all requested this feature.

## Approach
Add a React component for the metrics widget.
"""

SAMPLE_CHALLENGE = """\
---
debate_id: test-proposal
created: 2026-04-16T10:00:00-0700
mapping:
  A: claude-opus-4-7
  B: gpt-5.4
  C: gemini-3.1-pro
---
# test-proposal — Challenger Reviews

## Challenger A — Challenges

1. **ASSUMPTION [MATERIAL]:** The proposal assumes React is the right framework.

## Concessions
1. The problem is real.

## Verdict
REVISE

---

## Challenger B — Challenges

1. **RISK [ADVISORY]:** No test plan provided.

## Concessions
1. Widget is well-scoped.

## Verdict
PROCEED

---

## Challenger C — Challenges

1. **OVER-ENGINEERED [ADVISORY]:** A simple chart would suffice.

## Concessions
1. Metrics visibility is important.

## Verdict
PROCEED

---
"""

SAMPLE_DOCUMENT = """\
---
topic: test-doc
---
# Architecture Document

This document describes the system architecture.

## Components
- Frontend: React
- Backend: Python
- Database: PostgreSQL
"""


@pytest.fixture
def fake_credentials(monkeypatch):
    """Monkeypatch _load_credentials to return test values."""
    monkeypatch.setattr(
        debate_common, "_load_credentials",
        lambda: ("test-key", "http://test:4000", False),
    )


@pytest.fixture
def fake_credentials_fallback(monkeypatch):
    """Monkeypatch _load_credentials for fallback mode."""
    monkeypatch.setattr(
        debate_common, "_load_credentials",
        lambda: ("test-key", "http://test:4000", True),
    )


@pytest.fixture
def fake_llm(monkeypatch):
    """Monkeypatch _call_litellm to return canned responses."""
    def _fake_call(model, system_prompt, user_content, litellm_url, api_key,
                   temperature=None, timeout=None):
        return f"Response from {model}: Reviewed the content."

    monkeypatch.setattr(debate, "_call_litellm", _fake_call)


@pytest.fixture
def fake_llm_with_sections(monkeypatch):
    """Monkeypatch _call_litellm to return challenger-style responses."""
    def _fake_call(model, system_prompt, user_content, litellm_url, api_key,
                   temperature=None, timeout=None):
        return (
            "## Challenges\n\n"
            "1. **ASSUMPTION [MATERIAL]:** Test finding from model.\n\n"
            "## Concessions\n\n"
            "1. The approach is sound.\n\n"
            "## Verdict\n\nPROCEED\n"
        )

    monkeypatch.setattr(debate, "_call_litellm", _fake_call)


@pytest.fixture
def fake_config(monkeypatch):
    """Ensure config loads without needing real config file."""
    config = {
        "persona_model_map": {
            "architect": "claude-opus-4-7",
            "security": "gpt-5.4",
            "staff": "gemini-3.1-pro",
            "pm": "gpt-5.4",
        },
        "judge_default": "gpt-5.4",
        "single_review_default": "gpt-5.4",
        "refine_rotation": ["claude-opus-4-7", "gpt-5.4", "gemini-3.1-pro"],
        "fallback_map": {},
    }
    monkeypatch.setattr(debate_common, "_load_config", lambda config_path=None: config)


@pytest.fixture
def tmp_output(tmp_path):
    """Return a temporary output file path."""
    return str(tmp_path / "output.md")


@pytest.fixture
def proposal_file():
    """Return a file-like object with sample proposal."""
    f = io.StringIO(SAMPLE_PROPOSAL)
    f.name = "tasks/test-proposal.md"
    return f


@pytest.fixture
def challenge_file():
    """Return a file-like object with sample challenge."""
    f = io.StringIO(SAMPLE_CHALLENGE)
    f.name = "tasks/test-challenge.md"
    return f


@pytest.fixture
def document_file():
    """Return a file-like object with sample document."""
    f = io.StringIO(SAMPLE_DOCUMENT)
    f.name = "tasks/test-doc.md"
    return f


@pytest.fixture
def suppress_debate_log(monkeypatch, tmp_path):
    """Redirect debate log to temp dir to avoid polluting real stores."""
    log_path = str(tmp_path / "debate-log.jsonl")
    monkeypatch.setattr(
        debate_common, "_log_debate_event",
        lambda event, log_path=None, cost_snapshot=None: None,
    )


# ── cmd_challenge ────────────────────────────────────────────────────────────


class TestCmdChallenge:
    """Tests for cmd_challenge."""

    def test_basic_challenge_with_models(
        self, fake_credentials, fake_llm_with_sections, fake_config,
        tmp_output, proposal_file, suppress_debate_log,
    ):
        args = Namespace(
            proposal=proposal_file,
            models="claude-opus-4-7,gpt-5.4",
            personas=None,
            output=tmp_output,
            system_prompt=None,
            enable_tools=False,
            security_posture=3,
        )
        result = debate.cmd_challenge(args)
        assert result == 0
        output = Path(tmp_output).read_text()
        assert "Challenger A" in output
        assert "Challenger B" in output
        assert "debate_id:" in output

    def test_basic_challenge_with_personas(
        self, fake_credentials, fake_llm_with_sections, fake_config,
        tmp_output, proposal_file, suppress_debate_log,
    ):
        args = Namespace(
            proposal=proposal_file,
            models=None,
            personas="architect,security,staff",
            output=tmp_output,
            system_prompt=None,
            enable_tools=False,
            security_posture=3,
        )
        result = debate.cmd_challenge(args)
        assert result == 0
        output = Path(tmp_output).read_text()
        assert "Challenger A" in output
        assert "Challenger B" in output
        assert "Challenger C" in output

    def test_challenge_empty_proposal(
        self, fake_credentials, fake_llm_with_sections, fake_config,
        tmp_output, suppress_debate_log,
    ):
        empty = io.StringIO("")
        empty.name = "empty.md"
        args = Namespace(
            proposal=empty,
            models="gpt-5.4",
            personas=None,
            output=tmp_output,
            system_prompt=None,
            enable_tools=False,
            security_posture=3,
        )
        result = debate.cmd_challenge(args)
        assert result == 1

    def test_challenge_no_models_or_personas(
        self, fake_credentials, fake_llm_with_sections, fake_config,
        tmp_output, proposal_file, suppress_debate_log,
    ):
        args = Namespace(
            proposal=proposal_file,
            models=None,
            personas=None,
            output=tmp_output,
            system_prompt=None,
            enable_tools=False,
            security_posture=3,
        )
        result = debate.cmd_challenge(args)
        assert result == 1

    def test_challenge_unknown_persona(
        self, fake_credentials, fake_llm_with_sections, fake_config,
        tmp_output, proposal_file, suppress_debate_log,
    ):
        args = Namespace(
            proposal=proposal_file,
            models=None,
            personas="nonexistent",
            output=tmp_output,
            system_prompt=None,
            enable_tools=False,
            security_posture=3,
        )
        result = debate.cmd_challenge(args)
        assert result == 1

    def test_challenge_all_models_fail(
        self, fake_credentials, fake_config, tmp_output,
        proposal_file, suppress_debate_log, monkeypatch,
    ):
        def _fail(model, *a, **kw):
            raise debate.LLMError("timeout", category="timeout")

        monkeypatch.setattr(debate, "_call_litellm", _fail)
        args = Namespace(
            proposal=proposal_file,
            models="model-a,model-b",
            personas=None,
            output=tmp_output,
            system_prompt=None,
            enable_tools=False,
            security_posture=3,
        )
        result = debate.cmd_challenge(args)
        assert result == 2

    def test_challenge_output_has_frontmatter(
        self, fake_credentials, fake_llm_with_sections, fake_config,
        tmp_output, proposal_file, suppress_debate_log,
    ):
        args = Namespace(
            proposal=proposal_file,
            models="claude-opus-4-7,gpt-5.4",
            personas=None,
            output=tmp_output,
            system_prompt=None,
            enable_tools=False,
            security_posture=3,
        )
        debate.cmd_challenge(args)
        output = Path(tmp_output).read_text()
        assert output.startswith("---\n")
        assert "mapping:" in output

    def test_challenge_posture_floor(
        self, fake_credentials, fake_llm_with_sections, fake_config,
        tmp_output, suppress_debate_log,
    ):
        """Proposal with DELETE triggers posture floor."""
        dangerous = io.StringIO("DELETE FROM users WHERE active = 0")
        dangerous.name = "dangerous.md"
        args = Namespace(
            proposal=dangerous,
            models="gpt-5.4",
            personas=None,
            output=tmp_output,
            system_prompt=None,
            enable_tools=False,
            security_posture=1,
        )
        debate.cmd_challenge(args)
        # Posture should have been raised from 1
        assert args.security_posture >= debate_common.SECURITY_FLOOR_MIN


# ── cmd_judge ────────────────────────────────────────────────────────────────


class TestCmdJudge:
    """Tests for cmd_judge."""

    def test_basic_judge(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, proposal_file, challenge_file, suppress_debate_log,
    ):
        args = Namespace(
            proposal=proposal_file,
            challenge=challenge_file,
            model=None,
            rebuttal=None,
            output=tmp_output,
            system_prompt=None,
            verify_claims=False,
            no_consolidate=True,
            use_ma_consolidation=False,
            security_posture=3,
        )
        result = debate.cmd_judge(args)
        assert result == 0
        output = Path(tmp_output).read_text()
        assert len(output) > 0

    def test_judge_empty_proposal(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, challenge_file, suppress_debate_log,
    ):
        empty = io.StringIO("")
        empty.name = "empty.md"
        args = Namespace(
            proposal=empty,
            challenge=challenge_file,
            model=None,
            rebuttal=None,
            output=tmp_output,
            system_prompt=None,
            verify_claims=False,
            no_consolidate=True,
            use_ma_consolidation=False,
            security_posture=3,
        )
        result = debate.cmd_judge(args)
        assert result == 1

    def test_judge_no_frontmatter(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, proposal_file, suppress_debate_log,
    ):
        bad_challenge = io.StringIO("No frontmatter here, just text.")
        bad_challenge.name = "bad.md"
        args = Namespace(
            proposal=proposal_file,
            challenge=bad_challenge,
            model=None,
            rebuttal=None,
            output=tmp_output,
            system_prompt=None,
            verify_claims=False,
            no_consolidate=True,
            use_ma_consolidation=False,
            security_posture=3,
        )
        result = debate.cmd_judge(args)
        assert result == 1

    def test_judge_custom_model(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, proposal_file, suppress_debate_log,
    ):
        challenge = io.StringIO(SAMPLE_CHALLENGE)
        challenge.name = "challenge.md"
        args = Namespace(
            proposal=proposal_file,
            challenge=challenge,
            model="gemini-3.1-pro",
            rebuttal=None,
            output=tmp_output,
            system_prompt=None,
            verify_claims=False,
            no_consolidate=True,
            use_ma_consolidation=False,
            security_posture=3,
        )
        result = debate.cmd_judge(args)
        assert result == 0


# ── cmd_review ───────────────────────────────────────────────────────────────


class TestCmdReview:
    """Tests for cmd_review."""

    def test_single_persona_review(
        self, fake_credentials, fake_llm, fake_config,
        suppress_debate_log,
    ):
        input_file = io.StringIO(SAMPLE_DOCUMENT)
        input_file.name = "doc.md"
        args = Namespace(
            command="review",
            persona="pm",
            personas=None,
            model=None,
            models=None,
            prompt="Review this for completeness",
            prompt_file=None,
            input=input_file,
            enable_tools=False,
            allowed_tools=None,
            security_posture=3,
        )
        result = debate.cmd_review(args)
        assert result == 0

    def test_single_model_review(
        self, fake_credentials, fake_llm, fake_config,
        suppress_debate_log,
    ):
        input_file = io.StringIO(SAMPLE_DOCUMENT)
        input_file.name = "doc.md"
        args = Namespace(
            command="review",
            persona=None,
            personas=None,
            model="gpt-5.4",
            models=None,
            prompt="Review this",
            prompt_file=None,
            input=input_file,
            enable_tools=False,
            allowed_tools=None,
            security_posture=3,
        )
        result = debate.cmd_review(args)
        assert result == 0

    def test_review_empty_input(
        self, fake_credentials, fake_llm, fake_config,
        suppress_debate_log,
    ):
        empty = io.StringIO("")
        empty.name = "empty.md"
        args = Namespace(
            command="review",
            persona="pm",
            personas=None,
            model=None,
            models=None,
            prompt="Review",
            prompt_file=None,
            input=empty,
            enable_tools=False,
            allowed_tools=None,
            security_posture=3,
        )
        result = debate.cmd_review(args)
        assert result == 1

    def test_review_no_prompt(
        self, fake_credentials, fake_llm, fake_config,
        suppress_debate_log,
    ):
        input_file = io.StringIO(SAMPLE_DOCUMENT)
        input_file.name = "doc.md"
        args = Namespace(
            command="review",
            persona="pm",
            personas=None,
            model=None,
            models=None,
            prompt=None,
            prompt_file=None,
            input=input_file,
            enable_tools=False,
            allowed_tools=None,
            security_posture=3,
        )
        result = debate.cmd_review(args)
        assert result == 1

    def test_review_no_model_flags(
        self, fake_credentials, fake_llm, fake_config,
        suppress_debate_log,
    ):
        input_file = io.StringIO(SAMPLE_DOCUMENT)
        input_file.name = "doc.md"
        args = Namespace(
            command="review",
            persona=None,
            personas=None,
            model=None,
            models=None,
            prompt="Review",
            prompt_file=None,
            input=input_file,
            enable_tools=False,
            allowed_tools=None,
            security_posture=3,
        )
        result = debate.cmd_review(args)
        assert result == 1

    def test_review_llm_returns_empty(
        self, fake_credentials, fake_config, suppress_debate_log,
        monkeypatch,
    ):
        def _empty(*a, **kw):
            return ""

        monkeypatch.setattr(debate, "_call_litellm", _empty)
        input_file = io.StringIO(SAMPLE_DOCUMENT)
        input_file.name = "doc.md"
        args = Namespace(
            command="review",
            persona="pm",
            personas=None,
            model=None,
            models=None,
            prompt="Review",
            prompt_file=None,
            input=input_file,
            enable_tools=False,
            allowed_tools=None,
            security_posture=3,
        )
        result = debate.cmd_review(args)
        assert result == 1


# ── cmd_explore ──────────────────────────────────────────────────────────────


class TestCmdExplore:
    """Tests for cmd_explore."""

    def test_basic_explore(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, suppress_debate_log,
    ):
        args = Namespace(
            question="What are the options for caching?",
            directions=2,
            model=None,
            synth_model=None,
            context=None,
            output=tmp_output,
            security_posture=3,
        )
        result = debate.cmd_explore(args)
        assert result == 0
        output = Path(tmp_output).read_text()
        assert len(output) > 0

    def test_explore_empty_question(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, suppress_debate_log,
    ):
        args = Namespace(
            question="",
            directions=3,
            model=None,
            synth_model=None,
            context=None,
            output=tmp_output,
            security_posture=3,
        )
        result = debate.cmd_explore(args)
        assert result == 1

    def test_explore_with_context(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, suppress_debate_log,
    ):
        args = Namespace(
            question="How should we handle auth?",
            directions=2,
            model="gpt-5.4",
            synth_model=None,
            context="We use OAuth2 currently. Team prefers JWT.",
            output=tmp_output,
            security_posture=3,
        )
        result = debate.cmd_explore(args)
        assert result == 0

    def test_explore_with_dimensions(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, suppress_debate_log,
    ):
        args = Namespace(
            question="What are the options?",
            directions=2,
            model=None,
            synth_model=None,
            context="DIMENSIONS:\nApproach\nScope\nTradeoff\nPRE-FLIGHT CONTEXT:\nSome context here",
            output=tmp_output,
            security_posture=3,
        )
        result = debate.cmd_explore(args)
        assert result == 0


# ── cmd_pressure_test ────────────────────────────────────────────────────────


class TestCmdPressureTest:
    """Tests for cmd_pressure_test."""

    def test_basic_pressure_test(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, proposal_file, suppress_debate_log,
    ):
        args = Namespace(
            proposal=proposal_file,
            frame="challenge",
            model=None,
            models=None,
            synthesis_model=None,
            context=None,
            output=tmp_output,
            security_posture=3,
        )
        result = debate.cmd_pressure_test(args)
        assert result == 0
        output = Path(tmp_output).read_text()
        assert "mode: pressure-test" in output

    def test_premortem_frame(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, proposal_file, suppress_debate_log,
    ):
        args = Namespace(
            proposal=proposal_file,
            frame="premortem",
            model=None,
            models=None,
            synthesis_model=None,
            context=None,
            output=tmp_output,
            security_posture=3,
        )
        result = debate.cmd_pressure_test(args)
        assert result == 0
        output = Path(tmp_output).read_text()
        assert "mode: pre-mortem" in output

    def test_pressure_test_empty_input(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, suppress_debate_log,
    ):
        empty = io.StringIO("")
        empty.name = "empty.md"
        args = Namespace(
            proposal=empty,
            frame="challenge",
            model=None,
            models=None,
            synthesis_model=None,
            context=None,
            output=tmp_output,
            security_posture=3,
        )
        result = debate.cmd_pressure_test(args)
        assert result == 1

    def test_pressure_test_model_and_models_exclusive(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, proposal_file, suppress_debate_log,
    ):
        args = Namespace(
            proposal=proposal_file,
            frame="challenge",
            model="gpt-5.4",
            models="claude-opus-4-7,gemini-3.1-pro",
            synthesis_model=None,
            context=None,
            output=tmp_output,
            security_posture=3,
        )
        result = debate.cmd_pressure_test(args)
        assert result == 1

    def test_pressure_test_models_needs_two(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, proposal_file, suppress_debate_log,
    ):
        args = Namespace(
            proposal=proposal_file,
            frame="challenge",
            model=None,
            models="only-one-model",
            synthesis_model=None,
            context=None,
            output=tmp_output,
            security_posture=3,
        )
        result = debate.cmd_pressure_test(args)
        assert result == 1

    def test_pressure_test_models_must_be_distinct(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, proposal_file, suppress_debate_log,
    ):
        args = Namespace(
            proposal=proposal_file,
            frame="challenge",
            model=None,
            models="gpt-5.4,gpt-5.4",
            synthesis_model=None,
            context=None,
            output=tmp_output,
            security_posture=3,
        )
        result = debate.cmd_pressure_test(args)
        assert result == 1

    def test_multi_model_pressure_test(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, suppress_debate_log,
    ):
        proposal = io.StringIO(SAMPLE_PROPOSAL)
        proposal.name = "proposal.md"
        args = Namespace(
            proposal=proposal,
            frame="challenge",
            model=None,
            models="claude-opus-4-7,gpt-5.4",
            synthesis_model=None,
            context=None,
            output=tmp_output,
            security_posture=3,
        )
        result = debate.cmd_pressure_test(args)
        assert result == 0
        output = Path(tmp_output).read_text()
        assert "Analyst A" in output or "mode:" in output


# ── cmd_refine ───────────────────────────────────────────────────────────────


class TestCmdRefine:
    """Tests for cmd_refine."""

    def test_basic_refine(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, document_file, suppress_debate_log,
    ):
        args = Namespace(
            document=document_file,
            mode=None,
            rounds=1,
            models=None,
            judgment=None,
            output=tmp_output,
            enable_tools=False,
            early_stop=False,
            security_posture=3,
        )
        result = debate.cmd_refine(args)
        assert result == 0
        output = Path(tmp_output).read_text()
        assert len(output) > 0

    def test_refine_empty_document(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, suppress_debate_log,
    ):
        empty = io.StringIO("")
        empty.name = "empty.md"
        args = Namespace(
            document=empty,
            mode=None,
            rounds=1,
            models=None,
            judgment=None,
            output=tmp_output,
            enable_tools=False,
            early_stop=False,
            security_posture=3,
        )
        result = debate.cmd_refine(args)
        assert result == 1

    def test_refine_explicit_proposal_mode(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, suppress_debate_log,
    ):
        doc = io.StringIO(SAMPLE_PROPOSAL)
        doc.name = "proposal.md"
        args = Namespace(
            document=doc,
            mode="proposal",
            rounds=1,
            models=None,
            judgment=None,
            output=tmp_output,
            enable_tools=False,
            early_stop=False,
            security_posture=3,
        )
        result = debate.cmd_refine(args)
        assert result == 0

    def test_refine_with_judgment(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, suppress_debate_log,
    ):
        doc = io.StringIO(SAMPLE_PROPOSAL)
        doc.name = "proposal.md"
        judgment = io.StringIO("## Judgment\n\nPROCEED with conditions.\n")
        judgment.name = "judgment.md"
        args = Namespace(
            document=doc,
            mode=None,
            rounds=1,
            models=None,
            judgment=judgment,
            output=tmp_output,
            enable_tools=False,
            early_stop=False,
            security_posture=3,
        )
        result = debate.cmd_refine(args)
        assert result == 0


# ── cmd_premortem ────────────────────────────────────────────────────────────


class TestCmdPremortem:
    """Tests for cmd_premortem shim."""

    def test_premortem_delegates_to_pressure_test(
        self, fake_credentials, fake_llm, fake_config,
        tmp_output, suppress_debate_log,
    ):
        plan = io.StringIO(SAMPLE_PROPOSAL)
        plan.name = "plan.md"
        args = Namespace(
            plan=plan,
            model=None,
            models=None,
            synthesis_model=None,
            context=None,
            output=tmp_output,
            security_posture=3,
        )
        result = debate.cmd_premortem(args)
        assert result == 0
        assert args.frame == "premortem"
        output = Path(tmp_output).read_text()
        assert "mode: pre-mortem" in output


# ── cmd_outcome_update ───────────────────────────────────────────────────────


class TestCmdOutcomeUpdate:
    """Tests for cmd_outcome_update."""

    def test_basic_outcome_update(
        self, suppress_debate_log,
    ):
        args = Namespace(
            debate_id="test-proposal",
            recommendation=1,
            implementation_status="shipped",
            validation_status="verified",
            reversal=False,
            downstream_issues=0,
            notes="Shipped successfully",
        )
        result = debate.cmd_outcome_update(args)
        assert result == 0


# ── Credential failures ─────────────────────────────────────────────────────


class TestCredentialFailures:
    """Commands should return 1 when credentials are missing."""

    def _no_creds(self):
        return (None, None, False)

    def test_challenge_no_creds(self, monkeypatch, tmp_output, proposal_file):
        monkeypatch.setattr(debate_common, "_load_credentials", self._no_creds)
        args = Namespace(
            proposal=proposal_file,
            models="gpt-5.4",
            personas=None,
            output=tmp_output,
            system_prompt=None,
            enable_tools=False,
            security_posture=3,
        )
        assert debate.cmd_challenge(args) == 1

    def test_judge_no_creds(self, monkeypatch, tmp_output, proposal_file, challenge_file):
        monkeypatch.setattr(debate_common, "_load_credentials", self._no_creds)
        args = Namespace(
            proposal=proposal_file,
            challenge=challenge_file,
            model=None,
            rebuttal=None,
            output=tmp_output,
            system_prompt=None,
            verify_claims=False,
            no_consolidate=True,
            use_ma_consolidation=False,
            security_posture=3,
        )
        assert debate.cmd_judge(args) == 1

    def test_review_no_creds(self, monkeypatch):
        monkeypatch.setattr(debate_common, "_load_credentials", self._no_creds)
        input_file = io.StringIO(SAMPLE_DOCUMENT)
        input_file.name = "doc.md"
        args = Namespace(
            command="review",
            persona="pm",
            personas=None,
            model=None,
            models=None,
            prompt="Review",
            prompt_file=None,
            input=input_file,
            enable_tools=False,
            allowed_tools=None,
            security_posture=3,
        )
        assert debate.cmd_review(args) == 1

    def test_explore_no_creds(self, monkeypatch, tmp_output):
        monkeypatch.setattr(debate_common, "_load_credentials", self._no_creds)
        args = Namespace(
            question="test?",
            directions=2,
            model=None,
            synth_model=None,
            context=None,
            output=tmp_output,
            security_posture=3,
        )
        assert debate.cmd_explore(args) == 1

    def test_pressure_test_no_creds(self, monkeypatch, tmp_output, proposal_file):
        monkeypatch.setattr(debate_common, "_load_credentials", self._no_creds)
        args = Namespace(
            proposal=proposal_file,
            frame="challenge",
            model=None,
            models=None,
            synthesis_model=None,
            context=None,
            output=tmp_output,
            security_posture=3,
        )
        assert debate.cmd_pressure_test(args) == 1

    def test_refine_no_creds(self, monkeypatch, tmp_output, document_file):
        monkeypatch.setattr(debate_common, "_load_credentials", self._no_creds)
        args = Namespace(
            document=document_file,
            mode=None,
            rounds=1,
            models=None,
            judgment=None,
            output=tmp_output,
            enable_tools=False,
            early_stop=False,
            security_posture=3,
        )
        assert debate.cmd_refine(args) == 1
