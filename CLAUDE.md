# CLAUDE.md

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

**Essential eight invariants (6 of 8 apply to BuildOS):** idempotency · ~~approval gating~~ · audit completeness · degraded mode visible · ~~state machine validation~~ · rollback path exists · version pinning enforced · ~~exactly-once scheduling~~. Struck-through invariants require a downstream outbox (not present in BuildOS).

## Operating rules

### Simplicity is the override rule
<!-- Why: Claude over-engineers by default. This phrase is from Anthropic's own docs and Claude responds to it reliably. -->
Avoid over-engineering. Only make changes that are directly requested or clearly necessary. The simplest version wins unless there's evidence otherwise. No speculative abstraction. No premature generalization. See code-quality.md for specific constraints.

### The model may decide; software must act
<!-- Why: Prevents the most dangerous class of AI bugs — LLM-driven state changes. -->
LLMs classify, summarize, and draft. Deterministic code performs state transitions. If the LLM can cause irreversible state changes, it must not be the actor. See security.md for the full boundary specification.

### Inspect before acting
<!-- Why: The model defaults to training knowledge over available tools, especially under context pressure. -->
<!-- Why: Editing code you haven't read produces confident-looking but wrong changes. -->
Minimum required at session start: read handoff.md and current-state.md. Before proposing a plan, also complete the full orient-before-planning checklist in workflow.md (project-prd.md, lessons.md, session-log.md). Skipping the full checklist before planning is a violation, not an optimization.
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
Update decisions.md after making material decisions and before implementing them.
Update lessons.md after surprises or mistakes.
Update handoff.md before ending incomplete work.
See session-discipline.md for the full what-goes-where table.

### Verify before declaring done
<!-- Why: "It should work" is not evidence. Claude will claim completion confidently even when things are broken. -->
Prove it works. Tests, logs, evidence. A claim of completion is not evidence.

### Watch for gate gaming
<!-- Why: Gates that are routinely bypassed become invisible. -->
If `[CHALLENGE-SKIPPED]` or `[TRIVIAL]` appears more than 3 times in a sprint, the trigger criteria may be miscalibrated — review and adjust.

## Infrastructure reference
- **Hooks (17):** `hook-intent-router.py` (UserPromptSubmit), `hook-plan-gate.sh`, `hook-review-gate.sh`, `hook-tier-gate.sh`, `hook-decompose-gate.py`, `hook-agent-isolation.py`, `hook-guard-env.sh`, `hook-pre-edit-gate.sh`, `hook-memory-size-gate.py`, `hook-post-tool-test.sh`, `hook-prd-drift-check.sh`, `hook-pre-commit-tests.sh`, `hook-ruff-check.sh`, `hook-syntax-check-python.sh`, `hook-bash-fix-forward.py`, `hook-error-tracker.py` (PostToolUse:Bash), `hook-stop-autocommit.py` — all in `hooks/`, wired in `.claude/settings.json` (see [Hooks Reference](docs/hooks.md))
- **Scripts:** `scripts/debate.py` (cross-model engine: challenge, judge, refine, review, check-models — config-driven via `config/debate-models.json`; **read [invocation reference](.claude/rules/reference/debate-invocations.md) before calling directly**), `scripts/browse.sh` (thin wrapper around gstack's headless browser binary — used by `/design review`, `/design consult`, `/design variants`; requires gstack installed at `~/.claude/skills/gstack/`), `scripts/tier_classify.py` (file tier classification), `scripts/recall_search.py` (governance search), `scripts/finding_tracker.py` (finding lifecycle), `scripts/enrich_context.py` (context enrichment), `scripts/artifact_check.py` (artifact validation), `scripts/lesson_events.py` (lesson lifecycle event logger + velocity metrics — used by `/healthcheck`) — see [How It Works](docs/how-it-works.md)
- **Config:** `config/protected-paths.json` defines protected globs, exempt paths, and required plan fields. `config/debate-models.json` maps personas to LiteLLM models (fallback to hardcoded defaults if missing).
- **Skills:** `.claude/skills/` — each skill is a `SKILL.md` file with YAML frontmatter (21 skills):
  - Pipeline: `/start` → `/think` → `/elevate` → `/challenge` → `/plan` → `/review` → `/ship` → `/wrap`
  - Thinking: `/explore` (divergent options), `/pressure-test` (counter-thesis or pre-mortem)
  - Design: `/design` (4 modes: `consult`, `review`, `variants`, `plan-check`)
  - Specialist: `/research`, `/audit`, `/investigate` (root-cause analysis), `/setup`, `/triage`
  - System health: `/healthcheck` (learning system health — auto-runs in `/start` and `/wrap`, manual via `/healthcheck`)
  - Discovery: `/guide` (intent-based skill map — "what can I do?")
  - Utility: `/polish` (6-round cross-model refinement), `/log` (capture decisions/lessons), `/sync` (post-ship doc sync)
  - `/challenge --deep` = full adversarial pipeline: challenge → judge → refine. For pressure-testing decisions.
  - `/polish` = 6-round cross-model collaborative improvement. Standalone on any input, or as final phase of `/challenge --deep`.
  - Pipeline tiers: T0 (spike) = build. T2 (standard) = `/think refine` → `/plan` → build. T1 (new feature) = `/think discover` → `/challenge` → `/plan` → build. T1+UI = `/think discover` → `/design consult` → `/challenge` → `/plan` → build → `/design review`. Big bet = `/think discover` → `/elevate` → `/challenge` → `/plan` → build. All tiers end with → `/review` → `/ship`. If it has a UI, wire in `/design consult` before plan and `/design review` before ship. Use `/plan --auto` to auto-chain the full pipeline.
- **Rules:** `.claude/rules/` — code-quality, design, natural-language-routing, orchestration, review-protocol, session-discipline, skill-authoring, workflow (see individual files for details)

## Compact Instructions

When compacting this session, preserve in order of priority:
1. **Active task**: current objective, which step I'm on, acceptance criteria, and immediate blockers
2. **Decisions made this session**: choices, rejected alternatives, and rationale — if not yet written to disk
3. **Dirty state**: uncommitted changes, files modified but not committed, pending git operations
4. **Review status**: active review-protocol phase, unresolved findings, whether review is required before commit
5. **File pointers**: paths to session-log.md, handoff.md, and any task-specific plan or artifact files

Discard freely: tool output bodies, file contents re-readable from disk, resolved error traces, exploratory dead ends (unless the dead end was the decision), verbose search results. Reference disk files by path instead of carrying their contents.

If handoff.md or session-log.md were updated this session, reference their paths rather than restating their contents.

## Project-specific rules
<!-- Add rules specific to your project as you discover them. Examples: -->
<!-- - "All API responses must be validated against the schema before processing" -->
<!-- - "Never modify the payments table directly — use the payments service" -->
<!-- - "Run pytest after any change to src/" -->
