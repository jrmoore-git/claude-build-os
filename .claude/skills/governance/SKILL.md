# Governance — Qualitative Governance Hygiene Scan

Scan lessons, decisions, and rules for staleness, promotion candidates, duplicates, and cross-reference integrity. Report findings with concrete recommendations. Defers to `/review` for code review and `/ship` for deployment.

## Procedure

### Step 1: Scan Lessons

Read `tasks/lessons.md` and classify each active lesson:

| Classification | Criteria |
|---|---|
| **PROMOTE** | Lesson has explicit recurrence metadata (e.g., `Violations: 2+`) and no corresponding rule exists in `.claude/rules/`. |
| **ARCHIVE** | Lesson is tagged `[ARCHIVED]`, tagged `[PROMOTED -> ...]` but still in the active list, or user previously confirmed it as a one-off. |
| **KEEP** | Lesson is active, useful, and below the promotion threshold. |

Additional flags:
- A lesson tagged `[PROMOTED -> ...]` with no corresponding rule found -> flag as a **cross-reference integrity issue**.
- Count total active lessons and compare against the target of 30.
- **Structural check**: lessons that appear outside the active table (e.g., loose bullets in wrong sections) are misplaced and must be flagged for migration into the table or archival.
- Lessons that say "promoted to X" in their text but lack the `[PROMOTED -> X]` tag have a missing tag — flag as integrity issue.

#### Staleness Detection

For each active lesson, run these checks:

1. **STALE — review needed**: Lesson is >14 days old AND no commits in the last 14 days reference its ID. Check with: `git log --all --oneline --since="14 days ago" --grep="LNNN"` (replace NNN with the lesson number). If zero results, it is stale.

2. **CANDIDATE RESOLVED — verify fix shipped**: Lesson references a specific file path or hook. Check whether that file exists and its last modified date is AFTER the lesson's date. Use `stat -f %Sm -t %Y-%m-%d FILE` (BSD stat on macOS) to get the file's modification date. If the file was modified after the lesson was created, the fix may have shipped.

3. **ESCALATION NEEDED — promote to hook**: Lesson has a `Violations: N` tag (or equivalent recurrence metadata) where N >= 3, AND no hook currently enforces this pattern (check `hooks/` directory for related hook scripts). These lessons have failed at the advisory level and need structural enforcement.

**CRITICAL: Never auto-resolve or auto-archive.** Present findings only. The user directs all mutations.

#### Triage Output

Add a "Lessons Triage" subsection to the governance report (in Step 6 output, after the health table):

```
### Lessons Triage
- STALE (>14d, no activity): L07, L24
- CANDIDATE RESOLVED (fix may have shipped): L13
- ESCALATION NEEDED (3+ violations, no hook): L284
- Active count: 17/30 (healthy)
```

Omit any triage category that has zero entries. If all lessons are healthy, output:
```
### Lessons Triage
- Active count: 17/30 (healthy)
- No staleness, resolution, or escalation flags.
```

### Step 2: Scan Decisions

Read `tasks/decisions.md` and classify each decision:

| Classification | Criteria |
|---|---|
| **ARCHIVE** | Decision is explicitly superseded by a later decision ID. |
| **ARCHIVE [Requires Confirmation]** | Decision is heuristically flagged as stale (see below). Never auto-executed. |
| **KEEP** | Decision still appears load-bearing or is referenced by active governance files. |

**Staleness heuristic** — a decision is a candidate for confirmed archival if it meets ALL of:
- Its date metadata (e.g., `Date: 2025-12-15`) is older than 90 days
- No references to its ID appear in active lessons, rules, or other active decisions
- It is not part of an active supersession chain

Age is determined from in-file date metadata, not from `git log`.

Additional flags:
- Decisions with `NEEDS DECISION` or open status notes that have been unresolved for >7 days -> flag as **overdue**.
- Decisions with version-only dates (e.g., `v3.5`) and no calendar date -> flag as **missing date metadata**.
- Decisions that are implicitly superseded (a later decision changes the same thing) but lack a formal `Superseded by:` tag -> flag as **implicit supersession**.

### Step 3: Scan Rules

Read `.claude/rules/*.md` (not `reference/`) and check for:

- **Duplicate or overlapping guidance** across files (requires model judgment — flag as advisory)
- **Broken references** to lessons or decisions that no longer exist
- **Size pressure**: measure total rule size and compare against the 50KB limit
- **Escalation candidates**: rules that appear to be repeatedly violated, based on explicit recurrence metadata in `tasks/lessons.md`

### Step 4: Cross-Reference Integrity

Check that:
- Every promoted lesson (`[PROMOTED -> rules/filename.md]`) has the corresponding rule file
- Every rule with an `Origin:` tag still points to an existing lesson or decision
- Supersession chains between decisions are valid (no dangling or circular references)
- No duplicate IDs exist across active and archived files

### Step 5: Escalation Ladder Analysis

Review the full scan results and identify enforcement ladder opportunities:

- **Lessons violated 3+ times at the same level** -> recommend promotion to rule
- **Rules violated repeatedly** (per lesson metadata) -> recommend escalation to hook enforcement
- **Recurring patterns across multiple lessons** -> recommend a new slash command or architectural change
- **Three-strikes threshold**: if the same behavior has been corrected three times, flag for immediate escalation per the enforcement ladder (lesson -> rule -> hook -> architecture)

### Step 6: Present Findings and Recommended Actions

Combine findings and recommendations into a single output. Don't list every KEEP item — only report items that need action or attention. Healthy items are noise.

**Structure:**

```md
## Governance Health

| Area | Count | Target | Status |
|------|-------|--------|--------|
| Active lessons | N | <=30 | OK / OVER |
| Active decisions | N | — | OK / N overdue |
| Rules size | ##KB | <50KB | OK / PRESSURE |
| Cross-ref integrity | — | — | OK / N issues |

## Recommended Actions

### Priority 1 — Fix now
N. [Exact action] — [one-line reason]

### Priority 2 — Fix soon
N. [Exact action] — [one-line reason]

### Priority 3 — Worth considering
N. [Exact action] — [one-line reason]

## Escalation Ladder
- [Any three-strikes candidates or new skill/hook recommendations]
```

For each recommended action, state exactly what you would change and in which file. Be opinionated — recommend the action you think is right, don't just list options. Group related items (e.g., "Archive L14, L15, L17 — all tagged PROMOTED with verified targets").

End with: "Say **go** to apply all, or tell me which to skip."

## What This Skill Does NOT Do

- Execute changes automatically — report only, user directs all mutations
- Modify hook scripts, `settings.json`, or enforcement mechanisms
- Rewrite rule content (only flags issues)
- Run `verify-state.sh` (complementary tool, not a dependency)
- Rely on `git log` for recurrence or age detection (except Step 1 staleness detection, which uses `git log --grep` to check for recent lesson references)
- Touch PRD, session log, or handoff documents

## When to Run

- At session close when governance counts approach limits
- On demand when governance drift is suspected
- After major sessions that added multiple lessons or decisions
- As part of quarterly governance audit (last: 2026-03-28)

## Cost

Low-medium. Primary cost is reading all governance files (~10K-30K tokens depending on file sizes). Duplicate detection across rules requires model judgment and is the most expensive operation. No external model calls — runs within the current session.

## Lessons from First Run (2026-04-02)

Issues discovered during the inaugural `/governance` scan that shaped this skill:

1. **Lessons can accumulate outside the active table.** The original lessons.md had ~24 lessons as loose bullets dumped after the "Archived" heading — technically misplaced but appearing active. The skill must check for lessons outside the table structure, not just scan the table.

2. **Promoted lessons without tags are invisible.** L262 said "Promoted to code-quality.md" in its text but lacked the `[PROMOTED]` tag. The skill must text-match "promoted to" as well as checking for the formal tag.

3. **Decisions with version-only dates can't be staleness-checked.** D01, D03, D06 used "v3.2", "v3.3", "v3.5" with no calendar date. The skill must flag these as metadata gaps, not silently skip them.

4. **NEEDS DECISION flags can go stale for weeks.** D15 and D65 had open status notes for 16-24 days. The skill must flag overdue status notes, not just staleness.

5. **Implicit supersession is common.** An earlier decision about surface hierarchy was superseded by a later one but had no formal link. The skill must detect when two decisions govern the same surface and the later one contradicts the earlier.

6. **Duplicate content across rule files is easy to miss.** The anti-slop vocabulary was identical in two files. The skill should check for literal text overlap, not just semantic similarity.

7. **One-off lessons mixed with active lessons inflate the count.** Without triage, the real active count was 35+ while the table showed 18. The skill must report the true count including misplaced items.
