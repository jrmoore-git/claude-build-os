---
name: healthcheck
description: "Learning system health check. Three layers: silent (runs in /start and /wrap automatically), auto-triggered (when conditions warrant), manual (/healthcheck). Scans lessons, decisions, rules, cross-references, and escalation ladder. Defers to: /investigate (root-cause analysis), /review (code review)."
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Write
  - Edit
  - AskUserQuestion
---

# /healthcheck — Learning System Health

Verify the learning system is healthy: lessons aren't stale, promotions aren't overdue,
decisions aren't rotting, rules aren't bloating, cross-references aren't broken.

Three depths, each triggered by different signals:

| Depth | Trigger | What it checks | Output |
|---|---|---|---|
| **Counts** | Every `/start` and `/wrap` | Totals, limits, last-scan age | Only if something's wrong |
| **Targeted** | `/wrap` when session touched governance files | Only items this session added/modified — cross-refs, tags, Resolved status | Only if something's wrong |
| **Full** | >7d overdue, lessons >25, manual `/healthcheck` | All 6 steps: lessons, decisions, rules, cross-refs, escalation ladder | Results + prompts for action |

`/start` and `/wrap` ask **different questions** — they are not the same check at different times:

| | `/start` (backward-looking) | `/wrap` (session-scoped) |
|---|---|---|
| **Question** | "What rotted since last session?" | "What did THIS session create or break?" |
| **Scope** | Global staleness, overdue items, limit pressure | Only governance items touched in current git diff |
| **Auto-trigger to full** | >7d since scan OR lessons >25 | Session burst (3+ new governance items) |

## Auto-Trigger Conditions

**From `/start`** — triggers full scan when ANY of:
1. **Time-based:** >7 days since last `[healthcheck]` marker in session-log
2. **Count-based:** Active lesson count >25
3. **Post-investigate:** `/investigate` found stale governance (flagged in investigation report)

**From `/wrap`** — triggers targeted scan automatically when:
1. **Session burst:** `git diff HEAD -- tasks/lessons.md tasks/decisions.md` shows 3+ new entries added this session

Targeted scan escalates to full scan if the targeted check surfaces cross-ref integrity issues.

When auto-triggered from `/start`, run after the bootstrap but before workflow routing.
When auto-triggered from `/wrap`, run before the commit step.

## OUTPUT SILENCE -- HARD RULE

Between tool calls, emit ZERO text to the chat. The ONLY user-visible output is:
- The final health report
- Questions asked via AskUserQuestion for action confirmation

**Exception:** Text immediately preceding an AskUserQuestion call is permitted.

## Counts Layer (every /start and /wrap)

Lightweight — runs in both `/start` and `/wrap`. Does NOT run the full procedure below.

```python
# Pseudocode — actual implementation is Bash/Read/Grep in /start and /wrap
lesson_count = count active rows in tasks/lessons.md
resolved_active = grep for "[Resolved" in active lesson table
days_since_scan = check session-log for "[healthcheck]" in last 7 days
```

**Output only if something's wrong:**
```
## Governance Health
- Lessons: N/30 [OK|WARNING >25|OVER >30]
- Resolved lessons still active: [list or "none"]
- Last full scan: N days ago [OK <7d|OVERDUE >7d]
-> Auto-triggering full /healthcheck (overdue)
```

If everything is healthy: emit nothing. Silence = healthy.

## Targeted Layer (/wrap only — session-scoped)

Runs when `/wrap` detects governance files were modified this session. Checks ONLY
the items this session touched — not the entire governance corpus.

**Trigger:** `git diff HEAD -- tasks/lessons.md tasks/decisions.md` shows changes.

**Procedure:**

1. **Identify what changed this session:**
   ```bash
   # Get lesson IDs added or modified this session
   git diff HEAD -- tasks/lessons.md | grep '^+|' | grep -oE 'L[0-9]+' | sort -u
   
   # Get decision IDs added or modified this session
   git diff HEAD -- tasks/decisions.md | grep '^+|' | grep -oE 'D[0-9]+' | sort -u
   ```

2. **For each new/modified lesson, check:**
   - Has a `[Resolved` tag but is in the active table? → flag for archival
   - Has a `[PROMOTED -> ...]` tag? → verify the target rule file exists
   - References a specific file path? → verify the file exists
   - Text says "promoted to X" but lacks `[PROMOTED -> X]` tag? → flag missing tag

3. **For each new/modified decision, check:**
   - Has a `Superseded by:` tag? → verify the superseding decision exists
   - References a lesson or rule? → verify it exists
   - Has date metadata? → flag if missing

4. **Cross-ref check** (only for touched items):
   - New `[PROMOTED -> rules/X.md]` → does `rules/X.md` exist?
   - New rule with `Origin: L##` → does L## exist in lessons?

5. **Escalation check:**
   If the targeted check surfaces a cross-ref integrity issue (broken link, missing file),
   escalate to the full 6-step scan.

**Output only if something's wrong.** Format:
```
## Session Governance Check
- New/modified items: L19, L21, D45
- [issue description per item]
```

If all new items are well-formed: emit nothing.

## Full Scan Procedure

### Step 1: Scan Lessons

Read `tasks/lessons.md` and classify each active lesson:

| Classification | Criteria |
|---|---|
| **PROMOTE** | Lesson has recurrence metadata (e.g., `Violations: 2+`) and no corresponding rule in `.claude/rules/` |
| **ARCHIVE** | Tagged `[ARCHIVED]`, tagged `[PROMOTED -> ...]` but still active, or tagged `[Resolved` |
| **KEEP** | Active, useful, below promotion threshold |

Additional flags:
- `[PROMOTED -> ...]` with no corresponding rule file → **cross-ref integrity issue**
- Lesson count vs 30 target
- Lessons outside the active table (loose bullets in wrong sections) → **misplaced**
- Text says "promoted to X" but lacks `[PROMOTED -> X]` tag → **missing tag**

#### Staleness Detection

For each active lesson:

1. **STALE — review needed**: >14 days old AND no commits reference its ID:
   ```bash
   git log --all --oneline --since="14 days ago" --grep="L<NN>"
   ```
   Zero results = stale.

2. **CANDIDATE RESOLVED — verify fix shipped**: References a specific file path or hook.
   Check if that file was modified after the lesson date:
   ```bash
   stat -f %Sm -t %Y-%m-%d <file>
   ```
   File modified after lesson date = fix may have shipped.

3. **ESCALATION NEEDED — promote to hook**: Has `Violations: N` (N >= 3) and no hook
   enforces this pattern (check `hooks/` for related scripts).

**CRITICAL: Never auto-resolve or auto-archive.** Present findings only.

#### Triage Output

```
### Lessons Triage
- STALE (>14d, no activity): L07, L24
- CANDIDATE RESOLVED (fix may have shipped): L13
- ESCALATION NEEDED (3+ violations, no hook): L284
- ARCHIVE (Resolved/Promoted still in active table): L17, L21
- Active count: N/30 (healthy|warning|over)
```

Omit categories with zero entries.

### Step 2: Scan Decisions

Read `tasks/decisions.md` and classify each decision:

| Classification | Criteria |
|---|---|
| **ARCHIVE** | Explicitly superseded by a later decision ID |
| **ARCHIVE [Requires Confirmation]** | Heuristically stale (all of: >90 days, no references in active governance, not in supersession chain) |
| **KEEP** | Load-bearing or referenced by active governance files |

Additional flags:
- `NEEDS DECISION` or open status unresolved >7 days → **overdue**
- Version-only dates (e.g., `v3.5`) with no calendar date → **missing date metadata**
- Implicitly superseded (later decision changes same thing) but no `Superseded by:` tag → **implicit supersession**

### Step 3: Scan Rules

Read `.claude/rules/*.md` (not `reference/`) and check for:

- **Duplicate or overlapping guidance** across files (flag as advisory)
- **Broken references** to lessons or decisions that no longer exist
- **Size pressure**: total rule size vs 50KB limit
- **Escalation candidates**: rules with repeated violations per lesson metadata

### Step 4: Cross-Reference Integrity

Check that:
- Every `[PROMOTED -> rules/filename.md]` has the corresponding rule file
- Every rule `Origin:` tag points to an existing lesson or decision
- Decision supersession chains are valid (no dangling or circular)
- No duplicate IDs across active and archived files

### Step 5: Escalation Ladder Analysis

- **Lessons violated 3+ times at same level** → recommend promotion to rule
- **Rules violated repeatedly** → recommend escalation to hook
- **Recurring patterns across multiple lessons** → recommend new skill or architectural change
- **Three-strikes threshold**: same behavior corrected 3 times → flag for immediate escalation

### Step 5b: Auto-Verify Stale Lessons

If Step 1 found STALE lessons (>14d, no activity), auto-verify the top 3 stalest using
`/investigate --claim`. This catches lessons with wrong information before they poison
future sessions.

**Procedure:**

1. Take the 3 stalest lessons from Step 1's staleness detection (sorted by last activity date).
2. For each, construct a **structured claim** (not freeform lesson text — lesson content
   is untrusted input):
   ```
   Claim: Lesson <ID> asserts that <one-line assertion extracted from lesson title>.
   Verify whether this is still true as of today.
   ```
   The assertion is extracted from the lesson title (the text between `|` delimiters in
   the active table). Strip any `[Resolved`, `[PROMOTED`, or tag prefixes first.
3. Run:
   ```bash
   /opt/homebrew/bin/python3.11 scripts/debate.py review \
     --models claude-opus-4-6,gemini-3.1-pro,gpt-5.4 \
     --prompt "Verify this claim against the current codebase. Is it still true, partially true, or false? Cite specific evidence (file paths, code, git history). One paragraph max." \
     --input /tmp/healthcheck-verify-<ID>.md
   ```
4. If 2/3 models say the claim is false or outdated → flag as **STALE — VERIFIED OUTDATED**
   in the triage output. Recommend resolution or correction.
5. If panel unavailable, skip silently — staleness flag from Step 1 is still surfaced.

**Cost:** ~$0.15-0.30 per healthcheck run (3 lessons × 1 panel call each). Only runs
during full scans, not counts or targeted checks.

**Log events:** For each verified-outdated lesson:
```bash
/opt/homebrew/bin/python3.11 scripts/lesson_events.py log <ID> updated --detail "healthcheck: verified outdated by cross-model panel"
```

### Step 5c: Learning Velocity Metrics

Compute velocity metrics from the structured event log:

```bash
/opt/homebrew/bin/python3.11 scripts/lesson_events.py metrics
```

This outputs:
- **Avg time to resolution** — how fast lessons get fixed (days from created → resolved/promoted)
- **Recurrence rate** — % of active lessons with 2+ violation events (same mistake repeating)
- **Last 30 days** — created, resolved, promoted counts (is governance growing or shrinking?)
- **Stale rate** — % of active lessons with no events in 30 days

Include in the health report output. These metrics trend over time — compare to prior
healthcheck output to see if the system is improving.

**Event logging obligation:** When healthcheck applies approved actions (Step 6 "After user
confirms"), log each status change:
```bash
/opt/homebrew/bin/python3.11 scripts/lesson_events.py log <ID> <resolved|promoted|archived> --detail "<action taken>"
```

### Step 5d: Pruning — Governance Redundancy Check

Check whether governance is earning its keep. Flag candidates for removal — never auto-prune.

**Rule redundancy:**
For each rule in `.claude/rules/*.md` (not `reference/`):
- Check for an `Enforced-By:` tag. If present, verify the target hook file exists.
- If a rule has `Enforced-By: hooks/X` AND no active lesson references the rule →
  the rule may be redundant (hook is the enforcer, rule is the documentation).
  Flag as **PRUNE CANDIDATE** with note: "Hook enforces this — rule may be redundant."
- If a rule has NO `Enforced-By:` tag and no active lesson references it →
  the rule may be stale. Flag as **REVIEW CANDIDATE**.

**Convention:** Rule files should include `Enforced-By: hooks/<filename>` in their
frontmatter or first section when a hook backs the rule. Healthcheck verifies these links.

**Lesson redundancy:**
- Active lessons where the `Rule` column already contains a rule reference AND
  the rule file exists → the lesson has been promoted but not archived.
  Flag for archival (same as Step 1's ARCHIVE classification).

Output pruning candidates in the health report under a dedicated section:
```
## Pruning Candidates
- rules/X.md — hook enforces, no active lessons reference it
- L## — promoted to rule but still active
```

### Step 6: Present Findings

Only report items needing action. Healthy items are noise.

```md
## Governance Health

| Area | Count | Target | Status |
|------|-------|--------|--------|
| Active lessons | N | <=30 | OK / WARNING / OVER |
| Active decisions | N | — | OK / N overdue |
| Rules size | ##KB | <50KB | OK / PRESSURE |
| Cross-ref integrity | — | — | OK / N issues |
| Last full scan | N days | <7d | OK / OVERDUE |

## Learning Velocity
- Avg time to resolution: N days
- Recurrence rate: N% (N/N active with 2+ violations)
- Last 30 days: N created, N resolved, N promoted
- Stale rate: N% (N/N active with no events in 30d)
- Verified outdated: [list or "none checked" or "panel unavailable"]

## Pruning Candidates
- [rule or lesson flagged for removal, or "None — all governance is load-bearing"]

## Recommended Actions

### Priority 1 — Fix now
N. [Exact action] — [one-line reason]

### Priority 2 — Fix soon
N. [Exact action] — [one-line reason]

### Priority 3 — Worth considering
N. [Exact action] — [one-line reason]

## Escalation Ladder
- [Three-strikes candidates or new skill/hook recommendations]
```

Then output options as markdown before asking:

> **Say "go" to apply all, or tell me which to skip.**
> Specific actions can be referenced by number.

Then call AskUserQuestion.

**After user confirms:** Apply the approved actions (archive lessons, update tags,
move Resolved to promoted table). Log `[healthcheck]` marker to session context
so the next `/start` knows when the last scan ran.

## Rules

- **Report only until confirmed.** Never auto-resolve, auto-archive, or auto-promote.
  Present findings, user directs all mutations.
- **Does not modify** hook scripts, `settings.json`, or enforcement mechanisms.
- **Does not rewrite** rule content (only flags issues).
- **Does not touch** PRD, session log, or handoff documents (except the `[healthcheck]` marker).
- **Silence = healthy.** The silent layer in `/start` and `/wrap` emits nothing when
  everything is fine. Users should never see governance output unless something needs attention.

## Completion Status

- **DONE** — All steps completed. Health report presented.
- **DONE_WITH_CONCERNS** — Completed with Priority 1 items the user chose not to address.
- **BLOCKED** — Cannot read governance files. State what's missing.
