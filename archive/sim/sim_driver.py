#!/usr/bin/env python3
"""
sim_driver.py — 3-Agent Simulation Loop for the Skill Compiler Simulator.

Orchestrates executor (Claude), persona (Gemini), and judge (GPT) to simulate
a user interacting with a BuildOS skill, then scores the interaction.

Usage:
    # Single run
    python3.11 scripts/sim_driver.py --skill explore \
        --persona fixtures/sim_compiler/explore/personas/anchor-1.json \
        --rubric fixtures/sim_compiler/explore/rubric.json

    # Batch mode (all personas in directory)
    python3.11 scripts/sim_driver.py --skill explore \
        --batch fixtures/sim_compiler/explore/personas/ \
        --rubric fixtures/sim_compiler/explore/rubric.json

    # Dry-run (single turn only, no judge)
    python3.11 scripts/sim_driver.py --skill explore \
        --persona fixtures/sim_compiler/explore/personas/anchor-1.json \
        --rubric fixtures/sim_compiler/explore/rubric.json --dry-run
"""

import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm_client import llm_call, llm_call_json, LLMError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"
FIXTURES_DIR = PROJECT_ROOT / "fixtures" / "sim_compiler"
LOGS_DIR = PROJECT_ROOT / "logs"

SIMULATOR_VERSION = "0.1.0-pilot"
DEFAULT_MAX_TURNS = 15
DEFAULT_EXECUTOR_MODEL = "claude-opus-4-6"
DEFAULT_PERSONA_MODEL = "gemini-3.1-pro"
DEFAULT_JUDGE_MODEL = "gpt-5.4"

# Termination signals the executor might produce
COMPLETION_SIGNALS = [
    "SUFFICIENCY_REACHED",
    "[COMPLETE]",
    "[DONE]",
    "## Output",      # skill producing final output
    "## Report",
    "## Result",
]

ABANDONMENT_SIGNALS = [
    "I'm done",
    "never mind",
    "forget it",
    "this isn't working",
    "I'll figure it out myself",
]

SIM_TOOL_UNAVAILABLE = "[SIM] Tool/resource not available in simulation environment"


# --- Built-in turn hooks ---

def sufficiency_reminder_hook(turn, max_turns, executor_history, transcript):
    """Reproduce eval_intake.py's mid-loop sufficiency/register reminders.

    Fires from turn 2 onward, matching eval_intake's intervention pattern.
    """
    if turn < 2:
        return None
    return (
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


def find_skill_path(skill_name):
    """Find the SKILL.md file for a given skill name."""
    skill_dir = SKILLS_DIR / skill_name
    skill_file = skill_dir / "SKILL.md"
    if skill_file.exists():
        return skill_file
    for path in SKILLS_DIR.glob("*/SKILL.md"):
        if path.parent.name == skill_name:
            return path
    return None


def load_json(path):
    """Load a JSON file."""
    with open(path) as f:
        return json.load(f)


def build_executor_system(skill_content, skill_name):
    """System prompt for the executor (runs the skill)."""
    return f"""You are executing the BuildOS skill "/{skill_name}" in a simulation environment.

Follow the skill procedure below exactly as written. Treat messages from the user as real user input.

SIMULATION RULES:
- Follow the skill procedure step by step.
- When the procedure calls for asking the user a question, ask it naturally.
- When the procedure calls for tool use (bash, file reads, web search), describe what you would do but note that tools are limited in this environment.
- When you complete the skill's objective, signal completion by writing "[COMPLETE]" on its own line, followed by any final output.
- If you cannot proceed due to missing tools or resources, write "[BLOCKED]" followed by what you need.
- Stay in character as the skill executor. Do not break the fourth wall or mention simulation.

SKILL PROCEDURE:
<document type="skill_procedure">
{skill_content}
</document>"""


def build_persona_system(persona_card):
    """System prompt for the persona (simulates the user).

    The persona sees ONLY their card — never the skill procedure or rubric.
    """
    hs = persona_card.get("hidden_state", {})
    rules = persona_card.get("behavioral_rules", "")
    opening = persona_card.get("opening_input", "")

    return f"""You are playing a user in a conversation with an AI assistant. Stay in character.

<document type="persona_card">
YOUR PROFILE:
- Goal: {hs.get('goal', 'unspecified')}
- Domain knowledge: {hs.get('knowledge', 'intermediate')}
- Urgency: {hs.get('urgency', 'medium')}
- Patience: {hs.get('patience', 'medium')}
- Trust in AI: {hs.get('trust', 'medium')}
- Cooperativeness: {hs.get('cooperativeness', 'medium')}

BEHAVIORAL RULES:
{rules}
</document>

RULES:
- Respond as this person would. Use appropriate vocabulary and tone for your knowledge level.
- Reveal information naturally — don't dump everything at once.
- Follow the behavioral rules precisely.
- Do NOT break character. Do NOT mention simulation.
- Do NOT be artificially helpful. Real users hedge, deflect, and sometimes don't give the answer the AI wants.
- Keep responses concise (1-4 sentences) unless your behavioral rules say otherwise."""


def build_judge_system(rubric):
    """System prompt for the judge (scores the completed interaction)."""
    dims = rubric.get("dimensions", [])
    dim_text = "\n".join(
        f"- {d['name']}: {d['description']} (scale {d.get('scale_min', 1)}-{d.get('scale_max', 5)})"
        for d in dims
    )
    return f"""You are an independent judge evaluating a simulated skill interaction.

Score the transcript on each dimension below. For each dimension, provide:
1. A numeric score ({dims[0].get('scale_min', 1)}-{dims[0].get('scale_max', 5)})
2. A brief rationale (1-2 sentences) citing specific turns

SCORING DIMENSIONS:
{dim_text}

Return a JSON object with:
{{
  "scores": {{"dimension_name": score_number, ...}},
  "rationale": "Overall assessment citing specific turns",
  "objective_achieved": true/false
}}

Be rigorous. Quote specific turns. Don't be generous — score exactly what you see.
Return ONLY valid JSON."""


def check_termination(executor_response, persona_response, turn_num, max_turns):
    """Check termination conditions after each turn.

    Returns (should_terminate, reason, status) or (False, None, None).
    """
    # Condition 1: Executor signals completion
    for signal in COMPLETION_SIGNALS:
        if signal in executor_response:
            return True, f"Executor signaled completion ({signal})", "success"

    # Condition 2: Persona abandons
    persona_lower = persona_response.lower() if persona_response else ""
    for signal in ABANDONMENT_SIGNALS:
        if signal.lower() in persona_lower:
            return True, f"Persona abandoned ({signal})", "abandoned"

    # Condition 3: Executor declares inability
    if "[BLOCKED]" in executor_response:
        return True, "Executor blocked on missing resource", "blocked_environment"

    # Condition 4: Turn limit
    if turn_num >= max_turns:
        return True, f"Hard turn limit reached ({max_turns})", "max_turns"

    return False, None, None


def check_mock_fixture(skill_name, resource_path):
    """Check if a mock fixture exists for a requested resource."""
    mock_dir = FIXTURES_DIR / skill_name / "mocks"
    if not mock_dir.exists():
        return None
    mock_file = mock_dir / resource_path.replace("/", "_")
    if mock_file.exists():
        return mock_file.read_text()
    return None


def run_simulation(skill_name, skill_content, persona_card, rubric,
                   executor_model, persona_model, judge_model, max_turns,
                   dry_run=False, turn_hooks=None):
    """Run a single 3-agent simulation loop.

    turn_hooks: optional list of callables, each with signature:
        hook(turn_num, max_turns, executor_history, transcript) -> str or None
    If a hook returns a string, it's appended to executor_history as a system
    reminder before the executor's next call. Multiple hooks can fire per turn.

    Returns a result dict matching the output schema.
    """
    run_id = str(uuid.uuid4())
    timestamp = datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()

    executor_sys = build_executor_system(skill_content, skill_name)
    persona_sys = build_persona_system(persona_card)

    transcript = []
    executor_history = []
    persona_history = []

    # Persona opens with their opening input
    opening = persona_card.get("opening_input", "help")
    transcript.append({
        "turn": 0,
        "role": "persona",
        "content": opening,
        "timestamp": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
    })
    executor_history.append(f"USER: {opening}")

    final_status = "max_turns"
    termination_reason = f"Reached {max_turns} turn limit"
    last_executor_response = ""

    for turn in range(1, max_turns + 1):
        # Run turn hooks — inject system reminders into executor context
        if turn_hooks:
            for hook in turn_hooks:
                reminder = hook(turn, max_turns, executor_history, transcript)
                if reminder:
                    executor_history.append(reminder)

        # Executor responds
        executor_user = "\n\n".join(executor_history)
        try:
            executor_response = llm_call(
                executor_sys, executor_user,
                model=executor_model, temperature=0.15, timeout=120
            )
        except LLMError as e:
            transcript.append({
                "turn": turn, "role": "system",
                "content": f"Executor error: {e}",
                "timestamp": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
            })
            final_status = "failure"
            termination_reason = f"Executor LLM error: {e}"
            break

        transcript.append({
            "turn": turn, "role": "executor",
            "content": executor_response,
            "timestamp": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
        })
        persona_history.append(f"ASSISTANT: {executor_response}")
        last_executor_response = executor_response

        if dry_run:
            final_status = "dry_run"
            termination_reason = "Dry run — stopped after first executor turn"
            break

        # Persona responds
        persona_user = "\n\n".join(persona_history)
        try:
            persona_response = llm_call(
                persona_sys, persona_user,
                model=persona_model, temperature=0.4, timeout=60
            )
        except LLMError as e:
            transcript.append({
                "turn": turn, "role": "system",
                "content": f"Persona error: {e}",
                "timestamp": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
            })
            final_status = "failure"
            termination_reason = f"Persona LLM error: {e}"
            break

        transcript.append({
            "turn": turn, "role": "persona",
            "content": persona_response,
            "timestamp": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
        })
        executor_history.append(f"ASSISTANT: {executor_response}")
        executor_history.append(f"USER: {persona_response}")

        # Check termination
        should_stop, reason, status = check_termination(
            executor_response, persona_response, turn, max_turns
        )
        if should_stop:
            final_status = status
            termination_reason = reason
            break

    # Judge the transcript (skip for dry-run)
    judge_scores = {}
    judge_rationale = ""
    objective_achieved = False

    if not dry_run:
        judge_sys = build_judge_system(rubric)
        transcript_text = "\n\n".join(
            f"[Turn {t['turn']}] {t['role'].upper()}: {t['content']}"
            for t in transcript
        )
        # Build ground truth context for the judge.
        # The judge needs the persona's hidden state to score dimensions like
        # hidden_truth_surfacing. This mirrors eval_intake.py which passes the
        # full persona file to the judge.
        hs = persona_card.get("hidden_state", {})
        ground_truth = (
            f"PERSONA GROUND TRUTH (for scoring only):\n"
            f"- Goal: {hs.get('goal', 'unspecified')}\n"
            f"- Hidden truth: {hs.get('hidden_truth', 'none')}\n"
            f"- Knowledge level: {hs.get('knowledge', 'intermediate')}\n"
        )
        judge_user = (
            f"TRANSCRIPT:\n{transcript_text}\n\n"
            f"{ground_truth}\n"
            f"TERMINATION: {termination_reason}\n"
            f"FINAL STATUS: {final_status}"
        )

        try:
            judge_result = llm_call_json(
                judge_sys, judge_user,
                model=judge_model, temperature=0.0, timeout=120
            )
            judge_scores = judge_result.get("scores", {})
            judge_rationale = judge_result.get("rationale", "")
            objective_achieved = judge_result.get("objective_achieved", False)
        except LLMError as e:
            judge_rationale = f"Judge error: {e}"
            print(f"WARNING: Judge call failed: {e}", file=sys.stderr)

    # Build result
    result = {
        "run_id": run_id,
        "timestamp": timestamp,
        "simulator_version": SIMULATOR_VERSION,
        "skill": skill_name,
        "skill_source_path": f"skills/{skill_name}/SKILL.md",
        "persona_state": {
            "persona_id": persona_card.get("persona_id", "unknown"),
            "persona_type": persona_card.get("persona_type", "unknown"),
            **persona_card.get("hidden_state", {})
        },
        "execution_config": {
            "executor_model": executor_model,
            "persona_model": persona_model,
            "judge_model": judge_model,
            "max_turns": max_turns
        },
        "transcript": transcript,
        "final_status": final_status,
        "termination_reason": termination_reason,
        "objective_achieved": objective_achieved,
        "judge_scores": judge_scores,
        "judge_rationale": judge_rationale,
        "rubric_metadata": {
            "rubric_version": rubric.get("rubric_version", "unknown"),
            "rubric_source": "generated_from_validated_ir",
        }
    }

    return result


def write_result(result, output_path=None):
    """Append a simulation result to the JSONL log."""
    if output_path is None:
        output_path = LOGS_DIR / "sim_compiler_runs.jsonl"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "a") as f:
        f.write(json.dumps(result) + "\n")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="3-Agent Simulation Driver")
    parser.add_argument("--skill", required=True, help="Skill name (e.g., 'explore')")
    parser.add_argument("--persona", help="Path to persona JSON file")
    parser.add_argument("--batch", help="Directory of persona JSON files (batch mode)")
    parser.add_argument("--rubric", required=True, help="Path to rubric JSON file")
    parser.add_argument("--executor-model", default=DEFAULT_EXECUTOR_MODEL)
    parser.add_argument("--persona-model", default=DEFAULT_PERSONA_MODEL)
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL)
    parser.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
    parser.add_argument("--output", help="Output JSONL path (default: logs/sim_compiler_runs.jsonl)")
    parser.add_argument("--dry-run", action="store_true", help="Run 1 turn only, no judge")
    args = parser.parse_args()

    # Load skill
    skill_path = find_skill_path(args.skill)
    if not skill_path:
        print(f"ERROR: Skill '{args.skill}' not found", file=sys.stderr)
        sys.exit(1)
    skill_content = skill_path.read_text()

    # Load rubric
    rubric = load_json(args.rubric)

    # Determine persona files
    if args.batch:
        batch_dir = Path(args.batch)
        if not batch_dir.exists():
            print(f"ERROR: Batch directory not found: {batch_dir}", file=sys.stderr)
            sys.exit(1)
        persona_files = sorted(batch_dir.glob("*.json"))
        if not persona_files:
            print(f"ERROR: No .json files in {batch_dir}", file=sys.stderr)
            sys.exit(1)
    elif args.persona:
        persona_files = [Path(args.persona)]
    else:
        parser.error("Either --persona or --batch is required")

    # Run simulations
    results = []
    for pf in persona_files:
        persona_card = load_json(pf)
        pid = persona_card.get("persona_id", pf.stem)
        print(f"Running simulation: {args.skill} x {pid}...", file=sys.stderr)

        t0 = time.time()
        result = run_simulation(
            skill_name=args.skill,
            skill_content=skill_content,
            persona_card=persona_card,
            rubric=rubric,
            executor_model=args.executor_model,
            persona_model=args.persona_model,
            judge_model=args.judge_model,
            max_turns=args.max_turns,
            dry_run=args.dry_run,
        )
        elapsed = time.time() - t0

        results.append(result)

        # Print summary
        scores_str = ", ".join(f"{k}={v}" for k, v in result["judge_scores"].items())
        print(
            f"  {pid}: {result['final_status']} "
            f"({result['termination_reason']}) "
            f"[{elapsed:.1f}s] "
            f"scores: {scores_str or 'N/A'}",
            file=sys.stderr
        )

        # Write to log
        if not args.dry_run:
            out_path = write_result(result, args.output)

    # Summary
    total = len(results)
    statuses = {}
    for r in results:
        s = r["final_status"]
        statuses[s] = statuses.get(s, 0) + 1

    print(f"\nDone. {total} simulation(s) completed.", file=sys.stderr)
    for s, c in sorted(statuses.items()):
        print(f"  {s}: {c}", file=sys.stderr)

    if args.dry_run:
        print(json.dumps(results, indent=2))
    elif total > 0:
        print(f"Results written to {LOGS_DIR / 'sim_compiler_runs.jsonl'}", file=sys.stderr)


if __name__ == "__main__":
    main()
