# Skill Rename Spec: 15 Clear Names + Contextual Suggestions

## Design Principles

1. **Names match the user's mental state, not the system's architecture.** When you're stuck on "what should I build?" the command `/think` comes to mind. You shouldn't need to remember that the system calls this "define discover."
2. **Every old name stays callable.** Renaming is additive. Nothing breaks.
3. **The system suggests the right skill at the right moment.** You shouldn't need to memorize the pipeline order.
4. **Auto-run routine stuff.** Session bootstrap, end-of-session wrap, pre-ship checks — these shouldn't require manual invocation.

## The 15 Skills

### Pipeline (daily use, in natural order)

| New | Old | Description | What it does |
|---|---|---|---|
| `/start` | `/recall` + `/status` | "Where am I? What should I do?" | Bootstrap session context, show status, suggest next action |
| `/think` | `/define discover` | "I need to figure out what to build" | Problem discovery: forcing questions, landscape research, design doc |
| `/explore` | `/debate --explore` | "What are my options?" | 3+ divergent directions with cross-model synthesis |
| `/elevate` | `/elevate` | "Am I thinking big enough?" | Scope and ambition review. Four modes: expand, cherry-pick, hold, reduce |
| `/challenge` | `/challenge` | "Should we even build this?" | Cross-model gate: 3 models evaluate whether work is necessary |
| `/plan` | `/plan` + `/autoplan` | "How do I build this?" | Generate implementation plan. `--auto` for full pipeline routing |
| `/polish` | `/refine` + `/define refine` | "Make this better" | 6-round cross-model iterative improvement on any document |
| `/check` | `/review` + `/review-x` + `/qa` + `/governance` | "Is this ready?" | Code review + quality checks. Flags: `--second-opinion`, `--qa`, `--governance` |
| `/ship` | `/ship` | "Deploy this" | Pre-flight checks then deploy. Auto-runs `/check` if not run recently |
| `/wrap` | `/wrap-session` | "End session" | Write handoff, session log, capture decisions |

### Thinking tools (use when you need deeper analysis)

| New | Old | Description |
|---|---|---|
| `/research` | `/research` | Deep web research via Perplexity. Unchanged |
| `/pressure-test` | `/debate --pressure-test` | Counter-thesis or pre-mortem (`--premortem` flag) |

### Specialist (when the work calls for it)

| New | Old | Description |
|---|---|---|
| `/design` | 4 design skills | All design work. Modes: `consult`, `review`, `variants`, `plan-check` |
| `/audit` | `/audit` | Codebase audit. Unchanged |
| `/setup` | `/setup` | One-time project setup. Unchanged |

### Also available

| Command | Notes |
|---|---|
| `/log` | Manual capture of a decision/lesson. Also auto-runs during `/wrap` |
| `/sync` | Manual doc sync. Also auto-runs after `/ship` |
| `/triage` | Classify incoming information. Suggested by `/start` when needed |

## Auto-Run Triggers

These happen without the user typing anything:

| Trigger | What runs | How to skip |
|---|---|---|
| Session opens | `/start` (bootstrap + status) | Already loaded = skip |
| `/ship` invoked without recent `/check` | `/check` runs first | `--skip-checks` |
| `/wrap` invoked | Captures decisions, writes session log, writes handoff | "skip" to any sub-step |
| After `/ship` completes | `/sync` (doc sync) | `--skip-sync` |
| Context budget at 55% | Suggest `/wrap` | User ignores = no action |

## Contextual Suggestions

`/start` reads project state at session open and suggests the right next skill. After key actions (plan written, code changed, commit), lightweight checks suggest the natural next step.

### Suggestion triggers

| The system sees... | It suggests... |
|---|---|
| No design doc for active topic | "/think would structure this" |
| Design doc exists, no challenge artifact | "New scope — /challenge before /plan?" |
| User asks "what are my options?" | "/explore would generate divergent options" |
| Plan exists, unstarted | "Ready to build, or /elevate to check ambition?" |
| Code changed since last review | "/check to validate" |
| Diff touches protected paths | "/check --qa recommended before commit" |
| User writes or discusses a decision | "Want me to /log that?" |
| Research question in conversation | "/research would help — want me to run it?" |
| Session long, context above 55% | "Consider /wrap soon" |

### How suggestions work

Suggestions are one-line nudges, not interrogations. The user can ignore them. They appear after natural breakpoints (commits, file writes, plan completions), not mid-thought.

Implementation: enhance `/start` to read artifact inventory and git state. Add a lightweight post-action check that runs after writes to `tasks/` and after commits. No new hooks needed for suggestions — they're guidance from the session model based on what it observes.

## `/check` Internal Routing

`/check` replaces four skills. The default is code review. Flags select specific checks:

```
/check                  → code review (was /review)
/check --second-opinion → cross-model review (was /review-x)
/check --qa             → domain-specific QA (was /qa)
/check --governance     → governance scan (was /governance)
/check --all            → run all checks (pre-ship bundle)
```

When invoked without flags, `/check` reads the context:
- If there's a spec/refined doc, review against it (was /review with spec compliance)
- If it's a pre-ship context, run `--all`
- Otherwise, standard code review

## `/design` Internal Routing

```
/design consult         → design system consultation (was /design-consultation)
/design review          → visual QA with audit checklist (was /design-review)
/design variants        → generate multiple design options (was /design-shotgun)
/design plan-check      → designer's eye on a plan (was /plan-design-review)
```

## Migration

1. Old names stay as hidden aliases. They work indefinitely.
2. When an old name is used, print one-line hint: `(hint: /debate --explore is now /explore)`
3. `/start` only recommends new names.
4. Help output shows only new names.
5. CLAUDE.md, rules files, and cross-references updated to new names.
6. Session log and decisions docs reference new names going forward.

## What's killed (no alias needed)

| Old | Why |
|---|---|
| `/debate` as a top-level skill | Split into `/explore`, `/pressure-test`. `/challenge --deep` for validate mode |
| `/define` as a name | Becomes `/think`. The "refine" mode of /define becomes part of `/polish` |
| `/review-x` as standalone | Becomes `/check --second-opinion` |
| `/autoplan` as standalone | Becomes `/plan --auto` |
| `/wrap-session` | Shortened to `/wrap` |
| `/recall` as standalone | Merged into `/start` |
| `/status` as standalone | Merged into `/start` |
| `/capture` as standalone | Renamed `/log`, also auto-runs in `/wrap` |
| `/doc-sync` as standalone | Renamed `/sync`, also auto-runs after `/ship` |

## Implementation Tracks

### Track 1: Rename skill directories + SKILL.md files
- Rename `.claude/skills/<old>/` to `.claude/skills/<new>/`
- Update SKILL.md frontmatter (name, description, cross-references)
- Create merged skills: `/start`, `/check`, `/design`

### Track 2: Alias layer
- Old names still resolve to new skills
- Hint message on old name usage

### Track 3: Update all cross-references
- CLAUDE.md infrastructure reference
- `.claude/rules/*.md` files
- `tasks/` doc references

### Track 4: Contextual suggestion system
- Enhance `/start` with artifact-aware suggestions
- Post-action suggestion logic

### Track 5: Auto-run hooks
- Session start auto-bootstrap
- Pre-ship auto-check
- Post-ship auto-sync
