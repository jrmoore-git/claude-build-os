"""Smoke tests for debate.py challenge --config flag.

Verifies that (a) the CLI arg parses, and (b) cmd_challenge threads
args.config through to debate_common._load_config(config_path=...).

No real API calls; uses the same monkeypatched-LLM pattern as
tests/test_debate_commands.py.
"""

import io
import json
import sys
from argparse import Namespace
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import debate
import debate_common


SAMPLE_PROPOSAL = """\
---
topic: test-proposal
created: 2026-04-19
---
# Test Proposal

## Problem
Need to verify --config routing.

## Current System Failures
N/A

## Operational Evidence
N/A

## Approach
Smoke test only.
"""


@pytest.fixture
def fake_credentials(monkeypatch):
    monkeypatch.setattr(
        debate_common, "_load_credentials",
        lambda: ("fake-key", "http://fake-litellm:4000", False),
    )


@pytest.fixture
def fake_llm(monkeypatch):
    def _fake_call(model, system_prompt, user_content, litellm_url, api_key,
                   temperature=None, timeout=None, max_tokens=None,
                   cache_control=None, cache_ttl=None):
        return (
            "## Challenges\n\n"
            "1. **ASSUMPTION [MATERIAL]:** Test finding.\n\n"
            "## Concessions\n\n"
            "1. Smoke only.\n\n"
            "## Verdict\n\nPROCEED\n"
        )
    monkeypatch.setattr(debate, "_call_litellm", _fake_call)


@pytest.fixture
def suppress_debate_log(monkeypatch):
    monkeypatch.setattr(
        debate_common, "_log_debate_event",
        lambda event, log_path=None, cost_snapshot=None: None,
    )


@pytest.fixture
def proposal_file():
    f = io.StringIO(SAMPLE_PROPOSAL)
    f.name = "tasks/test-proposal.md"
    return f


@pytest.fixture
def config_path_capture(monkeypatch):
    """Monkeypatch _load_config to capture the config_path it's called with."""
    captured = {"path": "UNCALLED"}

    def _capturing_load(config_path=None):
        captured["path"] = config_path
        return {
            "persona_model_map": {
                "architect": "claude-opus-4-6",
                "security": "gpt-5.4",
                "pm": "gemini-3.1-pro",
                "frame": "claude-sonnet-4-6",
                "staff": "claude-opus-4-6",
            },
            "judge_default": "gpt-5.4",
            "single_review_default": "gpt-5.4",
            "refine_rotation": ["claude-opus-4-6", "gpt-5.4", "gemini-3.1-pro"],
            "frame_factual_model": "gpt-5.4",
            "fallback_map": {},
        }

    monkeypatch.setattr(debate_common, "_load_config", _capturing_load)
    return captured


def test_cli_parser_accepts_config_flag():
    """argparse must accept --config on the challenge subcommand."""
    parser = debate.build_parser() if hasattr(debate, "build_parser") else None
    # Fall back to running the CLI help via argparse directly
    import argparse
    # Walk the source to confirm the arg was registered: we can parse a
    # minimal invocation and check that --config is present in the namespace.
    # Use the module's main argparse via main(argv=[...]) only if exposed;
    # otherwise check via the subparser definition indirectly.
    # Simplest: invoke --help and assert --config appears in output.
    import subprocess
    result = subprocess.run(
        ["python3.11", str(SCRIPTS_DIR / "debate.py"), "challenge", "--help"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, f"debate.py challenge --help failed: {result.stderr}"
    assert "--config" in result.stdout, (
        f"--config flag not in challenge --help output:\n{result.stdout}"
    )


def test_cmd_challenge_threads_config_to_load_config(
    fake_credentials, fake_llm, suppress_debate_log,
    proposal_file, config_path_capture, tmp_path,
):
    """cmd_challenge(args) with args.config=<path> must call
    debate_common._load_config(<path>), not _load_config(None)."""
    custom_config = str(tmp_path / "custom-arm.json")
    output_path = str(tmp_path / "output.md")

    args = Namespace(
        proposal=proposal_file,
        models=None,
        personas="architect",
        output=output_path,
        system_prompt=None,
        enable_tools=False,
        security_posture=3,
        config=custom_config,
    )

    result = debate.cmd_challenge(args)
    assert result == 0, "cmd_challenge returned non-zero"
    assert config_path_capture["path"] == custom_config, (
        f"Expected _load_config called with {custom_config!r}, "
        f"got {config_path_capture['path']!r}"
    )


def test_cmd_challenge_defaults_to_none_when_config_absent(
    fake_credentials, fake_llm, suppress_debate_log,
    proposal_file, config_path_capture, tmp_path,
):
    """cmd_challenge(args) without args.config must call _load_config(None)
    so the default config path is used. Backward-compatibility invariant."""
    output_path = str(tmp_path / "output.md")

    args = Namespace(
        proposal=proposal_file,
        models=None,
        personas="architect",
        output=output_path,
        system_prompt=None,
        enable_tools=False,
        security_posture=3,
        # Intentionally no 'config' attribute — getattr(args, "config", None)
        # must fall through to None.
    )

    result = debate.cmd_challenge(args)
    assert result == 0
    assert config_path_capture["path"] is None, (
        f"Expected _load_config called with None (default), "
        f"got {config_path_capture['path']!r}"
    )
