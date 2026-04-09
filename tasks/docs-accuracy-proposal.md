---
scope: "Accuracy review of docs/how-it-works.md, docs/hooks.md, and README.md pipeline tables"
author: claude-opus-4-6
---

# Documentation Accuracy Review

## Task for reviewers

Three documentation files describe the scripts, hooks, and skills in this repo. Your job is to verify every factual claim in the documentation against the source code provided below.

For each claim, check:
1. Are subcommand names, flags, and defaults correct?
2. Are "Used by" / "connects to" claims verifiable in the source?
3. Do behavior descriptions match the actual code paths?
4. Are file paths, model names, thresholds, and other constants correct?
5. Are there important behaviors in the source code that the docs omit?

Flag anything inaccurate as MATERIAL. Flag notable omissions as ADVISORY.

---

## DOCUMENTATION UNDER REVIEW

### File 1: docs/how-it-works.md

# How It Works

Technical internals for every script in the Build OS. Each script is a standalone CLI tool — pure stdlib Python, no pip dependencies — that powers part of the governance pipeline.

## debate.py

Cross-model adversarial review automation. This is the most important script: it orchestrates the full challenge → judge → refine pipeline by routing proposals through multiple AI models via a LiteLLM proxy.

The problem it solves: a single model reviewing its own work produces sycophantic reviews. debate.py sends proposals to different model families (GPT-5.4, Gemini 3.1 Pro, Claude Opus) with adversarial system prompts, then has an independent judge evaluate the challenges, and finally runs iterative cross-model refinement seeded by the judge's accepted findings.

### Subcommands

**challenge** — Send a proposal to challenger models for adversarial review. Each challenger receives the proposal (with author metadata redacted) and a role-specific adversarial prompt. Challengers must tag each finding with a type (RISK, ASSUMPTION, ALTERNATIVE, OVER-ENGINEERED, UNDER-ENGINEERED) and a materiality label (MATERIAL or ADVISORY).

```
python3 scripts/debate.py challenge \
    --proposal tasks/auth-redesign-proposal.md \
    --personas architect,security,pm \
    --output tasks/auth-redesign-challenge.md
```

Personas map to models: architect → gpt-5.4, staff → gemini-3.1-pro, security → gpt-5.4, pm → gemini-3.1-pro. Each persona gets a role-specific adversarial prompt (architecture concerns, security focus, operational feasibility, or user value). Note that personas sharing a model are deduplicated — `--personas architect,security` produces one challenger since both map to gpt-5.4. Alternatively, pass `--models gpt-5.4,gemini-3.1-pro` directly with a generic adversarial prompt. An optional `--system-prompt` flag (takes a file path) overrides the default prompt entirely.

Produces: `tasks/<topic>-challenge.md` with YAML frontmatter containing `debate_id`, `created` timestamp, and a `mapping` of challenger labels (A, B, C...) to model names. Also prints a JSON status object to stdout with `status`, `challengers` count, `mapping`, and any `warnings`.

**judge** — Independent evaluation of challenges by a non-author model. The judge receives the proposal and challenges (with challenger sections shuffled to eliminate position bias), then issues ACCEPT, DISMISS, or ESCALATE on each MATERIAL challenge with a confidence score (0.0–1.0).

```
python3 scripts/debate.py judge \
    --proposal tasks/auth-redesign-proposal.md \
    --challenge tasks/auth-redesign-challenge.md \
    --output tasks/auth-redesign-judgment.md
```

Default judge model: gpt-5.4 (chosen because a different model family avoids self-preference bias when the author is Claude). The judge warns if it matches the author model. An optional `--rebuttal` flag passes author context without giving the author decision authority. `--system-prompt` (file path) overrides the default judge prompt.

Produces: `tasks/<topic>-judgment.md` with accepted/dismissed/escalated counts. Findings marked ESCALATE require human review. Prints JSON to stdout with `accepted`, `dismissed`, `escalated` counts and `needs_human` flag.

**refine** — Iterative cross-model document improvement. Each round, a different model reviews and rewrites the document. The first round is seeded with accepted challenges from the judgment file so models know exactly what to fix.

```
python3 scripts/debate.py refine \
    --document tasks/auth-redesign-proposal.md \
    --judgment tasks/auth-redesign-judgment.md \
    --rounds 3 \
    --output tasks/auth-redesign-refined.md
```

Default model rotation: gemini-3.1-pro → gpt-5.4 → claude-opus-4-6 (cycles if rounds exceed model count). Default rounds: 6. Each round produces review notes and a complete revised document; the revised document feeds into the next round.

Produces: `tasks/<topic>-refined.md` with per-round review notes and the final refined document.

**compare** — Score two review methods against the same original document on five dimensions (accuracy, completeness, constructiveness, efficiency, artifact quality). Useful for evaluating whether the full pipeline outperforms simpler review approaches.

```
python3 scripts/debate.py compare \
    --original tasks/auth-redesign-proposal.md \
    --method-a tasks/auth-redesign-challenge.md \
    --method-b tasks/auth-redesign-refined.md \
    --output tasks/auth-redesign-compare.md
```

Default judge: gemini-3.1-pro. Produces a scorecard with METHOD_A / METHOD_B / TIE verdict.

**verdict** (legacy) — Sends a resolution back to the original challengers for a final APPROVE / REVISE / REJECT. This was the original pipeline's final step before the judge subcommand replaced it. Still functional but the standard pipeline now uses judge + refine instead.

```
python3 scripts/debate.py verdict \
    --resolution tasks/auth-redesign-resolution.md \
    --challenge tasks/auth-redesign-challenge.md \
    --output tasks/auth-redesign-verdict.md
```

### The standard pipeline

The recommended three-step pipeline:

1. `challenge` — adversarial models find issues
2. `judge` — independent model evaluates which issues are real
3. `refine` — collaborative models fix accepted issues and improve the document

All events are logged to `stores/debate-log.jsonl` (append-only JSONL with timestamps, phase, model mapping, and counts).

### Connection to LiteLLM

All API calls go through LiteLLM at `LITELLM_URL` (default: `http://localhost:4000`), authenticated with `LITELLM_MASTER_KEY`. Both are read from environment variables (or `.env` in the project root). This means any model LiteLLM can route to is available to the debate pipeline — no direct API keys needed per provider.


## tier_classify.py

Deterministic review tier classifier. Given a list of file paths, it classifies each file into a review tier based on regex pattern matching against the path.

The problem it solves: commit-time hooks need to know whether staged files require a full cross-model debate (Tier 1), a quality review (Tier 1.5), or just a log entry (Tier 2). This script makes that classification deterministic and consistent.

### Tiers

- **Tier 1 (Cross-model debate):** PRD files, database schema/migrations, security rules, direct `.db` edits
- **Tier 1.5 (Quality review):** Core skill SKILL.md files (requires populating `CORE_SKILLS` in the script — empty by default), toolbelt scripts (`*_tool.py`), debate.py itself, hook scripts
- **Tier 2 (Log only):** Everything else
- **Exempt:** `tasks/`, `docs/` (non-PRD), `tests/`, `config/`, `stores/` (non-db)

### Usage

```
# Classify specific files
python3 scripts/tier_classify.py scripts/debate.py docs/project-prd.md

# Classify files from git diff
python3 scripts/tier_classify.py --diff-base main

# Classify from stdin (one path per line)
echo "scripts/debate.py" | python3 scripts/tier_classify.py --stdin
```

### Output

JSON to stdout. The overall tier is the strictest tier among all non-exempt files:

```json
{
  "tier": 1.5,
  "tier_label": "Tier 1.5 — Quality review",
  "reason": "scripts/debate.py -> debate tooling",
  "files": {
    "scripts/debate.py": {"tier": 1.5, "reason": "debate tooling"},
    "tasks/decisions.md": {"tier": "exempt", "reason": "exempt path"}
  },
  "ambiguous": false
}
```

The `ambiguous` flag is true when multiple different non-exempt tiers are present in the same commit.

### Used by

`hook-review-gate.sh` and `hook-tier-gate.sh` both call this script to determine whether to block, warn, or allow.


## recall_search.py

BM25 + semantic hybrid search across governance files. Surfaces relevant prior context (lessons, decisions, session notes, current state) given a search query.

The problem it solves: governance files grow over time. Manually scanning 80+ lessons or 50+ decisions for relevant entries is slow. This script makes prior context searchable so `/recall` and other skills can load only what matters.

### Search modes

**BM25 (default):** Pure-stdlib keyword search with TF-IDF scoring. No dependencies, no external services. Parses each governance file into discrete documents (individual lessons, decisions, session entries) and ranks by relevance.

**Semantic (`--semantic`):** Generates embeddings via a local Ollama instance (nomic-embed-text model) and computes cosine similarity against pre-indexed chunks in `stores/context.db`. Requires Ollama running locally and a pre-built embeddings database. Threshold: 0.5 (chunks below this similarity are excluded).

### Source files

| Key | File | Parser |
|-----|------|--------|
| lessons | tasks/lessons.md | Rows from the markdown table (L1, L2, ...) |
| decisions | tasks/decisions.md | Sections starting with `### D1:`, `### D2:`, ... |
| sessions | tasks/session-log.md | Blocks separated by `---` |
| current | docs/current-state.md | Entire file as one document |

### Usage

```
# BM25 search across all files
python3 scripts/recall_search.py oauth token refresh

# Search only lessons and decisions
python3 scripts/recall_search.py --files lessons,decisions sqlite timeout

# Semantic search (requires Ollama)
python3 scripts/recall_search.py --semantic "database migration failures"

# JSON output for programmatic use
python3 scripts/recall_search.py --json --top-k 3 hook gate bypass
```

### Flags

- `--files` — Comma-separated source filter: `lessons`, `decisions`, `sessions`, `current`, or `all` (default: `all`)
- `--tags` — Search frontmatter tags only (lessons table only, BM25 mode only)
- `--semantic` — Use Ollama semantic search instead of BM25
- `--json` — Output results as a JSON array (BM25 mode only — semantic mode always outputs formatted text)
- `--top-k` — Max results to return (default: 5, BM25 mode only — semantic mode uses its own default of 5)

### Used by

`enrich_context.py` calls this script with `--json` to pull relevant lessons and decisions into debate proposals.


## finding_tracker.py

Per-finding state machine for debate findings. Tracks individual findings through their lifecycle: open → addressed | waived | obsolete.

The problem it solves: a judgment file may accept 5 challenges. After fixing 3, you need to know which 2 remain open. This script provides that tracking without manual bookkeeping.

### Data model

Store: `stores/findings.jsonl` (append-only, last-write-wins per `finding_id`).

Each finding has:
- `finding_id` — `{debate_id}:{challenge_num}` (e.g., `auth-redesign:3`)
- `debate_id` — Links back to the debate topic
- `state` — `open`, `addressed`, `waived`, or `obsolete`
- `state_history` — Timestamped log of all state transitions
- `summary`, `decision`, `confidence` — Imported from the judgment file

Valid transitions: open → addressed, open → waived, open → obsolete. No other transitions are allowed.

### Subcommands

**import** — Parse a judgment file and import all ACCEPT findings as open.

```
python3 scripts/finding_tracker.py import \
    --judgment tasks/auth-redesign-judgment.md
```

Idempotent: already-imported findings are skipped.

**list** — List findings for a debate, optionally filtered by state.

```
python3 scripts/finding_tracker.py list --debate-id auth-redesign
python3 scripts/finding_tracker.py list --debate-id auth-redesign --state open
```

**transition** — Move a finding to a new state.

```
python3 scripts/finding_tracker.py transition \
    --finding-id auth-redesign:3 \
    --to addressed \
    --reason "Fixed in commit abc123"
```

**summary** — Counts by state for a debate.

```
python3 scripts/finding_tracker.py summary --debate-id auth-redesign
```

Output: `{"debate_id": "auth-redesign", "open": 2, "addressed": 3, "waived": 0, "obsolete": 0}`

### Used by

`artifact_check.py` calls the summary subcommand to count open findings when checking artifact integrity.


## enrich_context.py

Enriches debate proposals with relevant prior context before sending to challengers. Extracts keywords from the proposal's title, scope, and first paragraph, then searches governance files for related lessons and decisions.

The problem it solves: challengers reviewing a proposal in isolation may miss relevant prior decisions or known gotchas. This script automatically surfaces that context so challenges are informed by project history.

### How it connects

Sits between proposal authoring and the challenge step. The enrichment output (JSON with keywords, matching lessons, and matching decisions) can be appended to the proposal or passed as additional context to challengers.

### Usage

```
python3 scripts/enrich_context.py \
    --proposal tasks/auth-redesign-proposal.md \
    --top-k 5
```

### Output

JSON to stdout:

```json
{
  "keywords": ["oauth", "token", "refresh", "gateway"],
  "lessons": [
    {"source": "tasks/lessons.md", "line": 42, "id": "L38", "score": 2.15,
     "text": "gog keyring file backend fails without TTY..."}
  ],
  "decisions": [
    {"source": "tasks/decisions.md", "line": 89, "id": "D12", "score": 1.87,
     "text": "External updates require four-persona review..."}
  ]
}
```

Keyword extraction: up to 8 keywords from frontmatter `scope:` field, first heading, and first body paragraph, with stopword removal.

### Used by

Standalone CLI tool. Run manually before `debate.py challenge` to surface relevant prior context for challengers. Calls `recall_search.py` internally with `--json` output. Note: `debate.py` does not call this script automatically — you run it yourself and append its output to the proposal or pass it as additional context.


## artifact_check.py

Artifact integrity and staleness checker. Given a topic name, checks whether plan, challenge, judgment, and review artifacts exist, are valid, and are current relative to the source files.

The problem it solves: hooks need to know whether a valid, non-stale plan or review artifact exists before allowing a commit. This script centralizes that check.

### What it checks

For each artifact type:
- **Existence** — Does the file exist at `tasks/<scope>-{plan,challenge,judgment,review}.md`?
- **Staleness** — Is the artifact older than the newest file changed since `--base` ref?
- **Validity** — Type-specific checks:
  - **plan**: Has at least one of the expected frontmatter fields (`scope`, `review_tier`)
  - **challenge**: Has YAML frontmatter with `debate_id` and contains `MATERIAL` tag
  - **judgment**: Counts of ACCEPT, DISMISS, ESCALATE decisions
  - **review**: Reads `status` and `review_tier` from frontmatter

Also counts open material findings by calling `finding_tracker.py summary` if `stores/findings.jsonl` exists, falling back to counting ACCEPT lines in the judgment file.

### Usage

```
python3 scripts/artifact_check.py --scope auth-redesign
python3 scripts/artifact_check.py --scope auth-redesign --base main
```

### Output

JSON to stdout:

```json
{
  "scope": "auth-redesign",
  "git_head": "a1b2c3d",
  "artifacts": {
    "plan": {"path": "tasks/auth-redesign-plan.md", "exists": true, "stale": false, "valid": true},
    "challenge": {"path": "tasks/auth-redesign-challenge.md", "exists": true, "stale": false, "valid": true, "has_material": true},
    "judgment": {"path": "tasks/auth-redesign-judgment.md", "exists": true, "stale": false, "accepted": 3, "dismissed": 2, "escalated": 0},
    "review": {"path": "tasks/auth-redesign-review.md", "exists": false}
  },
  "open_material_findings": 1
}
```

### Used by

Standalone CLI tool. The hooks replicate similar validation logic inline rather than calling this script directly. Use `artifact_check.py` for manual pre-commit checks or in CI pipelines.

---

### File 2: docs/hooks.md

# Hooks Reference

The Build OS ships three enforcement hooks. Each is a shell script that fires as a Claude Code PreToolUse hook — it runs before the tool executes, and can block or warn based on what it finds.

Hooks are the third level of the enforcement ladder: advisory (CLAUDE.md) → rules (.claude/rules/) → **hooks** → architecture. They fire every time, cannot be ignored by the model, and enforce governance as deterministic code.


## hook-plan-gate.sh

Gates commits to protected paths without a valid plan artifact.

**When it fires:** PreToolUse, on `git commit` commands. Only activates when staged files match protected globs from `config/protected-paths.json`.

**What it checks:**

1. Are any staged files in a protected path (and not in an exempt path)?
2. If yes, does a valid plan artifact exist in `tasks/`?

Protected paths (from `config/protected-paths.json`):
- `skills/**/*.md`
- `scripts/*_tool.py`
- `scripts/*_pipeline.py`
- `.claude/rules/*.md`

Exempt paths (always pass regardless of other rules):
- `tasks/*`
- `docs/*`
- `tests/*`
- `config/*`
- `stores/*`

**Pass conditions:**
- No staged files match protected globs (after excluding exempt paths)
- A valid plan artifact exists: any `tasks/*-plan.md` file with YAML frontmatter containing all required fields AND `verification_evidence` is not `PENDING`
- Commit message contains `[EMERGENCY]` (bypass with audit warning to stderr)
- Config file `config/protected-paths.json` is missing (fail-open)

**Block conditions:**
- Staged files hit a protected glob, no valid plan artifact exists, and no `[EMERGENCY]` bypass
- Commit message contains `[TRIVIAL]` on protected paths (always blocked — `[TRIVIAL]` is not allowed for protected paths)

**Required plan artifact frontmatter:**

```yaml
---
scope: "What this change does"
surfaces_affected: "What systems/files are touched"
verification_commands: "How to verify correctness"
rollback: "How to undo"
review_tier: "Tier 1|Tier 1.5|Tier 2"
verification_evidence: "Results of verification (must not be PENDING)"
---
```

The `verification_evidence` field is the key gate: it must contain actual evidence, not the placeholder value `PENDING`. This forces verification to happen before the commit, not after.

**Bypass:** `[EMERGENCY]` in the commit message skips the gate with a stderr warning. This is logged and audited in weekly review. `[TRIVIAL]` is explicitly blocked on protected paths.


## hook-review-gate.sh

Gates commits to high-risk files without valid debate artifacts.

**When it fires:** PreToolUse, on `git commit` commands.

**What it checks:**

1. Classifies all staged files via `tier_classify.py`
2. For Tier 1 files: requires debate artifacts (challenge, resolution, or review file) newer than the staged files
3. For advisory-level files (Tier 1.5 or risk-flagged Tier 2): warns but does not block

**Pass conditions:**
- All staged files classify as Tier 2 or exempt
- Commit message contains `[TRIVIAL]` (bypass with notice — allowed here, unlike plan-gate)
- A valid debate artifact exists in `tasks/` that is newer than the staged files:
  - `*-challenge.md` with YAML frontmatter (`debate_id:`), `MATERIAL` tag, and a verdict line (APPROVE/REVISE/REJECT)
  - `*-resolution.md` with a `## PM/UX Assessment` section
  - `*-review.md` (legacy compatibility — presence is sufficient)

**Block conditions:**
- Tier 1 files staged without any valid debate artifact newer than the staged files

**Advisory (non-blocking):**
- Tier 1.5 or risk-flagged Tier 2 files (matching `skill`, `_tool.py`, `.claude/rules/`, `hook-`, or `security` in the path) staged without debate artifacts → prints a notice suggesting a decision log entry

Note: `[EMERGENCY]` bypass is only available in hook-plan-gate. Neither hook-review-gate nor hook-tier-gate support it.


## hook-tier-gate.sh

Classifies file tier before the first edit and gates accordingly.

**When it fires:** PreToolUse, on `Write` or `Edit` tool calls. Unlike the other two hooks (which fire on `git commit`), this one fires before file edits.

**What it checks:**

1. Extracts the `file_path` from the tool input
2. Classifies it via `tier_classify.py`
3. For Tier 1 files: checks whether a debate artifact (challenge or judgment file) exists in `tasks/` that is newer than the current session start
4. For Tier 1.5 files: issues an advisory warning

**Session dedup:** Uses a marker file in `/tmp/build-os-tier-gate/` to avoid re-firing on every single edit. Once a tier has been classified and cleared (or warned) for a session, the gate passes for 4 hours.

**Pass conditions:**
- File classifies as Tier 2 or exempt
- Tier already cleared in this session (marker file exists and is less than 4 hours old)
- Tier 1: a valid debate artifact exists that is newer than the session start
  - `*-challenge.md` with YAML frontmatter (`debate_id:`) and MATERIAL tag (no verdict line required — less strict than review-gate)
  - `*-judgment.md` or `*-resolution.md` (presence is sufficient)

**Block conditions:**
- Tier 1 file edit attempted without any valid debate artifact from the current session. Block message includes the exact `debate.py challenge` command to run.

**Advisory (non-blocking):**
- Tier 1.5 file edit → prints a notice suggesting a quality review, then allows the edit


## Wiring hooks into your project

Add hooks to `.claude/settings.json` (or `.claude/settings.local.json` for personal, non-committed settings). Each hook needs a matcher pattern and the script path.

### All three hooks

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "bash hooks/hook-plan-gate.sh"
      },
      {
        "matcher": "Bash",
        "command": "bash hooks/hook-review-gate.sh"
      },
      {
        "matcher": "Write|Edit",
        "command": "bash hooks/hook-tier-gate.sh"
      }
    ]
  }
}
```

### Plan gate only (recommended starting point)

If you only want one hook, start with the plan gate. It enforces the highest-value discipline (plan before code on protected paths) with the lowest friction.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "bash hooks/hook-plan-gate.sh"
      }
    ]
  }
}
```

### Configuration

The plan gate reads its protected paths, exempt patterns, and required frontmatter fields from `config/protected-paths.json`. Edit that file to customize what's protected in your project:

```json
{
  "protected_globs": [
    "skills/**/*.md",
    "scripts/*_tool.py",
    "scripts/*_pipeline.py",
    ".claude/rules/*.md"
  ],
  "exempt_patterns": [
    "tasks/*",
    "docs/*",
    "tests/*",
    "config/*",
    "stores/*"
  ],
  "required_plan_fields": [
    "scope",
    "surfaces_affected",
    "verification_commands",
    "rollback",
    "review_tier"
  ]
}
```

The review gate and tier gate use `tier_classify.py` for classification. To customize which files trigger which tier, edit the pattern lists at the top of `scripts/tier_classify.py`.

---

### File 3: README.md (pipeline and under-the-hood tables only)


---

## SOURCE CODE (verify documentation claims against this)

### scripts/debate.py (argparse section + constants)

#!/usr/bin/env python3
"""
debate.py — Cross-model adversarial review automation.

Subcommands:
    challenge   Send proposal to challenger models for adversarial review
    judge       Independent judgment: non-author model evaluates challenges
    refine      Iterative cross-model refinement (guided by judgment)
    compare     Compare two review methods on the same document
    verdict     Send resolution back to challengers for final verdict (legacy)

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

[... system prompts omitted for brevity ...]

PERSONA_MODEL_MAP = {
    "architect": "gpt-5.4",
    "staff": "gemini-3.1-pro",
    "security": "gpt-5.4",
    "pm": "gemini-3.1-pro",
}

DEFAULT_REFINE_MODELS = ["gemini-3.1-pro", "gpt-5.4", "claude-opus-4-6"]

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
                     help="Comma-separated persona names (architect,staff,security). "
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
    elif args.command == "compare":
        return cmd_compare(args)
    return 1


if __name__ == "__main__":

### scripts/tier_classify.py (full)

#!/usr/bin/env python3
"""
tier_classify.py — Deterministic review tier classifier.

Consolidates tier logic for commit-time review gates.

Usage:
    python3 scripts/tier_classify.py [file1 file2 ...]
    python3 scripts/tier_classify.py --stdin
    python3 scripts/tier_classify.py --diff-base main
"""
import argparse
import json
import os
import re
import subprocess
import sys


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

# ── Tier 1: Architecture docs, database schema, security rules ──────────
# Customize: add your project's trust-boundary files here.
TIER1_PATTERNS = [
    r"^docs/.*PRD",           # product requirements docs
    r"^docs/project-prd\.md$",
    r"schema.*\.sql$",        # database schema
    r"migration.*\.sql$",     # database migrations
    r"^\.claude/rules/security\.md$",
    r"^stores/.*\.db$",       # direct DB file edits
]

# ── Tier 1.5: core skills, toolbelt scripts, hooks ──────────────────────
# Customize: list your project's core skill names.
CORE_SKILLS = ""  # e.g., "auth-flow|data-pipeline|notifications"

TIER15_PATTERNS = [
    *(
        [rf"^skills/({CORE_SKILLS})/SKILL\.md$"]
        if CORE_SKILLS else []
    ),
    r"^scripts/[a-z]+_tool\.py$",  # toolbelt scripts
    r"^scripts/debate\.py$",       # debate engine
    r"^scripts/hook-.*\.sh$",      # hook scripts
]

# ── Exempt paths ─────────────────────────────────────────────────────────
EXEMPT_PATTERNS = [
    r"^tasks/",
    r"^docs/(?!.*PRD|project-prd\.md)",
    r"^tests/",
    r"^config/",
    r"^stores/(?!.*\.db$)",
]


def classify_file(rel_path):
    """Classify a single file. Returns (tier, reason)."""
    for pat in EXEMPT_PATTERNS:
        if re.search(pat, rel_path):
            return "exempt", "exempt path"

    for pat in TIER1_PATTERNS:
        if re.search(pat, rel_path):
            if "PRD" in rel_path or "project-prd" in rel_path:
                return 1, "PRD change"
            if re.search(r"schema|migration", rel_path):
                return 1, "database schema"
            if "security.md" in rel_path:
                return 1, "security rules"
            if rel_path.endswith(".db"):
                return 1, "direct DB file edit"
            return 1, "trust boundary"

    for pat in TIER15_PATTERNS:
        if re.search(pat, rel_path):
            if "SKILL.md" in rel_path:
                return 1.5, "core skill"
            if "_tool.py" in rel_path:
                return 1.5, "toolbelt script"
            if "debate.py" in rel_path:
                return 1.5, "debate tooling"
            if "hook-" in rel_path:
                return 1.5, "hook script"
            return 1.5, "core infrastructure"

    return 2, "standard change"


def normalize_path(path):
    """Normalize to relative path from project root."""
    path = path.strip()
    if path.startswith(PROJECT_ROOT + "/"):
        path = path[len(PROJECT_ROOT) + 1:]
    if path.startswith("./"):
        path = path[2:]
    return path


def main():
    parser = argparse.ArgumentParser(description="Classify review tier for files")
    parser.add_argument("files", nargs="*", help="File paths to classify")
    parser.add_argument("--stdin", action="store_true",
                        help="Read newline-separated paths from stdin")
    parser.add_argument("--diff-base", metavar="REF",
                        help="Use git diff REF..HEAD for file list")
    args = parser.parse_args()

    paths = []

    if args.diff_base:
        result = subprocess.run(
            ["git", "-C", PROJECT_ROOT, "diff", "--name-only",
             f"{args.diff_base}..HEAD"],
            capture_output=True, text=True,
        )
        paths = [p.strip() for p in result.stdout.splitlines() if p.strip()]

    if args.stdin:
        paths.extend(p.strip() for p in sys.stdin if p.strip())

    if args.files:
        paths.extend(args.files)

    if not paths:
        print("ERROR: no files provided", file=sys.stderr)
        sys.exit(1)

    # Severity ordering: lower number = stricter review. 1 > 1.5 > 2.
    def severity(tier):
        """Map tier to severity rank (lower = stricter)."""
        if tier == "exempt":
            return 999
        return tier  # 1, 1.5, 2 — natural ordering works

    files = {}
    strictest_tier = None
    strictest_reason = ""

    for raw_path in paths:
        rel = normalize_path(raw_path)
        tier, reason = classify_file(rel)
        files[rel] = {"tier": tier, "reason": reason}

        if tier == "exempt":
            continue

        if strictest_tier is None or severity(tier) < severity(strictest_tier):
            strictest_tier = tier
            strictest_reason = f"{rel} -> {reason}"

    # If all exempt, overall tier is exempt
    if strictest_tier is None:
        overall_tier = "exempt"
        tier_label = "Exempt — no review needed"
    else:
        overall_tier = strictest_tier

        labels = {
            1: "Tier 1 — Cross-model debate",
            1.5: "Tier 1.5 — Quality review",
            2: "Tier 2 — Log only",
        }
        tier_label = labels.get(overall_tier, f"Tier {overall_tier}")

    # Ambiguous: multiple different non-exempt tiers present
    tiers_present = {f["tier"] for f in files.values() if f["tier"] != "exempt"}
    ambiguous = len(tiers_present) > 1

    output = {
        "tier": overall_tier,
        "tier_label": tier_label,
        "reason": strictest_reason,
        "files": files,
        "ambiguous": ambiguous,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

### scripts/recall_search.py (full)

#!/usr/bin/env python3
"""BM25 + semantic recall search across governance files. Pure stdlib, no pip."""
import argparse, json, math, re, sqlite3, sys, urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {"lessons": ROOT / "tasks/lessons.md", "decisions": ROOT / "tasks/decisions.md",
           "sessions": ROOT / "tasks/session-log.md", "current": ROOT / "docs/current-state.md"}

def tokenize(text): return re.findall(r"[a-z0-9_]+", text.lower())

def parse_lessons(text, tags_only=False):
    docs = []
    for m in re.finditer(r"^\| (L\d+) \| .+\|$", text, re.M):
        row = m.group(0)
        if tags_only: row = row.split("|")[-2].strip() if row.count("|") >= 7 else ""
        docs.append(("tasks/lessons.md", text[:m.start()].count("\n") + 1, m.group(1), row))
    return docs

def parse_decisions(text, tags_only=False):
    return [("tasks/decisions.md", text[:m.start()].count("\n") + 1, m.group(1),
             "" if tags_only else m.group(0))
            for m in re.finditer(r"^### (D\d+):.+?(?=\n### D\d+:|\Z)", text, re.M | re.S)]

def parse_sessions(text, tags_only=False):
    if tags_only: return []
    docs, offset = [], 0
    for entry in text.split("\n---\n"):
        label = re.search(r"^## (.+)", entry, re.M)
        docs.append(("tasks/session-log.md", text[:offset].count("\n") + 1 if offset else 1,
                     label.group(1)[:40] if label else "session", entry))
        offset += len(entry) + 5
    return docs

def parse_current(text, tags_only=False):
    return [] if tags_only else [("docs/current-state.md", 1, "current-state", text)]

PARSERS = {"lessons": parse_lessons, "decisions": parse_decisions,
           "sessions": parse_sessions, "current": parse_current}

def bm25(query_tokens, docs, k1=1.5, b=0.75):
    N = len(docs)
    if N == 0: return []
    doc_tokens = [tokenize(d[3]) for d in docs]
    avgdl = sum(len(t) for t in doc_tokens) / N
    df = Counter()
    for toks in doc_tokens:
        for t in set(toks): df[t] += 1
    scores = []
    for i, toks in enumerate(doc_tokens):
        tf, dl, score = Counter(toks), len(toks), 0.0
        for qt in query_tokens:
            if qt not in tf: continue
            idf = math.log((N - df[qt] + 0.5) / (df[qt] + 0.5) + 1)
            score += idf * tf[qt] * (k1 + 1) / (tf[qt] + k1 * (1 - b + b * dl / avgdl))
        if score > 0: scores.append((score, i))
    scores.sort(reverse=True)
    return scores

def semantic_search(query, file_filter=None, top_k=5, threshold=0.5):
    db_path = ROOT / "stores" / "context.db"
    if not db_path.exists():
        print("No embeddings DB found. Run: python3 scripts/embed_governance.py"); return
    body = json.dumps({"model": "nomic-embed-text", "prompt": query[:8000]}).encode()
    try:
        req = urllib.request.Request("http://localhost:11434/api/embeddings", data=body,
                                    headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            q_vec = json.loads(resp.read())["embedding"]
    except Exception as e:
        print(f"Ollama unavailable ({e}). Re-run without --semantic for BM25 results."); return
    conn = sqlite3.connect(str(db_path), timeout=5)
    conn.execute("PRAGMA busy_timeout = 5000")
    query_sql = "SELECT source_file, chunk_id, chunk_text, embedding FROM recall_embeddings"
    params = []
    if file_filter:
        placeholders = ",".join("?" * len(file_filter))
        query_sql += f" WHERE source_file IN ({placeholders})"
        params = list(file_filter)
    rows = conn.execute(query_sql, params).fetchall()
    conn.close()
    results = []
    for src, cid, text, emb_blob in rows:
        d_vec = json.loads(emb_blob)
        dot = sum(a * b for a, b in zip(q_vec, d_vec))
        mag_q = math.sqrt(sum(a * a for a in q_vec))
        mag_d = math.sqrt(sum(b * b for b in d_vec))
        sim = dot / (mag_q * mag_d) if mag_q and mag_d else 0.0
        if sim >= threshold:
            results.append((sim, src, cid, text))
    results.sort(reverse=True)
    if not results:
        print(f"No semantic matches found for: {query}"); sys.exit(0)
    for sim, src, cid, text in results[:top_k]:
        print(f"  {src}  [{cid}]  similarity={sim:.3f}")
        print(f"    {' '.join(text.split())[:120]}\n")

def main():
    p = argparse.ArgumentParser(description="BM25 + semantic search across governance files")
    p.add_argument("terms", nargs="+")
    p.add_argument("--tags", action="store_true", help="Search frontmatter tags only")
    p.add_argument("--semantic", action="store_true", help="Use Ollama semantic search")
    p.add_argument("--files", default="all", help="Comma-separated: lessons,decisions,sessions,current,all")
    p.add_argument("--json", action="store_true", help="Output results as JSON array")
    p.add_argument("--top-k", type=int, default=5, help="Max results to return")
    args = p.parse_args()
    if args.semantic:
        file_map = {"lessons": "tasks/lessons.md", "decisions": "tasks/decisions.md",
                    "sessions": "tasks/session-log.md", "current": "docs/current-state.md"}
        file_filter = None
        if "all" not in args.files:
            file_filter = [file_map[f] for f in args.files.split(",") if f in file_map]
        semantic_search(" ".join(args.terms), file_filter)
        return
    targets = list(PARSERS.keys()) if "all" in args.files else args.files.split(",")
    docs = []
    for t in targets:
        path = SOURCES.get(t)
        if path and path.exists(): docs.extend(PARSERS[t](path.read_text(), tags_only=args.tags))
    results = bm25(tokenize(" ".join(args.terms)), docs)[:args.top_k]
    if not results:
        if args.json:
            print("[]")
        else:
            print(f"No matches found for: {' '.join(args.terms)}")
        sys.exit(0)
    if args.json:
        out = []
        for score, i in results:
            src, line, label, text = docs[i]
            out.append({"source": src, "line": line, "id": label,
                         "score": round(score, 3), "text": " ".join(text.split())[:300]})
        print(json.dumps(out))
    else:
        for score, i in results:
            src, line, label, text = docs[i]
            print(f"  {src}:{line}  [{label}]  score={score:.3f}")
            print(f"    {' '.join(text.split())[:120]}\n")

if __name__ == "__main__":
    main()

### scripts/finding_tracker.py (argparse section)

#!/usr/bin/env python3
"""
finding_tracker.py — Per-finding state machine for debate findings.

Tracks individual findings through: open -> addressed | waived | obsolete.
Store: stores/findings.jsonl (append-only, last-write-wins per finding_id).

Usage:
    python3 scripts/finding_tracker.py import --judgment tasks/<topic>-judgment.md
    python3 scripts/finding_tracker.py list --debate-id <topic> [--state open]
    python3 scripts/finding_tracker.py transition --finding-id <topic>:3 --to addressed --reason "Fixed in abc123"
    python3 scripts/finding_tracker.py summary --debate-id <topic>
"""
import argparse
import json

[... implementation omitted ...]

VALID_STATES = {"open", "addressed", "waived", "obsolete"}
VALID_TRANSITIONS = {
    ("open", "addressed"),
    ("open", "waived"),
    ("open", "obsolete"),
}
def main():
    parser = argparse.ArgumentParser(description="Per-finding state machine")
    sub = parser.add_subparsers(dest="command")

    p_import = sub.add_parser("import", help="Import findings from judgment")
    p_import.add_argument("--judgment", required=True)

    p_list = sub.add_parser("list", help="List findings")
    p_list.add_argument("--debate-id", required=True)
    p_list.add_argument("--state", default=None)

    p_trans = sub.add_parser("transition", help="Transition a finding")
    p_trans.add_argument("--finding-id", required=True)
    p_trans.add_argument("--to", required=True)
    p_trans.add_argument("--reason", default="")

    p_summary = sub.add_parser("summary", help="Summary counts")
    p_summary.add_argument("--debate-id", required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {"import": cmd_import, "list": cmd_list,
            "transition": cmd_transition, "summary": cmd_summary}
    cmds[args.command](args)


if __name__ == "__main__":

### scripts/enrich_context.py (full)

#!/usr/bin/env python3
"""
enrich_context.py — Pull relevant lessons/decisions into debate proposals.

Extracts keywords from a proposal, searches governance files via recall_search.py,
and returns structured JSON for challengers to consume.

Usage:
    python3 scripts/enrich_context.py --proposal tasks/<topic>-proposal.md [--top-k 5]
"""
import argparse
import json
import os
import re
import subprocess
import sys


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
PYTHON = sys.executable
RECALL = os.path.join(PROJECT_ROOT, "scripts/recall_search.py")


def extract_keywords(text, max_keywords=8):
    """Extract keywords from proposal title, scope, and first paragraph."""
    lines = text.splitlines()
    important_text = []

    # Frontmatter scope field
    in_frontmatter = False
    for line in lines:
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter and line.startswith("scope:"):
            important_text.append(line.partition(":")[2].strip().strip('"'))

    # First heading
    for line in lines:
        if line.startswith("# "):
            important_text.append(line.lstrip("# ").strip())
            break

    # First non-empty, non-frontmatter paragraph
    past_frontmatter = False
    fm_count = 0
    for line in lines:
        if line.strip() == "---":
            fm_count += 1
            if fm_count >= 2:
                past_frontmatter = True
            continue
        if not past_frontmatter:
            continue
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            important_text.append(stripped)
            break

    combined = " ".join(important_text).lower()
    # Remove common words
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                 "have", "has", "had", "do", "does", "did", "will", "would",
                 "could", "should", "may", "might", "can", "shall", "to",
                 "of", "in", "for", "on", "with", "at", "by", "from", "as",
                 "into", "through", "during", "before", "after", "and", "or",
                 "but", "not", "no", "if", "then", "than", "that", "this",
                 "it", "its", "all", "each", "every", "both", "few", "more"}
    tokens = re.findall(r"[a-z][a-z0-9_-]+", combined)
    keywords = [t for t in tokens if t not in stopwords and len(t) > 2]
    # Deduplicate preserving order
    seen = set()
    unique = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    return unique[:max_keywords]


def search_governance(keywords, sources, top_k=5):
    """Run recall_search.py with --json and return parsed results."""
    if not keywords:
        return []
    cmd = [PYTHON, RECALL] + keywords + ["--files", sources, "--json", "--top-k", str(top_k)]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            cwd=PROJECT_ROOT, timeout=10)
    if result.returncode != 0:
        return []
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return []


def main():
    parser = argparse.ArgumentParser(description="Enrich proposal with prior context")
    parser.add_argument("--proposal", required=True, help="Path to proposal file")
    parser.add_argument("--top-k", type=int, default=5, help="Max results per source")
    args = parser.parse_args()

    proposal_path = args.proposal
    if not os.path.isabs(proposal_path):
        proposal_path = os.path.join(PROJECT_ROOT, proposal_path)

    try:
        text = open(proposal_path).read()
    except OSError as e:
        print(json.dumps({"error": str(e), "lessons": [], "decisions": []}))
        sys.exit(1)

    keywords = extract_keywords(text)
    if not keywords:
        print(json.dumps({"keywords": [], "lessons": [], "decisions": []}))
        sys.exit(0)

    lessons = search_governance(keywords, "lessons", args.top_k)
    decisions = search_governance(keywords, "decisions", args.top_k)

    output = {
        "keywords": keywords,
        "lessons": lessons,
        "decisions": decisions,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

### scripts/artifact_check.py (key sections)

#!/usr/bin/env python3
"""
artifact_check.py — Artifact integrity and staleness checker.

Checks for plan, challenge, judgment, and review artifacts for a given topic.
Validates frontmatter, staleness relative to source files, and open findings.

Usage:
    python3 scripts/artifact_check.py --scope <topic> [--base <ref>]
"""
import argparse
import json
import os
import re
import subprocess

[... helpers omitted ...]

def _check_artifact(name, path, scope_mtime):
    """Check a single artifact file. Returns dict with status info."""
    info = {"path": path, "exists": False}
    content = _read_file(path)
    if content is None:
        return info

    info["exists"] = True
    mtime = _file_mtime(path)

    # Staleness: artifact older than newest scope file
    if scope_mtime and mtime and mtime < scope_mtime:
        info["stale"] = True
    else:
        info["stale"] = False

    fm = _parse_frontmatter(content)

    if name == "plan":
        # Valid if has required frontmatter fields
        required = {"scope", "review_tier"}
        info["valid"] = bool(required.intersection(set(fm.keys())))

    elif name == "challenge":
        info["has_material"] = bool(re.search(r"MATERIAL", content))
        has_fm = bool(re.match(r"^---\n.*?debate_id:", content, re.DOTALL))
        info["valid"] = has_fm

    elif name == "judgment":
        accepted = len(re.findall(r"Decision:\s*ACCEPT", content, re.IGNORECASE))
        dismissed = len(re.findall(r"Decision:\s*DISMISS", content, re.IGNORECASE))
        escalated = len(re.findall(r"Decision:\s*ESCALATE", content, re.IGNORECASE))
        info["accepted"] = accepted
        info["dismissed"] = dismissed
        info["escalated"] = escalated

    elif name == "review":
        info["status"] = fm.get("status", "unknown")
        info["review_tier"] = fm.get("review_tier", "unknown")

    return info


def _count_open_material(artifacts, scope=None):
def _count_open_material(artifacts, scope=None):
    """Count open material findings. Uses finding_tracker if available, falls back to judgment counts."""
    judgment = artifacts.get("judgment", {})
    if not judgment.get("exists"):
        return None  # No judgment yet

    # Try finding_tracker.py for per-finding state
    if scope:
        tracker_path = os.path.join(PROJECT_ROOT, "stores/findings.jsonl")
        if os.path.exists(tracker_path):
            try:
                result = subprocess.run(
                    [sys.executable, os.path.join(PROJECT_ROOT, "scripts/finding_tracker.py"),
                     "summary", "--debate-id", scope],
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    summary = json.loads(result.stdout)
                    return summary.get("open", 0)
            except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
                pass  # Fall through to simple count

    # Fallback: count ACCEPT lines in judgment
    return judgment.get("accepted", 0)


def main():
def main():
    parser = argparse.ArgumentParser(description="Check artifact integrity")
    parser.add_argument("--scope", required=True, help="Topic name (artifact prefix)")
    parser.add_argument("--base", default=None, help="Git ref for staleness check")
    args = parser.parse_args()

    scope = args.scope
    scope_mtime = _newest_scope_mtime(args.base)

    # Get current git HEAD
    head_result = subprocess.run(
        ["git", "-C", PROJECT_ROOT, "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    )
    git_head = head_result.stdout.strip() or "unknown"

    # Check each artifact type
    artifact_names = {
        "plan": f"tasks/{scope}-plan.md",
        "challenge": f"tasks/{scope}-challenge.md",
        "judgment": f"tasks/{scope}-judgment.md",
        "review": f"tasks/{scope}-review.md",
    }

    artifacts = {}
    for name, rel_path in artifact_names.items():
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        artifacts[name] = _check_artifact(name, full_path, scope_mtime)

    open_material = _count_open_material(artifacts, scope=scope)

    output = {
        "scope": scope,
        "git_head": git_head,
        "artifacts": artifacts,
        "open_material_findings": open_material,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":

### hooks/hook-plan-gate.sh (full)

#!/bin/bash
# PreToolUse hook: Block commits to protected paths without a valid plan artifact.
#
# Protected paths defined in config/protected-paths.json.
# Exempt paths (tasks/, docs/, tests/, config/, stores/) always pass.
#
# Accepts:
#   1. [EMERGENCY] in commit message — bypass with stderr warning (logged)
#   2. tasks/*-plan.md with complete YAML frontmatter AND verification_evidence != "PENDING"
#
# Rejects:
#   1. [TRIVIAL] on protected paths
#   2. Missing or incomplete plan artifacts
#
# Missing config = fail-open (exit 0).

INPUT=$(cat)
PROJECT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
COMMAND=$(printf '%s' "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

case "$COMMAND" in
  git\ commit*)
    CONFIG="$PROJECT/config/protected-paths.json"
    TASKS="$PROJECT/tasks"

    # Fail-open if config missing
    [ ! -f "$CONFIG" ] && exit 0

    STAGED=$(cd "$PROJECT" && git diff --cached --name-only 2>/dev/null)
    [ -z "$STAGED" ] && exit 0

    # Check if any staged files match protected globs (minus exempt patterns)
    PROTECTED_HIT=$(PLAN_GATE_CONFIG="$CONFIG" PLAN_GATE_STAGED="$STAGED" python3 <<'PYEOF'
import json, os, re, sys

config_path = os.environ["PLAN_GATE_CONFIG"]
try:
    with open(config_path) as f:
        config = json.load(f)
except (OSError, json.JSONDecodeError):
    sys.exit(0)

protected_globs = config.get("protected_globs", [])
exempt_patterns = config.get("exempt_patterns", [])

def glob_to_regex(pattern):
    parts = pattern.split("**")
    converted = []
    for part in parts:
        segment = ""
        for ch in part:
            if ch == "*":
                segment += "[^/]*"
            elif ch == "?":
                segment += "[^/]"
            elif ch in r"\.+^${}()|[]":
                segment += "\\" + ch
            else:
                segment += ch
        converted.append(segment)
    return "^" + ".*".join(converted) + "$"

def matches_any(path, patterns):
    for pat in patterns:
        regex = glob_to_regex(pat)
        if re.match(regex, path):
            return True
    return False

staged = os.environ.get("PLAN_GATE_STAGED", "").strip().splitlines()
for path in staged:
    path = path.strip()
    if not path:
        continue
    if matches_any(path, exempt_patterns):
        continue
    if matches_any(path, protected_globs):
        print("yes")
        sys.exit(0)

print("no")
PYEOF
    )

    [ "$PROTECTED_HIT" != "yes" ] && exit 0

    # --- [TRIVIAL] BLOCKED on protected paths ---
    if printf '%s' "$COMMAND" | grep -q '\[TRIVIAL\]'; then
      printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"block","permissionDecisionReason":"BLOCKED: [TRIVIAL] bypass not allowed for protected paths. Write a plan to tasks/<topic>-plan.md first. See config/protected-paths.json."}}\n'
      exit 2
    fi

    # --- [EMERGENCY] bypass ---
    if printf '%s' "$COMMAND" | grep -q '\[EMERGENCY\]'; then
      echo "WARNING: [EMERGENCY] bypass — plan gate skipped. This will be audited." >&2
      exit 0
    fi

    # --- Check for valid plan artifact ---
    PLAN_VALID=$(PLAN_GATE_CONFIG="$CONFIG" PLAN_GATE_TASKS="$TASKS" python3 <<'PYEOF'
import json, os, re, sys

config_path = os.environ["PLAN_GATE_CONFIG"]
tasks_dir = os.environ["PLAN_GATE_TASKS"]

try:
    with open(config_path) as f:
        config = json.load(f)
except (OSError, json.JSONDecodeError):
    print("yes")  # fail-open
    sys.exit(0)

required_fields = config.get("required_plan_fields", [])

if not os.path.isdir(tasks_dir):
    print("no")
    sys.exit(0)

for f in sorted(os.listdir(tasks_dir)):
    if not f.endswith("-plan.md"):
        continue
    path = os.path.join(tasks_dir, f)
    try:
        content = open(path).read()
    except OSError:
        continue

    if not content.startswith("---"):
        continue
    fm_end = content.find("---", 3)
    if fm_end < 0:
        continue
    frontmatter = content[3:fm_end]

    all_present = True
    for field in required_fields:
        if not re.search(r"^" + re.escape(field) + r"\s*:", frontmatter, re.MULTILINE):
            all_present = False
            break
    if not all_present:
        continue

    ve_match = re.search(r"^verification_evidence\s*:\s*(.+)", frontmatter, re.MULTILINE)
    if ve_match:
        val = ve_match.group(1).strip().strip('"').strip("'")
        if val.upper() == "PENDING":
            continue

    print("yes")
    sys.exit(0)

print("no")
PYEOF
    )

    if [ "$PLAN_VALID" = "yes" ]; then
      exit 0
    fi

    # --- No valid plan found ---
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"block","permissionDecisionReason":"BLOCKED: Protected files staged without a valid plan artifact. Create tasks/<topic>-plan.md with YAML frontmatter containing: scope, surfaces_affected, verification_commands, rollback, review_tier. verification_evidence must not be PENDING."}}\n'
    exit 2
    ;;
esac

exit 0

### hooks/hook-review-gate.sh (full)

#!/bin/bash
# PreToolUse hook: Block/warn if high-risk files staged without valid debate artifacts.
#
# Accepts:
#   1. [TRIVIAL] in commit message — bypass for typo/doc-only commits (logged)
#   2. tasks/*-challenge.md with YAML frontmatter + MATERIAL tag + verdict line
#   3. tasks/*-resolution.md with ## PM/UX Assessment section
#   4. tasks/*-review.md (legacy compat) newer than staged files
#
# Warns: skills/, *_tool.py, .claude/rules/, hook scripts, security files.

INPUT=$(cat)
PROJECT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
COMMAND=$(printf '%s' "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

case "$COMMAND" in
  git\ commit*)
    # --- Check [TRIVIAL] bypass ---
    if printf '%s' "$COMMAND" | grep -q '\[TRIVIAL\]'; then
      echo "NOTICE: [TRIVIAL] bypass — review gate skipped. Logged."
      exit 0
    fi

    STAGED=$(cd "$PROJECT" && git diff --cached --name-only 2>/dev/null)
    [ -z "$STAGED" ] && exit 0

    # --- Classify staged files via tier_classify.py ---
    RISK_LEVEL=$(echo "$STAGED" | python3 -c "
import sys, json, subprocess

stdin_text = sys.stdin.read()
result = subprocess.run(
    [sys.executable, 'scripts/tier_classify.py', '--stdin'],
    input=stdin_text, capture_output=True, text=True,
    cwd='$PROJECT'
)
try:
    d = json.loads(result.stdout)
except (json.JSONDecodeError, ValueError):
    print('ok')
    sys.exit(0)
t = d.get('tier', 2)
if t == 1:
    print('tier1')
elif t == 1.5:
    print('warn')
elif t == 'exempt':
    print('ok')
else:
    files = d.get('files', {})
    warn = any('skill' in f or '_tool.py' in f or '.claude/rules/' in f
               or 'hook-' in f or 'security' in f for f in files)
    print('warn' if warn else 'ok')
" 2>/dev/null)

    [ "$RISK_LEVEL" = "ok" ] && exit 0

    # --- Find newest staged file mtime ---
    NEWEST_STAGED=$(python3 -c "
import os, subprocess, sys
result = subprocess.run(
    ['git', '-C', '$PROJECT', 'diff', '--cached', '--name-only'],
    capture_output=True, text=True
)
newest = 0
for rel in result.stdout.splitlines():
    rel = rel.strip()
    if not rel:
        continue
    full = os.path.join('$PROJECT', rel)
    try:
        newest = max(newest, os.path.getmtime(full))
    except OSError:
        pass
print(newest)
" 2>/dev/null)

    # --- Check for valid debate artifacts ---
    TASKS="$PROJECT/tasks"
    ARTIFACT_VALID=$(python3 -c "
import os, re, sys

tasks = '$TASKS'
newest_staged = float('$NEWEST_STAGED')
found_valid = False

if not os.path.isdir(tasks):
    print('no')
    sys.exit(0)

for f in sorted(os.listdir(tasks)):
    path = os.path.join(tasks, f)
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        continue
    if mtime <= newest_staged:
        continue

    if f.endswith('-challenge.md'):
        try:
            content = open(path).read()
        except OSError:
            continue
        has_frontmatter = bool(re.match(r'^---\n.*?debate_id:', content, re.DOTALL))
        has_material = bool(re.search(r'MATERIAL', content))
        has_verdict = bool(re.search(r'\b(APPROVE|REVISE|REJECT)\b', content))
        if has_frontmatter and has_material and has_verdict:
            found_valid = True
            break

    if f.endswith('-resolution.md'):
        try:
            content = open(path).read()
        except OSError:
            continue
        if '## PM/UX Assessment' in content:
            found_valid = True
            break

    if f.endswith('-review.md'):
        found_valid = True
        break

print('yes' if found_valid else 'no')
" 2>/dev/null)

    if [ "$ARTIFACT_VALID" = "yes" ]; then
      exit 0
    fi

    # --- No valid artifacts found ---
    if [ "$RISK_LEVEL" = "tier1" ]; then
      printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"block","permissionDecisionReason":"BLOCKED: Tier 1 files staged without debate artifacts. Run cross-model debate before committing."}}\n'
      exit 2
    fi

    # Advisory for Tier 2 files
    echo "NOTICE: High-risk files staged without debate artifacts. Log decision in tasks/decisions.md."
    ;;
esac

exit 0

### hooks/hook-tier-gate.sh (full)

#!/bin/bash
# PreToolUse hook: Classify task tier BEFORE first file edit.
# Fires on: Write|Edit
#
# Tier 1 (debate required): PRD, database schema, trust boundary code, security rules
# Tier 1.5 (quality review): core skills, toolbelt scripts
# Tier 2 (log only): everything else
#
# Behavior:
#   - On first Tier 1 file edit in a session, BLOCKS unless debate artifacts exist
#   - On first Tier 1.5 file edit, WARNS (advisory, not blocking)
#   - Tracks "already classified" via a session marker file to avoid re-firing every edit

INPUT=$(cat)
PROJECT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

RESULT=$(python3 -c "
import sys, json, os, re, subprocess, time

PROJECT = '$PROJECT'
TASKS = os.path.join(PROJECT, 'tasks')
MARKER_DIR = '/tmp/build-os-tier-gate'
os.makedirs(MARKER_DIR, exist_ok=True)

try:
    d = json.load(sys.stdin)
except json.JSONDecodeError:
    print('ALLOW')
    sys.exit(0)

ti = d.get('tool_input', {})
file_path = ti.get('file_path', '')

if not file_path:
    print('ALLOW')
    sys.exit(0)

# Normalize to relative path
rel = file_path
if rel.startswith(PROJECT + '/'):
    rel = rel[len(PROJECT) + 1:]

# ── Tier classification via tier_classify.py ──────────────────────────────
try:
    result = subprocess.run(
        [sys.executable, os.path.join(PROJECT, 'scripts/tier_classify.py'), rel],
        capture_output=True, text=True, timeout=5
    )
    tier_data = json.loads(result.stdout)
    raw_tier = tier_data.get('tier', 2)
except Exception:
    raw_tier = 2

if raw_tier == 'exempt' or raw_tier == 2:
    print('ALLOW')
    sys.exit(0)

tier = 15 if raw_tier == 1.5 else int(raw_tier)

# ── Session dedup — don't fire on every single edit ──────────────────────
marker_file = os.path.join(MARKER_DIR, f'tier{tier}_passed')
if os.path.exists(marker_file):
    age = time.time() - os.path.getmtime(marker_file)
    if age < 14400:  # 4 hours
        print('ALLOW')
        sys.exit(0)

# ── Check for valid debate artifacts (Tier 1 only) ───────────────────────
if tier == 1:
    session_marker = os.path.join(MARKER_DIR, 'session_start')
    if not os.path.exists(session_marker):
        with open(session_marker, 'w') as sm:
            sm.write(str(time.time()))
        session_start = time.time()
    else:
        session_start = os.path.getmtime(session_marker)

    found_artifact = False
    if os.path.isdir(TASKS):
        for f in os.listdir(TASKS):
            path = os.path.join(TASKS, f)
            try:
                mtime = os.path.getmtime(path)
            except OSError:
                continue
            if mtime < session_start:
                continue

            if f.endswith('-challenge.md'):
                try:
                    content = open(path).read()
                except OSError:
                    continue
                has_frontmatter = bool(re.match(r'^---\n.*?debate_id:', content, re.DOTALL))
                has_material = bool(re.search(r'MATERIAL', content))
                if has_frontmatter and has_material:
                    found_artifact = True
                    break

            if f.endswith('-judgment.md') or f.endswith('-resolution.md'):
                found_artifact = True
                break

    if found_artifact:
        with open(marker_file, 'w') as mf:
            mf.write(f'artifact_found:{rel}')
        print('ALLOW')
        sys.exit(0)

    print(f'BLOCK_TIER1:{rel}')
    sys.exit(0)

# ── Tier 1.5: advisory warning ───────────────────────────────────────────
if tier == 15:
    with open(marker_file, 'w') as mf:
        mf.write(f'warned:{rel}')
    print(f'WARN_TIER15:{rel}')
    sys.exit(0)

print('ALLOW')
" <<< "$INPUT" 2>/dev/null)

case "$RESULT" in
  BLOCK_TIER1:*)
    FILE="${RESULT#BLOCK_TIER1:}"
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"block","permissionDecisionReason":"BLOCKED: %s is a Tier 1 file (PRD/schema/trust boundary). Cross-model debate required BEFORE editing. Write a proposal to tasks/<topic>-proposal.md, then run: python3 scripts/debate.py challenge --proposal tasks/<topic>-proposal.md --personas architect,security,pm --output tasks/<topic>-challenge.md"}}\n' "$FILE"
    exit 2
    ;;
  WARN_TIER15:*)
    FILE="${RESULT#WARN_TIER15:}"
    echo "NOTICE: $FILE is Tier 1.5 (core skill/toolbelt). Consider running a quality review (1 round, 1 challenger). Proceeding — this is advisory."
    exit 0
    ;;
  *)
    exit 0
    ;;
esac

### config/protected-paths.json (full)

{
  "protected_globs": [
    "skills/**/*.md",
    "scripts/*_tool.py",
    "scripts/*_pipeline.py",
    ".claude/rules/*.md"
  ],
  "exempt_patterns": [
    "tasks/*",
    "docs/*",
    "tests/*",
    "config/*",
    "stores/*"
  ],
  "required_plan_fields": [
    "scope",
    "surfaces_affected",
    "verification_commands",
    "rollback",
    "review_tier"
  ]
}

--- END OF SOURCE CODE ---
