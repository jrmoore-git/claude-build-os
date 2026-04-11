---
debate_id: skill-rename-spec
created: 2026-04-11T13:49:32-0700
phase: refine
rounds: 4
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: no
---
# skill-rename-spec — Refined Document

## Round 1 (gemini-3.1-pro)
The specification is exceptionally well-structured. The tabular mappings between old and new states provide excellent operational clarity, and the design principles are user-centric and logical. 

To make this document even stronger, I have sharpened the "Implementation Tracks" at the end. In the original draft, these were written as high-level goals. I have converted them into concrete, executable phases with specific completion criteria to ensure there is zero ambiguity during the rollout.

## Round 2 (gpt-5.4)
The revision is already strong: the rename set is coherent, the user-facing names match intent, aliases preserve backward compatibility, and the suggestion/auto-run model reduces memorization. The structure is also mostly sound.

Key improvements made in this pass:
- Tightened execution details so the spec is easier to implement without guessing.
- Resolved a few ambiguity points:
  - `/start` is defined more clearly as an auto-run bootstrap that should be idempotent.
  - “recent `/check`” now needs an explicit freshness rule; the prior draft implied one but did not define it.
  - The boundary between `/challenge` and `/pressure-test` is now clearer.
  - The “no new hooks needed” line conflicted with “deploy post-action listeners”; this is corrected by distinguishing router/session observations from OS-level hooks.
- Improved flow by separating product behavior from implementation requirements and adding acceptance criteria.
- Preserved all recommendation-bearing sections and all original implementation tracks.

Remaining issues in the prior revision:
- It mixed user experience, migration policy, and implementation work in a way that could force readers to bounce around.
- Some terms were under-specified: “recent,” “artifact inventory,” “protected paths,” and “already loaded = skip.”
- A few recommendations were slightly softer than necessary. This revision makes them more executable rather than more tentative.

## Round 3 (claude-opus-4-6)
The current revision is well-structured and comprehensive. It reads as a clear, actionable spec. Here are the issues I identified and addressed:

1. **"Also available" commands are under-specified.** `/log`, `/sync`, and `/triage` appear in a table but lack the semantic detail given to other commands. `/triage` in particular has no old-name mapping, no description of what "classify incoming information" means concretely, and no explanation of when `/start` would suggest it. I added minimal but sufficient definitions.

2. **`/challenge --deep` appears once (in the "killed" table) with no prior definition.** The `/challenge` command semantics section doesn't mention a `--deep` flag or explain what "validate mode" from the old `/debate` maps to. This is a dangling reference. I resolved it by adding the flag to the `/challenge` semantics section.

3. **`/polish` semantics are missing.** Every other pipeline command gets a semantics subsection or at least a clear behavioral description. `/polish` ("6-round cross-model iterative improvement") has no detail on what the 6 rounds are, what "cross-model" means here, or how it differs from `/check`. I added a brief semantics block.

4. **`/explore` semantics are thin.** "3+ divergent directions with cross-model synthesis" needs at minimum a statement about what the output artifact looks like and how it feeds into `/plan`. Added.

5. **Freshness rule scope ambiguity.** The freshness rule says "relevant to the ship action" but doesn't define how relevance is determined. I tightened this to use the concrete signal: files changed since the last `/check` run that overlap with the files being shipped.

6. **Implementation tracks lack sequencing constraints.** The rollout order section partially addresses this, but the tracks themselves don't state dependencies. I added explicit dependency notes to each track.

7. **Context budget trigger is under-specified.** "Context budget at 55%" — 55% of what? Token window? Session cost? I clarified this refers to the context window token budget.

8. **Minor: the "Command Set" header is followed by "The 15 Skills" header with no content between them.** Removed the redundant empty header.

9. **The spec never states who owns implementation or target timeline.** This is intentional for a spec of this type (it's a design doc, not a project plan), so I left it alone.

No regressions from the previous revision were detected. The document is factually consistent throughout.

## Round 4 (gemini-3.1-pro)
The previous revision is strong, well-structured, and highly actionable. I have made a few targeted adjustments to sharpen execution and mitigate hidden operational risks:

1. **Git History Preservation:** Changed the instruction in Track 1 from standard `mv` to `git mv`. Moving skill directories without git awareness breaks file history and complicates rollback. 
2. **Find-and-Replace Safety:** Updated Track 3 to mandate strict word boundaries (`\b`) during global find-and-replace to prevent substring corruption (e.g., preventing `/status` from accidentally altering unrelated words like `/status_code`).
3. **Infinite Loop Prevention:** Added a strict constraint to the `/ship` freshness rule. If `/check` auto-runs and modifies files itself, it immediately invalidates its own freshness rule. Auto-run `/check` must execute in a reporting/read-only mode.
4. **Rollout Order:** Hardened the 5 steps in the recommended rollout order into imperative execution commands.

## Final Refined Document

# Skill Rename Spec: 15 Clear Names + Contextual Suggestions

## Goal

Rename and consolidate skills so command names match the user's immediate intent, preserve backward compatibility through aliases, and reduce manual orchestration through contextual suggestions and auto-run behavior.

This is an additive change: old names continue to work, new names become the primary interface, and the system steers usage toward the new names.

## Design Principles

1. **Names match the user's mental state, not the system's architecture.**
   When you're stuck on "what should I build?" the command `/think` comes to mind. You shouldn't need to remember that the system calls this "define discover."

2. **Every old name stays callable.**
   Renaming is additive. Nothing breaks.

3. **The system suggests the right skill at the right moment.**
   You shouldn't need to memorize the pipeline order.

4. **Auto-run routine stuff.**
   Session bootstrap, end-of-session wrap, and pre-ship checks must not require manual invocation.

## The 15 Skills

### Pipeline (daily use, in natural order)

| New | Old | One-liner | What it does |
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

| Command | Old | Description |
|---|---|---|
| `/log` | `/capture` | Manual capture of a decision, lesson, or rationale. Also auto-runs during `/wrap`. Output: timestamped entry appended to the session decisions log |
| `/sync` | `/doc-sync` | Synchronize project documentation with current state of code and specs. Also auto-runs after `/ship` |
| `/triage` | (new surface) | Classify incoming information (bug reports, feature requests, support threads) by urgency and type. Suggested by `/start` when unprocessed items exist in the intake area |

## Command Semantics

### `/start`

`/start` is the default session bootstrap. It combines the old `/recall` and `/status` behavior and adds a next-step suggestion.

It must:
- load relevant project/session context
- summarize current status
- detect obvious blockers or stale work
- suggest the most likely next command

It must be **idempotent** within the same loaded session:
- if session context is already loaded and status is current, do not re-run expensive bootstrap work
- instead, return the current status snapshot and any updated suggestion

### `/think`

`/think` drives problem discovery. It walks through forcing questions ("what problem?", "for whom?", "why now?"), runs landscape research if needed, and produces a design doc or problem-framing artifact. The output is the primary input to `/explore` and `/plan`.

### `/explore`

`/explore` generates 3 or more divergent solution directions for a framed problem. Each direction includes a one-paragraph description, key tradeoffs, and estimated complexity. The output is a comparison artifact that feeds into `/plan` (to select and implement a direction) or `/challenge` (to question whether any direction is worth pursuing).

Cross-model synthesis means at least two models contribute directions independently before a reconciliation pass merges, deduplicates, and contrasts them.

### `/challenge` vs `/pressure-test`

These two commands must stay distinct:

- `/challenge` answers: **should this work exist at all?**
- `/pressure-test` answers: **given a direction, what breaks, what opposes it, or how does it fail?**

Rule of thumb:
- use `/challenge` before committing to a project or major scope
- use `/pressure-test` after a direction exists and needs adversarial analysis

#### `/challenge --deep`

`--deep` invokes the old `/debate --validate` mode: a structured multi-model evaluation that produces a scored verdict (proceed / modify / kill) with explicit criteria. Use `--deep` when the default `/challenge` pass is insufficient — typically for high-cost or irreversible commitments.

### `/polish`

`/polish` runs iterative cross-model improvement on any document (spec, design doc, prose, code). The process:

1. Model A critiques the document and proposes specific edits.
2. Model B applies edits and produces a revised draft.
3. Repeat for up to 6 rounds or until both models agree no material improvements remain.

The output is the final revised document plus a changelog of what changed per round. `/polish` improves quality of content; `/check` validates correctness and readiness. Use `/polish` before `/check`, not instead of it.

### `/plan --auto`

`/plan --auto` replaces `/autoplan` and routes through the missing prerequisite steps only when they are absent from the current context.

Example behavior:
- if no design/problem framing exists, route through `/think`
- if options are unresolved, route through `/explore`
- if necessity has not been challenged for new scope, route through `/challenge`
- then produce the implementation plan

This is routing, not duplication: if the needed artifact already exists, do not re-run the step.

## Auto-Run Triggers

These happen without the user typing anything:

| Trigger | What runs | How to skip |
|---|---|---|
| Session opens | `/start` (bootstrap + status) | Already loaded = skip |
| `/ship` invoked without recent `/check` | `/check` runs first | `--skip-checks` |
| `/wrap` invoked | Captures decisions, writes session log, writes handoff | "skip" to any sub-step |
| After `/ship` completes | `/sync` (doc sync) | `--skip-sync` |
| Context window token budget at 55% | Suggest `/wrap` | User ignores = no action |

### Freshness rule for `/ship`

"Recent `/check`" must be evaluated against the current work state, not just time.

A prior `/check` counts as recent only if:
- no files included in the ship action have been modified since that `/check` run (determined by comparing file modification timestamps or commit SHAs against the `/check` completion record), **and**
- no new commits touching those files have occurred since that check

If either condition fails, `/ship` runs `/check` again unless `--skip-checks` is provided. 

*Safety Constraint:* Auto-run `/check` executions inside `/ship` must run in read-only/reporting mode. If an auto-run `/check` modifies files, it instantly invalidates its own freshness check, causing an infinite loop.

## Contextual Suggestions

`/start` reads project state at session open and suggests the right next skill. After key actions such as plan completion, code changes, and commits, lightweight checks suggest the natural next step.

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
| Unprocessed items in intake area | "/triage to classify incoming items" |

### How suggestions work

Suggestions are:
- one-line nudges
- dismissible by inaction
- shown after natural breakpoints such as commits, file writes, and plan completions
- never injected mid-thought or during active drafting unless explicitly requested

### Detection inputs

`/start` and the post-action suggestion pass inspect:
- artifact inventory in the active work area
- git status and recent commits
- whether a plan, design doc, challenge artifact, or review artifact exists for the active topic
- whether changed files intersect protected paths

### Protected paths

"Protected paths" must be defined in configuration, not inferred ad hoc. Typical examples include:
- deployment config
- auth or permissions code
- billing or financial logic
- migration scripts
- production infra definitions

If no configured protected-path list exists, the `/check --qa recommended before commit` suggestion must not trigger from path sensitivity alone.

### Implementation note

No new OS-level hooks are required for suggestions. The system generates them from session/router-visible events it already observes, especially:
- writes to `tasks/`
- successful git commits
- completion of named skill runs

If existing infrastructure does not expose one of these events to the session layer, add the minimum router-level event emission needed to surface it.

## `/check` Internal Routing

`/check` replaces four skills. The default is code review. Flags select specific checks:

```text
/check                  → code review (was /review)
/check --second-opinion → cross-model review (was /review-x)
/check --qa             → domain-specific QA (was /qa)
/check --governance     → governance scan (was /governance)
/check --all            → run all checks (pre-ship bundle)
```

When invoked without flags, `/check` reads the context:
- if there's a spec or refined doc, review against it
- if it's a pre-ship context, run `--all`
- otherwise, run standard code review

### `/check` output contract

Every `/check` invocation returns:
- **verdict**: pass, pass-with-warnings, or fail
- **blocking issues**: list (may be empty)
- **non-blocking issues**: list (may be empty)
- **checks run**: which of the four checks executed
- **suggested next action**: what to do based on the verdict

This contract prevents ambiguity when `/check` is auto-run inside `/ship`.

## `/design` Internal Routing

```text
/design consult         → design system consultation (was /design-consultation)
/design review          → visual QA with audit checklist (was /design-review)
/design variants        → generate multiple design options (was /design-shotgun)
/design plan-check      → designer's eye on a plan (was /plan-design-review)
```

`/design` is the only user-facing design entry point. The legacy sub-skill names remain callable as aliases but are not shown in help or suggestions.

## Migration

1. Old names stay as hidden aliases. They work indefinitely.
2. When an old name is used, print one-line hint: `(hint: /debate --explore is now /explore)`
3. `/start` only recommends new names.
4. Help output shows only new names.
5. `CLAUDE.md`, rules files, and cross-references updated to new names.
6. Session log and decisions docs reference new names going forward.

### Alias policy

Aliases must preserve behavior, flags, and defaults unless the behavior has been intentionally merged into a new command surface.

Examples:
- `/autoplan` → `/plan --auto`
- `/review-x` → `/check --second-opinion`
- `/wrap-session` → `/wrap`
- `/capture` → `/log`
- `/doc-sync` → `/sync`

If an old command mapped to a sub-mode, the alias invokes that sub-mode directly rather than emitting a help page.

## What's Killed (no alias needed)

| Old | Why |
|---|---|
| `/debate` as a top-level skill | Split into `/explore`, `/pressure-test`. `/challenge --deep` absorbs validate mode |
| `/define` as a name | Becomes `/think`. The "refine" mode of `/define` becomes part of `/polish` |
| `/review-x` as standalone | Becomes `/check --second-opinion` |
| `/autoplan` as standalone | Becomes `/plan --auto` |
| `/wrap-session` | Shortened to `/wrap` |
| `/recall` as standalone | Merged into `/start` |
| `/status` as standalone | Merged into `/start` |
| `/capture` as standalone | Renamed `/log`, also auto-runs in `/wrap` |
| `/doc-sync` as standalone | Renamed `/sync`, also auto-runs after `/ship` |

### Clarification

"Killed" means **not shown as primary top-level commands**. Old names remain callable as hidden aliases (per the migration section) unless a command is explicitly removed from the callable surface for technical reasons. None are removed in this spec.

The table above describes product positioning, not hard deletion.

## Implementation Tracks

**Track 1: Rename skill directories + SKILL.md files**
*No dependencies.*
- Execute `git mv` commands for all `.claude/skills/<old>/` to `.claude/skills/<new>/` to preserve version control history.
- Rewrite `SKILL.md` frontmatter (name, description, cross-references) in all migrated directories.
- Construct the merged skills (`/start`, `/check`, `/design`, `/polish`) by combining the logic from their deprecated standalone components.

**Track 2: Alias layer**
*Depends on: Track 1 (new skill endpoints must exist before aliases can resolve to them).*
- Implement command mapping in the central router to ensure all old names resolve to the new skill endpoints.
- Inject the standard stdout hint for deprecated commands: `(hint: [old_command] is now [new_command])`.

**Track 3: Update all cross-references**
*Depends on: Track 1 (new names must be final before bulk replacement).*
- Run global find-and-replace across `CLAUDE.md`, `.claude/rules/*.md`, and `tasks/` directory to update all skill invocations to the new syntax. Use strict word boundaries (`\b`) to prevent substring corruption.
- Verify no broken internal links remain in documentation.

**Track 4: Contextual suggestion system**
*Depends on: Track 1 (suggestions reference new command names) and Track 2 (aliases must be live so suggested commands work regardless of user habit).*
- Update `/start` logic to parse the active directory's artifact inventory and `git status`.
- Deploy post-action listeners that trigger the suggestion table logic specifically after file writes to `tasks/` and successful git commits.

**Track 5: Auto-run hooks**
*Depends on: Track 1 and Track 2 (the commands being auto-run must be functional).*
- Bind `/start` to the session initialization event.
- Insert `/check` execution block into the `/ship` pre-flight sequence, bypassed only by `--skip-checks`.
- Insert `/sync` execution block at the successful termination of `/ship`.

## Acceptance Criteria

The rename is complete when all of the following are true:

1. A user can invoke every new command shown in this spec.
2. A user can still invoke every old command listed as preserved by alias.
3. Help output shows only the new command set.
4. Deprecated command use prints the one-line replacement hint.
5. Session open triggers `/start`, and repeated `/start` calls do not duplicate expensive bootstrap work.
6. `/ship` auto-runs `/check` when the current work has changed since the last check (per the freshness rule).
7. `/wrap` captures decisions, writes a session log, and writes a handoff unless the user skips specific sub-steps.
8. `/sync` runs automatically after successful `/ship` unless `--skip-sync` is set.
9. Suggestions appear at natural breakpoints and do not interrupt active drafting.
10. `/check` and `/design` route correctly to their merged sub-modes and `/check` returns the specified output contract.
11. Documentation and rule references use the new names.
12. No broken aliases, links, or references remain after migration.

## Recommended Rollout Order

1. **Deploy Alias layer first** (Track 2, after minimal Track 1 scaffolding) so compatibility is guaranteed before anything else changes.
2. **Execute rename and merge of skill surfaces** (Track 1 complete): `/start`, `/check`, `/design`, `/plan --auto`, `/polish`.
3. **Update documentation and cross-references** (Track 3).
4. **Enable auto-run hooks** (Track 5): `/start` on session open, `/check` in `/ship`, `/sync` after `/ship`.
5. **Enable contextual suggestions** (Track 4) after the merged command surfaces are stable.
