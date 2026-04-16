# Hooks Reference

Build OS ships 20 hooks organized by event type. Hooks are the third level of the enforcement ladder: advisory (CLAUDE.md) → rules (.claude/rules/) → **hooks** → architecture. They fire every time the matched tool is called, cannot be ignored by the model, and enforce governance as deterministic code.

## Overview

| Hook | Event | Matcher | Behavior |
|------|-------|---------|----------|
| [hook-intent-router.py](#hook-intent-routerpy) | UserPromptSubmit | — | **Injects** skill routing suggestions based on user intent |
| [hook-decompose-gate.py](#hook-decompose-gatepy) | PreToolUse | Write\|Edit | **Blocks** first write until parallel decomposition is assessed |
| [hook-guard-env.sh](#hook-guard-envsh) | PreToolUse | Write\|Edit, Bash | **Blocks** .env writes and credential management commands |
| [hook-tier-gate.sh](#hook-tier-gatesh) | PreToolUse | Write\|Edit | **Blocks** Tier 1 file edits without debate artifacts |
| [hook-pre-edit-gate.sh](#hook-pre-edit-gatesh) | PreToolUse | Write\|Edit | **Blocks** protected file edits without a recent plan/proposal |
| [hook-memory-size-gate.py](#hook-memory-size-gatepy) | PreToolUse | Write\|Edit | **Blocks** MEMORY.md writes when file exceeds 150 lines |
| [hook-agent-isolation.py](#hook-agent-isolationpy) | PreToolUse | Agent | **Blocks** write-capable agents without worktree isolation |
| [hook-plan-gate.sh](#hook-plan-gatesh) | PreToolUse | Bash | **Blocks** commits to protected paths without a valid plan |
| [hook-review-gate.sh](#hook-review-gatesh) | PreToolUse | Bash | **Blocks** Tier 1 commits without debate artifacts |
| [hook-pre-commit-tests.sh](#hook-pre-commit-testssh) | PreToolUse | Bash | **Blocks** commits if pytest fails |
| [hook-prd-drift-check.sh](#hook-prd-drift-checksh) | PreToolUse | Bash | **Blocks** commits with 5+ unsynced decisions; warns at 3+ |
| [hook-bash-fix-forward.py](#hook-bash-fix-forwardpy) | PreToolUse | Bash | **Blocks** bandaid commands (rm lock files, kill -9) without investigation |
| [hook-syntax-check-python.sh](#hook-syntax-check-pythonsh) | PostToolUse | Write\|Edit | **Blocks** on Python syntax errors |
| [hook-ruff-check.sh](#hook-ruff-checksh) | PostToolUse | Write\|Edit | **Warns** on ruff lint violations (non-blocking) |
| [hook-post-tool-test.sh](#hook-post-tool-testsh) | PostToolUse | Write\|Edit | **Warns** — auto-runs pytest for toolbelt scripts |
| [hook-error-tracker.py](#hook-error-trackerpy) | PostToolUse | Bash | **Observes** — tracks recurring errors for proactive routing |
| [hook-read-before-edit.py](#hook-read-before-editpy) | PreToolUse + PostToolUse | Write\|Edit, Read | **Warns** if editing a file not recently read in session |
| [hook-skill-lint.py](#hook-skill-lintpy) | PostToolUse | Write\|Edit | **Warns** on SKILL.md frontmatter issues (description format, field validation) |
| [hook-spec-status-check.py](#hook-spec-status-checkpy) | PostToolUse | Read | **Warns** when reading spec files without `implementation_status` field |
| [hook-stop-autocommit.py](#hook-stop-autocommitpy) | Stop | — | Auto-captures uncommitted work on session exit |

---

## PreToolUse: Bash Hooks


## hook-plan-gate.sh

Gates commits to protected paths without a valid plan artifact.

**When it fires:** PreToolUse with `Bash` matcher, activates on `git commit` commands. Only runs its checks when staged files match protected globs from `config/protected-paths.json`.

**What it checks:**

1. Are any staged files in a protected path (and not in an exempt path)?
2. If yes, does a valid plan artifact exist in `tasks/`?

Protected paths (from `config/protected-paths.json`):
- `skills/**/*.md`
- `scripts/*_tool.py`
- `scripts/*_pipeline.py`
- `.claude/rules/*.md`

Exempt paths (always pass regardless of other rules):
- `tasks/*`
- `docs/*`
- `tests/*`
- `config/*`
- `stores/*`

**Pass conditions:**
- No staged files match protected globs (after excluding exempt paths)
- A valid plan artifact exists: any `tasks/*-plan.md` file with YAML frontmatter containing all required fields from `config/protected-paths.json`. If a `verification_evidence` field is present, its value must not be `PENDING` — but the field itself is not required by the config
- Commit message contains `[EMERGENCY]` (bypass with warning to stderr — no persistent audit trail; only the stderr warning)
- Config file `config/protected-paths.json` is missing, unreadable, or contains invalid JSON (fail-open in all three cases)

**Block conditions:**
- Staged files hit a protected glob, no valid plan artifact exists, and no `[EMERGENCY]` bypass
- Commit message contains `[TRIVIAL]` on protected paths (always blocked — `[TRIVIAL]` is not allowed for protected paths)

**Required plan artifact frontmatter** (fields from `config/protected-paths.json`):

```yaml
---
scope: "What this change does"
surfaces_affected: "What systems/files are touched"
verification_commands: "How to verify correctness"
rollback: "How to undo"
review_tier: "Tier 1|Tier 1.5|Tier 2"
verification_evidence: "Results of verification (if present, must not be PENDING)"
---
```

The five fields (`scope`, `surfaces_affected`, `verification_commands`, `rollback`, `review_tier`) are required by the config. `verification_evidence` is checked as an additional gate only if the field exists in the frontmatter — a plan without the field can still pass.

**Bypass:** `[EMERGENCY]` in the commit message skips the gate with a stderr warning. There is no persistent logging beyond stderr — if your project needs audit trails for emergency bypasses, add external logging. `[TRIVIAL]` is explicitly blocked on protected paths.


## hook-review-gate.sh

Gates commits to high-risk files without valid debate artifacts.

**When it fires:** PreToolUse with `Bash` matcher, activates on `git commit` commands.

**What it checks:**

1. Classifies all staged files as a single aggregate tier via `tier_classify.py --stdin` (uses the strictest tier across all files)
2. For Tier 1: requires debate artifacts newer than the staged files
3. For Tier 1.5 or risk-pattern matches: warns but does not block

**Pass conditions:**
- All staged files classify as Tier 2 or exempt (aggregate result is `ok`)
- Commit message contains `[TRIVIAL]` — **bypasses unconditionally**, including for Tier 1 files. This is checked before any file classification. Be aware: this means `[TRIVIAL]` can skip review-gate entirely even for trust-boundary changes
- A valid debate artifact exists in `tasks/` that is newer than the newest staged file:
  - `*-challenge.md` with YAML frontmatter (`debate_id:`), `MATERIAL` tag, and a verdict line (APPROVE/REVISE/REJECT)
  - `*-resolution.md` with a `## PM/UX Assessment` section
  - `*-review.md` (legacy compatibility — presence is sufficient, no content validation)

**Block conditions:**
- Tier 1 files staged without any valid debate artifact newer than the staged files

**Advisory (non-blocking):**
- Tier 1.5 files or Tier 2 files matching risk-pattern substrings (`skill`, `_tool.py`, `.claude/rules/`, `hook-`, or `security` in the filename) staged without debate artifacts → prints a notice to stdout suggesting a decision log entry. Note: this is substring matching, not classifier-driven — it may trigger on filenames that coincidentally contain these strings

Neither `[EMERGENCY]` nor any other bypass (besides `[TRIVIAL]`) is available in review-gate.


## hook-pre-commit-tests.sh

Blocks commits if the test suite fails.

**When it fires:** PreToolUse with `Bash` matcher, activates on `git commit` commands.

**What it checks:** Runs `pytest` against the project test suite. If any test fails, the commit is blocked.

**Pass conditions:**
- No `git commit` in the command
- All pytest tests pass (exit code 0)
- No tests exist (pytest returns "no tests collected")

**Block conditions:**
- Any pytest test fails — the commit is blocked with the test output shown

**Timeout:** 60 seconds (longest timeout of any hook — test suites can be slow).


## hook-prd-drift-check.sh

Prevents commits when too many decisions have accumulated without being synced to the PRD.

**When it fires:** PreToolUse with `Bash` matcher, activates on `git commit` commands.

**What it checks:** Counts decision entries in `tasks/decisions.md` that haven't been reflected in `docs/project-prd.md`.

**Pass conditions:**
- Fewer than 3 unsynced decisions
- No `git commit` in the command

**Advisory (non-blocking):**
- 3–4 unsynced decisions → prints a warning suggesting a PRD sync

**Block conditions:**
- 5 or more unsynced decisions → blocks the commit until the PRD is updated or decisions are marked as synced


## hook-bash-fix-forward.py

Blocks common "bandaid" bash commands that skip investigation.

**When it fires:** PreToolUse with `Bash` matcher.

**What it checks:** Scans the command for patterns that indicate a workaround rather than a root-cause fix:

| Blocked pattern | Required investigation first |
|----------------|----------------------------|
| `rm .git/index.lock` | `lsof .git/index.lock` or `pgrep git` |
| `kill -9` / `kill -KILL` | `ps aux` to identify the stuck process |
| `pkill <name>` | `pgrep -a <name>` to see what's running |
| `rm *.lock` / `rm *.pid` | `lsof <file>` or `fuser <file>` |

**Block conditions:**
- Any blocked pattern detected without evidence of prior investigation in the session

**Design rationale:** See `.claude/rules/bash-failures.md` for the full policy. Bandaid commands mask root causes. This hook enforces "diagnose first, fix second."

---

---

## PreToolUse: Write|Edit Hooks


## hook-decompose-gate.py

Forces decomposition assessment before the first write operation in each session.

**When it fires:** PreToolUse with `Write|Edit` matcher. Fires on every `Write` or `Edit` tool call, but only blocks until a session flag file exists.

**What it checks:**

1. Reads tool call JSON from stdin; extracts `tool_name`
2. Only gates `Write` and `Edit` — all other tools pass through
3. Checks for a session-scoped flag file at `/tmp/claude-decompose-{session_id}.json`
4. If flag file exists with `plan_submitted: true` or `bypass: true` → allow
5. If flag file is corrupt or unreadable → **deny** with recovery message (fail-closed)
6. If no flag file → **deny** with decomposition prompt

**Session ID:** Uses `$CLAUDE_SESSION_ID` if set, falls back to parent PID (`os.getppid()`).

**Pass conditions:**
- Tool is not `Write` or `Edit`
- Flag file exists with valid `plan_submitted` or `bypass` key
- Stdin is unreadable or tool call JSON is malformed (fail-open on infrastructure errors only)

**Block conditions:**
- First `Write` or `Edit` in a session before flag file exists → deny with full decomposition prompt
- Subsequent `Write` or `Edit` calls in the same batch (before the flag file is created) → deny with a short "waiting for assessment" message instead of repeating the full prompt. Uses a sentinel file (`/tmp/claude-decompose-{session_id}.pending`) to deduplicate — the sentinel is cleaned up once the real flag file exists
- Flag file exists but is corrupt JSON → deny with recovery instructions

**How to create the flag file:** The deny message instructs the agent to use `Bash` (not `Write`) to create the flag:
```bash
echo '{"plan_submitted": true}' > /tmp/claude-decompose-{session_id}.json
# or for bypass:
echo '{"bypass": true}' > /tmp/claude-decompose-{session_id}.json
```

This is critical: if the agent attempts to use the `Write` tool to create the flag file, it will be blocked by this very hook, creating an infinite loop.

**Design rationale:** Advisory rules for parallel decomposition were ignored for months across three escalation levels. This hook is Level 3 on the enforcement ladder — mechanical enforcement of a behavioral requirement that advisory text could not sustain.


## hook-tier-gate.sh

Classifies file tier before the first edit and gates accordingly.

**When it fires:** PreToolUse with `Write|Edit` matcher. Unlike the other two hooks (which fire on `git commit`), this one fires before file edits.

**What it checks:**

1. Extracts the `file_path` from the tool input
2. Classifies it via `tier_classify.py`
3. For Tier 1 files: checks whether a debate artifact exists in `tasks/` that is newer than the current session start
4. For Tier 1.5 files: issues an advisory warning

**Session dedup:** Uses marker files in `/tmp/build-os-tier-gate/` to avoid re-firing on every edit. Important: this directory is **global** — not scoped by project or repository. Once a tier is cleared in any project, the marker applies to all projects for 4 hours. The dedup is also **per-tier**, not per-file: once `tier1_passed` exists, all Tier 1 files pass regardless of which file originally triggered the clearance.

**Pass conditions:**
- File classifies as Tier 2 or exempt
- Tier already cleared (marker file exists and is less than 4 hours old — applies globally, not per-project)
- Tier 1: a debate artifact exists that is newer than the session start
  - `*-challenge.md` with YAML frontmatter (`debate_id:`) and MATERIAL tag (no verdict line required — less strict than review-gate)
  - `*-judgment.md` or `*-resolution.md` (presence is sufficient — no content validation)
- `tier_classify.py` fails or returns invalid JSON (fail-open, defaults to Tier 2)
- Tool input is not valid JSON or has no `file_path` (fail-open)

**Block conditions:**
- Tier 1 file edit attempted without any valid debate artifact from the current session. Block message includes the exact `debate.py challenge` command to run.

**Advisory (non-blocking):**
- Tier 1.5 file edit → prints a notice suggesting a quality review, then allows the edit

Neither `[EMERGENCY]` nor `[TRIVIAL]` bypass is available in tier-gate.


## hook-guard-env.sh

Protects credentials by blocking .env file writes and credential management commands.

**When it fires:** PreToolUse with `Write|Edit` and `Bash` matchers. Fires on both file edits and shell commands.

**What it checks:**

1. For Write|Edit: is the target file a `.env` file or a SKILL.md file?
2. For Bash: does the command include credential management operations (e.g., `gog auth`)?

**Block conditions:**
- Direct writes to `.env` files — asks for human approval
- Credential management commands in Bash
- Edits to SKILL.md files that could expose credentials

**Design rationale:** Secrets in `.env` are Tier 1 data. Accidental overwrites or exposure are high-blast-radius and hard to reverse. This hook ensures human oversight on all credential-adjacent operations.


## hook-pre-edit-gate.sh

Prevents edits to protected files unless a plan or proposal artifact was recently modified.

**When it fires:** PreToolUse with `Write|Edit` matcher.

**What it checks:**

1. Is the target file in a protected path? (matches `scripts/*_tool.py`, `scripts/*_pipeline.py`, `skills/**/*.md`, `.claude/rules/*.md`)
2. If yes, was any plan or proposal artifact (`tasks/*-plan.md`, `tasks/*-proposal.md`) modified in the last 2 hours?

**Pass conditions:**
- File is not in a protected path
- A plan or proposal artifact was modified within the last 2 hours

**Block conditions:**
- Protected file edit attempted without a recent plan or proposal artifact

**Relationship to plan-gate:** The plan gate blocks *commits* without a valid plan. The pre-edit gate blocks *edits* without a recent plan — it fires earlier in the workflow, before code is even written.


## hook-memory-size-gate.py

Prevents the auto-memory index (`MEMORY.md`) from growing unbounded.

**When it fires:** PreToolUse with `Write|Edit` matcher, only for MEMORY.md files.

**What it checks:**

1. Is the target file a MEMORY.md?
2. If yes, is the file already at or above 150 lines?
3. Would this edit add more lines?

**Block conditions:**
- MEMORY.md is at or above 150 lines and the edit would add content

The deny message instructs the agent to prune existing entries before adding new ones.

---

## PreToolUse: Agent Hooks


## hook-agent-isolation.py

Enforces worktree isolation for write-capable agents dispatched during parallel plans.

**When it fires:** PreToolUse with `Agent` matcher. Only activates when a parallel plan is in progress (detected via decomposition flag file).

**What it checks:**

1. Is a parallel plan active? (checks for `plan_submitted: true` in the decomposition flag file)
2. Is the agent being dispatched write-capable? (has edit/write permissions)
3. Does the agent specify `isolation: "worktree"`?

**Pass conditions:**
- No parallel plan is active (bypass flag or no flag file)
- Agent is read-only (Explore, research agents)
- Agent specifies worktree isolation

**Block conditions:**
- Parallel plan active and agent dispatched without `isolation: "worktree"` and agent is write-capable

**Design rationale:** Multiple write-capable agents editing the same checkout cause file collisions, merge conflicts, and `index.lock` contention. Worktree isolation gives each agent its own git checkout. This was enforced as a hook after repeated incidents of parallel agents trampling each other's work.

---

## PostToolUse: Write|Edit Hooks

These hooks run *after* a file is written or edited. They validate the result and surface issues immediately.


## hook-syntax-check-python.sh

Validates Python syntax after every write or edit to a `.py` file.

**When it fires:** PostToolUse with `Write|Edit` matcher. Only activates for Python files.

**What it checks:** Runs `python3 -m py_compile` on the edited file.

**Pass conditions:**
- File is not a `.py` file
- Python syntax is valid

**Block conditions:**
- Python syntax error detected — the edit is flagged and the error message is shown

**Why PostToolUse, not PreToolUse:** The file must exist with the new content before syntax can be checked. This catches errors immediately after the write so they can be fixed in the same turn.


## hook-ruff-check.sh

Runs the ruff linter on Python files after edits.

**When it fires:** PostToolUse with `Write|Edit` matcher. Only activates for Python files.

**What it checks:** Runs `ruff check` with complexity (C901) and line length (E501) rules.

**Behavior:** Non-blocking — displays lint violations but does not prevent the edit. The agent sees the warnings and can choose to fix them.

**Timeout:** 15 seconds.


## hook-post-tool-test.sh

Auto-runs the corresponding test file when a toolbelt script is edited.

**When it fires:** PostToolUse with `Write|Edit` matcher. Only activates for `scripts/*_tool.py` files.

**What it does:** When a toolbelt script is edited, looks for a matching test file (`tests/test_<name>.py`) and runs `pytest` on it.

**Behavior:** Non-blocking — shows test results but does not prevent the edit. Gives immediate feedback on whether the change broke existing tests.

**Timeout:** 60 seconds.

---

## UserPromptSubmit Hooks


## hook-intent-router.py

Deterministic skill routing. Classifies user intent via keyword matching and injects routing suggestions into Claude's context before processing. Also checks for recurring-error flags set by hook-error-tracker.py.

**When it fires:** Every user message submission.

**What it does:**

1. Reads the user's message from stdin (`prompt` field)
2. Matches against intent patterns (diagnostic, feature, planning, review, shipping, etc.)
3. If a pattern matches, outputs a routing suggestion as plain text (injected into Claude's context)
4. Checks for recurring-error flags from hook-error-tracker.py — if the same error class appeared 2+ times, injects a proactive `/investigate` suggestion
5. Tracks suggestions per session to avoid nagging (each skill suggested at most once per session)

**Key behaviors:**
- First match wins — patterns are ordered by specificity
- Simple tasks ("fix the typo on line 42") produce no suggestion — no pattern matches
- Session-scoped: suggestions reset each session via temp files (`/tmp/claude-intent-suggestions-{session_id}.json`)
- Output is advisory context, not a block — Claude can still override if the suggestion doesn't fit

**Timeout:** 2 seconds.

---

## PostToolUse: Bash Hooks


## hook-error-tracker.py

Passive error observer. Tracks recurring Bash failures in a session-scoped temp file. When the same error class appears 2+ times, hook-intent-router.py picks up the flag on the next user message and suggests `/investigate`.

**When it fires:** After every Bash tool call.

**What it does:**

1. Reads the Bash tool input and result from stdin
2. Checks for failure indicators (non-zero exit code, error keywords in output)
3. Normalizes the command to an error signature (groups by base command + subcommand, ignoring flags — so `npm test` and `npm test --verbose` are the same class)
4. Writes the error count to a session-scoped temp file (`/tmp/claude-error-tracker-{session_id}.json`)

**Key behaviors:**
- Observe-only — never blocks or warns directly
- The intent router reads the tracker file on next UserPromptSubmit
- Normalizer groups `git push` and `git push --force` as same class, but `git push` and `git pull` as different
- Temp files are session-scoped and cleaned up automatically

**Timeout:** 2 seconds.

---

## Stop Hooks


## hook-stop-autocommit.py

Session safety net. When a Claude Code session exits without running `/wrap`, this hook auto-captures uncommitted work so nothing is lost.

**When it fires:** Stop hook (runs when the Claude Code session ends).

**What it does:**

1. Checks for uncommitted changes in the working tree
2. If changes exist, writes an auto-capture entry to `tasks/session-log.md` listing the changed files
3. Marks `docs/current-state.md` as stale by injecting a `## ⚠ STALE` warning after the first header line. The warning includes the auto-capture date, file count, and a notice that the "Next Action" section may be outdated
4. Stages all changed files plus the updated session log and current-state doc
5. Commits with message `[auto] Session work captured <date>`

**Staleness marking:** The stale marker in `current-state.md` is detected by `/start`'s freshness check (`scripts/check-current-state-freshness.py`). When `/start` sees the marker, it warns the user not to trust the frozen "Next Action" and derives recommendations from git log + session-log instead. The marker is idempotent — if `## ⚠ STALE` already exists, it won't add a duplicate.

**Pass conditions:** Always runs (stop hooks don't block). If there are no uncommitted changes, it exits silently.


## Wiring hooks into your project

Add hooks to `.claude/settings.json` (or `.claude/settings.local.json` for personal, non-committed settings). Each hook needs a matcher pattern and the script path.

### All 20 hooks (full Build OS)

This matches the actual wiring in the Build OS `.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {"type": "command", "command": "python3 hooks/hook-intent-router.py", "timeout": 2}
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {"type": "command", "command": "python3 hooks/hook-decompose-gate.py", "timeout": 2},
          {"type": "command", "command": "bash hooks/hook-guard-env.sh", "timeout": 10},
          {"type": "command", "command": "bash hooks/hook-tier-gate.sh \"$TOOL_INPUT\"", "timeout": 10},
          {"type": "command", "command": "bash hooks/hook-pre-edit-gate.sh", "timeout": 10},
          {"type": "command", "command": "python3 hooks/hook-memory-size-gate.py", "timeout": 2},
          {"type": "command", "command": "HOOK_EVENT=PreToolUse python3 hooks/hook-read-before-edit.py", "timeout": 2}
        ]
      },
      {
        "matcher": "Agent",
        "hooks": [
          {"type": "command", "command": "python3 hooks/hook-agent-isolation.py", "timeout": 2}
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "bash hooks/hook-guard-env.sh", "timeout": 10},
          {"type": "command", "command": "bash hooks/hook-pre-commit-tests.sh", "timeout": 60},
          {"type": "command", "command": "bash hooks/hook-prd-drift-check.sh", "timeout": 10},
          {"type": "command", "command": "bash hooks/hook-review-gate.sh", "timeout": 10},
          {"type": "command", "command": "bash hooks/hook-plan-gate.sh", "timeout": 10},
          {"type": "command", "command": "python3 hooks/hook-bash-fix-forward.py", "timeout": 5}
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {"type": "command", "command": "bash hooks/hook-syntax-check-python.sh", "timeout": 30},
          {"type": "command", "command": "bash hooks/hook-post-tool-test.sh", "timeout": 60},
          {"type": "command", "command": "bash hooks/hook-ruff-check.sh", "timeout": 15},
          {"type": "command", "command": "python3 hooks/hook-skill-lint.py", "timeout": 10}
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "python3 hooks/hook-error-tracker.py", "timeout": 2}
        ]
      },
      {
        "matcher": "Read",
        "hooks": [
          {"type": "command", "command": "python3 hooks/hook-spec-status-check.py", "timeout": 5},
          {"type": "command", "command": "HOOK_EVENT=PostToolUse python3 hooks/hook-read-before-edit.py", "timeout": 2}
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {"type": "command", "command": "python3 hooks/hook-stop-autocommit.py", "timeout": 30}
        ]
      }
    ]
  }
}
```

### Plan gate only (recommended starting point)

If you only want one hook, start with the plan gate. It enforces the highest-value discipline (plan before code on protected paths) with the lowest friction.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "bash hooks/hook-plan-gate.sh", "timeout": 10}
        ]
      }
    ]
  }
}
```

### Incremental adoption

Add hooks in order of value. Each row adds one capability:

| Level | Add these hooks | What you get |
|-------|----------------|-------------|
| **1** | plan-gate | Plans required before commits to protected paths |
| **2** | + pre-commit-tests, syntax-check-python | Tests must pass, no broken syntax |
| **3** | + review-gate, tier-gate | Cross-model review enforced for high-risk files |
| **4** | + decompose-gate, agent-isolation | Parallel work gated and isolated |
| **5** | + all remaining | Full governance: env protection, linting, drift checks, auto-capture |

### Configuration

The plan gate reads its protected paths, exempt patterns, and required frontmatter fields from `config/protected-paths.json`. Edit that file to customize what's protected in your project:

```json
{
  "protected_globs": [
    "skills/**/*.md",
    "scripts/*_tool.py",
    "scripts/*_pipeline.py",
    ".claude/rules/*.md"
  ],
  "exempt_patterns": [
    "tasks/*",
    "docs/*",
    "tests/*",
    "config/*",
    "stores/*"
  ],
  "required_plan_fields": [
    "scope",
    "surfaces_affected",
    "verification_commands",
    "rollback",
    "review_tier"
  ]
}
```

The review gate and tier gate use `tier_classify.py` for classification. To customize which files trigger which tier, edit the pattern lists at the top of `scripts/tier_classify.py`.
