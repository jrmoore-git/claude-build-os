# Build OS Cheat Sheet
## Pipeline by Task Type

```
SPIKE:       build
BUGFIX:      /plan --skip-challenge → build → /review → /ship
FEATURE:     /define refine → /plan → build → /review → /ship
NEW FEATURE: /define discover → /challenge → /plan → build → /review → /ship
BIG BET:     /define discover → /elevate → /challenge → /plan → build → /review → /ship
```

Optional: `/refine` on any plan or design before building. `/debate` for architectural uncertainty.

## Session Commands

| When | Run |
|------|-----|
| Starting a session | `/recall` |
| Need project status | `/status` |
| Ending a session | `/wrap-session` |
| Capture a decision mid-session | `/capture` |
| Route incoming info | `/triage` |

## All Skills

| Role | Skill | What it does |
|------|-------|-------------|
| PM | `/define` | Problem discovery (`discover`) or forcing questions (`refine`) |
| PM | `/elevate` | Stress-test scope and ambition (4 modes) |
| PM | `/status` | Project status + next action suggestion |
| Designer | `/design-consultation` | Create or upgrade DESIGN.md with competitive research |
| Designer | `/design-review` | Visual QA with browser, 94-item checklist |
| Designer | `/design-shotgun` | Generate and compare multiple design variants |
| Designer | `/plan-design-review` | Rate a plan 0-10 on design completeness |
| Architect | `/challenge` | Cross-model gate: should we build this? |
| Architect | `/debate` | Adversarial review: personas attack, judge rules, refine |
| Refiner | `/refine` | 6-round cross-model improvement on any document |
| Lead Eng | `/plan` | Write implementation plan with valid frontmatter |
| Lead Eng | `/autoplan` | Auto-detect tier, chain skills, surface taste decisions |
| Reviewer | `/review` | Cross-model code review (PM + Security + Architecture) |
| Reviewer | `/review-x` | Second opinion from a different model family |
| QA | `/qa` | Domain-specific QA validation |
| QA | `/governance` | Governance hygiene scan |
| Release | `/ship` | Pre-flight gates (tests + review + verify) then deploy |
| Release | `/doc-sync` | Sync docs to match what shipped |
| Session | `/recall` | Bootstrap session from disk (PRD, decisions, lessons) |
| Session | `/wrap-session` | Write handoff, session log, current state |
| Session | `/capture` | Extract decisions/lessons from conversation |
| Session | `/triage` | Classify and route incoming information |
| Bootstrap | `/setup` | Interactive project setup |
| Bootstrap | `/audit` | Two-phase blind discovery audit |

## Key Files

```
PRD:              docs/project-prd.md
Build plan:       docs/build-plan.md
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
