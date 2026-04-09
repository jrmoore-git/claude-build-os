#!/usr/bin/env python3
"""
multi_model_debate.py — Three-model parallel debate with rotation refinement and judge.

Flow:
  Round 1: Three models answer the proposal independently (parallel)
  Round 2: Each answer is refined by a *different* model (rotation)
            Model A -> refined by Model B
            Model B -> refined by Model C
            Model C -> refined by Model A
  Judge:   One model reads all 3 refined answers and renders a final synthesis/verdict

Usage:
  python3 scripts/multi_model_debate.py --proposal tasks/<topic>-proposal.md \
      --output-dir tasks/ --topic <slug>

Environment:
  LITELLM_URL         (default: http://localhost:4000)
  LITELLM_MASTER_KEY  (required)
"""

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone


def _get_project_root():
    """Detect project root via git or fallback to script parent."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


PROJECT_ROOT = _get_project_root()
DEFAULT_LITELLM_URL = "http://localhost:4000"


def _load_dotenv():
    dotenv_path = os.path.join(PROJECT_ROOT, ".env")
    if not os.path.exists(dotenv_path):
        print(f"WARNING: {dotenv_path} not found", file=sys.stderr)
        return
    with open(dotenv_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:]
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            if " #" in value:
                value = value[:value.index(" #")].rstrip()
            if key and key not in os.environ:
                os.environ[key] = value


def _call_litellm(model, system_prompt, user_content, litellm_url, api_key, timeout=180):
    url = f"{litellm_url.rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": 4096,
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code} from {model}: {body[:300]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Connection error calling {model}: {e.reason}")


ROUND1_SYSTEM = """\
You are an expert analyst. Answer the proposal's questions directly, specifically, \
and adversarially — assume the competitive threat executes well.
Do not hedge. Do not repeat the question. Be concrete and crisp.
Structure your response with a numbered section per question.
Maximum 800 words total."""

ROUND2_SYSTEM = """\
You are a sharp editor and strategic thinker. You have been given a draft analysis.
Your job: refine, sharpen, and improve it. Correct any errors, fill gaps, push the analysis deeper.
You may restructure, cut, or add — but you must keep the numbered structure.
Do not add hedges or soften the conclusions. Make it more precise and more adversarial where warranted.
Maximum 900 words."""

JUDGE_SYSTEM = """\
You are an independent judge in a cross-model debate. Three different AI models have each independently answered \
the same question, then each answer was refined by a different model. \
You have all three refined answers in front of you.

Your task:
1. Identify where the three analyses AGREE — these are high-confidence findings.
2. Identify where they DIVERGE — note the most important disagreement and adjudicate it.
3. Produce a SYNTHESIS that represents the best combined answer to each question.
4. Flag any claim that appears in only one answer and is unsupported by the others — label it UNVERIFIED.
5. End with a one-paragraph VERDICT on the overall situation.

Be direct. Do not restate the question. Maximum 1200 words."""


def run_round1(proposal, models, litellm_url, api_key):
    """Call all 3 models in parallel with the proposal. Returns dict: model -> response."""
    print(f"\n[Round 1] Querying {len(models)} models in parallel...")

    def call(model):
        print(f"  -> {model} ...", flush=True)
        result = _call_litellm(model, ROUND1_SYSTEM, proposal, litellm_url, api_key)
        print(f"  done: {model} ({len(result)} chars)", flush=True)
        return model, result

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(call, m): m for m in models}
        for fut in concurrent.futures.as_completed(futures):
            model, response = fut.result()
            results[model] = response

    return results


def run_round2(round1_results, rotation, litellm_url, api_key):
    """Each model refines a different model's output. rotation: list of (author_model, refiner_model)."""
    print(f"\n[Round 2] Rotating refinement across {len(rotation)} pairs...")

    def refine(author_model, refiner_model):
        draft = round1_results[author_model]
        user_content = f"Here is the draft analysis from a different model:\n\n{draft}\n\nRefine and improve it."
        print(f"  -> {refiner_model} refines {author_model} ...", flush=True)
        result = _call_litellm(refiner_model, ROUND2_SYSTEM, user_content, litellm_url, api_key)
        print(f"  done: {refiner_model} ({len(result)} chars)", flush=True)
        return author_model, refiner_model, result

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(refine, a, r): (a, r) for a, r in rotation}
        for fut in concurrent.futures.as_completed(futures):
            author_model, refiner_model, response = fut.result()
            results[author_model] = {"refiner": refiner_model, "text": response}

    return results


def run_judge(round1_results, round2_results, judge_model, proposal, litellm_url, api_key):
    """Judge reads all 3 refined answers and produces synthesis."""
    print(f"\n[Judge] {judge_model} synthesizing all 3 refined answers...")

    sections = [f"# Original Proposal\n\n{proposal}\n\n---\n"]
    for original_model, data in round2_results.items():
        refiner = data["refiner"]
        text = data["text"]
        round1_text = round1_results[original_model]
        sections.append(
            f"## Answer Set: Originally by {original_model}, refined by {refiner}\n\n"
            f"### Round 1 (original):\n{round1_text}\n\n"
            f"### Round 2 (refined):\n{text}\n"
        )

    combined = "\n---\n".join(sections)
    result = _call_litellm(judge_model, JUDGE_SYSTEM, combined, litellm_url, api_key, timeout=300)
    print(f"  done: Judge ({len(result)} chars)", flush=True)
    return result


def write_output(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"  Wrote: {path}")


def main():
    _load_dotenv()
    parser = argparse.ArgumentParser(description="Multi-model debate with rotation refinement and judge")
    parser.add_argument("--proposal", required=True, help="Path to proposal markdown file")
    parser.add_argument("--output-dir", default="tasks", help="Output directory")
    parser.add_argument("--topic", required=True, help="Slug for output filenames")
    parser.add_argument("--judge-model", default="gpt-4o", help="Judge model (default: gpt-4o)")
    parser.add_argument("--models", nargs=3, default=["claude-sonnet-4-20250514", "gpt-4o", "gemini-2.5-pro"],
                        help="Three models for the debate (default: claude-sonnet-4, gpt-4o, gemini-2.5-pro)")
    args = parser.parse_args()

    litellm_url = os.environ.get("LITELLM_URL", DEFAULT_LITELLM_URL)
    api_key = os.environ.get("LITELLM_MASTER_KEY")
    if not api_key:
        print("ERROR: LITELLM_MASTER_KEY not set", file=sys.stderr)
        return 1

    with open(args.proposal) as f:
        proposal = f.read()

    models = args.models
    # Rotation: model[0] -> refined by model[1], model[1] -> refined by model[2], model[2] -> refined by model[0]
    rotation = [
        (models[0], models[1]),
        (models[1], models[2]),
        (models[2], models[0]),
    ]

    outdir = args.output_dir
    slug = args.topic

    # Round 1
    round1 = run_round1(proposal, models, litellm_url, api_key)
    for model, text in round1.items():
        safe = model.replace("/", "_").replace("-", "_")
        write_output(os.path.join(outdir, f"{slug}-r1-{safe}.md"), text)

    # Round 2
    round2 = run_round2(round1, rotation, litellm_url, api_key)
    for orig_model, data in round2.items():
        safe = orig_model.replace("/", "_").replace("-", "_")
        write_output(
            os.path.join(outdir, f"{slug}-r2-{safe}-refined-by-{data['refiner'].replace('/', '_').replace('-', '_')}.md"),
            data["text"]
        )

    # Judge
    judgment = run_judge(round1, round2, args.judge_model, proposal, litellm_url, api_key)
    write_output(os.path.join(outdir, f"{slug}-judgment.md"), judgment)

    print(f"\nDone. Judgment: {outdir}/{slug}-judgment.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
