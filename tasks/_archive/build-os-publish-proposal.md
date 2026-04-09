# Proposal: Publishable Build OS Framework — Structure, Content, and Audience Fitness

**Author:** Claude Opus (Round 1)
**Date:** 2026-03-13
**Debate type:** Architecture (3 rounds: author → both challengers → author responds → final verdict)
**Scope:** Evaluate whether `docs/claude-build-os.md` is the right artifact for a publishable, cross-project framework — and whether the four source docs (Overview, Team Playbook, Operating Reference, CLAUDE Kernel) should be shared alongside it, replaced by it, or restructured.

---

## Context

Justin Moore has four existing docs that describe how to build with Claude Code:

1. **Overview — Building with Claude** (143 lines) — Top-level essay arguing governance > prompting. Written for publication. Narrative-driven, uses first-person stories from production failures.

2. **Team Playbook** (585 lines) — Practical engineering guide. File structure, memory layer, retrieval, hooks, review, workflow. Organized for navigation. Includes cheat sheets, artifact examples, agent teams guidance.

3. **Operating Reference** (721 lines) — Deep manual. 9 sections covering core rules, session behavior, execution behavior, review behavior, enforcement behavior, invariants, institutional memory, bootstrap, and implementation mapping. Written to shape Claude's behavior, not as a public essay.

4. **CLAUDE Kernel** (148 lines) — Always-on rule set. 18 numbered operating rules. Designed to be loaded into CLAUDE.md.

These four docs share a "how this fits" preamble and were designed as one system, with each layer serving a different depth level.

A fifth doc was created after a cross-model debate comparing Justin's system with his daughter Anna Marie Kelly's `claude-obsidian-os` repo:

5. **The Build OS** (516 lines) — A synthesized framework incorporating debate-validated insights from both systems. Tiered governance, named operations, enforcement ladder, bootstrap instructions.

**The question for challengers:** Is the Build OS the right publishable artifact? Should the four source docs be shared alongside it, replaced by it, or restructured into something different? What should the final file set look like for someone cloning a GitHub repo?

---

## Assessment

### 1. The Build OS is the right single-document framework

The Build OS succeeds as a unified document because it:
- **Resolves the audience problem.** The four source docs were written for different purposes (essay, team guide, Claude behavior shaping, always-on rules) with significant overlap. The Build OS has one audience: anyone building with Claude Code.
- **Introduces tiered governance.** The biggest insight from the cross-model debate was that recommendations must match blast radius. Tiers 0–3 let readers self-select their governance depth. The four source docs don't have this — they assume Tier 2–3 throughout.
- **Names the cognitive operations.** Triage, distill, connect, review, recall — imported from the daughter's system and validated by the debate. The four source docs only have engineering operations.
- **Provides a clear bootstrap path.** Interactive setup + manual checklist + CLAUDE.md starter template. The four source docs have a bootstrap section each, with overlap and inconsistency.

### 2. The four source docs should NOT be published as-is alongside the Build OS

The source docs have several problems for external consumption:

**Overlap:** All four docs repeat the same core principles (LLM boundary, KISS, state on disk, enforcement ladder, essential eight invariants). The enforcement ladder appears in: Overview §IV, Playbook §24, Operating Reference §5, and Kernel §9/§14. A reader encountering all four docs would read the same content 4 times.

**OpenClaw specificity:** The Operating Reference includes patterns deeply tied to OpenClaw's production context — toolbelt audit, proxy-layer budgets, MCP supply chain evaluation, Granola enterprise cache privacy. These are valuable but not generalizable without heavy editing.

**Wrong audience assumptions:** The Kernel is designed to be loaded into CLAUDE.md (it's an instruction set for Claude), not read by humans. The Operating Reference is "not a public essay" by its own admission. The Playbook is the closest to a team guide but assumes Tier 2–3 throughout.

**Inconsistent bootstrap:** The Kernel says "minimum day-one setup" includes 10 items (git init, CLAUDE.md, PRD, project-map, current-state, lessons, decisions, handoff, smoke test, hook). The Playbook §32 says the same 10 items. The Operating Reference §8 also lists 10 items. The Build OS offers two paths (interactive setup, manual checklist) and correctly makes most items tier-dependent. Three copies of the same bootstrap with slight differences is worse than one copy.

### 3. Recommended file set for a publishable GitHub repo

The target is a repo like Anna Marie's: someone clones it, follows a setup flow, and has a working operating environment.

**Proposed structure:**

```
claude-build-os/
├── README.md                    # What this is, quick start, link to full guide
├── docs/
│   └── the-build-os.md         # The full framework document (current Build OS)
├── CLAUDE.md                    # Starter CLAUDE.md template (ready to customize)
├── .claude/
│   ├── commands/
│   │   ├── setup.md            # Interactive setup — asks about project, picks tier, creates files
│   │   ├── recall.md           # Session bootstrap — loads handoff, current-state, relevant context
│   │   ├── plan.md             # Write a plan to disk before executing
│   │   ├── review.md           # Run staged review (architect → staff+security → product)
│   │   ├── handoff.md          # Write session handoff before closing
│   │   └── sync.md             # Update PRD, decisions, lessons after approved changes
│   └── rules/
│       └── security.md         # Starter security rules (LLM boundary, hook safety)
├── docs-templates/
│   ├── project-prd.md          # PRD template with section guide
│   ├── decisions.md            # Decisions log template with format example
│   ├── lessons.md              # Lessons log template with format example
│   ├── handoff.md              # Handoff template
│   ├── current-state.md        # Current state template
│   ├── contract-tests.md       # Contract tests template with the essential eight
│   └── review-protocol.md      # Review protocol template
└── examples/
    ├── hook-test-after-edit.sh  # Example: run tests after source edits
    └── hook-block-env-write.sh  # Example: block writes to .env files
```

**What changes from the four source docs:**
- The **Overview** essay becomes the GitHub README (condensed) + the philosophy section of the Build OS. The narrative framing is the right tone for a README.
- The **Team Playbook** content is absorbed into the Build OS (file structure, workflow protocol, review, cheat sheets) and into the slash commands and templates. The "annotated project tree" becomes the actual project tree.
- The **Operating Reference** deep patterns are absorbed into the Build OS's "Patterns Worth Knowing" section and into the `.claude/rules/` starter files. The OpenClaw-specific content is dropped.
- The **Kernel** rules become the starter CLAUDE.md template. Instead of telling people "put these 18 rules in your CLAUDE.md," give them an actual CLAUDE.md they can customize.

### 4. The slash commands fill the gap the debate identified

The debate's biggest finding was that Anna Marie had named cognitive operations (triage, distill, connect, review) as executable slash commands, while Justin's system had the concepts but not the packaging. The proposed slash commands solve this:

- `/setup` — from Anna Marie's system, validated by debate as the best onboarding pattern either system has
- `/recall` — session bootstrap, equivalent to the Kernel's "retrieve before planning" rule made executable
- `/plan` — the planning threshold made into a workflow instead of just a rule
- `/review` — staged persona review as a runnable operation
- `/handoff` — session close discipline made executable
- `/sync` — upstream doc reconciliation as a command

These are engineering operations, not cognitive operations (triage/distill are domain-specific). The framework provides the structure; users add domain-specific commands for their context.

### 5. The four source docs should be retained privately but not published

The four docs represent Justin's accumulated knowledge. They should:
- Continue to exist in the OpenClaw repo as his personal operating reference
- NOT be published in the GitHub repo — they create confusion through overlap and wrong-audience framing
- Be referenced in the Build OS acknowledgments as the source material

---

## What the challengers should evaluate

1. **Structure:** Is the proposed file set the right structure? Too many files? Too few? Wrong organization?
2. **Audience:** Does this work for engineering teams who have never used Claude Code? For individuals? For teams already using it?
3. **Overlap with source docs:** Am I right that the four docs create more confusion than value if published alongside the Build OS?
4. **Slash commands:** Are these the right commands? Too many? Missing any?
5. **Tier model:** Does the tiered governance model hold up under scrutiny? Are the tier boundaries right?
6. **What's missing:** What does someone need that this framework doesn't provide?
