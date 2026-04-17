"""Tests for security posture floor enforcement (D4 audit remediation)."""

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import debate


class TestApplyPostureFloor:
    """Unit tests for _apply_posture_floor."""

    def test_no_clamp_when_posture_already_at_floor(self):
        posture, clamped = debate._apply_posture_floor(3, "some proposal about credentials", "test")
        assert posture == 3
        assert clamped is False

    def test_no_clamp_when_posture_above_floor(self):
        posture, clamped = debate._apply_posture_floor(5, "proposal about API keys", "test")
        assert posture == 5
        assert clamped is False

    def test_no_clamp_when_no_security_content(self):
        posture, clamped = debate._apply_posture_floor(1, "a proposal about UI layout changes", "test")
        assert posture == 1
        assert clamped is False

    def test_clamp_on_credential(self):
        posture, clamped = debate._apply_posture_floor(1, "this handles user credentials", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_clamp_on_api_key(self):
        posture, clamped = debate._apply_posture_floor(2, "stores the API key in .env", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_clamp_on_oauth(self):
        posture, clamped = debate._apply_posture_floor(1, "OAuth token refresh flow", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_clamp_on_password(self):
        posture, clamped = debate._apply_posture_floor(2, "password hashing with bcrypt", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_clamp_on_secret_key(self):
        posture, clamped = debate._apply_posture_floor(1, "rotate the secret key weekly", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_clamp_on_private_key(self):
        posture, clamped = debate._apply_posture_floor(1, "load private_key from disk", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_clamp_on_env_file(self):
        posture, clamped = debate._apply_posture_floor(2, "add DB_URL to .env file", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_clamp_on_auth(self):
        posture, clamped = debate._apply_posture_floor(1, "the auth middleware validates tokens", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_clamp_on_egress(self):
        posture, clamped = debate._apply_posture_floor(1, "network egress policy for containers", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_clamp_on_exfiltration(self):
        posture, clamped = debate._apply_posture_floor(2, "prevent data exfiltration via DNS", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_clamp_on_rm_rf(self):
        posture, clamped = debate._apply_posture_floor(1, "runs rm -rf /tmp/build after deploy", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_clamp_on_drop_table(self):
        posture, clamped = debate._apply_posture_floor(1, "migration runs DROP TABLE users", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_clamp_on_delete_from(self):
        posture, clamped = debate._apply_posture_floor(2, "DELETE FROM audit_log WHERE age > 90", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_clamp_on_destructive(self):
        posture, clamped = debate._apply_posture_floor(1, "this is a destructive migration", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_clamp_on_irreversible(self):
        posture, clamped = debate._apply_posture_floor(2, "irreversible schema change", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_case_insensitive(self):
        posture, clamped = debate._apply_posture_floor(1, "CREDENTIAL rotation schedule", "test")
        assert posture == debate.SECURITY_FLOOR_MIN
        assert clamped is True

    def test_warns_to_stderr(self, capsys):
        debate._apply_posture_floor(1, "stores API key", "proposal")
        captured = capsys.readouterr()
        assert "posture floor applied" in captured.err
        assert "1→3" in captured.err

    def test_label_in_warning(self, capsys):
        debate._apply_posture_floor(2, "auth middleware", "my-input")
        captured = capsys.readouterr()
        assert "my-input" in captured.err


class TestPostureFloorPatterns:
    """Verify that common safe content doesn't trigger the floor."""

    @pytest.mark.parametrize("text", [
        "add a new button to the dashboard",
        "refactor the sorting algorithm",
        "update CSS grid layout",
        "fix pagination bug on page 3",
        "add unit tests for the parser module",
        "rename variable from camelCase to snake_case",
        "improve error messages in the CLI",
        "optimize database query performance",
    ])
    def test_safe_content_not_clamped(self, text):
        posture, clamped = debate._apply_posture_floor(1, text, "test")
        assert posture == 1
        assert clamped is False


class TestPostureFloorConstants:
    """Verify floor configuration is correct."""

    def test_floor_min_is_balanced(self):
        assert debate.SECURITY_FLOOR_MIN == 3

    def test_patterns_nonempty(self):
        assert len(debate.SECURITY_FLOOR_PATTERNS) > 0

    def test_compiled_regex_exists(self):
        assert debate._SECURITY_FLOOR_RE is not None
