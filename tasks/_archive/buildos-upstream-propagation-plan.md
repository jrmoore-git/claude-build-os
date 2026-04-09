---
scope: "Establish structural framework/project boundary in OpenClaw rules + sync script to push framework files to claude-build-os"
surfaces_affected: ".claude/rules/code-quality.md, .claude/rules/design.md, .claude/rules/orchestration.md, .claude/rules/session-discipline.md, .claude/rules/workflow.md, scripts/buildos-sync.sh"
verification_commands: "grep -rn 'Justin\\|Jarvis\\|openclaw\\|OpenClaw\\|innovius\\|cloudzero\\|/Users/macmini' .claude/rules/*.md | grep -v reference/ && bash scripts/buildos-sync.sh --dry-run"
rollback: "git revert per commit — no state changes, no databases, no infrastructure"
review_tier: "Tier 2"
verification_evidence: "PENDING"
challenge_artifact: "tasks/buildos-upstream-propagation-challenge.md"
design_doc: "tasks/buildos-upstream-propagation-design.md"
---

# Plan: BuildOS Upstream Propagation

## Context

BuildOS is a shared Claude Code governance framework distributed via GitHub (claude-build-os). Improvements discovered during OpenClaw production work don't flow upstream because: (1) generalization is hard, (2) framework/project boundary is blurry. Solution: make the boundary structural so sync becomes trivial copy.

**Audit results (go/no-go passed):** Only 8 project-specific lines across 5 framework rule files (1-6% per file). Well under the 30% threshold.

## Build Order

### Step 1: Clean framework rule files (5 files, 8 lines)

Move project-specific lines from `.claude/rules/*.md` to `.claude/rules/reference/*.md`. Generalize examples.

| File | Lines to move/change | What |
|------|---------------------|------|
| `code-quality.md` | 3 lines (L29, L33, L39) | Granola doc ID validation, CAZ misattribution rationale, CloudZero email example → generalize to generic examples |
| `design.md` | 1 line (L4) | `jarvis-app/**` glob → remove or generalize to `app/**` |
| `orchestration.md` | 1 line (L43) | `/Users/macmini/openclaw/primitives/synthesis.py` → `src/module.py` |
| `session-discipline.md` | 2 lines (L17, L34) | "Justin" → "the user" or "the owner" |
| `workflow.md` | 1 line (L65) | Project-specific shipping goal → move to reference/ |

### Step 2: Write `scripts/buildos-sync.sh` (new file, ~80 lines)

Sync script with:
- File manifest defining exactly which files sync (framework layer only)
- Diff framework files between OpenClaw and claude-build-os
- Banned-terms security scan — **hard gate, aborts if any match**
- Modes: `--dry-run` (default), `--commit`, `--push`
- Banned terms list: Justin, Jarvis, openclaw, OpenClaw, innovius, Innovius, cloudzero, CloudZero, /Users/macmini, @innovius, @cloudzero, TELEGRAM, telegram, 8387329260, sk-ant, xoxb-, xapp-, GOG_KEYRING, JUSTIN_TELEGRAM, AFFINITY_API

### Step 3: Run first sync (validate end-to-end)

1. `buildos-sync.sh --dry-run` → review diff
2. `buildos-sync.sh --commit` → commit to claude-build-os
3. Verify security scan passes on claude-build-os

### Step 4 (v1.1 — deferred): CLAUDE.md split + debate.py cleanup

- Extract framework operating rules from CLAUDE.md to `.claude/rules/` files
- Make debate.py `PROJECT_ROOT` dynamic (git root detection)
- These are lower priority — the rule files are the immediate win

## Execution Strategy

**Decision:** hybrid
**Pattern:** fan-out + sequential synthesis
**Reason:** Rule cleanup (5 files) and sync script (1 new file) have zero file overlap. First sync depends on both completing.

| Subtask | Files | Depends On | Isolation |
|---------|-------|------------|-----------|
| A: Rule cleanup | 5 `.claude/rules/*.md` files | — | worktree |
| B: Sync script | `scripts/buildos-sync.sh` | — | worktree |
| C: First sync | (reads both repos) | A, B | sequential |

**Synthesis:** Main agent merges worktree branches, runs `buildos-sync.sh --dry-run` to validate end-to-end.

## Verification

```bash
# 1. Security scan on framework files (must return zero results)
grep -rn 'Justin\|Jarvis\|openclaw\|OpenClaw\|innovius\|cloudzero\|/Users/macmini' .claude/rules/*.md | grep -v reference/

# 2. Sync script dry-run
bash scripts/buildos-sync.sh --dry-run

# 3. Security scan on claude-build-os after sync
grep -rn 'Justin\|Jarvis\|openclaw\|OpenClaw\|innovius\|cloudzero\|/Users/macmini' /Users/macmini/claude-build-os/ -r --include='*.md' --include='*.py' --include='*.sh' | grep -v '.git/'
```

## Files

| File | Action | Scope |
|------|--------|-------|
| `.claude/rules/code-quality.md` | Modify | Move 3 project-specific lines to reference/, generalize examples |
| `.claude/rules/design.md` | Modify | Remove/generalize jarvis-app glob |
| `.claude/rules/orchestration.md` | Modify | Generalize absolute path example |
| `.claude/rules/session-discipline.md` | Modify | Replace "Justin" → "the user" (2 lines) |
| `.claude/rules/workflow.md` | Modify | Move project-specific shipping goal to reference/ |
| `scripts/buildos-sync.sh` | Create | Sync script with manifest, diff, scan, copy modes |
