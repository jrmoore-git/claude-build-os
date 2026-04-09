---
name: review-x
description: Cross-model code review — get a second opinion from a different AI model
user-invocable: true
---

# Cross-Model Review

Get a second opinion on code changes from a different AI model family. Optional enhancement to `/review`.

## Prerequisites

A completed `/review` artifact must exist at `tasks/review-[topic].md` before running this skill.

## How it works

This skill generates a review prompt, sends it to a second model, and classifies where the two models agree or disagree. No API keys or infrastructure required — copy-paste works.

## Procedure

### Step 1: Load the primary review
Read `tasks/review-[topic].md` and the relevant diff (`git diff` or staged changes).

### Step 2: Generate the cross-model prompt
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

### Step 3: Get the second opinion

**Option A — Copy-paste (default, no infrastructure):**
Tell the user: "Paste this prompt into a different AI model and paste the response back here."

**Option B — Automated (if configured):**
If your project has a cross-review script (e.g., a shell wrapper around `curl` to OpenAI or Gemini), run it automatically. The script should accept the prompt on stdin and return the response on stdout. No script is required — Option A works for any project.

### Step 4: Classify findings

Read the second model's response and classify every finding:

- **Consensus**: both models flagged the same issue → **blocking by default**
- **Confirmed**: second model agrees with primary finding → no change to severity
- **Singleton (primary only)**: primary found it, second model didn't mention it → stays as-is
- **Singleton (secondary only)**: second model found something primary missed → **concern** (not auto-blocking)
- **Disputed**: models explicitly disagree on whether something is a problem → **requires human decision**

### Step 5: Write the artifact

Create `tasks/review-x-[topic].md`:

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

### Step 6: Present results

Show the user the merged findings. Highlight:
1. Any **consensus blocking** issues (highest confidence — fix these)
2. Any **new findings** from the second model (worth investigating)
3. Any **disputes** that need human judgment

## Rules
- This skill is optional. `/review` is complete without it.
- Only consensus findings auto-block. Singleton findings from the second model are concerns, not blockers — one model seeing something the other missed is signal, not proof.
- Disputed findings are never auto-resolved. Surface both positions and let the human decide.
- The cross-model prompt must be identical regardless of which model receives it. Same diff, same instructions, same expected format. Prompt normalization prevents noisy comparisons.
- **Anonymous labels only.** The cross-model prompt must not reveal which model performed the primary review. Use "primary reviewer" / "Reviewer A" / "Reviewer B" — never model names. This prevents anchoring bias (deference or hostility based on model identity). Model names appear only in the final artifact metadata, after classification is complete.
- Do not rubber-stamp the second model either. If its response is vague, generic, or doesn't engage with the actual diff, note that the cross-check was inconclusive.
