# The Build OS — A Framework for Building with Claude Code

**By Justin Moore**

A practical operating system for teams and individuals building serious projects with Claude Code. This framework treats Claude as a governed subsystem inside a real engineering workflow — not a chatbot you prompt harder.

---

## How to read this document

| You are... | Read these parts | Skim or skip |
|---|---|---|
| **Solo / personal project** | Philosophy, Tier 0–1, File System, Bootstrap, Survival Basics | Enforcement Ladder details, Model Routing |
| **Engineering team** | Philosophy, Tiers 1–2, File System, Operations, Review, Enforcement | Tier 3 specifics |
| **Production agent system** | Everything | Nothing |

This document is organized in layers:

1. **Philosophy** — the six things that matter (read once)
2. **Governance tiers** — pick the tier that matches your risk (read once, revisit when stakes change)
3. **File system** — what goes on disk and why (reference)
4. **Operations** — cognitive and engineering, named and composable (reference)
5. **Enforcement ladder** — how to make rules stick (reference)
6. **Memory model** — how state survives between sessions (reference)
7. **Review and testing** — how to verify work (reference)
8. **Bootstrap** — how to start a new project (do once)
9. **Patterns worth knowing** — hard-won production lessons (reference)
10. **Survival basics** — protect yourself from common failures (read once, internalize)

If you only read one section, read the governance tiers. Everything else follows from choosing the right tier.

---

## Part I. Philosophy

### 1. Governance beats prompting

Most AI coding guidance focuses on better prompts. That matters, but it stops being the main event once Claude participates in real work. The hard problems are architecture, memory, verification, and enforcement.

The shift: stop treating Claude like a chatbot. Start treating it like a governed subsystem.

### 2. The model may decide; software must act

The single most important architectural choice is where the model stops and deterministic software begins.

LLMs may: classify, summarize, draft, extract structured intent, propose plans.
Deterministic code must: mutate data, call APIs, validate schemas, enforce approvals, write audit logs.

The pattern: `deterministic fetch → LLM reason/draft → schema validate → deterministic apply → audit`

If the LLM can cause irreversible state changes, it must not be the actor.

### 3. State lives on disk, not in context

The context window is expensive RAM. The filesystem is free permanent storage.

Plans, decisions, reviews, state tracking — all belong on disk. Every decision gets written to a decisions log. Every session writes a handoff. Every plan is written to a file before execution starts. The context window is for active reasoning. Disk is for everything that needs to survive.

### 4. Retrieve selectively, not everything

Loading all docs into every session creates drift, not safety. The model hallucinates consistency with old state instead of inspecting current state.

CLAUDE.md is the only auto-loaded layer. Everything else — PRD, lessons, decisions, handoff — is retrieved when relevant to the current task.

Sequence: `retrieve → narrow → research → plan → execute`

### 5. Simplicity is risk control

Claude has a strong bias toward plausible overbuilding. Use Anthropic's anti-overengineering language verbatim in your CLAUDE.md:

> Avoid over-engineering. Only make changes that are directly requested or clearly necessary. Keep solutions simple and focused. Don't add features, refactor code, or make "improvements" beyond what was asked. Don't add error handling for scenarios that can't happen. Don't create abstractions for one-time operations. Don't design for hypothetical future requirements.

Use this language verbatim rather than paraphrasing — in practice, Claude responds to these exact phrases more reliably than to rewrites.

### 6. Every rule has a maintenance cost

Governance prevents failures. Governance also creates maintenance burden, onboarding friction, and operator fatigue. A lesson log that only grows is recording failures, not preventing them. A rule that nobody checks is advisory text in a better location.

Match governance depth to risk. A personal note vault does not need contract tests. A system that sends email on your behalf does.

---

## Part II. The Governance Tiers

Pick the tier that matches your project's blast radius. Move up when the stakes increase. Do not start at Tier 3 for a Tier 0 project.

### Tier 0 — Advisory Only

**For:** Personal projects, note systems, solo explorations, learning projects.
**Blast radius if Claude is wrong:** A file in the wrong folder. A bad summary. Easily reversible.
**Governance cost:** Near zero.

**What you need:**
- `CLAUDE.md` with operating rules
- Git for version control
- Human confirmation before destructive actions

**What you do NOT need:** Hook scripts, contract tests, toolbelt enforcement, review personas, audit logs.

**You're at the wrong tier if:** You've lost work because a session didn't know what the last session did. → Move to Tier 1.

### Tier 1 — Structured Memory

**For:** Multi-session projects, team projects, anything that lasts more than a week.
**Blast radius if Claude is wrong:** Wasted work from misalignment. Lost context between sessions. Relitigated decisions.
**Governance cost:** ~30 minutes setup, 5 minutes per session.

**What you add to Tier 0:**
- `docs/project-prd.md` — product source of truth
- `tasks/decisions.md` — numbered decisions with rationale (assertion-style titles)
- `tasks/lessons.md` — mistakes and patterns (assertion-style titles, target ≤30 active)
- `tasks/handoff.md` — what the next session needs to know
- `docs/current-state.md` — what is true right now
- A recall step at session start (read handoff + current-state + relevant lessons)
- A session close step (write to handoff + session log)

**What you do NOT need yet:** Hooks, contract tests, formal review personas, enforcement scripts.

**You're at the wrong tier if:** Claude has made a change to production code or user-facing output that you didn't review first. → Move to Tier 2.

**Title convention:** Both decisions and lessons use assertion-style titles. "Web auth must use HttpOnly cookies because query-param tokens leak" — not "Auth decision." The title IS the takeaway.

### Tier 2 — Enforced Governance

**For:** Production systems, anything that touches real users, anything with financial or reputational consequences.
**Blast radius if Claude is wrong:** User-facing errors. Data corruption. Incorrect sends. Security exposure.
**Governance cost:** Hours of initial setup, 15-30 minutes per session.

**What you add to Tier 1:**
- `.claude/rules/` — conditional rule files loaded when relevant
- `docs/contract-tests.md` — behavioral invariants that must not break
- `docs/review-protocol.md` — staged review order and definition of done
- At least one hook (block commits when tests fail, or auto-run tests after edits)
- Toolbelt scripts for state-changing operations (parameterized SQL, validated inputs)
- `docs/audit-corrections.md` — append-only log of corrected false audit findings

**You're at the wrong tier if:** The system acts on your behalf without human approval (sends emails, publishes content, modifies external data). → Move to Tier 3.

### Tier 3 — Production OS

**For:** Autonomous agent systems, anything that acts on your behalf, systems managing sensitive data.
**Blast radius if Claude is wrong:** Emails sent to wrong people. Financial data exposed. Trust destroyed.
**Governance cost:** Significant — justified by blast radius.

**What you add to Tier 2:**
- Cross-model debate for architecture decisions (see [Advanced Patterns](advanced-patterns.md) §7)
- Enforcement ladder fully operational: advisory → rules → hooks → architecture
- Model routing by task type with cost tracking
- Three-strikes escalation (if the same rule is violated 3 times at the same level, move it up)
- Kill switches and rollback paths for all autonomous actions
- Approval gating for all high-stakes actions (human reviews before anything irreversible)

### Upgrade triggers

| Event | Move to |
|---|---|
| Lost context between sessions for the first time | Tier 1 |
| Same decision relitigated in two different sessions | Tier 1 |
| Claude changed production code or output without review | Tier 2 |
| First external user or customer interaction | Tier 2 |
| First security or data-handling requirement | Tier 2 |
| System sends, publishes, or modifies external data autonomously | Tier 3 |
| Financial, legal, or reputational consequences if the system is wrong | Tier 3 |

---

## Part III. The File System

### Minimum viable project (Tier 1+)

```
project-root/
├── CLAUDE.md                    # Always-loaded operating rules. Keep short.
├── .claude/
│   ├── settings.json            # Hook config (Tier 2+)
│   ├── skills/                  # Slash commands — session operations (SKILL.md format)
│   └── rules/                   # Conditional rules, loaded when relevant
├── docs/
│   ├── project-prd.md           # Product source of truth
│   ├── current-state.md         # What is true now, blockers, next actions
│   ├── contract-tests.md        # Behavioral invariants (Tier 2+)
│   ├── review-protocol.md       # Review order and done criteria (Tier 2+)
│   └── audit-corrections.md     # Corrected false findings (Tier 2+)
├── tasks/
│   ├── decisions.md             # Numbered decisions with assertion titles
│   ├── lessons.md               # Assertion-titled patterns (≤30 active)
│   ├── handoff.md               # Next-session context
│   └── session-log.md           # Historical record
└── tests/                       # At least one smoke test (Tier 2+)
```

### Keep CLAUDE.md short

Target under 200 lines. CLAUDE.md loads into every session on every turn and consumes context budget. Research shows instruction compliance decreases as instruction count grows — prioritize ruthlessly. Put only rules that apply to every task in every session. The tradeoff: rules in `.claude/rules/` only load when the matcher triggers, so they're invisible for unrelated work. Rules that must apply to every task belong in CLAUDE.md. Rules that apply only to specific domains (security, auth, deployment) belong in scoped files.

### CLAUDE.md and rules are advisory, not enforced

CLAUDE.md and `.claude/rules/` files are context that Claude reads and tries to follow — they are not enforced configuration. This is why the enforcement ladder exists: when a rule must hold, escalate to a hook (deterministic, cannot be overridden) or architecture (structural, doesn't depend on Claude at all). The right mental model: **rules are strong suggestions; hooks are laws.**

For platform details — how rules load, how hooks fire, skills format, auto memory — see [Platform Features](platform-features.md).

### Scaling rule

Flat until it hurts, then nest. Add complexity only when you need it:
- `tasks/[phase]-orchestration.md` — when you have 3+ parallel tracks
- `state/[task]-state.json` — when you need machine-readable progress tracking
- `.claude/skills/` — when you have repeatable workflows worth packaging

### What goes where

| Change type | Document |
|---|---|
| Bug, gotcha, platform surprise | `tasks/lessons.md` |
| Settled architectural or product decision | `tasks/decisions.md` |
| What the next session needs to know | `tasks/handoff.md` |
| What is true right now | `docs/current-state.md` |
| How Claude should behave (always) | `CLAUDE.md` |
| How Claude should behave (conditionally) | `.claude/rules/*.md` |
| Behavioral invariants | `docs/contract-tests.md` |

---

## Part IV. The Operations

Two types of operations power the system. Name them so teams can discuss them.

### Cognitive operations — how you think

These are the operations that turn raw information into structured knowledge. They apply to any project, not just engineering.

| Operation | What it does | When to run |
|---|---|---|
| **Triage** | Classify incoming information and route it | When new input arrives |
| **Distill** | Extract claim-style insights from raw input | After learning something |
| **Connect** | Find relationships between existing knowledge | Weekly maintenance |
| **Review** | Synthesize what changed, what's emerging, what's stuck | Weekly |
| **Recall** | Load relevant prior context before planning | Session start |
| **Capture** | Extract decisions and lessons from conversations | After meetings, design sessions |

**Claim-style titles:** When distilling patterns, title them as assertions: "JWT cookie auth bridges Django sessions and Next.js cleanly" — not "Authentication patterns." The title IS the takeaway.

**The two-view principle:** The same data often serves different questions. Design for multiple lenses:
- Priority view: "What should I work on next?" (sorted by urgency)
- Relationship view: "What do I owe people?" (sorted by person)
- Timeline view: "What happened this week?" (sorted by date)

### Engineering operations — how you build

| Operation | What it does | When to run |
|---|---|---|
| **Plan** | Research the system, write a plan to disk, verify before executing | Before non-trivial work |
| **Execute** | Implement against the plan, not against conversation | After plan is verified |
| **Verify** | Prove it works — tests, logs, evidence, negative cases | Before declaring done |
| **Review** | Staged persona review for meaningful changes | Before committing |
| **Handoff** | Write what the next session needs to know | Before closing |
| **Sync** | Update PRD, decisions, lessons, rules after approved changes | After review |

### Session loop

1. **Recall** — load handoff, current-state, relevant lessons and decisions
2. **Plan** — research, then write plan to disk
3. **Execute** — implement against the plan
4. **Verify** — tests, evidence, negative cases
5. **Document** — update decisions, lessons, handoff
6. **Sync** — update PRD and rules if behavior changed

After significant meetings, design sessions, or external conversations where decisions were made, capture them to decisions.md and lessons.md. These are the most common source of institutional knowledge that never makes it to disk.

---

## Part V. The Enforcement Ladder

Rules are only as reliable as their enforcement mechanism. When a rule keeps being violated, move it up the ladder — don't reword it at the same level.

| Level | Mechanism | Reliability | Example |
|---|---|---|---|
| 1 | Advisory instruction in CLAUDE.md | Usually follows | "Do not edit .env files" |
| 2 | Conditional rule in `.claude/rules/` | When loaded | Auth rules load when touching auth code |
| 3 | Deterministic hook | Always fires | Block commits when tests fail |
| 4 | Architectural constraint | Impossible to violate | LLM cannot write directly to the database |

**Three-strikes rule:** If the same behavior has been corrected three times at the same level, escalate immediately. Do not keep rewriting advisory text for a behavior that clearly needs a hook or architectural constraint.

**Escalation speed matches blast radius:** Low-stakes, self-correcting failures can stay advisory. Repeatable failures with material downside should escalate rapidly — sometimes after one strike.

**Test your instructions:** After writing a rule, deliberately test whether Claude follows it. If it does not trigger reliably, escalate. A rule without a verification test is Level 1 regardless of where it lives. Before promoting a lesson to a `.claude/rules/` file, state how you would catch a violation. If you cannot describe a concrete test, the rule belongs in `lessons.md` until you can — it is advisory text in a better location, not enforced governance.

**Verify your verifiers:** Gates that check accumulated history files (session-log.md, lessons.md) will eventually always pass because the file has grown large enough to contain the keyword. Gates must check for fresh artifacts, not accumulated history.

### Promotion lifecycle

```
noticed → lessons.md → .claude/rules/ → hook → architecture
```

- **Lesson** (Level 1): noticed once, written down
- **Rule** (Level 2): recurring pattern, promoted to a rules file
- **Hook** (Level 3): rule kept being violated, now deterministic
- **Architecture** (Level 4): hook bypassed, now structurally impossible

A lesson violated for the second time should be promoted immediately. A second entry for the same pattern is evidence that Level 1 doesn't work. For high-blast-radius failures, promote after one violation (see escalation speed above).

A lessons file that only grows is recording failures, not preventing them. Target ≤30 active lessons. Triage regularly — promote, archive, or retire.

---

## Part VI. The Memory Model

A pile of markdown is not memory until it is queryable.

### Three layers

1. **Authoritative docs** — PRD, contract tests, review protocol. Source of truth. Rarely changes.
2. **Institutional memory** — decisions, lessons, handoff, session log, current state. Changes every session.
3. **Retrieval layer** — search, index, or bootstrap skill that loads the right slice before planning.

### Retrieval modes

Support at least:
- **Temporal** — what happened yesterday, last week, in the last N sessions
- **Topic** — what do we know about this issue across all docs
- **Structural** — which files, sessions, and outputs connect to this topic

For small projects, grep is fine. For larger knowledge bases, add ranked search (BM25 for structured docs, semantic retrieval for transcripts, hybrid when you need both).

### Session ingestion

At session end, a hook or script should:
- Export useful signal from the session
- Update the searchable index
- Refresh handoff.md if work is incomplete
- Refresh current-state.md if truth changed

This turns old sessions into recallable memory instead of dead chat history.

---

## Part VII. Review and Testing

### Review tiers

**Full review** for: new features, workflow changes, state transitions, auth/security, external dependencies.
**Log-only review** for: config changes, formatting, copy edits, non-behavioral cleanup.

The test: does this change affect how the system behaves? If yes → full review. If no → log only.

### Review order

For full reviews, run staged personas in this order:
1. **Architect** — structural issues, boundary violations, unnecessary complexity
2. **Staff Engineer + Security** — implementation quality, auth weaknesses, injection risks
3. **Product / UX** — does it solve the right problem simply enough?

Security has blocking veto on dependency changes, auth changes, and external code.

**Review gates bind to the unit of change.** A review written earlier does not gate later commits automatically. If any file the review covered has been modified since the review was written, the gate is stale. Re-review after significant changes.

### Contract tests

Behavioral invariants that must not break. The essential eight (add domain-specific ones on top):

1. **Idempotency** — duplicate inputs never produce duplicate outputs
2. **Approval gating** — no high-stakes action without explicit approval
3. **Audit completeness** — every operation logged, including failures
4. **Degraded mode visible** — silent failures are impossible
5. **State machine validation** — no invalid state transitions
6. **Rollback path exists** — every change can be reverted
7. **Version pinning enforced** — no unreviewed dependency changes
8. **Exactly-once scheduling** — scheduled jobs fire once per window

**Example contract test entry:**

```markdown
### C3: Audit completeness — every operation logged, including failures

**What it means:** Every state-changing operation writes an audit log entry
before AND after execution. Failures are logged, not swallowed.

**Why it matters:** Without complete audit trails, silent failures are
indistinguishable from correct behavior. Debugging becomes archeology.

**How it's tested:**
- Run the email-send path with a valid draft → verify audit entry exists
- Run with an invalid draft → verify failure audit entry exists
- Kill the process mid-operation → verify partial completion is logged

**What failure looks like:** A user reports "my email never sent" and
there's no audit entry for the attempt — you can't tell if the
operation was never attempted or if it failed silently.
```

### Definition of done

A task is not done because the model says it is done. It is done when:
- Behavior matches the spec
- Tests pass
- Negative cases were checked
- Evidence exists
- Rollback is understood
- Affected docs are updated

---

## Part VIII. Bootstrap

### Option A: Interactive setup (recommended)

Run `/setup` in Claude Code. It will:

1. Ask about your project — what you're building, who it's for, what's the risk
2. Pick a governance tier based on blast radius
3. Create only the files needed for your tier — CLAUDE.md, tasks/, and starter `.claude/skills/` commands
4. Customize CLAUDE.md for your project
5. Create starter content — a first decision, an initial PRD skeleton

Alternatively, run `/init` in Claude Code to generate a starter CLAUDE.md from your existing codebase, then layer governance files on top.

### Option B: Manual checklist

Create in this order:

1. `git init` and `.gitignore`
2. `CLAUDE.md` — core operating rules (use the starter template, target under 200 lines)
3. `docs/project-prd.md` — what you're building
4. `docs/current-state.md` — what is true now
5. `tasks/decisions.md` — first decision: "We chose [framework/approach] because [reason]"
6. `tasks/lessons.md` — empty, ready
7. `tasks/handoff.md` — empty, ready
8. `.claude/skills/` — copy the skills you need from this repo's `.claude/skills/` directory

Add when complexity demands:
- `.claude/rules/` — conditional governance (see `examples/rules/` for starters)
- `docs/contract-tests.md` — behavioral invariants
- `docs/review-protocol.md` — review order
- One hook — block commits when tests fail (see `examples/` for hook scripts)
- One smoke test — full-path integration check

---

## Part IX. Patterns Worth Knowing

These are real failures from production Claude systems. Each one taught a lesson that shaped this framework.

### The invented email

We had a system that prepared follow-up emails after meetings. It had attendee names from the transcript and company context from the CRM. One morning, a draft appeared in the outbox addressed to "sarah.chen@acmecapital.com" — an email address that did not exist anywhere in our systems. The model had constructed it from a name and a company domain, and it looked perfectly plausible.

We added an advisory rule: "Do not hallucinate contact data." The model ignored it within two sessions. The fix was architectural — a deterministic allowlist that validates every email address against verified records before any draft is created. The model proposes; the allowlist gates. Now the worst case is "draft not created" instead of "email sent to fabricated address."

That is the enforcement ladder in one sentence: when advisory fails, escalate to architecture.

### The mocks that validated the bug

A calendar integration had strong unit-test coverage. Every test passed. The CI was green. But the live system returned zero events for a day that clearly had meetings.

The problem: the mocked API response had the same incorrect field structure as the code expected. The mock didn't model reality — it modeled our (wrong) assumption about reality. The tests weren't testing the integration; they were testing whether our code was consistent with our misunderstanding.

One end-to-end smoke test against the real API — not the mock — would have caught it immediately. The lesson: your mocks encode your assumptions. If your assumptions are wrong, your tests validate the wrong thing perfectly. Build at least one smoke test that hits the real system.

### The $724 day

We noticed a cost anomaly: $724 against a daily budget of roughly $15. Nothing was technically broken. Every scheduled job had run. Every output looked correct.

The problem was model routing. Every cron job — including simple classification tasks and "is there anything to process?" checks — was running on the strongest (most expensive) model. Twenty scheduled jobs, each burning premium tokens on tasks that a mid-tier model could handle, added up fast.

The fix was routing by task type: classification and tagging go to the cheapest model that handles them reliably, synthesis goes to mid-tier, and only high-stakes drafting uses the strongest model. Cost discipline is architecture, not a billing cleanup exercise after the fact. A $15 budget documented in a routing guide means nothing — the limit must be enforced in code.

That lesson had a sequel. A post-meeting skill had a documented 10-run daily cap. The cap was never enforced in code. It burned $1,949 in eleven days. A limit that exists only in documentation constrains nothing.

### The gate that always passed

We built a commit gate: a PreToolUse hook that checked whether the session log contained evidence of a completed review before allowing a commit. It worked perfectly for weeks.

Then it stopped working — not by failing, but by always passing. The session-log.md file had accumulated months of entries. Every possible keyword the gate checked for existed somewhere in the file's history. The gate was syntactically correct and behaviorally broken. It bred false confidence for months before anyone noticed.

Gates must check for **fresh** artifacts — entries written during the current session, with timestamps or markers — not accumulated history. And before trusting any enforcement mechanism: ask what would cause this gate to always pass. Then write a test for that condition.

### Model routing by task type

Default to the cheapest model that handles the task reliably:

| Task type | Model tier | Why |
|---|---|---|
| Classification, tagging, routing | Cheapest fast model | Binary/categorical output, structured prompt |
| Extraction (entities, action items) | Cheapest fast model | Pattern matching against clear schema |
| Summarization, assembly | Mid-tier model | Needs coherent narrative |
| High-stakes drafting, nuanced judgment | Strongest model | Reputation risk, tone calibration |
| Validation, schema checks | Deterministic code | Not an LLM task |

### Provenance beats plausibility

The model must not invent source data. Names, email addresses, identifiers, and dates come from verified systems, not model inference.

| Data | Strongest source | Not this |
|---|---|---|
| Who attended | Transcript evidence | Calendar invite |
| Contact email | Verified directory / allowlist | LLM construction |
| Due date | Explicit mention in text | LLM default |
| Meeting topic | Transcript content | Calendar title alone |

Human inputs are also untrusted. Validate human-provided IDs, file paths, and assumptions the same way you validate model outputs.

### The LLM boundary in practice

The principle "the model may decide; software must act" looks like this in code:

```
# 1. DETERMINISTIC FETCH — code fetches verified data
record = db.query("SELECT * FROM drafts WHERE id = ?", [draft_id])

# 2. LLM REASONS — model classifies, summarizes, or drafts
llm_output = call_model("Classify this draft: " + record.text)

# 3. SCHEMA VALIDATE — code validates the model's output
if not valid_json(llm_output) or llm_output.action not in ALLOWED_ACTIONS:
    log_error("Invalid LLM output", llm_output)
    return  # Fail safe: do nothing

# 4. DETERMINISTIC APPLY — code performs the state change
db.execute("UPDATE drafts SET status = ? WHERE id = ?",
           [llm_output.action, draft_id])

# 5. AUDIT — code logs what happened
db.execute("INSERT INTO audit_log (action, draft_id, result) VALUES (?, ?, ?)",
           [llm_output.action, draft_id, "applied"])
```

Every step except step 2 is deterministic code. If the LLM hallucinates in step 2, step 3 catches it and step 5 logs it. The worst outcome is "nothing happened" — not "wrong thing happened."

### Strip before it reaches the model

Never trust a default response shape on a cost-sensitive path. In one case, extracting plain text instead of passing raw connector output cut the payload from 582K tokens to 9K — a 63x reduction for the same underlying data. Strip to what the model needs deterministically before it reaches the prompt. The model doesn't need the full API response; it needs the fields relevant to its task.

### Toolbelt audit

Periodically audit your system by mapping each operation to one of two buckets: deterministic code or LLM reasoning. The dangerous gaps are where the LLM is discovering, constructing, or guessing data that code should have fetched and validated first. Run this audit when adding a new integration, after security reviews, or quarterly for production systems.

### Metrics require time bounds

A number without a date range, recency context, and source is an incomplete finding. This applies to audits, reviews, cost reports, and status updates. Ad hoc conversation is exempt.

Wrong: "Daily cost is $488." Right: "Daily cost for March 1–7 (measured March 8, source: Postgres spend logs): $488."

### Hook safety

Hooks run arbitrary commands with user permissions. A `.claude/settings.json` committed to a repo can execute commands the moment Claude Code opens it. Review hook configs like CI scripts.

### Dependency discipline

Before trusting a new dependency (MCP server, npm package, Python library):
- What code will execute locally?
- What permissions does it have?
- What data can it read?
- How are updates pinned and reviewed?
- How easily can it be removed?

---

## Part X. Survival Basics

These apply at every tier. They protect solo developers as much as production teams.

### Compaction discipline

Use `/compact` proactively at roughly 50–70% context usage. Do not wait for the system to rescue an overgrown session. By the time automatic compaction arrives, quality has often already degraded — the model starts contradicting its own earlier work, dropping context, and making confident mistakes.

Long sessions are the most common source of subtle quality loss. When in doubt, split work into narrower tracks and compact early.

### Destructive command safety

Before using any mutating CLI command, check whether `--dry-run` exists. A command that "usually works" but has no undo path is a production risk.

We learned this when a platform CLI silently overwrote existing configuration during what was supposed to be an update. There was no `--dry-run`, no confirmation prompt, and no backup. The fix took longer than the original task. Assume this class of mistake is possible until disproven.

### Fresh-session rule

After changing `CLAUDE.md`, rules files, `.env`, or other loaded configuration, start a fresh session or reset. Running sessions continue using stale context — they loaded the old config at startup and will not pick up your changes.

This is one of the most common "why isn't my rule working?" issues. The rule is fine. The session is stale.

### Native session management

Claude Code provides built-in session continuity: `--continue` resumes the most recent session, `--resume` picks a specific one, `/rewind` creates checkpoints within a session, and `/btw` asks side questions without adding to conversation history. Use these alongside — not instead of — the handoff file. Native continuity preserves conversation; the handoff preserves decisions and intent. A resumed session has history but not structured context. See [Platform Features](platform-features.md) for the full reference.

### Sanity-check volumes, not just success codes

A pipeline can return valid JSON, no errors, and still be fundamentally wrong. If the output volume is wildly inconsistent with what you know should exist, stop and investigate.

We had an extraction that returned a small, perfectly formatted dataset from years of activity. The shape looked fine. The volume was nonsense — a few dozen records from a source that should have had thousands. The bug was only caught because someone asked whether the count made sense, not because any validation failed.

---

## Artifact Examples

These show what real entries look like. The templates provide the structure to copy; these examples show the substance to aim for.

### Decisions log entry

```markdown
### D7: Web auth must use HttpOnly cookies because query-param tokens leak

Decision: Web auth uses HttpOnly cookies.
Rationale: Query-param tokens leak to browser history, server logs, and
referrer headers. A security review caught this before launch.
Alternatives: Query-param tokens (rejected — leaks everywhere),
bearer headers only (rejected — too fragile for browser clients).
Date: 2026-03-01
```

**Convention:** Decision titles are assertions that carry the rationale. "Cookie-based auth" is a label. "Web auth must use HttpOnly cookies because query-param tokens leak" is a decision — the body becomes optional for routine scanning.

### Lessons log entry

```markdown
| # | Lesson | Source | Rule |
|---|---|---|---|
| 27 | Long sessions silently eat their own corrections — compact at 50–70% context | Build session | Split work into narrower tracks and compact early |
```

**Convention:** Lesson titles are assertions, not topics. The title is the takeaway. "Long sessions degrade quality" tells you nothing actionable. "Long sessions silently eat their own corrections — compact at 50–70% context" tells you what to do and when.

---

## Acknowledgments

This framework was developed through production work with Claude Code, cross-referenced with Anthropic's documentation and community best practices. The cognitive operations model (triage, distill, connect, review) was informed by Anna Marie Kelly's [claude-obsidian-os](https://github.com/annamarie-kelly/claude-obsidian-os), which demonstrated that Claude Code slash commands can serve as composable thinking operations. The governance tiers emerged from a cross-model debate (Claude Opus, GPT-5.4, Gemini 3.1 Pro) that challenged the original framework for context-blindness and overclaimed universality.

The model keeps getting smarter. The discipline around it is what you have to build yourself.
