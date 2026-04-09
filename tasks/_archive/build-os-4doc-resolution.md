# Resolution: Four-Doc Publishable Structure

**Author:** Claude Opus (Round 3)
**Date:** 2026-03-13
**Responding to:** Challenger A (9 challenges, 5 MATERIAL) + Challenger B (3 challenges, 2 MATERIAL)

---

## Responses to Challenger A

### 1. [UNDER-ENGINEERED] [MATERIAL]: Topic ownership is muddy — enforcement ladder, review, essential eight appear in multiple docs

**CONCEDE.** This is the strongest challenge and both challengers raised it. The enforcement ladder appearing in Build OS, Team Playbook, AND Advanced Patterns is exactly the kind of overlap the whole restructure was supposed to fix.

**Revised rule — strict topic ownership:**

| Topic | Canonical doc | Other docs may... |
|---|---|---|
| Governance tiers | Build OS | Reference the tier table, never redefine it |
| Enforcement ladder | Build OS | Reference "see enforcement ladder in Build OS," give one-line reminder |
| Essential eight invariants | Build OS | Reference by name, never re-list all eight |
| Session loop | Build OS | Reference, never redefine |
| Operations (cognitive + engineering) | Build OS | Reference by operation name |
| Review personas and order | Build OS | Reference, add team-specific review notes |
| Contract test format | Build OS | Reference |
| Agent teams / parallel work | Team Playbook | Not mentioned elsewhere |
| Orchestration documents | Team Playbook | Not mentioned elsewhere |
| Cheat sheets | Team Playbook | Not mentioned elsewhere |
| Skills and eval pipelines | Team Playbook | Not mentioned elsewhere |
| Git worktrees | Team Playbook | Not mentioned elsewhere |
| Audit protocol | Advanced Patterns | Not mentioned elsewhere |
| Degradation testing | Advanced Patterns | Not mentioned elsewhere |
| Cross-model debate | Advanced Patterns | Not mentioned elsewhere |
| Failure classes table | Advanced Patterns | Not mentioned elsewhere |
| Proxy-layer budgets | Advanced Patterns | Not mentioned elsewhere |
| Instruction placement / Safety Rules block | Advanced Patterns | Not mentioned elsewhere |

**The discipline:** Each doc owns its topics. Other docs cross-reference with a one-line pointer ("See Build OS §V for the enforcement ladder"), never re-explain.

### 2. [ASSUMPTION] [MATERIAL]: ~1,400 lines may be too heavy for broad external adoption

**COMPROMISE.** The concern is legitimate — 1,400 lines IS a lot. But the alternative (thin core with topic pages) creates the fragmentation problem that Challenge 1 already identified. The fix is not fewer lines but better routing.

The reading guide table in Build OS already addresses this for that doc. What's missing is **repo-level routing** — a single "Start Here" block that tells every reader exactly what to read and what to skip.

**What to add to README (at the very top, before the essay):**

```
## Start Here

| You are... | Read | Skip |
|---|---|---|
| Curious what this is | This README | Everything else (for now) |
| Starting a project with Claude Code | README + run /setup | Team Playbook, Advanced Patterns |
| Running a team project | README + Build OS + Team Playbook | Advanced Patterns |
| Building a production system | Everything | Nothing |
```

This is 5 lines. It answers "what do I read?" before the essay begins. Most readers will only need 1-2 docs.

### 3. [ALTERNATIVE] [MATERIAL]: Organized by source-doc lineage rather than user journey

**COMPROMISE.** The challenger is right that the 4-doc structure maps to the original 4 docs. But the content mapping IS a user journey:

- README = "why should I care?"
- Build OS = "what do I do?"
- Team Playbook = "how do teams work together?"
- Advanced Patterns = "what do I need when things get serious?"

That IS a user journey: convince → framework → team operations → deep patterns. The structure shouldn't change. But the naming and "When to use this doc" sections should make the journey explicit rather than implicit. Each doc's opener should state the journey position.

### 4. [RISK] [MATERIAL]: Removing inline examples creates comprehension loss

**CONCEDE.** This is correct. The decisions.md template has a format example, but the Build OS itself doesn't show what a real decision entry looks like in context. Same for lessons.

**Revised approach:** Keep at least one inline example per critical artifact in the Build OS:
- One real decision entry (D-format with assertion title)
- One real lesson entry (L-format with assertion title)
- One contract test entry (the full 4-field format with a concrete invariant)

These examples stay in the docs even though templates exist. The template is what you copy. The inline example is how you understand it.

### 5. [UNDER-ENGINEERED] [ADVISORY]: Need a front-door map at the repo level

**CONCEDE.** Addressed by the "Start Here" table in Challenge 2 response.

### 6. [ASSUMPTION] [MATERIAL]: Adding scaffolding to README may dilute the essay voice

**CONCEDE.** The challenger is right that cross-references, tier tables, and Quick Start blocks can kill the rhythm of an essay.

**Revised approach:** The README has three clean sections:
1. **Start Here** — the 5-line routing table (above the essay)
2. **The Essay** — Justin's Overview, nearly untouched. No cross-reference tables mid-essay. No tier table (that's in Build OS). The essay references the framework conceptually but doesn't try to be a navigation doc.
3. **Quick Start** — at the bottom, after the essay. "Ready to try it? Open this repo in Claude Code and run `/setup`."

The essay stays pure. The routing and quick start bracket it without interrupting it.

### 7. [OVER-ENGINEERED] [ADVISORY]: 18→6 rules may over-compress

**REBUT.** The 6 rules ARE the 18 rules — the Kernel's 18 rules cluster into 6 themes. The HTML comments explain the mapping. And the `/setup` command generates a project-specific CLAUDE.md that may include more rules based on the tier. The starter template is a starting point, not the ceiling.

### 8. [RISK] [MATERIAL]: Some "advanced" content is critical for all tiers

**CONCEDE.** Both challengers raised this. Destructive command safety, compaction discipline, fresh-session rule, and "sanity-check volumes" are not Tier 2+ concepts — they protect solo developers too.

**Revised approach:** Move these to the Build OS under a new "Survival Basics" subsection in Part IX (Patterns Worth Knowing):
- Destructive command safety (check for --dry-run)
- Compaction discipline (compact at 50-70%)
- Fresh-session rule (restart after config changes)
- Sanity-check volumes, not just success codes

These are 4 short paragraphs. They belong in the document everyone reads, not the document only production teams read.

### 9. [UNDER-ENGINEERED] [ADVISORY]: Need concrete examples even after removing OpenClaw specifics

**CONCEDE.** Addressed by Challenge 4 response. Every concept keeps at least one generalized-but-concrete example.

---

## Responses to Challenger B

### 1. [OVER-ENGINEERED] [MATERIAL]: Same concept fragmented across 3 docs

**CONCEDE.** Same conclusion as Challenger A, Challenge 1. Strict topic ownership with cross-references instead of re-explanation. See the topic ownership table above.

### 2. [RISK] [MATERIAL]: README as essay violates open-source UX — Quick Start must come first

**COMPROMISE.** The challenger is right that developers expect "what is this, how do I use it" at the top. But the essay IS the differentiator — it's what makes someone keep reading instead of thinking "oh, another Claude Code template repo."

**Revised README structure:**

```
# The Build OS

A practical framework for building serious projects with Claude Code.

## Start Here
[5-line routing table]

## Quick Start
[Run /setup or manual 5-step setup — 10 lines]

---

## Why This Exists
[The essay — sections I-VII, Justin's voice, production stories]

---

## Further Reading
[Links to Build OS, Team Playbook, Advanced Patterns]
```

Quick Start and routing are above the fold. The essay follows for those who want the argument. This satisfies both the "I want to use it now" reader and the "I want to understand why" reader.

### 3. [ASSUMPTION] [ADVISORY]: Some "advanced" content is critical for solo developers

**CONCEDE.** Same conclusion as Challenger A, Challenge 8. Survival basics (compaction, destructive commands, fresh-session rule, volume sanity-checks) move to the Build OS.

---

## Revised Structure Summary

### README.md (~200 lines)
1. Start Here (routing table — 5 lines)
2. Quick Start (setup + manual — 10 lines)
3. The Essay (Why This Exists — Justin's voice, unchanged — ~140 lines)
4. Further Reading (links — 5 lines)

### docs/the-build-os.md (~520 lines)
- Parts I-VIII unchanged from current version
- Part IX expanded: operator scars as stories (not just bullets) + survival basics (compaction, destructive commands, fresh-session, volume checks) moved from advanced-patterns
- Inline examples for decisions, lessons, and contract tests (not just template pointers)
- Strict topic ownership: this is the canonical source for tiers, enforcement ladder, operations, session loop, review, essential eight, contract test format

### docs/team-playbook.md (~350 lines)
- Strictly team-specific content: agent teams, parallel work, orchestration docs, interface contracts, spawn prompts, git worktrees, cheat sheets, skills/eval, release discipline
- Cross-references Build OS for tiers, enforcement ladder, session loop, review personas — never re-explains them
- "When to use this doc" opener

### docs/advanced-patterns.md (~300 lines)
- Strictly deep/production content: audit protocol, degradation testing, cross-model debate, failure classes, proxy-layer budgets, instruction placement, Safety Rules block pattern, institutional memory lifecycle
- Survival basics (compaction, destructive commands, fresh-session) REMOVED — moved to Build OS
- Cross-references Build OS for enforcement ladder, essential eight — never re-explains them
- "When to use this doc" opener
