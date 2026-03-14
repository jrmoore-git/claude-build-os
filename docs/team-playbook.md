# Team Playbook — Engineering Teams Building with Claude Code

## When to use this doc

You need this doc when your project involves **more than one person or more than one parallel workstream**. If you're working solo on a single-track project, the [Build OS](the-build-os.md) covers everything you need.

This doc covers: agent teams, parallel work decomposition, orchestration documents, interface contracts, spawn prompts, git worktrees, cheat sheets, skills and eval, and release discipline.

For governance tiers, the enforcement ladder, the session loop, review personas, contract tests, and the essential eight invariants, see the [Build OS](the-build-os.md). This doc cross-references those — it does not redefine them.

---

## 1. Planning and Workflow

### Planning threshold

Use explicit thresholds rather than "plan everything."

Plan first if:
- More than 3 files may change
- Behavior changes, not just formatting
- Auth, security, state, or integrations are touched
- Unfamiliar architecture is involved
- Multiple workstreams will run in parallel

Skip formal planning for:
- One-line config changes
- Small copy edits
- Obvious isolated fixes with simple verification

### Standard sequence

For non-trivial work:
1. Research
2. Write plan to disk
3. Implement
4. Verify with evidence
5. Review if threshold met
6. Write handoff if incomplete

### Verification standard

A task is not done because the model says it is done. It is done when:
- The behavior matches the spec
- Tests or smoke checks pass
- Negative cases were considered
- Evidence exists
- Rollback is understood if the change is material

---

## 2. Parallel Work and Orchestration

### When to parallelize

Default to a single agent unless parallelism clearly earns its cost through context isolation, real wall-clock speedup, or necessary specialization. Parallel work has real overhead — duplicated context, coordination cost, and merge complexity.

### Subagents vs. agent teams

Two distinct mechanisms exist. Choosing the wrong one wastes tokens and creates coordination failure.

**Subagents** run within a single session. They accept a task, execute it, and report results back to the parent. They cannot communicate with each other. Use subagents when the work is cleanly decomposable and no coordination between workers is needed.

**Agent teams** (enabled via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) spawn independent sessions with their own context windows, connected by a shared task list and teammate coordination. Use agent teams when work has interdependencies and agents need to share findings, challenge assumptions, or coordinate on shared interfaces during execution.

The deciding question: **do the workers need to communicate with each other during execution?** If no, subagents. If yes, agent teams.

Agent teams remain experimental. Use subagents for production-critical work; use agent teams when lateral coordination adds real value.

### Decompose by output boundary, not role boundary

The primary failure mode in parallel agent work is not bad code. It is incompatible assumptions at boundaries.

**Good decomposition:** non-overlapping file ownership, testable in isolation, clear integration surfaces.
- Agent 1: backend routes
- Agent 2: frontend components
- Agent 3: database migrations

**Bad decomposition:** shared files, shared state, sequential coupling disguised as parallelism.
- Agent 1: authentication
- Agent 2: authorization
- Agent 3: session management

Why the second fails: shared files, shared state, and the work is actually sequential — each piece depends on the others.

**Governance files are always write-conflicting.** Tasks that write to `lessons.md`, `decisions.md`, `handoff.md`, or any shared institutional memory file must be sequenced, not parallelized. The last writer wins and the earlier write disappears silently.

### Interface contracts before agents spin up

If agents will build components that interact, the lead must define the interface contract as a written artifact before any agent starts implementation. Not as a vague prompt description. As a file both sides reference.

Pattern: **foundation wave → contract delivery → parallel execution**

1. Foundation wave: establish shared schema, types, interface stubs, or API contracts.
2. Parallel waves: spawn remaining agents with the contract injected into their prompts and explicit file ownership boundaries.

This prevents the most expensive class of failure: multiple agents each producing plausible code that does not integrate.

### Spawn prompts must include full context

Teammates do not inherit the lead's conversation history. Whatever they need must be included in the spawn prompt.

Minimum spawn prompt contents:
- Task scope
- File ownership boundary
- Interface contracts relevant to that agent
- Acceptance criteria
- Pointer to the relevant PRD or build-plan section

### Token cost is not optional context

Parallel implementations often use materially more tokens than single-agent approaches because context is duplicated across agents and coordination adds summarization overhead.

Use parallelism only when the benefit is clear. If your environment supports it, `CLAUDE_CODE_SUBAGENT_MODEL` can route subagents to a cheaper tier. A common pattern: strongest model for the orchestrating lead, cheaper model for focused worker tasks. Cap teams at five or fewer agents unless you have a strong reason not to.

### State files for multi-track work

For three or more parallel tracks, create a machine-readable JSON state file before execution begins.

Track:
- Task ID
- Owner agent
- Status (`pending`, `in_progress`, `blocked`, `completed`, `failed`)
- Dependencies
- Blockers

Blocked tasks must not proceed on stale or failed upstream output.

### Convergence review

The normal staged review (see [Build OS](the-build-os.md) §VII) assumes one coherent changeset. Parallel tracks require an additional convergence review before the standard review closes.

The convergence review examines:
- Interface compatibility between merged tracks
- Overlapping file edits that weren't anticipated
- Contract compliance
- Integration test results against the real system

Run at least one smoke test against the integrated system before closing.

### Orchestration documents

For complex builds, write the whole orchestration plan to disk and point Claude at it. A long orchestration document outperforms a long conversation because it externalizes scope, dependencies, and verification criteria without bloating the live context window.

One of our highest-leverage patterns was exactly this: write the orchestration document, point Claude at it, and let the session execute against the file rather than against a constantly mutating chat history.

---

## 3. Git Worktrees for Parallel Sessions

If multiple Claude sessions need to work on the same repo simultaneously, use git worktrees instead of letting them fight over one checkout.

```bash
git worktree add ../feature-auth feature-auth
git worktree add ../feature-api feature-api
```

Each session gets its own branch and working directory while preserving one shared repository history. This prevents merge conflicts from concurrent file edits and lets each agent work with a clean working tree.

---

## 4. Skills and Eval Pipelines

Skills are how you package domain knowledge and workflow instructions so Claude loads them when relevant instead of carrying everything in the base operating layer.

For teams, the important pattern is not just creating skills. It is evaluating them. Treat skills the way you treat code: create them, test whether they trigger, improve them when they fail, and benchmark them against representative scenarios.

A useful mental model is a four-mode loop:
1. **Create** — write the skill with clear triggers and acceptance criteria
2. **Eval** — test whether it triggers and produces correct output
3. **Improve** — fix failure modes, refine prompts, tighten constraints
4. **Benchmark** — run against representative scenarios to measure quality

The principle is the same as governance testing: do not assume a skill works because the instructions look plausible. Test whether it actually triggers and behaves correctly.

---

## 5. Release Discipline

Every production-capable system needs:
- A **kill switch** — a way to stop all autonomous actions immediately
- **Staged rollout** — test in a narrow scope before full deployment
- **Pinned versions** — every dependency, model, and Docker image pinned
- **Last-known-good restore** — a path back to the previous working state
- **Explicit rollback thinking** — before release, answer: "How do we undo this?"

---

## 6. Cheat Sheets

### Minimum viable operating stack

Stand up these first, usually in the same initial setup window:
- `CLAUDE.md`
- `docs/project-prd.md`
- `docs/current-state.md`
- `tasks/lessons.md`
- `tasks/decisions.md`
- `tasks/handoff.md`
- One smoke test
- One hook

Then add, as complexity rises:
- `docs/review-protocol.md` and `docs/contract-tests.md`
- `tasks/session-log.md`
- `tasks/[phase]-orchestration.md`
- `state/[task]-state.json`
- More contract tests and stronger hook gates

### Session opener cheat sheet

```
Reference the relevant PRD sections, lessons, decisions, and handoff before starting.
If the task crosses the planning threshold, research first and write the plan to disk.
Keep the solution simple. Do not over-engineer. Verify before declaring done.
```

### Review cheat sheet

```
Run staged review in this order: Architect, Staff Engineer + Security, Product / UX.
Flag LLM-boundary violations, hidden state risk, audit gaps, auth weakness,
unnecessary complexity, and release-risk regressions.
```

### Handoff cheat sheet

```
Write a handoff note to disk: current state, confirmed working behavior,
open questions, blockers, and the next concrete step.
```

### Audience-specific starter notes

**Product leaders:** Start with the PRD, review protocol, and decisions log. Your job is to keep scope and rationale stable enough that Claude builds against a real source of truth.

**Engineering teams:** Start with the PRD, lessons log, decisions log, one smoke test, and one hook. Add orchestration docs and state files as concurrency rises.

**Cross-functional teams:** Use the markdown operating environment even when not everyone is coding. The point is shared memory, clear decisions, and durable handoffs — not code ownership.

---

## 7. Feedback Loops

Governance prevents bad outcomes. Feedback loops improve the system over time.

Build measurement before you trust the workflow:
- Daily cost by workflow and model
- Model-routing accuracy and override rate
- Draft approval rate
- Retrieval precision / false-positive rate
- Review escape rate

A good rule of thumb: every workflow that matters should have both a guardrail and a measurement loop.
