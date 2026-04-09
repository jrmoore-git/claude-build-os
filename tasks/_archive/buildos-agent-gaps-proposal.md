---
scope: Evaluate Claude Desktop's gap analysis of BuildOS agent parallelization docs
surfaces_affected: claude-build-os README.md, docs/team-playbook.md, docs/platform-features.md, docs/hooks.md, docs/operating-reference.md
review_tier: Tier 1
---

# BuildOS Agent Parallelization Gap Analysis — Proposal

## Context

Claude Desktop produced a 10-point gap analysis claiming the Build OS documentation is strong on strategic doctrine (when/why to parallelize) but has material gaps in operational how-to (how to configure and run agent-based workflows). It graded the operational layer as mostly "F" across the board.

Before acting on this analysis, we need cross-model adversarial review to determine:
1. Which claimed gaps are real and worth documenting
2. Which claims reference features that don't actually exist (hallucinations)
3. Which gaps are real but low priority for a framework-level doc

## The 10 Claimed Gaps (from Claude Desktop)

### Gap 1: Custom Subagent Definitions (.claude/agents/) — "Completely Absent"
**Claim:** BuildOS never mentions .claude/agents/. The project tree doesn't include agents/.
**Reality check needed:** Is this actually absent, or does existing documentation cover it?

### Gap 2: Built-in Subagents — "Not Mentioned"
**Claim:** Claude Code ships with built-in subagents (Explore, Plan, general-purpose) that aren't documented.
**Reality check needed:** Are these actually built-in? Do they matter for a framework doc?

### Gap 3: Background Subagents — "Not Mentioned"
**Claim:** Subagents can run in background (Ctrl+B) with progress tracked via /tasks.
**Reality check needed:** Is this a real feature? Is it material for framework guidance?

### Gap 4: Agent Team Operational Controls — "Thin Coverage"
**Claim:** Missing: display modes (tmux/iTerm2 split panes), plan approval for teammates, direct teammate messaging, task list mechanics, shutdown/cleanup protocol, TeammateIdle hook.
**Reality check needed:** Which of these are real features vs. hallucinated? Is TeammateIdle a real hook event?

### Gap 5: Subagent Capabilities and Restrictions — "Not Covered"
**Claim:** Custom subagents can have tool restrictions, scoped MCP servers, permission modes, persistent memory directories (~/.claude/agent-memory/), preloaded skills, per-subagent hooks.
**Reality check needed:** Which of these are real? Is ~/.claude/agent-memory/ a real path?

### Gap 6: Review Swarm Pattern — "Missing Connection"
**Claim:** Review personas (Architect, Staff Engineer, Security, PM) could run in parallel with read-only subagents instead of sequentially via debate.py.
**Reality check needed:** Is this actually better than the current cross-model approach? debate.py already uses different model families — would subagents add value or just add complexity?

### Gap 7: Scheduled Tasks and Channels — "Not Mentioned"
**Claim:** Claude Code now supports /loop (cron-style recurring tasks), /schedule (one-time future tasks), and Channels for pushing external events.
**Reality check needed:** Are these native Claude Code features, or are they custom skills specific to our project?

### Gap 8: Headless/Programmatic Mode — "Not Mentioned"
**Claim:** Claude Code can run headless for CI/CD integration.
**Reality check needed:** Is this real and material for the BuildOS audience?

### Gap 9: Plugin Ecosystem — "Not Mentioned"
**Claim:** /plugin system lets you install pre-built agent configurations, skills, and workflows as distributable units.
**Reality check needed:** Does /plugin actually exist as a Claude Code command?

### Gap 10: Annotated Project Tree Is Stale
**Claim:** The project tree should include .claude/agents/.
**Reality check needed:** Does the tree exist in BuildOS docs, and is agents/ actually missing from it?

## Author's Initial Assessment

**Likely real and worth documenting:**
- Gap 1 (custom agents) — but may already be partially covered
- Gap 2 (built-in subagents) — Explore, Plan, general-purpose are real
- Gap 3 (background agents) — run_in_background is real
- Gap 8 (headless mode) — claude -p is real

**Skeptical — needs verification:**
- Gap 4 (TeammateIdle hook, specific operational controls)
- Gap 5 (~/.claude/agent-memory/, per-subagent hooks in frontmatter)
- Gap 7 (/loop and /schedule as native features vs. custom skills)
- Gap 9 (/plugin ecosystem — likely hallucinated)

**Valid insight but questionable priority:**
- Gap 6 (review swarm) — debate.py cross-model approach may be superior to subagent parallelism for reviews
- Gap 10 (stale tree) — minor fix

## Key Question for Challengers

The most dangerous outcome is documenting features that don't exist. Claude models are known to hallucinate platform features with high confidence. Each gap claim must be evaluated against: (a) does this feature actually exist in Claude Code as described? (b) if it exists, is it stable enough to document in a framework meant to be reused? (c) if it exists and is stable, where does it rank against other documentation priorities?

## Grading Critique

The analysis grades everything absent as "F" regardless of importance. A missing section on headless CI/CD mode is not the same severity as missing documentation on custom agent definitions. Priority should weight by: how many BuildOS users would benefit × how badly they'd fail without it.

---

## APPENDIX A: Current BuildOS Documentation

The following is the complete text of all relevant BuildOS docs, provided so challengers can verify claims against what actually exists.

### A1: docs/team-playbook.md (260 lines)

```markdown
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

### Decomposition gate

Claude defaults to sequential execution even when tasks are clearly independent. Advisory rules fail under cognitive load. The fix is a PreToolUse hook that blocks Write|Edit until the session assesses whether the task should be decomposed into parallel agents. The gate fires once per session; after the agent writes a flag file (via Bash, not Write), all writes proceed normally. See The Build OS — Enforcement Ladder for the full pattern.

### When to parallelize

Default to a single agent unless parallelism clearly earns its cost through context isolation, real wall-clock speedup, or necessary specialization. Parallel work has real overhead — duplicated context, coordination cost, and merge complexity.

### Subagents vs. agent teams

Two distinct mechanisms exist. Choosing the wrong one wastes tokens and creates coordination failure.

**Subagents** run within a single session. They accept a task, execute it, and report results back to the parent. They cannot communicate with each other. Use subagents when the work is cleanly decomposable and no coordination between workers is needed.

**Agent teams** (enabled via CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1) spawn independent sessions with their own context windows, connected by a shared task list and teammate coordination. Use agent teams when work has interdependencies and agents need to share findings, challenge assumptions, or coordinate on shared interfaces during execution.

The deciding question: **do the workers need to communicate with each other during execution?** If no, subagents. If yes, agent teams.

Agent teams remain experimental. Use subagents for production-critical work; use agent teams when lateral coordination adds real value.

Claude Code also supports custom subagent definitions in .claude/agents/ — YAML files that restrict tools, override models, and set isolation boundaries. Use these to create specialized agents (e.g., a read-only researcher, a test runner limited to Bash) without cluttering main context. See Platform Features for the full reference.

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

**Governance files are always write-conflicting.** Tasks that write to lessons.md, decisions.md, handoff.md, or any shared institutional memory file must be sequenced, not parallelized. The last writer wins and the earlier write disappears silently.

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

Use parallelism only when the benefit is clear. If your environment supports it, CLAUDE_CODE_SUBAGENT_MODEL can route subagents to a cheaper tier. A common pattern: strongest model for the orchestrating lead, cheaper model for focused worker tasks. Cap teams at five or fewer agents unless you have a strong reason not to.

### State files for multi-track work

For three or more parallel tracks, create a machine-readable JSON state file before execution begins.

Track:
- Task ID
- Owner agent
- Status (pending, in_progress, blocked, completed, failed)
- Dependencies
- Blockers

Blocked tasks must not proceed on stale or failed upstream output.

### Convergence review

The normal staged review assumes one coherent changeset. Parallel tracks require an additional convergence review before the standard review closes.

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

[cheat sheets content omitted for brevity — no agent-related content]

---

## 7. Feedback Loops

[feedback loops content omitted for brevity — no agent-related content]
```

### A2: docs/platform-features.md §7 — Subagents (the only section relevant to this analysis)

```markdown
## 7. Subagents (.claude/agents/)

Define custom subagents with restricted capabilities:

```yaml
# .claude/agents/researcher.yaml
name: researcher
description: Read-only research agent
tools:
  - Read
  - Glob
  - Grep
  - WebSearch
model: haiku
```

- **Tool restrictions.** Limit what tools the subagent can use — for example, a researcher that can read but not write.
- **Model override.** Use cheaper models for simple subagent tasks.
- **Worktree isolation.** Add `isolation: worktree` for subagents that need an isolated copy of the repo.
- **Skills access.** Subagents can load specific skills.

Use subagents to delegate investigation without cluttering main context, or to create specialized agents with restricted permissions.
```

### A3: docs/hooks.md §4 — Key hook events (from platform-features.md)

```markdown
### Key hook events

| Event | Fires when | Common use |
|---|---|---|
| PreToolUse | Before any tool executes | Block dangerous operations, validate paths |
| PostToolUse | After a tool completes | Run tests after edits, format code |
| Stop | Session is ending | Export handoff, run final checks |
| SessionStart | Session begins | Inject context, verify environment |
| PreCompact | Before context compaction | Preserve critical state |
| SubagentStart | Subagent is spawned | Audit or restrict subagent behavior |
| UserPromptSubmit | User sends a message | Inject instructions, validate input |
| ConfigChange | Settings are modified | Audit configuration changes |
```

Note: "TeammateIdle" is NOT listed as a hook event. "SubagentStart" IS listed.

### A4: README.md — Hooks table (relevant rows only)

```markdown
| hook-decompose-gate.py | Before Write/Edit (first per session) | Blocks writes until decomposition assessed; deduplicates denial messages for parallel calls in the same batch; blocks main-session writes after parallel plan (must dispatch agents or bypass with reason); fail-closed on corrupt state |
| hook-agent-isolation.py | Before Agent dispatch (when plan_submitted) | Requires isolation: "worktree" on write-capable agents; exempts read-only subagent types |
```

### A5: README.md — "The difference between guidance and governance" section

```markdown
The Build OS ships thirteen hooks that implement level 3: hook-plan-gate.sh blocks commits to protected paths without a valid plan artifact, hook-review-gate.sh blocks Tier 1 commits without debate artifacts, hook-tier-gate.sh blocks file edits to high-risk files without prior review, hook-pre-edit-gate.sh requires a plan artifact before writing to protected paths, hook-pre-commit-tests.sh blocks commits when tests fail, hook-agent-isolation.py blocks write-capable Agent dispatches without worktree isolation after a parallel plan is declared, and five more covering decomposition reminders, env file protection, post-edit testing, PRD drift detection, linting, and syntax validation. Each is configured as a Claude Code hook — deterministic shell scripts that fire before or after the matched tool executes. See Hooks Reference for the full specification.

A related discipline: mandatory decomposition analysis before parallelizing work. Before spawning parallel agents, the plan must list every subtask with its write targets, identify dependencies, and justify the execution strategy. "Sequential because it's simpler" is not a justification — cite the specific task property (shared files, output dependency, or genuine independence). This started as advisory guidance and was ignored for months. Three escalation levels (lesson → rule → stronger rule) failed. Only hook-decompose-gate.py — a PreToolUse hook that physically blocks Write|Edit until decomposition is assessed — changed the behavior. A companion hook, hook-agent-isolation.py, completes the enforcement: after a parallel plan is declared, it blocks write-capable Agent dispatches that lack isolation: "worktree", ensuring the model can't simply spawn non-isolated agents. If a rule matters, enforce it mechanically.
```
