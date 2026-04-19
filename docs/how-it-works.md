# How It Works

Technical internals for every script in the Build OS. Each script is a standalone CLI tool — pure stdlib Python, no pip dependencies — that powers part of the governance pipeline.

**Jump to script:**

| Script | What it does |
|---|---|
| [`debate.py`](#debatepy) | Cross-model challenge / judge / refine / review / pressure-test / explore |
| [`tier_classify.py`](#tier_classifypy) | File-tier classification for review routing |
| [`recall_search.py`](#recall_searchpy) | Governance search across decisions/lessons/rules |
| [`finding_tracker.py`](#finding_trackerpy) | Finding lifecycle (open → resolved → archived) |
| [`enrich_context.py`](#enrich_contextpy) | Context enrichment for proposals |
| [`artifact_check.py`](#artifact_checkpy) | Artifact validation |
| [`check-current-state-freshness.py`](#check-current-state-freshnesspy) | Freshness gate on `docs/current-state.md` |
| [`lesson_events.py`](#lesson_eventspy) | Lesson lifecycle events + velocity metrics |

---

## debate.py

Cross-model adversarial review automation. This is the most important script: it orchestrates the full challenge → judge → refine pipeline by routing proposals through multiple AI models via a LiteLLM proxy.

The problem it solves: a single model reviewing its own work produces sycophantic reviews. debate.py sends proposals to different model families (Gemini 3.1 Pro, GPT-5.4, Claude Opus) with adversarial system prompts, then has an independent judge evaluate the challenges, and finally runs iterative cross-model refinement seeded by the judge's accepted findings. All three model families participate as both challengers and refiners, with the judge assigned to a different family than the code author to avoid self-preference bias.

### Subcommands

**challenge** — Send a proposal to challenger models for adversarial review. Each challenger receives the proposal (with author metadata redacted) and a role-specific adversarial prompt. Challengers must tag each finding with a type (RISK, ASSUMPTION, ALTERNATIVE, OVER-ENGINEERED, UNDER-ENGINEERED) and a materiality label (MATERIAL or ADVISORY).

```
python3.11 scripts/debate.py challenge \
    --proposal tasks/auth-redesign-proposal.md \
    --personas architect,security,pm,frame \
    --output tasks/auth-redesign-challenge.md
```

Personas map to models via `config/debate-models.json`. The default assignments balance all three model families across the personas:

| Persona | Default model | Rationale |
|---------|--------------|-----------|
| architect | claude-opus-4-7 | Systems reasoning, architecture benchmarks |
| security | gpt-5.4 | Strictest reviewer, best at finding edge cases |
| pm | gemini-3.1-pro | Product reasoning, spec compliance, user empathy |
| frame | claude-sonnet-4-6 | Candidate-set critique: binary framings, missing compositional candidates, source-driven inheritance, problem inflation. With `--enable-tools`, expands to dual-mode: `frame-structural` (tools off) + `frame-factual` (tools on, `frame_factual_model` default `gpt-5.4`). See `.claude/rules/review-protocol.md` Stage 1 and `tasks/lessons.md` L43. |
| staff | gemini-3.1-pro | Code quality review by a different family than the author (opt-in; not in default persona set) |

The judge defaults to gpt-5.4 (different family from the typical Claude author avoids self-preference bias). The refinement rotation cycles all three families: gemini → gpt → claude.

Each persona gets a role-specific adversarial prompt (architecture concerns, security focus, operational feasibility, or user value). Note that personas sharing a model are deduplicated — `--personas pm,staff` produces one challenger since both map to gemini-3.1-pro. Alternatively, pass `--models gpt-5.4,gemini-3.1-pro` directly with a generic adversarial prompt. An optional `--system-prompt` flag (takes a string or file path) overrides the default prompt entirely — used by `/review` to replace adversarial challenge prompts with review-specific persona lens definitions.

**`--enable-tools`** gives challengers access to read-only verifier tools (`check_code_presence`, `check_function_exists`, `check_test_coverage`, `read_file_snippet`, `read_config_value`, `get_recent_commits`, `get_job_schedule` — defined in `scripts/debate_tools.py`). These let challengers verify claims against the actual codebase rather than speculating. Tools are sandboxed to read-only operations.

Produces: `tasks/<topic>-challenge.md` with YAML frontmatter containing `debate_id`, `created` timestamp, and a `mapping` of challenger labels (A, B, C...) to model names. Also prints a JSON status object to stdout with `status`, `challengers` count, `mapping`, and any `warnings`.

**judge** — Independent evaluation of challenges by a non-author model. Before judging, multi-challenger findings are automatically consolidated: overlapping findings from different challengers are deduplicated and merged into a unified list with corroboration notes (e.g., "Raised by 2/3 challengers"). This reduces redundancy and gives the judge a cleaner input. Use `--no-consolidate` to skip this step and send raw challenger sections (shuffled to eliminate position bias). The judge then issues ACCEPT, DISMISS, or ESCALATE on each MATERIAL challenge with a confidence score (0.0–1.0).

```
python3.11 scripts/debate.py judge \
    --proposal tasks/auth-redesign-proposal.md \
    --challenge tasks/auth-redesign-challenge.md \
    --output tasks/auth-redesign-judgment.md
```

Default judge model: gpt-5.4 (chosen because a different model family avoids self-preference bias when the author is Claude). The judge warns if it matches the author model. An optional `--rebuttal` flag passes author context without giving the author decision authority. `--system-prompt` (file path) overrides the default judge prompt.

**FRAME CRITIQUE (judge stage):** After evaluating challenger findings, the judge runs a second pass against the proposal itself to surface frame-level defects that no challenger raised — binary framings, missing compositional candidates, source-driven inheritance, problem inflation, and unstated assumptions. A **novelty gate** requires the judge to (1) state the concrete fix the frame finding implies, (2) scan existing challenger findings for any recommending the same fix, and (3) suppress the new finding as "covered" if the fix overlaps. Output separates "additive" from "covered" findings with explicit `covered by Challenge [N]` mapping when redundant. Validated n=11 + negative control + 3 novelty-gate re-runs, 0 fabrications. See `tasks/lessons.md` L46.

**Overall verdict:** The judge emits an overall decision on the proposal itself — `APPROVE`, `REVISE`, `REJECT`, or `INVESTIGATE` (the latter means "insufficient evidence; run a time-boxed investigation before deciding"). `INVESTIGATE` was previously named `SPIKE`; the JSON CLI fields (`investigating`, etc.) reflect the rename.

Produces: `tasks/<topic>-judgment.md` with accepted/dismissed/escalated counts. Findings marked ESCALATE require human review. Prints JSON to stdout with `accepted`, `dismissed`, `escalated`, `investigating` counts and `needs_human` flag.

**refine** — Iterative cross-model document improvement. Each round, a different model reviews and rewrites the document. Works as both the final phase of the `/challenge --deep` pipeline (seeded with accepted challenges) and as a standalone tool via the `/polish` skill (for collaborative improvement without adversarial framing).

```
# As part of /challenge --deep pipeline (seeded with judgment)
python3.11 scripts/debate.py refine \
    --document tasks/auth-redesign-proposal.md \
    --judgment tasks/auth-redesign-judgment.md \
    --rounds 6 \
    --output tasks/auth-redesign-refined.md

# Standalone via /polish skill (no judgment needed)
python3.11 scripts/debate.py refine \
    --document tasks/any-document.md \
    --rounds 6 \
    --output tasks/any-document-refined.md \
    --enable-tools
```

Default model rotation: gemini-3.1-pro → gpt-5.4 → claude-opus-4-7 (cycles if rounds exceed model count). All three model families participate in refinement, ensuring no single family's biases dominate the final output. Default rounds: 6 (each model refines twice). Each round produces review notes and a complete revised document; the revised document feeds into the next round.

**Challenge synthesis mode:** When refine processes a multi-challenger document (output of `challenge`), it automatically switches to structured extract-then-classify synthesis instead of prose rewriting. Phase 1 extracts every distinct finding from all challengers and classifies each by diagnosticity (HIGH/MEDIUM/LOW), evidence type (CITED/REASONED/ASSERTED), and support count. Phase 2 verifies completeness. A NEVER-DROP rule ensures minority findings (1-of-3 challengers) are preserved — these are often the most valuable insights. A MERGE vs SPLIT rule prevents same-topic-different-claim findings from being incorrectly merged (e.g., a risk and its mitigation stay separate). A/B tested: 5/5 blind judge wins vs prose consolidation, Finding Recall 4.8/5 vs 3.0/5.

The `--judgment` flag is optional. When provided (as in the `/challenge --deep` pipeline), the first round is seeded with accepted challenges so models know exactly what to fix. When omitted (standalone `/polish`), models use their own judgment to improve the document. The `/polish` skill can also pass user-specified focus areas via the same `--judgment` slot.

**Per-model timeout with fallback:** Models with known tail latency (e.g., Gemini 3.1 Pro Preview — 29s TTFT, p99=542s) get shorter timeouts via `MODEL_TIMEOUTS`. On timeout, the refine loop automatically falls back to the next model in the rotation instead of blocking the serial pipeline. Fallback attempts are logged to stderr.

**FRAME CHECK (refine stage):** Each refine round includes a FRAME CHECK pass that surfaces frame-level concerns the round introduces or carries forward. Three filters gate findings: (1) load-bearing — the concern must affect downstream decisions; (2) out-of-scope for refine — concerns refine cannot address belong in review; (3) not-already-covered — concerns already handled in the document's Review Notes section are suppressed. A **mutually-exclusive channel rule** prevents double-reporting: fixed concerns appear in Review Notes with explicit frame-lens language; unfixed concerns appear in Frame Check. Never both. Calibrated across v1→v5 iterations with a 5-proposal benchmark; v2 had 0/6 detection (silent failure) before the benchmark caught it. See `tasks/lessons.md` L47.

Produces: `tasks/<topic>-refined.md` with per-round review notes, Frame Check section, and the final refined document.

**compare** — Score two review methods against the same original document on five dimensions (accuracy, completeness, constructiveness, efficiency, artifact quality). Useful for evaluating whether the full pipeline outperforms simpler review approaches.

```
python3.11 scripts/debate.py compare \
    --original tasks/auth-redesign-proposal.md \
    --method-a tasks/auth-redesign-challenge.md \
    --method-b tasks/auth-redesign-refined.md \
    --output tasks/auth-redesign-compare.md
```

Default judge: gpt-5.4. Produces a scorecard with METHOD_A / METHOD_B / TIE verdict.

**verdict** (legacy) — Sends a resolution back to the original challengers for a final APPROVE / REVISE / REJECT. This was the original pipeline's final step before the judge subcommand replaced it. Still functional but the standard pipeline now uses judge + refine instead.

```
python3.11 scripts/debate.py verdict \
    --resolution tasks/auth-redesign-resolution.md \
    --challenge tasks/auth-redesign-challenge.md \
    --output tasks/auth-redesign-verdict.md
```

**review** — Unified review command: single persona/model or multi-model panel. Accepts four mutually exclusive model-selection flags: `--persona` (single, with persona framing), `--personas` (parallel panel, with persona framing), `--model` (single, no persona framing), `--models` (parallel panel, no persona framing). Multiple reviewers run concurrently via `ThreadPoolExecutor` with anonymous output (labeled A, B, C to eliminate position and identity bias).

```
# Single persona (code review)
python3.11 scripts/debate.py review \
    --persona pm \
    --prompt "Review this plan for completeness" \
    --input tasks/auth-redesign-plan.md

# Single model (no persona framing)
python3.11 scripts/debate.py review \
    --model gemini-3.1-pro \
    --prompt "Review this brief for implementability" \
    --input tasks/auth-redesign-brief.md

# Multiple personas (parallel panel)
python3.11 scripts/debate.py review \
    --personas architect,security,pm \
    --prompt "Review this diff for production readiness" \
    --input tasks/auth-redesign-diff.md

# Multiple models (parallel panel, no persona framing)
python3.11 scripts/debate.py review \
    --models claude-opus-4-7,gemini-3.1-pro,gpt-5.4 \
    --prompt-file /tmp/eval-prompt.md \
    --input tasks/auth-redesign-doc.md
```

When using `--model` or `--models`, no persona framing is injected — the caller's prompt is the only system prompt. `--enable-tools` gives reviewers read-only verifier tools (works with all model-selection flags). `review-panel` is a deprecated alias that maps to `review`.

**explore** — Generate 3+ divergent directions with cross-model synthesis. Each direction is generated by a rotating model from the `explore_rotation` config (cycles through all three model families), then a synthesis pass identifies common themes, complementary ideas, and contradictions across directions. Model rotation ensures each direction reflects a different model family's reasoning style.

```
python3.11 scripts/debate.py explore \
    --question "What are the options for X?" \
    --directions 4 \
    --context "additional market/tech context here" \
    --output tasks/auth-redesign-explore.md
```

**pressure-test** — Counter-thesis or pre-mortem failure analysis. In `challenge` frame (default), generates a strategic counter-thesis arguing against the proposal. In `premortem` frame, assumes the plan has already failed and writes the post-mortem from the future.

```
python3.11 scripts/debate.py pressure-test \
    --proposal tasks/auth-redesign-plan.md \
    --frame challenge \
    --output tasks/auth-redesign-pressure-test.md
```

Use `--frame premortem` for prospective failure analysis instead of adversarial counter-thesis.

**premortem** — Dedicated pre-mortem subcommand. Assumes the plan failed and writes a post-mortem from the future, identifying the most likely failure modes, warning signs that were missed, and what should have been done differently.

```
python3.11 scripts/debate.py pre-mortem \
    --plan tasks/auth-redesign-plan.md \
    --output tasks/auth-redesign-premortem.md
```

**check-models** — Verify that configured models in `config/debate-models.json` are reachable via the LiteLLM proxy. Tests connectivity to each model and reports which are available and which are failing.

```
python3.11 scripts/debate.py check-models
```

**outcome-update** — Update debate outcomes after implementation. Records whether accepted challenges were actually addressed, linking debate findings to implementation results for retrospective analysis.

```
python3.11 scripts/debate.py outcome-update \
    --debate-id auth-redesign \
    --outcome implemented
```

**stats** — Show debate activity statistics. Reads from `stores/debate-log.jsonl` and reports run counts by phase, model usage, and recent activity.

```
python3.11 scripts/debate.py stats
```

### The standard pipeline

The recommended three-step pipeline (via `/challenge --deep`):

1. `challenge` — adversarial models find issues
2. `judge` — independent model evaluates which issues are real
3. `refine` — collaborative models fix accepted issues and improve the document

The `refine` subcommand also runs standalone (via `/polish` skill) for collaborative improvement without the adversarial phases. Use `/challenge --deep` when you need to pressure-test whether something is right. Use `/polish` when you have something and want it better.

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
python3.11 scripts/tier_classify.py scripts/debate.py docs/project-prd.md

# Classify files from git diff
python3.11 scripts/tier_classify.py --diff-base main

# Classify from stdin (one path per line)
echo "scripts/debate.py" | python3.11 scripts/tier_classify.py --stdin
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

The problem it solves: governance files grow over time. Manually scanning 80+ lessons or 50+ decisions for relevant entries is slow. This script makes prior context searchable so `/start` and other skills can load only what matters.

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
python3.11 scripts/recall_search.py oauth token refresh

# Search only lessons and decisions
python3.11 scripts/recall_search.py --files lessons,decisions sqlite timeout

# Semantic search (requires Ollama)
python3.11 scripts/recall_search.py --semantic "database migration failures"

# JSON output for programmatic use
python3.11 scripts/recall_search.py --json --top-k 3 hook gate bypass
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
python3.11 scripts/finding_tracker.py import \
    --judgment tasks/auth-redesign-judgment.md
```

Idempotent: already-imported findings are skipped.

**list** — List findings for a debate, optionally filtered by state.

```
python3.11 scripts/finding_tracker.py list --debate-id auth-redesign
python3.11 scripts/finding_tracker.py list --debate-id auth-redesign --state open
```

**transition** — Move a finding to a new state.

```
python3.11 scripts/finding_tracker.py transition \
    --finding-id auth-redesign:3 \
    --to addressed \
    --reason "Fixed in commit abc123"
```

**summary** — Counts by state for a debate.

```
python3.11 scripts/finding_tracker.py summary --debate-id auth-redesign
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
# Default enrichment
python3.11 scripts/enrich_context.py \
    --proposal tasks/auth-redesign-proposal.md \
    --top-k 5

# Scoped enrichment (adjusts keyword weighting by stage)
python3.11 scripts/enrich_context.py \
    --proposal tasks/auth-redesign-proposal.md \
    --scope challenge    # or: debate, review
```

The `--scope` parameter adjusts keyword extraction and scoring weights for the pipeline stage. For example, `--scope review` emphasizes implementation-related terms, while `--scope challenge` emphasizes problem-space terms. Without `--scope`, uses balanced defaults.

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

Called by `/challenge`, `/challenge --deep`, and `/review` skills to enrich context before sending to cross-model reviewers. Also usable as a standalone CLI tool. Calls `recall_search.py` internally with `--json` output.


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
python3.11 scripts/artifact_check.py --scope auth-redesign
python3.11 scripts/artifact_check.py --scope auth-redesign --base main
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


## check-current-state-freshness.py

Detects whether `docs/current-state.md` is stale relative to recent git activity. Used by `/start` to prevent trusting a frozen "Next Action" from a previous session.

The problem it solves: if a session exits without running `/wrap`, `current-state.md` becomes stale because commits land after its header date. This script detects that.

### What it checks

1. Parses the date from the `# Current State — YYYY-MM-DD` header
2. Compares the header date against the latest git commit date
3. If the latest commit is >24 hours after the header date, reports stale

### Usage

```
python3.11 scripts/check-current-state-freshness.py
```

### Output

JSON to stdout:

```json
{
  "is_stale": true,
  "current_state_date": "2026-03-30",
  "latest_commit_date": "2026-04-01",
  "days_behind": 2,
  "has_stale_marker": true,
  "recent_commits": ["f3c306b App v2 reliability fix", "dea3eb5 Session capture"],
  "message": "current-state.md has an explicit STALE marker. current-state.md date (2026-03-30) is 2 day(s) behind latest commit (2026-04-01). Do NOT trust 'Next Action' — check recent commits and session-log instead."
}
```

When not stale: `{"is_stale": false}`.

### Used by

The `/start` skill calls this in step 0c. When `is_stale` is true, `/start` adds a warning to the session brief and derives its "Next" recommendations from git log + session-log instead of the frozen current-state doc.


## lesson_events.py

Lesson lifecycle event logger and velocity metrics. Tracks lesson creation, promotion, resolution, and archival events, and computes velocity metrics (lessons created per week, promotion rate, median time-to-resolution).

The problem it solves: lessons accumulate in `tasks/lessons.md` but without tracking when they were created, promoted, or resolved, there is no way to measure whether the learning system is healthy. This script provides the event log and metrics that `/healthcheck` uses to assess learning velocity.

### Usage

```
# Log a lesson event
python3.11 scripts/lesson_events.py log --lesson-id L42 --event created

# Log promotion to a rule
python3.11 scripts/lesson_events.py log --lesson-id L42 --event promoted --detail "Promoted to .claude/rules/code-quality.md"

# Show velocity metrics
python3.11 scripts/lesson_events.py metrics
```

### Events

- `created` — New lesson added to `tasks/lessons.md`
- `promoted` — Lesson promoted to a rule in `.claude/rules/`
- `resolved` — Lesson marked resolved (code fix shipped)
- `archived` — Lesson moved to `tasks/lessons-archived.md`

### Used by

The `/healthcheck` skill calls `metrics` to assess learning system health — lesson creation rate, promotion rate, and staleness of open lessons.
