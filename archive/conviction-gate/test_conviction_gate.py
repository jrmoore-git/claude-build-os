#!/usr/bin/env python3.11
"""Tests for scripts/check_conviction_gate.py."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_conviction_gate.py"
PYTHON = "/opt/homebrew/bin/python3.11"


def run_gate(proposal_path):
    """Run the gate and return (exit_code, parsed_json_report)."""
    result = subprocess.run(
        [PYTHON, str(SCRIPT), "--proposal", proposal_path, "--json"],
        capture_output=True,
        text=True,
    )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        report = None
    return result.returncode, report, result.stdout, result.stderr


def write_proposal(tmpdir, body):
    path = Path(tmpdir) / "proposal.md"
    path.write_text(body, encoding="utf-8")
    return str(path)


PASS_BODY = """# Velocity v3 proposal

## Summary
Stuff.

## Methodology
- Cycle time: p90 from merged PR data
- Incident rate: count per week

## Recommendations

1. Run a cycle-time reduction pilot on the payments squad.
   - Owner: Platform team lead
   - Horizon: this quarter
   - Why now: p90 cycle time exceeds 14 days

2. Add attribution telemetry to the cost pipeline.
   - Owner: Dev Productivity guild
   - Horizon: next quarter
   - Why now: attribution rate below 80%

3. Tighten incident-response rotation.
   - Owner: Engineering leadership
   - Horizon: ongoing
   - Why now: incident rate above 3 per week

## Appendix
"""

VAGUE_OWNER_BODY = """## Recommendations

1. Do a cost audit.
   - Owner: Engineering
   - Horizon: this quarter
   - Why now: p90 cycle time exceeds 14 days
"""

BAD_HORIZON_BODY = """## Recommendations

1. Do a cost audit.
   - Owner: Platform team lead
   - Horizon: soon
   - Why now: p90 cycle time exceeds 14 days
"""

VAGUE_WHY_BODY = """## Recommendations

1. Do a cost audit.
   - Owner: Platform team lead
   - Horizon: this quarter
   - Why now: monitor for regression
"""

MISSING_OWNER_BODY = """## Recommendations

1. Do a cost audit.
   - Horizon: this quarter
   - Why now: p90 cycle time exceeds 14 days
"""

ALT_FORMAT_BODY = """## Recommendations

1. Ship the telemetry rewrite. **Owner:** Platform team lead **Horizon:** this quarter **Why now:** p90 cycle time exceeds 14 days.
"""

NAMED_INDIVIDUAL_BODY = """## Recommendations

1. Ship the telemetry rewrite.
   - Owner: Jane Smith
   - Horizon: this quarter
   - Why now: p90 cycle time exceeds 14 days
"""


class ConvictionGateTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir_obj = tempfile.TemporaryDirectory()
        self.tmpdir = self.tmpdir_obj.name

    def tearDown(self):
        self.tmpdir_obj.cleanup()

    def test_pass_three_valid_recommendations(self):
        path = write_proposal(self.tmpdir, PASS_BODY)
        code, report, stdout, stderr = run_gate(path)
        self.assertEqual(code, 0, f"expected exit 0\nstdout={stdout}\nstderr={stderr}")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["rec_count"], 3)
        self.assertEqual(report["failures"], [])

    def test_fail_vague_owner(self):
        path = write_proposal(self.tmpdir, VAGUE_OWNER_BODY)
        code, report, stdout, stderr = run_gate(path)
        self.assertNotEqual(code, 0)
        self.assertEqual(report["status"], "fail")
        owner_fails = [f for f in report["failures"] if f["field"] == "Owner"]
        self.assertTrue(owner_fails, f"expected Owner failure, got {report}")
        self.assertIn("Engineering", owner_fails[0]["reason"])

    def test_fail_bad_horizon(self):
        path = write_proposal(self.tmpdir, BAD_HORIZON_BODY)
        code, report, stdout, stderr = run_gate(path)
        self.assertNotEqual(code, 0)
        horizon_fails = [f for f in report["failures"] if f["field"] == "Horizon"]
        self.assertTrue(horizon_fails)
        self.assertIn("soon", horizon_fails[0]["reason"])
        self.assertIn("enum", horizon_fails[0]["reason"])

    def test_fail_vague_why_now(self):
        path = write_proposal(self.tmpdir, VAGUE_WHY_BODY)
        code, report, stdout, stderr = run_gate(path)
        self.assertNotEqual(code, 0)
        why_fails = [f for f in report["failures"] if f["field"] == "Why-now"]
        self.assertTrue(why_fails)
        self.assertIn("monitor for regression", why_fails[0]["reason"])

    def test_fail_missing_owner(self):
        path = write_proposal(self.tmpdir, MISSING_OWNER_BODY)
        code, report, stdout, stderr = run_gate(path)
        self.assertNotEqual(code, 0)
        owner_fails = [f for f in report["failures"] if f["field"] == "Owner"]
        self.assertTrue(owner_fails)
        self.assertIn("missing", owner_fails[0]["reason"])

    def test_pass_alt_inline_bold_format(self):
        path = write_proposal(self.tmpdir, ALT_FORMAT_BODY)
        code, report, stdout, stderr = run_gate(path)
        self.assertEqual(code, 0, f"expected exit 0\nreport={report}\nstdout={stdout}")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["rec_count"], 1)

    def test_fail_named_individual_owner(self):
        path = write_proposal(self.tmpdir, NAMED_INDIVIDUAL_BODY)
        code, report, stdout, stderr = run_gate(path)
        self.assertNotEqual(code, 0)
        owner_fails = [f for f in report["failures"] if f["field"] == "Owner"]
        self.assertTrue(owner_fails)
        self.assertIn("individual", owner_fails[0]["reason"])


if __name__ == "__main__":
    unittest.main()
