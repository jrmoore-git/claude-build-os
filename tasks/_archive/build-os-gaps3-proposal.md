# Proposal: Build OS Structural Gaps + Feature Currency Update

**Author:** Claude Opus (Round 1)
**Date:** 2026-03-13
**Debate type:** Architecture (3 rounds)
**Scope:** Address structural gaps identified by repo audit AND feature currency gaps identified by comparison against Anthropic's official docs and community best practices. The Build OS repo teaches original concepts no one else has published (enforcement ladder, governance tiers, 7-step session loop, cross-model debate, contract tests, LLM boundary rule) — but it's behind on documenting newer Claude Code platform features. This proposal fixes both.

---

## Context

### Repo Audit (37 gaps found)
A full audit compared every cross-reference and teaching concept against actual repo artifacts. The highest-priority gaps: no `.claude/rules/` examples (despite 12+ references), 4 of 8 slash commands not wired, broken bootstrap path in /setup, missing session-log template.

### Feature Currency Research
A comparison against Anthropic's official docs (code.claude.com), community frameworks (Everything Claude Code, Claude Playbook, Awesome Claude Code Toolkit, Continuous Claude v3), and published research revealed:

**Where the Build OS leads (unique contributions):**
- Enforcement ladder (Advisory → Rules → Hooks → Architecture) — not in Anthropic's docs or any community framework
- Governance tiers (Tier 0–3) — no other framework provides graduated adoption
- 7-step session loop — Anthropic recommends 4 steps; we add Recall, Capture, Review
- Cross-model debate for review — more sophisticated than any community approach
- Contract tests (7 universal invariants) — unique to us
- LLM boundary rule — not in Anthropic's official docs
- "Disk over context" with structured templates — better developed than any community approach

**Where the Build OS is behind:**
- `.claude/commands/` is legacy — SKILL.md with YAML frontmatter is the current standard
- `.claude/rules/` path matchers (YAML frontmatter with `paths:` globs) — major context-saving feature not documented
- CLAUDE.md size guidance — Anthropic recommends under 200 lines; research shows compliance collapses past 150–200 instructions
- CLAUDE.md and rules are advisory, not enforced — our "HARD RULE" language implies enforcement that doesn't exist; the enforcement ladder already solves this (hooks enforce, rules advise) but we don't say it clearly enough
- Auto memory (`~/.claude/projects/<project>/memory/MEMORY.md`) — native feature not mentioned
- Hook types — Anthropic has 4 types (command, http, prompt, agent) and 17 events; we only show command hooks with 2 events
- Subagents (`.claude/agents/`) — not documented
- Native session management (`--continue`, `--resume`, `/rewind`, `/btw`) — not mentioned
- `/init` command for generating starter CLAUDE.md — not mentioned

Nobody else has published a *framework* — the community has published collections of configs and kitchen-sink repos. The Build OS is the only thing that teaches *why* and *when*, not just *what*. This proposal keeps that advantage while closing the platform feature gaps.

---

## Proposed Fixes

### Group A — Bootstrap Integrity

**Fix A1: Consolidate all 8 commands into `.claude/commands/`**

Move `templates/commands/capture.md`, `handoff.md`, `sync.md`, `triage.md` into `.claude/commands/` alongside plan, recall, review, setup. Delete `templates/commands/` directory.

These stay as `.claude/commands/*.md` format (not SKILL.md) because: (a) commands still work and are simpler for a framework repo, (b) the Build OS should model the simplest viable pattern at each tier, and (c) converting to skills adds directory-per-command overhead that doesn't serve a template repo. Fix A8 documents the skills format for users who need it.

**Fix A2: Create `examples/rules/security.md`**

Starter security rules (~25 lines) with:
- "Adapt to your project" header explaining this is illustrative, not policy
- One rule WITH a `paths:` frontmatter example showing path-specific loading
- One rule WITHOUT frontmatter showing always-loaded behavior
- A note that rules are advisory — for enforcement, use hooks (linking to enforcement ladder)

Content covers: LLM boundary rule, provenance over plausibility, hook safety.

**Fix A3: Create `examples/rules/code-quality.md`**

Starter code quality rules (~15 lines) with same "adapt" header. Covers: simplicity override, no speculation, guard clauses. Uses `paths:` frontmatter targeting `src/**/*.{ts,py,js}` to demonstrate the pattern.

**Fix A4: Update `/setup` command**

- For all tiers: explicitly state "copy `.claude/commands/` to your project" and mention `/init` as an alternative for generating a starter CLAUDE.md
- For simple files: create directly with header content
- For structured templates: reference the Build OS repo
- For Tier 2: mention creating `.claude/rules/` and `.claude/settings.json`
- Add: "The Build OS uses `.claude/commands/` format. For production systems, consider migrating to SKILL.md format (see Build OS Part III)."
- Frame honestly as a reference repo, not an installer

### Group B — Teaching Examples

**Fix B1: Create `templates/session-log.md`**

~15 lines showing entry format: file header, separator convention, entry structure (date + topic header, Decided/Implemented/Not Finished/Next Session bullets).

**Fix B2: Update `examples/README.md`**

- Reference the new example rules files and explain the `paths:` frontmatter
- Replace inline settings.json with per-hook merge snippets and "do not replace entire file" note
- Add a section documenting all 4 hook types (command, http, prompt, agent) with one-line descriptions of each
- Note that `prompt` hooks enable LLM-based evaluation (the missing piece between rules and command hooks in the enforcement ladder)
- List the most important hook events: PreToolUse, PostToolUse, Stop, SessionStart, PreCompact, SubagentStart
- Link to Anthropic's full hook reference for the complete list

### Group C — Feature Currency (doc updates)

**Fix C1: Add "Platform Features" section to Build OS Part III (File System)**

After the file tree and CLAUDE.md length guidance, add a new subsection covering features the framework builds on:

- **CLAUDE.md**: target under 200 lines; fully survives compaction (re-read from disk); use `/init` to generate from codebase analysis; supports `@path/to/import` syntax for splitting content
- **Auto memory**: Claude maintains `~/.claude/projects/<project>/memory/MEMORY.md` automatically; complements your disk-based files (decisions.md, lessons.md); first 200 lines loaded per session
- **Rules path matchers**: `.claude/rules/` files support YAML frontmatter with `paths:` globs; rules without matchers load every session; rules with matchers load only for matching files — use this to reduce context noise
- **Advisory vs enforced**: CLAUDE.md and rules are context that Claude tries to follow, not enforced configuration. Research shows compliance decreases as instruction count increases. This is why the enforcement ladder exists — when a rule must be enforced, escalate to a hook (deterministic) or architecture (structural). The right mental model: rules are strong suggestions; hooks are laws.

~30 lines. This section teaches the platform features that make the enforcement ladder work.

**Fix C2: Add "Skills Format" note to Build OS Part III**

After the commands section in the file tree, add:

"The Build OS uses `.claude/commands/` format for slash commands — it still works and is the simplest option. For production systems with more complex needs, Claude Code also supports SKILL.md format (in `.claude/skills/<name>/SKILL.md`) with YAML frontmatter for: tool restrictions (`allowed-tools`), model override (`model`), isolated execution (`context: fork`), auto-invocation control (`disable-model-invocation`), and argument hints. See Anthropic's skills documentation for the full spec."

~5 lines. Acknowledges the current standard without forcing a migration.

**Fix C3: Add "Subagents" note to Team Playbook**

In the Team Playbook's section on agent teams, add:

"Claude Code supports custom subagent definitions in `.claude/agents/` with YAML frontmatter controlling: available tools, model selection, skill access, and worktree isolation. Use these when you need specialized agents with restricted tool access — for example, a research agent that can read but not write, or a test agent that can only run in a worktree."

~5 lines in the appropriate section.

**Fix C4: Add "Native Session Management" to Build OS Part X (Survival Basics)**

After the compaction discipline section, add:

"Claude Code provides native session management that complements the handoff workflow: `--continue` resumes the most recent session, `--resume` picks a specific session, `/rewind` checkpoints and rolls back within a session, and `/btw` asks a side question without adding to conversation history (useful for quick lookups that shouldn't consume context). Use these alongside — not instead of — the handoff file. Native session continuity preserves conversation; the handoff file preserves decisions and intent."

~5 lines. Integrates native features with our framework's approach.

**Fix C5: Update Build OS Part VIII (bootstrap) to mention `/init`**

In the bootstrap section, add to Option A (Interactive setup):

"Alternatively, run `/init` in Claude Code to generate a starter CLAUDE.md from your existing codebase. Then layer on governance files using the manual checklist below."

~2 lines.

---

## What is NOT included (and why)

- **Full skills migration**: Converting all 8 commands to SKILL.md format would add directory-per-command overhead inappropriate for a template repo. The note in Fix C2 points users to the skills format when they need it.
- **Full hook event documentation**: 17 events is reference material, not framework content. Fix B2 covers the most important ones and links to Anthropic's docs for the rest.
- **Plugins and marketplaces**: Too new and evolving to document in a stable framework.
- **Agent teams protocol**: Experimental feature. The Team Playbook covers the concepts; linking to Anthropic's docs is sufficient.
- **PERSONAS.md example**: Previous debate concluded this is premature — a "grow into it" artifact.
- **Orchestration template**: Previous debate concluded this is over-scoped.
- **Block-commit hook**: Previous debate concluded this is too environment-specific.
- **Standalone settings.json**: Previous debate concluded merge snippets are safer than a full file.

---

## What the challengers should evaluate

1. **Scope**: 12 fixes across 3 groups. Is this too many? The groups are independent — A (bootstrap), B (examples), C (doc updates) — and can be executed separately.
2. **Skills format**: Is a note sufficient, or should we migrate the commands to SKILL.md?
3. **Advisory nature**: Does Fix C1 adequately address the contradiction between our "HARD RULE" language and the advisory reality? Should we go further and update the CLAUDE.md template itself?
4. **Auto memory**: Is a mention in Part III sufficient, or does this need its own section?
5. **Feature currency vs framework stability**: Adding platform feature documentation creates maintenance burden — when Anthropic updates features, our docs go stale. Is the proposed level of detail right, or should we keep it lighter and link more?
6. **Tone**: The Build OS teaches principles, not platform specifics. Do the Group C additions shift the tone too far toward platform documentation?
