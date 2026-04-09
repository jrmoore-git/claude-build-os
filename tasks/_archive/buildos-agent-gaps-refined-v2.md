---
debate_id: buildos-agent-gaps
created: 2026-04-05T15:01:55-0700
phase: refine
rounds: 3
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: yes
---
# buildos-agent-gaps — Refined Document

## Round 1 (gemini-3.1-pro)
The original proposal correctly identified the risk of hallucinated features but failed to apply a rigorous enough standard to filter them out, relying on recollection rather than authoritative evidence. It also bundled multiple claims together, increasing the risk of accidentally accepting false features (like the falsified `TeammateIdle` hook), and mischaracterized existing documentation (Gap 1). 

To strengthen the document, I have:
1. **Added a Strict Verification Rubric**: All claims must now pass a formal evidence check against authoritative vendor documentation before being considered valid gaps.
2. **Quarantined Unverified Claims**: Gaps 7 and 9, alongside any D115-quarantined items, have been moved to a strict quarantine state. They are rejected by default unless reopened with new, authoritative vendor evidence.
3. **Corrected False Claims**: Gap 1 is explicitly marked as false since `.claude/agents/` is already documented. Gap 10 is reclassified as a minor presentation nit.
4. **Unbundled Complex Claims**: Gaps 4 and 5 have been split into per-feature claims for independent evaluation. Known hallucinations (like `TeammateIdle`) are explicitly rejected.
5. **Reframed Gap 6**: The "Review Swarm" is now correctly framed as a speculative design alternative rather than a documentation gap, explicitly rejecting the assumption that it is superior to the existing cross-model `debate.py` architecture.

## Round 2 (gpt-5.4)
The current revision is already strong: it correctly rejects Gap 1, quarantines the highest-risk hallucinations (Gaps 7 and 9), preserves the D115 boundary, and reframes Gap 6 appropriately as a design alternative rather than a documentation defect.

Key improvements still needed:

1. **Numbering consistency**
   - The list skips Gap 7 and Gap 9 in the main “Claimed Gaps” section because they were moved to quarantine. That is acceptable, but the structure can more clearly signal that numbering is preserved intentionally from the original 10-point analysis.

2. **Sharper distinction between “feature may exist” and “documentation gap”**
   - Several items are correctly marked “Needs Verification,” but the document can more explicitly state that even a verified feature is not automatically a BuildOS documentation gap. It must also clear the audience relevance and existing-coverage tests from the rubric.

3. **Existing coverage should be cited more explicitly**
   - For Gap 5, some subclaims are already partially covered by A2:
     - tool restrictions
     - model override
     - worktree isolation
     - skills access
   - Those should not be treated as wholly undocumented. They are better classified as “partially covered; verify whether the claimed extra surface actually exists.”

4. **Operational controls category is slightly too bundled**
   - Gap 4 is labeled “UNBUNDLED FOR REVIEW,” which is good, but the subclaims would benefit from short notes distinguishing likely CLI/UI conveniences from framework-relevant mechanisms. This helps avoid over-prioritizing presentational features such as display modes.

5. **Minor clarity edits**
   - The proposal should reiterate that D115-quarantined claims are out of scope for routine adversarial review.
   - “F across the board” is rhetorically useful, but the critique should more directly say the grading method appears severity-insensitive.

No factual regressions were introduced. The main remaining work is improving precision, flow, and the treatment of partially covered items.

## Round 3 (claude-opus-4-6)
The previous revision is thorough, well-structured, and makes sound analytical decisions. It correctly identifies false claims, applies a verification rubric, and separates quarantined items from open verification items. Here are my observations:

**Strengths of the current revision:**
- Strong verification rubric that prevents hallucination-driven documentation
- Correct identification of Gap 1 as already covered, Gap 4f as hallucinated, Gap 6 as a design alternative
- Good unbundling of Gap 4 and Gap 5 into verifiable subclaims
- Appropriate quarantine of Gaps 7 and 9
- Sound decision rule for follow-up documentation
- Complete appendix for verification against actual docs

**Issues I'm addressing:**

1. **Missing summary table.** The document is long and the status of each gap is scattered. A summary table at the top (after context) would dramatically improve usability for decision-makers who need the verdict without reading every section.

2. **Gap 3 verification framing could be stronger.** The `Ctrl+B` shortcut claim and `/tasks` slash command are specific enough to verify or reject quickly. The current text flags hallucination risk but doesn't note that these are the kind of claims that can be resolved in minutes with a product session — worth calling out as a quick-win verification.

3. **Gap 8 (headless mode) under-discusses what IS known.** Claude Code's `--print` / `-p` flag for non-interactive use is widely referenced in Anthropic's public documentation. The current draft treats this as fully unverified, but this is one of the more well-established features. I'll note this without asserting it as verified (since I'm applying the rubric), but I'll flag that this is likely the highest-confidence open item.

4. **The "Author's Updated Assessment" section partially duplicates the summary I'm adding.** I'll consolidate to avoid redundancy while keeping the categorized breakdown.

5. **Gap 5 structure is slightly confusing.** The "Already covered" and "Still requiring verification" lists are clear, but the subsequent "Notes by subclaim" section re-lists items already marked as covered (5a), which is redundant. I'll tighten this.

6. **The Grading Critique section is good but could be slightly more actionable.** I'll add a brief severity framework suggestion.

7. **Minor: the Appendix header says "Current BuildOS Documentation" but it's actually excerpts.** Small accuracy fix.

## Final Refined Document

# BuildOS Agent Parallelization Gap Analysis — Proposal

## Context

Claude Desktop produced a 10-point gap analysis claiming the BuildOS documentation is strong on strategic doctrine (when/why to parallelize) but has material gaps in operational how-to (how to configure and run agent-based workflows). It graded the operational layer as mostly "F" across the board.

Before acting on this analysis, we need cross-model adversarial review to determine which claimed gaps are real and worth documenting, and which claims rely on hallucinated or unverified features.

**Crucially, we must avoid re-investigating D115-quarantined hallucinated features.** Any features previously quarantined as unverified or hallucinated by D115 are treated as rejected by default. They are explicitly removed from routine review scope and will not be re-evaluated unless reopened with new, authoritative vendor evidence.

---

## Summary of Findings

| Gap | Claim | Verdict | Action |
|-----|-------|---------|--------|
| 1 | Custom subagent definitions (`.claude/agents/`) undocumented | **False** — already covered in A2 and team-playbook §2 | Closed. Editorial discoverability only. |
| 2 | Built-in subagents (Explore, Plan, etc.) | **Unverified** | Verify via vendor docs before any work |
| 3 | Background subagents (`Ctrl+B`, `/tasks`) | **Unverified** — high hallucination risk | Verify via vendor docs; quick-win check |
| 4a | Display modes (tmux/iTerm2 splits) | **Unverified** — likely user workflow, not product feature | Verify; probably low-priority even if real |
| 4b | Plan approval for teammates | **Unverified** | Verify; distinguish vendor feature from BuildOS process |
| 4c | Direct teammate messaging | **Unverified** | Verify; material if true |
| 4d | Task list mechanics | **Unverified** | Verify; partially relevant to existing team-playbook |
| 4e | Shutdown/cleanup protocol | **Unverified** | Verify; operational value depends on vendor surface |
| 4f | `TeammateIdle` hook | **Rejected** — hallucinated | Closed. Not in hook event list (A3). |
| 5a | Tool restrictions | **Already covered** in A2 | Closed |
| 5b | Scoped MCP servers | **Unverified** | Verify via vendor docs |
| 5c | Permission modes | **Unverified** | Verify via vendor docs |
| 5d | Persistent memory dirs (`~/.claude/agent-memory/`) | **Unverified** | Verify via vendor docs |
| 5e | Preloaded skills | **Partially covered** in A2 | Verify whether additional mechanism exists |
| 5f | Per-subagent hooks | **Unverified** | Verify via vendor docs |
| 6 | Review swarm pattern | **Reframed** — design alternative, not gap | Closed as gap; optionally explore as experiment |
| 7 | Scheduled tasks and channels | **Quarantined (D115)** | Do not investigate without new vendor evidence |
| 8 | Headless/programmatic mode | **Unverified** — likely highest-confidence open item | Verify via vendor docs; likely real (`-p` / `--print`) |
| 9 | Plugin ecosystem (`/plugin`) | **Quarantined (D115)** | Do not investigate without new vendor evidence |
| 10 | Project tree missing `.claude/agents/` | **Editorial nit** | Low-priority cleanup |

**Bottom line:** Of 10 claimed gaps, 3 are closed (false, hallucinated, or editorial), 2 are quarantined, 1 is reframed as a design alternative, and the remaining items require vendor-doc verification before any documentation work begins. No gap should be treated as actionable based on the external analysis alone.

---

## Verification Rubric

To prevent accidental documentation of hallucinated features, **no gap will be treated as real based on recollection.** Every claimed feature must pass the following rubric before being considered for documentation:

1. **Authoritative Source**: Must be verified via official vendor docs, changelogs, or release notes.
2. **Exact Surface**: The exact command, API, hook, or file path must be confirmed to exist.
3. **Stability Status**: Is the feature stable, experimental, or deprecated?
4. **Audience Relevance**: Is it material for the BuildOS framework audience?
5. **Existing Coverage**: Does BuildOS already address the underlying user need through another mechanism?

**Important:** Passing steps 1–3 proves a feature exists. It does **not** by itself prove BuildOS has a documentation gap. A gap is only actionable if the feature also matters to the BuildOS audience and is not already adequately covered through existing BuildOS guidance.

---

## Scope and Numbering

The numbering below preserves the original 10-point Claude Desktop analysis so each claim can be traced back exactly. Some items are reclassified, rejected, or quarantined rather than kept as open gaps.

---

## The Claimed Gaps (from Claude Desktop)

### Gap 1: Custom Subagent Definitions (.claude/agents/) — FALSE / ALREADY COVERED

**Claim:** BuildOS never mentions `.claude/agents/`. The project tree doesn't include `agents/`.

**Correction:** This claim is false. Appendix A2 directly documents `.claude/agents/` with a YAML example and capabilities, and `team-playbook.md` §2 references custom subagent definitions.

**Assessment:** Not a real absence. At most, there may be a discoverability or presentation issue.

**Status:** Closed. Any follow-up is limited to possible expansion or discoverability improvements, not absence.

---

### Gap 2: Built-in Subagents — Needs Verification

**Claim:** Claude Code ships with built-in subagents (Explore, Plan, general-purpose) that aren't documented.

**Reality check needed:** Apply the Verification Rubric.

Questions to resolve:
- Do these built-in subagents actually exist in official vendor documentation?
- Are those exact names and behaviors documented by the vendor?
- Are they stable product surfaces or transient UX affordances?
- If real, are they material to BuildOS users, or are BuildOS custom subagents already sufficient for the user need?

**Status:** Open for verification only. Do not treat as a documentation gap until existence and relevance are confirmed.

---

### Gap 3: Background Subagents — Needs Verification

**Claim:** Subagents can run in background (`Ctrl+B`) with progress tracked via `/tasks`.

**Reality check needed:** Apply the Verification Rubric.

Questions to resolve:
- Is background execution a real, documented Claude Code capability?
- Do `Ctrl+B` and `/tasks` exist as official surfaces?
- Is this stable behavior or an experimental/UI-only affordance?
- If real, is it important enough for BuildOS operational guidance?

**Status:** Open for verification only. Shortcut and slash-command claims have high hallucination risk. However, these are specific enough to confirm or reject quickly with a single product session — this is a quick-win verification item.

---

### Gap 4: Agent Team Operational Controls — UNBUNDLED FOR REVIEW

**Claim:** BuildOS is missing various operational controls for agent teams.

This category must be reviewed as separate subclaims rather than accepted as a bundle. Some subclaims may be real but low-value; others may be unverified or irrelevant to BuildOS.

#### 4a: Display modes (tmux/iTerm2 split panes)
**Verification question:** Is this an official Claude Code feature, a user-created workflow, or merely a recommended terminal setup?

**Preliminary assessment:** Even if real, this is likely a convenience or presentation pattern rather than a framework-level gap. Terminal layout recommendations belong in a tips section at most, not in core operational docs.

#### 4b: Plan approval for teammates
**Verification question:** Is there a native plan-approval mechanism for teammates, or is approval handled through BuildOS governance and external review flow?

**Preliminary assessment:** Must distinguish vendor product feature from BuildOS process control. BuildOS already has plan gates (hook-plan-gate.sh, hook-decompose-gate.py) — the question is whether agent teams introduce a distinct approval surface.

#### 4c: Direct teammate messaging
**Verification question:** Can agent teammates directly message each other through an official surface, or is coordination only mediated through shared state/task mechanisms?

**Preliminary assessment:** Material if true, because it would affect the documented distinction between subagents and agent teams in team-playbook §2.

#### 4d: Task list mechanics
**Verification question:** Is there an official task-list surface for agent teams, and what exact commands or UI elements expose it?

**Preliminary assessment:** Potentially material, because `team-playbook.md` §2 already references "a shared task list and teammate coordination" without specifying the mechanics. If a concrete surface exists, documenting it would strengthen existing coverage.

#### 4e: Shutdown/cleanup protocol
**Verification question:** Is there an official teardown, stop, or cleanup workflow for agent teams beyond generic session termination and BuildOS release discipline?

**Preliminary assessment:** Could matter operationally, but only if the vendor exposes concrete mechanics beyond what BuildOS's kill-switch and release discipline already cover.

#### 4f: `TeammateIdle` hook — REJECTED
**Claim:** A `TeammateIdle` hook exists.

**Correction:** Rejected. Appendix A3 lists the hook events and does **not** include `TeammateIdle`. It does include `SubagentStart`.

**Status:** Hallucinated feature. Closed.

---

### Gap 5: Subagent Capabilities and Restrictions — PARTIALLY COVERED

**Claim:** Custom subagents have various undocumented capabilities.

This category should not be treated as wholly missing, because Appendix A2 already documents several capabilities. The right question is which claimed capabilities are already covered, which are partially covered, and which remain unverified.

#### Already covered in Appendix A2 — no action needed
- **5a: Tool restrictions** — explicitly documented
- **Model override** — explicitly documented (not separately numbered in the original claim list)
- **Worktree isolation** — explicitly documented as `isolation: worktree`
- **5e: Skills access / preloaded skills** — partially covered as "Subagents can load specific skills"

#### Requiring verification before any documentation work

##### 5b: Scoped MCP servers
**Verification question:** Can MCP servers be scoped per subagent via an official, documented surface? What is the exact YAML key or configuration mechanism?

##### 5c: Permission modes
**Verification question:** Are there subagent-specific permission modes beyond tool restriction and isolation settings already documented in A2?

##### 5d: Persistent memory directories (`~/.claude/agent-memory/`)
**Verification question:** Does this exact directory exist as an official vendor-documented feature? This has the hallmark of a hallucinated path — specific enough to sound plausible, hard to verify without product access.

##### 5e: Preloaded skills (remaining question)
**Verification question:** Is there a more specific or stronger mechanism than the documented "Subagents can load specific skills"? If so, what is the exact syntax?

##### 5f: Per-subagent hooks
**Verification question:** Are hooks configurable per subagent, or does BuildOS only have global/session-level hook surfaces plus `SubagentStart` events? Note that `SubagentStart` (A3) already provides a hook point *when* a subagent spawns, but the question is whether individual subagents can carry their own hook configurations.

**Status:** Reclassify this gap from "missing capabilities" to "partially documented capabilities plus several unverified extensions."

---

### Gap 6: Review Swarm Pattern — REFRAMED AS DESIGN ALTERNATIVE

**Claim:** Review personas (Architect, Staff Engineer, Security, PM) could run in parallel with read-only subagents instead of sequentially via `debate.py`.

**Correction:** This conflates feature existence with framework-level documentation requirements. Subagent review is **not** an assumed upgrade over `debate.py`. The existing debate system relies on diversity across model families, which subagents within a single vendor may not preserve.

**Assessment:** This is not a documentation omission. It is a speculative design alternative that would require separate evaluation of quality, independence, and failure modes before being recommended.

**Status:** Closed as a gap. Optionally explorable as a future experiment.

---

### Gap 7: Scheduled Tasks and Channels — QUARANTINED (D115)

**Claim:** Claude Code now supports `/loop` (cron-style recurring tasks), `/schedule` (one-time future tasks), and Channels for pushing external events.

**Status:** Quarantined. No evidence in provided materials; highly likely to be hallucinated. This item remains intentionally out of routine review scope unless reopened with new authoritative vendor evidence.

---

### Gap 8: Headless/Programmatic Mode — Needs Verification

**Claim:** Claude Code can run headless for CI/CD integration.

**Reality check needed:** Apply the Verification Rubric.

Questions to resolve:
- Is there an official headless or non-interactive Claude Code mode?
- What exact command/API surface exists? (Note: Claude Code's `-p` / `--print` flag for non-interactive use is widely referenced in public-facing Anthropic materials, making this likely the highest-confidence open item on this list.)
- Is it stable and intended for CI/CD use?
- If real, is this material for BuildOS users, or only for a narrower automation audience?

**Status:** Open for verification only. If confirmed, this may warrant BuildOS documentation because it directly affects how BuildOS workflows could be integrated into CI/CD pipelines — satisfying Decision Rule conditions 1 and 3.

---

### Gap 9: Plugin Ecosystem — QUARANTINED (D115)

**Claim:** `/plugin` system lets you install pre-built agent configurations, skills, and workflows as distributable units.

**Status:** Quarantined. Highly likely to be a hallucinated command. This item remains intentionally out of routine review scope unless reopened with new authoritative vendor evidence.

---

### Gap 10: Annotated Project Tree Is Stale — EDITORIAL NIT

**Claim:** The project tree should include `.claude/agents/`.

**Correction:** This is a minor presentation consistency issue, not an operational how-to gap. It does not affect the overall assessment of documentation quality.

**Status:** Low-priority editorial cleanup only.

---

## Decision Rule for Follow-up Documentation

Even if a feature is verified to exist, BuildOS should only document it if at least one of the following is true:

1. It is necessary to safely run BuildOS-recommended workflows.
2. It materially improves success rates for common BuildOS users.
3. BuildOS currently references the underlying mechanism indirectly but omits the operational steps users would need.
4. The feature changes or qualifies an existing BuildOS recommendation.

If none of those conditions apply, the feature may be real but still not worth documenting in the core framework.

---

## Recommended Verification Priority

Not all open items are equally worth investigating. Prioritize by expected information value:

| Priority | Item | Rationale |
|----------|------|-----------|
| **High** | Gap 8: Headless mode | Likely real; high audience relevance for CI/CD integration |
| **High** | Gap 4d: Task list mechanics | Strengthens already-existing team-playbook coverage |
| **Medium** | Gap 3: Background subagents | Quick to confirm or reject; material if real |
| **Medium** | Gap 4c: Direct teammate messaging | Affects documented subagent vs. team distinction |
| **Medium** | Gap 5b: Scoped MCP servers | Could meaningfully extend subagent configuration |
| **Low** | Gap 2: Built-in subagents | May be transient UX; BuildOS custom agents may suffice |
| **Low** | Gap 4a: Display modes | Likely user workflow, not product feature |
| **Low** | Gap 4b: Plan approval | BuildOS plan gates may already cover this need |
| **Low** | Gap 4e: Shutdown/cleanup | BuildOS release discipline may already cover this need |
| **Low** | Gap 5c: Permission modes | May overlap with existing tool restriction coverage |
| **Low** | Gap 5d: Memory directories | High hallucination risk on the specific path |
| **Low** | Gap 5e: Preloaded skills (extension) | Current coverage may be sufficient |
| **Low** | Gap 5f: Per-subagent hooks | SubagentStart may already meet the need |

---

## Grading Critique

The external analysis grades absence as "F" regardless of importance. That is not a useful severity model. A missing section on headless CI/CD mode is not the same severity as missing documentation on custom agent definitions (which, in this case, was not actually missing).

**Suggested severity framework for future gap analyses:**

- **Critical:** Feature is real, stable, and BuildOS users will fail or produce unsafe output without it.
- **Important:** Feature is real and would meaningfully improve documented workflows.
- **Nice-to-have:** Feature is real but BuildOS already covers the underlying need adequately.
- **Not applicable:** Feature is unverified, hallucinated, unstable, or irrelevant to the BuildOS audience.

Priority should be weighted by:
- How many BuildOS users would benefit
- How badly they would fail without it
- Whether BuildOS already covers the underlying need another way
- Whether the feature is stable enough to justify framework-level documentation

The right output is **not** "accept all missing features as major gaps." The right output is a filtered, prioritized list of features that definitely exist, matter to BuildOS users, are not already covered, and are stable enough to document.

---

## APPENDIX A: Relevant BuildOS Documentation Excerpts

The following is the complete text of all relevant BuildOS doc sections, provided so reviewers can verify claims against what actually exists.

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
