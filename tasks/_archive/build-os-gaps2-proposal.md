# Proposal: Fix Build OS Repo Structural Gaps

**Author:** Claude Opus (Round 1)
**Date:** 2026-03-13
**Debate type:** Architecture (3 rounds)
**Scope:** Address 8 HIGH-priority gaps and 6 MEDIUM-priority gaps identified by a full repo audit. All changes are within the claude-build-os repo (23 files currently, framework/template repo — no runtime code).

---

## Context

A full audit of the published Build OS repo (github.com/jrmoore-git/claude-build-os) compared every cross-reference, teaching concept, and artifact promise against what actually exists in the repo. The framework teaches concepts extensively but several core artifacts are missing — most critically, the enforcement ladder's Level 2 (`.claude/rules/` files) has zero examples despite being referenced in 12+ places.

The repo currently has 23 files: 3 docs, 8 templates, 4 template commands, 4 slash commands, 2 hook scripts, 1 hook README, 1 CLAUDE.md, 1 README, 1 .gitignore.

---

## Proposed Fixes

### Fix 1: Move all 8 slash commands into `.claude/commands/`

**What:** Move `templates/commands/capture.md`, `handoff.md`, `sync.md`, `triage.md` into `.claude/commands/` alongside the existing 4 (plan, recall, review, setup). Remove `templates/commands/` directory.

**Why:** The session loop teaches 7 cognitive/engineering operations. Currently only 4 have working slash commands. The other 4 exist in a separate directory that users must manually discover and copy. All 8 should be immediately usable.

**Risk:** Users who already copied `templates/commands/` separately would have duplicates. Low risk — the repo is days old.

### Fix 2: Add example `.claude/rules/security.md`

**What:** Create `examples/rules/security.md` with starter security rules covering the two concepts taught most heavily in the Build OS: the LLM boundary rule ("the model may decide; software must act") and hook safety ("review hook configs like CI scripts"). Keep it to 15-20 lines — enough to show structure and content, not a comprehensive security policy.

**Why:** The enforcement ladder teaches `.claude/rules/` files as Level 2 governance. The /setup command promises to create `security.md` for Tier 2 projects. The lessons.md template shows a promoted lesson pointing to `.claude/rules/security.md`. But zero example rules files exist in the repo.

### Fix 3: Add example `.claude/rules/code-quality.md`

**What:** Create `examples/rules/code-quality.md` with starter code quality rules: the simplicity override ("avoid over-engineering"), the no-speculation rule ("don't design for hypothetical future requirements"), and the guard-clause preference. Keep it to 15-20 lines.

**Why:** Provides a second example of what a rules file looks like, covering a different domain than security. Two examples establish the pattern better than one.

### Fix 4: Add "block commit when tests fail" hook

**What:** Create `examples/hook-block-commit-no-tests.sh` — a PreToolUse hook that blocks `git commit` when no test evidence exists in the current session. This is the hook described in the Build OS as the starter Tier 2 hook.

**Why:** This is the most frequently referenced hook in the entire framework (mentioned in the Build OS Part II, Part VIII, examples/README.md, and the bootstrap checklist) but it's the only one that doesn't have an example script.

### Fix 5: Add standalone `examples/settings.json`

**What:** Create `examples/settings.json` showing how to wire all 3 example hooks (block-env-write, test-after-edit, block-commit-no-tests) into Claude Code. Currently this content exists only as an inline code block in examples/README.md.

**Why:** A standalone file is more discoverable and copy-friendly than extracting JSON from a markdown code block.

### Fix 6: Add `templates/session-log.md`

**What:** Create a session-log template showing the expected entry format: date header, Decided/Implemented/Not Finished/Next Session bullets, separator between entries.

**Why:** session-log.md is referenced in the file tree, the session loop, and the handoff process. It's the only core file in the "minimum viable project" file tree that lacks a template.

### Fix 7: Fix `/setup` command to handle commands and template references

**What:** Update `.claude/commands/setup.md` to:
1. Explicitly instruct copying `.claude/commands/` to the user's project
2. Remove references to `templates/` directory (which won't exist in the user's project) — instead, embed the key template structures inline or instruct the user to reference the Build OS repo
3. For Tier 2: add creation of `.claude/rules/security.md` and `.claude/settings.json` with a starter hook

**Why:** Currently /setup creates docs and tasks files but doesn't ensure the slash commands are available in the user's project. It also references `templates/` which won't exist in the user's project directory.

### Fix 8: Add example `PERSONAS.md`

**What:** Create `examples/personas.md` with starter review personas: Architect (3-5 questions), Staff Engineer + Security (3-5 questions), Product/UX (3-5 questions). These should be the universal questions from the review-protocol template, expanded into the detailed checklist format that a growing team would use.

**Why:** The review-protocol template says "Create a PERSONAS.md file with detailed checklists per persona" but gives only one example question. Users need to see what a complete starter file looks like.

### Fix 9: Update `examples/README.md`

**What:** Update the hooks README to:
1. Reference the new third hook (block-commit-no-tests)
2. Reference the standalone settings.json file instead of inline JSON
3. Add a note about the example rules files

**Why:** Keep the examples README consistent with the actual examples directory contents.

### Fix 10: Add `templates/orchestration.md`

**What:** Create a lightweight orchestration document template with sections for: Objective (1 paragraph), Tracks (parallel work items with owner/status/blockers), Dependencies (what blocks what), Verification criteria (how to know it's done), and State file location.

**Why:** Orchestration documents are called "one of our highest-leverage patterns" in the Team Playbook but have no template. This is the missing piece for teams doing parallel work.

### Fix 11: Update `docs/the-build-os.md` bootstrap section

**What:** Add one line to the manual setup checklist mentioning that slash commands should be copied: "Copy `.claude/commands/` to your project for session operations (recall, plan, review, capture, sync, handoff, triage)."

**Why:** The bootstrap section currently only mentions /setup or the manual file creation path. It doesn't tell users about the slash commands that operate the session loop.

---

## What is NOT included (and why)

- **Example skill (SKILL.md)**: Skills are platform-specific (OpenClaw, Claude Code custom). The format varies. Teaching the concept is sufficient; providing an example that only works on one platform would mislead.
- **Example toolbelt script**: Language-specific. The pseudocode in the Build OS is intentionally language-agnostic. A Python example was debated and rejected in the prior additions debate.
- **Example smoke test**: Too implementation-specific. The "mocks that validated the bug" story teaches the principle effectively.
- **State file JSON example**: Adding this inline to the Team Playbook is sufficient — a standalone template file for a JSON blob is over-engineering.
- **Interface contract / spawn prompt examples**: Team Playbook concepts that are too context-dependent for generic templates.
- **Tier 3 starter artifacts**: Acknowledged as "custom engineering" — generic templates would be misleading.
- **tests/ directory**: The repo is a framework, not a testable project.

---

## What the challengers should evaluate

1. **Volume:** Are 11 fixes too many? Should they be batched or reduced?
2. **Scope creep:** Do any fixes add artifacts that will drift or become stale?
3. **Rules files:** Are the example rules too opinionated? Should they be more generic?
4. **PERSONAS.md:** Is this premature? The framework positions it as a "grow into it" artifact.
5. **Setup command:** Is the proposed fix sufficient, or does /setup need a more fundamental redesign?
6. **Orchestration template:** Is this over-engineering for a framework repo?
