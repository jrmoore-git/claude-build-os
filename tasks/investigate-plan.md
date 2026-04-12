---
scope: "New /investigate skill — orchestrates existing BuildOS infra for live debugging and root-cause analysis"
surfaces_affected:
  - ".claude/skills/investigate/SKILL.md"
verification_commands:
  - "cat .claude/skills/investigate/SKILL.md | head -5  # confirm frontmatter"
  - "grep -c 'debate.py' .claude/skills/investigate/SKILL.md  # uses debate engine"
  - "grep -c 'recall_search' .claude/skills/investigate/SKILL.md  # uses recall search"
  - "grep -c 'finding_tracker' .claude/skills/investigate/SKILL.md  # uses finding tracker"
rollback: "rm -rf .claude/skills/investigate/"
review_tier: "T1 — new skill, cross-model review before merge"
verification_evidence: pending
---

# Plan: /investigate skill

## What

New user-invocable skill that provides structured root-cause analysis using BuildOS infrastructure that no generic debugging skill has access to.

## Why

BuildOS has `/audit` (archaeology) and `/pressure-test` (pre-mortem), but neither handles live debugging: "something is broken right now, help me find why." The hypothesis-test loop (propose cause -> check evidence -> narrow down) is the missing middle.

## Differentiators vs generic investigate

| Capability | Generic | BuildOS /investigate |
|---|---|---|
| Search code | grep | grep + `recall_search.py` (BM25 + semantic over governance docs) |
| Form hypotheses | LLM guessing | 3+ hypotheses with cited evidence, cross-model panel evaluation |
| Know WHY the system works this way | no | `enrich_context.py` + `decisions.md` surface architectural rationale |
| Track findings after investigation | doc dump | `finding_tracker.py` state machine (open -> addressed/waived/obsolete) |
| Detect stale artifacts | no | `artifact_check.py` catches plans/reviews that drifted from code |
| Prior gotchas | no | `recall_search.py` over `lessons.md` surfaces known domain pitfalls |
| Enforce diagnostic-before-fix | advisory | Structural: evidence phase must complete before diagnosis |

## Design

### Three modes

- **symptom** (default) — something is broken, find root cause
- **drift** — expected behavior changed, find what diverged
- **claim** — verify a claim about the system ("does X actually work?")

### Six phases

1. **Scope** — Parse input, determine mode, identify investigation target
2. **Gather** — Collect evidence without forming hypotheses (blind discovery, like audit Phase 1)
3. **Context** — Pull governance memory via enrich_context.py + recall_search.py
4. **Hypothesize** — Form 3+ competing hypotheses, each citing Phase 2 evidence
5. **Test** — Systematically test each hypothesis; cross-model panel on strongest candidate
6. **Route** — Persist findings via finding_tracker.py, route to decisions/lessons/tasks

### Infrastructure used

- `scripts/debate.py review-panel` — cross-model hypothesis evaluation (Phase 5)
- `scripts/recall_search.py` — search lessons + decisions for related gotchas (Phase 3)
- `scripts/enrich_context.py` — pull governance context for the investigation area (Phase 3)
- `scripts/finding_tracker.py` — persist findings with state machine lifecycle (Phase 6)
- `scripts/artifact_check.py` — detect stale plans/reviews in the investigated area (Phase 2)
- Health scripts (`check-infra-versions.py`, `check-current-state-freshness.py`) — validate environment isn't contributing to the issue (Phase 2)

### Output

`tasks/<topic>-investigation.md` with: symptom, evidence, hypotheses tested, root cause, recommended fix, routed findings.

## Files changed

1. `.claude/skills/investigate/SKILL.md` — new file (the skill)

## Risks

- Low: skill is read-heavy, write-light. Only writes investigation report + finding tracker entries.
- No new scripts, no new dependencies, no new abstractions.
