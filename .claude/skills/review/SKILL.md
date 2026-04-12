---
name: review
description: "Cross-model code review. Default: 3 lenses (PM, Security, Architecture). Modes: --second-opinion (cross-model second opinion), --qa (5-dimension QA gate), --governance (governance hygiene scan), --all (run everything), --fix (review + auto-fix), --fix-loop (iterative fix cycle). Defers to /ship for deployment, /think for problem definition, /challenge --deep for adversarial design review."
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

## Interactive Question Protocol

These rules apply to EVERY AskUserQuestion call in this skill:

1. **Text-before-ask:** Before every AskUserQuestion, output the question, all options,
   and context as regular markdown. Then call AskUserQuestion. Options persist if the
   user discusses rather than picks immediately.

2. **Recommended-first:** Mark the recommended option with "(Recommended)" and list it
   as option A. If no option is clearly better (depends on user intent), omit the marker.

3. **Empty-answer guard:** If AskUserQuestion returns empty/blank: re-prompt once with
   "I didn't catch a response — here are the options again:" and the same options.
   If still empty: pause the skill — "Pausing — let me know when you're ready."
   Do NOT auto-select any option.

4. **Vague answer recovery:** If the user says "whatever you think" / "either is fine" /
   "up to you": state "Going with [recommended] since no strong preference. Noted as
   assumption." Proceed with recommended.

5. **Topic sanitization:** Before constructing any file path with `<topic>`, sanitize to
   lowercase alphanumeric + hyphens only (`[a-z0-9-]`). Strip `/`, `..`, spaces, and
   special characters. This prevents path traversal in file writes.

# /review — Unified Quality Check

## Mode Routing

Parse the user's invocation to determine which mode to run:

| Invocation | Mode | Description |
|---|---|---|
| `/review` (no flags) | **code-review** | Cross-model code review (3 lenses). Smart context: if `tasks/<topic>-refined.md` exists, review against spec. If pre-ship context detected (review + qa artifacts already exist), suggest `--all`. |
| `/review --second-opinion` | **second-opinion** | Get a second model's opinion on an existing review. Requires a prior `/review` review artifact. |
| `/review --qa` | **qa** | 5-dimension QA validation (test coverage, regression risk, plan compliance, negative tests, integration). |
| `/review --governance` | **governance** | Governance hygiene scan (lessons, decisions, rules, cross-references, escalation ladder). |
| `/review --all` | **all** | Run code-review, then QA, then governance. Aggregate results. |
| `/review --fix` | **fix** | Code review + auto-fix mode. Apply mechanical fixes, ask about judgment calls. |
| `/review --fix-loop` | **fix-loop** | Iterative fix cycle: review -> fix -> re-review, max 3 iterations. |

If the user passes a topic argument (e.g., `/review my-feature`), use it as the topic. Otherwise infer per Step 2 below.

## Output Contract

Every invocation returns:
- **Verdict:** `pass` / `pass-with-warnings` / `fail`
- **Blocking issues:** count and list (MATERIAL findings, QA failures, governance P1s)
- **Non-blocking issues:** count and list (ADVISORY findings, governance P2/P3s)
- **Checks run:** which modes executed
- **Suggested next action:** what to do next (`/ship`, fix and re-check, etc.)

---

## Mode: Code Review (default)

Three models review your diff through independent lenses (PM, Security, Architecture). If a debate spec exists, PM lens escalates to strict spec compliance.

### Step 0: Security posture

Ask: "Security posture? (1=move-fast, 2=speed-with-guardrails, 3=balanced, 4=production-grade, 5=critical). Default: 3"

Store as `POSTURE` (default 3). Pass `--security-posture $POSTURE` to `debate.py` commands.

### Step 1: Detect changes

```bash
git diff --name-only HEAD
git diff --cached --name-only
git diff --name-only
```

Combine all unique file paths. If no changes detected, tell the user "No changes to review" and stop.

### Step 2: Get topic

If the user provided a topic as an argument, use it. Otherwise infer from:
1. Recent `tasks/*-plan.md` files (use filename stem as topic)
2. Recent `tasks/*-challenge.md` files (use filename stem as topic)
3. Current git branch name (strip prefixes like `feature/`, `fix/`)
4. The nature of the changed files

Only ask if all inference fails. If asking, output candidate topics as a markdown list, mark the most likely one "(Recommended)", then call AskUserQuestion.

### Step 2.5: Fat template validation

Check if `tasks/<topic>-proposal.md` exists. If it does, read it and check for these sections:

1. **Always required:** `### Current System Failures` — warn if missing.
2. **Conditional:** If the proposal contains quantitative keywords (cost, frequency, token, percentage, latency, throughput, batch size, rate limit, per day, per month), check for `### Operational Context` — warn if missing.
3. **Conditional:** If the proposal contains replacement keywords (replace, instead of, new approach, migrate, rewrite, switch from, move to), check for `### Baseline Performance` — warn if missing.

If any warnings exist, output them as advisory (not blocking):

> **Template warnings** (advisory, not blocking):
> - Missing `### Current System Failures` — challengers may fabricate failure examples
> - Missing `### Operational Context` — quantitative claims lack grounding

If no proposal file exists, skip this step silently. These are warnings only — they do not block the review.

### Step 3: Get the diff

```bash
git diff HEAD -- ':!.env' ':!*.pem' ':!*.key' ':!*credentials*' ':!*secret*'
git diff --cached -- ':!.env' ':!*.pem' ':!*.key' ':!*credentials*' ':!*secret*'
```

Combine into the full diff to review. The pathspec exclusions prevent secrets from being sent to external models. If any excluded files were changed, note: "N files excluded from review (potential secrets). Review those manually."

### Step 4: Check for spec artifact

```bash
test -f tasks/<topic>-refined.md && echo "found" || echo "none"
```

If found, read it. This enables **spec compliance mode** — the PM lens validates implementation against the refined spec. The PM lens checks both positive compliance (does the diff implement what the spec requires?) and negative compliance (does the diff avoid what the spec forbids?). Negative compliance catches cases where implementation accidentally includes something the spec explicitly excluded — e.g., a regex pattern containing a term the spec said "EXCEPTION: do NOT include."

### Step 4.5: Enrich context

Pull relevant governance context (prior decisions, lessons learned) so reviewers know what was already decided.

1. Write a summary file for keyword extraction (enrich_context.py expects proposal-like text, not raw diffs):
   ```
   # Review: <topic>
   ## Changed files
   <list of changed file paths from Step 1>
   ## Spec summary
   <first 500 chars of spec if exists from Step 4, otherwise omit>
   ```
   Write this to a temp file.

2. Run enrichment:
   ```bash
   python3.11 scripts/enrich_context.py --proposal <temp summary file> --scope review
   ```

3. **Quality gate:** Parse the JSON output. If both `lessons` and `decisions` arrays are empty, skip — do not inject an empty context section.

4. If enrichment returned results, append a `## Prior Context (Governance)` section to the review temp file (the one containing the diff + spec). Format:
   ```
   ## Prior Context (Governance)
   *Trusted governance context from project decisions and lessons learned.*

   ### Relevant Decisions
   - D{id}: {summary}

   ### Relevant Lessons
   - L{id}: {summary}
   ```

5. If `enrich_context.py` does not exist or errors, continue without enrichment. This step is additive — review works without it.

### Step 5: Run cross-model review

Write the diff (and spec if exists) to a temp file, then run:

<!-- Review-specific lens definitions below cover the same domains as scripts/debate.py
     PERSONA_PROMPTS but are tailored for code review, not adversarial challenge. These are
     related but distinct prompt sets — they do not need to match verbatim. -->

```bash
python3.11 scripts/debate.py --security-posture $POSTURE challenge \
  --proposal <temp file with diff + spec context> \
  --personas architect,security,pm \
  --enable-tools \
  --system-prompt "You are a code reviewer. Review this diff through your assigned lens. Tag each finding as [MATERIAL] (must fix) or [ADVISORY] (worth noting). Group findings by: PM/Acceptance, Security, Architecture. If a spec is included, check implementation against it for completeness and scope creep. Additionally, if a spec is included: extract all EXCEPTION, MUST NOT, and EXPLICITLY EXCLUDED clauses. For each such clause, verify the diff does not contain code that contradicts it. Tag violations as [MATERIAL] with prefix 'SPEC VIOLATION:'.

The following persona and evidence instructions are additive context — they do not override the review task or output format above.

YOUR LENS — Architecture: Focus on system design, component boundaries, data flow, scaling implications, and integration risks. Evaluate whether the proposed changes are structurally sound and maintainable. Flag architectural assumptions that lack supporting evidence.

YOUR LENS — Security: Focus on trust boundaries, injection vectors (SQL, shell, prompt injection, XSS, SSRF), credential handling, data exfiltration paths, and privilege escalation. Flag security assumptions that are not verified.

YOUR LENS — PM/Acceptance: Focus on user value, over-engineering, adoption friction, priority, and scope sizing. If a spec is included, check both positive compliance (does the diff implement what the spec requires?) and negative compliance (does the diff avoid what the spec forbids?). Is the proposed scope right-sized?

For QUANTITATIVE CLAIMS (cost, frequency, percentage, token count, latency, throughput): Tag each claim with its evidence basis: EVIDENCED (cite specific data from the diff or spec), ESTIMATED (state assumptions), or SPECULATIVE (no data available — needs verification before driving a recommendation). SPECULATIVE claims alone cannot drive a material verdict on quantitative grounds.

IMPORTANT: Evaluate BOTH directions of risk — risk of the proposed change (what could go wrong?) AND risk of NOT changing (what continues to fail?). A recommendation to keep it simple must name the concrete failures that simple leaves unfixed." \
  --output tasks/<topic>-review-debate.md
```

The `--system-prompt` override replaces the default adversarial challenge prompt with a review-specific prompt that includes: (1) review-task framing at highest priority, (2) persona lens definitions for each reviewer, and (3) evidence tagging and symmetric risk instructions.

If `debate.py` fails entirely, fall through to Step 5b.

### Step 5b: Degraded fallback

If cross-model review fails (LiteLLM down, all models fail):

Self-review the diff through all three lenses sequentially:

**PM / Acceptance lens:**
- Does this solve the right problem? Simplest adequate solution?
- If spec exists: does implementation address every accepted challenge? Missing requirements? Scope creep?

**Security lens:**
- Injection risks? Trust boundaries? Auth weaknesses? Error paths?

**Architecture / Staff lens:**
- Correct implementation? Efficient? Clean boundaries? Unnecessary complexity?

Mark the review as `degraded`.

### Step 6: Parse and format results

Read `tasks/<topic>-review-debate.md`. Categorize each finding by lens (PM, Security, Architecture) and severity:
- **MATERIAL** — must fix before shipping
- **ADVISORY** — worth noting, not blocking

### Step 7: Write review artifact

Create `tasks/<topic>-review.md`:
```yaml
---
topic: <topic>
review_tier: cross-model
status: <passed|revise|degraded>
git_head: <current short SHA>
producer: claude-opus-4-6
created_at: <ISO datetime in Pacific>
scope: <comma-separated changed files>
findings_count: <N material>
spec_compliance: <true if spec existed, false otherwise>
---
```

Below the frontmatter, write findings grouped by lens:

```
## PM / Acceptance
- [MATERIAL|ADVISORY] Finding description

## Security
- [MATERIAL|ADVISORY] Finding description

## Architecture
- [MATERIAL|ADVISORY] Finding description
```

### Step 8: Status and next action

- **Any MATERIAL findings** -> `status: revise`. Tell user: "N material findings. Address them, then `/review` again."
- **No MATERIAL findings** -> `status: passed`. Tell user: "Review passed. Run `/ship` when ready."
- **LiteLLM down** -> `status: degraded`. Tell user: "Cross-model review unavailable. Single-model review completed with degraded status. `/ship` will note the degraded status but won't block."

Display:
```
## Review Result: <PASSED|REVISE|DEGRADED>

| Lens         | Material | Advisory |
|--------------|----------|----------|
| PM           | N        | N        |
| Security     | N        | N        |
| Architecture | N        | N        |

Spec compliance: <yes (tasks/<topic>-refined.md)|no spec found>
Artifact: tasks/<topic>-review.md
```

After displaying the result, update the pipeline manifest:

```bash
python3.11 scripts/pipeline_manifest.py add <topic> --skill check --artifact tasks/<topic>-review.md --status complete
```

## Important Notes (Code Review)

- No tier classification. No debate orchestration. Just "three models look at your diff from three angles."
- If `tasks/<topic>-refined.md` exists, the PM lens automatically checks spec compliance. This is the key linkage: `/challenge --deep` produces a spec, `/review` enforces it.
- Degraded mode is advisory, not blocking. `/ship` will note it.
- Re-running `/review` overwrites the previous review artifact.

---

## Fix-First Mode (opt-in: `--fix`)

When the user runs `/review --fix` or `/review <topic> --fix`, enable Fix-First mode after the standard review completes:

### Fix-First Heuristic

For each MATERIAL or ADVISORY finding, classify as AUTO-FIX or ASK:

**AUTO-FIX** (apply without asking):
- Dead code / unused variables
- Stale comments contradicting code
- Missing error logging (bare `except: pass`)
- Typos in user-facing strings

**ASK** (needs human judgment):
- Security findings (auth, injection, trust boundaries)
- Race conditions
- Design decisions / API changes
- Anything where reasonable engineers could disagree

**Rule of thumb:** If the fix is mechanical and a senior engineer would apply it without discussion, AUTO-FIX. Otherwise ASK.

### Procedure

1. After Step 8 (standard review output), if `--fix` was passed:
2. Classify each finding as AUTO-FIX or ASK
3. Apply all AUTO-FIX items, outputting: `[AUTO-FIXED] [file:line] Problem -> fix applied`
4. Output all ASK items as a numbered markdown list with per-item recommendations BEFORE calling AskUserQuestion. Example: "1. [Issue] — Recommendation: [fix approach]\n2. [Issue] — Recommendation: [fix approach]"
5. Batch into a single AskUserQuestion with numbered options
6. If AskUserQuestion returns empty: re-prompt once with the same list. If still empty: pause fix mode — "Pausing fix mode. ASK items logged in the review file for later."
7. Apply fixes for items the user approves

Without `--fix`, review remains read-only — findings are reported but no code is modified.

---

## Fix-Loop Mode (opt-in: `--fix-loop`)

When the user runs `/review --fix-loop` or `/review <topic> --fix-loop`, enable an automated fix -> re-review cycle:

### Procedure

1. Run the standard review (Steps 1-8).
2. If **no MATERIAL findings** -> stop. Review passed on first iteration.
3. If MATERIAL findings exist, start the fix-loop:
   a. Apply AUTO-FIX items (same heuristic as `--fix` mode above).
   b. Present ASK items to the user. Apply approved fixes.
   c. Re-run Steps 3-8 (get a fresh diff from the updated code, run cross-model review again).
   d. Increment the iteration counter.
4. **Termination bounds (HARD RULE — max 3 iterations):**
   - If iteration 3 still has MATERIAL findings -> **stop and escalate**: "3 review iterations complete. N material findings remain. Manual review required." Write remaining findings to the review artifact.
   - If any iteration produces 0 MATERIAL findings -> **stop with passed status**.
   - If the user declines all ASK items in an iteration (no fixes applied) -> **stop**: "No fixes applied — loop would not progress. N material findings remain."
5. After the loop completes, write `tasks/<topic>-review-iterations.md` tracking:
   - Number of iterations run
   - Per-iteration: findings count, AUTO-FIX count, ASK count, user-approved count
   - Final status (passed / escalated / stalled)

### Example output

```
## Fix-Loop Complete

| Iteration | Material | Auto-Fixed | Asked | Approved | Status |
|-----------|----------|------------|-------|----------|--------|
| 1         | 5        | 2          | 3     | 2        | fixed  |
| 2         | 1        | 1          | 0     | —        | fixed  |
| 3         | 0        | —          | —     | —        | passed |

Review passed after 3 iterations. Artifact: tasks/<topic>-review.md
```

`--fix-loop` implies `--fix` — you do not need to pass both.

---

## Mode: Second Opinion (`--second-opinion`)

Get a second model's opinion on an existing `/review` review. Requires a prior review artifact at `tasks/<topic>-review.md`.

### Prerequisites

A completed `/review` review artifact must exist at `tasks/<topic>-review.md` before running this mode.

### Procedure

#### Step 1: Load the primary review
Read `tasks/<topic>-review.md` and the relevant diff (`git diff` or staged changes).

#### Step 2: Generate the cross-model prompt
Produce this exact prompt (fill in the bracketed sections):

```
You are a hostile senior engineer reviewing code changes. Your job is to find problems the primary reviewer missed, and to challenge findings you disagree with.

DIFF HASH: [first 8 chars of sha256 of the diff — for staleness verification]
REVIEW DATE: [ISO 8601]

PRIMARY REVIEWER FOUND THESE ISSUES:
[Copy blocking + concerns from the primary review]

HERE IS THE DIFF:
[The actual diff]

INSTRUCTIONS:
For each finding from the primary reviewer, state: AGREE or DISAGREE (with reason).
Then list any NEW issues the primary reviewer missed entirely.

Format your response as:
## Primary findings
- [finding]: AGREE | DISAGREE — [reason if disagree]

## Missed issues
- [issue]: [severity: blocking | concern] — [explanation]

## Metadata
- diff_hash: [repeat the DIFF HASH above]
- model: [your model name]
- date: [today's date]
```

When the user pastes the response back, verify the `diff_hash` matches. If it doesn't, the response is stale — ask for a fresh review.

#### Step 3: Get the second opinion

**Option A — Copy-paste (default, no infrastructure):**
Tell the user: "Paste this prompt into a different AI model and paste the response back here."

**Option B — Automated (if configured):**
If your project has a cross-review script, run it automatically. The script should accept the prompt on stdin and return the response on stdout.

#### Step 4: Classify findings

Read the second model's response and classify every finding:

- **Consensus**: both models flagged the same issue -> **blocking by default**
- **Confirmed**: second model agrees with primary finding -> no change to severity
- **Singleton (primary only)**: primary found it, second model didn't mention it -> stays as-is
- **Singleton (secondary only)**: second model found something primary missed -> **concern** (not auto-blocking)
- **Disputed**: models explicitly disagree on whether something is a problem -> **requires human decision**

#### Step 5: Write the artifact

Create `tasks/<topic>-review-x.md`:

```markdown
# Cross-Model Review: [topic]

**Primary model:** Reviewer A
**Secondary model:** Reviewer B
**Date:** [ISO 8601]

## Consensus (both models agree — blocking)
- [finding]

## Confirmed (second model agrees with primary)
- [finding]

## Singleton — secondary only (new findings)
- [finding]: [blocking | concern]

## Disputed (models disagree)
- [finding]: Primary says [X], Secondary says [Y]
- **Human decision required:** [what needs to be decided]

## Summary
- Consensus blocking: [count]
- New findings from second model: [count]
- Disputes requiring human judgment: [count]
```

#### Step 6: Present results

Show the user the merged findings. Highlight:
1. Any **consensus blocking** issues (highest confidence — fix these)
2. Any **new findings** from the second model (worth investigating)
3. Any **disputes** that need human judgment

### Rules (Second Opinion)
- This mode is optional. `/review` code review is complete without it.
- Only consensus findings auto-block. Singleton findings from the second model are concerns, not blockers.
- Disputed findings are never auto-resolved. Surface both positions and let the human decide.
- **Anonymous labels only.** The cross-model prompt must not reveal which model performed the primary review. Use "primary reviewer" / "Reviewer A" / "Reviewer B" — never model names. This prevents anchoring bias.

---

## Mode: QA (`--qa`)

5-dimension quality assurance validation. Produces a go/no-go report.

### Procedure

#### Step 1: Detect scope

Find the most recent topic artifact:
```bash
ls -t tasks/*-plan.md tasks/*-review.md 2>/dev/null | head -5
```

Extract the topic from the newest file. If unclear, ask the user.

#### Step 2: Load context

Read the plan (if exists):
```bash
cat tasks/<topic>-plan.md 2>/dev/null
```

Read the review (if exists):
```bash
cat tasks/<topic>-review.md 2>/dev/null
```

Get the diff:
```bash
git diff HEAD --stat && git diff HEAD
```

#### Step 3: Evaluate 5 dimensions

Work through each dimension. For each, note PASS or FAIL with a one-line reason.

**1. Test coverage:**
- For each changed `.py` or `.sh` file, check if a corresponding test file exists:
  ```bash
  ls tests/test_*.py
  ```
- New scripts without tests = FAIL.

**2. Regression risk:**
- Check for changed function signatures. Are all callers updated?
- Check for changed imports. Are all importers updated?
  ```bash
  git diff HEAD -- '*.py' | grep -E '^\+.*def |^\-.*def '
  ```

**3. Plan compliance:**
- If a plan exists: does the actual diff match the plan's `surfaces_affected`?
- Files changed but not in the plan? Files in the plan but not changed?

**4. Negative tests:**
- Are error paths covered? (bad input, missing files, timeouts)
- Check test files for assertions on error cases.

**5. Integration:**
- If imports or interfaces changed, are downstream consumers updated?
- If new scripts were added, are they referenced correctly (shebangs, paths)?

#### Step 4: Run tests

```bash
bash tests/run_all.sh
```

If tests fail, note which ones.

#### Step 5: Produce report

Determine overall result: `go` if all 5 dimensions PASS and tests pass. `no-go` otherwise.

Write `tasks/<topic>-qa.md`:
```yaml
---
topic: <topic>
qa_result: <go|no-go>
git_head: <current short SHA>
producer: claude-opus-4-6
created_at: <ISO datetime in Pacific>
---
```

Below frontmatter, write the 5-dimension results as a checklist:
```
- [x] Test coverage: <reason>
- [x] Regression risk: <reason>
- [ ] Plan compliance: <reason for fail>
- [x] Negative tests: <reason>
- [x] Integration: <reason>

Tests: PASS (N passed) / FAIL (N failed)
```

#### Step 6: Handoff

If `go`:
- "QA passed. Run `/review` then `/ship`."

If `no-go`:
- List the failing dimensions with specific fix suggestions.
- "Fix these, then `/review --qa` again."

### Notes (QA)
- QA is a SOFT gate in `/ship` — advisory, not blocking. But a `no-go` is a strong signal.
- This checks domain-specific quality that automated tests can't catch (plan compliance, signature changes, integration).
- Don't re-run the full test suite if the user just ran it — check the output timestamp.

---

## Mode: Governance (`--governance`)

Governance hygiene scan: lessons, decisions, rules, cross-references, escalation ladder. Report findings with concrete recommendations. Defers to `/review` code review for code, `/ship` for deployment.

### Procedure

#### Step 1: Scan Lessons

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

##### Staleness Detection

For each active lesson, run these checks:

1. **STALE — review needed**: Lesson is >14 days old AND no commits in the last 14 days reference its ID. Check with: `git log --all --oneline --since="14 days ago" --grep="LNNN"` (replace NNN with the lesson number). If zero results, it is stale.

2. **CANDIDATE RESOLVED — verify fix shipped**: Lesson references a specific file path or hook. Check whether that file exists and its last modified date is AFTER the lesson's date. Use `stat -f %Sm -t %Y-%m-%d FILE` (BSD stat on macOS) to get the file's modification date. If the file was modified after the lesson was created, the fix may have shipped.

3. **ESCALATION NEEDED — promote to hook**: Lesson has a `Violations: N` tag (or equivalent recurrence metadata) where N >= 3, AND no hook currently enforces this pattern (check `hooks/` directory for related hook scripts). These lessons have failed at the advisory level and need structural enforcement.

**CRITICAL: Never auto-resolve or auto-archive.** Present findings only. The user directs all mutations.

##### Triage Output

Add a "Lessons Triage" subsection to the governance report:

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

#### Step 2: Scan Decisions

Read `tasks/decisions.md` and classify each decision:

| Classification | Criteria |
|---|---|
| **ARCHIVE** | Decision is explicitly superseded by a later decision ID. |
| **ARCHIVE [Requires Confirmation]** | Decision is heuristically flagged as stale (see below). Never auto-executed. |
| **KEEP** | Decision still appears load-bearing or is referenced by active governance files. |

**Staleness heuristic** — a decision is a candidate for confirmed archival if it meets ALL of:
- Its date metadata is older than 90 days
- No references to its ID appear in active lessons, rules, or other active decisions
- It is not part of an active supersession chain

Additional flags:
- Decisions with `NEEDS DECISION` or open status notes unresolved for >7 days -> flag as **overdue**.
- Decisions with version-only dates (e.g., `v3.5`) and no calendar date -> flag as **missing date metadata**.
- Decisions that are implicitly superseded (a later decision changes the same thing) but lack a formal `Superseded by:` tag -> flag as **implicit supersession**.

#### Step 3: Scan Rules

Read `.claude/rules/*.md` (not `reference/`) and check for:

- **Duplicate or overlapping guidance** across files (requires model judgment — flag as advisory)
- **Broken references** to lessons or decisions that no longer exist
- **Size pressure**: measure total rule size and compare against the 50KB limit
- **Escalation candidates**: rules that appear to be repeatedly violated, based on explicit recurrence metadata in `tasks/lessons.md`

#### Step 4: Cross-Reference Integrity

Check that:
- Every promoted lesson (`[PROMOTED -> rules/filename.md]`) has the corresponding rule file
- Every rule with an `Origin:` tag still points to an existing lesson or decision
- Supersession chains between decisions are valid (no dangling or circular references)
- No duplicate IDs exist across active and archived files

#### Step 5: Escalation Ladder Analysis

Review the full scan results and identify enforcement ladder opportunities:

- **Lessons violated 3+ times at the same level** -> recommend promotion to rule
- **Rules violated repeatedly** (per lesson metadata) -> recommend escalation to hook enforcement
- **Recurring patterns across multiple lessons** -> recommend a new slash command or architectural change
- **Three-strikes threshold**: if the same behavior has been corrected three times, flag for immediate escalation per the enforcement ladder (lesson -> rule -> hook -> architecture)

#### Step 6: Present Findings

Combine findings and recommendations into a single output. Don't list every KEEP item — only report items that need action or attention. Healthy items are noise.

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

End with: "Say **go** to apply all, or tell me which to skip."

### Rules (Governance)
- Report only — user directs all mutations. Never auto-resolve or auto-archive.
- Does not modify hook scripts, `settings.json`, or enforcement mechanisms.
- Does not rewrite rule content (only flags issues).
- Does not touch PRD, session log, or handoff documents.
- Does not rely on `git log` for recurrence or age detection (except staleness detection in Step 1, which uses `git log --grep`).

---

## Mode: All (`--all`)

Run all checks in sequence: code review -> QA -> governance.

1. Run the full code review procedure (Steps 0-8 above).
2. Run the QA procedure.
3. Run the governance procedure.
4. Aggregate into a single summary:

```
## /review --all Summary

| Check       | Verdict         | Blocking | Non-blocking |
|-------------|-----------------|----------|--------------|
| Code Review | pass/revise/deg | N        | N            |
| QA          | go/no-go        | N        | N            |
| Governance  | ok/issues       | N        | N            |

Overall: <pass|pass-with-warnings|fail>
Suggested next action: <what to do>
```

---

## When to Run Each Mode

| Situation | Recommended mode |
|---|---|
| Before `/ship` | `/review` (default code review) |
| Architectural change with spec | `/review` (auto-detects spec, enables compliance) |
| Want mechanical fixes applied | `/review --fix` |
| Want full fix cycle | `/review --fix-loop` |
| Low confidence in review | `/review --second-opinion` |
| Before first commit on a feature | `/review --qa` |
| Governance counts approaching limits | `/review --governance` |
| Pre-ship, want everything | `/review --all` |

## Cost

- **Code review (default):** Medium. 3 external model calls via debate.py + diff tokens.
- **Second opinion:** Low-medium. 1 external model call (or manual copy-paste).
- **QA:** Low. Local analysis + test suite run. No external model calls.
- **Governance:** Low-medium. Reading all governance files (~10K-30K tokens). No external model calls.
- **All:** Sum of above.
