---
topic: next-build-priorities-v2
created: 2026-04-15
---
# Next Build Priorities — Post-Linter (v2, enriched context)

## What Build OS Is

Build OS is a governance framework for building with Claude Code. It treats Claude as a governed subsystem inside a real engineering workflow — not a chatbot you prompt harder. The core philosophy: "The model may decide; software must act." LLMs classify, summarize, and draft. Deterministic code performs state transitions.

The framework consists of:
- **22 skills** (`.claude/skills/*/SKILL.md`) — composable procedures that Claude follows for specific tasks (e.g., `/challenge` runs cross-model evaluation before planning, `/review` runs cross-model code review, `/plan` writes implementation plans). Skills are markdown files with YAML frontmatter that define procedures, safety rules, and completion criteria.
- **A cross-model debate engine** (`scripts/debate.py`, 4,136 lines) — the shared backend that powers 5+ skills. It calls Claude, GPT, and Gemini via LiteLLM to run challenge panels, code reviews, iterative refinement, and exploration. Subcommands: `challenge`, `judge`, `refine`, `review`, `explore`, `pressure-test`, `pre-mortem`, `check-models`.
- **17 hooks** in `hooks/` — shell/Python scripts wired to Claude Code events (PreToolUse, PostToolUse, UserPromptSubmit) that enforce rules at runtime (plan gates, review gates, decomposition, skill linting, etc.).
- **Rules** in `.claude/rules/` — governance rules loaded into every Claude Code session (code quality, security, orchestration, review protocol, workflow, session discipline).
- **Tracking docs** — `tasks/decisions.md`, `tasks/lessons.md`, `tasks/session-log.md`, `tasks/handoff.md`, `docs/current-state.md` — persistent state that survives across sessions.

This is a solo developer project. The user builds and iterates on Build OS itself, and also uses it as the governance layer for other projects.

## The Arc: Sessions 6-10

The last 5 sessions followed a discovery arc:

1. **Session 6:** Built `/simulate` V1 (smoke-test + quality-eval modes for validating skills). Battle-tested it. Began V2 design for a "skill compiler simulator" that would compile SKILL.md into interaction models and simulate users.

2. **Sessions 7-8:** Built all 16 files for V2 sim-compiler (sim_compiler.py, sim_persona_gen.py, sim_rubric_gen.py, sim_driver.py + tests + reference IRs). Then questioned whether it drives real impact. Discovery:
   - Smoke-test of all 22 skills revealed 18/22 missing Safety Rules, 7/22 missing Output Silence — **structural rot** in skill files was the dominant problem, not conversation-flow bugs.
   - Cross-model panel + Perplexity research: IR extraction (compiling procedures into structured interaction models) is genuinely novel (no existing tools do this). But the 3-agent simulation loop is commodity (DeepEval, LangSmith, MLflow all have it).
   - **Pivot decision:** Structural linting is highest-leverage next move. Keep IR extraction as a differentiated technique. Don't invest further in simulation scaffolding.

3. **Session 9:** Studied gstack's skill validation system + ran Perplexity research on prompt quality/structured authoring/drift detection. Drafted the canonical SKILL.md sections spec — defining exactly what sections every skill must have (two tiers: Utility skills need 4 sections, Workflow skills need 8). Cross-model refined the spec through 3 rounds (Gemini → GPT → Claude).

4. **Session 10:** Built the linter (`scripts/lint_skills.py`, 246 lines), fixed all 22 skills to pass (116 violations → 0 using 4 parallel worktree agents), wired a PostToolUse hook that warns on violations after skill edits. Self-review passed: 0 material findings, 3 advisory.

## Problem

The linter is built and working. Four items are carried forward from prior sessions. Need to evaluate which are worth building next — or whether infrastructure investment should pause.

## Candidates

### Candidate 1: Wire IR extraction into pre-commit diff
**What it is:** `sim_compiler.py` (376 lines) extracts structured interaction models from SKILL.md procedures — states, transitions, branching paths, tool calls. This was identified as the "differentiated asset" in sessions 7-8 (Perplexity confirmed: no existing tools extract structured IRs from agent procedures).

**What wiring it would require:**
- Generate reference IRs for 19 more skills (only 3 exist: explore, investigate, plan)
- Define what constitutes a "breaking" IR change vs. a benign one
- Build the diff logic that compares current extraction to reference
- Wire into pre-commit hook

**What it would catch:** Procedure-level drift — when a skill's logic changes (lost branching paths, changed tool-calling patterns, removed error handling) even though its section headings remain intact. The linter catches section-level drift; IR extraction catches logic-level drift.

**Current state:** sim_compiler.py exists, has 26 passing tests, but is not wired to any automated workflow. No one is manually running it.

### Candidate 2: Linter hardening
**What it is:** Two small improvements to `scripts/lint_skills.py` (246 lines, 9 validation checks):
- **Regex fix:** Current `## Output` check uses `^##\s+Output\b` which matches `## Output Contract` — a heading that exists in skill-authoring rules. May or may not be a bug (Output Contract IS an output spec section, so matching it could be correct). Needs investigation before changing.
- **Automated tests:** 9 checks with 0 tests. Each check needs a positive case (violation detected) and negative case (clean file passes). ~18 test cases total.

**Why it matters:** The linter runs on every SKILL.md write/edit via PostToolUse hook. If a check has a false positive, it creates noisy warnings that erode trust. Tests prevent regressions and are needed before promoting the hook to a hard pre-commit gate.

### Candidate 3: debate.py test coverage
**What it is:** `scripts/debate.py` is 4,136 lines with 12+ subcommands, 0 tests. It's the cross-model engine powering `/challenge`, `/review`, `/polish`, `/explore`, `/pressure-test`, and more.

**Recent activity (last 5 days, commits touching debate.py):**
- Gemini timeout hardening: per-model timeout + automatic fallback
- Challenge synthesis: structured extract-then-classify replaces prose rewrite
- Refine critique mode: document-type-aware refinement for pressure-tests
- LiteLLM graceful degradation: single-model fallback via ANTHROPIC_API_KEY
- Fall back to WebSearch when Perplexity unavailable instead of skipping
- Fix 3 inline temperature violations
- Per-stage timing instrumentation
- Debate engine sync + pre-mortem fold
- Explore-gate refinement
- Debate engine refactor evaluation

That's **10+ substantive changes in 5 days**. Despite this, no bugs have been reported from production usage (runs 5-10 times/day).

**Testability:** Much of debate.py calls external LLM APIs, which makes unit testing expensive (mocking 3 different API providers). However, pure-function utilities (argument parsing, prompt assembly, log formatting, persona routing, config loading) could be tested without any mocking.

### Candidate 4: sim-compiler /review
**What it is:** 4 scripts from sessions 7-8 that were never code-reviewed: sim_compiler.py, sim_persona_gen.py, sim_rubric_gen.py, sim_driver.py.

**Context:** Sessions 7-8 explicitly decided persona_gen, rubric_gen, and driver are commodity (industry tools already do this). Only sim_compiler.py (IR extraction) was kept as worth investment. Reviewing 3 scripts the project has decided not to invest in is low-value. sim_compiler.py review makes sense only if IR extraction is being actively wired (Candidate 1).

## Proposed Approach
Build Candidate 2 (linter hardening) — the only item with concrete scope, a known issue, and direct relevance to the just-built infrastructure. The others are either speculative (Candidate 1), insurance for stable code (Candidate 3), or work on deprioritized code (Candidate 4).

## Simplest Version
Investigate the `## Output` regex to determine if it's actually a bug. If so, fix it. Write ~18 test cases for the 9 linter checks. Done.

### Current System Failures
- **Linter:** No failures observed (just built in session 10). The `## Output` regex false-positive risk was identified during self-review as an advisory finding — it hasn't actually caused a problem yet.
- **debate.py:** No failures despite 10+ substantive changes in 5 days and daily production usage.
- **sim-compiler:** Mostly unused — no failures because no one runs it.
- **IR extraction:** Never wired, so no failures from absence.

### Operational Context
- Linter runs on every SKILL.md write/edit via PostToolUse hook (fires ~2-5 times per session when editing skills)
- debate.py runs ~5-10 times/day across challenge, review, explore, polish, pressure-test
- sim_compiler.py is not wired to any hook or automated workflow
- 22 skills conform to canonical spec as of session 10 (116 violations fixed)
- The project has been in an infrastructure-building phase for 5 sessions straight

### Baseline Performance
- Linter: 22/22 skills passing, 0 violations, 9 validation checks, tier classification working, PostToolUse hook fires correctly
- debate.py: functional, 4,136 lines, 12+ subcommands, 0 tests, 10+ recent substantive changes, no reported bugs
- sim-compiler: 376 lines, 26 passing tests, built but unused in any automated workflow
