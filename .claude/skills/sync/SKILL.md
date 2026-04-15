---
name: sync
description: "Sync project docs to match what shipped. Cross-references the git diff against all project docs, polishes CHANGELOG voice, checks cross-doc consistency. Never auto-commits. Use when asked to sync docs, update the docs, or post-ship docs. Suggest after a commit lands or code is shipped."
version: 1.0.0
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# Doc Sync: Post-Ship Documentation Update

You are running the `/sync` workflow. This runs **after code is committed**
but **before declaring the work done**. Your job: ensure every documentation file
in the project is accurate and up to date.

You are mostly automated. Make obvious factual updates directly. Stop and ask only
for risky or subjective decisions.

**Only stop for:**
- Risky/questionable doc changes (narrative, philosophy, security, removals, large rewrites)
- New items to add to `tasks/decisions.md`
- Cross-doc contradictions that are narrative (not factual)

**Never stop for:**
- Factual corrections clearly from the diff
- Adding items to tables/lists
- Updating paths, counts, version numbers
- Fixing stale cross-references
- CHANGELOG voice polish (minor wording adjustments)
- Cross-doc factual inconsistencies (e.g., version number mismatch)

**NEVER do:**
- Overwrite, replace, or regenerate CHANGELOG entries — polish wording only, preserve all content
- Auto-commit without presenting changes for review
- Use `Write` tool on CHANGELOG files — always use `Edit` with exact `old_string` matches

---

## Safety Rules

- NEVER auto-commit doc changes. All changes must be presented for user review first.
- Do not modify code files during doc sync — this skill updates documentation only.
- NEVER clobber or regenerate CHANGELOG entries from scratch.

**Output silence** — Do not emit text between tool calls. Single formatted output at the end only.

## Procedure

## Step 1: Pre-flight and Diff Analysis

1. Check the current branch and recent commits:

```bash
git branch --show-current
```

```bash
git log --oneline -20
```

```bash
git diff HEAD~5 --stat
```

```bash
git diff HEAD~5 --name-only
```

Adjust the range based on what the user shipped. If they specify a commit range
or say "since last session", use that instead.

2. Classify the changes into categories:
   - **New features** — new files, new commands, new skills, new capabilities
   - **Changed behavior** — modified services, updated APIs, config changes
   - **Removed functionality** — deleted files, removed commands
   - **Infrastructure** — build system, test infrastructure, CI

3. Output: "Analyzing N files changed across M commits. Checking project docs."

---

## Step 2: Per-File Documentation Audit

Read each documentation file and cross-reference against the diff.

**Target files (our doc structure):**

| File | What to check |
|------|--------------|
| `docs/current-state.md` | Does it reflect what is true NOW after this change? Stale descriptions, missing new components, wrong status. |
| `tasks/handoff.md` | Does next-session context reflect the work just completed? Stale blockers, completed items still listed as pending. |
| `tasks/decisions.md` | Were any decisions made during this work that aren't logged? Check commit messages and plan artifacts for decision signals. |
| `docs/CHANGELOG.md` (or project changelog) | Does the latest entry cover what actually shipped? Voice polish: lead with what the user can now DO. |
| `tasks/lessons.md` | Were any gotchas discovered during this work? Check for patterns that should be captured. |
| PRD file (per `docs/project-prd.md` pointer) | Only if changes affect PRD scope: new integrations, schedule changes, capability changes. Be conservative — most changes don't touch the PRD. |
| `CLAUDE.md` | Are listed commands, paths, environment details still accurate? Does the workflow routing section match current skills? |

For each file, classify needed updates as:

- **Auto-update** — Factual corrections clearly warranted by the diff: adding an item to a
  table, updating a path, fixing a count, updating a status.
- **Ask user** — Narrative changes, section removal, security model changes, large rewrites
  (more than ~10 lines in one section), ambiguous relevance, adding new sections.

---

## Step 3: Apply Auto-Updates

Make all clear, factual updates directly using the Edit tool.

For each file modified, output a one-line summary describing **what specifically changed**:
not "Updated current-state.md" but "current-state.md: updated skill count from 6 to 7,
added new-skill to active skills list."

**Never auto-update:**
- PRD positioning or strategy sections
- Security model descriptions
- Architecture philosophy or design rationale
- Do not remove entire sections from any document

---

## Step 4: Ask About Risky/Questionable Changes

For each risky or questionable update identified in Step 2, use AskUserQuestion:
- Context: which doc file, what we're reviewing
- The specific documentation decision
- RECOMMENDATION: Choose [X] because [one-line reason]
- Options including C) Skip — leave as-is

Apply approved changes immediately after each answer.

---

## Step 5: CHANGELOG Voice Polish

**NEVER CLOBBER CHANGELOG ENTRIES.**

This step polishes voice. It does NOT rewrite, replace, or regenerate content.

**Rules:**
1. Read the entire CHANGELOG first. Understand what is already there.
2. Only modify wording within existing entries. Never delete, reorder, or replace entries.
3. Never regenerate a CHANGELOG entry from scratch. The entry was written from the actual
   diff and commit history. It is the source of truth. You are polishing prose.
4. If an entry looks wrong or incomplete, use AskUserQuestion — do NOT silently fix it.
5. Use Edit tool with exact `old_string` matches.

**If CHANGELOG was not modified in the recent commits:** skip this step.

**If CHANGELOG was modified**, review the entry for voice:
- Lead with what the user can now **do** — not implementation details.
- "You can now..." not "Refactored the..."
- Flag and rewrite any entry that reads like a commit message.
- Auto-fix minor voice adjustments. Use AskUserQuestion if a rewrite would alter meaning.

---

## Step 6: Cross-Doc Consistency Check

After auditing each file individually, do a cross-doc consistency pass:

1. Does `docs/current-state.md` match what `tasks/handoff.md` says about current status?
2. Does `CLAUDE.md`'s environment section match reality?
3. Are decisions referenced in `tasks/handoff.md` logged in `tasks/decisions.md`?
4. Does the project changelog latest entry align with `docs/current-state.md`?
5. Flag any contradictions between documents. Auto-fix clear factual inconsistencies.
   Use AskUserQuestion for narrative contradictions.

---

## Step 7: Deferred Work Scan

Check the diff for `TODO`, `FIXME`, `HACK`, and `XXX` comments. For each one that
represents meaningful deferred work (not a trivial inline note), use AskUserQuestion
to ask whether it should be captured in `tasks/lessons.md` or `tasks/handoff.md`.

---

## Output Format

Final output is a summary of all documentation changes made, presented as a bullet list of file-level changes for user review before commit.

## Step 8: Present Changes for Review

**NEVER auto-commit.** This respects the commit doc update HARD RULE — the user
must review all doc changes before they are committed.

1. Run `git status` (never use `-uall`).
2. If no documentation files were modified, output "All documentation is up to date." and exit.
3. Run `git diff` to show all pending changes.
4. Present a summary of all changes made:

```
Documentation updates ready for review:

- [file]: [what changed]
- [file]: [what changed]
...

Review the diff above. When ready, commit these changes or ask me to adjust.
```

The user decides when and how to commit. Do not commit, do not push.

---

## Completion Status Protocol

When completing, report status using one of:
- **DONE** — All docs reviewed. Changes staged for user review.
- **DONE_WITH_CONCERNS** — Completed with issues. List each concern.
- **BLOCKED** — Cannot proceed. State what is blocking.
- **NEEDS_CONTEXT** — Missing information. State exactly what you need.
