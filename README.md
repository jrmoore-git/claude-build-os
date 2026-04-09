# The Build OS

A governance framework for multi-session development with Claude Code.

Build OS gives you a PM, designer, architect, engineering team, cross-model review panel, and release engineer — in a box. Product thinking comes first: a PM defines the problem and a designer shapes the experience. Then engineering takes over: an architect evaluates the approach, engineers build against a plan, three models from different families review the code through independent lenses (PM, Security, Architecture), and a release engineer runs pre-flight gates before deploying. Each stage is backed by a slash command that Claude Code can run, writing artifacts that the next stage picks up.

> **Use Build OS if** you're doing multi-session work with Claude Code and need persistent memory, clear boundaries, and enforceable rules.
> **Skip it if** you're doing one-off prompting or single-session tasks.

---

## In 30 Seconds

- **State lives on disk, not in chat.** Plans, decisions, and lessons go to files. The context window is RAM; the filesystem is memory.
- **The model proposes; deterministic code acts.** LLMs classify, summarize, and draft. Software mutates data, calls APIs, and enforces approvals.
- **Rules escalate into enforcement.** When guidance fails, promote it: lesson → rule → hook → architecture.
- **Define what before planning how.** Scope the problem before designing the solution. Build against a plan, not a conversation.

---

## The Pipeline

Build OS structures work as a pipeline. Product thinking defines the *what*; engineering delivers the *how*.

```mermaid
flowchart LR
    subgraph Product["🎯 Product Thinking"]
        direction TB
        A[Define] --> B[Design]
    end
    subgraph Engineering["⚙️ Engineering"]
        direction TB
        C[Challenge] --> D[Plan]
        D --> E[Build]
        E --> F[Review]
        F --> G[Ship]
    end
    Product --> Engineering
```

| Stage | Role | Skills | Output |
|---|---|---|---|
| **Define** | PM | `/define`, `/elevate` | Design doc or brief — the *what* and *why* |
| **Design** | Designer | `/design-consultation`, `/design-review`, `/design-shotgun` | Visual direction, UX review, design variants |
| **Challenge** | Architect | `/challenge`, `/debate` | Cross-model review — *should we build this?* |
| **Plan** | Lead Engineer | `/plan`, `/autoplan` | Implementation plan — the *how* |
| **Refine** | Cross-model panel | `/refine` | 6-round iterative improvement across 3 model families |
| **Build** | Engineer | *(you + Claude Code)* | Working code against the plan |
| **Review** | Cross-model panel | `/review` | Three models review through PM, Security, and Architecture lenses |
| **Ship** | Release Engineer | `/ship` | Pre-flight gates (tests, review, verify, QA) → deploy → post-deploy smoke |

Not every task uses every stage. The framework scales with risk:

| Task type | Pipeline |
|---|---|
| **Bugfix** | `/plan` → build → `/review` → `/ship` |
| **Small feature** | `/define refine` → `/plan` → build → `/review` → `/ship` |
| **New feature** | `/define discover` → `/challenge` → `/plan` → build → `/review` → `/ship` |
| **Big bet** | `/define discover` → `/elevate` → `/challenge` → `/plan` → build → `/review` → `/ship` |

All tiers can optionally use `/refine` on plans or designs before building. Design skills (`/design-consultation`, `/design-review`, `/plan-design-review`) slot in where needed — they're not mandatory pipeline stages.

Two distinct multi-model workflows: **`/debate`** is adversarial (personas attack → judge rules → collaborative refine). **`/refine`** is standalone collaborative improvement (6 rounds across 3 model families, no personas or judgment). Use `/debate` when you need to pressure-test whether something is right. Use `/refine` when you have something and want it better.

The key insight: **Define** (what are we building and why?) is a different activity from **Plan** (how do we build it?). Skipping the first leads to well-planned solutions to the wrong problem.

---

## Quick Start

```bash
git clone https://github.com/jrmoore-git/claude-build-os.git
cd claude-build-os
./setup.sh
```

`setup.sh` detects your platform, finds Python 3.11+, installs git hooks, copies templates, and writes a config cache. No interactive prompts — everything auto-detected. Then open Claude Code and run `/setup` to configure your project.

**Requirements:** [Claude Code](https://claude.ai/claude-code), git, Python 3.11+, Unix shell (macOS or Linux).

---

## Prerequisites

Build OS scales its infrastructure requirements with the governance tier. Tier 0–1 needs nothing beyond Claude Code and git. Cross-model skills need more.

### Tier 0–1: Just Claude Code

- [Claude Code](https://claude.ai/claude-code) (CLI, desktop, or IDE extension)
- git

Skills that work out of the box: `/define`, `/elevate`, `/plan`, `/autoplan`, `/ship`, `/recall`, `/wrap-session`, `/capture`, `/status`, `/doc-sync`, `/governance`, `/qa`, `/design-consultation`, `/design-review`, `/design-shotgun`, `/plan-design-review`, `/triage`, `/setup`.

### Tier 2+: Cross-Model Review

The `/challenge`, `/debate`, `/refine`, and `/review` skills send proposals to three different model families for independent review. This requires a proxy that routes requests to each provider.

**You need:**

1. **Python 3.11+** — runs hooks, the debate engine, and utility scripts
2. **API keys from three providers:**
   - [Anthropic](https://console.anthropic.com/) (Claude — PM persona)
   - [OpenAI](https://platform.openai.com/) (GPT — judge + security persona)
   - [Google AI](https://aistudio.google.com/) (Gemini — architect persona)
3. **LiteLLM** — an open-source proxy that presents a single OpenAI-compatible endpoint and routes to the correct provider based on model name:
   ```bash
   pip install 'litellm[proxy]'
   ```
4. **OpenAI Python SDK** — used by `llm_client.py` to talk to LiteLLM (since LiteLLM exposes an OpenAI-compatible API):
   ```bash
   pip install openai
   ```

### Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/jrmoore-git/claude-build-os.git
cd claude-build-os

# 2. Copy example configs
cp .env.example .env
cp config/litellm-config.example.yaml config/litellm-config.yaml

# 3. Edit .env — add your API keys
#    ANTHROPIC_API_KEY=your-anthropic-key
#    OPENAI_API_KEY=sk-...
#    GEMINI_API_KEY=AI...
#    LITELLM_MASTER_KEY=sk-buildos-local-1234  (any string you choose)

# 4. Edit config/litellm-config.yaml — update model names to match your access
#    The example maps debate persona names to specific provider models.
#    Change gpt-4.1 to your available OpenAI model, etc.

# 5. Start LiteLLM
litellm --config config/litellm-config.yaml
# Runs on http://localhost:4000. Leave this terminal open.

# 6. In a new terminal, verify models are reachable
python3 scripts/debate.py check-models
```

If `check-models` shows all three models as reachable, cross-model skills will work. If a model fails, check the API key and model name in your config.

### What works without this setup

| Setup level | What works |
|---|---|
| **Claude Code + git only** | All skills except `/challenge`, `/debate`, `/refine`, `/review`. Full governance framework, session management, planning, design, and shipping. |
| **+ LiteLLM + API keys** | Cross-model review and refinement. Three models independently challenge, judge, refine, and review your work. |

You can start at Tier 0 and add cross-model review later. The framework doesn't break without it — you just won't have multi-model review until you set it up.

### Optional: Web Research (You.com Search API)

Gives `/define discover`, `/elevate`, and `/design-consultation` access to live web search for competitive research, landscape analysis, and design inspiration.

```bash
# Get an API key at https://you.com/search-api
# Add to .env:
YOU_COM_API_KEY=ydc-sk-...
```

**Fallback:** Without this, skills fall back to Claude's built-in WebSearch tool. If that's also unavailable (e.g., running in a restricted environment), skills skip web research and proceed with Claude's training knowledge only. The core pipeline (`/challenge`, `/debate`, `/review`, `/ship`) never uses web search.

### Optional: Semantic Search (Ollama)

Gives `/recall` semantic similarity search for finding conceptually related lessons and decisions, even when they don't share exact keywords.

```bash
brew install ollama    # or see https://ollama.ai/
ollama pull nomic-embed-text
# Add to .env:
OLLAMA_HOST=http://localhost:11434
```

Ollama runs locally — no data leaves your machine. The `nomic-embed-text` model is ~274MB.

**Fallback:** Without this, `/recall` uses BM25 keyword search, which works well for exact term matches but misses conceptually related results.

### Optional: Headless Browser (for `/design-review`, `/design-consultation`)

Gives design skills the ability to take screenshots, inspect live pages, and run visual QA.

**Fallback:** Without a browser, design skills work from web search results and built-in design knowledge. Visual QA (`/design-review`) requires a browser — it will report "browser unavailable" without one.

---

## Why This Exists

Most people start by treating Claude Code like a chat window with tools: ask, reply, refine, repeat. That works for small tasks. It breaks once the work has state, history, and consequences.

The problem is rarely "the model is dumb." The problem is that without a system, each session starts close to zero. Specifications, decisions, and lessons that lived only in chat disappear with the window. Build OS fixes that by making the project legible on disk: a PRD for scope, decision logs for settled choices, lessons for mistakes not to repeat, and task files for current work.

The job shifts from "write a better prompt" to "build a better operating environment."

---

## The Session Loop

Within each stage of the pipeline, every Build OS session follows the same loop:

```mermaid
flowchart LR
    A[Recall] --> B[Plan]
    B --> C[Execute]
    C --> D[Verify]
    D --> E[Document]
    E --> F[Sync]
    F -->|next session| A
```

| Step | What happens |
|---|---|
| **Recall** | Load prior context from disk: PRD, decisions, lessons, last handoff |
| **Plan** | Write the approach to a file before building |
| **Execute** | Implement against the plan |
| **Verify** | Prove it works — tests, output, screenshots, manual checks |
| **Document** | Capture decisions and lessons |
| **Sync** | Update the PRD and task state; save the handoff for the next session |

Chat is a poor place to store project state. A written plan, a numbered lesson, or a logged decision can be reloaded, cited, reviewed, and enforced later. That is the difference between "Claude helped with a task" and "Claude is operating inside a system."

---

## What Lives on Disk

Build OS keeps project state in a predictable file structure. Tier 0 needs only `CLAUDE.md` and git. Here is a typical layout for Tier 1 and above:

```
project-root/
├── CLAUDE.md                  # Top-level instructions for Claude
├── .claude/
│   ├── rules/                 # Rules loaded automatically each session
│   │   └── no-raw-sql.md
│   └── skills/                # Slash commands Claude can invoke
│       ├── define/
│       ├── plan/
│       ├── review/
│       └── ship/
├── docs/
│   ├── prd.md                 # Product requirements — the source of truth
│   ├── decisions.md           # Numbered decision log with rationale
│   └── lessons.md             # Numbered lessons from mistakes
├── tasks/
│   ├── current.md             # Active task: goal, plan, status, blockers
│   └── handoff.md             # What the next session needs to know
└── tests/                     # At least one smoke test (Tier 2+)
```

| File | Purpose | Updated when |
|---|---|---|
| `CLAUDE.md` | Project-wide instructions and constraints | Setup; major scope changes |
| `docs/prd.md` | What you're building and why | Scope changes approved by human |
| `docs/decisions.md` | Settled choices with rationale | Any non-trivial "why" is resolved |
| `docs/lessons.md` | Mistakes and surprises, numbered | Something unexpected happens |
| `tasks/current.md` | Active task with plan and status | Every session |
| `tasks/handoff.md` | Context for the next session | End of every session |
| `.claude/rules/` | Standing rules Claude must follow | A lesson gets promoted |
| `.claude/skills/` | Reusable procedures as slash commands | A workflow gets formalized |

**The key principle:** if it must survive the session, it belongs in a file.

---

## The Enforcement Ladder

Memory gives you continuity. The enforcement ladder gives you control.

Instructions in `CLAUDE.md` are guidance. Claude will often follow them. Under time pressure, ambiguous context, or competing goals, guidance alone may not hold. Why? Because the model is not executing a fixed procedure — it is predicting the next best action from a limited context window. The model is not malicious; it is probabilistic. Deterministic checks are stronger than advisory text.

```mermaid
flowchart BT
    A["1 — Lesson · Written down once, advisory"] --> B["2 — Rule · Loaded from .claude/rules/"]
    B --> C["3 — Hook · Deterministic script, fires every time"]
    C --> D["4 — Architecture · Structurally impossible to violate"]
```

A concrete example: telling the model "do not hallucinate contact data" does not reliably stop it from inventing an email address from a person's name and company. A validation hook that checks generated addresses against a real source does. If a rule matters, reduce discretion.

> If you've told Claude to do something three times and it still gets missed, stop rewriting the instruction. Move it up the ladder.

---

## Governance Tiers

Start at the lowest tier that matches your risk. Move up when the stakes increase.

| Tier | You're building... | What you add |
|---|---|---|
| **0 — Advisory** | Personal projects, learning, solo exploration | `CLAUDE.md` + git + human review |
| **1 — Structured** | Multi-session projects, anything lasting >1 week | + PRD, decisions log, lessons log, handoff |
| **2 — Enforced** | Production systems, real users, financial consequences | + hooks, contract tests, review protocol |
| **3 — Production OS** | Autonomous agents, acts on your behalf, sensitive data | + cross-model review, kill switches, approval gating |

**What goes wrong if you stay too low:**

- **Tier 0:** You lose context between sessions, repeat old decisions, and spend the start of every session re-explaining the project.
- **Tier 1:** Docs exist, but nothing forces compliance. The model skips tests or makes risky edits because the rules are only advisory.
- **Tier 2:** Code changes are controlled, but the system can still take expensive or high-impact actions unless approvals and shutdown paths are explicit.

> **Upgrade triggers:**
> Lost context between sessions → **Tier 1**.
> Claude made risky changes without review → **Tier 2**.
> The system acts on your behalf → **Tier 3**.

---

## Parallel Work and Multi-Agent Teams

Build OS is designed for parallelization. When a task has three or more independent components, it should be decomposed into parallel agents rather than executed sequentially.

```mermaid
flowchart TD
    A[Lead Agent] -->|defines interfaces| B[Foundation Wave]
    B --> C[Agent 1: Backend routes]
    B --> D[Agent 2: Frontend components]
    B --> E[Agent 3: Database migrations]
    C --> F[Integration & Review]
    D --> F
    E --> F
```

**Decomposition gate:** A hook blocks the first write in each session until you assess whether the task should be parallelized. Three or more independent file groups? Decompose. One tightly coupled change? Proceed normally. This enforces the habit because Claude defaults to sequential execution even when tasks are clearly independent.

**How it works in practice:**

- **Subagents** run within a session. They accept a task, execute it, and report back. They can't communicate with each other. Use them when work is cleanly decomposable.
- **Agent teams** spawn independent sessions with shared task lists and teammate coordination. Use them when agents need to share findings or coordinate on interfaces during execution.
- **Worktree isolation** gives each parallel agent its own git checkout, preventing file collisions and merge conflicts. Write-capable agents running in parallel must use worktree isolation — this is not optional.

**The critical rule:** define interface contracts *before* agents spin up. If two agents build components that interact, the lead must write the contract as a file both sides reference. Without this, you get multiple agents producing plausible code that doesn't integrate. The pattern: foundation wave (shared schema, types, stubs) → parallel execution.

For the full guide — spawn prompts, token budgets, custom agent definitions, and orchestration patterns — see the [Team Playbook](docs/team-playbook.md).

---

## The Skills

Build OS ships with 24 skills — slash commands that implement the pipeline stages. Think of them as the team members you'd want on a real project:

| Role | Skills | What they do |
|---|---|---|
| **PM** | `/define`, `/elevate`, `/status` | Problem discovery, scope review, project status |
| **Designer** | `/design-consultation`, `/design-review`, `/design-shotgun`, `/plan-design-review` | Design system, visual QA, variant exploration, plan design audit |
| **Architect** | `/challenge`, `/debate` | Cross-model gate ("should we build this?"), adversarial review |
| **Refiner** | `/refine` | 6-round cross-model collaborative improvement on any document |
| **Lead Engineer** | `/plan`, `/autoplan` | Implementation planning, auto-tier detection |
| **Reviewer** | `/review` | Cross-model code review (3 lenses: PM, Security, Architecture). `--fix` auto-fixes mechanical issues. `--fix-loop` runs fix → re-review cycles (max 3 iterations). |
| **QA** | `/qa`, `/governance` | Domain-specific QA validation, governance hygiene |
| **Release** | `/ship`, `/doc-sync` | Pre-flight gates (verify + QA + tests + review) → deploy → doc sync |
| **Session** | `/recall`, `/wrap-session`, `/capture`, `/triage` | Bootstrap, session close, knowledge capture, info routing |

Running `/define` → `/challenge` → `/plan` → build → `/review` → `/ship` gives you the equivalent of a PM defining scope, an architect stress-testing the approach, engineers building, a cross-model review panel checking quality, and a release engineer running pre-flight gates before deploying. `/ship` includes verification (adversarial probes), QA dimensions, and all other gates inline — the standard path is `/review` → `/ship`, not a longer chain. Each skill writes artifacts to disk so the next stage (or session) picks up where the last one left off. Pipeline progress is tracked in manifest files (`tasks/<topic>-manifest.json`) so you can see which stages have completed for any topic.

**Recent additions (v3.1):** Challengers get optional read-only verifier tools (`--enable-tools`) to check claims against the actual codebase. Quantitative claims must be tagged as EVIDENCED, ESTIMATED, or SPECULATIVE — speculative claims alone can't drive material verdicts. `/review --fix-loop` automates the fix → re-review cycle. Proposals use a structured template with mandatory sections (Current System Failures, Operational Context, Baseline Performance) to prevent challengers from fabricating numbers.

You don't need all of them. Start with `/plan` and `/review`. Add the rest as your workflow matures.

---

## Common Pitfalls

**Scope creep through helpfulness.** Claude will often add features, abstractions, or "improvements" you didn't ask for. The model optimizes for being helpful, not for staying in scope. The PRD and task file are your defense: if it's not in scope, it doesn't ship.

**Confident but wrong mocks.** Claude will generate mocks based on its understanding of an API, which may be outdated or incorrect. A test suite can pass perfectly while validating the wrong behavior. Keep at least one smoke test that hits the real integration path.

**Cost discipline is architecture.** A budget written in a doc is not a control. If every scheduled job defaults to the strongest model, your "policy" is fiction. Limits and routing need to exist in code.

---

## Starter Kit

If you do nothing else:

**Essential:**
1. **Create a PRD** that Claude references every session. Numbered sections, explicit scope, clear non-goals.
2. **Define before planning.** Articulate *what* you're building and *why* before designing *how*.
3. **Plan before building.** Write the plan to a file. Review it. Then execute.
4. **Write to disk, not context.** Plans, reviews, decisions, and handoffs all go to files.

**Add as you scale:**
5. **Keep a lessons log.** Record every surprise and mistake, numbered and referenceable.
6. **Draw the LLM boundary.** LLMs classify and draft. Deterministic code validates and acts.
7. **Use hooks for enforcement.** If a rule keeps getting missed, enforce it in code.
8. **Test from day one.** Create the test directory alongside `git init`, not after the first incident.

---

## Staying Updated

Build OS is actively maintained. Rules, hooks, skills, and scripts improve as we learn from real multi-session projects. To pull improvements:

```bash
git pull origin main
./setup.sh   # re-runs safely — idempotent, won't overwrite your files
```

`setup.sh` only copies templates to `docs/` and `tasks/` if the destination doesn't already exist. Your project-specific files (PRD, decisions, lessons) are never overwritten. Updated hooks, skills, rules, and scripts take effect immediately.

**What updates include:** New skills, hook improvements, better debate prompts, portability fixes, new contract tests, and documentation. **What never changes:** Your project files, `.env`, or `config/litellm-config.yaml`.

---

## Docs Map

| You want to... | Read |
|---|---|
| **Understand the philosophy** | [Why Build OS Exists](docs/why-build-os.md) — the narrative case for governance over prompting |
| **Learn the full framework** | [The Build OS](docs/the-build-os.md) — governance tiers, file system, operations, enforcement, memory, review, bootstrap |
| **Run a team project** | [Team Playbook](docs/team-playbook.md) — agent teams, parallel work, orchestration, cheat sheets |
| **Build a production system** | [Advanced Patterns](docs/advanced-patterns.md) — audit protocol, degradation testing, cross-model debate, failure classes |
| **Understand Claude Code features** | [Platform Features](docs/platform-features.md) — hooks, rules, skills, memory, session management |

---

The model keeps getting smarter. The discipline around it is what you still have to build yourself.
