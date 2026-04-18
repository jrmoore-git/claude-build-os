---
study: debate-efficacy-study
topic: ground-truth methodology pivot
date: 2026-04-17
---

# Methodology Note — Ground Truth Pivot

## What we tried

The plan called for building a **pre-built ground truth checklist** — a list of 5–10 MATERIAL findings per proposal, derived from arm-independent sources (proposal text, git log, lessons, decisions, source files), to score arm C and arm D findings against.

## Why it didn't work as planned

Two Explore agents attempted this. Both contaminated the output despite explicit forbidden-sources lists:

- **v1** (`tasks/debate-efficacy-study-ground-truth.md`, 38 findings): ~18 findings cited `*-judgment.md` files directly. Unusable for the original purpose.
- **v2** (`tasks/debate-efficacy-study-ground-truth-v2.md`, 15 findings): 1 direct citation of `*-challenge.md` at line 45; several outcomes (shelved/rejected) derived implicitly from debate files. Cleaner than v1 but still not arm-independent.

The pattern: once a large context window loads session history, lessons, and decisions that themselves reference the debate system's verdicts, truly arm-independent evidence becomes a moving target. The agents didn't fail at following instructions — they ran into the methodological reality that *our own retrospective documents cite the debate output*, making clean separation hard.

## The pivot

Drop the upfront ground-truth checklist. Validate findings **on the fly at adjudication time** against first-principles evidence only.

The hardened judge prompt (F6) asks for each finding:

> Given finding X from an anonymous reviewer, verify against:
> - The proposal text itself (what is claimed?)
> - `git log --oneline` output around the proposal date
> - Actual source files referenced (exists? contents match claim?)
> - Nothing else.
>
> Return: VALID_IN_EVIDENCE (finding confirmed by allowed sources), UNVALIDATED (no evidence either way), INVALID (evidence contradicts finding), DUPLICATE_OF_N.

This is methodologically stronger than the original plan:

1. **No pre-built checklist** means no risk that the checklist itself is arm-biased.
2. **Per-finding evidence check** forces the judge to cite specific proposal lines, commits, or file states — not just match against a list.
3. **UNVALIDATED as a category** lets the study report precision honestly: the denominator of "VALID + INVALID" findings is the adjudicated set; UNVALIDATED are neither for nor against.

## Effect on decision matrix

The pre-registered decision matrix from `debate-efficacy-study-plan.md` still applies, with "MATERIAL findings" replaced by "VALID_IN_EVIDENCE findings" at adjudication time. Escalation rules unchanged.

## v1/v2 ground-truth files — reclassified

- v1 and v2 are no longer authoritative inputs to adjudication.
- They remain on disk as **lightweight outcome references** — useful for the final writeup to describe what each proposal's downstream fate was, but not part of the scoring pipeline.
- Final writeup will cite v2's outcomes (with appropriate caveats) when describing context, not when computing precision/recall.

## Cost impact

None. The adjudication step's API spend is the same (external Gemini judge × 5 proposals × ~2x findings per proposal = ~10–20 judge calls, ~$1–2 total). The work moved from upfront Explore-agent labor to adjudication-time judge inference. Net: study is cheaper and more rigorous.
