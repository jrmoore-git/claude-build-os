#!/usr/bin/env python3.11
"""Phase 0x orchestrator — dual-mode Frame critique pass over cmd_judge output.

Runs frame-structural (tools OFF, different model family from author) + frame-factual
(tools ON) in parallel on (judge_output + proposal + challenge_output). Applies the
pre-committed aggregation rule (structural vetoes factual-only). Writes markdown
output with both critiques and final REJECT/PROCEED assessment.

Plan: tasks/judge-stage-frame-reach-audit-plan.md (LOCKED pre-commits in frontmatter).

Safety:
- Family-overlap enforcement: exits before any LLM call if frame-structural family
  matches author family (correlated-blind-spot risk).
- Credential-pattern pre-check: exits before any LLM call if inputs contain
  credentials or private keys.
- NO modification to scripts/debate.py or cmd_judge. Self-contained.
"""

import argparse
import concurrent.futures
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import debate_common
import debate_tools
import llm_client
from debate_common import _get_model_family

debate_common._load_dotenv()


# Credential patterns — exit-before-egress if any match in inputs.
CREDENTIAL_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
]


FRAME_STRUCTURAL_PROMPT = """\
You are an adversarial frame reviewer critiquing a cmd_judge VERDICT at the judge stage
of a cross-model debate pipeline. You have NO tools — reason from the text alone.

Your job: identify judge adjudication errors. Given (a) the original proposal, (b) the
challenger findings, and (c) the judge's verdict + rationale, determine whether the judge:
- MISSED DISQUALIFIER: produced PROCEED/REVISE when a challenger finding warranted REJECT.
- COLLAPSED DEFECTS: merged two distinct findings into one ruling, dropping content.
- FALSE DISMISS: rejected a valid MATERIAL finding as noise.
- OVERREACHED: escalated to REJECT when REVISE was appropriate (over-restriction).

You do NOT re-challenge the proposal itself. You critique only whether the judge
adjudicated the findings correctly.

Output format:
## Judge-Adjudication Critique
1. [TYPE] [MATERIAL/ADVISORY]: explanation (cite specific finding/verdict passage)
...

## Frame-Structural Verdict
One of: REJECT (judge missed a disqualifier) | REVISE (judge made smaller errors) | PROCEED (judge adjudicated correctly).
One-sentence rationale.
"""


FRAME_FACTUAL_PROMPT = """\
You are an adversarial frame reviewer with tool access, operating at the judge stage
of a cross-model debate pipeline. Use tools AGGRESSIVELY to verify factual claims in:
(a) the original proposal, (b) challenger findings, and (c) the judge's rationale.

Your job: identify factual errors in the judge's adjudication. Given tool access:
- Are claims in the judge's rationale verifiable against the codebase?
- Did the judge dismiss a challenger finding whose factual basis the tools confirm?
- Did the judge uphold a challenger finding whose factual basis the tools falsify?
- Are there "already shipped" patterns the judge missed? (This class catches REJECT-worthy
  findings — proposals that claim to add capability already present in code.)

Use tools: check_code_presence, read_file_snippet, get_recent_commits. Cite tool output
in each finding.

You do NOT re-challenge the proposal itself. You critique only whether the judge's
adjudication matches codebase reality.

Output format:
## Judge-Adjudication Factual Critique
1. [TYPE] [MATERIAL/ADVISORY]: explanation + cited tool result
...

## Frame-Factual Verdict
One of: REJECT (judge dismissed a verifiable disqualifier) | REVISE (judge made
factual errors) | PROCEED (judge's rationale checks out).
One-sentence rationale.
"""


def _scan_credentials(*texts):
    """Return list of (pattern, sample) tuples for any credential matches."""
    hits = []
    for text in texts:
        for pat in CREDENTIAL_PATTERNS:
            m = pat.search(text)
            if m:
                hits.append((pat.pattern, m.group(0)[:20] + "..."))
    return hits


def _infer_author_family(proposal_text):
    """Infer author model family from proposal frontmatter if present.

    Falls back to 'claude' since Round 2 proposals were typically Claude-authored.
    Returns family string. Caller can override via --author-family.
    """
    for line in proposal_text.splitlines()[:30]:
        line = line.strip()
        if line.startswith("author_model:") or line.startswith("author:"):
            model = line.split(":", 1)[1].strip().strip('"\'')
            return _get_model_family(model)
    return "claude"


def _assemble_input(proposal, challenge, judge_output):
    """Build the combined user content for Frame."""
    return (
        "## Proposal\n\n"
        f"{proposal}\n\n"
        "---\n\n"
        "## Challenger Findings\n\n"
        f"{challenge}\n\n"
        "---\n\n"
        "## Judge Verdict + Rationale\n\n"
        f"{judge_output}\n"
    )


def _run_frame_structural(user_content, model):
    """Run frame-structural (tools OFF)."""
    t0 = time.time()
    result = llm_client.llm_call(
        system=FRAME_STRUCTURAL_PROMPT,
        user=user_content,
        model=model,
        temperature=0.5,
        max_tokens=2048,
        timeout=120,
    )
    return {"content": result, "duration": time.time() - t0, "model": model}


def _run_frame_factual(user_content, model):
    """Run frame-factual (tools ON)."""
    t0 = time.time()
    result = llm_client.llm_tool_loop(
        system=FRAME_FACTUAL_PROMPT,
        user=user_content,
        tools=debate_tools.TOOL_DEFINITIONS,
        tool_executor=debate_tools.execute_tool,
        model=model,
        temperature=0.5,
        max_tokens=2048,
        max_turns=8,
        timeout=120,
    )
    return {
        "content": result["content"],
        "turns": result["turns"],
        "tool_calls": len(result["tool_calls"]),
        "duration": time.time() - t0,
        "model": model,
    }


def _extract_verdict(critique_text, section_header):
    """Parse REJECT/REVISE/PROCEED verdict from a critique output."""
    lines = critique_text.splitlines()
    idx = next((i for i, l in enumerate(lines) if section_header in l), None)
    if idx is None:
        return "UNPARSED"
    for line in lines[idx : idx + 5]:
        for v in ("REJECT", "REVISE", "PROCEED"):
            if re.search(rf"\b{v}\b", line):
                return v
    return "UNPARSED"


def _parse_material_findings(critique_text):
    """Count MATERIAL findings in a critique. Returns int."""
    return len(re.findall(r"\[MATERIAL\]", critique_text))


def _aggregate(structural, factual):
    """Apply locked aggregation rule.

    Rule (from plan frontmatter):
      - Structural vetoes factual-only findings: if structural says PROCEED and factual
        alone says REJECT, final is PROCEED.
      - Second clause: a finding whose only novel substantive content is a factual claim
        unsupported by structural is discarded entirely (operationalized below via
        verdict comparison — we treat factual-only REJECT as non-triggering).

    Decision table:
      structural=PROCEED, factual=PROCEED  -> PROCEED
      structural=PROCEED, factual=REVISE   -> PROCEED (factual-only findings don't trigger)
      structural=PROCEED, factual=REJECT   -> PROCEED (factual-only REJECT cannot trigger)
      structural=REVISE,  factual=PROCEED  -> REVISE
      structural=REVISE,  factual=REVISE   -> REVISE
      structural=REVISE,  factual=REJECT   -> REJECT (structural co-signs concern → factual escalates OK)
      structural=REJECT,  *                -> REJECT (structural alone can escalate)
      UNPARSED in structural               -> UNPARSED (investigate before trusting output)
    """
    s, f = structural["verdict"], factual["verdict"]
    if s == "UNPARSED":
        return "UNPARSED"
    if s == "REJECT":
        return "REJECT"
    if s == "PROCEED":
        return "PROCEED"
    # s == "REVISE"
    if f == "REJECT":
        return "REJECT"
    return "REVISE"


def _write_output(out_path, args, structural, factual, aggregate_verdict, author_family):
    lines = []
    lines.append("---")
    lines.append(f"topic: judge-stage-frame-reach-audit")
    lines.append(f"phase: 0x-smoke" if args.smoke else "phase: 1-run")
    lines.append(f"orchestrator: judge_frame_orchestrator.py")
    lines.append(f"inputs:")
    lines.append(f"  proposal: {args.proposal}")
    lines.append(f"  challenge: {args.challenge}")
    lines.append(f"  judge_output: {args.judge_output}")
    lines.append(f"models:")
    lines.append(f"  frame_structural: {structural['model']}")
    lines.append(f"  frame_factual: {factual['model']}")
    lines.append(f"author_family: {author_family}")
    lines.append(f"aggregation_rule: structural-vetoes-factual-only")
    lines.append(f"verdicts:")
    lines.append(f"  structural: {structural['verdict']}")
    lines.append(f"  factual: {factual['verdict']}")
    lines.append(f"  aggregate: {aggregate_verdict}")
    lines.append(f"material_finding_counts:")
    lines.append(f"  structural: {structural['material_count']}")
    lines.append(f"  factual: {factual['material_count']}")
    lines.append(f"timing_sec:")
    lines.append(f"  structural: {structural['duration']:.1f}")
    lines.append(f"  factual: {factual['duration']:.1f}")
    if "tool_calls" in factual:
        lines.append(f"factual_tool_calls: {factual['tool_calls']}")
    lines.append("---\n")
    lines.append("# Judge-Stage Frame Critique\n")
    lines.append(f"**Aggregate verdict:** {aggregate_verdict}\n")
    lines.append("## Frame-Structural Critique\n")
    lines.append(structural["content"])
    lines.append("\n---\n")
    lines.append("## Frame-Factual Critique\n")
    lines.append(factual["content"])
    pathlib.Path(out_path).write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--judge-output", required=True, help="Path to cmd_judge output file.")
    parser.add_argument("--proposal", required=True, help="Path to proposal file.")
    parser.add_argument("--challenge", required=True, help="Path to challenge/findings file.")
    parser.add_argument("--output", required=True, help="Output path for critique file.")
    parser.add_argument("--frame-structural-model", default="gemini-3.1-pro", help="Model for frame-structural (default: gemini-3.1-pro, non-claude for anti-family-overlap).")
    parser.add_argument("--frame-factual-model", default="gpt-5.4", help="Model for frame-factual (default: gpt-5.4).")
    parser.add_argument("--author-family", default=None, help="Override author family (inferred from proposal frontmatter if absent).")
    parser.add_argument("--smoke", action="store_true", help="Mark output as smoke test (Phase 0x).")
    args = parser.parse_args()

    proposal_text = pathlib.Path(args.proposal).read_text()
    challenge_text = pathlib.Path(args.challenge).read_text()
    judge_text = pathlib.Path(args.judge_output).read_text()

    # Credential pre-check (step 3 of plan Phase 0x).
    cred_hits = _scan_credentials(proposal_text, challenge_text, judge_text)
    if cred_hits:
        print(f"ERROR: credential patterns detected in input: {cred_hits}", file=sys.stderr)
        sys.exit(2)

    # Family-overlap check (step 2 of plan Phase 0x).
    author_family = args.author_family or _infer_author_family(proposal_text)
    structural_family = _get_model_family(args.frame_structural_model)
    if structural_family == author_family:
        print(
            f"ERROR: family-overlap — frame-structural model {args.frame_structural_model} "
            f"(family={structural_family}) matches author family ({author_family}). "
            f"This re-introduces correlated-blind-spot risk. Pick a non-{author_family} model.",
            file=sys.stderr,
        )
        sys.exit(3)

    print(f"[orchestrator] author_family={author_family}, structural={structural_family} → OK", file=sys.stderr)

    user_content = _assemble_input(proposal_text, challenge_text, judge_text)

    # Run both halves in parallel.
    print(f"[orchestrator] launching frame-structural ({args.frame_structural_model}) + frame-factual ({args.frame_factual_model})...", file=sys.stderr)
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        fut_structural = ex.submit(_run_frame_structural, user_content, args.frame_structural_model)
        fut_factual = ex.submit(_run_frame_factual, user_content, args.frame_factual_model)
        structural = fut_structural.result()
        factual = fut_factual.result()

    structural["verdict"] = _extract_verdict(structural["content"], "Frame-Structural Verdict")
    structural["material_count"] = _parse_material_findings(structural["content"])
    factual["verdict"] = _extract_verdict(factual["content"], "Frame-Factual Verdict")
    factual["material_count"] = _parse_material_findings(factual["content"])

    aggregate = _aggregate(structural, factual)
    total_dur = time.time() - t0

    _write_output(args.output, args, structural, factual, aggregate, author_family)

    status = {
        "status": "ok",
        "verdicts": {
            "structural": structural["verdict"],
            "factual": factual["verdict"],
            "aggregate": aggregate,
        },
        "material_counts": {
            "structural": structural["material_count"],
            "factual": factual["material_count"],
        },
        "wall_clock_sec": round(total_dur, 1),
        "tool_calls": factual.get("tool_calls", 0),
        "output": args.output,
    }
    print(json.dumps(status), file=sys.stderr)


if __name__ == "__main__":
    main()
