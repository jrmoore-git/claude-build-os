---
description: Patterns for authoring SKILL.md files -- data ownership, defaults, idempotency, routing
globs:
  - "skills/**"
---

# Skill Authoring Rules

- One skill owns each database table. Two skills writing the same table need unified idempotency or single ownership. Conflicting dedup strategies cause data corruption.
- Never leave `due_date` NULL in action items. Always infer a 7-day soft deadline when no explicit date exists. NULL dates create infinite actionable queues via `due_date IS NULL` views.
- sqlite3 multi-statement inserts via single CLI arg may silently not persist. Use separate `sqlite3` invocations per INSERT, or verify row count after multi-statement execution.
- When multiple skills could match the same input, each skill description must declare what it handles AND what it defers to other skills. Without explicit precedence, the LLM may route to the wrong skill or double-process.
- **Output silence rule:** Between tool calls, a skill MUST NOT emit text to the chat. No progress updates, no JSON echoes, no SQL results, no "checking..." messages. The ONLY user-visible output is the single formatted block at the end of the procedure. Intermediate output clutters the UI and causes double-renders (agent stream + delivery inject). Enforce with an explicit "Output silence -- HARD RULE" block. **Placement:** For skills that face external non-privileged users, use a standalone `## OUTPUT SILENCE -- HARD RULE` section placed before `## Safety Rules` -- prominence is more important than placement inside Safety Rules. For internal-only skills, a bold bullet inside Safety Rules is sufficient.
- **Single output format:** A skill that runs on multiple channels (cron vs on-demand) must produce ONE output format. Do not add separate compact and full format sections -- the agent will output both, causing double-renders. Design the single format to be informative enough for the primary UI; the delivery framework handles truncation for character-limited channels.
- **Cron skills producing output:** All cron jobs use `delivery.mode: "none"`. Skills that need delivery pipe their formatted output to a delivery script as the final procedure step. This is a deterministic filter -- narration between tool calls never reaches the delivery channel. Add a "Delivery routing" section at the end of the procedure with cron (pipe to script) vs on-demand (output text) paths.
- **Audit log for every run, even zero results.** Skills that process meetings, emails, or items MUST write an audit_log entry for every execution, including runs with 0 results found. Without this, a silent failure (timeout, no data, wrong date) is indistinguishable from a legitimate empty run. Log: action_type, item_count, and any candidate counts before filtering.
- **Two-pass extraction for LLM tasks.** For promise extraction, fact extraction, or any LLM classification task: first ask the LLM to list ALL candidate items without filtering, then ask it to filter/classify the full candidate list. A single "extract only the important ones" pass causes the LLM to silently miss items. Separating "find everything" from "evaluate each" prevents lazy omission.

## Persona Definition — Problem-First, No Style Classification

Personas in skills and tests are defined by **problem and answers only**. No style tables, no style columns, no style matrices, no communication-style stress tests. Register is observed in transcripts, not designed into test personas.

**Prohibited:**
- Tables or columns organizing personas by communication style
- "Style stress test" descriptions
- Validation result columns for style adherence
- Any persona classification dimension based on how someone communicates rather than what problem they have

## Skill Frontmatter — Description Field

Always use `description: "single line quoted string"` in skill frontmatter. Never use YAML `|` or `>` block scalars for the description field — Claude Code's skill loader doesn't expand them, causing the `/` menu to show literal `|` instead of the description text. Orphaned YAML lines between fields further corrupt frontmatter. After editing frontmatter, verify the `/` menu shows the correct text.

## LLM-Extracted Descriptions

LLM-extracted descriptions for tasks and action items must be action-oriented. State WHAT the owner must deliver ("Send deck to X by Friday"), never narrate that they promised ("X committed to send the deck"). Direction/description mismatches confuse downstream consumers. Enforce with a deterministic coherence check that rejects mismatched direction/description.

## Skill Query Bounds

Every skill that queries external data (email, calendar, APIs, database) must have explicit bounds: max result count (`--max` or `LIMIT`), max content size per result, and a scope filter (time window, account). Before committing a skill, answer: "If every query returns its maximum, how many tokens does one run consume?" If unbounded, the skill is not ready.

## Batch-then-Cache for Cron Skills

When a cron skill produces output that is consumed at a later scheduled time (e.g., prep generated in the morning, delivered as a reminder later), batch all work at the scheduled time and write results to a cache. At delivery time, read from cache — do not poll per-item. Per-item polling wastes API calls and tokens when a cache exists. The pattern: batch at generation time → write to cache → read at delivery time.

## Cron Output Contract
Any skill running in cron context MUST satisfy ALL of these:
1. Empty result -> zero output -- absolute silence (not "found 0", not "no items", not "already sent")
2. Auth failure -> zero output + audit log entry only
3. External API error -> zero output + audit log entry only
4. No narration -> never output "I'll check...", "Now I'll generate...", or any reasoning prefix
5. Every SKILL.md that runs in cron context must have an `## Output Contract` section at the top declaring what triggers output vs silent exit

## Completion Status Protocol

When completing any skill workflow, report status using one of:
- **DONE** -- All steps completed successfully. Evidence provided.
- **DONE_WITH_CONCERNS** -- Completed with issues the user should know about. List each concern.
- **BLOCKED** -- Cannot proceed. State what is blocking and what was tried.
- **NEEDS_CONTEXT** -- Missing information. State exactly what you need.

If you have attempted a task 3 times without success, STOP and escalate. Bad work is worse than no work.

## Skill Preamble Standard

Every user-invocable skill should include in its frontmatter `description` a one-line summary of when to use it and what it defers to other skills. The skill body should begin with a context pull (read current-state.md + recent session-log) unless the skill is lightweight (< 3 steps).

## AskUserQuestion Format

When asking the user a question mid-skill, always include: (1) the project and branch context, (2) what you're asking and why, (3) numbered options if applicable. Never echo secrets, internal paths, or sensitive incident details in questions.
