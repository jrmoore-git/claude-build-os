---
debate_id: streamline-rules-tools-off
created: 2026-04-17T14:51:06-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# streamline-rules-tools-off — Challenger Reviews

## Challenger A (pm) — Challenges
## Challenges

1. [ASSUMPTION] [MATERIAL] [COST: SMALL]: The proposal assumes that deduplicating rules via cross-references ("See `code-quality.md`") improves LLM compliance. In prompt engineering, repetition of critical invariants often *increases* attention and compliance. Furthermore, if these files are concatenated into the context window, indirection fragments the LLM's attention. If they are *not* automatically concatenated, forcing the LLM to use a `read_file` tool to retrieve a rule guarantees it will occasionally skip reading it to save time, resulting in dropped rules. 
*Quantitative Claim Check:* The claim that compliance decreases with instruction count is SPECULATIVE in the context of replacing duplicated rules with cross-file pointers. 

2. [OVER-ENGINEERED] [ADVISORY]: Phase 3 trims human-readable preambles and sentences to save an ESTIMATED ~375 tokens. On modern LLMs (e.g., Claude 3.5 Sonnet), 375 input tokens cost roughly $0.001. Hyper-compressing rules into robotic shorthand degrades human maintainability and readability for zero measurable performance or cost benefit.

## Concessions
1. Phase 1 (Fixing Ambiguity) is highly valuable. Contradictions actively confuse deterministic state machines and LLMs alike. Aligning "before vs after" and skip conditions is a clear win.
2. Designating a "canonical" file for each concept is good practice for human maintainers updating the rules, even if the LLM prompt compiler ultimately duplicates the text.
3. Removing `*Origin: ...*` tags (Phase 3A) is a sensible cleanup of context-free noise.

## Verdict
REVISE: Approve Phase 1 (resolving contradictions) and Phase 3A, but abandon Phase 2's strategy of replacing duplicated LLM rules with cross-file references, as indirection degrades LLM adherence more than repetition does.

---
