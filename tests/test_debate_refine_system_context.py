"""Tests for cmd_refine's --system-context flag and round-count aggregation.

Covers the L57 fix surface:
- `--system-context` is registered on refine, binds to `args.system_context`,
  and is read verbatim with no ACCEPT-block filtering (unlike `--judgment`).
- `_aggregate_round_counts` partitions round notes into mutually-exclusive
  buckets (completed = failed + discarded + successful) so the polish skill's
  sanity check (`rounds_successful == 0`) is robust to mixed failure modes.
"""
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import debate


class TestAggregateRoundCounts:
    def test_all_successful(self):
        notes = [{"notes": "revised ok", "truncated": False, "slots_dropped": False}
                 for _ in range(6)]
        counts = debate._aggregate_round_counts(notes)
        assert counts == {"completed": 6, "failed": 0, "discarded": 0, "successful": 6}

    def test_all_errored(self):
        notes = [{"notes": "[ERROR: timeout]", "errored": True} for _ in range(6)]
        counts = debate._aggregate_round_counts(notes)
        assert counts == {"completed": 6, "failed": 6, "discarded": 0, "successful": 0}

    def test_all_truncated(self):
        notes = [{"notes": "promoted notes\n\n[NOTE: revision discarded as truncated]",
                  "truncated": True, "slots_dropped": False}
                 for _ in range(6)]
        counts = debate._aggregate_round_counts(notes)
        assert counts == {"completed": 6, "failed": 0, "discarded": 6, "successful": 0}

    def test_all_slots_dropped(self):
        notes = [{"notes": "kept notes",
                  "truncated": False, "slots_dropped": True}
                 for _ in range(3)]
        counts = debate._aggregate_round_counts(notes)
        assert counts == {"completed": 3, "failed": 0, "discarded": 3, "successful": 0}

    def test_mixed_error_and_truncated_covers_sanity_check_bug(self):
        """Regression test for the bug PM lens caught: a mix of 5 truncated + 1
        errored round means zero successful refinements, but the naive check
        `rounds_discarded == rounds_completed` (5 == 6) evaluates false. The
        correct check is `rounds_successful == 0`."""
        notes = [
            {"notes": "note", "truncated": True, "slots_dropped": False},
            {"notes": "note", "truncated": True, "slots_dropped": False},
            {"notes": "note", "truncated": True, "slots_dropped": False},
            {"notes": "note", "truncated": True, "slots_dropped": False},
            {"notes": "note", "truncated": True, "slots_dropped": False},
            {"notes": "[ERROR: rate limited]", "errored": True},
        ]
        counts = debate._aggregate_round_counts(notes)
        assert counts["completed"] == 6
        assert counts["failed"] == 1
        assert counts["discarded"] == 5
        assert counts["successful"] == 0

    def test_mixed_success_failed_discarded(self):
        notes = [
            {"notes": "good", "truncated": False, "slots_dropped": False},
            {"notes": "good", "truncated": False, "slots_dropped": False},
            {"notes": "trunc", "truncated": True, "slots_dropped": False},
            {"notes": "[ERROR: 503]", "errored": True},
            {"notes": "slots", "truncated": False, "slots_dropped": True},
            {"notes": "good", "truncated": False, "slots_dropped": False},
        ]
        counts = debate._aggregate_round_counts(notes)
        assert counts == {"completed": 6, "failed": 1, "discarded": 2, "successful": 3}

    def test_empty_notes(self):
        assert debate._aggregate_round_counts([]) == {
            "completed": 0, "failed": 0, "discarded": 0, "successful": 0}

    def test_missing_flags_treated_as_false(self):
        """Error rounds have the explicit `errored` key but not truncated/
        slots_dropped. `.get()` must handle missing keys without crashing —
        missing keys are falsy, not discarded."""
        notes = [{"notes": "[ERROR: x]", "errored": True}]
        counts = debate._aggregate_round_counts(notes)
        assert counts["failed"] == 1
        assert counts["discarded"] == 0

    def test_errored_round_with_truncated_flag_is_not_double_counted(self):
        """Defensive: if a future code path sets both `errored: True` and
        `truncated: True` on the same round note, the round must count as
        errored only — not as both errored and discarded. Preserves the
        mutual-exclusivity invariant even under pathological inputs."""
        notes = [
            {"notes": "[ERROR: x]", "errored": True, "truncated": True, "slots_dropped": False},
        ]
        counts = debate._aggregate_round_counts(notes)
        assert counts == {"completed": 1, "failed": 1, "discarded": 0, "successful": 0}

    def test_partition_is_mutually_exclusive(self):
        """completed == failed + discarded + successful, always. The polish
        sanity check depends on this invariant."""
        notes = [
            {"notes": "good", "truncated": False, "slots_dropped": False},
            {"notes": "trunc", "truncated": True, "slots_dropped": False},
            {"notes": "[ERROR: x]", "errored": True},
            {"notes": "both_flags", "truncated": True, "slots_dropped": True},
        ]
        counts = debate._aggregate_round_counts(notes)
        assert counts["completed"] == (
            counts["failed"] + counts["discarded"] + counts["successful"]
        )

    def test_error_classification_does_not_rely_on_notes_prefix(self):
        """Regression guard: `_aggregate_round_counts` must use the explicit
        `errored` flag, not `notes.startswith("[ERROR:")`. If a future change
        alters the error-note wording (emojis, localization, richer rendering),
        the metric must not silently break."""
        notes = [
            {"notes": "something went wrong without the ERROR prefix",
             "errored": True, "truncated": False, "slots_dropped": False},
            {"notes": "[ERROR: but errored flag missing — should NOT count as failed]",
             "truncated": False, "slots_dropped": False},
        ]
        counts = debate._aggregate_round_counts(notes)
        assert counts["failed"] == 1  # only the first, despite second having ERROR prefix
        assert counts["successful"] == 1  # second is treated as successful (no flags)


class TestSystemContextFlag:
    def _make_parser(self):
        """Build the refine subparser in isolation to test argparse wiring."""
        import argparse
        p = argparse.ArgumentParser()
        sub = p.add_subparsers(dest="cmd")
        rf = sub.add_parser("refine")
        rf.add_argument("--document", type=argparse.FileType("r"), required=True)
        rf.add_argument("--system-context", dest="system_context",
                        type=argparse.FileType("r"), default=None)
        rf.add_argument("--judgment", type=argparse.FileType("r"), default=None)
        rf.add_argument("--output", required=True)
        return p

    def test_system_context_flag_registered_on_real_parser(self):
        """Verify the real debate.py parser accepts --system-context."""
        parser = debate._build_parser() if hasattr(debate, "_build_parser") else None
        # debate.py builds argparse inline in main(); test via help text instead
        import subprocess
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "debate.py"), "refine", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "--system-context" in result.stdout
        assert "verbatim" in result.stdout.lower()
        assert "no filtering" in result.stdout.lower()

    def test_system_context_help_warns_about_judgment_filter(self):
        """--judgment help text should point callers at --system-context so the
        silent-drop footgun doesn't re-emerge."""
        import subprocess
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "debate.py"), "refine", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        # --judgment section must warn about filtering AND name the escape hatch
        assert "ACCEPT" in result.stdout
        assert "--system-context" in result.stdout

    def test_system_context_binds_file_handle(self):
        """Confirm argparse produces a readable handle, not a path string."""
        parser = self._make_parser()
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as ctx:
            ctx.write("## Project Context\nSome background info.\n")
            ctx_path = ctx.name
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as doc:
            doc.write("# Doc\nbody\n")
            doc_path = doc.name
        try:
            args = parser.parse_args([
                "refine", "--document", doc_path,
                "--system-context", ctx_path,
                "--output", "/tmp/unused.md",
            ])
            assert args.system_context is not None
            content = args.system_context.read()
            assert "Project Context" in content
            assert "Some background info." in content
        finally:
            Path(ctx_path).unlink(missing_ok=True)
            Path(doc_path).unlink(missing_ok=True)

    def test_system_context_default_is_none(self):
        """When not provided, the attribute must be None — cmd_refine checks
        `getattr(args, "system_context", None)` and skips loading if falsy."""
        parser = self._make_parser()
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as doc:
            doc.write("# Doc\n")
            doc_path = doc.name
        try:
            args = parser.parse_args([
                "refine", "--document", doc_path,
                "--output", "/tmp/unused.md",
            ])
            assert args.system_context is None
        finally:
            Path(doc_path).unlink(missing_ok=True)
