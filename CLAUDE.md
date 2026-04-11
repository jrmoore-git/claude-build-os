# CLAUDE.md

<!-- Target: under 200 lines. Every line loads into every turn and consumes context. -->
<!-- These rules are advisory — Claude reads them and tries to follow them, but compliance -->
<!-- is not guaranteed. For rules that must be enforced, use hooks (see docs/platform-features.md). -->

## What this project is
<!-- Replace this section with a one-paragraph description of what you're building and why. -->
[Describe your project here. What are you building? Who is it for? What problem does it solve?]

## Hard Rules

<!-- These are the non-negotiable invariants. Advisory rules live in Operating Rules below. -->
- Nothing is done because Claude says it is done. Verify with evidence.
- Put constraints near the action they govern, not front-loaded at the top.
- After config changes (CLAUDE.md, rules, .env, hooks), start a fresh session.
- If the LLM can cause irreversible state changes, it must not be the actor.
- Resource limits must be enforced in code — a limit in documentation constrains nothing.
- No task completion without the appropriate review tier.
- Every commit must update relevant tracking docs.
- Before trusting a new hook or gate, verify it can actually fail.

**Essential eight invariants:** idempotency · approval gating · audit completeness · degraded mode visible · state machine validation · rollback path exists · version pinning enforced · exactly-once scheduling.

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

### Inspect before acting
<!-- Why: The model defaults to training knowledge over available tools, especially under context pressure. -->
<!-- Why: Editing code you haven't read produces confident-looking but wrong changes. -->
Read handoff.md and current-state.md before starting work. Read relevant lessons and decisions before touching risky areas. Don't load everything — load what's relevant.
- Before editing a file: read it and its immediate context (tests, callers, related modules).
- Before answering "can we do X" or "does this support Y": Grep/Read the relevant code first. Answer from what you found, not from memory. If you didn't inspect the code, say so explicitly instead of implying certainty.
- Never say "I don't think this supports..." or "this probably doesn't..." without checking.

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
- **Hooks:** `hooks/hook-plan-gate.sh`, `hooks/hook-review-gate.sh`, `hooks/hook-tier-gate.sh`, `hooks/hook-decompose-gate.py` (blocks Write|Edit until decomposition assessed), `hooks/hook-agent-isolation.py` (blocks Agent dispatch without worktree isolation after parallel plan), `hooks/hook-guard-env.sh`, `hooks/hook-pre-edit-gate.sh`, `hooks/hook-post-tool-test.sh`, `hooks/hook-prd-drift-check.sh`, `hooks/hook-pre-commit-tests.sh`, `hooks/hook-ruff-check.sh`, `hooks/hook-syntax-check-python.sh` — wired in `.claude/settings.json` (see [Hooks Reference](docs/hooks.md))
- **Scripts:** `scripts/debate.py` (cross-model engine: challenge, judge, refine, review, review-panel, check-models — config-driven via `config/debate-models.json`), `scripts/tier_classify.py` (file tier classification), `scripts/recall_search.py` (governance search), `scripts/finding_tracker.py` (finding lifecycle), `scripts/enrich_context.py` (context enrichment), `scripts/artifact_check.py` (artifact validation) — see [How It Works](docs/how-it-works.md)
- **Config:** `config/protected-paths.json` defines protected globs, exempt paths, and required plan fields. `config/debate-models.json` maps personas to LiteLLM models (fallback to hardcoded defaults if missing).
- **Skills:** `.claude/skills/` — each skill is a `SKILL.md` file with YAML frontmatter (24 skills):
  - Pipeline: `/recall` → `/define` → `/elevate` → `/challenge` → `/debate` → `/plan` → `/refine` → `/review` → `/ship`
  - Design: `/design-consultation`, `/design-review`, `/design-shotgun`, `/plan-design-review`
  - Session: `/status`, `/capture`, `/wrap-session`, `/triage`
  - Quality: `/qa`, `/governance`, `/doc-sync`
  - Automation: `/autoplan`, `/review-x`
  - Bootstrap: `/setup`, `/audit`
  - `/debate` = adversarial personas attack → judge rules → refine. For pressure-testing decisions.
  - `/refine` = 6-round cross-model collaborative improvement. Standalone on any input, or as final phase of `/debate`.
  - Pipeline tiers: T0 (spike) = build. T2 (standard) = `/define refine` → `/plan` → build. T1 (new feature) = `/define discover` → `/challenge` → `/plan` → build. Big bet = `/define discover` → `/elevate` → `/challenge` → `/plan` → build. All tiers can optionally use `/refine` on plans or designs before building. All end with → `/review` → `/ship`.
- **Rules:** `.claude/rules/` — code-quality, design, orchestration, review-protocol, session-discipline, skill-authoring, workflow (see individual files for details)

## Project-specific rules
<!-- Add rules specific to your project as you discover them. Examples: -->
<!-- - "All API responses must be validated against the schema before processing" -->
<!-- - "Never modify the payments table directly — use the payments service" -->
<!-- - "Run pytest after any change to src/" -->
