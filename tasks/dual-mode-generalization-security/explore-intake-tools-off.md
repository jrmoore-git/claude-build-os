---
debate_id: explore-intake-tools-off
created: 2026-04-17T14:50:44-0700
mapping:
  A: gpt-5.4
personas:
  A: security
---
# explore-intake-tools-off — Challenger Reviews

## Challenger A (security) — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposal adds a new translation layer from raw user answers into a structured context block, but it does not specify any trust-boundary handling for user-supplied content before that content is embedded into downstream prompts. If a user includes prompt-injection text in answers or uploaded documents (e.g. “ignore prior instructions,” “reveal system prompt,” “send this externally”), the composition step may faithfully preserve or elevate that malicious content into high-salience sections like PROBLEM, THE TENSION, or ASSUMPTIONS TO CHALLENGE. You need an explicit rule that intake content is untrusted data, must be quoted/summarized as data not instructions, and must not override system/developer directives in explore prompts.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: The proposal says “preserve the user's exact words for The Tension,” which is good for fidelity but increases injection risk because exact wording is given the most prominent semantic position. Add a guardrail: preserve wording only as attributed content, and sanitize/neutralize instruction-like text before insertion into prompt-control regions. This is a small prompt-spec fix, but without it the recommendation changes because the new design centralizes untrusted text in the most influential prompt slot.

3. [ASSUMPTION] [ADVISORY]: The proposal assumes `scripts/debate.py explore --help` is sufficient verification, but that command does not appear to exercise the security-sensitive path introduced here: composing arbitrary user answers/documents into prompts. Verification evidence is explicitly pending, so claims about safe behavior are currently unproven.

4. [ALTERNATIVE] [ADVISORY]: Consider adding a lightweight “prompt injection scrub” composition rule: detect and demote instruction-shaped substrings into a separate “USER-PROVIDED TEXT NOTES” or summarize them instead of verbatim carry-through. This would preserve the UX intent without relying solely on the model to distinguish data from instructions.

## Concessions
- The proposal explicitly avoids storing more data than needed in the context block and emphasizes compression, which reduces accidental data exposure surface.
- One-question-at-a-time and adaptive stopping reduce unnecessary collection of sensitive or extraneous user information.
- The design is otherwise sound from a security perspective: no new external calls, credential flows, or privilege boundaries are introduced in the proposal as written.

## Verdict
REVISE — strong interaction design, but the new context-composition layer needs explicit prompt-injection handling because it promotes untrusted user text into high-authority prompt regions.

---
