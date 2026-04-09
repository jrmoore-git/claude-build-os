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

### Step 5: Run cross-model review

Write the diff (and spec if exists) to a temp file, then run:
```bash
python3 scripts/debate.py challenge \
  --proposal <temp file with diff + spec context> \
  --personas architect,security,pm \
  --system-prompt "You are a code reviewer. Review this diff through your assigned lens. Tag each finding as [MATERIAL] (must fix) or [ADVISORY] (worth noting). Group findings by: PM/Acceptance, Security, Architecture. If a spec is included, check implementation against it for completeness and scope creep. Additionally, if a spec is included: extract all EXCEPTION, MUST NOT, and EXPLICITLY EXCLUDED clauses. For each such clause, verify the diff does not contain code that contradicts it. Tag violations as [MATERIAL] with prefix 'SPEC VIOLATION:'." \
  --output tasks/<topic>-review-debate.md
```

The `--system-prompt` override replaces the default adversarial challenge prompt with a review-specific prompt so models produce lens-attributed, severity-tagged findings.

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
