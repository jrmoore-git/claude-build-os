# The Build OS

A practical framework for building serious projects with Claude Code.

## Start Here

| You are... | Read | Skip (for now) |
|---|---|---|
| Curious what this is | This README | Everything else |
| Starting a project with Claude Code | This README → run `/setup` | Team Playbook, Advanced Patterns |
| Running a team project | README → Build OS → Team Playbook | Advanced Patterns |
| Building a production or autonomous system | Everything | Nothing |

## Quick Start

Open this repo in Claude Code and run:

```
/setup
```

It asks three questions about your project, picks a governance tier, and creates everything you need.

Or do it manually: copy `CLAUDE.md` to your project root, copy templates from `templates/` into `docs/` and `tasks/`, copy `.claude/skills/` to your project, edit `CLAUDE.md` to describe your project, and `git init`.

**Requirements:** [Claude Code](https://claude.ai/claude-code) with `/commands` support, git. Hooks need a Unix shell (macOS, Linux, WSL) but are optional for personal projects.

## Prerequisites

The pipeline skills work without any dependencies. The cross-model review engine (`/challenge`, `/debate`, `/review`, `/define`, `/elevate`) requires:

- **Python 3.x** — scripts are Python
- **[gh CLI](https://cli.github.com/)** — GitHub integration
- **[LiteLLM](https://docs.litellm.ai/)** — routes debate calls to multiple model families. All cross-model operations go through LiteLLM, which handles provider authentication, retries, and model routing.
  ```bash
  pip install litellm
  litellm --config config/litellm-config.example.yaml
  ```
- **API keys** for at least two model families (the debate engine uses adversarial review across families):
  - Anthropic (Claude) — author model
  - OpenAI (GPT-5.4) — judge and challenger
  - Google AI (Gemini 3.1 Pro) — challenger
  Copy `.env.example` to `.env` and fill in your keys. Model assignments are configured in `config/debate-models.json` — you can remap which model plays which role.
- **Verify your setup:** `python3 scripts/debate.py check-models` confirms all configured models are reachable through LiteLLM.

**Optional:**
- **[Ollama](https://ollama.ai/)** + `nomic-embed-text` — enables semantic search in `/recall`
  ```bash
  brew install ollama
  ollama pull nomic-embed-text
  ```

---

## The Pipeline

The Build OS ships with slash commands that chain into a development pipeline. The full sequence:

```
/recall → /define → /challenge → /plan → build → /review → /ship
                        ↗ /elevate (stress-test scope and ambition)
                        ↗ /debate (if architectural uncertainty)
                        ↗ /plan-design-review (if UI)
```

`/define` has two modes: `discover` (full problem discovery — forcing questions, premise challenges, alternatives, design doc) and `refine` (lightweight sanity check — 5 forcing questions, brief). It replaces the old `/think` command.

Each stage produces an artifact on disk. Each artifact feeds the next stage. Skip stages that don't apply — but understand what you're skipping and why before you skip it.

### Stage by stage: what happens, what it costs, and why it's worth it

---

#### 1. `/recall` — Load context from the last session

**What happens:** Loads your handoff (`tasks/handoff.md`), current project state (`docs/current-state.md`), and pulls relevant lessons and decisions via hybrid search (`scripts/recall_search.py`).

**Cost:** Free (local file reads + optional BM25/semantic search).

**Why it exists:** Claude sessions start from zero. Without `/recall`, you spend the first 10 minutes re-explaining what you decided last session. With it, the model picks up where you left off.

**What it produces:** Context in the conversation window. No disk artifact.

---

#### 2. `/define` — Clarify the problem before committing to a solution

**What happens:** Problem definition in two modes:

- **`/define discover`** — Full problem discovery (6 phases). Gathers context, runs a diagnostic with pushback-first forcing questions, searches for landscape awareness, challenges your premises, generates 2-3 implementation alternatives, and writes a design doc (`tasks/<topic>-design.md`). Includes an optional cross-model second opinion via `debate.py review --persona pm` — an actual external model (not a Claude subagent) evaluates your problem statement and premises independently.

- **`/define refine`** — Lightweight sanity check. Classifies the task (bugfix → auto-skip questions, write brief immediately). For features: 5 forcing questions, then writes a brief (`tasks/<topic>-think.md`).

Both modes include a spec review step. In discover mode, this is a multi-model panel review (`debate.py review-panel --personas architect,security,pm`) that catches completeness gaps and YAGNI before you start building.

**Cost:** `/define refine` is free. `/define discover` costs ~$0.03–0.10 (measured: $0.03 on a small proposal, ~35 sec of external model time). Scales with input size.

**Why it exists:** We kept building the wrong thing. Not wrong as in buggy — wrong as in solving the wrong problem. Claude is agreeable by default. Tell it "build X" and it builds X, even when what you actually need is Y. `/define` forces the model into an anti-sycophancy posture: it pushes back on your framing before accepting your conclusion. The design doc or brief it produces becomes the input to everything downstream — if the problem statement is wrong here, every subsequent stage optimizes for the wrong goal.

The discover mode goes further: it asks "is this the right problem?" before "how do we solve it?" The premise challenge (Phase 3) catches framing errors. The alternatives generation (Phase 4) prevents premature commitment to the first approach. The spec review (Phase 5.5) uses external models to catch what a single model misses.

**Skip for:** Bugfixes with obvious root causes. Docs. One-line config changes.

---

#### 3. Write or refine the PRD

**What happens:** You write (or update) `docs/project-prd.md` — the single source of truth for what you're building. Numbered sections, explicit scope, concrete examples. This isn't a formality. Every downstream stage references it.

**Cost:** Free (your time writing, or Claude drafting from the `/define` brief or design doc).

**Why it exists:** Without a PRD, Claude builds against the conversation. Conversations are lossy — they compact, they drift, they contradict themselves. A PRD on disk is stable. When `/review` checks "does this match the spec?" — the spec is the PRD. When `/challenge` asks "is this in scope?" — scope is defined in the PRD. Every ambiguity you leave in the PRD becomes a coin flip in every stage that reads it.

The PRD also survives across sessions. You can close Claude Code, come back next week, and the PRD is still there. The conversation isn't.

---

#### 4. `/elevate` — Is this ambitious enough?

**What happens:** Scope and ambition review across 11 sections: Architecture, Error & Rescue Map, Security & Threat Model, Data Flow & Edge Cases, Code Quality, Tests, Performance, Observability, Deployment, Long-Term Trajectory, and Design/UX (if applicable). Begins with a pre-review system audit and a Step 0 scope challenge.

Four modes:
- **SCOPE EXPANSION** — Dream big. "What's 10x more ambitious for 2x the effort?"
- **SELECTIVE EXPANSION** — Hold current scope as baseline, surface expansion opportunities as individual opt-ins.
- **HOLD SCOPE** — Make the current plan bulletproof. Maximum rigor, no scope changes.
- **SCOPE REDUCTION** — Find the minimum viable version. Cut everything else.

Includes an optional "outside voice" — an independent agent via `debate.py review --persona staff` that gives a brutally honest challenge after all review sections complete.

**Cost:** ~$0.01–0.05 if the outside voice runs (measured: $0.01, ~8 sec for one external model call). Free otherwise.

**Why it exists:** `/challenge` asks "should we build this?" — a gate. `/elevate` asks "are we thinking big enough?" — an amplifier. They're complementary. `/elevate` catches the opposite failure mode from overengineering: underengineering, where the plan solves today's problem but creates next quarter's nightmare. The 11 review sections map every error path, trace every data flow, and force you to answer "what breaks at 10x?"

**When to run:** After `/define discover`, before `/challenge`. Best for features where you're unsure if the scope is right — too big or too small.

**Skip for:** Bugfixes, docs, small features with obvious scope.

**What it produces:** Review findings via AskUserQuestion (one issue = one question). In EXPANSION and SELECTIVE modes, also writes `tasks/<topic>-elevate.md` with scope decisions.

---

#### 5. `/challenge` — Should we build this?

**What happens:** Three models from different families independently evaluate whether the proposed work is necessary and appropriately scoped. Model assignments are config-driven via `config/debate-models.json` — by default, GPT-5.4 and Gemini 3.1 Pro challenge as architect/security/PM, with Claude as author. Each labels findings as MATERIAL (changes the recommendation) or ADVISORY (valid but doesn't change the decision). Produces `tasks/<topic>-challenge.md` with a verdict: proceed, simplify, pause, or reject.

**Cost:** ~$0.05–0.20 per run (measured: $0.10, ~22 sec on a small proposal). Three model calls through LiteLLM. Scales with proposal size.

**Why it exists:** Claude has a documented tendency to overengineer. Tell it "add logging" and it builds a logging framework. Tell it "add a config option" and it builds a plugin system. Each addition sounds reasonable in isolation. `/challenge` catches this before you spend a session building something that should have been three lines of code.

In our project, `/challenge` has rejected or simplified roughly 40% of proposed work. Not because the ideas were bad — because the scope was wrong. The question "what breaks without this?" kills gold-plating faster than any style rule.

**Skip for:** Bugfixes, test additions, docs, trivial refactors. Go straight to `/plan`.

**What it produces:** `tasks/<topic>-challenge.md`. This is a dependency — `/plan` checks for it when it detects new abstractions or dependencies. No challenge artifact + new abstraction = the plan flags the gap.

---

#### 6. `/debate` — How should we build it?

**What happens:** Full adversarial pipeline: challenge → judge → refine. Three models rotate through all roles across multiple rounds. GPT-5.4 judges (different model family prevents self-preference bias). The output is a refined specification that has survived genuine disagreement — not rubber-stamp consensus. Produces three artifacts: `tasks/<topic>-challenge.md`, `tasks/<topic>-judgment.md`, and `tasks/<topic>-refined.md`.

**Cost:** ~$0.20–0.75 per run (measured: $0.24, ~78 sec on a small proposal). Multiple rounds, three models each round. Scales with proposal size — real architectural proposals cost 2–3x more.

**Why it exists:** Models from the same family agree with each other too easily. We measured this: when Claude reviews Claude's work, it catches surface issues but misses structural problems. When GPT reviews Claude's work, it catches different things. When all three flag the same concern, it is almost certainly real.

We added `/debate` after a schema migration that passed single-model review but would have broken two downstream consumers. The debate caught it because the Gemini challenger asked "what reads this table?" — a question Claude's self-review hadn't considered. That $0.75 debate saved a production incident.

**When to run:** Schema changes, PRD changes, new integrations, any decision where the approach isn't obvious. If you're unsure whether to debate, the cost of debating ($0.50–1.00) is almost always less than the cost of building the wrong thing.

**Skip for:** Simple features where the implementation path is clear.

**What it produces:** `tasks/<topic>-refined.md` — the spec you build against. When `/review` runs later, if this file exists, the PM lens escalates to strict spec compliance checking.

---

#### 7. `/plan` — Write the implementation spec

**What happens:** Reads the codebase, reads any `/challenge` or `/debate` artifacts, and writes `tasks/<topic>-plan.md` with YAML frontmatter:

```yaml
---
scope: "What this change does"
surfaces_affected: "What systems/files are touched"
verification_commands: "How to verify correctness"
rollback: "How to undo"
review_tier: "Tier 1|Tier 1.5|Tier 2"
---
```

**Cost:** Free (codebase analysis + file write).

**Why it exists:** This isn't documentation — it's a structural gate. `hook-plan-gate.sh` blocks commits to [protected paths](config/protected-paths.json) unless a valid plan artifact exists with verified frontmatter. The plan must exist on disk before code lands.

We added the commit-time hook after discovering that "plan before you build" as an advisory instruction was being ignored ~30% of the time. The model would read the instruction, agree it was important, and then start coding anyway. Advisory rules degrade under context pressure. A hook that blocks the commit does not degrade.

The `rollback` field is mandatory. Before you build, you must write down how to undo it. This kills the "we'll figure out rollback later" pattern — later never comes, and you discover the rollback problem after you've shipped.

**If the plan touches UI**, run `/plan-design-review` after `/plan` but before building. It rates the plan 0–10 across seven design dimensions and identifies gaps to fix before you write a line of CSS.

**If you're creating a new design system**, run `/design-consultation` first for guided competitive research and a complete design proposal.

---

#### 8. Build

**What happens:** You build. Hooks fire automatically as you work:

- Edit a Python file → `hook-syntax-check-python.sh` validates syntax, `hook-ruff-check.sh` checks complexity
- Edit a `*_tool.py` file → `hook-post-tool-test.sh` auto-runs the matching test file
- Try to edit a protected path without a plan → `hook-pre-edit-gate.sh` blocks you
- Try to write to `.env` → `hook-guard-env.sh` blocks it

You don't manage these. They just run. That's the point of level 3 on the [enforcement ladder](examples/enforcement-ladder.md).

---

#### 9. `/review` — Is the implementation correct?

**What happens:** Three external models from different families review your diff through independent lenses via `debate.py review-panel`:

1. **Architect** — Is the design sound? Are there simpler alternatives?
2. **Security** — Are there vulnerabilities, injection risks, data leaks?
3. **PM** — Does this match the spec? Are edge cases handled?

Each reviewer sees the diff with anonymous labels (Reviewer A/B/C) — no model identity leaks. Review order is randomized to prevent anchoring bias. Findings are tagged MATERIAL (must fix) or ADVISORY (worth noting).

If `tasks/<topic>-refined.md` exists from a prior `/debate`, the PM lens escalates to strict spec compliance — checking the implementation against the agreed specification, not just general quality.

Produces `tasks/<topic>-review.md` with findings grouped by lens and severity.

**Cost:** ~$0.02–0.10 per run (measured: $0.02, ~26 sec on a small diff). Three model calls through LiteLLM. Scales with diff size.

**Why it exists:** Self-review is weak. We tracked this: Claude reviewing its own code catches ~60% of issues. Adding the security lens catches injection and data-leak patterns the architect lens misses. Adding the PM lens catches spec drift the other two don't care about. The three lenses together catch roughly 85–90% of what a human staff engineer would flag.

One example: the security lens caught that we were interpolating untrusted calendar data into shell command strings — `gog gmail search "from:ATTENDEE_EMAIL"` where the attendee email came from a calendar API response. The architect lens hadn't flagged it because the code was well-structured. The security lens flagged it because it recognized the injection pattern. That's a $0.10 review that caught a real vulnerability.

If cross-model review fails (LiteLLM down, all models fail), `/review` falls back to single-model self-review through all three lenses sequentially and marks the review as `degraded`. Degraded reviews are advisory — `/ship` notes the status but doesn't block.

`hook-review-gate.sh` enforces review at commit time: Tier 1 files (high blast radius) are blocked without debate artifacts. Tier 1.5 files warn without review artifacts.

---

#### 10. `/ship` — Deploy with verification

**What happens:** Pre-flight checks, then deployment:
- Tests pass
- Review completed (artifact exists)
- Plan artifact has verified evidence (not PENDING)
- Services restart cleanly
- Smoke tests pass post-deploy

**Cost:** Free (runs your test suite and deploy scripts).

**Why it exists:** AI-assisted development creates a velocity illusion. Features land fast. Reviews pass. But the verifications happened in conversation, not in repeatable scripts. We had a production path with full unit-test coverage fail completely because the mocks encoded the wrong assumption — tests passed with confidence while the real system returned nothing. A single end-to-end smoke test would have caught it immediately.

The deploy pattern is: build → restart → verify. A feature is not done when you deploy it — it's done when the verification suite passes after deployment.

Run `/qa` before `/ship` for domain-specific validation — it's a go/no-go gate customized to your project's quality criteria.

---

#### 11. `/wrap-session` — Close the loop

**What happens:** Checks document hygiene (are decisions.md, lessons.md, session-log.md current?), writes `tasks/handoff.md` with what the next session needs to know, appends to `tasks/session-log.md`, and commits everything.

**Cost:** Free.

**Why it exists:** The handoff is what makes `/recall` work next session. Without it, your next session starts cold. The session log is your audit trail — when you need to know "why did we decide X three weeks ago?", the answer is in the log.

At ~50% context usage, use `/compact` proactively. At ~60%, write your session log. Don't wait for automatic compression — quality degrades before you notice.

---

### The full cost picture

Measured on 2026-03-28 against a 144-word test proposal routed through LiteLLM → Gemini 3.1 Pro + GPT-5.4. Real proposals are 3–10x longer; costs scale roughly linearly with input size. Time columns show external model call time — full skill time includes conversation and tool calls on top.

| Stage | Measured cost | Measured time | Estimated range | Runs per typical feature |
|-------|--------------|---------------|-----------------|------------------------|
| `/recall` | $0.00 | <1 sec | Free | Every session |
| `/define refine` | $0.00 | <1 sec | Free | Once per feature |
| `/define discover` | $0.03 | ~35 sec | $0.03–0.10 | Once per new feature/architecture |
| `/elevate` | $0.01 | ~8 sec | $0.01–0.05 | Only for scope uncertainty |
| PRD | $0.00 | — | Free (your time) | Once (updates as needed) |
| `/challenge` | $0.10 | ~22 sec | $0.05–0.20 | Once per feature |
| `/debate` | $0.24 | ~78 sec | $0.20–0.75 | Only for architecture decisions |
| `/plan` | $0.00 | <1 sec | Free | Once per feature |
| `/review` | $0.02 | ~26 sec | $0.02–0.10 | Once per feature (re-run after fixes) |
| `/ship` | $0.00 | 1–5 min | Free | Once per deploy |

**Total cost for a typical feature** (define + challenge + review): ~$0.15. For an architectural decision with full debate: ~$0.40–0.80. For a big bet with discover + elevate + debate: ~$0.50–1.00. Costs scale with proposal size — a 1,000-word proposal costs roughly 3–5x more than the measurements above. The cost of *not* running the pipeline — building the wrong thing, missing a vulnerability, shipping without rollback — is orders of magnitude higher.

---

### Choosing your path

Not every task needs every stage. Here are the common routes:

| Change type | Path | Cost |
|---|---|---|
| Bugfix | `/recall` → `/define refine` → `/plan` → build → `/review` → `/ship` | ~$0.02 |
| Small feature | `/recall` → `/define refine` → `/challenge` → `/plan` → build → `/review` → `/ship` | ~$0.12 |
| New feature | `/recall` → `/define discover` → `/challenge` → `/plan` → build → `/review` → `/ship` | ~$0.15 |
| UI feature | `/recall` → `/define discover` → `/challenge` → `/plan` → `/plan-design-review` → build → `/design-review` → `/review` → `/ship` | ~$0.17 |
| Architectural change | `/recall` → `/define discover` → `/challenge` → `/debate` → `/plan` → build → `/review` (with spec compliance) → `/ship` | ~$0.40 |
| Big bet | `/recall` → `/define discover` → `/elevate` → `/challenge` → `/plan` → build → `/review` → `/ship` | ~$0.50–1.00 |
| New design system | `/recall` → `/define discover` → `/design-consultation` → `/plan` → `/plan-design-review` → build → `/design-review` → `/ship` | ~$0.17 |
| Docs or config only | `/recall` → edit → `/wrap-session` | Free |

---

### All commands reference

| Command | What it does |
|---------|-------------|
| /setup | Bootstrap a new project — picks governance tier, creates all files |
| /recall | Session start — loads handoff, current state, relevant lessons and decisions |
| /define discover | Full problem discovery — forcing questions, premise challenge, alternatives, design doc |
| /define refine | Lightweight sanity check — 5 forcing questions, brief. Pass-through for bugfixes |
| /elevate | Scope and ambition review — 11 sections, 4 modes (expand/selective/hold/reduce) |
| /challenge | "Should we build this?" Cross-model gate. Produces artifact that /plan checks |
| /debate | Full adversarial pipeline — challenge, judge, refine across model families |
| /plan | Research the system, write a plan to disk with verified frontmatter |
| /review | Three-lens cross-model review (Architect, Security, PM) before committing |
| /ship | Deployment pre-flight — gates on passing tests and completed review |
| /qa | Domain-specific quality validation — go/no-go gate before deployment |
| /design-consultation | Guided design system creation — competitive research, SAFE/RISK breakdown |
| /design-review | Visual QA — 94-item checklist, AI slop detection, letter grades, fix loop |
| /plan-design-review | Rate a plan 0-10 across 7 design dimensions, fix gaps before building |
| /triage | Classify incoming information and route to decisions, lessons, tasks, or reference |
| /capture | Extract decisions, lessons, and action items from conversations before they're lost |
| /sync | Update PRD, decisions, lessons, and current state after approved changes |
| /handoff | Write what the next session needs to know |
| /audit | Two-phase audit — blind discovery first, then targeted questions from evidence |
| /status | Current project status, workflow stage, recommended next action |
| /wrap-session | End-of-session — document hygiene, handoff, session log, commit |

---

## Under the Hood

The skills are powered by deterministic scripts and enforcement hooks. See [How It Works](docs/how-it-works.md) and [Hooks Reference](docs/hooks.md) for full details.

**Scripts:**

| Script | What it does | Used by |
|--------|-------------|---------|
| debate.py | Cross-model engine with 7 subcommands: `challenge`, `judge`, `refine`, `review`, `review-panel`, `check-models`, plus the full pipeline. Config-driven model assignments via `config/debate-models.json` | /challenge, /debate, /review, /define, /elevate |
| multi_model_debate.py | Three-model parallel debate with rotation refinement | /debate skill |
| model_conversation.py | Persistent multi-model conversation manager | multi_model_debate.py |
| tier_classify.py | Classifies files by blast radius and review tier | hook-review-gate, hook-tier-gate |
| recall_search.py | BM25 + semantic hybrid search across governance files | enrich_context.py |
| finding_tracker.py | Tracks debate findings through open → addressed lifecycle | artifact_check.py |
| enrich_context.py | Enriches proposals with relevant lessons and decisions | Standalone CLI (pre-challenge) |
| artifact_check.py | Validates plan, challenge, judgment, review artifacts | Standalone CLI |
| verify_state.py | Governance hygiene — checks rule size, decision count, lesson count | hook / session close |

**Hooks:**

| Hook | When it fires | What it gates |
|------|--------------|---------------|
| hook-plan-gate.sh | Before commit to protected paths | Requires valid plan artifact with verified frontmatter |
| hook-review-gate.sh | Before commit | Blocks Tier 1 without debate artifacts; warns for Tier 1.5 and risk-flagged Tier 2 |
| hook-tier-gate.sh | Before file edit (Write/Edit) | Blocks Tier 1 edits without debate artifacts; warns for Tier 1.5 |
| hook-decompose-gate.py | Before Write/Edit (first per session) | Blocks writes until decomposition assessed; blocks main-session writes after parallel plan (must dispatch agents or bypass with reason); fail-closed on corrupt state |
| hook-agent-isolation.py | Before Agent dispatch (when plan_submitted) | Requires isolation: "worktree" on write-capable agents; exempts read-only subagent types |
| hook-guard-env.sh | Before .env writes | Blocks .env modification and credential management commands |
| hook-pre-edit-gate.sh | Before Write/Edit on protected paths | Requires plan or proposal artifact |
| hook-post-tool-test.sh | After *_tool.py edits | Auto-runs pytest on changed test files |
| hook-prd-drift-check.sh | Before commit | Warns when decisions are unsynced to project docs |
| hook-pre-commit-tests.sh | Before git commit | Blocks commit if pytest fails |
| hook-ruff-check.sh | After Python write/edit | Ruff complexity and line-length check (advisory) |
| hook-syntax-check-python.sh | After Python write/edit | Python syntax validation (advisory) |

---

## Rules

`.claude/rules/` files are loaded conditionally — more authoritative than CLAUDE.md, less rigid than hooks. The Build OS ships seven:

| Rule file | What it governs |
|-----------|----------------|
| code-quality.md | Anti-overengineering, anti-slop vocabulary, input validation patterns |
| design.md | AI slop detection checklist for generated UI |
| orchestration.md | When and how to decompose into parallel agents; decomposition gate enforcement |
| review-protocol.md | Three-stage review: challenge → debate → review |
| session-discipline.md | Plan gates, document-first protocol, context budget |
| skill-authoring.md | Output silence, cron contracts, query bounds |
| workflow.md | Orient → document → verify → decompose → self-improve |

---

## Why This Exists

Most writing about AI assistants still lives in the world of prompt engineering: how to ask better questions, how to provide better context, how to get cleaner code back. Those questions matter. But once Claude starts participating in real engineering work, they stop being the main event.

The teams getting real leverage from Claude aren't the ones writing cleverer prompts. They're the ones defining where the model is allowed to reason, where it is not allowed to act, and how the system behaves when the model is wrong.

That shift — from prompting to governance — is the difference between dabbling and building. And it is still under-discussed.

---

### The first mistake: treating Claude like a chatbot

Most people interact with Claude Code the way they'd interact with a smart colleague in a chat window. Ask a question, get an answer, ask a follow-up. That works for small tasks. It falls apart the moment you're building anything with state, persistence, or consequences.

The problem isn't Claude's intelligence. It's that sessions do not retain memory unless you externalize it. Every session starts from zero. There is no accumulated context, no institutional knowledge — unless you build it yourself. A human colleague remembers what you decided last week. Claude doesn't.

So the first investment isn't a better prompt. It's a better operating environment: a PRD that defines what you're building, a decisions log that records what you've already settled, a lessons log that prevents repeating mistakes. These are just files — markdown on disk — but they transform Claude from an amnesiac assistant into something that operates against a stable specification. The Build OS ships templates for all of these in `templates/` and the `/setup` skill creates them for you.

But persistent files are only half the answer. A pile of markdown is not memory until it is queryable. Serious Claude workflows need a retrieval layer — whether that is search, an indexed notes system, or a bootstrap skill — that loads the right slice of context before planning begins. That's what `recall_search.py` and the `/recall` skill do: BM25 keyword search across your governance files, so every session starts with the relevant slice of context, not everything or nothing. The `/recall` skill supports both keyword (BM25) and semantic search (via local embeddings) — so retrieval finds conceptually related context, not just exact matches.

**But retrieve selectively.** The default instinct is to compensate with huge prompts that load every doc. That backfires — the model hallucinates consistency with stale context instead of inspecting current state. `CLAUDE.md` should be the only always-loaded layer. Everything else should be pulled in on demand by relevance.

The gap between "using Claude" and "building with Claude" is the same gap between having a conversation and running a project. Conversations are stateless. Projects have memory, governance, and accountability.

---

### The most important decision: where the model stops

The single most important architectural choice in an AI system is not which model to use. It's where the model stops and deterministic software begins.

We learned this the hard way. After enough build sessions, we discovered that multiple critical components had the LLM constructing raw SQL queries with string interpolation from untrusted input. Each one looked reasonable in isolation. Together, they were a disaster waiting to happen — one malformed update in an approval workflow could approve the wrong item, send the wrong email, or corrupt the wrong record.

The fix wasn't better prompting. It was architectural: build a deterministic toolbelt that handles all data operations with parameterized queries and state validation. The LLM's job shrinks to classifying, summarizing, and drafting. It produces structured JSON. Deterministic code validates the schema and applies the change. If the LLM hallucinates, the worst outcome is "draft not created" — not "data corrupted."

A subtler version of the same mistake: asking the model to "extract only the important items" from a large document. The model silently skips things. The fix is two-pass extraction — first ask the model to list ALL candidates without filtering, then ask it to classify the full list. Separating "find everything" from "evaluate each" prevents lazy omission.

This boundary question extends to data. **Provenance beats plausibility.** The model must not invent source data. Names, emails, identifiers, and metrics must come from verified systems of record. The model may transform, summarize, classify, or route data — but it must never fabricate authoritative facts, even when they sound plausible. If you find yourself wondering whether the model made something up, your boundary is drawn in the wrong place.

The one-line rule: if the LLM can cause irreversible state changes, it must not be the actor. In the Build OS, this boundary is enforced architecturally: the scripts in `scripts/` are deterministic tools — `tier_classify.py` classifies files, `finding_tracker.py` manages state transitions, `artifact_check.py` validates artifacts — and Claude never calls external APIs directly.

---

### The hidden lever: move state to disk

The context window is RAM: scarce, expensive, and ephemeral. The filesystem is durable memory. Treat them accordingly.

Plans, decisions, reviews, state tracking — all belong on disk. Not in conversation history, which vanishes on compaction. Not in Claude's "memory," which doesn't exist between sessions. On disk, where any session can read it and no session can lose it.

This sounds obvious, but the natural workflow fights it. When you're moving fast in a Claude Code session, everything lives in the conversation. Decisions get made conversationally. Plans exist as chat messages. Review results float in the output. Then the session ends, or the context compacts, and it's gone.

The discipline: every decision gets written to decisions.md. Every lesson gets written to lessons.md. Every session writes a handoff document. Every plan gets written to a task file before execution starts. The context window is for active reasoning. The filesystem is for everything that needs to survive. The `/sync`, `/capture`, and `/handoff` skills automate this — they make writing to disk the default, not the exception.

The Build OS takes this further with validated artifacts. Plan files have YAML frontmatter with required fields — scope, rollback path, verification commands — and a commit-time hook validates the frontmatter before allowing changes to protected paths. The plan isn't just documentation; it's a structural gate. The same pattern applies to findings: `finding_tracker.py` manages an append-only JSONL file where each finding has a state machine (open → addressed/waived/obsolete). State lives on disk, not in conversation.

Two operational corollaries:

- **Restart after rule or config changes.** If you update `CLAUDE.md`, rules files, or `.env`, start a fresh session. Running sessions loaded the old config at startup and will silently ignore your changes. This is one of the most common "why isn't my rule working?" issues.
- **Compact proactively.** Use `/compact` at roughly 50–70% of context usage. Quality degrades subtly as context bloats — the model starts contradicting its own earlier work before you notice.

---

### The difference between guidance and governance

Instructions in CLAUDE.md are suggestions. Claude will probably follow them. Under context pressure, in complex workflows, during long sessions — it may not.

Hooks are policy.

Claude Code supports hooks — shell commands that fire automatically before or after specific events. A PostToolUse hook that runs your test suite after every code edit doesn't rely on Claude remembering to test. A PreToolUse hook that blocks commits when tests fail doesn't rely on Claude's judgment about whether tests matter right now.

This distinction generalizes into what I think of as the enforcement ladder:

1. **Advisory** — CLAUDE.md instructions. "Please follow this convention." Works most of the time.
2. **Rules** — `.claude/rules/` files. Loaded conditionally, more authoritative. Works more reliably.
3. **Hooks** — Deterministic code. Fires every time. Cannot be ignored.
4. **Architecture** — The system physically cannot do the wrong thing. LLM never sees the database. Secrets never enter the context.

The Build OS ships twelve hooks that implement level 3: `hook-plan-gate.sh` blocks commits to protected paths without a valid plan artifact, `hook-review-gate.sh` blocks Tier 1 commits without debate artifacts, `hook-tier-gate.sh` blocks file edits to high-risk files without prior review, `hook-pre-edit-gate.sh` requires a plan artifact before writing to protected paths, `hook-pre-commit-tests.sh` blocks commits when tests fail, `hook-agent-isolation.py` blocks write-capable Agent dispatches without worktree isolation after a parallel plan is declared, and five more covering decomposition reminders, env file protection, post-edit testing, PRD drift detection, linting, and syntax validation. Each is configured as a Claude Code hook — deterministic shell scripts that fire before or after the matched tool executes. See [Hooks Reference](docs/hooks.md) for the full specification.

Most teams stop at level 1 and wonder why Claude keeps breaking their conventions. The answer: move the important rules up the ladder.

A practical example: we had a model invent an email address from a person's name and company context. An advisory rule saying "do not hallucinate contact data" did not stop it. Deterministic validation did. That is the enforcement ladder in one sentence.

If you've told Claude to do something three times and it keeps not doing it, stop writing stronger instructions. Escalate to the next enforcement level.

A practical escalation pattern: if the same behavior has been corrected three times at the same level, promote it. Lesson → rule → hook → architecture. A lesson that keeps recurring is not a lesson — it's a missing rule. A rule that keeps being violated is not a rule — it's a missing hook.

Four principles that keep the ladder honest:

- **Automate mechanical procedures.** Restarting a service, running a test suite, collecting artifacts — these are repeatable steps that should be scripted immediately, not managed through repeated prompts. A forgotten restart is not a judgment error; it's a missing script.
- **Treat hooks as a security boundary.** Hooks run arbitrary commands with user permissions. A `.claude/settings.json` committed to a repo can execute commands the moment Claude Code opens it. Review hook configs the way you would review CI scripts — they are privileged code.
- **Verify your verifiers.** Gates that check accumulated history files will eventually always pass because the file has grown large enough to contain the keyword. Gates must check for fresh artifacts tied to the current change, not accumulated history. Before trusting any gate: ask what would cause it to always pass.
- **Watch for gate gaming.** If bypass flags like `[TRIVIAL]` or `[CHALLENGE-SKIPPED]` appear frequently, the trigger criteria are miscalibrated. Track bypass frequency and adjust thresholds.
- **Prune governance regularly.** Every rule has a maintenance cost. A lessons log that only grows is recording failures, not preventing them. Institutional memory is not append-only — lessons and rules must be promoted, consolidated, or retired. Target ≤30 active lessons. Governance bloat creates the same drift it was meant to prevent.

---

### The default failure mode: complexity drift

Anthropic's own documentation acknowledges it: Claude Opus has "a tendency to overengineer by creating extra files, adding unnecessary abstractions, or building in flexibility that wasn't requested."

This is the single most important behavioral tendency to understand. Claude sounds confident and reasonable while doing it. "I've added a factory pattern for extensibility." "I've created a helper utility for reuse." "I've added comprehensive error handling." Each addition sounds defensible. Collectively, they turn a 50-line script into a 400-line architecture that nobody asked for.

The antidote is active simplicity. After every plan review: "What can I remove and still meet the requirement?" Anthropic provides specific anti-overengineering language that Claude is trained to follow — use it verbatim in your configuration rather than paraphrasing, because the model responds to those exact phrases more reliably than to rewrites.

The Build OS operationalizes this with `/define` and `/challenge`. `/define` forces problem clarity before solutions — its forcing questions ("What's the current workaround? What's the smallest version?") prevent scope creep at the idea stage. `/challenge` is a pre-planning gate where multiple external models independently evaluate whether proposed work is necessary. The default posture is skepticism: the simplest version wins unless there's evidence otherwise. For features where scope is uncertain, `/elevate` stress-tests ambition in the opposite direction — ensuring you're not underbuilding.

A related discipline: mandatory decomposition analysis before parallelizing work. Before spawning parallel agents, the plan must list every subtask with its write targets, identify dependencies, and justify the execution strategy. "Sequential because it's simpler" is not a justification — cite the specific task property (shared files, output dependency, or genuine independence). This started as advisory guidance and was ignored for months. Three escalation levels (lesson → rule → stronger rule) failed. Only `hook-decompose-gate.py` — a PreToolUse hook that physically blocks `Write|Edit` until decomposition is assessed — changed the behavior. A companion hook, `hook-agent-isolation.py`, completes the enforcement: after a parallel plan is declared, it blocks write-capable Agent dispatches that lack `isolation: "worktree"`, ensuring the model can't simply spawn non-isolated agents. If a rule matters, enforce it mechanically.

But the deeper point is that style rules alone don't solve this. If the architecture gives the LLM a large, unconstrained surface to operate on, you'll get entropy — just simpler entropy. The real defense is architectural: shrink the surface. Move deterministic operations out of LLM control. Then simplicity rules apply to a much smaller, more manageable area.

---

### The missing discipline: testing, rollback, and release control

AI-assisted development creates a dangerous velocity illusion. Every session ships working features, each with ad-hoc verification during the build. Reviews pass. Commits land. The system grows. But those verifications are ephemeral — they happened in conversation, not in repeatable test scripts.

We saw a production path with strong unit-test coverage fail completely because the tests were validating the wrong assumption at the integration boundary. The API returned one shape, the code expected another, and the mocks mirrored the broken expectation. The tests passed with full confidence while the real system quietly returned nothing. A single end-to-end smoke test would have caught it immediately.

The lesson: your mocks encode your assumptions. If your assumptions are wrong, your tests validate the wrong thing perfectly.

Testing, rollback capability, and release discipline aren't separate from the AI development workflow — they're more important because of it. Build test infrastructure in the first session, not the fiftieth. Require a rollback path before any deployment. Use kill switches for anything that runs autonomously. The Build OS encodes this: every plan artifact requires a `rollback` field, and `debate.py` runs cross-model adversarial review so critical changes are stress-tested before they land (see [How It Works](docs/how-it-works.md)).

The Build OS ships eight contract tests that verify structural invariants: idempotency, approval gating, audit completeness, degraded mode visibility, state machine validation, rollback path existence, version pinning, and exactly-once scheduling. These are not unit tests — they verify that the system's safety properties hold regardless of what features change. Add domain-specific invariants on top.

The deploy pattern is: build → restart services → run smoke tests → verify. `deploy_all.sh` chains these steps and fails fast if any check fails. Never declare a feature done by deploying — declare it done when the verification suite passes after deployment.

**The real completion criterion is boundary verification.** Component tests validate assumptions. The final acceptance gate is verification at the production boundary — where the system actually meets users, dependencies, and infrastructure. If the change has not been verified there, it has not been fully verified. The deployment process defines "done."

The same is true of model cost. One team discovered a $724 day against a roughly $15 expected budget because every scheduled job defaulted to the strongest model. Nothing was technically broken; the routing policy was. Cost discipline is not a billing cleanup exercise. It is architecture.

---

### Design as a first-class concern

Generated UI has a distinctive failure mode: it looks plausible at a glance and falls apart under scrutiny. Purple gradient backgrounds. Three-column feature grids with icons in colored circles. Centered everything. Body text under 16px. Generic hero copy. We call this "AI slop" — and it is the visual equivalent of complexity drift.

The Build OS includes a design governance layer: `/design-consultation` for creating design systems through guided competitive research, `/design-review` for visual QA with a 94-item checklist and letter grades, and `/plan-design-review` for rating implementation plans across seven design dimensions before building.

The 94-item checklist catches specific patterns: missing hover/focus states, inconsistent border radius, more than three font families, `outline: none` without a replacement focus indicator. Each pattern has a concrete test. The review produces letter grades (A-F) per category and a prioritized fix list. The goal is not aesthetic perfection — it is catching the patterns that make generated UI feel generated.

---

### Cross-model review: adversarial by design

The most important insight from running cross-model debate in production: models from the same family agree with each other too easily. Self-preference bias is real and measurable.

The Build OS uses adversarial review across model families. All cross-model operations route through `debate.py` → LiteLLM → external providers — these are genuine independent evaluations from different model families, not Claude subagents pretending to be independent.

**Config-driven model assignments.** `config/debate-models.json` defines which model plays which role. The default mapping assigns Gemini 3.1 Pro and GPT-5.4 as challengers, GPT-5.4 as judge, and rotates all three families during refinement. You can override per-persona or globally. `debate.py check-models` verifies your configuration is reachable.

**Anti-bias constraints.** Reviewers see anonymous labels (Reviewer A, B, C) — never model identity. Position in the review order is randomized (`random.shuffle`) to prevent anchoring bias. Model names never appear in prompts or stdout.

**Tiered review architecture.** Not every review needs a full panel:
- **Single-persona review** (`debate.py review`): one external model, one lens. Used by `/define` (Phase 3.5 second opinion) and `/elevate` (outside voice). Fast and cheap.
- **Multi-persona panel** (`debate.py review-panel`): 2-3 external models reviewing independently through different lenses. Used by `/define` (Phase 5.5 spec review) and `/review` (full code review). More thorough, still ~$0.05-0.15.

The practical benefit: when three models from different families all flag the same concern, it is almost certainly real. When only one flags something, it is worth discussing but may be model-specific bias. Cross-model agreement is a stronger signal than single-model confidence.

---

### Skill authoring: the discipline behind slash commands

Skills are markdown files with YAML frontmatter — they are prompts with structure. Writing a good skill is closer to writing a good runbook than writing a good prompt.

Three hard-won patterns:

**Output silence.** Between tool calls, a skill must not emit reasoning text. No "I'll check the database now..." No "Here are the results..." The only user-visible output is the single formatted block at the end. Intermediate narration clutters the interface and creates double-render bugs when the same content appears in both the agent stream and the final delivery.

**Query bounds.** Every skill that queries external data must have explicit limits: max result count, max content size per result, and a scope filter (time window, account, category). Before shipping a skill, answer: "If every query returns its maximum, how many tokens does one run consume?" If unbounded, the skill is not ready.

**Cron output contracts.** Skills that run on a schedule must produce zero output when there is nothing to report — not "No items found," not "All clear," literally nothing. A skill that outputs "nothing to report" on every quiet run generates noise that trains users to ignore it. Empty result means silent exit.

---

### The practical starter kit

If you do nothing else:

1. **Create a PRD in Markdown** that Claude references every session. Numbered sections, explicit scope, concrete examples. → Copy [`templates/project-prd.md`](templates/project-prd.md) to `docs/project-prd.md` and fill it in. See [`examples/reference-project/docs/project-prd.md`](examples/reference-project/docs/project-prd.md) for a worked example. `CLAUDE.md` tells Claude to read it before every plan.

2. **Plan before building.** Write the plan to a file. Review it. Then execute. → Run `/plan`. It writes `tasks/<topic>-plan.md` with YAML frontmatter (scope, rollback, verification). [`hook-plan-gate.sh`](hooks/hook-plan-gate.sh) blocks commits to protected paths without one.

3. **Challenge before planning.** New features and abstractions go through `/challenge` first — a "should we build this?" gate that prevents scope creep. For architectural uncertainty, `/debate` runs adversarial cross-model review. Skip both for bugfixes and docs. → See [Workflow: Choosing your path](#choosing-your-path) above.

4. **Review after building.** `/review` runs your diff through three lenses (Architect, Staff+Security, PM) before you commit. If a `/debate` spec exists, the PM lens checks strict compliance. [`hook-review-gate.sh`](hooks/hook-review-gate.sh) enforces this at commit time for high-risk files.

5. **Keep a lessons log — and prune it.** Every surprise, every mistake, numbered and referenceable. Promote recurring lessons to rules. Archive one-offs. Target ≤30 active entries. → Copy [`templates/lessons.md`](templates/lessons.md). The three-strikes rule: if the same lesson appears three times, promote it to a [rule](examples/rules/) or a [hook](hooks/). `/capture` extracts lessons from conversations before they're lost.

6. **Draw the LLM boundary.** LLMs classify, summarize, and draft. Deterministic code acts. Source data comes from verified systems, never model inference. → The scripts in [`scripts/`](scripts/) are the deterministic layer — `tier_classify.py` classifies, `finding_tracker.py` manages state, `artifact_check.py` validates. Claude never calls external APIs directly.

7. **Write to disk, not context.** Plans, reviews, decisions — all go to files. Restart sessions after config changes. Compact early. → `/recall` loads from disk at session start. `/capture`, `/sync`, and `/handoff` write back. `/wrap-session` ensures nothing is lost at close. Templates for every artifact type are in [`templates/`](templates/).

8. **Use hooks for enforcement.** If a rule matters, don't phrase it as guidance. Enforce it as code. Verify gates can actually fail. → Eleven hooks ship in [`hooks/`](hooks/), wired in [`.claude/settings.json`](.claude/settings.json). See the [enforcement ladder](examples/enforcement-ladder.md) for when to use advisory rules vs. hooks vs. architecture.

9. **Ship with verification, not hope.** `/qa` validates domain rules. `/ship` gates on passing tests, completed review, and post-deploy smoke tests. Unit tests help, but production-boundary verification is the real completion criterion. → [`scripts/deploy_all.sh`](scripts/deploy_all.sh) chains build → restart → verify. [`tests/contracts/`](tests/contracts/) verifies the eight structural invariants.

10. **Set cost limits before you start.** Token budgets, iteration caps, and spending alerts are not optional in agentic workflows. → [`.claude/rules/skill-authoring.md`](.claude/rules/skill-authoring.md) requires query bounds on every skill. Route by task type: classification → cheapest model, synthesis → mid-tier, high-stakes → strongest. See [`config/litellm-config.example.yaml`](config/litellm-config.example.yaml) for model routing.

---

Using Claude is conversational. Building with Claude is operational.

The teams that will get the most leverage from AI coding tools over the next few years won't be the ones with the best prompts. They'll be the ones that figured out governance: where to draw the boundary, what to put on disk, which rules to enforce deterministically, and how to keep the system simple as it grows.

The model keeps getting smarter. The discipline around it is what you have to build yourself.

---

## Further Reading

- **[The Build OS](docs/the-build-os.md)** — The full framework: governance tiers, file system, operations, enforcement ladder, review, bootstrap
- **[How It Works](docs/how-it-works.md)** — Technical internals for every script: debate.py, tier_classify.py, recall_search.py, finding_tracker.py, enrich_context.py, artifact_check.py
- **[Hooks Reference](docs/hooks.md)** — Complete specification for all enforcement hooks: plan-gate, review-gate, tier-gate, and eight more
- **[Platform Features](docs/platform-features.md)** — Claude Code features the Build OS uses: hooks, rules, skills, settings
- **[File Ownership](docs/file-ownership.md)** — Which files belong to which layer: governance, enforcement, templates, config
- **[Team Playbook](docs/team-playbook.md)** — For engineering teams: agent teams, parallel work, orchestration, cheat sheets
- **[Advanced Patterns](docs/advanced-patterns.md)** — For production systems: audit protocol, degradation testing, cross-model debate, failure classes
- **[Contract Tests](docs/contract-tests.md)** — The eight structural invariants and how to verify them
- **[Operating Reference](docs/Operating-Reference.md)** — Day-to-day operations: session lifecycle, context management, deployment
- **[Review Protocol](docs/review-protocol.md)** — Three-stage review pipeline: challenge, debate, review
- **[Skill Contract Standard](docs/SKILL-CONTRACT-STANDARD.md)** — How to write skills: frontmatter, output contracts, query bounds
- **[Infrastructure](docs/infrastructure.md)** — Dependencies, setup, and verification

---
