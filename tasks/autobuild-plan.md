---
scope: "Add --build flag to /plan --auto: autonomous build-test-iterate loop with scope enforcement, verification safety, and context management"
surfaces_affected: ".claude/skills/plan/SKILL.md, scripts/autobuild-scope-check.sh, scripts/autobuild-verify-cmd.py"
verification_commands: "grep -q 'build Mode' .claude/skills/plan/SKILL.md && python3.11 scripts/autobuild-verify-cmd.py --test && bash scripts/autobuild-scope-check.sh --test"
rollback: "git revert <sha>"
review_tier: "Tier 2"
verification_evidence: "PENDING"
challenge_artifact: "tasks/autobuild-challenge.md"
challenge_recommendation: "PROCEED-WITH-FIXES"
---

# Plan: Autobuild Mode v1

## Context

Challenge gate: PROCEED-WITH-FIXES (cross-model `--deep` pipeline). Refined spec: `tasks/autobuild-refined.md`. Four material findings accepted and addressed in refined spec: inline escalation definitions, context management, hard scope enforcement, verification command safety.

## Build Order

### Step 1: Create `scripts/autobuild-scope-check.sh`

Post-step scope enforcement script.

- **Input:** plan file path (to extract `surfaces_affected` from frontmatter), git ref of last checkpoint (default: HEAD~1)
- **Output:** exit 0 if all changed files are within scope; exit 1 + list of violating files if not
- **Logic:**
  1. Parse `surfaces_affected` from plan frontmatter
  2. Run `git diff --name-only <checkpoint-ref>` to get changed files
  3. Check each changed file is in the allowed set
  4. Print violations and exit 1 on any mismatch
- **`--test` flag:** self-test mode that validates the script works against a mock scenario
- ~25 lines

### Step 2: Create `scripts/autobuild-verify-cmd.py`

Verification command validator.

- **Input:** plan file path (to extract `verification_commands` from frontmatter)
- **Output:** JSON list of `{command, safe: bool, reason}` for each verification command
- **Allowlist (derived from repo config):**
  - Test runners: `pytest`, `npm test`, `pnpm test`, `go test`, `bash tests/run_all.sh`
  - Linters: `ruff check`, `npm run lint`, `pnpm lint`, `cargo fmt --check`
  - Build/typecheck: `npm run build`, `tsc --noEmit`
  - Repo-specific: scripts already in `tests/` or declared in `package.json`/`pyproject.toml`
- **Reject rules:** shell chaining (`&&`, `;`, `|`), redirects, command substitution, `curl`/`wget`, `rm`, `git reset`, package installs, env mutation
- **`--test` flag:** self-test mode with known-safe and known-unsafe command examples
- ~50 lines

### Step 3: Add `--build` mode to `plan/SKILL.md` (depends on 1, 2)

Add `## --build Mode (Autonomous Build Pipeline)` section after the existing `--auto` section.

Contents (from refined spec `tasks/autobuild-refined.md`):

1. **Build phase behavior** — 8-step procedure:
   - Read approved plan (parse steps, surfaces_affected, verification_commands)
   - Load project lessons before editing
   - Implement sequentially by default
   - Run validated verification after each step (calls `autobuild-verify-cmd.py`)
   - Run mandatory scope enforcement after each step (calls `autobuild-scope-check.sh`)
   - Escalate on 7 defined stop conditions
   - Decision classification (mechanical/taste/user-challenge)
   - After all steps: final verification → `/review` → ship summary

2. **7 explicit stop conditions** (inline, no external references):
   - Repeated-failure (3 attempts same step)
   - Scope-growth (file outside `surfaces_affected`)
   - Security-sensitive (auth, secrets, permissions, payments, network exposure)
   - Irreversible side effects (data deletion, history rewrite, destructive migrations)
   - Ambiguity (user-visible/API-visible behavior change)
   - Architecture-decision (beyond approved plan)
   - Constraint-conflict (plan + repo state + tests incompatible)

3. **Context management:**
   - Small-plan-only constraint
   - Checkpoint after every step (step, files changed, verification result, open issues)
   - Pause/resume on low context → emit `tasks/<topic>-autobuild-checkpoint.md`
   - No silent compression — must checkpoint before continuing past truncation

4. **Verification command safety:**
   - Run `python3.11 scripts/autobuild-verify-cmd.py --plan tasks/<topic>-plan.md`
   - Execute only commands marked `safe: true`
   - Stop and ask human for any `safe: false` command

5. **Scope enforcement:**
   - After each build step: `bash scripts/autobuild-scope-check.sh tasks/<topic>-plan.md`
   - Hard stop on exit 1 — surface violating files, require plan amendment or rollback

6. **Checkpoint/resume artifact format:**
   ```
   tasks/<topic>-autobuild-checkpoint.md
   ---
   topic: <topic>
   step_completed: <N of M>
   remaining_steps: [list]
   files_changed: [list]
   last_verification: pass|fail
   blockers: [list or none]
   ---
   ```

~120 lines added to SKILL.md

## Files

| File | Action | Scope |
|---|---|---|
| `.claude/skills/plan/SKILL.md` | Modify | Add `--build` mode section after `--auto` |
| `scripts/autobuild-scope-check.sh` | Create | Post-step diff-vs-scope enforcement |
| `scripts/autobuild-verify-cmd.py` | Create | Verification command allowlist validator |

## Execution Strategy

**Decision:** sequential
**Pattern:** pipeline
**Reason:** Step 3 references scripts from steps 1-2 by name and must describe their interfaces accurately. All files are non-overlapping but logically dependent.

## Verification

```bash
# Scripts exist and are functional
test -x scripts/autobuild-scope-check.sh && echo "scope check exists"
test -f scripts/autobuild-verify-cmd.py && echo "verify cmd exists"

# SKILL.md has the new section
grep -q "build Mode" .claude/skills/plan/SKILL.md && echo "build mode section present"

# Scope check self-test
bash scripts/autobuild-scope-check.sh --test

# Verify cmd self-test
python3.11 scripts/autobuild-verify-cmd.py --test
```
