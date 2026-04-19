#!/usr/bin/env python3.11
"""
Arm-comparison study: independent miss-rate discoverer (item 5 of the
metric-fix plan).

Reads a proposal + code repo and produces a REFERENCE issue list: the set
of concrete issues a rigorous adversarial review should catch. This
reference set is independent of both arms — the scorer can then diff each
arm's challenge output against it to compute miss_rate per arm.

Design rationale:
- The original miss_rate definition in comparison-prompt.md was degenerate
  (extract only items where the review explicitly acknowledges a gap),
  which returned empty on virtually every proposal. The useful miss_rate
  is "issues that exist but weren't caught," which requires a reference.
- The discoverer uses claude-sonnet-4-6 + repo tools (grep, read_file
  snippet) to ground claims, matching the verifier's posture. Sonnet is not
  in either arm (arms use opus-4-6 or a production mix), so the discoverer
  is not structurally aligned with either.
- Prompt targets exhaustive concrete issues with key_tokens for
  matcher-based coverage. Not inflationary — matcher treats unmatched
  tokens as a miss, so over-producing reference issues would unfairly
  favor neither arm.

Usage:
    python3.11 scripts/arm_study_miss_discoverer.py \\
        --proposal tasks/foo-proposal.md \\
        --output stores/arm-study/<run-id>/miss_reference_issues.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = "claude-sonnet-4-6"


MISS_DISCOVERER_SYSTEM_PROMPT = """\
You are an independent meta-reviewer evaluating a proposal.

Your job is to enumerate every concrete issue a rigorous adversarial review
SHOULD catch in this proposal. These become the reference set for measuring
how well different review processes cover the real issue space. You are NOT
reviewing on behalf of one approach or another — you are producing the
ground truth list.

For each issue, emit:
- id: short unique identifier (issue-1, issue-2, ...)
- category: one of
    {risk, gap, inconsistency, unverified-claim, scope-problem, assumption,
     spec-drift, contradiction}
- description: one-sentence concrete statement of the issue
- key_tokens: 2-5 distinctive lowercase tokens (file paths, function
  names, specific quoted phrases from the proposal) that would appear in
  any review flagging this issue. At least one token must be highly
  specific (a filename, a flag like "--verify-claims", or a function name
  like "compute_verdict"). Generic terms like "security" or "testing" do
  not count as distinctive.
- severity: one of {blocker, material, minor}
- rationale: 1-2 lines on why this matters (what goes wrong if unfixed)

Use the available tools to verify any claim the proposal makes about code
(file paths, function signatures, specific content). If a proposal asserts
X about the codebase, check X, and if X is wrong, add an issue for it.

Be exhaustive but NOT inflationary. Every issue must be concrete and
actionable. Emit no more than 20 issues per proposal. If a proposal is
simple and lacks issues, emit 3-5 and stop. If you emit zero issues, the
proposal is trivially clean — say so explicitly in a final JSON field.

Output format: a single JSON object of shape
  {"issues": [<issue1>, <issue2>, ...], "notes": "<optional>"}
No prose before or after. No code fences.
"""


# ── LLM wiring (imports lazily to keep the script light) ───────────────────


def _run_discoverer(
    proposal_text: str,
    model: str = DEFAULT_MODEL,
    timeout_seconds: int = 900,
) -> tuple[str | None, dict[str, Any] | None]:
    """Invoke the issue-discoverer LLM with tool access.

    Returns (raw_text, stats) where stats is a dict of token/tool usage.
    Returns (None, None) on failure — callers must handle.
    """
    try:
        import debate_common
        import debate_tools
        from llm_client import llm_tool_loop
    except ImportError as e:
        print(f"ERROR: import failed: {e}", file=sys.stderr)
        return None, None

    try:
        api_key, litellm_url, _ = debate_common._load_credentials()
    except Exception as e:
        print(f"ERROR: credential load failed: {e}", file=sys.stderr)
        return None, None

    user_content = (
        "## PROPOSAL UNDER REVIEW\n\n"
        f"{proposal_text}\n\n"
        "---\n\n"
        "Use your tools to verify claims about the codebase and to discover "
        "issues. Emit the JSON object described in the system prompt."
    )

    tool_log: list[dict[str, Any]] = []
    try:
        result = llm_tool_loop(
            system=MISS_DISCOVERER_SYSTEM_PROMPT,
            user=user_content,
            tools=debate_tools.TOOL_DEFINITIONS,
            tool_executor=debate_tools.execute_tool,
            model=model,
            max_turns=20,
            max_tokens=8000,
            timeout=timeout_seconds,
            base_url=litellm_url,
            api_key=api_key,
            on_tool_call=lambda turn, name, targs, res: tool_log.append(
                {"turn": turn, "tool": name}
            ),
        )
    except Exception as e:
        print(f"ERROR: discoverer LLM raised: {e}", file=sys.stderr)
        return None, None

    stats = {
        "model": model,
        "tool_calls": len(tool_log),
    }
    return result.get("content"), stats


# ── Output parsing + sanity check ──────────────────────────────────────────


def parse_discoverer_output(raw: str | None) -> dict[str, Any]:
    """Parse the discoverer's JSON. Returns {"issues": [...], "notes": ...,
    "parse_error": <optional>}."""
    if not raw:
        return {"issues": [], "parse_error": "empty output"}

    # Strip optional code fences.
    s = raw.strip()
    if s.startswith("```json"):
        s = s.split("\n", 1)[-1]
        if s.endswith("```"):
            s = s[:-3]
    elif s.startswith("```"):
        s = s.split("\n", 1)[-1]
        if s.endswith("```"):
            s = s[:-3]
    s = s.strip()

    try:
        obj = json.loads(s)
    except json.JSONDecodeError as e:
        # Try to extract the first balanced { ... } block.
        depth = 0
        start = None
        for i, ch in enumerate(s):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    try:
                        obj = json.loads(s[start:i + 1])
                        break
                    except json.JSONDecodeError:
                        continue
        else:
            return {"issues": [], "parse_error": f"invalid JSON: {e}"}

    if not isinstance(obj, dict):
        return {"issues": [], "parse_error": "top-level not an object"}

    issues = obj.get("issues")
    if not isinstance(issues, list):
        return {"issues": [], "parse_error": "missing or non-list 'issues'"}

    # Normalize each issue — fill in missing fields with defaults.
    clean: list[dict[str, Any]] = []
    for i, issue in enumerate(issues):
        if not isinstance(issue, dict):
            continue
        clean.append({
            "id": str(issue.get("id", f"issue-{i+1}")),
            "category": str(issue.get("category", "uncategorized")),
            "description": str(issue.get("description", "")).strip(),
            "key_tokens": [
                str(t).strip().lower()
                for t in (issue.get("key_tokens") or [])
                if str(t).strip()
            ],
            "severity": str(issue.get("severity", "material")),
            "rationale": str(issue.get("rationale", "")).strip(),
        })

    out: dict[str, Any] = {"issues": clean}
    if obj.get("notes"):
        out["notes"] = str(obj["notes"])
    return out


# ── Matcher (used by the scorer) ───────────────────────────────────────────


TOKEN_MATCH_THRESHOLD = 0.6  # require ≥60% of key_tokens to appear


def match_reference_issues(
    issues: list[dict[str, Any]],
    challenge_text: str,
    threshold: float = TOKEN_MATCH_THRESHOLD,
) -> dict[str, Any]:
    """For each reference issue, check whether the challenger output mentions
    its key tokens. An issue is "caught" when ≥threshold fraction of its
    key_tokens appear in challenge_text (case-insensitive substring).

    V1 strict-AND matching produced 80-100% miss rates on n=3 because
    challenger wording didn't match every token verbatim. Relaxed to a
    majority threshold (0.6) — still token-grounded and deterministic, but
    allows for partial phrasing overlap. Tune via `threshold` arg.
    """
    lower = (challenge_text or "").lower()
    caught: list[dict[str, Any]] = []
    missed: list[dict[str, Any]] = []
    for issue in issues:
        tokens = issue.get("key_tokens") or []
        if not tokens:
            missed.append({**issue, "_match_reason": "no key_tokens"})
            continue
        matches = [t for t in tokens if t in lower]
        match_ratio = len(matches) / len(tokens)
        if match_ratio >= threshold:
            caught.append({
                **issue, "_match_tokens": matches,
                "_match_ratio": round(match_ratio, 3),
            })
        else:
            missed.append({
                **issue, "_match_tokens": matches,
                "_missing_tokens": [t for t in tokens if t not in lower],
                "_match_ratio": round(match_ratio, 3),
            })
    total = len(issues)
    return {
        "total_reference_issues": total,
        "caught_count": len(caught),
        "missed_count": len(missed),
        "miss_rate": (len(missed) / total) if total > 0 else None,
        "token_threshold": threshold,
        "caught": caught,
        "missed": missed,
    }


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--proposal", required=True, type=Path,
                    help="Path to proposal markdown")
    ap.add_argument("--output", type=Path, default=None,
                    help="Path to write reference-issues JSON (default: stdout)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dry-run", action="store_true",
                    help="Emit fixture issues without LLM call")
    args = ap.parse_args()

    if not args.proposal.exists():
        print(f"ERROR: proposal not found: {args.proposal}", file=sys.stderr)
        return 1

    if args.dry_run:
        parsed = {
            "issues": [
                {
                    "id": "issue-1", "category": "gap",
                    "description": "DRY_RUN fixture issue",
                    "key_tokens": ["dry-run"], "severity": "minor",
                    "rationale": "placeholder",
                },
            ],
            "notes": "dry-run fixture",
        }
        stats = {"model": "dry-run", "tool_calls": 0}
    else:
        proposal_text = args.proposal.read_text()
        raw, stats = _run_discoverer(proposal_text, model=args.model)
        if raw is None:
            return 1
        parsed = parse_discoverer_output(raw)
        parsed["raw_output"] = raw

    out = {
        "discoverer_stats": stats or {},
        "proposal_path": str(args.proposal),
        **parsed,
    }

    serialized = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized)
    sys.stdout.write(serialized)

    if parsed.get("parse_error"):
        print(f"WARNING: {parsed['parse_error']}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
