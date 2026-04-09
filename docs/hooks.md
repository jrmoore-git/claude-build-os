# Hooks Reference

The Build OS ships three enforcement hooks. Each is a shell script configured as a Claude Code PreToolUse hook — it runs before the matched tool executes, and can block or warn based on what it finds. Each hook is scoped by a matcher pattern: plan-gate and review-gate match `Bash` (firing on `git commit`), while tier-gate matches `Write|Edit` (firing on file edits).

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
        "matcher": "Write|Edit",
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
