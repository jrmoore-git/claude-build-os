# Resolution: Fix Build OS Repo Structural Gaps

**Author:** Claude Opus (Round 3)
**Date:** 2026-03-13
**Responding to:** Challenger A (9 challenges, 4 MATERIAL) + Challenger B (3 challenges, 2 MATERIAL)

---

## Responses to Challenger A

### 1. [ASSUMPTION] [MATERIAL]: Moving commands assumes "immediately usable"

**COMPROMISE.** Fair point — this is a template repo, not an installed package. Moving files internally doesn't change user adoption. Revised approach: keep all 8 commands in `.claude/commands/` for internal consistency (the repo should model what a project looks like), but the real fix is in /setup (see response to challenge #2). The README manual path already says "copy `.claude/commands/` to your project" — with all 8 in one place, that instruction now works correctly.

### 2. [ALTERNATIVE] [MATERIAL]: /setup fix is a doc patch, not robust design

**CONCEDE.** The challenger is right — narrating a manual-copy workflow more clearly doesn't fix the design. Revised Fix 7: instead of embedding templates inline (which Challenger B also flagged as DRY violation), `/setup` will:
1. List the files it creates (decisions.md, lessons.md, etc.) with inline content for each
2. For templates it can't embed cleanly (review-protocol, contract-tests), tell the user: "Copy from the Build OS repo: `cp path/to/claude-build-os/templates/review-protocol.md docs/`"
3. Explicitly state: "The slash commands in `.claude/commands/` are already active if you cloned this repo. If you started from scratch, copy them: `cp -r path/to/claude-build-os/.claude/commands/ .claude/commands/`"

This is honest about the repo's nature (a reference, not an installer) rather than pretending /setup is a package manager.

### 3. [RISK] [MATERIAL]: Block-commit hook has severe false-positive risk

**CONCEDE.** Both challengers flagged this — the hook is too environment-specific, contradicts the rationale for excluding toolbelt scripts, and "test evidence in the current session" is undefined. Dropping Fix 4 entirely. The two existing hooks (block-env-write, test-after-edit) are sufficient examples. The concept of "block commits when tests fail" is taught in the Build OS; users who need it will build one for their specific test framework.

### 4. [UNDER-ENGINEERED] [MATERIAL]: Rules files need "adapt this" framing

**COMPROMISE.** Good catch. Each example rules file will include a header comment:
```markdown
# Example rules file — adapt to your project
# Copy to .claude/rules/security.md and modify for your needs.
# Rules in this directory load only when the file path matcher triggers.
# See the-build-os.md Part V for the enforcement ladder.
```
And each rule will have a brief inline comment explaining why it exists and when to remove or modify it. The goal is "starting point you customize" not "policy you adopt."

### 5. [ALTERNATIVE] [ADVISORY]: settings.json overwrite risk

**COMPROMISE.** The challenger is right about overwrite risk. Instead of a standalone file, add a section to `examples/README.md` with per-hook snippets and a merge note: "Add these entries to your existing `.claude/settings.json`. Do not replace the entire file." Drop standalone Fix 5.

### 6. [OVER-ENGINEERED] [ADVISORY]: PERSONAS.md is premature

**CONCEDE.** The review-protocol template already says when to create PERSONAS.md and gives one example question. That's the right level of guidance for a starter framework. Dropping Fix 8. Users who reach that maturity point will build their own.

### 7. [OVER-ENGINEERED] [ADVISORY]: Orchestration template is scope creep

**CONCEDE.** Both challengers flagged this. The Team Playbook describes orchestration well enough — a template for something this context-dependent would be cargo-culted. Dropping Fix 10.

### 8. [UNDER-ENGINEERED] [MATERIAL]: 11 fixes need prioritization

**CONCEDE.** The revised plan below is split into two groups: (A) bootstrap integrity (commands, setup, rules examples) and (B) teaching examples (session-log template, README update). Group A must land first. Group B is independent.

### 9. [ASSUMPTION] [ADVISORY]: session-log.md may not need a template

**REBUT.** session-log.md is the only core file in the minimum viable project file tree that lacks a template. The handoff template covers next-session context; the session log covers historical record. These are distinct artifacts. A 15-line template showing the entry format costs nothing and prevents users from inventing incompatible formats. Keeping Fix 6.

---

## Responses to Challenger B

### 1. [UNDER-ENGINEERED] [MATERIAL]: Inline templates in /setup create drift

**CONCEDE.** Same conclusion as Challenger A #2. /setup will not embed template content inline. Instead it will create the simple files directly (decisions.md header, lessons.md header, handoff.md header — these are just headers with no complex structure) and point users to the repo for the structured templates. See revised Fix 7 above.

### 2. [ASSUMPTION] [MATERIAL]: Block-commit hook contradicts toolbelt exclusion rationale

**CONCEDE.** Same conclusion as Challenger A #3. Fix 4 dropped.

### 3. [OVER-ENGINEERED] [ADVISORY]: Orchestration template is over-scoped

**CONCEDE.** Same conclusion as Challenger A #7. Fix 10 dropped.

---

## Revised Plan: 7 Edits, 2 Groups

### Group A — Bootstrap Integrity (do first)

**Edit A1: Move template commands into `.claude/commands/`**
Move `templates/commands/capture.md`, `handoff.md`, `sync.md`, `triage.md` into `.claude/commands/`. Delete `templates/commands/` directory. All 8 operations now live in one directory that models what a user's project should look like.

**Edit A2: Create `examples/rules/security.md`**
Starter security rules (~20 lines) with "adapt to your project" header. Covers: LLM boundary rule, provenance over plausibility, hook safety. Each rule has an inline comment explaining when to modify or remove it.

**Edit A3: Create `examples/rules/code-quality.md`**
Starter code quality rules (~15 lines) with same "adapt" header. Covers: simplicity override, no speculation, guard clauses. Two examples establish the pattern better than one.

**Edit A4: Update `/setup` command**
- For all tiers: explicitly state that `.claude/commands/` should be copied to the project
- For simple files (decisions.md, lessons.md, handoff.md, current-state.md): create with header content directly
- For structured templates (review-protocol, contract-tests, project-prd): tell user to copy from the Build OS repo
- For Tier 2: mention creating `.claude/rules/` with starter rules from examples

### Group B — Teaching Examples (independent of A)

**Edit B1: Create `templates/session-log.md`**
~15 lines showing the entry format: file header, separator convention, entry structure (date + topic header, Decided/Implemented/Not Finished/Next Session bullets).

**Edit B2: Update `examples/README.md`**
- Reference the new example rules files
- Replace inline settings.json with per-hook merge snippets and a "do not replace entire file" note

**Edit B3: Update `docs/the-build-os.md` bootstrap section**
Add one line to the manual setup checklist: "Copy `.claude/commands/` to your project for session operations (recall, plan, review, capture, sync, handoff, triage)."

### Dropped from original proposal:
- ~~Fix 4: Block-commit hook~~ — both challengers: too environment-specific, false-positive risk
- ~~Fix 5: Standalone settings.json~~ — Challenger A: overwrite risk, merge snippets better
- ~~Fix 8: PERSONAS.md~~ — Challenger A: premature, current guidance sufficient
- ~~Fix 10: Orchestration template~~ — both challengers: over-scoped, too context-dependent
