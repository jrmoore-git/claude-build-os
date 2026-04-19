"""Locked arm-study verdict thresholds (REDESIGN C).

Loads `config/study/arm_study_thresholds.json` and computes its SHA256.
The verdict aggregator captures the hash in every run artifact so a later
verdict rerun can verify the file hasn't drifted between studies.

Failure mode: if the JSON file is missing or unparseable, the verdict
aggregator falls back to module-level legacy constants (degraded mode)
and surfaces the fallback in the run artifact. This preserves the
verdict pipeline's ability to score in environments where the JSON
isn't shipped (e.g., legacy reruns of pre-REDESIGN-C scored.json).

See tasks/arm-study-redesign-c-bootstrap-thresholds-plan.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_THRESHOLDS_PATH = REPO_ROOT / "config" / "study" / "arm_study_thresholds.json"


# Legacy fallback — mirrors prior verdict.py module-level constants.
# Used when the JSON file is missing or unparseable. The verdict surfaces
# fallback usage explicitly so operators know the lock isn't active.
_LEGACY_THRESHOLDS: dict[str, Any] = {
    "version": "legacy-fallback",
    "bootstrap": {"B": 10000, "seed": 20260419,
                  "ci_directional": 0.95, "ci_confident": 0.99},
    "catch_rate": {
        "floor_directional_pp": 0.05,
        "floor_confident_pp": 0.10,
        "hallucination_regression_pp": 0.02,
    },
    "judge_graded": {
        "floor_directional": 5.0,  # legacy summed-score floor
        "floor_confident": 10.0,
        "harmful_rate_per_proposal_max": 0.20,
    },
    "miss_rate": {"floor_directional_pp": 0.15,
                  "floor_confident_pp": 0.25},
    "plan_quality_delta": {"floor_directional_pp": 0.15,
                           "floor_confident_pp": 0.25},
    "min_sample_for_directional": 3,
    "min_sample_for_confident": 5,
    "quality_weights": {"substantive": 3.0, "marginal": 1.0,
                        "superficial": 0.5, "harmful": -1.0},
}


class ThresholdHashMismatch(RuntimeError):
    """Raised when the threshold file's SHA256 does not match the expected
    value (e.g., file edited between two runs of the same study)."""
    def __init__(self, actual: str, expected: str, path: Path):
        super().__init__(
            f"threshold file {path} sha256={actual} does not match "
            f"expected={expected}; the file was edited mid-study"
        )
        self.actual = actual
        self.expected = expected
        self.path = path


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_thresholds(
    path: Path | None = None,
) -> tuple[dict[str, Any], str]:
    """Read the threshold JSON and return (thresholds, sha256).

    On read/parse failure, returns the legacy fallback thresholds with
    sha256 = "legacy-fallback". Callers can detect degraded mode by
    inspecting `thresholds["version"]` (== "legacy-fallback") or the hash.
    """
    if path is None:
        path = DEFAULT_THRESHOLDS_PATH
    try:
        thresholds = json.loads(path.read_text())
        sha = _hash_file(path)
        return thresholds, sha
    except (OSError, json.JSONDecodeError):
        return dict(_LEGACY_THRESHOLDS), "legacy-fallback"


def verify_hash(
    expected_hash: str, path: Path | None = None,
) -> str:
    """Re-hash the file and raise ThresholdHashMismatch on drift.

    Returns the actual hash on success. The "legacy-fallback" sentinel is
    a no-op (degraded mode bypasses lock; expected to be uncommon in
    production runs).
    """
    if expected_hash == "legacy-fallback":
        return expected_hash
    if path is None:
        path = DEFAULT_THRESHOLDS_PATH
    actual = _hash_file(path)
    if actual != expected_hash:
        raise ThresholdHashMismatch(
            actual=actual, expected=expected_hash, path=path,
        )
    return actual
