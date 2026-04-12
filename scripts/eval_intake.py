#!/usr/bin/env python3
"""
eval_intake.py — Cross-model intake evaluation harness.

Claude runs the intake (interviewer). Gemini plays the persona.
GPT judges the transcript against a rubric.

Usage:
    python3.11 scripts/eval_intake.py \
        --protocol tasks/explore-intake-refined.md \
        --persona config/eval-personas/reframe-acceptance.md \
        --interviewer-model claude-opus-4-6 \
        --persona-model gemini-3.1-pro \
        --judge-model gpt-5.4 \
        --output tasks/eval-intake-reframe-acceptance.md \
        --max-turns 8

    # Run all 5 personas:
    python3.11 scripts/eval_intake.py --run-all \
        --protocol tasks/explore-intake-refined.md \
        --output-dir tasks/eval-results/

Architecture:
    1. Turn loop: interviewer (Claude) ↔ persona (Gemini) via llm_call
    2. Interviewer composes context block after sufficiency
    3. Judge (GPT) scores transcript + block against rubric
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add scripts/ to path for llm_client import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm_client import llm_call, llm_call_json, LLMError


PERSONA_DIR = Path(__file__).resolve().parent.parent / "config" / "eval-personas"
RUBRIC_PATH = Path(__file__).resolve().parent.parent / "config" / "eval-rubric.md"


def load_file(path):
    return Path(path).read_text().strip()


def build_interviewer_system(protocol_text):
    """System prompt for the interviewer (Claude)."""
    return f"""You are running an explore intake conversation. Follow the protocol below EXACTLY.

Your job: ask questions until the problem is clear enough for explore to produce directions people act on. Then compose a context block.

RULES:
- One question per message. No batching.
- Q1 IS the opening move. No preamble, no "great question", no acknowledgment.
- Thread-and-steer from the user's last answer.
- When you've reached sufficiency (you know the decision, what makes it hard, and 2+ concrete facts), say EXACTLY: "SUFFICIENCY_REACHED" on its own line, then compose the context block using the template from the protocol.
- Do NOT solve during intake.
- Mirror the user's register.

PROTOCOL:
{protocol_text}

IMPORTANT: When sufficiency is reached, you MUST output "SUFFICIENCY_REACHED" on a line by itself, followed by the context block. This signals the end of intake."""


def build_persona_system(persona_text):
    """System prompt for the persona (Gemini)."""
    return f"""You are playing a character in a simulation. Stay in character for the ENTIRE conversation.

{persona_text}

RULES:
- Answer as this character would. Use their writing style, vocabulary, and emotional temperature.
- Reveal information naturally -- don't dump everything at once.
- Follow the "Behavior" section precisely. If it says to reject something, reject it. If it says to give short answers, give short answers.
- Do NOT break character. Do NOT mention that you're in a simulation.
- Do NOT be artificially helpful. Real people hedge, deflect, get impatient, and don't always give the answer the interviewer wants.
- Your answers should be 1-4 sentences unless the Behavior section says otherwise (e.g., thin answers = 5-15 words)."""


def build_judge_system(rubric_text):
    """System prompt for the judge (GPT)."""
    return f"""You are an independent judge evaluating an AI intake conversation.

{rubric_text}

Be rigorous. Quote specific turns. Don't be generous -- score exactly what you see."""


def run_conversation(protocol_text, persona_text, opening_input,
                     interviewer_model, persona_model, max_turns=8):
    """Run the multi-turn intake conversation."""
    interviewer_sys = build_interviewer_system(protocol_text)
    persona_sys = build_persona_system(persona_text)

    transcript = []
    interviewer_history = []  # messages for interviewer context
    persona_history = []      # messages for persona context

    # Turn 0: persona's opening input
    transcript.append(("PERSONA", opening_input))
    interviewer_history.append(f"USER: {opening_input}")

    context_block = None

    for turn in range(1, max_turns + 1):
        # Interviewer responds to persona's last message
        interviewer_user = "\n\n".join(interviewer_history)
        try:
            interviewer_response = llm_call(
                interviewer_sys, interviewer_user,
                model=interviewer_model, temperature=0.3, timeout=120
            )
        except LLMError as e:
            print(f"ERROR: Interviewer call failed: {e}", file=sys.stderr)
            transcript.append(("SYSTEM", f"Interviewer error: {e}"))
            break

        # Check for sufficiency signal
        if "SUFFICIENCY_REACHED" in interviewer_response:
            parts = interviewer_response.split("SUFFICIENCY_REACHED", 1)
            question_part = parts[0].strip()
            context_part = parts[1].strip() if len(parts) > 1 else ""

            if question_part:
                transcript.append(("INTERVIEWER", question_part))
            transcript.append(("INTERVIEWER", "[SUFFICIENCY REACHED]"))
            context_block = context_part
            break

        transcript.append(("INTERVIEWER", interviewer_response))
        persona_history.append(f"INTERVIEWER: {interviewer_response}")

        # Persona responds to interviewer's question
        persona_user = "\n\n".join(persona_history)
        try:
            persona_response = llm_call(
                persona_sys, persona_user,
                model=persona_model, temperature=0.4, timeout=120
            )
        except LLMError as e:
            print(f"ERROR: Persona call failed: {e}", file=sys.stderr)
            transcript.append(("SYSTEM", f"Persona error: {e}"))
            break

        transcript.append(("PERSONA", persona_response))
        interviewer_history.append(f"ASSISTANT: {interviewer_response}")
        interviewer_history.append(f"USER: {persona_response}")
        persona_history.append(f"ASSISTANT: {persona_response}")

        print(f"  Turn {turn} complete", file=sys.stderr)

    return transcript, context_block


def run_judge(transcript, context_block, persona_text, rubric_text, judge_model):
    """Judge the transcript against the rubric."""
    transcript_text = "\n\n".join(
        f"**{role}:** {text}" for role, text in transcript
    )

    judge_input = f"""## Transcript

{transcript_text}

## Context Block (composed by interviewer)

{context_block or "[No context block composed -- interviewer did not reach sufficiency]"}

## Persona File

{persona_text}"""

    judge_sys = build_judge_system(rubric_text)

    try:
        result = llm_call(
            judge_sys, judge_input,
            model=judge_model, temperature=0.0, timeout=180
        )
        # Try to parse JSON from the response
        try:
            # Find JSON block in response
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(result[json_start:json_end])
                return parsed, result
        except json.JSONDecodeError:
            pass
        return None, result
    except LLMError as e:
        return None, f"Judge error: {e}"


def extract_opening_input(persona_text):
    """Extract the opening input from a persona file."""
    in_opening = False
    for line in persona_text.split("\n"):
        if line.strip().startswith("## Opening Input"):
            in_opening = True
            continue
        if in_opening:
            line = line.strip()
            if line.startswith("##"):
                break
            if line and not line.startswith("#"):
                return line.strip('"').strip("'")
    return None


def format_output(persona_name, transcript, context_block, judge_parsed, judge_raw):
    """Format the evaluation output as markdown."""
    lines = []
    lines.append(f"# Intake Eval: {persona_name}")
    lines.append(f"Date: {time.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # Transcript
    lines.append("## Transcript")
    lines.append("")
    for role, text in transcript:
        lines.append(f"**{role}:** {text}")
        lines.append("")

    # Context block
    lines.append("## Context Block")
    lines.append("")
    if context_block:
        lines.append(context_block)
    else:
        lines.append("*No context block composed*")
    lines.append("")

    # Judge evaluation
    lines.append("## Judge Evaluation")
    lines.append("")
    if judge_parsed:
        scores = judge_parsed.get("scores", {})
        lines.append("| Dimension | Score | Evidence |")
        lines.append("|-----------|-------|----------|")
        for dim, data in scores.items():
            if isinstance(data, dict):
                score = data.get("score", "?")
                evidence = data.get("evidence", "").replace("|", "\\|")[:100]
                lines.append(f"| {dim} | {score}/5 | {evidence} |")
            else:
                lines.append(f"| {dim} | {data}/5 | |")
        lines.append("")
        avg = judge_parsed.get("average", "?")
        passed = judge_parsed.get("pass", "?")
        lines.append(f"**Average: {avg}/5.0 | Pass: {passed}**")
        lines.append("")
        hidden = judge_parsed.get("hidden_truth_surfaced", "?")
        lines.append(f"**Hidden truth surfaced: {hidden}**")
        lines.append("")
        summary = judge_parsed.get("summary", "")
        if summary:
            lines.append(f"**Summary:** {summary}")
    else:
        lines.append("*Could not parse structured judge output. Raw response:*")
        lines.append("")
        lines.append(judge_raw)

    return "\n".join(lines)


def run_single_eval(persona_path, protocol_text, rubric_text,
                    interviewer_model, persona_model, judge_model,
                    max_turns, output_path):
    """Run a single persona evaluation end-to-end."""
    persona_name = Path(persona_path).stem
    persona_text = load_file(persona_path)
    opening_input = extract_opening_input(persona_text)

    if not opening_input:
        print(f"ERROR: No opening input found in {persona_path}", file=sys.stderr)
        return None

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Running eval: {persona_name}", file=sys.stderr)
    print(f"  Interviewer: {interviewer_model}", file=sys.stderr)
    print(f"  Persona: {persona_model}", file=sys.stderr)
    print(f"  Judge: {judge_model}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

    # Run conversation
    print("Phase 1: Conversation...", file=sys.stderr)
    transcript, context_block = run_conversation(
        protocol_text, persona_text, opening_input,
        interviewer_model, persona_model, max_turns
    )

    # Run judge
    print("Phase 2: Judging...", file=sys.stderr)
    judge_parsed, judge_raw = run_judge(
        transcript, context_block, persona_text, rubric_text, judge_model
    )

    # Format and write output
    output = format_output(persona_name, transcript, context_block,
                          judge_parsed, judge_raw)
    Path(output_path).write_text(output)
    print(f"Output written to {output_path}", file=sys.stderr)

    return {
        "persona": persona_name,
        "turns": len([t for t in transcript if t[0] == "INTERVIEWER"]),
        "sufficiency_reached": context_block is not None,
        "judge_parsed": judge_parsed,
        "output_path": str(output_path),
    }


def run_all(args):
    """Run all personas in parallel."""
    protocol_text = load_file(args.protocol)
    rubric_text = load_file(RUBRIC_PATH)

    persona_files = sorted(PERSONA_DIR.glob("*.md"))
    if not persona_files:
        print(f"ERROR: No persona files found in {PERSONA_DIR}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    with ThreadPoolExecutor(max_workers=min(len(persona_files), 3)) as pool:
        futures = {}
        for pf in persona_files:
            output_path = output_dir / f"eval-{pf.stem}.md"
            fut = pool.submit(
                run_single_eval, pf, protocol_text, rubric_text,
                args.interviewer_model, args.persona_model, args.judge_model,
                args.max_turns, output_path
            )
            futures[fut] = pf.stem

        for fut in as_completed(futures):
            name = futures[fut]
            try:
                result = fut.result()
                if result:
                    results.append(result)
                    j = result.get("judge_parsed")
                    avg = j.get("average", "?") if j else "?"
                    passed = j.get("pass", "?") if j else "?"
                    print(f"  {name}: avg={avg}, pass={passed}", file=sys.stderr)
            except Exception as e:
                print(f"  {name}: FAILED — {e}", file=sys.stderr)

    # Write summary
    summary_path = output_dir / "eval-summary.md"
    lines = ["# Intake Eval Summary", f"Date: {time.strftime('%Y-%m-%d %H:%M')}", ""]
    lines.append("| Persona | Turns | Sufficiency | Average | Pass | Hidden Truth |")
    lines.append("|---------|-------|-------------|---------|------|-------------|")
    for r in sorted(results, key=lambda x: x["persona"]):
        j = r.get("judge_parsed") or {}
        lines.append(
            f"| {r['persona']} | {r['turns']} | "
            f"{'Yes' if r['sufficiency_reached'] else 'No'} | "
            f"{j.get('average', '?')} | "
            f"{'PASS' if j.get('pass') else 'FAIL'} | "
            f"{'Yes' if j.get('hidden_truth_surfaced') else 'No'} |"
        )
    lines.append("")

    all_pass = all(r.get("judge_parsed", {}).get("pass", False) for r in results)
    lines.append(f"**Overall: {'ALL PASS' if all_pass else 'FAILURES DETECTED'}**")

    summary_path.write_text("\n".join(lines))
    print(f"\nSummary written to {summary_path}", file=sys.stderr)

    return 0 if all_pass else 1


def main():
    parser = argparse.ArgumentParser(description="Cross-model intake evaluation")
    parser.add_argument("--protocol", required=True, help="Path to protocol file")
    parser.add_argument("--interviewer-model", default="claude-opus-4-6")
    parser.add_argument("--persona-model", default="gemini-3.1-pro")
    parser.add_argument("--judge-model", default="gpt-5.4")
    parser.add_argument("--max-turns", type=int, default=8)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--persona", help="Path to single persona file")
    group.add_argument("--run-all", action="store_true",
                       help="Run all personas in config/eval-personas/")

    parser.add_argument("--output", help="Output path (single persona mode)")
    parser.add_argument("--output-dir", default="tasks/eval-results/",
                        help="Output directory (--run-all mode)")

    args = parser.parse_args()

    if args.run_all:
        return run_all(args)

    if not args.output:
        persona_name = Path(args.persona).stem
        args.output = f"tasks/eval-intake-{persona_name}.md"

    protocol_text = load_file(args.protocol)
    rubric_text = load_file(RUBRIC_PATH)

    result = run_single_eval(
        args.persona, protocol_text, rubric_text,
        args.interviewer_model, args.persona_model, args.judge_model,
        args.max_turns, args.output
    )

    if result:
        j = result.get("judge_parsed")
        if j:
            print(f"\nResult: avg={j.get('average')}, pass={j.get('pass')}", file=sys.stderr)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
