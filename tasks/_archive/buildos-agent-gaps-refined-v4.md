---
debate_id: buildos-agent-gaps-refined-v4
created: 2026-04-05T21:11:53-0700
phase: refine
rounds: 3
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: yes
---
# buildos-agent-gaps-refined-v4 — Refined Document

## Round 1 (gemini-3.1-pro)
The document has been revised to address the accepted challenges, focusing on rigorous verification of upstream feature claims and protecting the integrity of the BuildOS documentation. 

Key improvements:
1. **Verification and Stability Protocols Added:** Introduced explicit rules for verifying upstream features and assessing their stability before inclusion in framework docs (addressing Challenges 5 and 11).
2. **Hallucinations Hard-Rejected:** Gaps 7 and 9, along with specific hallucinated features like `TeammateIdle`, are now explicitly rejected rather than left as "needs verification" (Challenge 1).
3. **Gap 1 Corrected:** Reclassified Gap 1 as a false positive, as `.claude/agents/` is already documented in the provided appendix (Challenge 2).
4. **Gap 5 Decomposed:** Split Gap 5 into verified capabilities (tool restrictions, model overrides) and rejected hallucinations (`agent-memory`, `permission_mode`) to prevent contamination (Challenge 3).
5. **Gap 6 Reframed:** Adjusted the "Review Swarm" gap to acknowledge the intentional, cross-model design of `debate.py` (verified via config showing Claude/Gemini splits), framing subagents as an experimental trade-off rather than a missing capability (Challenge 4).

## Round 2 (gpt-5.4)
[ERROR: LLM call failed (APITimeoutError): Request timed out.]

## Round 3 (claude-opus-4-6)
Claude Code can spawn subagents — lightweight child sessions that execute a scoped task and return a result to the parent. Subagents are useful for decomposing work without polluting the main context window.

### Built-in subagents

Claude Code ships with a small set of built-in subagents:

| Name | Purpose |
|------|---------|
| Explore | Read-only research — browses files, searches code, reads docs. Cannot write. |
| Plan | Generates a structured plan for a task. Cannot execute. |
| (default) | General-purpose subagent with full tool access. |

You do not need to define these. They are available automatically.

### Custom subagent definitions

Place YAML files in `.claude/agents/` to define custom subagents:

```yaml
# .claude/agents/researcher.yaml
name: researcher
description: Read-only research agent for codebase exploration
model: claude-sonnet-4-20250514
tools:
  - Read
  - Glob
  - Grep
  - Bash(rg:*)
  - mcp: github
allowed_tools: null  # or explicit allowlist
disallowed_tools:
  - Write
  - Edit
  - MultiEdit
```

Key fields:
- **model** — override the model for this subagent (e.g., route workers to a cheaper tier)
- **tools / allowed_tools / disallowed_tools** — control what the subagent can do
- **description** — helps Claude decide when to use this subagent

### Worktree isolation

When using git worktrees for parallel sessions, each subagent operates in its own worktree. This prevents file conflicts between concurrent agents.

### Skills access

Subagents inherit the project's skills (from `.claude/skills/`). A subagent with appropriate tool access can use any skill available to the parent session.

### When to use subagents vs. agent teams

See [Team Playbook § Subagents vs. agent teams](team-playbook.md#subagents-vs-agent-teams) for the decision framework.
```

### A3: docs/the-build-os.md (relevant excerpts only)

```markdown
## Enforcement Ladder

[Contains PreToolUse hook patterns, including the decomposition gate referenced in team-playbook.md. Does not contain agent-specific hooks beyond the decomposition gate.]

## Review Personas

[Contains the four-persona review framework: Architect, Staff Engineer, Security Reviewer, PM/User Advocate. These are used by debate.py for cross-model review. Does not reference subagent-based review.]
```

### A4: scripts/debate.py (operational context)

```markdown
debate.py implements the cross-model review system. It rotates review personas across different model families (Claude and Gemini) using persona_model_map from debate-models.json. This ensures diverse evaluation perspectives that a single-model subagent swarm cannot replicate.
```

---

## APPENDIX B: Current System Failures

The following are real, observed failures from production use of the BuildOS framework. They represent the actual pain points that any documentation update should address.

### Failure 1: Agent Sprawl Without Kill Switch
**Observed:** A team spawned 7 parallel agents for a medium-complexity feature. Three agents produced conflicting schema migrations. The team had no mechanism to halt all agents simultaneously when the conflict was discovered.
**Impact:** 4 hours of manual merge resolution. ~$47 in wasted API costs.
**Root cause:** No documentation on agent team limits, no kill switch pattern for multi-agent scenarios.

### Failure 2: Spawn Prompt Context Loss
**Observed:** Agent teammates were spawned with minimal prompts ("implement the auth module"). They lacked interface contracts, file ownership boundaries, and acceptance criteria.
**Impact:** Two agents wrote overlapping implementations of the same middleware. One agent invented an API contract that didn't match the existing schema.
**Root cause:** Spawn prompt requirements existed in docs but were buried in prose. No checklist or template was provided.

### Failure 3: Sequential Work Disguised as Parallel
**Observed:** A team decomposed work into "database layer," "API layer," and "frontend layer" — but the API layer depended on database types, and the frontend depended on API response shapes. All three agents started simultaneously.
**Impact:** Frontend agent hallucinated API response shapes. API agent used different column names than the database agent. Integration took longer than sequential implementation would have.
**Root cause:** The decomposition guidance existed but the dependency-checking gate was advisory, not enforced.

### Failure 4: Governance File Write Conflicts
**Observed:** Three parallel agents all appended to lessons.md and decisions.md. Git merge preserved only the last write; two agents' learnings were silently lost.
**Impact:** Institutional memory loss. Team repeated a mistake that had been "learned" by a lost agent.
**Root cause:** The warning about governance file conflicts existed in docs but had no enforcement mechanism.

### Failure 5: Review Monoculture
**Observed:** A team replaced the cross-model debate.py review with four Claude-only subagent reviewers. All four reviewers approved code with the same subtle authorization bug — a bug that the Gemini reviewer in the standard rotation would likely have caught due to different attention patterns.
**Impact:** Authorization bypass reached staging. Caught by manual security review before production.
**Root cause:** No documentation explaining *why* cross-model review exists or the risks of monoculture review.

---

## APPENDIX C: Operational Context

### debate.py Architecture
- Uses `persona_model_map` from `debate-models.json` to assign review personas to specific model families
- Current rotation: Claude (Architect, Security) + Gemini (Staff Engineer, PM/User Advocate)
- Cross-model diversity is a deliberate design choice to avoid single-model blind spots
- The system has caught 3 authorization bugs in the last month that single-model review missed

### Token Economics (observed)
- Single-agent complex feature: ~150K tokens average
- 3-agent parallel feature: ~380K tokens average (2.5× multiplier, not 3×, due to shared context)
- 5-agent parallel feature: ~750K tokens average (5× multiplier — coordination overhead dominates)
- Agent team coordination overhead: ~15-20% additional tokens for task list management
- Subagent overhead: ~5-8% additional tokens (no coordination protocol)

### Current Usage Patterns
- 73% of BuildOS users work single-agent
- 19% use subagents (2-3 agents)
- 8% use agent teams (experimental)
- Most common failure: spawning agents before defining interface contracts

---

*Document version: Gap analysis proposal for review. Not yet approved for implementation.*

## Final Refined Document

# BuildOS Agent Parallelization Gap Analysis — Proposal

## Context

Claude Desktop produced a 10-point gap analysis claiming the Build OS documentation is strong on strategic doctrine (when/why to parallelize) but has material gaps in operational how-to (how to configure and run agent-based workflows). It graded the operational layer as mostly "F" across the board.

Before acting on this analysis, we must apply strict verification to determine which claimed gaps are real, which are hallucinations, and which are appropriate for a reusable framework document.

### Verification Protocol and Stability Criteria
To protect the framework's credibility, any claimed Claude Code feature must pass the following gates before being added to the documentation:
1. **Verification Rule:** Any claimed feature not verified either in official Anthropic documentation/changelogs or already present in current BuildOS docs must be treated as unsupported and excluded from planned updates.
2. **Stability Criterion:** Only officially documented and stable features will be included in the core framework guidance. Experimental or volatile features (such as agent teams, which are currently flagged as experimental) must be placed in a clearly labeled appendix or omitted entirely to prevent the documentation from becoming rapidly stale.

## The 10 Claimed Gaps (from Claude Desktop)

### Gap 1: Custom Subagent Definitions (.claude/agents/) — FALSE POSITIVE / ALREADY COVERED
**Claim:** BuildOS never mentions .claude/agents/. The project tree doesn't include agents/.
**Resolution:** This claim is factually incorrect. Existing documentation (`docs/platform-features.md` and `docs/team-playbook.md`) already covers `.claude/agents/` and custom subagent definitions. This gap is closed, though we may consider adding a more operational example.

### Gap 2: Built-in Subagents — "Not Mentioned"
**Claim:** Claude Code ships with built-in subagents (Explore, Plan, general-purpose) that aren't documented.
**Reality check needed:** Are these actually built-in? Do they matter for a framework doc?

### Gap 3: Background Subagents — "Not Mentioned"
**Claim:** Subagents can run in background (Ctrl+B) with progress tracked via /tasks.
**Reality check needed:** Is this a real feature? Is it material for framework guidance?

### Gap 4: Agent Team Operational Controls — "Thin Coverage"
**Claim:** Missing: display modes (tmux/iTerm2 split panes), plan approval for teammates, direct teammate messaging, task list mechanics, shutdown/cleanup protocol, TeammateIdle hook.
**Resolution:** `TeammateIdle` is an unverified/hallucinated hook and is explicitly rejected. The remaining operational controls must be verified against official upstream docs before inclusion.

### Gap 5: Subagent Capabilities and Restrictions — PARTIALLY VERIFIED / PARTIALLY REJECTED
**Claim:** Custom subagents can have tool restrictions, scoped MCP servers, permission modes, persistent memory directories (~/.claude/agent-memory/), preloaded skills, per-subagent hooks.
**Resolution:** This claim bundles real features with hallucinations. 
- **Verified & Retained:** Tool restrictions, model overrides, worktree isolation, and skills access (already documented in `platform-features.md`).
- **Rejected:** `agent-memory`, `permission_mode`, and per-subagent hooks beyond documented events are unsupported and explicitly rejected pending official upstream evidence.

### Gap 6: Review Swarm Pattern — DESIGN TRADE-OFF (NOT A GAP)
**Claim:** Review personas (Architect, Staff Engineer, Security, PM) could run in parallel with read-only subagents instead of sequentially via debate.py.
**Resolution:** The current `debate.py` architecture intentionally utilizes a cross-model review design (`persona_model_map` splits personas across Claude and Gemini families) to ensure diverse evaluation. Replacing this with a monoculture subagent swarm is a design trade-off, not a missing capability. Subagent review swarms may be discussed as an optional experiment, but not as a recommended replacement for the current cross-model architecture.

### Gap 7: Scheduled Tasks and Channels — REJECTED (UNSUPPORTED)
**Claim:** Claude Code now supports /loop (cron-style recurring tasks), /schedule (one-time future tasks), and Channels for pushing external events.
**Resolution:** These features are unverified in official documentation and are treated as hallucinations. This gap is explicitly rejected.

### Gap 8: Headless/Programmatic Mode — "Not Mentioned"
**Claim:** Claude Code can run headless for CI/CD integration.
**Reality check needed:** Is this real and material for the BuildOS audience?

### Gap 9: Plugin Ecosystem — REJECTED (UNSUPPORTED)
**Claim:** /plugin system lets you install pre-built agent configurations, skills, and workflows as distributable units.
**Resolution:** The `/plugin` command is unverified and highly likely to be a hallucination. This gap is explicitly rejected.

### Gap 10: Annotated Project Tree Is Stale
**Claim:** The project tree should include .claude/agents/.
**Reality check needed:** Does the tree exist in BuildOS docs, and is agents/ actually missing from it?

## Author's Initial Assessment

**Likely real and worth documenting (subject to stability criteria):**
- Gap 2 (built-in subagents) — Explore, Plan, general-purpose are real
- Gap 3 (background agents) — run_in_background is real
- Gap 8 (headless mode) — claude -p is real

**Explicitly Rejected (Hallucinations / Unsupported):**
- Gap 7 (/loop, /schedule, Channels)
- Gap 9 (/plugin ecosystem)
- Unsupported elements of Gap 4 (`TeammateIdle`) and Gap 5 (`agent-memory`, `permission_mode`)

**Reclassified / Addressed:**
- Gap 1 (custom agents) — False positive; already covered in existing docs.
- Gap 5 (capabilities) — Decomposed into verified features vs. rejected hallucinations.
- Gap 6 (review swarm) — Reframed as a design trade-off; current cross-model `debate.py` is intentional.
- Gap 10 (stale tree) — Minor fix if applicable.

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
