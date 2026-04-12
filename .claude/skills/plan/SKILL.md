---
name: plan
description: "Auto-generate plan artifact with valid frontmatter. Satisfies hook-plan-gate.sh for protected paths."
user-invocable: true
---

# /plan — Generate Plan Artifact

Auto-generate the plan artifact that `hook-plan-gate.sh` requires for protected paths.

## Procedure

### Step 1: Get topic and context

Ask the user for a topic name if not provided as an argument.

Check for a `/think` design doc or brief:
```bash
test -f tasks/<topic>-design.md && echo "design doc found" || test -f tasks/<topic>-think.md && echo "brief found" || echo "none"
```

If found, read it (design doc takes precedence over brief).

If not found, ask the user: "No design doc or brief found. What's the scope of this change? What files will you modify? Consider running `/think refine` first."

### Step 1b: Challenge gate

Check for a `/challenge` artifact:
```bash
test -f tasks/<topic>-challenge.md && echo "found" || echo "none"
```

**If found — validate:**

1. **Slug match:** Verify `topic_slug` in frontmatter matches the plan topic exactly.
2. **Freshness:** Check the `date` field in frontmatter. Default freshness window is 7 days. If older, warn: "Challenge artifact is >7 days old. Consider re-running `/challenge <topic>`." This is advisory, not blocking.
3. **Required sections:** Verify the artifact contains: Proposal Summary, Challenger Findings, Recommendation, Simpler Alternative, Override.
4. **Recommendation:** Read and honor:
   - `proceed` → continue planning
   - `simplify` → plan must implement the Simpler Alternative section, not the original scope
   - `pause` → hard stop until evidence/prerequisites addressed
   - `reject` → hard stop unless explicitly overridden (see override policy in `.claude/rules/reference/review-protocol.md`)

Note the recommendation to the user: "Challenge recommended `<recommendation>`."

**If not found + `--skip-challenge`:** Continue with a note: "Challenge gate skipped (`--skip-challenge`)." Log `challenge_skipped: true` in plan frontmatter. Honor `/challenge` bypass rules: bugfixes, test-only, docs, trivial, reduction refactors.

**If not found + no skip:** Ask: "No challenge artifact found. Is this a bugfix, test addition, docs update, or trivial refactor? (y → skip challenge, n → run `/challenge <topic>` first)"

### Step 2: Identify files and classify tier

From the user's description (or think brief), list the files that will be created or modified.

Classify:
```bash
echo "<file list, one per line>" | python3.11 scripts/tier_classify.py --stdin
```

Parse the JSON output to determine the review tier.

### Step 3: Three-lens analysis

Work through these lenses sequentially. Keep each brief — 2-3 bullets max per lens.

**Architecture lens:**
- What are the boundaries between components?
- What are the failure modes? What happens if external calls fail?
- What depends on what? Are there ordering constraints?

**UX lens:**
- What's the user-visible value?
- Is there a simpler alternative that delivers 80% of the value?

**Staff lens:**
- Is this feasible in one session?
- What's the rollback path?
- What's the operational burden (new cron jobs, new DBs, monitoring)?

Auto-resolve mechanical decisions silently (e.g., file naming, import order). Only surface taste decisions to the user (e.g., "Should this be a separate skill or part of an existing one?").

### Step 3b: Decomposition analysis (MANDATORY for eligible tasks)

If the plan touches more than 1 file or requires more than 3 tool calls, perform a decomposition analysis.

**When to decompose into parallel agents** — ALL must hold:
- 3+ subtasks with clear, independent deliverables
- Non-overlapping file scope (no two agents editing the same file)
- Combined work would exceed ~10 tool calls sequentially

Skip for: single-file edits, direct questions, lookups, tasks < 3 tool calls.

**Steps:**
1. List every subtask with its write targets (files it creates or modifies).
2. Identify dependencies: which subtasks require another's output?
3. Choose an orchestration pattern:
   - **Fan-out:** independent searches, reviews, or analyses
   - **Pipeline:** when outputs feed downstream steps
   - **Map-reduce:** repeated analysis over many items with synthesis
   - **Reviewer/synthesizer:** quality control and integration
4. Decide: `parallel`, `hybrid`, or `sequential`. Cite specific reasons — not "sequential because it's simpler."
5. If parallel or hybrid:
   - Define expected outputs before spawning agents (file path, answer format, test result — not a vague topic)
   - Assign one synthesis owner — parallel work converges through a single integrating step
   - Minimize context per agent — only what it needs, not the full conversation
   - Note: runtime isolation and post-completion reconciliation are enforced by `.claude/rules/orchestration.md`

Include the decomposition in the plan under a **## Execution Strategy** section:

```markdown
## Execution Strategy

**Decision:** parallel | hybrid | sequential
**Pattern:** fan-out | pipeline | map-reduce | reviewer/synthesizer
**Reason:** <cite specific task properties — shared files, dependency edges, or independence>

| Subtask | Files | Depends On | Isolation |
|---------|-------|------------|-----------|
| A       | file1.py | — | worktree |
| B       | file2.py | — | worktree |
| C       | file3.py | A | sequential |

**Synthesis:** <how outputs merge — e.g., "main agent verifies no conflicts, runs tests">
```

If the task is below the eligibility threshold (1 file, ≤3 tool calls), skip this step.

### Step 4: Generate plan artifact

Build the plan content:

```yaml
---
scope: "<from analysis — one line>"
surfaces_affected: "<comma-separated files to touch>"
verification_commands: "<how to verify — e.g., 'python3 -m pytest tests/test_foo.py'>"
rollback: "<how to undo — e.g., 'git revert <sha>'>"
review_tier: "<Tier 1|Tier 1.5|Tier 2 — from tier_classify.py>"
verification_evidence: "PENDING"
---
```

Below the frontmatter, write:
- **Build order** — numbered steps with dependencies noted
- **Files** — table of create vs modify with scope per file
- **Verification** — specific commands to prove correctness

### Step 5: Present and confirm

Display the plan to the user. Ask: "Does this look right? I'll write it to `tasks/<topic>-plan.md`."

Only write the file after user approval.

### Step 6: Handoff

After writing:
- "Plan written to `tasks/<topic>-plan.md`."
- "This satisfies the plan gate for protected paths."
- "Build the changes, then run `/review` when ready."


## `--auto` Mode (Auto-Planning Pipeline)

`/plan --auto` detects the pipeline tier from the task description, then chains skills with auto-decisions using 6 decision principles. Surfaces taste decisions at a final approval gate.

### Tier Detection

- **T2 (standard):** Bugfix, test, docs, trivial refactor, small feature → `/think refine` → `/plan`
- **T1 (new feature):** New capability, new abstraction, scope expansion → `/think discover` → `/challenge` → `/plan`
- **Big bet:** Architectural decision, major feature, uncertain scope → `/think discover` → `/elevate` → `/challenge` → `/plan`
- **T0 (spike):** Prototype, exploration → skip pipeline, just build

If UI scope detected (2+ UI terms in task description), `/design plan-check` runs after `/plan`.

### The 6 Decision Principles

These auto-answer every intermediate question:

1. **Choose completeness** — Ship the whole thing. Pick the approach that covers more edge cases.
2. **Boil lakes** — Fix everything in the blast radius. Auto-approve expansions that are in blast radius AND < 1 day effort.
3. **Pragmatic** — If two options fix the same thing, pick the cleaner one.
4. **DRY** — Duplicates existing functionality? Reject. Reuse what exists.
5. **Explicit over clever** — 10-line obvious fix > 200-line abstraction.
6. **Bias toward action** — Flag concerns but don't block.

**Conflict resolution:** `/think` phase: P1+P6 dominate. `/challenge` phase: P5+P3 dominate. `/plan` phase: P5+P1 dominate.

### Decision Classification

- **Mechanical:** One clearly right answer. Auto-decide silently.
- **Taste:** Reasonable people could disagree. Auto-decide with recommendation, surface at final gate.
- **User Challenge:** Both models agree the user's stated direction should change. NEVER auto-decided.

### Sequential Execution (MANDATORY)

Skills execute in strict order per the tier's chain. Each must complete fully before the next begins. Between each skill, verify all required outputs from the prior skill exist.

### Final Approval Gate

After the pipeline completes, present ALL deferred decisions in a single AskUserQuestion:

- Taste decisions: what was auto-decided, which principle, the close alternative
- User challenges: full context block (what user said, what models recommend, why, blind spots, cost of being wrong)
- Options: A) Approve all, proceed to build. B) Review taste decisions one by one. C) Reject — revert.

## Important Notes

- The plan artifact MUST have valid YAML frontmatter with all required fields — `hook-plan-gate.sh` validates this.
- `verification_evidence` starts as "PENDING" — it gets filled in during `/review --qa` or `/ship`.
- If the user already has a plan in mind, don't fight it. Use the three lenses to sanity-check, not to redesign.
