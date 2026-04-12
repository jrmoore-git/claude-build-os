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

## Review (single persona)

```bash
python3.11 scripts/debate.py review \
  --persona pm \
  --prompt "Review this plan for completeness" \
  --input tasks/<topic>-plan.md
```

- `--persona` options: architect, staff, security, pm.
- `--prompt-file` for longer prompts from a file.

## Review Panel (multi-persona, anonymous)

```bash
python3.11 scripts/debate.py review-panel \
  --personas architect,security,pm \
  --prompt "Review this diff for production readiness" \
  --input tasks/<topic>-diff.md
```

- `--enable-tools` gives reviewers read-only verifier tools.

## Explore (divergent directions + synthesis)

```bash
python3.11 scripts/debate.py explore \
  --question "What are the options for X?" \
  --directions 4 \
  --context "additional market/tech context here" \
  --output tasks/<topic>-explore.md
```

## Pressure Test (counter-thesis or pre-mortem frame)

```bash
python3.11 scripts/debate.py pressure-test \
  --proposal tasks/<topic>.md \
  --frame challenge \
  --output tasks/<topic>-pressure-test.md
```

- `--frame premortem` for prospective failure analysis.

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

**Never use 3× serial `review` calls when `review-panel` exists.** If you need 3 independent models to evaluate the same document, use `review-panel` (parallel via ThreadPoolExecutor). Using `review` 3 times serially costs 3× the wall-clock time for the same result.

**Persona simulations are embarrassingly parallel.** When running N persona simulations against a protocol, launch all N as parallel Agent calls (or parallel `review-panel` personas). Never run them serially.

**Stop on consensus.** When a cross-model evaluation loop reaches the target score (e.g., 3/3 models at 4/5), stop. Do not run additional rounds to chase edge-case improvements — the marginal value drops faster than the time cost rises.

**What's inherently serial:** `refine` rounds (output N = input N+1), triage between eval rounds (human judgment on real issue vs. model taste). Don't try to parallelize these.
