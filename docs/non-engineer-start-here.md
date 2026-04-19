# Start Here (No Engineering Background Needed)

BuildOS is a set of tools inside [Claude Code](https://claude.ai/claude-code) that helps you plan projects, track decisions, and build things without losing context between sessions. You don't need to be an engineer to use it — but what you get depends on how far into setup you go.

This page shows you what works at each step.

---

## What BuildOS does, in plain words

Claude forgets everything between sessions. BuildOS gives it a memory: files on disk that record what you're building, what you've decided, and what you've learned. Then it adds a pipeline — problem discovery, planning, review, shipping — that Claude walks through with you.

You describe what you want. BuildOS routes you to the right tool.

---

## Level 1: The browser version (zero setup)

**You need:** A [claude.ai](https://claude.ai) account.

**What works:** You can talk to Claude about your project and ask it to do BuildOS-style thinking — problem discovery, planning, reviewing — by describing what you want. You get most of the thinking style, but not the persistence and enforcement that make BuildOS durable.

**What doesn't:** No disk-based memory between sessions. No automated gates. You're doing the framework by hand.

**Good for:** Testing whether the BuildOS way of thinking fits your work before committing to setup.

---

## Level 2: Claude Code, no API keys (~10 min setup)

**You need:**
- [Claude Code](https://claude.ai/claude-code) installed on your machine (it has an installer; no terminal expertise required to install).
- Basic comfort opening a folder and running a command or two.

**What works:**
- `/setup` — walks you through 3 questions and creates your project files.
- `/think` — structured problem discovery. Ask Claude "help me figure out what to build" and it runs forcing questions, challenges your premises, and writes a design doc.
- `/plan` — writes an implementation plan to disk before building.
- `/start` and `/wrap` — session bootstrap and session close. These are the "memory" that survives between sessions.
- `/guide` — if you're lost, type this.
- `/log` — capture decisions mid-session.
- Manual review — read your own code, ask Claude to critique it directly.

**What doesn't:**
- `/review`, `/challenge`, `/challenge --deep` — these run **cross-model review** (multiple AI models review your work from different angles). They need API keys. Without them, the framework tells you to do a manual review instead — it doesn't block you.

**Good for:** Most personal projects, side projects, and learning. You get the core memory + workflow value without paying for multiple AI APIs. Cross-model review (`/challenge`, `/review`, `/polish`, `/pressure-test`) unlocks at Level 3.

---

## Level 3: Full power (+API keys, ~20 min extra setup)

**You need:** Level 2, plus:
- API keys from [Anthropic](https://console.anthropic.com), [OpenAI](https://platform.openai.com), and [Google AI Studio](https://aistudio.google.com).
- [LiteLLM](https://docs.litellm.ai/) running locally (the framework's setup script helps with this).

**What unlocks:**
- `/review` — three AI models from different families review your code through independent lenses (PM, Security, Architecture).
- `/challenge` — cross-model gate that asks "should we build this at all?" before you plan.
- `/challenge --deep` — full adversarial pipeline: challenge → judge → refine.
- `/polish` — 6-round cross-model refinement on any document.
- `/pressure-test` — adversarial counter-thesis on a direction or plan.

**Cost:** Typically small for personal use — each cross-model run costs a few cents to a few dollars depending on document size.

**Good for:** Anything where the cost of a bad decision outweighs the cost of an API call. Products, systems, anything touching real users.

---

## What you can ignore

BuildOS has lots of files. Most of them exist for the framework itself, not for you. You don't need to read or edit:

- `.claude/` — rules, skills, and hooks that run automatically
- `hooks/` — scripts that fire on file changes and commits
- `config/` — framework configuration
- `scripts/` — the framework's internal tools

Files **you** should know about:

- `docs/project-prd.md` — what you're building (created by `/setup`)
- `tasks/decisions.md` — choices you've made and why
- `tasks/lessons.md` — surprises and gotchas worth remembering
- `tasks/handoff.md` — where you left off last session
- `tasks/*-plan.md` — plans for specific work (created by `/plan`)

If you stay out of `.claude/`, `hooks/`, and `scripts/`, you can't break the framework.

---

## If you get lost

- Type `/guide` — gives you a map of what each tool does, organized by what you're trying to accomplish.
- Type `/start` — Claude reads your project files and tells you where things stand.
- Read [Getting Started](getting-started.md) for the first-hour tutorial (assumes Level 2+).

---

## The honest caveat

BuildOS's philosophy docs (`docs/why-build-os.md`, `docs/the-build-os.md`) are written for technical readers. If you hit jargon, skip those for now. The tools themselves work without reading the philosophy.

The recommended path for a non-engineer: start at Level 2. Run `/setup` → `/think` → `/plan` on a real project you care about. You'll learn more from doing it than from reading the docs.
