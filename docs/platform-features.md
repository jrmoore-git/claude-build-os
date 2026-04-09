# Platform Features — Claude Code Reference

> **Last verified:** Claude Code, March 2026. Platform features evolve. When in doubt, check [Anthropic's official docs](https://docs.anthropic.com/en/docs/claude-code). This file consolidates platform-specific details so the rest of the framework stays focused on timeless principles.

This doc covers: CLAUDE.md mechanics, rules files, skills format, hook types and events, auto memory, native session management, and subagents.

---

## 1. CLAUDE.md Mechanics

- **Target under 200 lines.** Every line loads into every turn of every session and consumes context. Research shows instruction compliance decreases as instruction count grows. Prioritize ruthlessly.
- **Advisory, not enforced.** CLAUDE.md is context that Claude reads and tries to follow — it is not enforced configuration. For rules that must hold, use hooks (Level 3) or architecture (Level 4). See the [enforcement ladder](the-build-os.md#part-v-the-enforcement-ladder).
- **Survives compaction.** CLAUDE.md is re-read from disk after `/compact`. Your rules survive even when conversation history is compressed.
- **`/init` generates a starter.** Run `/init` in Claude Code to generate a CLAUDE.md from your existing codebase. Then customize.
- **Import syntax.** Split large CLAUDE.md files with `@path/to/import` (max depth 5 hops). Useful for separating project rules from team conventions.
- **Multiple locations.** `~/.claude/CLAUDE.md` (user-level, all projects), `./CLAUDE.md` or `./.claude/CLAUDE.md` (project-level). Project overrides user.

---

## 2. Rules Files (.claude/rules/)

- **One file per topic.** Place markdown files in `.claude/rules/`: `security.md`, `code-quality.md`, `api-design.md`, etc.
- **Always-loaded rules.** Files without YAML frontmatter load at session start, same as CLAUDE.md content.
- **Path-specific rules.** Add `paths:` frontmatter with glob patterns to load rules only when Claude reads matching files:
  ```yaml
  ---
  paths:
    - "src/api/**/*.ts"
    - "src/**/*.test.ts"
  ---
  ```
  This reduces context noise — security rules don't load during doc edits. Glob patterns support `**`, `*`, brace expansion `{ts,tsx}`.
- **Loading order and precedence:**
  1. Global rules (no `paths:` frontmatter) load first, apply to all files
  2. Path-specific rules load when Claude reads a matching file
  3. Both global and path-specific content are additive — they combine, they don't override each other
  4. If two rules files give conflicting guidance, the more specific file (path-scoped) takes precedence
  5. Within the same scope, files load in alphabetical order by filename
  6. A single file can contain both global guidance and a `paths:` frontmatter — but this is discouraged. Prefer separate files: one global, one path-scoped.
- **Advisory, not enforced.** Like CLAUDE.md, rules are context Claude tries to follow. For enforcement, escalate to hooks.
- **User-level rules.** `~/.claude/rules/` applies to every project. User rules load before project rules (project takes priority on conflicts).
- **Recursive discovery.** Subdirectories like `rules/frontend/` and `rules/backend/` are found automatically.

See `examples/rules/` for starter files demonstrating both always-loaded and path-specific patterns.

---

## 3. Skills Format (.claude/skills/)

Claude Code supports two formats for slash commands:

- **Legacy:** `.claude/commands/name.md` — simple markdown files, still functional
- **Current:** `.claude/skills/name/SKILL.md` — directory per skill with YAML frontmatter

The Build OS uses the SKILL.md format. Key frontmatter fields:

```yaml
---
name: review
description: Run a structured review of changes
user-invocable: true           # Shows in /slash menu
allowed-tools:                 # Restrict available tools
  - Read
  - Grep
  - Glob
model: sonnet                  # Override model for this skill
context: fork                  # Run in isolated subagent
disable-model-invocation: true # Only user can trigger (for side-effect skills)
---
```

- **Supporting files.** Skills can include additional files in their directory (data, templates, scripts).
- **Dynamic context.** Use `` !`command` `` syntax to inject shell command output into the skill at runtime.
- **String substitution.** `$ARGUMENTS` (full args), `$1`, `$2` (positional), `${CLAUDE_SESSION_ID}`, `${CLAUDE_SKILL_DIR}`.
- **Bundled skills.** Claude Code ships with `/batch`, `/debug`, `/simplify`, `/loop`.
- **Size limit.** Keep SKILL.md under 500 lines. Move reference material to supporting files.

---

## 4. Hook Types and Events

Hooks are deterministic enforcement — Level 3 on the enforcement ladder. They fire automatically and cannot be overridden by Claude.

### Four hook types

| Type | What it does | Use case |
|---|---|---|
| `command` | Runs a shell command | Block file writes, run tests, format code |
| `http` | POSTs to a URL | External service integration, webhooks |
| `prompt` | Single-turn LLM evaluation (returns ok/not-ok) | Policy checks too nuanced for regex |
| `agent` | Multi-turn subagent with tool access | Complex verification requiring file reads |

### Key hook events

| Event | Fires when | Common use |
|---|---|---|
| `PreToolUse` | Before any tool executes | Block dangerous operations, validate paths |
| `PostToolUse` | After a tool completes | Run tests after edits, format code |
| `Stop` | Session is ending | Export handoff, run final checks |
| `SessionStart` | Session begins | Inject context, verify environment |
| `PreCompact` | Before context compaction | Preserve critical state |
| `SubagentStart` | Subagent is spawned | Audit or restrict subagent behavior |
| `UserPromptSubmit` | User sends a message | Inject instructions, validate input |
| `ConfigChange` | Settings are modified | Audit configuration changes |

- **Exit code 2 blocks the action.** Any other exit code (including errors) allows it to proceed.
- **Matchers** filter by tool name, file path, or event type. Support regex.
- **JSON output** from hooks enables structured control (allow/deny/ask).

For the full list of 17 events and complete hook API, see [Anthropic's hook reference](https://docs.anthropic.com/en/docs/claude-code/hooks).

See `examples/` for hook scripts and `examples/enforcement-ladder.md` for a walkthrough of hook-based enforcement.

---

## 5. Auto Memory

Claude Code maintains automatic memory at `~/.claude/projects/<project>/memory/MEMORY.md`. This is separate from CLAUDE.md and your framework files.

- **What it captures.** Patterns Claude notices across sessions: project conventions, user preferences, recurring gotchas.
- **First 200 lines loaded** per session. Topic files in the same directory load on demand.
- **Toggle with `/memory`** command or `autoMemoryEnabled` setting.

### How auto memory relates to framework files

| File | Purpose | Who writes it |
|---|---|---|
| `MEMORY.md` (auto) | Claude's session-to-session observations | Claude (automatic) |
| `tasks/decisions.md` | Deliberate architectural choices with rationale | You (via /capture or /doc-sync) |
| `tasks/lessons.md` | Mistakes and patterns worth remembering | You (via /capture or /doc-sync) |
| `tasks/handoff.md` | Next-session context and status | You (via /wrap-session) |

Auto memory and framework files serve different purposes. Auto memory captures what Claude notices; framework files capture what you deliberately record. If both contain the same information, the framework file is authoritative.

Consider disabling auto memory (`/memory off`) if it creates noise or duplicates your framework files. Or curate `MEMORY.md` periodically to keep it useful.

---

## 6. Native Session Management

Claude Code provides session continuity features that complement the handoff workflow:

| Command/Flag | What it does |
|---|---|
| `--continue` | Resume the most recent session |
| `--resume` | Pick a specific session to resume |
| `/rewind` | Checkpoint and roll back within a session |
| `/btw` | Ask a side question without adding to conversation history |
| `/compact <instructions>` | Guided compaction with preservation hints |
| `/clear` | Clear context between unrelated tasks |

Use these alongside — not instead of — the handoff file. Native session continuity preserves conversation; the handoff file preserves decisions and intent. A resumed session has conversation history but not the structured context that `/recall` provides.

---

## 7. Built-in Subagents

Claude Code includes three built-in subagent types available via the Agent tool:

| Type | Model | Tools | Use case |
|------|-------|-------|----------|
| **Explore** | Haiku (fast) | Read-only (Read, Glob, Grep, WebSearch, WebFetch) | Codebase search, file discovery, research questions |
| **Plan** | Inherited | Read-only | Research during plan mode |
| **general-purpose** | Inherited | All tools | Complex multi-step tasks, code changes |

These run automatically when Claude delegates work. Explore agents are cheap and safe to fan out widely (5-10 parallel). General-purpose agents need worktree isolation when running in parallel.

---

## 8. Custom Subagents (.claude/agents/)

Define custom subagents with restricted capabilities. Files live in `.claude/agents/` (project-level) or `~/.claude/agents/` (user-level).

### Basic example — read-only researcher

```yaml
# .claude/agents/researcher.yaml
name: researcher
description: Read-only research agent for codebase exploration
tools:
  - Read
  - Glob
  - Grep
  - WebSearch
model: haiku
```

### Example — test runner restricted to Bash

```yaml
# .claude/agents/test-runner.yaml
name: test-runner
description: Runs tests and reports results — cannot modify code
tools:
  - Read
  - Bash
  - Glob
  - Grep
model: sonnet
```

### Example — code reviewer with write access

```yaml
# .claude/agents/implementer.yaml
name: implementer
description: Implements code changes in an isolated worktree
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
isolation: worktree
```

### Key capabilities

- **Tool restrictions.** Limit what tools the subagent can use. A researcher that literally cannot write files is the [enforcement ladder](the-build-os.md#part-v-the-enforcement-ladder) applied at the agent level — architectural prevention, not advisory guidance.
- **Model override.** Use cheaper models for focused tasks. A common pattern: Opus for the lead, Haiku for research subagents, Sonnet for implementation workers.
- **Worktree isolation.** Add `isolation: worktree` for subagents that write files in parallel. Each gets its own git checkout. Required by `hook-agent-isolation.py` when a parallel plan is active.
- **Skills access.** Subagents can load specific skills from `.claude/skills/`.

### Scope hierarchy

Custom agents are discovered in order: project (`.claude/agents/`) → user (`~/.claude/agents/`). Project-level definitions take precedence over user-level definitions with the same name.

### Connecting to hooks

Two hooks govern subagent behavior:

- **`SubagentStart`** — fires when any subagent is spawned. Use for auditing or restricting subagent behavior at the governance level.
- **`hook-agent-isolation.py`** (Build OS) — blocks write-capable Agent dispatches without `isolation: "worktree"` after a parallel plan is declared. This enforces isolation as a structural gate, not a suggestion.

---

## 9. Headless and Programmatic Mode

Claude Code can run non-interactively for CI/CD pipelines and automation scripts:

```bash
# Single prompt, no interactive session
claude -p "Run the test suite and report failures"

# Pipe input
echo "Explain this error" | claude -p

# With specific model
claude -p --model sonnet "Summarize changes in the last 5 commits"
```

This is relevant for:
- **CI/CD integration** — run code review, test analysis, or doc generation as pipeline steps
- **Automated workflows** — scripts that invoke Claude for classification, summarization, or structured extraction
- **Batch processing** — process multiple files or inputs programmatically

Headless mode respects the same `.claude/` configuration (CLAUDE.md, rules, settings, hooks) as interactive mode. Hooks fire normally. The key difference: there is no interactive approval — permissions must be pre-configured in settings or the command will fail on any action that requires user confirmation.
