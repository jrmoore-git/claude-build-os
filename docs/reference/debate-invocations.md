---
description: debate.py invocation patterns. Read before calling debate.py directly.
---

# debate.py — Invocation Reference

Common invocation patterns for `scripts/debate.py`. Read this before calling debate.py directly — do not guess at arguments.

All commands use: `/opt/homebrew/bin/python3.11 scripts/debate.py`

Global option: `--security-posture {1-5}` (before subcommand). Default 3.

## Challenge (3 challengers evaluate a proposal)

```bash
python3.11 scripts/debate.py challenge \
  --proposal tasks/<topic>-explore.md \
  --personas architect,staff,security \
  --output tasks/<topic>-challenge.md
```

- `--personas` expands to models via config. Alternative: `--models` with explicit LiteLLM model names.
- `--enable-tools` gives challengers read-only verifier tools.

## Judge (independent evaluation of challenges)

```bash
python3.11 scripts/debate.py judge \
  --proposal tasks/<topic>-explore.md \
  --challenge tasks/<topic>-challenge.md \
  --output tasks/<topic>-judgment.md
```

- `--model` overrides judge model (default: gpt-5.4 from config).
- `--rebuttal` adds optional author rebuttal as context.
- `--verify-claims` runs scoped claim verifier before judgment.
- `--no-consolidate` skips automatic challenge dedup/merge.

## Refine (iterative cross-model improvement, 6 rounds)

```bash
python3.11 scripts/debate.py refine \
  --document tasks/<topic>-explore.md \
  --judgment tasks/<topic>-judgment.md \
  --output tasks/<topic>-refined.md
```

- `--rounds N` overrides round count (default: 6).
- `--models` overrides rotation (default: gemini-3.1-pro,gpt-5.4,claude-opus-4-6).
- `--early-stop` stops when a round changes < 5% characters.
- `--judgment` is optional — seeds first round with accepted challenges.

## Full pipeline (challenge → judge → refine)

```bash
# Step 1: Challenge
python3.11 scripts/debate.py --security-posture 1 challenge \
  --proposal tasks/<topic>.md \
  --personas architect,staff,security \
  --output tasks/<topic>-challenge.md

# Step 2: Judge
python3.11 scripts/debate.py --security-posture 1 judge \
  --proposal tasks/<topic>.md \
  --challenge tasks/<topic>-challenge.md \
  --output tasks/<topic>-judgment.md

# Step 3: Refine
python3.11 scripts/debate.py refine \
  --document tasks/<topic>.md \
  --judgment tasks/<topic>-judgment.md \
  --output tasks/<topic>-refined.md
```

## Review (unified — single or multi-model)

The `review` command handles all review modes. Pass one of four mutually exclusive model-selection flags:

**Single persona** (code review — persona routes to model via config):
```bash
python3.11 scripts/debate.py review \
  --persona pm \
  --prompt "Review this plan for completeness" \
  --input tasks/<topic>-plan.md
```

**Single model** (no persona framing):
```bash
python3.11 scripts/debate.py review \
  --model gemini-3.1-pro \
  --prompt "Review this brief for implementability" \
  --input tasks/<topic>-brief.md
```

**Multiple personas** (parallel panel, anonymous labels):
```bash
python3.11 scripts/debate.py review \
  --personas architect,security,pm \
  --prompt "Review this diff for production readiness" \
  --input tasks/<topic>-diff.md
```

**Multiple models** (parallel panel, no persona framing):
```bash
python3.11 scripts/debate.py review \
  --models claude-opus-4-6,gemini-3.1-pro,gpt-5.4 \
  --prompt-file /tmp/eval-prompt.md \
  --input tasks/<topic>-doc.md
```

- `--persona`, `--personas`, `--model`, `--models` are mutually exclusive (exactly one required).
- `--models` bypasses persona lookup entirely — use for non-code evaluation where code-review personas are inappropriate.
- `--enable-tools` gives reviewers read-only verifier tools (works with all model-selection flags).
- `--prompt` and `--prompt-file` are mutually exclusive (exactly one required).
- Plural flags accept one or more items (`--models gemini-3.1-pro` is valid single-reviewer mode).
- `review-panel` is a deprecated alias — use `review` instead.

## Explore (divergent directions + synthesis)

```bash
python3.11 scripts/debate.py explore \
  --question "What are the options for X?" \
  --directions 4 \
  --context "additional market/tech context here" \
  --output tasks/<topic>-explore.md
```

## Pressure Test (counter-thesis or pre-mortem frame)

**Single-model** (default):
```bash
python3.11 scripts/debate.py pressure-test \
  --proposal tasks/<topic>.md \
  --frame challenge \
  --output tasks/<topic>-pressure-test.md
```

**Multi-model** (parallel execution + synthesis):
```bash
python3.11 scripts/debate.py pressure-test \
  --proposal tasks/<topic>.md \
  --models "claude-opus-4-6,gemini-3.1-pro,gpt-5.4" \
  --output tasks/<topic>-pressure-test.md
```

- `--model` and `--models` are mutually exclusive. `--models` requires at least 2 models.
- `--synthesis-model` overrides the model used for cross-analysis synthesis (default: `judge_default` from config). Should be from a different family than input models.
- `--frame premortem` for prospective failure analysis. Works with both `--model` and `--models`.
- Multi-model output includes individual analyses (anonymized A/B/C) + synthesis section identifying agreements, disagreements, and unique findings.

## Pre-Mortem (assume plan failed, write post-mortem)

```bash
python3.11 scripts/debate.py pre-mortem \
  --plan tasks/<topic>-plan.md \
  --output tasks/<topic>-premortem.md
```

## Check Models (verify config vs available)

```bash
python3.11 scripts/debate.py check-models
```

## Parallelism Rules (D13)

**Never use 3× serial `review --persona` calls when `review --personas` exists.** If you need 3 independent models to evaluate the same document, use `review --personas` or `review --models` (parallel via ThreadPoolExecutor). Using single-persona review 3 times serially costs 3× the wall-clock time for the same result.

**Persona simulations are embarrassingly parallel.** When running N persona simulations against a protocol, launch all N as parallel Agent calls (or parallel `review --personas`). Never run them serially.

**Stop on consensus.** When a cross-model evaluation loop reaches the target score (e.g., 3/3 models at 4/5), stop. Do not run additional rounds to chase edge-case improvements — the marginal value drops faster than the time cost rises.

**What's inherently serial:** `refine` rounds (output N = input N+1), triage between eval rounds (human judgment on real issue vs. model taste). Don't try to parallelize these.
