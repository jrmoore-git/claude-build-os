#!/usr/bin/env python3.11
"""
debate_verdict.py — `debate.py verdict` subcommand.

Extracted from debate.py. Round 4 of the adversarial pipeline: sends the
resolution back to the original challengers for their final verdict. Shared
helpers (credentials, frontmatter, dispatch, logging, prompt constant) pulled
lazily from the debate module.
"""
import concurrent.futures
import json
import sys


def cmd_verdict(args):
    """Round 4: send resolution back to original challengers for final verdict."""
    import debate  # lazy: pulls config, dispatch helpers, prompt, logger
    import debate_common

    _cost_snapshot = debate_common.get_session_costs()
    api_key, litellm_url, _is_fallback = debate_common._load_credentials()
    if api_key is None:
        return 1

    challenge_text = args.challenge.read()
    meta, challenge_body = debate._parse_frontmatter(challenge_text)
    if not meta:
        print("ERROR: challenge file has no frontmatter", file=sys.stderr)
        return 1

    debate._auto_generate_mapping(meta, challenge_body)

    resolution = args.resolution.read()
    if not resolution.strip():
        print("ERROR: resolution file is empty", file=sys.stderr)
        return 1

    system_prompt = debate.VERDICT_SYSTEM_PROMPT
    if args.system_prompt:
        system_prompt = args.system_prompt.read()

    # Latent fix: original cmd_verdict referenced `config` without loading it.
    # Every other cmd_* function calls _load_config() at its top; parity fix.
    config = debate._load_config()

    mapping = meta["mapping"]
    debate_id = meta.get("debate_id", "unknown")
    results = {}
    all_warnings = []

    def _run_verdict(label, model):
        print(f"Calling {label} for verdict...", file=sys.stderr)
        try:
            fallback = debate_common._get_fallback_model(model, config)
            response, _used = debate._call_with_model_fallback(
                model, fallback, system_prompt, resolution, litellm_url, api_key)
            return label, response, None
        except debate.LLM_SAFE_EXCEPTIONS as e:
            msg = f"Challenger {label} ({model}): {e}"
            print(f"WARNING: {msg}", file=sys.stderr)
            return label, f"[ERROR: {msg}]", msg

    # Run verdicts in parallel — each hits an independent model API.
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(mapping)) as pool:
        futures = {
            pool.submit(_run_verdict, label, model): label
            for label, model in mapping.items()
        }
        for fut in concurrent.futures.as_completed(futures):
            label, response, warning = fut.result()
            results[label] = response
            if warning:
                all_warnings.append(warning)

    successful = sum(1 for v in results.values() if not v.startswith("[ERROR:"))
    if successful == 0:
        print("ERROR: all verdict calls failed", file=sys.stderr)
        return 2

    # Build output — reuse same frontmatter format
    fm_extras = {"execution_mode": "fallback_single_model"} if _is_fallback else None
    frontmatter = debate._build_frontmatter(debate_id, mapping, extras=fm_extras)
    sections = [frontmatter, f"# {debate_id} — Final Verdicts", ""]
    for label in sorted(results.keys()):
        sections.append(f"## Challenger {label} — Verdict")
        sections.append(results[label])
        sections.append("\n---\n")

    output_text = "\n".join(sections).rstrip() + "\n"

    with open(args.output, "w") as f:
        f.write(output_text)

    result = {
        "status": "ok" if not all_warnings else "partial",
        "verdicts": successful,
        "mapping": mapping,
    }
    if all_warnings:
        result["warnings"] = all_warnings
    print(json.dumps(result))

    debate._log_debate_event({
        "phase": "verdict",
        "debate_id": debate_id,
        "mapping": mapping,
        "verdicts": successful,
        "warnings": all_warnings,
        "output": args.output,
    }, cost_snapshot=_cost_snapshot)
    return 0
