"""Smoke tests for scripts/debate.py.

Catches argparse-wiring, import, and constant-existence regressions.
NOT a behavioral test — it does not run actual LLM calls. Pairs with the
AST linter (test_tool_loop_config.py) which catches static-pattern
regressions.

Why this exists: debate.py has ~2500 lines and historically had no
behavioral test coverage. The 2026-04-09 cleanup touches ~30 sites; smoke
tests are the cheapest possible regression guard. Cross-model challenge
synthesis (debate-py-bandaid-cleanup) flagged this gap explicitly.

Run with: python3.11 tests/test_debate_smoke.py
Exit 0 = all smoke tests pass.
Exit 1 = at least one smoke test failed.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEBATE_PY = REPO_ROOT / "scripts" / "debate.py"
SCRIPTS_DIR = REPO_ROOT / "scripts"


def test_constants_exist():
    """LLM_SAFE_EXCEPTIONS, LLM_CALL_DEFAULTS, TOOL_LOOP_DEFAULTS must exist
    with expected shape after the 2026-04-09 cleanup.
    """
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        # Force a fresh import in case a prior test imported the old version
        if "debate" in sys.modules:
            del sys.modules["debate"]
        import debate

        assert hasattr(debate, "LLM_SAFE_EXCEPTIONS"), "LLM_SAFE_EXCEPTIONS missing"
        assert isinstance(debate.LLM_SAFE_EXCEPTIONS, tuple)
        assert debate.LLMError in debate.LLM_SAFE_EXCEPTIONS
        assert TimeoutError in debate.LLM_SAFE_EXCEPTIONS

        assert hasattr(debate, "LLM_CALL_DEFAULTS"), "LLM_CALL_DEFAULTS missing"
        for key in (
            "timeout",
            "max_tokens",
            "judge_temperature",
            "challenger_temperature_default",
            "challenger_temperature_per_model",
            "consolidation_max_tokens",
        ):
            assert key in debate.LLM_CALL_DEFAULTS, f"LLM_CALL_DEFAULTS missing key: {key}"
        assert isinstance(
            debate.LLM_CALL_DEFAULTS["challenger_temperature_per_model"], dict
        ), "challenger_temperature_per_model must be a dict"

        assert hasattr(debate, "TOOL_LOOP_DEFAULTS"), "TOOL_LOOP_DEFAULTS missing"
        for key in ("timeout", "max_tokens", "max_turns"):
            assert key in debate.TOOL_LOOP_DEFAULTS, f"TOOL_LOOP_DEFAULTS missing key: {key}"

        # Helper introduced in the cleanup
        assert hasattr(debate, "_challenger_temperature"), "_challenger_temperature helper missing"
        # Per-model: gemini gets 1.0, others get the default
        assert debate._challenger_temperature("gemini-3.1-pro") == 1.0
        assert debate._challenger_temperature("gpt-5.4") == debate.LLM_CALL_DEFAULTS[
            "challenger_temperature_default"
        ]
    finally:
        sys.path.pop(0)


def test_load_config_includes_compare_default():
    """compare_default must resolve through _load_config (not hardcoded)."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        if "debate" in sys.modules:
            del sys.modules["debate"]
        import debate  # noqa: F401  (loads side-effects)
        import debate_common
        config = debate_common._load_config()
        assert "compare_default" in config, "compare_default missing from _load_config output"
        assert "judge_default" in config, "judge_default missing from _load_config output"
        # compare and judge should be distinct concepts (compare is lighter)
        # They may or may not be different models — what matters is that both
        # keys exist and are resolvable.
    finally:
        sys.path.pop(0)


def _run_help(subcommand):
    return subprocess.run(
        ["python3.11", str(DEBATE_PY), subcommand, "--help"],
        capture_output=True, text=True, timeout=15,
    )


def test_subcommand_help_works():
    """Every subcommand must respond to --help without crashing.

    This catches argparse-wiring regressions: a typo in `add_argument`,
    a missing default, or a malformed help string will fail here.
    """
    subcommands = [
        "challenge",
        "judge",
        "refine",
        "review",
        "review-panel",
        "compare",
        "check-models",
        "outcome-update",
        "verdict",
        "stats",
    ]
    failures = []
    for sub in subcommands:
        result = _run_help(sub)
        if result.returncode != 0:
            failures.append(
                f"  {sub}: exit {result.returncode}\n    stderr: {result.stderr[:300]}"
            )
    assert not failures, "Subcommand --help failures:\n" + "\n".join(failures)


def test_top_level_help_works():
    """`debate.py --help` must work."""
    result = subprocess.run(
        ["python3.11", str(DEBATE_PY), "--help"],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, f"top-level --help failed: {result.stderr[:300]}"


def test_judge_default_is_none_not_hardcoded():
    """Verify the dead-code fix: argparse default for `judge --model` should
    be None so that config[\"judge_default\"] resolves it.
    """
    result = subprocess.run(
        ["python3.11", str(DEBATE_PY), "judge", "--help"],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0
    # Help string should reference config, not a hardcoded model name
    assert "config" in result.stdout.lower() or "judge_default" in result.stdout, (
        "judge --help should reference config-driven default; "
        f"got: {result.stdout}"
    )


def test_compare_default_is_none_not_hardcoded():
    """Verify the dead-code fix for compare: argparse default should be None."""
    result = subprocess.run(
        ["python3.11", str(DEBATE_PY), "compare", "--help"],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0
    assert "config" in result.stdout.lower() or "compare_default" in result.stdout, (
        "compare --help should reference config-driven default; "
        f"got: {result.stdout}"
    )


TESTS = [
    test_constants_exist,
    test_load_config_includes_compare_default,
    test_top_level_help_works,
    test_subcommand_help_works,
    test_judge_default_is_none_not_hardcoded,
    test_compare_default_is_none_not_hardcoded,
]


def main():
    failures = []
    for fn in TESTS:
        name = fn.__name__
        try:
            fn()
            print(f"PASS: {name}")
        except AssertionError as e:
            print(f"FAIL: {name} — {e}", file=sys.stderr)
            failures.append((name, str(e)))
        except Exception as e:
            print(f"ERROR: {name} — {type(e).__name__}: {e}", file=sys.stderr)
            failures.append((name, f"{type(e).__name__}: {e}"))

    if failures:
        print(f"\n{len(failures)} test(s) failed", file=sys.stderr)
        return 1
    print(f"\nAll {len(TESTS)} smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
