---
debate_id: streamline-rules-tools-on
created: 2026-04-17T14:51:11-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# streamline-rules-tools-on — Challenger Reviews

## Challenger A (pm) — Challenges
## Challenges

1. [RISK] [MATERIAL] [COST:SMALL]: Cross-referencing degrades LLM instruction adherence. Replacing explicit rules with pointers ("See review-protocol.md") forces the LLM to either resolve references across a massive concatenated context window or pause to execute tool calls to read the referenced files. Both patterns empirically reduce instruction compliance compared to local, contextual repetition.

2. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal assumes all rule files are always loaded into the context window. If `.claude/rules/*.md` files are attached dynamically based on context/globs (a common pattern), moving core invariants out of the always-loaded `CLAUDE.md` means the agent will frequently operate without knowing those rules exist. 

3. [OVER-ENGINEERED] [ADVISORY]: Optimizing for [ESTIMATED] ~1,200 tokens (which costs fractions of a cent per run) by creating a complex web of cross-references trades a microscopic cost saving for a tangible risk of behavioral degradation.

## Concessions
1. Phase 1 (fixing the 4 concrete contradictions) is an excellent, necessary intervention that directly improves agent determinism.
2. Phase 3 (removing origin tags and verbose preambles) is a pure win, stripping noise without losing any normative signal.
3. The commitment to maintaining the exact same governance constraints rather than weakening enforcement is the correct product boundary.

## Verdict
REVISE: Approve the contradiction resolutions and verbosity tightening (Phases 1 & 3), but reject the Phase 2 cross-referencing strategy which will obfuscate instructions and degrade agent compliance.

---
