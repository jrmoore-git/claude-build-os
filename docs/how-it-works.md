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

- **Tier 1 (Cross-model debate):** PRD files (matching `docs/.*PRD` or `docs/project-prd.md`), database schema/migration SQL files, `.claude/rules/security.md` specifically, direct `.db` edits
- **Tier 1.5 (Quality review):** Core skill SKILL.md files (requires populating `CORE_SKILLS` in the script — empty by default), toolbelt scripts (`scripts/*_tool.py`), `scripts/debate.py`, and scripts matching `scripts/hook-*.sh`. Note: actual hook files in `hooks/` are not matched by default — only scripts-directory hooks are Tier 1.5
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
  - **challenge**: `valid` checks YAML frontmatter with `debate_id`; `has_material` is a separate field checking for the `MATERIAL` tag
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
