---
scope: "Build skill linter, wire as hook, fix all 22 skills to pass canonical sections spec"
surfaces_affected: "scripts/lint_skills.py, hooks/hook-skill-lint.py, .claude/settings.json, .claude/skills/*/SKILL.md (22 files)"
verification_commands: "for skill in .claude/skills/*/SKILL.md; do python3.11 scripts/lint_skills.py \"$skill\" || echo \"FAIL: $skill\"; done"
rollback: "git revert <sha>"
review_tier: "Tier 2"
verification_evidence: "PENDING"
challenge_skipped: true
---

# Canonical Skill Sections — Build Plan

## Execution Strategy

**Decision:** hybrid (sequential linter build -> parallel skill fixes -> sequential hook wiring)
**Pattern:** pipeline + fan-out
**Reason:** Linter must exist before fixes can be verified. 22 skill edits are independent (no file overlaps). Hook depends on both.

| Subtask | Files | Depends On | Isolation |
|---------|-------|------------|-----------|
| A: Build linter | `scripts/lint_skills.py` | -- | main |
| B: Fix Tier 1 skills (5) | guide, log, triage, setup, audit | A | worktree |
| C: Fix Tier 2 group 1 (6) | challenge, design, elevate, explore, healthcheck, investigate | A | worktree |
| D: Fix Tier 2 group 2 (6) | plan, polish, pressure-test, research, review, ship | A | worktree |
| E: Fix Tier 2 group 3 (5) | simulate, start, sync, think, wrap | A | worktree |
| F: Wire hook + settings | `hooks/hook-skill-lint.py`, `.claude/settings.json` | A-E | main |

**Synthesis:** Main agent merges worktrees, runs linter across all 22, resolves conflicts, wires hook, runs full verification.

## Build Order

### Step 1: Build linter (`scripts/lint_skills.py`)

Python script. Accepts a file path argument. Validates against the refined spec.

Logic:
1. Read file, split frontmatter from body via regex (no PyYAML)
2. Parse frontmatter fields: name, description, version, tier, lint-exempt
3. Tier classification: use frontmatter `tier:` override if present, else heuristics:
   - Tier 2 if: >3 Step/Phase headings, mentions debate.py or scripts/*.py, contains Write/Edit keywords, contains Agent(/subagent, contains --mode/conditionals, specifies tasks/*/docs/* outputs
   - Otherwise Tier 1
4. All-tier checks:
   - `name` matches parent directory
   - `description` is quoted string (not block scalar)
   - `description` contains "Use when"
   - `version` matches semver pattern
   - Procedure heading exists (## Procedure, ## Steps, or ### Step N)
   - `DONE` appears in body + at least one of DONE_WITH_CONCERNS/BLOCKED/NEEDS_CONTEXT
5. Tier 2 checks:
   - `## Safety Rules` heading exists, body contains NEVER or "Do not"
   - Output Silence: contains "Output Silence" (case-insensitive) OR lint-exempt includes "output-silence"
   - Output Format: contains ## Output Format, ## Output, or ## Deliverable
   - Debate fallback (if body contains "debate.py"): within 5 lines above/below any "debate" match, one of: fallback, unavailable, fails, error
6. Exit 0 on pass. Exit 1 + list of violations on fail.

### Step 2: Fix skills in parallel (4 agents)

Each agent receives: the spec summary, the linter path, their skill batch.

**Tier 1 skills (agent B):** guide, log, triage, setup, audit
- Add `version: 1.0.0` to frontmatter
- Ensure description has "Use when" trigger phrase
- Ensure procedure section exists
- Add completion status codes (DONE, BLOCKED, NEEDS_CONTEXT)

**Tier 2 skills (agents C, D, E):** all of the above, plus:
- Add `## Safety Rules` with contextually appropriate NEVER/Do not prohibitions
- Add Output Silence reference (or `lint-exempt: ["output-silence"]` where intermediate output is the interface)
- Add `## Output Format` section
- Add debate fallback near debate.py references (for the 10 skills that use it)

Each agent runs the linter on every skill it edits to verify compliance.

### Step 3: Wire hook

Create `hooks/hook-skill-lint.py` (PreToolUse on Write/Edit):
- Match target path against `skills/*/SKILL.md` glob
- Run `scripts/lint_skills.py <path>` on the file content
- Block (exit 1) if linter fails
- Pass (exit 0) otherwise

Register in `.claude/settings.json` under PreToolUse hooks.

### Step 4: Verification

```bash
# All 22 skills must pass
for skill in .claude/skills/*/SKILL.md; do
  python3.11 scripts/lint_skills.py "$skill" || echo "FAIL: $skill"
done

# Verify hook blocks bad edits (manually test with a stripped skill)
```

## Files

| File | Action | Scope |
|------|--------|-------|
| `scripts/lint_skills.py` | create | ~150-200 lines, full linter |
| `hooks/hook-skill-lint.py` | create | ~30 lines, PreToolUse gate |
| `.claude/settings.json` | modify | add hook entry |
| 5 Tier 1 SKILL.md files | modify | add version, Use when, procedure, completion codes |
| 17 Tier 2 SKILL.md files | modify | above + Safety Rules, Output Silence, Output Format, debate fallback |

## Tier assignments

**Tier 1 (Utility):** audit, guide, log, setup, triage
**Tier 2 (Workflow):** challenge, design, elevate, explore, healthcheck, investigate, plan, polish, pressure-test, research, review, ship, simulate, start, sync, think, wrap

**Debate.py users (need fallback):** challenge, elevate, explore, healthcheck, investigate, polish, pressure-test, review, simulate, think
