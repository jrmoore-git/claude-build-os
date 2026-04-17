#!/usr/bin/env python3.11
"""
debate_compare.py — `debate.py compare` subcommand.

Extracted from debate.py. Side-by-side scoring of two review outputs
against a common original document. Shared helpers (credentials, config,
fallback dispatch, logging, prompt constant, timezone) pulled lazily.
"""
import json
import os
import re
import sys
from datetime import datetime


def cmd_compare(args):
    """Compare two review methods on the same original document."""
    import debate  # lazy: pulls credentials, config, dispatch helpers, prompt, logger
    import debate_common

    _cost_snapshot = debate.get_session_costs()
    api_key, litellm_url, _is_fallback = debate_common._load_credentials()
    if api_key is None:
        return 1

    original = args.original.read()
    method_a = args.method_a.read()
    method_b = args.method_b.read()

    if not original.strip() or not method_a.strip() or not method_b.strip():
        print("ERROR: all three input files must be non-empty", file=sys.stderr)
        return 1

    # compare uses its own config key (intentionally lighter-weight than the
    # adversarial judge — compare is a side-by-side scoring tool, not the
    # truth arbiter). See tasks/debate-py-bandaid-cleanup-challenge.md A.2.
    config = debate._load_config()
    judge_model = args.model or config.get("compare_default", "gemini-3.1-pro")

    user_content = (
        "## ORIGINAL DOCUMENT\n\n"
        f"{original}\n\n"
        "---\n\n"
        "## METHOD A OUTPUT\n\n"
        f"{method_a}\n\n"
        "---\n\n"
        "## METHOD B OUTPUT\n\n"
        f"{method_b}\n"
    )

    print(f"Calling compare judge ({judge_model})...", file=sys.stderr)
    try:
        compare_fallback = debate_common._get_fallback_model(judge_model, config)
        response, _used = debate._call_with_model_fallback(
            judge_model, compare_fallback, debate.COMPARE_JUDGE_PROMPT, user_content,
            litellm_url, api_key)
    except debate.LLM_SAFE_EXCEPTIONS as e:
        print(f"ERROR: compare call failed — {e}", file=sys.stderr)
        return 2

    # Parse verdict
    verdict_match = re.search(r"## Verdict\s*\n\s*(METHOD_A|METHOD_B|TIE)", response)
    verdict = verdict_match.group(1) if verdict_match else "UNKNOWN"

    # Parse scores
    scores = {}
    for row in re.findall(r"\|\s*(\w[\w\s]*?)\s*\|\s*(\d)\s*\|\s*(\d)\s*\|", response):
        dim = row[0].strip().strip("*")
        if dim.lower() != "total":
            scores[dim] = {"method_a": int(row[1]), "method_b": int(row[2])}

    # Derive debate_id from output filename
    debate_id = os.path.splitext(os.path.basename(args.output))[0]
    if debate_id.endswith("-compare"):
        debate_id = debate_id[:-8]

    # Build output
    now = datetime.now(debate.PROJECT_TZ)
    output_text = (
        "---\n"
        f"debate_id: {debate_id}\n"
        f"created: {now.strftime('%Y-%m-%dT%H:%M:%S%z')[:25]}\n"
        f"phase: compare\n"
        f"judge: {judge_model}\n"
        f"verdict: {verdict}\n"
        "---\n"
        f"# {debate_id} — Method Comparison\n\n"
        f"Judge model: {judge_model}\n\n"
        f"{response}\n"
    )

    with open(args.output, "w") as f:
        f.write(output_text)

    result = {
        "status": "ok",
        "judge": judge_model,
        "verdict": verdict,
        "scores": scores,
    }
    print(json.dumps(result))

    debate._log_debate_event({
        "phase": "compare",
        "debate_id": debate_id,
        "judge": judge_model,
        "verdict": verdict,
        "scores": scores,
        "output": args.output,
    }, cost_snapshot=_cost_snapshot)
    return 0
