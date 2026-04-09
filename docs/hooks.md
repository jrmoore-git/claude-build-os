# Hooks Reference

The Build OS ships five hooks. Four are PreToolUse enforcement hooks — they run before the matched tool executes, and can block or warn based on what they find. Each is scoped by a matcher pattern: plan-gate and review-gate match `Bash` (firing on `git commit`), while decompose-gate and tier-gate match `Write|Edit` (firing on file edits). The fifth, stop-autocommit, is a Stop hook that fires when the session ends.

Hooks are the third level of the enforcement ladder: advisory (CLAUDE.md) → rules (.claude/rules/) → **hooks** → architecture. They fire every time the matched tool is called, cannot be ignored by the model, and enforce governance as deterministic code.


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


## hook-stop-autocommit.py

Session safety net. When a Claude Code session exits without running `/wrap-session`, this hook auto-captures uncommitted work so nothing is lost.

**When it fires:** Stop hook (runs when the Claude Code session ends).

**What it does:**

1. Checks for uncommitted changes in the working tree
2. If changes exist, writes an auto-capture entry to `tasks/session-log.md` listing the changed files
3. Marks `docs/current-state.md` as stale by injecting a `## ⚠ STALE` warning after the first header line. The warning includes the auto-capture date, file count, and a notice that the "Next Action" section may be outdated
4. Stages all changed files plus the updated session log and current-state doc
5. Commits with message `[auto] Session work captured <date>`

**Staleness marking:** The stale marker in `current-state.md` is detected by `/recall`'s freshness check (`scripts/check-current-state-freshness.py`). When `/recall` sees the marker, it warns the user not to trust the frozen "Next Action" and derives recommendations from git log + session-log instead. The marker is idempotent — if `## ⚠ STALE` already exists, it won't add a duplicate.

**Pass conditions:** Always runs (stop hooks don't block). If there are no uncommitted changes, it exits silently.

**Wiring:**

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "command": "python3 hooks/hook-stop-autocommit.py"
      }
    ]
  }
}
```


## Wiring hooks into your project

Add hooks to `.claude/settings.json` (or `.claude/settings.local.json` for personal, non-committed settings). Each hook needs a matcher pattern and the script path.

### All five hooks

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "python3 hooks/hook-decompose-gate.py"
      },
      {
        "matcher": "Bash",
        "command": "bash hooks/hook-plan-gate.sh"
      },
      {
        "matcher": "Bash",
        "command": "bash hooks/hook-review-gate.sh"
      },
      {
        "matcher": "Write|Edit",
        "command": "bash hooks/hook-tier-gate.sh"
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "command": "python3 hooks/hook-stop-autocommit.py"
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
        "command": "bash hooks/hook-plan-gate.sh"
      }
    ]
  }
}
```

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
