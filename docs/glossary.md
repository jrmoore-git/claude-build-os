# BuildOS Glossary

Plain-English definitions of terms that appear across BuildOS docs. If you hit a term you don't recognize in another doc, check here first.

---

## Core concepts

**Context window** — The amount of information Claude can hold at once during a conversation. Think of it as Claude's short-term memory. It's finite, and it resets between sessions. BuildOS moves important state to disk because the context window is temporary and the filesystem is permanent.

**Compaction** — When a conversation gets long, Claude Code automatically summarizes old parts to free up context window space. Information lost in compaction is gone unless it was written to disk. BuildOS treats compaction as a failure mode to plan around.

**Governance** — The set of rules, files, and automated checks that constrain what Claude can do in your project. BuildOS governance includes CLAUDE.md instructions, rule files, hooks, and architectural boundaries.

**Enforcement ladder** — The four levels of making a rule stick, from weakest to strongest: (1) lesson (written advice), (2) rule (loaded conditionally by Claude), (3) hook (deterministic script that fires automatically), (4) architecture (physically impossible to violate). If a rule keeps getting broken, promote it to the next level.

---

## Files and structure

**PRD** — Product Requirements Document. Lives at `docs/project-prd.md`. Describes what you're building, for whom, and why. Created by `/setup` or `/prd`.

**Frontmatter** — The metadata block at the top of a Markdown file, enclosed in `---` lines. Contains structured fields like scope, verification commands, rollback steps. BuildOS plans use frontmatter so hooks can read them.

**Handoff** — `tasks/handoff.md`. The last thing written at the end of a session. Tells the next session where you left off.

**Current state** — `docs/current-state.md`. The single-file snapshot of "what is true right now in this project." Read by `/start` at session begin.

**Session log** — `tasks/session-log.md`. Append-only log of what happened in each session. For history and audit.

---

## Pipeline terminology

**Skill** — A BuildOS tool invoked via slash command (e.g., `/think`, `/plan`, `/review`). Each skill is a Markdown file in `.claude/skills/` that tells Claude how to perform that task. You invoke them by typing the slash command OR by describing what you want in natural language.

**Hook** — A small script that Claude Code runs automatically on certain events (before edits, after commits, at session start). Hooks live in `hooks/` and are wired in `.claude/settings.json`. BuildOS ships ~21 hooks that enforce the framework's rules.

**Spike** — In BuildOS pipeline terms: a quick exploratory build with no full pipeline ceremony. "I want to test if this is possible in under an hour" → spike. Different from INVESTIGATE (a judge verdict, see below).

**Pipeline tier** — How much ceremony a change needs. T0 (spike) = just build. T1 (new feature) = `/think discover` → `/challenge` → `/plan` → build → `/review` → `/ship`. T2 (standard) = `/think refine` → `/plan` → build → `/review` → `/ship`.

---

## Review and governance

**Cross-model review** — Asking multiple AI models (from different families: Anthropic, OpenAI, Google) to independently review the same work. Reduces single-model blind spots. Requires LiteLLM and API keys.

**LiteLLM** — A local proxy that speaks one unified API to multiple AI providers. BuildOS routes all cross-model calls through LiteLLM so the same code works with Anthropic, OpenAI, Google, etc.

**Judge** — The stage after `/challenge` where an independent AI model evaluates challenger findings as ACCEPT, DISMISS, or ESCALATE. The overall verdict is APPROVE, REVISE, REJECT, or INVESTIGATE.

**INVESTIGATE** — A judge verdict meaning "insufficient evidence; run a time-boxed investigation before deciding." Previously called SPIKE (the verdict was renamed to avoid confusion with the pipeline tier name).

**Contract test** — An automated test that verifies a behavioral invariant — something that must stay true even as code changes. BuildOS ships a suite of contract tests covering the essential invariants (idempotency, audit completeness, etc.).

**Idempotency** — The property that running the same operation multiple times gives the same result as running it once. A BuildOS invariant for any state-changing code.

**Approval gating** — Requiring a human to approve an action before it runs, especially for actions that affect external systems (send a message, publish content, mutate shared state).

**Audit log** — An append-only record of every important action: what ran, when, what it returned. BuildOS requires an audit log for any skill that processes external data, even if the run produced zero results — silent failures look identical to silent successes otherwise.

---

## Everyday terminology

**Artifact** — Any file BuildOS writes as output of a skill: a design doc, a plan, a review, a judgment. "Durable" in the sense that it persists on disk across sessions, unlike chat history.

**Design doc** — `tasks/<topic>-design.md`. The output of `/think discover`. Contains the problem, user, scope, premises, alternatives, and recommendation. Feeds into `/plan`.

**Manual review** — Reading your own code (or asking Claude to critique it in the same session) instead of running `/review`. No cross-model calls, no API keys. The framework explicitly allows this as a fallback when cross-model infrastructure isn't set up.

**Blast radius** — How much damage a change could cause if it goes wrong. A typo fix has small blast radius. A schema migration has large blast radius. `/setup` asks about this to pick your governance tier.

**Persona** — A named reviewer role with a specific lens: `architect` (systems reasoning), `security` (risks), `pm` (user value and spec match), `frame` (what's missing from the candidate set). Each persona maps to a specific AI model via `config/debate-models.json`.

---

## Setup terminology

**Claude Code** — Anthropic's official CLI for Claude. The BuildOS framework runs inside Claude Code. Not the same as claude.ai (the web app) or Claude Desktop.

**Tier declaration** — The first line of `CLAUDE.md`: `<!-- buildos-tier: N -->` where N is 0-3. Tells BuildOS hooks how strict to be. Tier 0 = advisory only; tier 3 = full enforcement.

---

## If you need a term not listed here

Grep the docs. Most BuildOS concepts appear inline-defined near their first use. If a term is truly unexplained, [file an issue](https://github.com/jrmoore-git/claude-build-os/issues) — the glossary is meant to grow.
