# Resolution: Build OS Structural Gaps + Feature Currency

**Author:** Claude Opus (Round 3)
**Date:** 2026-03-13
**Responding to:** Challenger A (7 challenges, 4 MATERIAL) + Challenger B (3 challenges, 3 MATERIAL)

---

## Responses to Challenger A

### 1. [ASSUMPTION] [MATERIAL]: Commands format is internally inconsistent

**CONCEDE.** Both challengers flagged this. A best-practices framework cannot teach a legacy format as its default. All 8 commands will be migrated to `.claude/skills/<name>/SKILL.md` format with YAML frontmatter. The directory-per-skill structure is the correct pattern for users to learn. The `/setup` skill will generate this structure.

### 2. [RISK] [MATERIAL]: Platform details will drift

**COMPROMISE.** The challenger is right that scattering version-sensitive details across multiple docs creates partial staleness. Revised approach: create a single `docs/platform-features.md` file that consolidates all platform-specific details (CLAUDE.md behavior, rules mechanics, hook types/events, skills format, auto memory, native session management, subagents). Each section includes a "last verified" note. The Build OS and Team Playbook link to this file rather than embedding platform specifics inline. This keeps the main docs timeless and the platform details maintainable.

### 3. [UNDER-ENGINEERED] [MATERIAL]: "HARD RULE" contradiction not fixed in templates

**CONCEDE.** Both challengers flagged this. The CLAUDE.md template will be updated to:
1. Remove any language that implies enforcement
2. Add an explicit note: "These rules are advisory — Claude reads them and tries to follow them, but compliance is not guaranteed. For rules that must be enforced, use hooks (see the enforcement ladder)."
3. Use language like "Always prefer X" and "Never do Y without Z" instead of "HARD RULE" — these are strong directives without false enforcement claims

### 4. [ALTERNATIVE] [MATERIAL]: Rules examples should teach the enforcement ladder, not just topical coverage

**COMPROMISE.** Brilliant suggestion. Instead of ONLY topical files, add one example that shows the same policy at all four enforcement levels. This will be `examples/enforcement-ladder.md` — a walkthrough showing "don't commit secrets" as:
- Level 1 (Advisory): line in CLAUDE.md
- Level 2 (Rule): `.claude/rules/security.md` with paths matcher
- Level 3 (Hook): PreToolUse hook blocking `git add .env`
- Level 4 (Architecture): `.gitignore` entry

ALSO keep the two topical rules files (security.md, code-quality.md) as practical starting points users can copy. The ladder example teaches the concept; the topical files give something to use immediately.

### 5. [OVER-ENGINEERED] [ADVISORY]: 12 fixes is a lot

**COMPROMISE.** Grouping into 3 independent groups addresses this. Group A (bootstrap) is the priority. Groups B and C can land separately. The consolidated platform-features.md (response to challenge #2) also reduces the number of files touched across the main docs.

### 6. [UNDER-ENGINEERED] [ADVISORY]: Session-log template needs lifecycle guidance

**COMPROMISE.** Add 3 lines of lifecycle context to the template header: when to create it (first session), when to use session-log vs handoff (session-log is historical record, handoff is next-session context), and that native `--continue`/`--resume` preserves conversation but not decisions.

### 7. [ASSUMPTION] [ADVISORY]: Rhetorical overreach

**CONCEDE.** Removed from the final plan. The fixes stand on their own merits.

---

## Responses to Challenger B

### 1. [ALTERNATIVE] [MATERIAL]: Must adopt SKILL.md

**CONCEDE.** Same conclusion as Challenger A #1. Full migration to `.claude/skills/` format.

### 2. [UNDER-ENGINEERED] [MATERIAL]: "HARD RULE" must be stripped from templates

**CONCEDE.** Same conclusion as Challenger A #3. Templates updated to use strong advisory language without false enforcement claims.

### 3. [ASSUMPTION] [MATERIAL]: Auto memory could conflict with framework files

**COMPROMISE.** Good catch. The platform-features.md section on auto memory will include explicit guidance:
- Auto memory captures things Claude notices across sessions (patterns, preferences, gotchas)
- Framework files (decisions.md, lessons.md) capture things you deliberately record
- They serve different purposes: auto memory is Claude's notes; framework files are your system of record
- If auto memory duplicates something already in lessons.md or decisions.md, the framework file is authoritative
- Consider disabling auto memory (`/memory off`) if it creates noise, or curate MEMORY.md periodically

---

## Final Plan: 13 Changes, 3 Groups

### Group A — Bootstrap Integrity (do first)

**A1: Migrate all 8 commands to `.claude/skills/` format**

Convert `.claude/commands/{plan,recall,review,setup}.md` and `templates/commands/{capture,handoff,sync,triage}.md` into `.claude/skills/<name>/SKILL.md` with YAML frontmatter (name, description, user-invocable: true). Delete `.claude/commands/` and `templates/commands/` directories.

Each SKILL.md gets minimal frontmatter:
```yaml
---
name: recall
description: Load context at the start of a session
user-invocable: true
---
```

**A2: Create `examples/rules/security.md`**

~25 lines. "Adapt to your project" header. One rule with `paths:` frontmatter example, one without. Advisory note linking to enforcement ladder. Content: LLM boundary, provenance, hook safety.

**A3: Create `examples/rules/code-quality.md`**

~15 lines. Same "adapt" header. Uses `paths:` frontmatter targeting source files. Content: simplicity, no speculation, guard clauses.

**A4: Create `examples/enforcement-ladder.md`**

~40 lines. Shows "don't commit secrets" at all 4 enforcement levels: CLAUDE.md line → `.claude/rules/security.md` rule → PreToolUse hook → `.gitignore` architecture. This is the teaching artifact for the framework's core concept.

**A5: Update CLAUDE.md template**

- Replace enforcement-implying language with strong advisory language
- Add: "These rules are advisory — Claude tries to follow them but compliance is not guaranteed. For enforcement, use hooks."
- Add: "Target: under 200 lines. Every line consumes context on every turn."
- Keep the same sections and content, just fix the framing

**A6: Update `/setup` (now `.claude/skills/setup/SKILL.md`)**

- Reference `.claude/skills/` as the command location
- Mention `/init` as an alternative for generating starter CLAUDE.md
- For Tier 2: mention `.claude/rules/` and `.claude/settings.json`
- Frame as reference repo, not installer

### Group B — Platform Currency (single consolidated file)

**B1: Create `docs/platform-features.md`**

Single file (~120 lines) consolidating all platform-specific details:

1. **CLAUDE.md mechanics**: under 200 lines target, survives compaction, `/init` generates from codebase, `@path/import` syntax, loaded at every turn
2. **Rules mechanics**: `.claude/rules/` files, YAML frontmatter with `paths:` globs, always-loaded vs path-specific, advisory nature, user-level rules in `~/.claude/rules/`
3. **Skills format**: SKILL.md with frontmatter (name, description, allowed-tools, model, context: fork, disable-model-invocation), directory structure, $ARGUMENTS substitution, bundled skills (/batch, /debug, /simplify, /loop)
4. **Hook types and events**: 4 types (command, http, prompt, agent) with one-line descriptions. Key events: PreToolUse, PostToolUse, Stop, SessionStart, PreCompact, SubagentStart. Exit code 2 = block. Link to Anthropic's full reference.
5. **Auto memory**: ~/.claude/projects/<project>/memory/MEMORY.md, first 200 lines loaded, complements framework files (auto memory = Claude's notes, framework files = your system of record), guidance on preventing duplication
6. **Native session management**: --continue, --resume, /rewind, /btw, /compact <instructions>, custom status line
7. **Subagents**: .claude/agents/ with YAML frontmatter, tool restrictions, model selection, worktree isolation

Each section has a "Last verified: Claude Code as of March 2026" note at the top. When Anthropic updates features, only this one file needs updating.

**B2: Update `examples/README.md`**

- Reference new rules files and enforcement ladder example
- Add section on all 4 hook types with per-hook merge snippets
- Link to platform-features.md for full hook event list
- Remove inline settings.json, replace with merge guidance

### Group C — Doc Cross-References (light touches)

**C1: Update Build OS Part III (File System)**

- Update file tree to show `.claude/skills/` instead of `.claude/commands/`
- Add one paragraph on advisory nature: "CLAUDE.md and rules are context Claude tries to follow, not enforced configuration. Research shows compliance decreases as instruction count grows. This is why the enforcement ladder exists: when a rule must be enforced, escalate to a hook or architecture."
- Add: "For platform mechanics (how rules load, how hooks fire, skills format), see [Platform Features](platform-features.md)."

**C2: Update Build OS Part VIII (Bootstrap)**

- Update Option A and B to reference `.claude/skills/` format
- Add: "Run `/init` in Claude Code to generate a starter CLAUDE.md from your codebase, then layer governance files on top."

**C3: Update Build OS Part X (Survival Basics)**

- Add one paragraph: "Claude Code provides native session management: `--continue` resumes the most recent session, `--resume` picks a specific one, `/btw` asks side questions without context cost. Use these alongside the handoff file — native continuity preserves conversation; the handoff preserves decisions and intent."

**C4: Update Team Playbook**

- Add one paragraph on subagents in the agent teams section, linking to platform-features.md

**C5: Create `templates/session-log.md`**

~20 lines with lifecycle header: when to create, session-log vs handoff distinction, entry format.

### Dropped from original:
- ~~Standalone settings.json~~ — merge snippets in examples/README.md (previous debate)
- ~~PERSONAS.md~~ — premature (previous debate)
- ~~Orchestration template~~ — over-scoped (previous debate)
- ~~Block-commit hook~~ — too environment-specific (previous debate)
- ~~Inline platform details in Build OS~~ — consolidated into platform-features.md (Challenger A #2)
- ~~Rhetorical "nobody else" claims~~ — removed (Challenger A #7)
