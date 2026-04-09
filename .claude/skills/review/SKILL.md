---
name: review
description: "Staff engineer reviewing for production bugs. Three lenses (PM, Security, Architecture) review your diff independently."
user-invocable: true
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

# /review — Cross-Model Code Review

Three models review your diff through independent lenses. If a debate spec exists, PM lens escalates to strict spec compliance.

## Procedure

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
python3.11 scripts/debate.py challenge \
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

- **Any MATERIAL findings** → `status: revise`. Tell user: "N material findings. Address them, then `/review` again."
- **No MATERIAL findings** → `status: passed`. Tell user: "Review passed. Run `/ship` when ready."
- **LiteLLM down** → `status: degraded`. Tell user: "Cross-model review unavailable. Single-model review completed with degraded status. `/ship` will note the degraded status but won't block."

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
python3.11 scripts/pipeline_manifest.py add <topic> --skill review --artifact tasks/<topic>-review.md --status complete
```

## Important Notes

- No tier classification. No debate orchestration. Just "three models look at your diff from three angles."
- If `tasks/<topic>-refined.md` exists, the PM lens automatically checks spec compliance. This is the key linkage: `/debate` produces a spec, `/review` enforces it.
- Degraded mode is advisory, not blocking. `/ship` will note it.
- Re-running `/review` overwrites the previous review artifact.

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
3. Apply all AUTO-FIX items, outputting: `[AUTO-FIXED] [file:line] Problem → fix applied`
4. Output all ASK items as a numbered markdown list with per-item recommendations BEFORE calling AskUserQuestion. Example: "1. [Issue] — Recommendation: [fix approach]\n2. [Issue] — Recommendation: [fix approach]"
5. Batch into a single AskUserQuestion with numbered options
6. If AskUserQuestion returns empty: re-prompt once with the same list. If still empty: pause fix mode — "Pausing fix mode. ASK items logged in the review file for later."
7. Apply fixes for items the user approves

Without `--fix`, review remains read-only — findings are reported but no code is modified.

## Fix-Loop Mode (opt-in: `--fix-loop`)

When the user runs `/review --fix-loop` or `/review <topic> --fix-loop`, enable an automated fix → re-review cycle:

### Procedure

1. Run the standard review (Steps 1-8).
2. If **no MATERIAL findings** → stop. Review passed on first iteration.
3. If MATERIAL findings exist, start the fix-loop:
   a. Apply AUTO-FIX items (same heuristic as `--fix` mode above).
   b. Present ASK items to the user. Apply approved fixes.
   c. Re-run Steps 3-8 (get a fresh diff from the updated code, run cross-model review again).
   d. Increment the iteration counter.
4. **Termination bounds (HARD RULE — max 3 iterations):**
   - If iteration 3 still has MATERIAL findings → **stop and escalate**: "3 review iterations complete. N material findings remain. Manual review required." Write remaining findings to the review artifact.
   - If any iteration produces 0 MATERIAL findings → **stop with passed status**.
   - If the user declines all ASK items in an iteration (no fixes applied) → **stop**: "No fixes applied — loop would not progress. N material findings remain."
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
