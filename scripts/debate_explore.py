#!/usr/bin/env python3.11
"""
debate_explore.py — `debate.py explore` subcommand.

Extracted from debate.py. Thinking-mode single-model divergent exploration:
generates N distinct directions with model rotation across rounds, then a
synthesis pass maps the solution space. Shared helpers (credentials, config,
prompt loader, direction parser, dispatch, logging, prompt constants,
timezone, defaults) pulled lazily from the debate module.
"""
import json
import sys
from datetime import datetime


def cmd_explore(args):
    """Divergent exploration: single model generates N distinct directions,
    then a synthesis pass maps the solution space."""
    import debate  # lazy: pulls credentials, config, dispatch, prompts, logger
    import debate_common

    _cost_snapshot = debate.get_session_costs()
    api_key, litellm_url, _is_fallback = debate_common._load_credentials()
    if api_key is None:
        return 1
    config = debate._load_config()

    # Rotate models across directions for genuine divergence (like refine).
    # --model locks all rounds to a single model (override).
    if args.model:
        explore_models = [args.model]
    else:
        explore_models = config.get("explore_rotation",
                                    config.get("refine_rotation",
                                               ["gpt-5.4", "gemini-3.1-pro", "gpt-5.4"]))
    directions_count = args.directions
    question = args.question
    context = getattr(args, 'context', None) or ""

    # Parse structured dimensions from context if present
    dimensions_block = ""
    narrative_context = context
    if "DIMENSIONS:" in context:
        parts = context.split("DIMENSIONS:", 1)
        dim_section = parts[1]
        # Split dimensions from the rest of the context
        if "PRE-FLIGHT CONTEXT:" in dim_section:
            dim_text, narrative_context = dim_section.split("PRE-FLIGHT CONTEXT:", 1)
            narrative_context = narrative_context.strip()
        elif "CONTEXT:" in dim_section:
            dim_text, narrative_context = dim_section.split("CONTEXT:", 1)
            narrative_context = narrative_context.strip()
        else:
            dim_text = dim_section
            narrative_context = ""
        dim_lines = [l.strip() for l in dim_text.strip().splitlines() if l.strip()]
        if dim_lines:
            dimensions_block = (
                "To ensure real divergence, at least 3 of these dimensions "
                "must differ from ALL previous directions:\n\n"
                + "\n".join(f"- **{l}**" if not l.startswith("-") else l
                            for l in dim_lines)
            )

    # Fall back to generic dimensions if none derived from pre-flight
    if not dimensions_block:
        dimensions_block = (
            "To ensure real divergence, your direction should differ from "
            "previous directions on at least 2 of these dimensions:\n\n"
            "- **Approach** — the fundamental mechanism or method\n"
            "- **Scope** — what's included vs excluded\n"
            "- **Tradeoff** — what you optimize for vs sacrifice\n"
            "- **Who it affects** — the primary audience or stakeholder\n"
            "- **Success criteria** — how you'd know it worked"
        )

    context_block = (f"\n## Context (use this to inform your thinking)\n\n"
                     f"{narrative_context}\n") if narrative_context else ""

    if not question.strip():
        print("ERROR: question is empty", file=sys.stderr)
        return 1

    # Load prompts from files (fall back to hardcoded constants)
    explore_prompt, explore_ver = debate._load_prompt("explore.md", debate.EXPLORE_SYSTEM_PROMPT)
    diverge_prompt_tpl, diverge_ver = debate._load_prompt("explore-diverge.md", debate.EXPLORE_DIVERGE_PROMPT)
    synth_prompt_tpl, synth_ver = debate._load_prompt("explore-synthesis.md", debate.EXPLORE_SYNTHESIS_PROMPT)

    # Inject context and dimensions into prompts
    explore_prompt = explore_prompt.replace("{context}", context_block)
    explore_prompt = explore_prompt.replace("{dimensions}", dimensions_block)
    user_content = question if not narrative_context else f"{question}\n{context_block}"

    directions = []
    direction_names = []

    # Round 1: first direction (no divergence constraint)
    model = explore_models[0 % len(explore_models)]
    explore_fallback = debate_common._get_fallback_model(model, config)
    print(f"Explore round 1/{directions_count} ({model})...", file=sys.stderr)
    try:
        resp, _used = debate._call_with_model_fallback(
            model, explore_fallback, explore_prompt, user_content,
            litellm_url, api_key,
            temperature=debate.LLM_CALL_DEFAULTS["explore_temperature"])
    except debate.LLM_SAFE_EXCEPTIONS as e:
        print(f"ERROR: explore round 1 failed — {e}", file=sys.stderr)
        return 1
    directions.append(resp)
    direction_names.append(debate._parse_explore_direction(resp))

    # Rounds 2..N: forced divergence, rotating models
    for i in range(2, directions_count + 1):
        model = explore_models[(i - 1) % len(explore_models)]
        explore_fallback = debate_common._get_fallback_model(model, config)
        prev_summary = "\n".join(
            f"{j}. {name}" for j, name in enumerate(direction_names, 1)
        )
        diverge_prompt = diverge_prompt_tpl.format(
            previous_directions=prev_summary,
            context=context_block,
            dimensions=dimensions_block,
            direction_number=i,
            total_directions=directions_count,
        )
        print(f"Explore round {i}/{directions_count} ({model})...",
              file=sys.stderr)
        try:
            resp, _used = debate._call_with_model_fallback(
                model, explore_fallback, diverge_prompt, user_content,
                litellm_url, api_key,
                temperature=debate.LLM_CALL_DEFAULTS["explore_temperature"])
        except debate.LLM_SAFE_EXCEPTIONS as e:
            print(f"WARNING: explore round {i} failed — {e}",
                  file=sys.stderr)
            continue
        directions.append(resp)
        direction_names.append(debate._parse_explore_direction(resp))

    if len(directions) < 2:
        print("ERROR: fewer than 2 directions generated", file=sys.stderr)
        return 1

    # Synthesis pass
    synth_model = args.synth_model or model
    combined = "\n\n---\n\n".join(
        f"### Direction {i}\n\n{d}" for i, d in enumerate(directions, 1)
    )
    synth_prompt = synth_prompt_tpl.format(n=len(directions), dimensions=dimensions_block)
    print(f"Synthesizing ({synth_model})...", file=sys.stderr)
    try:
        synth_fallback = debate_common._get_fallback_model(synth_model, config)
        synthesis, _used = debate._call_with_model_fallback(
            synth_model, synth_fallback, synth_prompt, combined,
            litellm_url, api_key)
    except debate.LLM_SAFE_EXCEPTIONS as e:
        print(f"WARNING: synthesis failed — {e}", file=sys.stderr)
        synthesis = ""

    # Build output
    now = datetime.now(debate.PROJECT_TZ)
    ver_str = f"prompt_versions: explore={explore_ver}, diverge={diverge_ver}, synthesis={synth_ver}"
    output_lines = [
        "---",
        f"mode: explore",
        f"created: {now.strftime('%Y-%m-%dT%H:%M:%S%z')[:25]}",
        f"models: {','.join(explore_models)}",
        f"directions: {len(directions)}",
        ver_str,
        "---",
        f"# Explore: {question[:80]}",
        "",
    ]
    for i, d in enumerate(directions, 1):
        output_lines.append(f"## Direction {i}")
        output_lines.append("")
        output_lines.append(d)
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")

    if synthesis:
        output_lines.append("## Synthesis")
        output_lines.append("")
        output_lines.append(synthesis)

    output_text = "\n".join(output_lines)
    with open(args.output, "w") as f:
        f.write(output_text)

    print(json.dumps({"status": "ok", "output": args.output, "directions": len(directions)}))

    debate._log_debate_event({
        "phase": "explore",
        "models": explore_models,
        "directions": len(directions),
        "direction_names": direction_names,
        "question": question[:200],
        "success": True,
    }, cost_snapshot=_cost_snapshot)

    result = {
        "status": "ok",
        "directions": len(directions),
        "direction_names": direction_names,
        "model": model,
    }
    print(json.dumps(result), file=sys.stderr)
    return 0
