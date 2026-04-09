# Skill Contract Standard

Every skill (an AI-driven procedure defined in a SKILL.md file) must satisfy a set of contracts that govern its behavior, output, and resource usage. These contracts prevent common failure modes: noisy cron jobs, unbounded queries, silent failures, and inconsistent output.

## Output Silence

Between tool calls, a skill MUST NOT emit text to the chat. No progress updates, no JSON echoes, no SQL results, no "checking..." messages.

The ONLY user-visible output is the single formatted block at the end of the procedure.

**Why:** Intermediate output clutters the UI and causes double-renders when both the agent stream and delivery mechanism show content simultaneously.

**Enforcement:** Add an explicit "Output silence -- HARD RULE" block to the skill.

**Placement rules:**
- For skills that face external or non-privileged users: use a standalone `## OUTPUT SILENCE -- HARD RULE` section placed before `## Safety Rules`. Prominence matters more than nesting.
- For internal-only skills: a bold bullet inside Safety Rules is sufficient.

## Single Output Format

A skill that runs on multiple channels (cron job vs on-demand invocation) must produce ONE output format. Never add separate compact and full format sections -- the agent will output both, causing double-renders.

Design the single format to be informative enough for the primary UI. The delivery framework handles truncation for character-limited channels.

## Cron Output Contract

Any skill running in cron context MUST satisfy ALL of these:

1. **Empty result -> zero output.** Absolute silence. Not "found 0", not "no items", not "already sent".
2. **Auth failure -> zero output + audit log entry only.**
3. **External API error -> zero output + audit log entry only.**
4. **No narration.** Never output "I'll check...", "Now I'll generate...", or any reasoning prefix.
5. **Declare the contract.** Every SKILL.md that runs in cron context must have an `## Output Contract` section at the top declaring what triggers output vs silent exit.

**Why:** A cron job that outputs "No meetings found" every 15 minutes generates noise. A cron job that silently fails with no audit log entry is indistinguishable from a legitimate empty run. The contract separates these cases.

## Cron Delivery Pattern

All cron jobs use `delivery.mode: "none"`. Skills that need delivery pipe their formatted output to a delivery script as the final procedure step. This is a deterministic filter -- narration between tool calls never reaches the delivery channel.

Add a "Delivery routing" section at the end of the procedure:
- **Cron path:** pipe output to the delivery script
- **On-demand path:** output text directly

## Audit Logging

Skills that process external data (meetings, emails, items) MUST write an audit log entry for every execution, including runs with 0 results found.

Without this, a silent failure (timeout, no data, wrong date) is indistinguishable from a legitimate empty run.

**Required fields:**
- `action_type` -- what the skill did
- `item_count` -- how many items were processed (0 is valid)
- Candidate counts before filtering (how many were considered vs how many passed)

## Two-Pass Extraction

For promise extraction, fact extraction, or any LLM classification task, use two passes:

1. **Pass 1: Find everything.** Ask the LLM to list ALL candidate items without filtering.
2. **Pass 2: Evaluate each.** Ask the LLM to filter/classify the full candidate list.

A single "extract only the important ones" pass causes the LLM to silently miss items. Separating "find everything" from "evaluate each" prevents lazy omission.

## Query Bounds

Every skill that queries external data (email, calendar, APIs, database) must have explicit bounds:

- **Max result count:** `--max` flag or `LIMIT` clause
- **Max content size per result:** truncate or summarize large items
- **Scope filter:** time window, account, or category

**Pre-commit check:** "If every query returns its maximum, how many tokens does one run consume?" If unbounded, the skill is not ready.

## Data Ownership

One skill owns each database table. If two skills write the same table, they need either:
- Unified idempotency (same dedup key, same conflict resolution), or
- Single ownership (one skill writes, others read)

Conflicting dedup strategies between skills cause data corruption.

## Skill Routing

When multiple skills could match the same input, each skill description must declare:
- What it handles
- What it defers to other skills

Without explicit precedence, the LLM may route to the wrong skill or double-process the same input.

## Completion Status Protocol

When completing any skill workflow, report status using one of:

| Status | Meaning |
|---|---|
| **DONE** | All steps completed successfully. Evidence provided. |
| **DONE_WITH_CONCERNS** | Completed with issues the user should know about. List each concern. |
| **BLOCKED** | Cannot proceed. State what is blocking and what was tried. |
| **NEEDS_CONTEXT** | Missing information. State exactly what you need. |

If you have attempted a task 3 times without success, STOP and escalate. Bad work is worse than no work.

## Skill Preamble Standard

Every user-invocable skill should include in its frontmatter:
- A `description` with a one-line summary of when to use it and what it defers to other skills
- The skill body should begin with a context pull (read current-state.md + recent session-log) unless the skill is lightweight (< 3 steps)
