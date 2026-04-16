# Build OS Cheat Sheet

**You don't need to memorize any of this.** Just describe what you want to do — Build OS routes you automatically. Type `/guide` if you're lost. This reference is for when you want precision.

## Pipeline by Task Type

```
SPIKE:       build
BUGFIX:      /plan --skip-challenge → build → /review → /ship
SMALL FEATURE: /think refine → /plan → build → /review → /ship
NEW FEATURE:   /think discover → /challenge → /plan → build → /review → /ship
FEATURE+UI:  /think discover → /design consult → /challenge → /plan → build → /design review → /review → /ship
BIG BET:     /think discover → /elevate → /challenge → /plan → build → /review → /ship
```

If it has a UI, wire in `/design consult` (before plan) and `/design review` (before ship). Optional: `/polish` on any plan or design. `/challenge --deep` for architectural uncertainty. `/plan --auto` to auto-chain the full pipeline.

## Session Commands

| When | Run |
|------|-----|
| Starting a session | `/start` |
| Ending a session | `/wrap` |
| Capture a decision mid-session | `/log` |
| Route incoming info | `/triage` |

## All Skills

| Role | Skill | What it does |
|------|-------|-------------|
| PM | `/think` | Problem discovery (`discover`) or forcing questions (`refine`) |
| PM | `/elevate` | Stress-test scope and ambition (4 modes) |
| PM | `/prd` | Generate or validate a PRD from a design doc |
| PM | `/start` | Session bootstrap + workflow routing + contextual suggestions |
| Designer | `/design consult` | Create or upgrade DESIGN.md with competitive research |
| Designer | `/design review` | Visual QA with browser, 94-item checklist |
| Designer | `/design variants` | Generate and compare multiple design variants |
| Designer | `/design plan-check` | Rate a plan 0-10 on design completeness |
| Architect | `/challenge` | Cross-model gate: should we build this? |
| Architect | `/challenge --deep` | Full adversarial pipeline: challenge → judge → refine |
| Architect | `/explore` | 3+ divergent directions with cross-model synthesis |
| Architect | `/pressure-test` | Counter-thesis or pre-mortem failure analysis |
| Architect | `/investigate` | Structured root-cause analysis (symptom, drift, claim modes) |
| Refiner | `/polish` | 6-round cross-model improvement on any document |
| Lead Eng | `/plan` | Write implementation plan with valid frontmatter |
| Lead Eng | `/plan --auto` | Auto-detect tier, chain skills, surface taste decisions |
| Reviewer | `/review` | Cross-model code review (PM + Security + Architecture) |
| Reviewer | `/review --second-opinion` | Second opinion from a different model family |
| Reviewer | `/review --qa` | Domain-specific QA validation |
| Reviewer | `/review --governance` | Governance hygiene scan |
| Release | `/ship` | Pre-flight gates (tests + review + verify) then deploy |
| Release | `/sync` | Sync docs to match what shipped |
| Research | `/research` | Deep web research via Perplexity Sonar |
| Session | `/start` | Bootstrap session from disk (PRD, decisions, lessons) |
| Session | `/wrap` | Write handoff, session log, current state |
| Session | `/log` | Extract decisions/lessons from conversation |
| Session | `/triage` | Classify and route incoming information |
| QA | `/simulate` | Zero-config skill simulation (smoke-test + quality-eval) |
| System | `/healthcheck` | Learning system health check (scans lessons, decisions, rules) |
| Bootstrap | `/setup` | Interactive project setup |
| Bootstrap | `/audit` | Two-phase blind discovery audit |
| Discovery | `/guide` | Intent-based skill map — "what can I do?" |

## Key Files

```
PRD:              docs/project-prd.md
Plans:            tasks/<topic>-plan.md
Current state:    docs/current-state.md
Decisions:        tasks/decisions.md
Lessons:          tasks/lessons.md
Handoff:          tasks/handoff.md
Session log:      tasks/session-log.md
Rules:            .claude/rules/
Skills:           .claude/skills/
```

## Governance Tiers

| Tier | When to upgrade |
|------|----------------|
| 0 - Advisory | Default. `CLAUDE.md` + git + human review. |
| 1 - Structured | Lost context between sessions. Add PRD, decisions, lessons, handoff. |
| 2 - Enforced | Claude made risky changes without review. Add hooks + contract tests. |
| 3 - Production OS | System acts on your behalf. Add cross-model review + approval gating. |

## Shortcuts

- **Skip challenge:** `/plan --skip-challenge`
- **Trivial commit:** `[TRIVIAL]` in commit message (typo/doc-only)
- **Emergency commit:** `[EMERGENCY]` in commit message (bypasses plan gate with warning)
