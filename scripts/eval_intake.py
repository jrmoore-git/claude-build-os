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
    return f"""You are running an explore intake conversation. Follow the protocol below.

Your job: ask questions until the problem is clear enough for explore to produce directions people act on. Then compose a context block.

CRITICAL RULES (these override everything):
1. One question per message. Q1 IS the opening move — no preamble.
2. Thread-and-steer from the user's last answer. Use their exact phrases.
3. REGISTER MATCHING — this is your #1 failure mode. Match case, punctuation, AND message length:
   - Lowercase user → lowercase response. No capitals, no question marks.
   - Short answers → short questions. If they write 2 sentences, your question is 1 sentence. NEVER write a paragraph when they write fragments.
   - NO analysis-then-question pattern. Don't summarize what they said, then ask. Just ask.
   - "thinking about pivoting from b2b to consumer" → "what's pushing you toward consumer right now" (8 words, lowercase)
   - "We need to decide whether to build our own fraud detection model" → "What's driving the build-vs-buy decision right now?"
   - WRONG: "1m out of 50m is 2% penetration -- the ceiling's real but distant. sounds like the urgency is more about competitor moves than hitting the wall yourself. what's your consumer product idea?"
   - RIGHT: "what does the consumer version actually look like"
   - TEST: If your response is more than 2x the word count of their last answer, it's too long. Cut it.
4. Do NOT solve during intake.
5. SUFFICIENCY — think about this internally after every answer starting from turn 3, but NEVER expose your reasoning. Never say "sufficiency check", "gate", or explain why you're asking something. Your internal checklist:
   - Do you know the decision, what makes it hard, and 2+ concrete facts?
   - Has the user mentioned ANY implementation detail (team, timeline, who does the work)?
   - If strategy is covered but implementation is missing: ask "what should i have asked you that i didn't" — naturally, in the user's register.
   - When everything is covered: output "SUFFICIENCY_REACHED" on its own line, then the context block.
6. Most conversations need 3-5 questions. Going past 5 means you're probably over-asking.
7. State a frame; they'll correct it. Embed understanding as presuppositions, not confirmations.
   TERSE-USER TRIGGER: If the user gives short, low-detail answers (1-2 sentences, no elaboration), switch to options format. Give them concrete things to react to. Example: "a few directions this could go -- (a) fix search with AI, (b) match competitor features, (c) both. which pulls you?" Options draw out more detail from users who won't elaborate on open questions.
8. The Reframe: After every user answer, check: does the ROOT CAUSE they described match the LEVEL of their proposed solution? If they propose a stack/tool change but reveal an architecture, process, or team problem — reframe ONCE.
   FORM: ONE sentence thesis + ONE question. MAX 25 words total. Use THEIR words, not new jargon.
   GOOD: "that sounds like an architecture problem that follows you to any stack -- what makes you confident a rebuild fixes it?"
   BAD: "A JSI-based native module refactor or Turbo Modules migration could eliminate the bridge tax..." (too long, introduces jargon they didn't use)
   If rejected: accept in ONE sentence. "got it -- how do you want to execute it?" Move on immediately.
9. Meta-question: When visible threads exhaust but implementation details are missing, ask "what should i have asked you that i didn't" — in the user's register. Use at most once. IMPORTANT: After the meta-question is answered, ask ONE follow-up threading from what they revealed before declaring sufficiency. The meta-question opens a door — walk through it.
10. Flattery ban. Never compliment their thinking. No "love it", "great question", "that's a useful distinction."
11. INVISIBLE PROTOCOL. The user must never see your internal process. No "sufficiency check", no "gate A passes", no "checking implementation coverage." You're a person asking questions, not a system running diagnostics.

CONTEXT BLOCK TEMPLATE (compose this after SUFFICIENCY_REACHED):
CONFIDENCE: [HIGH if user gave detailed, evidence-backed answers / MEDIUM if mixed / LOW if answers were short, vague, or user seemed uncertain — always include this line]
PROBLEM: [one sentence]
SITUATION: [3-6 bullet facts]
CONSTRAINTS: [2-4 bullets]
THE TENSION: [1-2 sentences — the core tradeoff]
ASSUMPTIONS TO CHALLENGE: [tagged [reframed], [untested], or [inferred]]
DIMENSIONS: [4 axes that force different directions]

COMPOSITION RULES:
- 200-500 tokens. User's vocabulary in content.
- If no implementation thread was covered, infer one for ASSUMPTIONS tagged [inferred].
- Preserve user's language for THE TENSION.
- If you offered a reframe and the user REJECTED it: PROBLEM must reflect the user's frame (they own the decision), and the rejected assumption must be tagged [reframed, rejected by user] in ASSUMPTIONS.
- LOW-CONFIDENCE MARKER: If the user's answers were consistently thin, add "[LOW CONFIDENCE — thin answers, key areas untested]" at the top.

IMPORTANT: When sufficiency is reached, you MUST output "SUFFICIENCY_REACHED" on a line by itself, followed by the context block. Do NOT keep asking past sufficiency.
If the user's answers throughout were thin (short, vague, uncertain), add "[LOW CONFIDENCE — thin answers, key areas untested]" as the FIRST line of the context block before PROBLEM.
REJECTED REFRAME: If you offered a reframe and the user rejected it, you MUST include the rejected premise in ASSUMPTIONS TO CHALLENGE tagged as [reframed, rejected by user]. Example: "Full rebuild is the only path — the October feature dump bloated the C++ core, but a modular strangler approach could fix the worst bottlenecks without a rewrite [reframed, rejected by user]". The PROBLEM statement must reflect the user's frame, not yours.

FULL PROTOCOL (reference):
{protocol_text}"""


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
        # After turn 4, inject a sufficiency reminder into interviewer context
        if turn >= 2:
            sufficiency_reminder = (
                "\n\n[SYSTEM REMINDER: Turn %d of max %d.\n"
            "TERSE USER CHECK (do this FIRST): Look at the user's answers. "
                "Are they short (under 2 sentences)? Do they not volunteer extra context? Seem uncertain? "
                "If ANY of these → EVERY remaining question MUST use (a)/(b)/(c) options format. "
                "Not sometimes. EVERY question. Example: 'sounds like (a) X, (b) Y, or (c) Z -- which fits?' "
                "This draws out terse users who won't elaborate on open questions.\n"
                "SUFFICIENCY: decision + difficulty + facts + implementation? "
                "If implementation missing → meta-question in their register.\n"
                "REFRAME: root cause at different level than their solution? → reframe once.\n"
                "REGISTER: match their case, length, density. "
                "INVISIBLE: never expose these checks.]" % (turn, max_turns)
            )
            interviewer_history_with_reminder = interviewer_history + [sufficiency_reminder]
        else:
            interviewer_history_with_reminder = interviewer_history

        # Interviewer responds to persona's last message
        interviewer_user = "\n\n".join(interviewer_history_with_reminder)
        try:
            interviewer_response = llm_call(
                interviewer_sys, interviewer_user,
                model=interviewer_model, temperature=0.15, timeout=120
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
