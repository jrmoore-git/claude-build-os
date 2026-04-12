# BuildOS Changelog — April 1-10, 2026

## What's New Since Your Last Pull

Your version (pre-April 1) had the basic framework: skills, hooks, rules, and the debate engine with single-model challenge. Here's everything that changed since then.

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

## New Skills (8 added, later consolidated to 18 total)

> **Note:** Skills were renamed and consolidated on 2026-04-11 (D12). The names below reflect the current skill names.

| Skill | What it does |
|-------|-------------|
| `/think` (discover + refine) | Full problem discovery with forcing questions, premise challenges, alternatives. Writes design doc + optional PRD generation. Refine mode = 5 quick questions for smaller tasks. |
| `/elevate` | Scope ambition review after `/think`. 4 modes: dream big, selective expansion, hold scope, strip to essentials. |
| `/polish` | 6-round cross-model collaborative improvement. Standalone on any input, or as final phase of `/challenge --deep`. |
| `/plan --auto` | Auto-detects pipeline tier from task description, chains skills with auto-decisions, surfaces taste decisions at final approval gate. |
| `/design variants` | Generate multiple AI design variants, open comparison board, collect structured feedback, iterate. |
| `/sync` | Cross-references git diff against all project docs. Fixes drift, polishes changelog voice, checks cross-doc consistency. |
| `/check --governance` | Qualitative governance hygiene scan. |
| `/check --qa` | Domain-specific QA validation. Go/no-go gate before `/ship`. |

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

## New Hooks (6 added → 17 total)

| Hook | What it prevents |
|------|-----------------|
| `hook-bash-fix-forward.py` | Bandaid debugging — blocks `rm index.lock`, `kill -9` without investigation first |
| `hook-stop-autocommit.py` | Lost work — auto-commits session progress when Claude Code stops |
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
  - `operational-context.md` — audit.db/metrics.db schemas and health queries

## Onboarding Docs (new)

- **`docs/getting-started.md`** — guided tutorial: clone → think → plan → build → check → ship
- **`docs/cheat-sheet.md`** — quick reference: pipeline tiers, all 18 skills, key files, governance shortcuts
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

## Cleanup

- Stripped all project-specific content (product references, contact names, project config)
- Archived 79 completed task artifacts
- Reduced banned-terms to secrets-only patterns (was catching false positives on common words)
- Deleted obsolete skills (pre-April names that were later consolidated)

---

## How to Update

```bash
git pull origin main
bash setup.sh
```

If you have local changes, `setup.sh` will warn before overwriting. The framework files are designed to be pulled cleanly — project-specific content lives in `docs/project-prd.md`, `tasks/`, and `.env`, which are not overwritten by sync.
