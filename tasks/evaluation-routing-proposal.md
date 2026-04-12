---
topic: evaluation-routing
created: 2026-04-11
---
# Content-Aware Evaluation Routing

## Problem
The system repeatedly mismatches evaluation approach to content type. Code-review personas (architect/security/pm) are used for non-code evaluation (protocol documents, strategy docs, design specs) because the only multi-model parallel tool (`review-panel`) requires persona names, and those names evoke code-review framing even though they're just model selectors.

This has happened 3+ times in a single sprint. An advisory lesson (L21) was written and violated within one turn. Behavioral fixes don't survive execution pressure.

### Current System Failures
1. 2026-04-11: Called `review-panel --personas architect,staff,pm` to evaluate explore intake protocol. User caught it, corrected.
2. 2026-04-11: Wrote L21 about the problem, then immediately used `--personas architect,staff,pm` again on the next command.
3. Prior sessions: same pattern with strategy documents routed through code-review personas (undocumented but recurring).

### Operational Context
`review-panel` is called 5-10 times per week. Roughly half of those calls evaluate non-code content (design docs, protocols, strategy). The persona system prompts (PERSONA_PROMPTS dict in debate.py) are adversarial code-review prompts that add no value for document evaluation.

### Baseline Performance
- Current: caller must remember to match personas to content type. No enforcement. Failure rate: ~50% on non-code content.
- review-panel `--prompt`/`--prompt-file` already serves as the system prompt (verified line 2889). Personas only route to models — they don't inject PERSONA_PROMPTS in review-panel (only in `challenge`).

## Proposed Approach
Two changes:

1. **Add `--models` to `review-panel`** — mutually exclusive with `--personas`. Accepts comma-separated LiteLLM model names directly. No persona lookup, no misleading names. The caller's `--prompt`/`--prompt-file` is the only system prompt.

2. **Update `/review` skill content-type routing (D15)** — code diffs route to `review-panel --personas` (persona framing appropriate). Non-code documents route to `review-panel --models` with a content-appropriate evaluation prompt. The routing decision moves from the caller's head into the skill.

Non-goals:
- Not adding new persona types for documents (over-engineering — the eval prompt IS the framing)
- Not adding content-type detection to debate.py itself (wrong layer — the skill knows what it's reviewing)
- Not changing how `/challenge` uses personas (challenge personas ARE appropriate — they're adversarial reviewers, not code reviewers)

## Simplest Version
Add `--models` arg to review-panel subparser. When used, skip persona lookup and map model strings directly. Test: `debate.py review-panel --models claude-opus-4-6,gemini-3.1-pro,gpt-5.4 --prompt "Evaluate this document" --input doc.md` runs 3 models with the eval prompt as system prompt and no persona framing.
