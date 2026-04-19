# BuildOS Changelog — April 2026

## What's New Since Your Last Pull

Your version (pre-April 1) had the basic framework: skills, hooks, rules, and the debate engine with single-model challenge. Here's everything that changed since then.

---

## At-a-glance summary

| Category | Count | Examples |
|---|---|---|
| **New skills** | 8 added (22 total after consolidations) | `/prd`, `/audit`, `/guide`, `/healthcheck`, `/triage`, `/log`, `/research`, `/sync` |
| **New hooks** | 11 added (22 total) | `hook-context-inject`, `hook-decompose-gate`, `hook-skill-lint`, `hook-spec-status-check`, `hook-session-telemetry`, `hook-post-build-review` |
| **New rules** | 6 added | `natural-language-routing`, `orchestration`, `bash-failures`, `session-discipline`, `code-quality`, `review-protocol` |
| **New config** | `config/debate-models.json`, `config/protected-paths.json` | Centralizes model→persona mapping and protected-path enforcement |
| **Skill renames** | 3 (affects invocation) | `/check` → `/review`, SPIKE verdict → INVESTIGATE, `/sim*` archived |
| **Breaking for downstream** | 2 | `cmd_judge` JSON fields (`spiked` → `investigating`), `/check` command removed in favor of `/review` |
| **Archived** | Sim ecosystem (`sim_compiler.py`, `eval_intake.py`) | Superseded by D22 — iterative critique loop replaces automated simulation |

**Operator action required:**

1. Re-run `./setup.sh` to sync templates and hook wiring
2. If you used `/check`, switch to `/review`
3. If you parse `cmd_judge` JSON output, update field names: `spiked` → `investigating`, `spikes` → `investigations`
4. If you rely on sim ecosystem scripts, check `archive/sim-retrospective.md` for replacement patterns

---

## Fixes For The Issues You Flagged

### "Exploration felt truncated"

- **Truncation detection** — if a model's response is <60% of expected length, the output is discarded and retried. Prevents half-finished reviews from being treated as complete.
- **"Inspect before acting" rule** — consolidated 6+ scattered exploration guidance fragments into one rule. Before answering "can we do X?" or "does this support Y?", the model must grep/read the code first. No more "I don't think this supports..." without actually checking.

### "Reviews didn't ground themselves in the code"

- **Verifier tools** (`debate_tools.py`, 517 lines, entirely new) — challengers and reviewers can now *check the code* before making claims. 6 read-only tools:
  - `check_code_presence` — does a function/pattern actually exist?
  - `read_file_snippet` — read up to 50 lines of actual source code
  - `count_records` — how many audit entries match?
  - `read_config_key` — what does the config actually say?
  - `get_job_schedule` — is this cron job actually configured?
  - `get_cost_trend` — what are the real cost numbers?
- **Forced tool use** — GPT and Gemini get `tool_choice: required` on their first turn, forcing them to actually use the verifier tools before commenting.
- **Evidence tagging** — judge prompt now requires `[EVIDENCE: verified]` or `[EVIDENCE: unverified]` tags on each finding. Unverified claims get weighted down in the final judgment.
- **Deny-by-default data egress** — tools return structured metadata only, never raw DB rows or secrets.

---

## Debate Engine — Major Overhaul

The cross-model debate engine (`debate.py`) got the most significant changes:

- **Per-model routing** — Claude gets `tool_choice: auto`, GPT/Gemini get `tool_choice: required` on first turn. Per-model temperature (Gemini=1.0 for creative divergence, others=0.0 for precision).
- **Fix-loop** — after judge rules, findings marked "addressed" are tracked and don't resurface in subsequent rounds.
- **Per-stage timing** — each challenger, consolidation phase, and judge call logs elapsed time to stderr. Visible in test output for performance tracking.
- **MRO-aware retry logic** — walks Python class hierarchy so `APITimeoutError` (subclass of `APIConnectionError`) gets caught properly. No more silent failures on transient errors.

## LLM Client — New Shared Infrastructure

`llm_client.py` (629 lines, entirely new) replaces per-file urllib boilerplate:

- 3-function API: `llm_call()` (returns text), `llm_call_json()` (returns parsed JSON), `llm_call_raw()` (returns dict with content, model, usage)
- Structured `LLMError` with categories: timeout, rate_limit, auth, network, parse
- Retries transient errors (429, 5xx, network) with exponential backoff (3 attempts)
- Rollback path via `BUILDOS_LLM_LEGACY=1` env var

## New Skills (8 added, later consolidated to 22 total)

> **Note:** Skills were renamed and consolidated on 2026-04-11 (D12). The names below reflect the current skill names.

| Skill | What it does |
|-------|-------------|
| `/think` (discover + refine) | Full problem discovery with forcing questions, premise challenges, alternatives. Writes design doc + optional PRD generation. Refine mode = 5 quick questions for smaller tasks. |
| `/elevate` | Scope ambition review after `/think`. 4 modes: dream big, selective expansion, hold scope, strip to essentials. |
| `/polish` | 6-round cross-model collaborative improvement. Standalone on any input, or as final phase of `/challenge --deep`. |
| `/plan --auto` | Auto-detects pipeline tier from task description, chains skills with auto-decisions, surfaces taste decisions at final approval gate. |
| `/design variants` | Generate multiple AI design variants, open comparison board, collect structured feedback, iterate. |
| `/sync` | Cross-references git diff against all project docs. Fixes drift, polishes changelog voice, checks cross-doc consistency. |
| `/review --governance` | Qualitative governance hygiene scan. |
| `/review --qa` | Domain-specific QA validation. Go/no-go gate before `/ship`. |

## PRD Generation (Phase 6.5 of `/think discover`)

After problem discovery, `/think` now offers to generate a PRD from the conversation:

- **Three paths:** generate from design doc, validate a user's existing draft, or skip
- **PRD template expanded** from 6 to 9 sections:
  - New: Acceptance criteria (Given/When/Then format, machine-verifiable)
  - New: Constraints (non-functional requirements the AI can't infer from omission)
  - New: Verification plan (how to prove each requirement works)
- **3 gap-filling questions** target the sections most often left vague
- **Open Questions** from the design doc surface during follow-ups; unresolved ones go to a PRD appendix

## Parallelization Infrastructure

- **Agent isolation hook** — blocks Agent dispatch without worktree isolation when a parallel plan is active. Prevents file collisions.
- **Decompose gate** (Python, 224 lines) — blocks first Write/Edit until decomposition is assessed. Forces "how many independent components?" before diving in.
- **Orchestration rules** — maximize fan-out (default failure mode is under-parallelization), worktree isolation mandatory for write agents, relative paths enforced in prompts.

## New Hooks (6 added → 17 total, later 22)

| Hook | What it prevents |
|------|-----------------|
| `hook-bash-fix-forward.py` | Bandaid debugging — blocks `rm index.lock`, `kill -9` without investigation first |
| `hook-memory-size-gate.py` | Memory bloat — blocks writes when memory index exceeds 150 lines |
| `hook-agent-isolation.py` | File collisions — blocks parallel agents without worktree isolation |
| `hook-decompose-gate.py` | Under-parallelization — blocks coding before assessing decomposition |
| `pre-commit-banned-terms.sh` | Credential leaks — blocks commits containing API keys or secrets |

## Rules & Reference Docs

- **`bash-failures.md`** (new) — diagnostic sequences for common errors, prohibited bandaid patterns
- **`security.md`** (new) — secrets handling, trust boundaries, MCP supply chain evaluation
- **`reference/` subdirectory** (new) — lazy-loaded domain rules:
  - `platform.md` — macOS/Docker/Node/Python quirks
  - `code-quality-detail.md` — bulk mutations, SQLite pitfalls, testing patterns
  - `operational-context.md` — debate-log.jsonl health queries

## Onboarding Docs (new)

- **`docs/getting-started.md`** — guided tutorial: clone → think → plan → build → check → ship
- **`docs/cheat-sheet.md`** — quick reference: pipeline tiers, all 22 skills, key files, governance shortcuts
- **`examples/pulse/`** — complete worked example project (PRD, decisions, lessons, current-state)
- **`docs/why-build-os.md`** — explains the problem BuildOS solves
- **`docs/PERSONAS.md`** — model persona assignments and routing rationale
- **`docs/model-routing-guide.md`** — when to use which model

## Clone-and-Go Infrastructure

- **`setup.sh`** — one-command bootstrap for new clones
- **GitHub Actions CI** — banned-terms scan on every push
- **Portable Python paths** — all hardcoded paths replaced with `resolve-python.sh`
- **`.env.example`** — template for required environment variables
- **`buildos-sync.sh`** — manifest-based sync between BuildOS and downstream projects

## Cleanup (April 1-10)

- Stripped all project-specific content (product references, contact names, project config)
- Archived 79 completed task artifacts
- Reduced banned-terms to secrets-only patterns (was catching false positives on common words)
- Deleted obsolete skills (pre-April names that were later consolidated)

---

# April 11-16, 2026

## Sim Ecosystem Archived

The `/simulate` skill and all simulation infrastructure (sim_driver.py, sim_compiler.py, sim_pipeline.py, sim_persona_gen.py, sim_rubric_gen.py, eval_intake.py, critique_spike.py) were moved to `archive/sim/`. Skill count went from 23 → 22. The sim ecosystem was shelved after evaluation showed insufficient value relative to complexity.

## New Skills: /prd, /audit, /guide, /healthcheck

- `/prd` — extracted from `/think` Phase 6.5 as a standalone skill for PRD generation/validation
- `/audit` — two-phase blind discovery for codebase review
- `/guide` — intent-based skill map ("what can I do?")
- `/healthcheck` — learning system health check (lesson velocity, promotion rate, staleness)

Total skills: **22** (after /simulate removal and 4 additions).

## Debate Engine Improvements

- **Explore model rotation** — each direction in `/explore` is now generated by a rotating model from `explore_rotation` config, instead of all directions using a single model. Better diversity across directions.
- **Multi-model pressure-test** — `/pressure-test` now supports cross-family synthesis.
- **Per-model timing** (`per_model_timing`) — tracks elapsed time per model call, logged to debate-log.jsonl.
- **Judge flexibility** — `mapping:` field is now optional in `cmd_judge` and `cmd_verdict`.
- **debate_tools.py** — manifest-based tool verification, multi-glob search, scan-match test discovery. Eliminates false claims by challengers.

## New Hooks (5 added → 22 total)

| Hook | What it does |
|------|-------------|
| `hook-context-inject.py` | Injects test file summary, import signatures, and git history before Python edits (T0) |
| `hook-read-before-edit.py` | Warns when editing a file not recently read in session (T0) |
| `hook-skill-lint.py` | Validates SKILL.md frontmatter after writes |
| `hook-spec-status-check.py` | Warns on spec files missing `implementation_status` |
| `hook-error-tracker.py` | Tracks recurring Bash errors for proactive `/investigate` routing |

## Tier-Aware Hooks

- All hooks now read `<!-- buildos-tier: N -->` from CLAUDE.md via `scripts/read_tier.py`
- T0 hooks (always active): guard-env, read-before-edit, syntax-check, ruff-check, context-inject
- T1 hooks (tier >= 1): intent-router, spec-status-check, prd-drift-check
- T2 hooks (tier >= 2): all remaining enforcement hooks
- Hooks self-disable above the declared tier — new projects start with less friction

## Scope Containment

- Plans can now include `allowed_paths` in frontmatter — a list of path globs the agent is permitted to edit
- `hook-pre-edit-gate.sh` enforces the scope, blocking writes outside allowed paths
- `scope_escalation: true` downgrades blocks to warnings for cases where the agent must go outside scope

## Design Skill Mode Split

`/design` SKILL.md was split into 4 separate mode files: `mode-consult.md`, `mode-review.md`, `mode-variants.md`, `mode-plan-check.md`. The main SKILL.md is now a thin router. Reduces context waste — only the active mode's instructions are loaded.

## Context Optimization

- **Silent cache hit** in `hook-context-inject.py` — dedup cache prevents re-reading the same file's context on repeat edits
- **Spike cleanup** — removed test-mode-split skill (experimental, no longer needed)
- **Reference docs moved to on-demand loading** — 4 reference files (`code-quality-detail.md`, `debate-invocations.md`, `operational-context.md`, `security-external-updates.md`) moved from `.claude/rules/reference/` to `docs/reference/`, reducing auto-loaded context

## Orchestrator Contract

New `docs/orchestrator-contract.md` defines the interface contract for conductor-style orchestration. Specifies how to spawn agents, define interfaces, and coordinate parallel work.

## Frame Lens + Judge/Refine Frame Directives (April 16-18)

Three-stage effort to fix "confidently wrong" output from the debate pipeline by adding frame-level critique at each stage.

- **Frame persona (4th `/challenge` lens)** — critiques the candidate set itself: binary framings, missing compositional candidates, source-driven inheritance (proposal inherits its source's frame), problem inflation. Default model: `claude-sonnet-4-6`. With `--enable-tools`, frame expands to two parallel challengers: `frame-structural` (tools off, reasons from proposal alone) and `frame-factual` (tools on, verifies proposal claims against codebase). Factual half uses a different model family (`frame_factual_model`, default `gpt-5.4`) for diversity. Validated across n=5 historical proposals: dual-mode caught ~30 novel MATERIAL findings beyond the 3-persona panel and flipped one verdict from REVISE to REJECT (proposal targeted a feature already shipped).
- **Judge-stage FRAME CRITIQUE + novelty gate** — after evaluating challenger findings, judge runs a second pass against the proposal to surface frame-level defects no challenger raised. Novelty gate requires judge to (1) state the concrete fix, (2) scan existing findings for the same fix, (3) suppress as "covered" if redundant. Validated n=11 + negative control + 3 novelty-gate re-runs, 0 fabrications.
- **Refine-stage FRAME CHECK with mutually-exclusive channel rule** — each refine round surfaces frame concerns through three filters (load-bearing, out-of-scope-for-refine, not-already-covered). Fixed concerns → Review Notes. Unfixed → Frame Check. Never both. Calibrated v1→v5 against a 5-proposal benchmark (v2 had 0/6 detection, silent failure caught only by building the benchmark).
- **Dual-mode generalization audited** — architect ADOPTS dual-mode (5/5 BIDIRECTIONAL). Security DECLINES at 5/5 threshold (passed 4/5). PM DECLINES (2/5; value comes from prompt-level reasoning, not codebase verification). Pattern: dual-mode benefit correlates with how much a persona's value comes from codebase verification vs prompt-level reasoning.
- **SPIKE verdict renamed INVESTIGATE** — plain English, aligns with `/investigate` skill. Breaking change to judge CLI JSON fields (`spiked` → `investigating`). No external consumer reads them.
- **Judge-stage Frame-reach audit: DECLINE.** Reusable harness shipped as `scripts/judge_frame_orchestrator.py`. Intake-check subcommand exists as a composable primitive but is NOT wired into `/challenge` as a pre-check — severity drift + factual-FP asymmetry make MATERIAL count an unreliable reject/proceed signal.

Evidence: decisions D28-D31; lessons L43, L46, L47. See `.claude/rules/review-protocol.md` Stage 1 for operator-facing spec.

## Other Changes

- README rewritten to lead with the enforcement ladder; collapsed detail for adoption
- Foundation audit: 21 decisions audited, posture floors shipped for challenge pipeline
- 41 new debate.py tests, integration test cleanup
- Conviction gate archived to `archive/conviction-gate/`
- `/start` fixed: verify before recommending, show results not process
- `/ship` expanded with pre-flight gate details
- Global tone rule added (`~/.claude/CLAUDE.md`) to counter Opus 4.7 register mirroring; BuildOS CLAUDE.md adopts "Plain language in chat output" operating rule
- Rule banning wall-clock time estimates (`tasks/session-discipline.md`) — use effort units (files, tool calls, review rounds, S/M/L)

---

## How to Update

```bash
git pull origin main
bash setup.sh
```

If you have local changes, `setup.sh` will warn before overwriting. The framework files are designed to be pulled cleanly — project-specific content lives in `docs/project-prd.md`, `tasks/`, and `.env`, which are not overwritten by sync.
