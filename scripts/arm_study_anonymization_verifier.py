#!/usr/bin/env python3.11
"""Arm-comparison study syntactic anonymization verifier.

Scope: Track C of tasks/arm-comparison-methodology-validation-plan.md.

Flags syntactic leakage in judge prompts / arm outputs:
  - arm identifiers (arm-a, arm-b, arm_a, "Arm A", etc.)
  - model names + family terms (claude, opus, sonnet, gpt-5, gemini, anthropic, openai, google)
  - cost/token data (dollar amounts, tokens, usd, spend — when co-located with a number)
  - run-order metadata (first arm, second arm, run 1, arm 1, prior arm, ...)

Semantic/stylistic leakage is explicitly OUT OF SCOPE. That is handled by
session-isolation (separate subprocesses per arm) plus a human eyeball pass.
Do not extend this script to chase stylistic fingerprints — that failure
mode was the subject of the premortem and is the reason the study uses
process boundaries instead of regex-based style detection.

Usage:
  python3.11 scripts/arm_study_anonymization_verifier.py --input <file_or_dir>
  python3.11 scripts/arm_study_anonymization_verifier.py --sample-mode

Exit codes:
  0 — clean (file mode) or both fixtures behaved correctly (sample mode)
  1 — leakage found (file mode) or verifier misbehaved on fixtures (sample mode)
  2 — usage error

Importable: `from arm_study_anonymization_verifier import check_text`
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Regex patterns, grouped by category.
# ---------------------------------------------------------------------------

# Arm identifiers. Case-insensitive. Word-boundary on the letter so "arm-arc"
# (arbitrary word starting with arm-) doesn't false-match.
# Note: arm-x / arm-y are the neutral filename tokens used on disk — those are
# fine inside a path like "stores/arm-study/<run>/arm-x/". But if they appear
# as free-standing tokens in a judge prompt narration (e.g. "the arm-x review
# said..."), that's still a run-ordering hint. Flag arm-x/arm-y too; callers
# that legitimately reference the on-disk directory name in a file path can
# strip the path before verifying.
_ARM_ID_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # arm-a / arm-b / arm_a / arm_b / arm a / arm b — as whole tokens.
    ("arm_identifier", re.compile(r"\b[Aa]rm[\s_\-][AaBbXxYy]\b")),
    # ArmA / ArmB (no separator) — seen when labels are camel-cased.
    ("arm_identifier", re.compile(r"\bArm[ABXY]\b")),
]

# Model names + family terms. Case-insensitive. Specific versioned names come
# first (more informative), then family terms.
_MODEL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Specific versioned names: claude-opus-4-6, claude-opus-4-7,
    # claude-sonnet-4-6, gpt-5.4, gpt-5, gemini-3.1-pro, gemini-3
    ("model_name", re.compile(r"\bclaude[\s\-]?(?:opus|sonnet|haiku)[\s\-]?\d+[\-.]?\d*\b", re.IGNORECASE)),
    ("model_name", re.compile(r"\bgpt[\s\-]?\d+(?:\.\d+)?\b", re.IGNORECASE)),
    ("model_name", re.compile(r"\bgemini[\s\-]?\d+(?:\.\d+)?(?:[\s\-]?pro)?\b", re.IGNORECASE)),
    # Family / vendor terms.
    ("model_name", re.compile(r"\bclaude\b", re.IGNORECASE)),
    ("model_name", re.compile(r"\bopus\b", re.IGNORECASE)),
    ("model_name", re.compile(r"\bsonnet\b", re.IGNORECASE)),
    ("model_name", re.compile(r"\bhaiku\b", re.IGNORECASE)),
    ("model_name", re.compile(r"\bgemini\b", re.IGNORECASE)),
    ("model_name", re.compile(r"\banthropic\b", re.IGNORECASE)),
    ("model_name", re.compile(r"\bopenai\b", re.IGNORECASE)),
    ("model_name", re.compile(r"\bgoogle\b", re.IGNORECASE)),
]

# Cost / token data. A hit requires either:
#   - a dollar amount ($1.23, $250), OR
#   - a number within 20 chars of a cost/token keyword, OR
#   - the keyword "usd" / "api cost" / etc. appearing at all (strong signal).
# The "within 20 chars" window is enforced by embedding the number in the
# regex directly rather than doing a second pass.
_COST_KEYWORDS = [
    "cost", "tokens", "token count", "input cost", "output cost",
    "total cost", "api cost", "usd", "spend", "expense",
]
_COST_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Dollar amount anywhere.
    ("cost_data", re.compile(r"\$\s*\d[\d,]*(?:\.\d+)?")),
    # "N tokens" — number immediately followed by "tokens".
    ("cost_data", re.compile(r"\b\d[\d,]*\s*tokens?\b", re.IGNORECASE)),
    # Keyword followed by up to 20 chars and then a number.
    ("cost_data", re.compile(
        r"\b(?:cost|tokens?|token count|input cost|output cost|total cost|api cost|spend|expense)\b.{0,20}?\d",
        re.IGNORECASE,
    )),
    # Number then up to 20 chars then keyword.
    ("cost_data", re.compile(
        r"\d.{0,20}?\b(?:cost|tokens?|token count|input cost|output cost|total cost|api cost|spend|expense)\b",
        re.IGNORECASE,
    )),
    # USD as a unit — by itself usually means currency is being discussed.
    ("cost_data", re.compile(r"\bUSD\b")),
]

# Run-order metadata. Case-insensitive.
_RUN_ORDER_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("run_order", re.compile(r"\bfirst arm\b", re.IGNORECASE)),
    ("run_order", re.compile(r"\bsecond arm\b", re.IGNORECASE)),
    ("run_order", re.compile(r"\barm\s+[12]\b", re.IGNORECASE)),
    ("run_order", re.compile(r"\brun\s+[12]\b", re.IGNORECASE)),
    ("run_order", re.compile(r"\bfirst run\b", re.IGNORECASE)),
    ("run_order", re.compile(r"\bsecond run\b", re.IGNORECASE)),
    ("run_order", re.compile(r"\binitial arm\b", re.IGNORECASE)),
    ("run_order", re.compile(r"\bfollow[\s\-]?up arm\b", re.IGNORECASE)),
    ("run_order", re.compile(r"\bprior arm\b", re.IGNORECASE)),
    ("run_order", re.compile(r"\bsubsequent arm\b", re.IGNORECASE)),
]

_ALL_PATTERNS: list[tuple[str, re.Pattern[str]]] = (
    _ARM_ID_PATTERNS + _MODEL_PATTERNS + _COST_PATTERNS + _RUN_ORDER_PATTERNS
)

_CATEGORIES = ("arm_identifier", "model_name", "cost_data", "run_order")


# ---------------------------------------------------------------------------
# Core checker.
# ---------------------------------------------------------------------------

def check_text(text: str, file_label: str = "<text>") -> list[dict]:
    """Return a list of findings for the given text.

    Each finding: {"category", "line", "match", "file"}.
    """
    findings: list[dict] = []
    # Precompute line offsets so we can map character offsets to line numbers.
    line_starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            line_starts.append(i + 1)

    def line_of(offset: int) -> int:
        # Binary search — but text files are small; linear is fine and clearer.
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= offset:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1  # 1-indexed

    for category, pattern in _ALL_PATTERNS:
        for m in pattern.finditer(text):
            findings.append({
                "category": category,
                "line": line_of(m.start()),
                "match": m.group(0),
                "file": file_label,
            })
    return findings


def check_file(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeError) as e:
        # Read failures surface as a synthetic finding so the caller knows
        # the file couldn't be verified. Treat as leakage to fail closed.
        return [{
            "category": "read_error",
            "line": 0,
            "match": f"could not read: {e}",
            "file": str(path),
        }]
    return check_text(text, file_label=str(path))


def iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for p in sorted(root.rglob("*")):
        if p.is_file():
            yield p


# ---------------------------------------------------------------------------
# Fixtures for --sample-mode.
# ---------------------------------------------------------------------------

CLEAN_SAMPLE = """Judge prompt excerpt (clean).

You will read two review outputs labelled X and Y. For each dimension
(D1 through D7), extract the items the review raised. For each item,
classify it as substantive / marginal / superficial / harmful with a
one-line rationale. Do not guess which review is which — the labels
carry no information.

Output JSON with per-dimension blocks.
"""

LEAKED_SAMPLE = """Judge prompt excerpt (leaked — for verifier self-test).

You will read two review outputs. The first arm is arm-a (claude-opus-4-6
in every slot) and the second arm is Arm B (the production OpenAI / Google
mix with gpt-5.4 and gemini-3.1-pro). Arm A cost approximately $42 and
consumed 180000 tokens; run 1 ran before run 2.

For each dimension, extract the items. The Anthropic-only arm should be
easy to spot by its prose. Total API cost across both arms was $95 USD.
"""


def run_sample_mode() -> int:
    """Run the verifier on the embedded fixtures.

    Returns 0 if the clean fixture is clean AND the leaked fixture flags all
    four categories. Returns 1 otherwise.
    """
    clean_findings = check_text(CLEAN_SAMPLE, file_label="<CLEAN_SAMPLE>")
    leaked_findings = check_text(LEAKED_SAMPLE, file_label="<LEAKED_SAMPLE>")

    clean_ok = len(clean_findings) == 0
    leaked_categories = {f["category"] for f in leaked_findings}
    required_categories = set(_CATEGORIES)
    leaked_ok = required_categories.issubset(leaked_categories)

    report = {
        "mode": "sample",
        "clean": {
            "expected": "clean",
            "findings": clean_findings,
            "pass": clean_ok,
        },
        "leaked": {
            "expected": "leaked",
            "findings_count": len(leaked_findings),
            "categories_found": sorted(leaked_categories),
            "categories_required": sorted(required_categories),
            "pass": leaked_ok,
        },
        "overall_pass": clean_ok and leaked_ok,
    }
    print(json.dumps(report, indent=2))

    if clean_ok and leaked_ok:
        print("sample-mode: PASS", file=sys.stderr)
        return 0
    print("sample-mode: FAIL", file=sys.stderr)
    if not clean_ok:
        print(f"  clean fixture produced {len(clean_findings)} findings (expected 0)", file=sys.stderr)
    if not leaked_ok:
        missing = required_categories - leaked_categories
        print(f"  leaked fixture missing categories: {sorted(missing)}", file=sys.stderr)
    return 1


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Syntactic anonymization verifier for arm-comparison study.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="File or directory to verify. Directories are walked recursively.",
    )
    parser.add_argument(
        "--sample-mode",
        action="store_true",
        help="Run against embedded fixtures (clean + leaked) and self-test.",
    )
    args = parser.parse_args(argv)

    if args.sample_mode:
        return run_sample_mode()

    if args.input is None:
        parser.print_usage(sys.stderr)
        print("error: --input is required when --sample-mode is not set", file=sys.stderr)
        return 2

    if not args.input.exists():
        print(f"error: {args.input} does not exist", file=sys.stderr)
        return 2

    all_findings: list[dict] = []
    files_checked = 0
    leaked_files: set[str] = set()

    for path in iter_files(args.input):
        files_checked += 1
        findings = check_file(path)
        if findings:
            leaked_files.add(str(path))
            all_findings.extend(findings)

    status = "clean" if not all_findings else "leaked"
    report = {
        "status": status,
        "findings": all_findings,
        "files_checked": files_checked,
        "files_leaked": len(leaked_files),
    }
    print(json.dumps(report, indent=2))
    print(
        f"verifier: {status} — {files_checked} file(s) checked, "
        f"{len(leaked_files)} leaked, {len(all_findings)} finding(s)",
        file=sys.stderr,
    )

    return 0 if status == "clean" else 1


if __name__ == "__main__":
    sys.exit(main())
