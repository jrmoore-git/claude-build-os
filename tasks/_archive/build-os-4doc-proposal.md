# Proposal: Four-Doc Publishable Structure for the Build OS Repo

**Author:** Claude Opus (Round 1)
**Date:** 2026-03-13
**Debate type:** Architecture (3 rounds)
**Scope:** Evaluate the revised 4-doc structure for the publishable Build OS GitHub repo. Prior debate approved the framework but identified that the Team Playbook was incorrectly collapsed into advanced-patterns.md. This proposal defines the final doc structure, what each doc covers, and what gets edited out of the originals for external consumption.

---

## Context

Justin Moore has four existing docs written for internal use:
1. **Overview — Building with Claude** (143 lines) — Essay arguing governance > prompting
2. **Team Playbook** (585 lines) — Engineering guide: file structure, memory, retrieval, hooks, review, workflow, agent teams, cheat sheets
3. **Operating Reference** (721 lines) — Deep manual: core rules, session/execution/review/enforcement behavior, invariants, institutional memory, bootstrap
4. **CLAUDE Kernel** (148 lines) — Always-on 18-rule set for CLAUDE.md

A prior debate (build-os-publish, both challengers APPROVED) established:
- A single Build OS framework doc with tiered governance (Tier 0–3)
- The Overview essay should be the README (keeps Justin's voice)
- The Team Playbook should NOT be collapsed — it has unique team-specific content
- The Operating Reference deep patterns should be preserved as advanced reference
- The Kernel becomes the starter CLAUDE.md template
- Slash commands, templates, and example hooks ship as working files

## The Proposed 4-Doc Structure

### Doc 1: README.md — The Argument

**Source:** Overview — Building with Claude (lightly edited)
**Role:** Why governance beats prompting. The essay that pulls the reader in.
**Audience:** Anyone considering whether this framework is worth their time.
**Length:** ~150 lines

**What stays from the original:**
- The full narrative argument (sections I–VII)
- Justin's voice: "We learned this the hard way," first-person production stories
- The practical starter kit (7 items)
- The closing: "The model keeps getting smarter. The discipline around it is what you have to build yourself."

**What changes:**
- Remove the "How this fits into the system" preamble (references the old 4-doc structure)
- Add a "Quick Start" section pointing to `/setup` and the Build OS
- Add cross-references to the other three docs
- Add the governance tier table (brief, links to the Build OS for details)

**What this doc does NOT cover:** File structure, slash commands, templates, bootstrap details, agent teams — those belong in the Build OS and Team Playbook.

### Doc 2: docs/the-build-os.md — The Framework

**Source:** The Build OS (revised from prior debate)
**Role:** The canonical reference. Tiers, file system, operations, enforcement ladder, memory model, review, bootstrap.
**Audience:** Anyone using the framework — individuals through production teams.
**Length:** ~500 lines

**What stays from the current Build OS:**
- Part I: Philosophy (6 principles)
- Part II: Governance Tiers (Tier 0–3 with upgrade triggers and anti-patterns)
- Part III: File System (project tree, scaling rule, what-goes-where table)
- Part IV: Operations (cognitive + engineering, session loop)
- Part V: Enforcement Ladder (4 levels, three-strikes, promotion lifecycle)
- Part VI: Memory Model (3 layers, retrieval modes, session ingestion)
- Part VII: Review and Testing (tiers, personas, contract tests, essential eight, definition of done)
- Part VIII: Bootstrap (interactive setup + manual checklist)

**What changes from the current Build OS:**
- Part IX "Patterns Worth Knowing" expands 3-4 operator scars into short stories (2-3 paragraphs each) instead of bullet points. The $724 day, the invented email, the gate that always passed, the mocks that validated the bug.
- Cognitive operations section adds one concrete example of what "distill" produces (an assertion-style pattern note from a meeting)
- Reading guide table at top stays (per prior debate)
- Acknowledgments section stays

**What this doc does NOT cover:** Agent teams, parallel work decomposition, orchestration documents, cheat sheets — those belong in the Team Playbook. Deep enforcement patterns, audit protocol, degradation testing — those belong in Advanced Patterns.

### Doc 3: docs/team-playbook.md — The Team Guide

**Source:** Team Playbook (edited for external audience)
**Role:** Practical engineering guide for teams. How to run agent teams, parallel work, orchestration, reviews, and daily workflow with Claude Code.
**Audience:** Engineering teams (Tier 1–2) and technical leads.
**Length:** ~400 lines (trimmed from 585)

**What stays from the original Team Playbook:**
- Part III: Workflow protocol (planning threshold, standard sequence, session loop cheat sheet, parallel work, orchestration documents)
- Part IV: Architecture and invariants (LLM boundary, essential eight, failure classes, model routing, provenance, human inputs untrusted, toolbelt audit)
- Part V: Enforcement, hooks, and governance (enforcement ladder details, high-value hooks, concrete hook example, hook safety, skills and eval pipelines)
- Part VI: Review, testing, and release discipline (review personas, testing layers, release discipline)
- Part VII: Cheat sheets (minimum viable stack, session opener, review, handoff, audience-specific starter notes, feedback loops, bootstrap recall skill)
- Agent teams guidance: subagents vs teams, decomposition by output boundary, interface contracts, spawn prompts, token cost, state files, convergence review
- Git worktrees for parallel sessions

**What gets removed:**
- Part I (doctrine) — absorbed into the Build OS philosophy section
- Part II (environment map, reference protocol, update protocol, cheat sheet §8-§9) — absorbed into the Build OS file system section
- The "How this fits into the system" preamble
- Concrete artifact examples (decisions log, lessons log) — now in the templates
- Section numbers that reference the old 4-doc structure

**What gets added:**
- Cross-references to the Build OS tier model ("this content is most relevant at Tier 1–2")
- A "When to use this doc" section at the top

### Doc 4: docs/advanced-patterns.md — The Deep Manual

**Source:** Operating Reference (edited for external audience)
**Role:** Deep production patterns, failure modes, and enforcement logic for teams at Tier 2–3.
**Audience:** Teams building production systems or autonomous agents.
**Length:** ~350 lines (trimmed from 721)

**What stays from the original Operating Reference:**
- §2 Session Behavior: retrieve before planning (depth), session bootstrap skill, compaction discipline, fresh-session rule, PRD reconciliation, audit protocol
- §3 Execution Behavior: parallel work patterns, orchestration documents, destructive command safety, sanity-check volumes, degradation testing
- §5 Enforcement Behavior: enforcement ladder depth, three-strikes depth, test your instructions, verify your verifiers, resource limits enforcement, hook safety, dependency discipline, one-hook minimum, Safety Rules block pattern, instruction placement
- §6 Core Invariants (the essential eight with expanded context)
- §7 Institutional Memory: promotion cycle, exit conditions, session ingestion pipeline, outside-session knowledge, scars worth remembering

**What gets removed:**
- §1 Core Rules — absorbed into the Build OS philosophy + starter CLAUDE.md
- §4 Review Behavior — absorbed into the Build OS review section + Team Playbook
- §8 Bootstrap — absorbed into the Build OS bootstrap section
- §9 Implementation Mapping — absorbed into the Build OS file system section
- The "How this fits into the system" preamble
- OpenClaw-specific implementation details (toolbelt file paths, specific database names, specific skill names)

**What gets added:**
- Cross-model debate protocol (from `.claude/rules/cross-model-debate.md`, generalized)
- Failure classes table
- Proxy-layer budgets section
- Feedback loops section
- "When to use this doc" section at the top

### Plus: The Starter CLAUDE.md

**Source:** CLAUDE Kernel (restructured)
**Role:** The always-on operating rules template that ships with the repo.
**What it is:** The 18 Kernel rules distilled to 6 commented rules with HTML `<!-- why: ... -->` annotations. Users customize it for their project. `/setup` generates a project-specific version.

---

## The Non-Doc Files

These ship alongside the 4 docs (unchanged from prior debate):

```
.claude/commands/setup.md        # Interactive bootstrap
.claude/commands/recall.md       # Session start
.claude/commands/plan.md         # Plan to disk
.claude/commands/review.md       # Staged review
templates/                       # 7 doc/task templates
templates/commands/              # 4 optional command templates
examples/                        # 2 example hook scripts
```

---

## What the challengers should evaluate

1. **Coverage:** Do the 4 docs cover everything an engineer needs without significant overlap?
2. **Separation of concerns:** Is the boundary between Build OS, Team Playbook, and Advanced Patterns clear? Would a reader know which doc to open?
3. **Editing approach:** Am I cutting the right things from each source doc? Am I keeping the right things?
4. **Voice and stories:** Does the proposal preserve Justin's original narrative voice (especially in the README and operator scars)?
5. **Audience fit:** Does this work for the three target audiences (individuals, teams, production systems)?
6. **What's missing:** Is there content in the original 4 docs that I'm dropping that should be preserved?
