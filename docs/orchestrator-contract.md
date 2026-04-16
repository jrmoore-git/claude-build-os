# Orchestrator Contract

How to build an external runner that drives BuildOS skills autonomously. BuildOS owns the gates (plan, review, ship). The runner owns execution between gates.

---

## Task Spec Format

The runner starts with a task spec file at `tasks/<topic>-spec.md`. Required fields:

```yaml
---
topic: "<slug used for all artifact filenames>"
objective: "<what the agent must deliver>"
allowed_paths:
  - "src/analytics/*"
  - "tests/test_analytics*"
acceptance_criteria:
  - "Dashboard listing page renders with mock data"
  - "Tests pass for CRUD operations"
escalation_triggers:
  - "Ambiguous requirement — two valid interpretations"
  - "Need to modify files outside allowed_paths"
max_attempts: 3
---
```

Optional fields: `context_files` (list of files the agent should read first), `excluded_paths` (never touch), `review_mode` (default: `--qa`).

---

## State Machine

```
spec → plan → build → test → review → ship
                ↑       |
                └───────┘  (test fails → fix → retest)
```

### Transitions

| From | To | Condition |
|---|---|---|
| spec | plan | Spec file exists with required fields |
| plan | build | `tasks/<topic>-plan.md` exists with valid frontmatter |
| build | test | Code changes exist (git diff non-empty) |
| test | review | Tests pass (exit 0) |
| test | build | Tests fail AND attempts < max_attempts |
| test | ESCALATE | Tests fail AND attempts >= max_attempts |
| review | ship | Review passes (0 open MATERIAL findings) |
| review | build | Review has MATERIAL findings → fix → re-review |
| ship | DONE | Ship summary written, PR opened |

### Illegal transitions

- spec → build (no plan = no scope containment)
- build → ship (no review = no quality gate)
- ESCALATE → build (human must intervene first)

---

## Gate Requirements

What must exist before each skill will accept work.

### /plan

**Input:** Task spec + any context files listed in `context_files`.

**Requires:** Nothing — /plan is the first gate.

**Produces:** `tasks/<topic>-plan.md` with frontmatter fields: `scope`, `surfaces_affected`, `allowed_paths`, `verification_commands`, `rollback`, `review_tier`.

### /review

**Input:** Git diff of changes since plan was written.

**Requires:**
- Code changes exist
- Tests pass (runner must verify before calling /review)
- `tasks/<topic>-plan.md` exists

**Produces:** `tasks/<topic>-review.md` with per-lens findings. Check `open_material_findings` in the artifact — 0 means passed.

### /ship

**Input:** All prior artifacts.

**Requires:**
- `tasks/<topic>-review.md` exists and is not stale (newer than last code change)
- Tests pass
- No open MATERIAL findings in review

**Produces:** `tasks/<topic>-ship-summary.md` with spec mapping, decisions, and acceptance criteria results. This is the PR body.

---

## Escalation Points

The runner MUST stop and hand control to a human when any of these occur. These match the escalation protocol in `.claude/rules/workflow.md`.

1. **Ambiguous requirements.** Two or more valid interpretations exist and the choice affects behavior.
2. **Architectural decisions outside the plan.** The work needs changes not covered by `surfaces_affected` or `allowed_paths`.
3. **Security-sensitive changes.** Auth, credentials, permissions, data access patterns, network exposure.
4. **Scope growth.** The task needs more files or abstractions than the spec scoped.
5. **Three failures on the same problem.** Three attempts at the same fix fail — the diagnosis is wrong.
6. **Irreversible side effects.** Deleting data, sending messages, publishing, pushing to shared branches.
7. **Contradictory constraints.** Two specs, rules, or prior decisions conflict.

The runner should log escalations to `tasks/<topic>-escalation.md` with: trigger type, what was attempted, what the agent observed, and what decision is needed.

---

## Success / Failure Signals

### Per-gate signals

| Gate | Success | Failure |
|---|---|---|
| /plan | `tasks/<topic>-plan.md` exists with all required frontmatter fields | File missing or frontmatter incomplete |
| tests | Exit code 0 | Exit code non-zero |
| /review | `open_material_findings` is 0 in review artifact | Non-zero MATERIAL findings |
| /ship | `tasks/<topic>-ship-summary.md` written | Any HARD gate in /ship fails |

### Overall signals

- **DONE:** Ship summary exists, PR opened, all acceptance criteria mapped to PASS.
- **ESCALATED:** Escalation file exists. Human must resolve before runner can resume.
- **FAILED:** max_attempts exceeded without passing tests or review.

---

## Runner Responsibilities

Things BuildOS does NOT do that the runner must handle:

1. **Environment setup.** Install dependencies, configure credentials, set up test databases.
2. **Test execution.** Run the project's test suite. BuildOS gates on results but doesn't run tests itself (except through /ship's verification probes).
3. **Git operations.** Create branches, commit code, push, open PRs.
4. **Retry logic.** Decide whether to retry after test failure, how to adjust the approach, when to give up.
5. **Resource management.** Token budgets, API rate limits, concurrent agent limits.
6. **PR description.** Use `tasks/<topic>-ship-summary.md` as the PR body — it contains spec mapping and verification evidence.

---

## Example Runner Loop (Pseudocode)

```
read spec from tasks/<topic>-spec.md
run /plan with spec as context
attempts = 0

loop:
  build (agent implements against plan)
  run tests
  if tests pass:
    run /review
    if review passes:
      run /ship
      open PR with ship-summary as body
      exit DONE
    else:
      feed review findings back to agent
      attempts += 1
  else:
    feed test failures back to agent
    attempts += 1

  if attempts >= spec.max_attempts:
    write escalation file
    exit ESCALATED

  if any escalation trigger detected:
    write escalation file
    exit ESCALATED
```

This is pseudocode, not a prescription. The runner can implement this loop however it wants — CI job, shell script, orchestration framework — as long as it respects the gate requirements and escalation points.
