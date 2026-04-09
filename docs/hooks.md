# Hooks Reference

The Build OS ships three enforcement hooks. Each is a shell script that fires as a Claude Code PreToolUse hook — it runs before the tool executes, and can block or warn based on what it finds.

Hooks are the third level of the enforcement ladder: advisory (CLAUDE.md) → rules (.claude/rules/) → **hooks** → architecture. They fire every time, cannot be ignored by the model, and enforce governance as deterministic code.


## hook-plan-gate.sh

Gates commits to protected paths without a valid plan artifact.

**When it fires:** PreToolUse, on `git commit` commands. Only activates when staged files match protected globs from `config/protected-paths.json`.

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
- A valid plan artifact exists: any `tasks/*-plan.md` file with YAML frontmatter containing all required fields AND `verification_evidence` is not `PENDING`
- Commit message contains `[EMERGENCY]` (bypass with audit warning to stderr)
- Config file `config/protected-paths.json` is missing (fail-open)

**Block conditions:**
- Staged files hit a protected glob, no valid plan artifact exists, and no `[EMERGENCY]` bypass
- Commit message contains `[TRIVIAL]` on protected paths (always blocked — `[TRIVIAL]` is not allowed for protected paths)

**Required plan artifact frontmatter:**

```yaml
---
scope: "What this change does"
surfaces_affected: "What systems/files are touched"
verification_commands: "How to verify correctness"
rollback: "How to undo"
review_tier: "Tier 1|Tier 1.5|Tier 2"
verification_evidence: "Results of verification (must not be PENDING)"
---
```

The `verification_evidence` field is the key gate: it must contain actual evidence, not the placeholder value `PENDING`. This forces verification to happen before the commit, not after.

**Bypass:** `[EMERGENCY]` in the commit message skips the gate with a stderr warning. This is logged and audited in weekly review. `[TRIVIAL]` is explicitly blocked on protected paths.


## hook-review-gate.sh

Gates commits to high-risk files without valid debate artifacts.

**When it fires:** PreToolUse, on `git commit` commands.

**What it checks:**

1. Classifies all staged files via `tier_classify.py`
2. For Tier 1 files: requires debate artifacts (challenge, resolution, or review file) newer than the staged files
3. For advisory-level files (Tier 1.5 or risk-flagged Tier 2): warns but does not block

**Pass conditions:**
- All staged files classify as Tier 2 or exempt
- Commit message contains `[TRIVIAL]` (bypass with notice — allowed here, unlike plan-gate)
- A valid debate artifact exists in `tasks/` that is newer than the staged files:
  - `*-challenge.md` with YAML frontmatter (`debate_id:`), `MATERIAL` tag, and a verdict line (APPROVE/REVISE/REJECT)
  - `*-resolution.md` with a `## PM/UX Assessment` section
  - `*-review.md` (legacy compatibility — presence is sufficient)

**Block conditions:**
- Tier 1 files staged without any valid debate artifact newer than the staged files

**Advisory (non-blocking):**
- Tier 1.5 or risk-flagged files (skills, `*_tool.py`, `.claude/rules/`, hook scripts, security files) staged without debate artifacts → prints a notice to stderr suggesting a decision log entry


## hook-tier-gate.sh

Classifies file tier before the first edit and gates accordingly.

**When it fires:** PreToolUse, on `Write` or `Edit` tool calls. Unlike the other two hooks (which fire on `git commit`), this one fires before file edits.

**What it checks:**

1. Extracts the `file_path` from the tool input
2. Classifies it via `tier_classify.py`
3. For Tier 1 files: checks whether a debate artifact (challenge or judgment file) exists in `tasks/` that is newer than the current session start
4. For Tier 1.5 files: issues an advisory warning

**Session dedup:** Uses a marker file in `/tmp/build-os-tier-gate/` to avoid re-firing on every single edit. Once a tier has been classified and cleared (or warned) for a session, the gate passes for 4 hours.

**Pass conditions:**
- File classifies as Tier 2 or exempt
- Tier already cleared in this session (marker file exists and is less than 4 hours old)
- Tier 1: a valid debate artifact exists that is newer than the session start
  - `*-challenge.md` with YAML frontmatter and MATERIAL tag
  - `*-judgment.md` or `*-resolution.md` (presence is sufficient)

**Block conditions:**
- Tier 1 file edit attempted without any valid debate artifact from the current session. Block message includes the exact `debate.py challenge` command to run.

**Advisory (non-blocking):**
- Tier 1.5 file edit → prints a notice suggesting a quality review, then allows the edit


## Wiring hooks into your project

Add hooks to `.claude/settings.json` (or `.claude/settings.local.json` for personal, non-committed settings). Each hook needs a matcher pattern and the script path.

### All three hooks

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "bash hooks/hook-plan-gate.sh"
      },
      {
        "matcher": "Bash",
        "command": "bash hooks/hook-review-gate.sh"
      },
      {
        "matcher": "Bash|Write|Edit",
        "command": "bash hooks/hook-tier-gate.sh"
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
    ".claude/rules/*.md"
  ],
  "exempt_patterns": [
    "tasks/*",
    "docs/*",
    "tests/*"
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
