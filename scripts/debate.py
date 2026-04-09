#!/usr/bin/env python3
"""
debate.py — Cross-model review automation for review protocol.

Subcommands:
    challenge     Send proposal to challenger models for adversarial review
    judge         Independent judgment: non-author model evaluates challenges
    refine        Iterative cross-model refinement (guided by judgment)
    review        Single-model review via persona (for skill inline reviews)
    review-panel  Multi-persona panel review (3 models, anonymous labels)
    check-models  Compare LiteLLM available models against config
    compare       Compare two review methods on the same document
    verdict       Send resolution back to challengers for final verdict (legacy)

Standard pipeline:
    1. challenge -> find issues (adversarial)
    2. judge -> accept/dismiss each issue (independent)
    3. refine --judgment -> fix accepted issues + improve (collaborative)

Usage:
    python3 scripts/debate.py challenge \
        --proposal tasks/<topic>-proposal.md \
        --personas architect,security,pm \
        --output tasks/<topic>-challenge.md

    python3 scripts/debate.py judge \
        --proposal tasks/<topic>-proposal.md \
        --challenge tasks/<topic>-challenge.md \
        --output tasks/<topic>-judgment.md

    python3 scripts/debate.py refine \
        --document tasks/<topic>-proposal.md \
        --judgment tasks/<topic>-judgment.md \
        --rounds 3 \
        --output tasks/<topic>-refined.md

    python3 scripts/debate.py compare \
        --original tasks/<topic>-proposal.md \
        --method-a tasks/<topic>-challenge.md \
        --method-b tasks/<topic>-refined.md \
        --output tasks/<topic>-compare.md

Environment:
    LITELLM_URL          LiteLLM base URL (default: http://localhost:4000)
    LITELLM_MASTER_KEY   API key for LiteLLM (required)
"""
import argparse
import json
import os
import re
import string
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta

# ── Project root & .env loading ──────────────────────────────────────────────


def _detect_project_root():
    """Detect project root via git."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


PROJECT_ROOT = _detect_project_root()


def _load_dotenv():
    """Load .env from project root for any env vars not already set.

    Supported .env format: KEY=value, KEY="value", KEY='value',
    optional 'export ' prefix, # comments. No multiline values,
    no variable interpolation.
    """
    dotenv_path = os.path.join(PROJECT_ROOT, ".env")
    if not os.path.exists(dotenv_path):
        print(f"WARNING: {dotenv_path} not found, env vars may be missing",
              file=sys.stderr)
        return
    with open(dotenv_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Strip optional 'export ' prefix
            if line.startswith("export "):
                line = line[7:]
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Strip matching quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            # Strip inline comments (only outside quotes — already stripped above)
            if " #" in value:
                value = value[:value.index(" #")].rstrip()
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_LITELLM_URL = "http://localhost:4000"

ADVERSARIAL_SYSTEM_PROMPT = """\
You are an adversarial reviewer. Your job is to find flaws, not confirm quality.

For each claim or decision in the proposal:
1. What assumption does it rely on? Is that assumption verified?
2. What alternative was not considered?
3. What failure mode is not addressed?
4. Where is it over-engineered? Where is it under-engineered?

If you find genuine flaws, list them. If the proposal is sound, say so —
manufacturing criticism wastes everyone's time. APPROVE is a valid verdict.

Each challenge MUST start with a type tag:
- RISK: [something that could go wrong]
- ASSUMPTION: [unstated premise that isn't verified]
- ALTERNATIVE: [approach not considered]
- OVER-ENGINEERED: [complexity that isn't justified]
- UNDER-ENGINEERED: [missing protection or consideration]

Each challenge MUST be labeled:
- MATERIAL: Changes the recommendation, top risks, key assumptions, or next steps
- ADVISORY: Valid observation but doesn't change the decision

Output format:
## Challenges
1. [TYPE] [MATERIAL/ADVISORY]: [explanation]
[... as many as genuinely warranted, or none if the proposal is sound]

## Concessions
[What the proposal gets right — max 3 items]

## Verdict
[APPROVE / REVISE / REJECT] with one-sentence rationale"""

VERDICT_SYSTEM_PROMPT = """\
You are a final-round reviewer in a cross-model debate. You previously \
challenged a proposal. The author has now responded to your challenges with \
concessions, rebuttals, and compromises.

Review the resolution and issue a final verdict:
- APPROVE: All material challenges adequately addressed
- REVISE: Some material gaps remain but fixable
- REJECT: Fundamental issues unresolved

Output format:
## Final Verdict
[APPROVE / REVISE / REJECT]

## Rationale
[2-3 sentences explaining your decision]

## Remaining Concerns
[Any unresolved issues, or "None"]"""

JUDGE_SYSTEM_PROMPT = """\
You are an independent judge. You did NOT write this proposal. You have no \
stake in its success or failure. Your job is to evaluate challenges raised \
by adversarial reviewers against a proposal.

For each MATERIAL challenge, evaluate independently:

1. Is the challenge valid? Does it identify a real flaw in the proposal?
2. If valid, is the concern serious enough to require a change before proceeding?
3. Rate your confidence (0.0-1.0):
   - 0.9+: Clear-cut — strong evidence supports your decision
   - 0.7-0.9: Confident — most evidence supports your decision
   - 0.5-0.7: Uncertain — could go either way, would benefit from human review
   - <0.5: Low confidence — should escalate to human

For each MATERIAL challenge, decide:
- ACCEPT: The challenge is valid and the proposal must be changed to address it
- DISMISS: The challenge is invalid, a false positive, or not material
- ESCALATE: You are not confident enough to decide — flag for human review

For ADVISORY challenges: note them but do not judge. They are informational.

IMPORTANT: You must evaluate each challenge on its merits. Do not defer to \
the challengers by default (they are incentivized to disagree). Do not defer \
to the author by default (they are incentivized to minimize criticism). \
Judge the substance.

CONVERGENCE: If multiple challengers raise the same or highly similar concern \
independently, note the overlap. Treat this as corroboration — it suggests \
the issue is real — but NOT as independent evidence, since both challengers \
saw the same proposal and constraints. Evaluate the substance of the \
duplicated concern, do not mechanically upweight it.

CROSS-CONCESSION CONFLICTS: If one challenger attacks something that another \
challenger concedes as a strength, note the conflict and evaluate which \
assessment is more substantive. This is useful signal about where reasonable \
reviewers disagree.

Output format:
## Judgment

### Challenge [N]: [one-line summary]
- Challenger: [A/B]
- Materiality: [MATERIAL/ADVISORY]
- Decision: [ACCEPT/DISMISS/ESCALATE]
- Confidence: [0.0-1.0]
- Rationale: [2-3 sentences]
- Required change: [if ACCEPT — what specifically must change]

[repeat for each challenge]

## Summary
- Accepted: [count]
- Dismissed: [count]
- Escalated: [count]
- Overall: [APPROVE proposal as-is / REVISE with accepted changes / ESCALATE to human]"""

CHALLENGER_LABELS = list(string.ascii_uppercase)  # A, B, C, ...


def _shuffle_challenger_sections(challenge_body, mapping):
    """Shuffle challenger sections to eliminate position bias for the judge.

    Splits on '## Challenger X' headers, randomizes order, relabels to
    sequential letters. Returns (shuffled_body, shuffled_mapping).
    The original mapping is preserved in the output file; shuffling only
    affects what the judge sees.
    """
    import random

    # Split into sections by ## Challenger header
    sections = []
    current_label = None
    current_lines = []

    for line in challenge_body.splitlines(keepends=True):
        header_match = re.match(r"^## Challenger ([A-Z])", line)
        if header_match:
            if current_label is not None:
                sections.append((current_label, "".join(current_lines)))
            current_label = header_match.group(1)
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_label is not None:
        sections.append((current_label, "".join(current_lines)))

    if len(sections) < 2:
        return challenge_body, mapping

    # Shuffle
    random.shuffle(sections)

    # Relabel to sequential A, B, C...
    relabel_map = {}
    shuffled_parts = []
    shuffled_mapping = {}

    for i, (old_label, text) in enumerate(sections):
        new_label = CHALLENGER_LABELS[i]
        relabel_map[old_label] = new_label
        # Replace label references in section text
        relabeled = text.replace(f"Challenger {old_label}", f"Challenger {new_label}")
        shuffled_parts.append(relabeled)
        # Map new label to original model
        if old_label in mapping:
            shuffled_mapping[new_label] = mapping[old_label]

    return "".join(shuffled_parts), shuffled_mapping


TYPE_TAGS = {"RISK", "ASSUMPTION", "ALTERNATIVE", "OVER-ENGINEERED", "UNDER-ENGINEERED"}

# Hardcoded fallback mapping: persona name -> LiteLLM model
_DEFAULT_PERSONA_MODEL_MAP = {
    "architect": "gemini-3.1-pro",
    "staff": "gpt-5.4",
    "security": "gpt-5.4",
    "pm": "gemini-3.1-pro",
}

_DEFAULT_JUDGE = "gpt-5.4"
_DEFAULT_REFINE_ROTATION = ["gemini-3.1-pro", "gpt-5.4", "claude-opus-4-6"]

VALID_PERSONAS = {"architect", "staff", "security", "pm"}


def _load_config(config_path=None):
    """Load debate model config from JSON file, fall back to hardcoded defaults.

    Returns dict with keys: persona_model_map, judge_default, refine_rotation,
    single_review_default, version.
    """
    if config_path is None:
        config_path = os.path.join(PROJECT_ROOT, "config", "debate-models.json")

    defaults = {
        "persona_model_map": dict(_DEFAULT_PERSONA_MODEL_MAP),
        "judge_default": _DEFAULT_JUDGE,
        "refine_rotation": list(_DEFAULT_REFINE_ROTATION),
        "single_review_default": "gpt-5.4",
        "version": "unknown",
    }

    if not os.path.exists(config_path):
        print(f"WARNING: {config_path} not found, using hardcoded defaults",
              file=sys.stderr)
        return defaults

    try:
        with open(config_path) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {config_path}: {e} — using defaults",
              file=sys.stderr)
        return defaults

    # Validate persona names
    pmap = config.get("persona_model_map", {})
    for persona in pmap:
        if persona not in VALID_PERSONAS:
            print(f"WARNING: unknown persona '{persona}' in config — ignoring",
                  file=sys.stderr)

    return {
        "persona_model_map": {k: v for k, v in pmap.items() if k in VALID_PERSONAS}
                              or defaults["persona_model_map"],
        "judge_default": config.get("judge_default", defaults["judge_default"]),
        "refine_rotation": config.get("refine_rotation", defaults["refine_rotation"]),
        "single_review_default": config.get("single_review_default",
                                            defaults["single_review_default"]),
        "version": config.get("version", defaults["version"]),
    }


# Keep backward-compat name for any code that reads this directly
PERSONA_MODEL_MAP = _DEFAULT_PERSONA_MODEL_MAP

# Role-differentiated adversarial prompts per persona
PERSONA_PROMPTS = {
    "architect": """\
You are an adversarial architecture reviewer. Focus on:
- Structural soundness: are component boundaries clean? Are dependencies manageable?
- Scaling implications: would this survive 10x load or a major requirement change?
- Missing abstractions or wrong abstractions
- Whether the design is over-coupled, under-modular, or misaligned with the system's existing patterns

If you find genuine flaws, list them. If the proposal is sound, say so —
manufacturing criticism wastes everyone's time. APPROVE is a valid verdict.

Each challenge MUST start with a type tag:
- RISK: [something that could go wrong]
- ASSUMPTION: [unstated premise that isn't verified]
- ALTERNATIVE: [approach not considered]
- OVER-ENGINEERED: [complexity that isn't justified]
- UNDER-ENGINEERED: [missing protection or consideration]

Each challenge MUST be labeled:
- MATERIAL: Changes the recommendation, top risks, key assumptions, or next steps
- ADVISORY: Valid observation but doesn't change the decision

Output format:
## Challenges
1. [TYPE] [MATERIAL/ADVISORY]: [explanation]
[... as many as genuinely warranted, or none if the proposal is sound]

## Concessions
[What the proposal gets right — max 3 items]

## Verdict
[APPROVE / REVISE / REJECT] with one-sentence rationale""",

    "security": """\
You are an adversarial security reviewer. Focus on:
- Trust boundaries: where does trusted data end and untrusted data begin?
- Injection vectors: SQL, shell, prompt injection, XSS, SSRF
- Credential handling: are secrets stored, transmitted, and rotated correctly?
- Data exfiltration paths: could this leak private data to logs, external services, or other users?
- Privilege escalation: could a lower-trust actor gain higher-trust access?

If you find genuine flaws, list them. If the proposal is sound, say so —
manufacturing criticism wastes everyone's time. APPROVE is a valid verdict.

Each challenge MUST start with a type tag:
- RISK: [something that could go wrong]
- ASSUMPTION: [unstated premise that isn't verified]
- ALTERNATIVE: [approach not considered]
- OVER-ENGINEERED: [complexity that isn't justified]
- UNDER-ENGINEERED: [missing protection or consideration]

Each challenge MUST be labeled:
- MATERIAL: Changes the recommendation, top risks, key assumptions, or next steps
- ADVISORY: Valid observation but doesn't change the decision

Output format:
## Challenges
1. [TYPE] [MATERIAL/ADVISORY]: [explanation]
[... as many as genuinely warranted, or none if the proposal is sound]

## Concessions
[What the proposal gets right — max 3 items]

## Verdict
[APPROVE / REVISE / REJECT] with one-sentence rationale""",

    "staff": """\
You are an adversarial staff/operations reviewer. Focus on:
- Implementation feasibility: can this actually be built as described?
- Operational burden: what's the on-call, monitoring, and maintenance overhead?
- Failure modes in production: what happens when dependencies are down, data is stale, or load spikes?
- Rollback path: can this change be reverted safely?
- Hidden complexity: are there edge cases, race conditions, or state management issues not addressed?

If you find genuine flaws, list them. If the proposal is sound, say so —
manufacturing criticism wastes everyone's time. APPROVE is a valid verdict.

Each challenge MUST start with a type tag:
- RISK: [something that could go wrong]
- ASSUMPTION: [unstated premise that isn't verified]
- ALTERNATIVE: [approach not considered]
- OVER-ENGINEERED: [complexity that isn't justified]
- UNDER-ENGINEERED: [missing protection or consideration]

Each challenge MUST be labeled:
- MATERIAL: Changes the recommendation, top risks, key assumptions, or next steps
- ADVISORY: Valid observation but doesn't change the decision

Output format:
## Challenges
1. [TYPE] [MATERIAL/ADVISORY]: [explanation]
[... as many as genuinely warranted, or none if the proposal is sound]

## Concessions
[What the proposal gets right — max 3 items]

## Verdict
[APPROVE / REVISE / REJECT] with one-sentence rationale""",

    "pm": """\
You are an adversarial PM/UX reviewer. Focus on:
- User value: does this change actually matter to the end user? Is it solving a real problem?
- Over-engineering: is the proposal building more than what was asked for?
- Adoption friction: will people actually use this, or is it adding process nobody follows?
- Priority: should this be done now, or is something more important being displaced?
- Simplicity: is there a simpler version that delivers 80% of the value at 20% of the cost?

If you find genuine flaws, list them. If the proposal is sound, say so —
manufacturing criticism wastes everyone's time. APPROVE is a valid verdict.

Each challenge MUST start with a type tag:
- RISK: [something that could go wrong]
- ASSUMPTION: [unstated premise that isn't verified]
- ALTERNATIVE: [approach not considered]
- OVER-ENGINEERED: [complexity that isn't justified]
- UNDER-ENGINEERED: [missing protection or consideration]

Each challenge MUST be labeled:
- MATERIAL: Changes the recommendation, top risks, key assumptions, or next steps
- ADVISORY: Valid observation but doesn't change the decision

Output format:
## Challenges
1. [TYPE] [MATERIAL/ADVISORY]: [explanation]
[... as many as genuinely warranted, or none if the proposal is sound]

## Concessions
[What the proposal gets right — max 3 items]

## Verdict
[APPROVE / REVISE / REJECT] with one-sentence rationale""",
}


# ── LiteLLM client ──────────────────────────────────────────────────────────


def _call_litellm(model, system_prompt, user_content, litellm_url, api_key):
    """Call LiteLLM chat completions. Returns response text or raises."""
    url = f"{litellm_url.rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.7,
    }).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    resp = urllib.request.urlopen(req, timeout=300)
    body = json.loads(resp.read().decode())
    return body["choices"][0]["message"]["content"]


# ── Frontmatter ──────────────────────────────────────────────────────────────


def _build_frontmatter(debate_id, mapping):
    """Build YAML frontmatter string with debate metadata."""
    now = datetime.now(timezone(timedelta(hours=-7)))
    lines = [
        "---",
        f"debate_id: {debate_id}",
        f"created: {now.strftime('%Y-%m-%dT%H:%M:%S%z')[:25]}",
        "mapping:",
    ]
    for label, model in mapping.items():
        lines.append(f"  {label}: {model}")
    lines.append("---")
    return "\n".join(lines)


def _redact_author(proposal_text):
    """Redact author metadata from proposal before sending to challengers/judge.

    Replaces 'author: <anything>' with 'author: anonymous' in YAML frontmatter
    to prevent model-identity bias. The original file on disk is not modified.
    """
    if not proposal_text.startswith("---"):
        return proposal_text
    fm_end = proposal_text.find("---", 3)
    if fm_end < 0:
        return proposal_text
    frontmatter = proposal_text[3:fm_end]
    body = proposal_text[fm_end:]
    redacted_fm = re.sub(
        r"^author\s*:.*$", "author: anonymous", frontmatter, flags=re.MULTILINE
    )
    return "---" + redacted_fm + body


def _parse_frontmatter(text):
    """Parse YAML frontmatter from a debate file. Returns (metadata_dict, body)."""
    match = re.match(r"^---\n(.*?)\n---\n?(.*)", text, re.DOTALL)
    if not match:
        return None, text

    meta = {}
    mapping = {}
    in_mapping = False
    for line in match.group(1).splitlines():
        if line.startswith("mapping:"):
            in_mapping = True
            continue
        if in_mapping:
            if line.startswith("  "):
                key, _, val = line.strip().partition(": ")
                mapping[key] = val
            else:
                in_mapping = False
        if not in_mapping and ": " in line:
            key, _, val = line.partition(": ")
            meta[key.strip()] = val.strip()

    meta["mapping"] = mapping
    return meta, match.group(2)


# ── Validation ───────────────────────────────────────────────────────────────


def _validate_challenge(text):
    """Check that challenge items have type tags. Returns warnings list."""
    warnings = []
    numbered = re.findall(r"^\d+\.\s+(.+)", text, re.MULTILINE)

    found_tags = set()
    for item in numbered:
        matched = False
        for tag in TYPE_TAGS:
            # Accept both "RISK ..." and "[RISK] ..." formats
            if item.startswith(tag) or item.startswith(f"[{tag}]"):
                found_tags.add(tag)
                matched = True
                break
        if not matched:
            warnings.append(f"Missing type tag in: {item[:60]}...")

    return warnings


# ── Debate tracker ───────────────────────────────────────────────────────────

DEFAULT_LOG_PATH = os.path.join(PROJECT_ROOT, "stores/debate-log.jsonl")


def _log_debate_event(event, log_path=None):
    """Append a debate event to the JSONL log file."""
    path = log_path or DEFAULT_LOG_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    now = datetime.now(timezone(timedelta(hours=-7)))
    event["timestamp"] = now.strftime("%Y-%m-%dT%H:%M:%S%z")[:25]
    with open(path, "a") as f:
        f.write(json.dumps(event) + "\n")


# ── Subcommands ──────────────────────────────────────────────────────────────


def cmd_challenge(args):
    """Round 2: send proposal to challenger models, write anonymized output."""
    api_key = os.environ.get("LITELLM_MASTER_KEY")
    if not api_key:
        print("ERROR: LITELLM_MASTER_KEY not set", file=sys.stderr)
        return 1

    litellm_url = os.environ.get("LITELLM_URL", DEFAULT_LITELLM_URL)

    proposal = _redact_author(args.proposal.read())
    if not proposal.strip():
        print("ERROR: proposal file is empty", file=sys.stderr)
        return 1

    # Resolve --personas to (model, prompt) pairs; --models uses generic prompt
    config = _load_config()
    pmap = config["persona_model_map"]
    challengers = []  # list of (model, system_prompt)
    custom_prompt = args.system_prompt.read() if args.system_prompt else None

    if args.personas:
        seen = set()
        persona_models = {}  # track persona->model for duplicate warning
        for p in args.personas.split(","):
            p = p.strip().lower()
            if p not in pmap:
                print(f"ERROR: unknown persona '{p}'. Valid: {', '.join(sorted(pmap))}", file=sys.stderr)
                return 1
            model = pmap[p]
            persona_models[p] = model
            key = (model, p)
            if key not in seen:
                prompt = custom_prompt or PERSONA_PROMPTS.get(p, ADVERSARIAL_SYSTEM_PROMPT)
                challengers.append((model, prompt))
                seen.add(key)
        # Duplicate-model warning
        model_to_personas = {}
        for persona, model in persona_models.items():
            model_to_personas.setdefault(model, []).append(persona)
        for model, ps in model_to_personas.items():
            if len(ps) > 1:
                print(f"WARNING: personas {', '.join(ps)} both resolve to "
                      f"{model} — consider diversifying",
                      file=sys.stderr)
    elif args.models:
        prompt = custom_prompt or ADVERSARIAL_SYSTEM_PROMPT
        for m in args.models.split(","):
            m = m.strip()
            if m:
                challengers.append((m, prompt))
    else:
        print("ERROR: specify --models or --personas", file=sys.stderr)
        return 1

    if not challengers:
        print("ERROR: no models specified", file=sys.stderr)
        return 1

    # Derive debate_id from output filename
    debate_id = os.path.splitext(os.path.basename(args.output))[0]
    if debate_id.endswith("-challenge"):
        debate_id = debate_id[:-10]

    mapping = {}
    results = {}
    all_warnings = []

    for i, (model, sys_prompt) in enumerate(challengers):
        label = CHALLENGER_LABELS[i]
        mapping[label] = model
        print(f"Calling {label}...", file=sys.stderr)
        try:
            response = _call_litellm(model, sys_prompt, proposal, litellm_url, api_key)
            results[label] = response
            warnings = _validate_challenge(response)
            if warnings:
                all_warnings.extend([f"Challenger {label}: {w}" for w in warnings])
        except urllib.error.HTTPError as e:
            msg = f"Challenger {label} ({model}): HTTP {e.code}"
            print(f"WARNING: {msg}", file=sys.stderr)
            results[label] = f"[ERROR: {msg}]"
            all_warnings.append(msg)
        except urllib.error.URLError as e:
            msg = f"Challenger {label} ({model}): connection error — {e.reason}"
            print(f"WARNING: {msg}", file=sys.stderr)
            results[label] = f"[ERROR: {msg}]"
            all_warnings.append(msg)
        except TimeoutError:
            msg = f"Challenger {label} ({model}): timeout"
            print(f"WARNING: {msg}", file=sys.stderr)
            results[label] = f"[ERROR: {msg}]"
            all_warnings.append(msg)

    successful = sum(1 for v in results.values() if not v.startswith("[ERROR:"))
    if successful == 0:
        print("ERROR: all challenger calls failed", file=sys.stderr)
        return 2

    # Build output
    frontmatter = _build_frontmatter(debate_id, mapping)
    sections = [frontmatter, f"# {debate_id} — Challenger Reviews", ""]
    for label in sorted(results.keys()):
        sections.append(f"## Challenger {label} — Challenges")
        sections.append(results[label])
        sections.append("\n---\n")

    output_text = "\n".join(sections).rstrip() + "\n"

    with open(args.output, "w") as f:
        f.write(output_text)

    # JSON result to stdout
    result = {
        "status": "ok" if not all_warnings else "partial",
        "challengers": successful,
        "mapping": mapping,
    }
    if all_warnings:
        result["warnings"] = all_warnings
    print(json.dumps(result))

    _log_debate_event({
        "phase": "challenge",
        "debate_id": debate_id,
        "mapping": mapping,
        "challengers": successful,
        "warnings": all_warnings,
        "output": args.output,
    })
    return 0


def cmd_verdict(args):
    """Round 4: send resolution back to original challengers for final verdict."""
    api_key = os.environ.get("LITELLM_MASTER_KEY")
    if not api_key:
        print("ERROR: LITELLM_MASTER_KEY not set", file=sys.stderr)
        return 1

    litellm_url = os.environ.get("LITELLM_URL", DEFAULT_LITELLM_URL)

    challenge_text = args.challenge.read()
    meta, _ = _parse_frontmatter(challenge_text)
    if not meta or not meta.get("mapping"):
        print("ERROR: challenge file has no frontmatter mapping", file=sys.stderr)
        return 1

    resolution = args.resolution.read()
    if not resolution.strip():
        print("ERROR: resolution file is empty", file=sys.stderr)
        return 1

    system_prompt = VERDICT_SYSTEM_PROMPT
    if args.system_prompt:
        system_prompt = args.system_prompt.read()

    mapping = meta["mapping"]
    debate_id = meta.get("debate_id", "unknown")
    results = {}
    all_warnings = []

    for label, model in mapping.items():
        print(f"Calling {label} for verdict...", file=sys.stderr)
        try:
            response = _call_litellm(model, system_prompt, resolution, litellm_url, api_key)
            results[label] = response
        except urllib.error.HTTPError as e:
            msg = f"Challenger {label} ({model}): HTTP {e.code}"
            print(f"WARNING: {msg}", file=sys.stderr)
            results[label] = f"[ERROR: {msg}]"
            all_warnings.append(msg)
        except urllib.error.URLError as e:
            msg = f"Challenger {label} ({model}): connection error — {e.reason}"
            print(f"WARNING: {msg}", file=sys.stderr)
            results[label] = f"[ERROR: {msg}]"
            all_warnings.append(msg)
        except TimeoutError:
            msg = f"Challenger {label} ({model}): timeout"
            print(f"WARNING: {msg}", file=sys.stderr)
            results[label] = f"[ERROR: {msg}]"
            all_warnings.append(msg)

    successful = sum(1 for v in results.values() if not v.startswith("[ERROR:"))
    if successful == 0:
        print("ERROR: all verdict calls failed", file=sys.stderr)
        return 2

    # Build output — reuse same frontmatter format
    frontmatter = _build_frontmatter(debate_id, mapping)
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

    _log_debate_event({
        "phase": "verdict",
        "debate_id": debate_id,
        "mapping": mapping,
        "verdicts": successful,
        "warnings": all_warnings,
        "output": args.output,
    })
    return 0


def cmd_judge(args):
    """Independent judge: evaluate challenges without author self-resolution."""
    api_key = os.environ.get("LITELLM_MASTER_KEY")
    if not api_key:
        print("ERROR: LITELLM_MASTER_KEY not set", file=sys.stderr)
        return 1

    litellm_url = os.environ.get("LITELLM_URL", DEFAULT_LITELLM_URL)

    proposal = _redact_author(args.proposal.read())
    if not proposal.strip():
        print("ERROR: proposal file is empty", file=sys.stderr)
        return 1

    challenge_text = args.challenge.read()
    meta, challenge_body = _parse_frontmatter(challenge_text)
    if not meta or not meta.get("mapping"):
        print("ERROR: challenge file has no frontmatter mapping", file=sys.stderr)
        return 1

    debate_id = meta.get("debate_id", "unknown")
    config = _load_config()
    judge_model = args.model or config["judge_default"]

    # Ensure judge is not the author model (avoid self-preference bias)
    author_models = {"claude-opus-4-6", "litellm/claude-opus-4-6"}
    if judge_model in author_models:
        print("WARNING: judge model matches author model — self-preference bias risk",
              file=sys.stderr)

    system_prompt = JUDGE_SYSTEM_PROMPT
    if args.system_prompt:
        system_prompt = args.system_prompt.read()

    # Shuffle challenger sections to eliminate position bias (Zheng et al.)
    shuffled_body, shuffled_mapping = _shuffle_challenger_sections(
        challenge_body, meta.get("mapping", {})
    )

    # Build user content: proposal + shuffled challenges
    user_content = (
        "## PROPOSAL UNDER REVIEW\n\n"
        f"{proposal}\n\n"
        "---\n\n"
        "## CHALLENGER REVIEWS\n\n"
        f"{shuffled_body}\n"
    )

    # Include author rebuttal brief if provided (preserves rebuttal signal)
    if args.rebuttal:
        rebuttal_text = _redact_author(args.rebuttal.read())
        if rebuttal_text.strip():
            user_content += (
                "\n---\n\n"
                "## AUTHOR REBUTTAL (for context — author argues but does not decide)\n\n"
                f"{rebuttal_text}\n"
            )

    print(f"Calling judge ({judge_model})...", file=sys.stderr)
    try:
        response = _call_litellm(judge_model, system_prompt, user_content,
                                 litellm_url, api_key)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        print(f"ERROR: judge call failed — {e}", file=sys.stderr)
        return 2

    # Parse rulings from response
    escalated = len(re.findall(r"Decision:\s*ESCALATE", response, re.IGNORECASE))
    accepted = len(re.findall(r"Decision:\s*ACCEPT", response, re.IGNORECASE))
    dismissed = len(re.findall(r"Decision:\s*DISMISS", response, re.IGNORECASE))

    # Extract per-challenge confidence scores for calibration logging
    confidences = [
        float(m) for m in re.findall(r"Confidence:\s*([\d.]+)", response)
    ]

    # Build output
    mapping = {"Judge": judge_model}
    mapping.update(meta["mapping"])
    frontmatter = _build_frontmatter(debate_id, mapping)
    output_text = (
        f"{frontmatter}\n"
        f"# {debate_id} — Independent Judgment\n\n"
        f"Judge model: {judge_model} (non-author)\n"
        f"Challenger mapping: {meta['mapping']}\n\n"
        f"{response}\n"
    )

    with open(args.output, "w") as f:
        f.write(output_text)

    result = {
        "status": "ok",
        "judge": judge_model,
        "accepted": accepted,
        "dismissed": dismissed,
        "escalated": escalated,
        "needs_human": escalated > 0,
    }
    print(json.dumps(result))

    _log_debate_event({
        "phase": "judge",
        "debate_id": debate_id,
        "judge": judge_model,
        "challenger_count": len(meta.get("mapping", {})),
        "accepted": accepted,
        "dismissed": dismissed,
        "escalated": escalated,
        "needs_human": escalated > 0,
        "confidences": confidences,
        "mean_confidence": round(sum(confidences) / len(confidences), 3) if confidences else None,
        "output": args.output,
    })
    return 0


# ── Refinement prompts ──────────────────────────────────────────────────────

REFINE_FIRST_ROUND_PROMPT = """\
You are a collaborative document reviewer and improver. Your job is to make \
this document better — not to find fault, but to produce a stronger version.

Review the document for:
1. Clarity: Are claims precise and unambiguous?
2. Completeness: Are there gaps in reasoning or missing considerations?
3. Correctness: Are facts and logic sound?
4. Structure: Is the document well-organized and easy to follow?

{judgment_context}

Produce your output in EXACTLY this format:

## Review Notes
[Your observations — what's strong, what needs improvement, and why]

## Revised Document
[The COMPLETE revised document — not a diff, not a summary. \
Include every section, improved where needed, unchanged where already good.]"""

REFINE_SUBSEQUENT_ROUND_PROMPT = """\
You are a collaborative document reviewer and improver. A previous reviewer \
has already revised this document. Your job is to review their revision and \
produce an even better version.

Review the current revision for:
1. Did the previous reviewer introduce any errors or regressions?
2. Are there remaining clarity, completeness, or correctness issues?
3. Can the structure or flow be improved further?
4. Is anything over-explained or under-explained?

Produce your output in EXACTLY this format:

## Review Notes
[Your observations on the current revision — improvements made, remaining issues]

## Revised Document
[The COMPLETE revised document — not a diff, not a summary. \
Include every section, improved where needed, unchanged where already good.]"""

COMPARE_JUDGE_PROMPT = """\
You are an impartial judge comparing two review methods applied to the same \
original document. Score each method on five dimensions (1-5 scale):

1. **Accuracy**: Are the claims in the output correct? Did it introduce errors?
2. **Completeness**: Does it address all important aspects of the original?
3. **Constructiveness**: Does it improve the document, not just criticize?
4. **Efficiency**: Is the output focused, without unnecessary verbosity or tangents?
5. **Artifact Quality**: Is the final output a well-structured, usable document?

Output format:
## Scores

| Dimension | Method A | Method B |
|-----------|----------|----------|
| Accuracy | [1-5] | [1-5] |
| Completeness | [1-5] | [1-5] |
| Constructiveness | [1-5] | [1-5] |
| Efficiency | [1-5] | [1-5] |
| Artifact Quality | [1-5] | [1-5] |
| **Total** | [sum] | [sum] |

## Verdict
[METHOD_A / METHOD_B / TIE]

## Rationale
[2-4 sentences explaining what each method did well and where it fell short]"""


def _parse_refine_response(text):
    """Parse a refinement response into (notes, revised_document).

    Returns (notes, revised_doc). If parsing fails, returns (text, "").
    """
    notes_match = re.search(r"## Review Notes\s*\n(.*?)(?=## Revised Document)", text, re.DOTALL)
    doc_match = re.search(r"## Revised Document\s*\n(.*)", text, re.DOTALL)

    if notes_match and doc_match:
        return notes_match.group(1).strip(), doc_match.group(1).strip()
    return text.strip(), ""


def cmd_refine(args):
    """Iterative cross-model refinement: each model improves the document in turn."""
    api_key = os.environ.get("LITELLM_MASTER_KEY")
    if not api_key:
        print("ERROR: LITELLM_MASTER_KEY not set", file=sys.stderr)
        return 1

    litellm_url = os.environ.get("LITELLM_URL", DEFAULT_LITELLM_URL)
    config = _load_config()

    document = args.document.read()
    if not document.strip():
        print("ERROR: document file is empty", file=sys.stderr)
        return 1

    rounds = args.rounds
    models = args.models.split(",") if args.models else config["refine_rotation"]
    models = [m.strip() for m in models if m.strip()]

    # Load judgment context if provided
    judgment_context = ""
    if args.judgment:
        judgment_text = args.judgment.read()
        if judgment_text.strip():
            accepted = re.findall(
                r"### Challenge.*?\n.*?Decision:\s*ACCEPT.*?(?=### Challenge|\Z)",
                judgment_text, re.DOTALL
            )
            if accepted:
                judgment_context = (
                    "The following challenges were ACCEPTED by an independent judge "
                    "and MUST be addressed in your revision:\n\n"
                    + "\n\n".join(accepted)
                )

    # Derive debate_id from output filename
    debate_id = os.path.splitext(os.path.basename(args.output))[0]
    if debate_id.endswith("-refined"):
        debate_id = debate_id[:-8]

    current_doc = document
    round_notes = []

    for i in range(rounds):
        model = models[i % len(models)]
        round_num = i + 1

        if i == 0:
            prompt_template = REFINE_FIRST_ROUND_PROMPT
            ctx = judgment_context if judgment_context else "No specific issues flagged — use your judgment."
            system_prompt = prompt_template.format(judgment_context=ctx)
        else:
            system_prompt = REFINE_SUBSEQUENT_ROUND_PROMPT

        print(f"Refine round {round_num}/{rounds} ({model})...", file=sys.stderr)
        try:
            response = _call_litellm(model, system_prompt, current_doc, litellm_url, api_key)
            notes, revised = _parse_refine_response(response)
            round_notes.append({
                "round": round_num,
                "model": model,
                "notes": notes,
            })
            if revised:
                current_doc = revised
            else:
                print(f"WARNING: round {round_num} did not produce a revised document, "
                      "continuing with current version", file=sys.stderr)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            print(f"WARNING: round {round_num} ({model}) failed — {e}, "
                  "continuing with current version", file=sys.stderr)
            round_notes.append({
                "round": round_num,
                "model": model,
                "notes": f"[ERROR: {e}]",
            })

    # Build output
    now = datetime.now(timezone(timedelta(hours=-7)))
    sections = [
        "---",
        f"debate_id: {debate_id}",
        f"created: {now.strftime('%Y-%m-%dT%H:%M:%S%z')[:25]}",
        f"phase: refine",
        f"rounds: {rounds}",
        f"models: {', '.join(models)}",
        f"seeded_from_judgment: {'yes' if judgment_context else 'no'}",
        "---",
        f"# {debate_id} — Refined Document",
        "",
    ]

    for rn in round_notes:
        sections.append(f"## Round {rn['round']} ({rn['model']})")
        sections.append(rn["notes"])
        sections.append("")

    sections.append("## Final Refined Document")
    sections.append("")
    sections.append(current_doc)

    output_text = "\n".join(sections).rstrip() + "\n"

    with open(args.output, "w") as f:
        f.write(output_text)

    result = {
        "status": "ok",
        "rounds_completed": len(round_notes),
        "rounds_failed": sum(1 for rn in round_notes if rn["notes"].startswith("[ERROR:")),
        "models": models[:rounds],
    }
    print(json.dumps(result))

    _log_debate_event({
        "phase": "refine",
        "debate_id": debate_id,
        "rounds": rounds,
        "rounds_completed": len(round_notes),
        "models": models[:rounds],
        "seeded_from_judgment": bool(judgment_context),
        "output": args.output,
    })
    return 0


def cmd_review(args):
    """Single-model review for inline skill use (e.g., /define, /elevate)."""
    api_key = os.environ.get("LITELLM_MASTER_KEY")
    if not api_key:
        print("ERROR: LITELLM_MASTER_KEY not set", file=sys.stderr)
        return 1

    litellm_url = os.environ.get("LITELLM_URL", DEFAULT_LITELLM_URL)
    config = _load_config()

    # Resolve model from persona or explicit --model
    if args.persona:
        persona = args.persona.strip().lower()
        pmap = config["persona_model_map"]
        if persona not in pmap:
            print(f"ERROR: unknown persona '{persona}'. "
                  f"Valid: {', '.join(sorted(pmap))}",
                  file=sys.stderr)
            return 1
        model = pmap[persona]
    elif args.model:
        model = args.model
    else:
        print("ERROR: specify --persona or --model", file=sys.stderr)
        return 1

    # Load prompt
    if args.prompt:
        prompt = args.prompt
    elif args.prompt_file:
        prompt = args.prompt_file.read()
    else:
        print("ERROR: specify --prompt or --prompt-file", file=sys.stderr)
        return 1

    # Load input document
    input_text = args.input.read()
    if not input_text.strip():
        print("ERROR: input file is empty", file=sys.stderr)
        return 1

    print(f"Calling reviewer ({args.persona or 'explicit'})...", file=sys.stderr)
    try:
        response = _call_litellm(model, prompt, input_text, litellm_url, api_key)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        print(f"ERROR: review call failed — {e}", file=sys.stderr)
        return 1

    if not response or not response.strip():
        print("ERROR: model returned empty response", file=sys.stderr)
        return 1

    # Output with anonymous label — no model name
    print(f"## Reviewer\n\n{response}")

    _log_debate_event({
        "phase": "review",
        "persona": args.persona or None,
        "model": model,
        "input_file": args.input.name if hasattr(args.input, 'name') else "stdin",
        "success": True,
        "response_length": len(response),
    })
    return 0


def cmd_review_panel(args):
    """Multi-persona panel review: 3 models review independently, anonymous labels."""
    import random

    api_key = os.environ.get("LITELLM_MASTER_KEY")
    if not api_key:
        print("ERROR: LITELLM_MASTER_KEY not set", file=sys.stderr)
        return 1

    litellm_url = os.environ.get("LITELLM_URL", DEFAULT_LITELLM_URL)
    config = _load_config()

    personas = [p.strip().lower() for p in args.personas.split(",") if p.strip()]
    if not personas:
        print("ERROR: no personas specified", file=sys.stderr)
        return 1

    pmap = config["persona_model_map"]
    for p in personas:
        if p not in pmap:
            print(f"ERROR: unknown persona '{p}'. Valid: {', '.join(sorted(pmap))}",
                  file=sys.stderr)
            return 1

    # Load prompt
    if args.prompt:
        prompt = args.prompt
    elif args.prompt_file:
        prompt = args.prompt_file.read()
    else:
        print("ERROR: specify --prompt or --prompt-file", file=sys.stderr)
        return 1

    input_text = args.input.read()
    if not input_text.strip():
        print("ERROR: input file is empty", file=sys.stderr)
        return 1

    # Call each persona's model
    reviews = []  # list of (persona, model, response_or_error, success)
    for p in personas:
        model = pmap[p]
        print(f"Calling {p}...", file=sys.stderr)
        try:
            response = _call_litellm(model, prompt, input_text, litellm_url, api_key)
            if response and response.strip():
                reviews.append((p, model, response, True))
            else:
                reviews.append((p, model, "Empty response", False))
                print(f"WARNING: {p} returned empty response", file=sys.stderr)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            reviews.append((p, model, str(e), False))
            print(f"WARNING: {p} failed — {e}", file=sys.stderr)

    successful = [r for r in reviews if r[3]]
    if not successful:
        print("ERROR: all panel reviewers failed", file=sys.stderr)
        return 1

    # Position randomization (Zheng et al.) — shuffle before labeling
    random.shuffle(successful)

    # Output with anonymous labels — no model names
    for i, (persona, model, response, _) in enumerate(successful):
        label = CHALLENGER_LABELS[i]
        print(f"## Reviewer {label}\n\n{response}\n\n---\n")

    failed = [r for r in reviews if not r[3]]
    if failed:
        print(f"Note: {len(failed)} of {len(reviews)} reviewers failed.",
              file=sys.stderr)

    # Build mapping for audit (not visible in output)
    mapping = {}
    for i, (persona, model, _, _) in enumerate(successful):
        mapping[CHALLENGER_LABELS[i]] = model

    _log_debate_event({
        "phase": "review-panel",
        "personas": personas,
        "mapping": mapping,
        "successful": len(successful),
        "failed": len(failed),
        "input_file": args.input.name if hasattr(args.input, 'name') else "stdin",
    })

    # JSON status to stderr (stdout is the reviews)
    result = {
        "status": "ok" if not failed else "partial",
        "reviewers": len(successful),
        "mapping": mapping,
    }
    print(json.dumps(result), file=sys.stderr)
    return 0


def cmd_check_models(args):
    """Compare LiteLLM available models against config."""
    config = _load_config()
    litellm_url = os.environ.get("LITELLM_URL", DEFAULT_LITELLM_URL)
    api_key = os.environ.get("LITELLM_MASTER_KEY")

    if not api_key:
        print("ERROR: LITELLM_MASTER_KEY not set", file=sys.stderr)
        return 1

    # Fetch available models from LiteLLM
    url = f"{litellm_url.rstrip('/')}/models"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        body = json.loads(resp.read().decode())
        available = {m["id"] for m in body.get("data", [])}
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        print(f"ERROR: cannot reach LiteLLM at {url} — {e}", file=sys.stderr)
        return 1

    # Models referenced in config
    configured = set()
    for model in config["persona_model_map"].values():
        configured.add(model)
    configured.add(config["judge_default"])
    for model in config["refine_rotation"]:
        configured.add(model)
    configured.add(config["single_review_default"])

    # Report
    print(f"Config version: {config['version']}")
    print(f"\nConfigured models: {', '.join(sorted(configured))}")
    print(f"Available in LiteLLM: {', '.join(sorted(available))}")

    missing = configured - available
    if missing:
        print(f"\n⚠ Models in config but NOT in LiteLLM: {', '.join(sorted(missing))}")

    new_models = available - configured
    if new_models:
        print(f"\n→ New models in LiteLLM not in config: {', '.join(sorted(new_models))}")
        print("  Consider running 'debate.py benchmark' to evaluate new models.")
    else:
        print("\nAll available models are accounted for in config.")

    return 0


def cmd_compare(args):
    """Compare two review methods on the same original document."""
    api_key = os.environ.get("LITELLM_MASTER_KEY")
    if not api_key:
        print("ERROR: LITELLM_MASTER_KEY not set", file=sys.stderr)
        return 1

    litellm_url = os.environ.get("LITELLM_URL", DEFAULT_LITELLM_URL)

    original = args.original.read()
    method_a = args.method_a.read()
    method_b = args.method_b.read()

    if not original.strip() or not method_a.strip() or not method_b.strip():
        print("ERROR: all three input files must be non-empty", file=sys.stderr)
        return 1

    judge_model = args.model or "gemini-3.1-pro"

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
        response = _call_litellm(judge_model, COMPARE_JUDGE_PROMPT, user_content,
                                 litellm_url, api_key)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
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
    now = datetime.now(timezone(timedelta(hours=-7)))
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

    _log_debate_event({
        "phase": "compare",
        "debate_id": debate_id,
        "judge": judge_model,
        "verdict": verdict,
        "scores": scores,
        "output": args.output,
    })
    return 0


# ── CLI ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Cross-model adversarial review automation"
    )
    sub = parser.add_subparsers(dest="command")

    # challenge
    ch = sub.add_parser("challenge", help="Round 2: send proposal to challengers")
    ch.add_argument("--proposal", required=True, type=argparse.FileType("r"),
                     help="Path to proposal markdown file")
    ch.add_argument("--models", default=None,
                     help="Comma-separated LiteLLM model names")
    ch.add_argument("--personas", default=None,
                     help="Comma-separated persona names (architect,staff,security,pm). "
                          "Expands to models via PERSONA_MODEL_MAP. Alternative to --models.")
    ch.add_argument("--output", required=True,
                     help="Output path for anonymized challenge file")
    ch.add_argument("--system-prompt", type=argparse.FileType("r"), default=None,
                     help="Override default adversarial system prompt")

    # verdict
    vd = sub.add_parser("verdict", help="Round 4: final verdict from challengers")
    vd.add_argument("--resolution", required=True, type=argparse.FileType("r"),
                     help="Path to resolution markdown file")
    vd.add_argument("--challenge", required=True, type=argparse.FileType("r"),
                     help="Path to challenge file (with frontmatter mapping)")
    vd.add_argument("--output", required=True,
                     help="Output path for verdict file")
    vd.add_argument("--system-prompt", type=argparse.FileType("r"), default=None,
                     help="Override default verdict system prompt")

    # judge
    jg = sub.add_parser("judge", help="Independent judge: evaluate challenges without author bias")
    jg.add_argument("--proposal", required=True, type=argparse.FileType("r"),
                     help="Path to proposal markdown file")
    jg.add_argument("--challenge", required=True, type=argparse.FileType("r"),
                     help="Path to challenge file (with frontmatter mapping)")
    jg.add_argument("--model", default="gpt-5.4",
                     help="Judge model (default: gpt-5.4 — must differ from author)")
    jg.add_argument("--rebuttal", type=argparse.FileType("r"), default=None,
                     help="Optional author rebuttal brief (context only, author does not decide)")
    jg.add_argument("--output", required=True,
                     help="Output path for judgment file")
    jg.add_argument("--system-prompt", type=argparse.FileType("r"), default=None,
                     help="Override default judge system prompt")

    # refine
    rf = sub.add_parser("refine", help="Iterative cross-model refinement")
    rf.add_argument("--document", required=True, type=argparse.FileType("r"),
                     help="Path to document to refine")
    rf.add_argument("--rounds", type=int, default=6,
                     help="Number of refinement rounds (default: 6)")
    rf.add_argument("--models", default=None,
                     help="Comma-separated model rotation (default: gemini-3.1-pro,gpt-5.4,claude-opus-4-6)")
    rf.add_argument("--judgment", type=argparse.FileType("r"), default=None,
                     help="Path to judgment file — seeds first round with accepted challenges")
    rf.add_argument("--output", required=True,
                     help="Output path for refined document")

    # review (single-persona inline review)
    rv = sub.add_parser("review", help="Single-model review via persona")
    rv_model = rv.add_mutually_exclusive_group()
    rv_model.add_argument("--persona", default=None,
                          help="Persona name — resolved to model via config")
    rv_model.add_argument("--model", default=None,
                          help="Explicit model name (debug/admin only)")
    rv_prompt = rv.add_mutually_exclusive_group()
    rv_prompt.add_argument("--prompt", default=None,
                           help="Review prompt string")
    rv_prompt.add_argument("--prompt-file", type=argparse.FileType("r"), default=None,
                           help="File containing review prompt")
    rv.add_argument("--input", required=True, type=argparse.FileType("r"),
                    help="Document to review")

    # review-panel (multi-persona panel review)
    rp = sub.add_parser("review-panel", help="Multi-persona panel review")
    rp.add_argument("--personas", required=True,
                    help="Comma-separated persona names (e.g., architect,security,pm)")
    rp_prompt = rp.add_mutually_exclusive_group()
    rp_prompt.add_argument("--prompt", default=None,
                           help="Review prompt string")
    rp_prompt.add_argument("--prompt-file", type=argparse.FileType("r"), default=None,
                           help="File containing review prompt")
    rp.add_argument("--input", required=True, type=argparse.FileType("r"),
                    help="Document to review")

    # check-models
    sub.add_parser("check-models", help="Compare LiteLLM models against config")

    # compare
    cp = sub.add_parser("compare", help="Compare two review methods")
    cp.add_argument("--original", required=True, type=argparse.FileType("r"),
                     help="Path to original document")
    cp.add_argument("--method-a", required=True, type=argparse.FileType("r"),
                     help="Path to method A output")
    cp.add_argument("--method-b", required=True, type=argparse.FileType("r"),
                     help="Path to method B output")
    cp.add_argument("--model", default="gemini-3.1-pro",
                     help="Judge model (default: gemini-3.1-pro)")
    cp.add_argument("--output", required=True,
                     help="Output path for comparison file")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    if args.command == "challenge":
        return cmd_challenge(args)
    elif args.command == "verdict":
        return cmd_verdict(args)
    elif args.command == "judge":
        return cmd_judge(args)
    elif args.command == "refine":
        return cmd_refine(args)
    elif args.command == "review":
        return cmd_review(args)
    elif args.command == "review-panel":
        return cmd_review_panel(args)
    elif args.command == "check-models":
        return cmd_check_models(args)
    elif args.command == "compare":
        return cmd_compare(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
