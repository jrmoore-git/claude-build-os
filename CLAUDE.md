# CLAUDE.md

<!-- Target: under 200 lines. Every line loads into every turn and consumes context. -->
<!-- These rules are advisory — Claude reads them and tries to follow them, but compliance -->
<!-- is not guaranteed. For rules that must be enforced, use hooks (see docs/platform-features.md). -->

## What this project is
<!-- Replace this section with a one-paragraph description of what you're building and why. -->
[Describe your project here. What are you building? Who is it for? What problem does it solve?]

## Operating rules

### Simplicity is the override rule
<!-- Why: Claude over-engineers by default. This phrase is from Anthropic's own docs and Claude responds to it reliably. -->
Avoid over-engineering. Only make changes that are directly requested or clearly necessary. Keep solutions simple and focused.
- Don't add features, refactor code, or make "improvements" beyond what was asked.
- Don't add error handling, fallbacks, or validation for scenarios that can't happen.
- Don't create helpers, utilities, or abstractions for one-time operations.
- Don't design for hypothetical future requirements.

### The model may decide; software must act
<!-- Why: Prevents the most dangerous class of AI bugs — LLM-driven state changes. -->
LLMs classify, summarize, and draft. Deterministic code performs state transitions, API calls, and data mutations.
If the LLM can cause irreversible state changes, it must not be the actor.

### Retrieve before planning
<!-- Why: Loading everything into context creates drift, not safety. -->
Read handoff.md and current-state.md before starting work. Read relevant lessons and decisions before touching risky areas. Don't load everything — load what's relevant.

### Challenge before planning, plan before building
<!-- Why: Most expensive mistakes happen before code — wrong scope, wrong abstraction, wrong priority. -->
<!-- Why: Plans written to disk prevent wasted work and survive session compaction. Skip for trivial edits. -->
If work introduces any of: new abstractions, new dependencies, new infrastructure, generalization, or scope expansion — run `/challenge` first. Default posture is skepticism — the simplest version wins unless there's evidence otherwise.
Write a plan to disk if: more than 3 files change, auth/security is involved, user-facing behavior changes, or multiple tracks need coordination.
Skip both for: bugfixes, test-only changes, docs, `[TRIVIAL]` (≤2 files, no new abstractions, one-sentence scope).

### Document results
<!-- Why: Decisions and lessons that stay in conversation history are lost on the next session. Disk is durable memory. -->
Update decisions.md after material decisions.
Update lessons.md after surprises or mistakes.
Update handoff.md before ending incomplete work.

### Verify before declaring done
<!-- Why: "It should work" is not evidence. Claude will claim completion confidently even when things are broken. -->
Prove it works. Tests, logs, evidence. A claim of completion is not evidence.

### Watch for gate gaming
<!-- Why: Gates that are routinely bypassed become invisible. -->
If `[CHALLENGE-SKIPPED]` or `[TRIVIAL]` appears more than 3 times in a sprint, the trigger criteria may be miscalibrated — review and adjust.

## Infrastructure reference

<!-- These point at the enforcement and tooling layers that back the rules above. -->
- **Hooks:** `hooks/hook-plan-gate.sh`, `hooks/hook-review-gate.sh`, `hooks/hook-tier-gate.sh`, `hooks/hook-decompose-gate.sh`, `hooks/hook-guard-env.sh`, `hooks/hook-pre-edit-gate.sh`, `hooks/hook-post-tool-test.sh`, `hooks/hook-prd-drift-check.sh`, `hooks/hook-pre-commit-tests.sh`, `hooks/hook-ruff-check.sh`, `hooks/hook-syntax-check-python.sh` — wired in `.claude/settings.json` (see [Hooks Reference](docs/hooks.md))
- **Scripts:** `scripts/debate.py` (cross-model review), `scripts/multi_model_debate.py` (three-model debate), `scripts/model_conversation.py` (persistent conversation manager), `scripts/tier_classify.py` (file tier classification), `scripts/recall_search.py` (governance search), `scripts/finding_tracker.py` (finding lifecycle), `scripts/enrich_context.py` (context enrichment), `scripts/artifact_check.py` (artifact validation) — see [How It Works](docs/how-it-works.md)
- **Config:** `config/protected-paths.json` defines protected globs, exempt paths, and required plan fields
- **Skills:** `.claude/skills/` — each skill is a `SKILL.md` file with YAML frontmatter. Design skills: `/design-consultation`, `/design-review`, `/plan-design-review`. Operational skills: `/debate`, `/qa`, `/status`, `/capture`, `/wrap-session`
  - `/define` — Problem definition. Two modes: `discover` (full problem discovery with forcing questions, premise challenges, alternatives — writes `tasks/<topic>-design.md`) and `refine` (lightweight sanity check — writes `tasks/<topic>-think.md`). Run before `/challenge` or `/plan`.
  - `/elevate` — Scope and ambition review. 10-star product thinking, 4 scope modes (expansion, selective expansion, hold, reduction). Reads the design doc from `/define discover`. Run after `/define discover` to stress-test scope and ambition before planning.
  - Pipeline tiers: T0 (spike) = build. T2 (standard) = `/define refine` → `/plan` → build. T1 (new feature) = `/define discover` → `/challenge` → `/plan` → build. Big bet = `/define discover` → `/elevate` → `/challenge` → `/plan` → build. All end with → `/review` → `/ship`.
- **Rules:** `.claude/rules/` — code-quality, design, orchestration, review-protocol, session-discipline, skill-authoring, workflow (see individual files for details)

## Project-specific rules
<!-- Add rules specific to your project as you discover them. Examples: -->
<!-- - "All API responses must be validated against the schema before processing" -->
<!-- - "Never modify the payments table directly — use the payments service" -->
<!-- - "Run pytest after any change to src/" -->
