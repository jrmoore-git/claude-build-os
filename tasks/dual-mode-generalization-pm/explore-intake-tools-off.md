---
debate_id: explore-intake-tools-off
created: 2026-04-17T14:51:00-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# explore-intake-tools-off — Challenger Reviews

## Challenger A (pm) — Challenges
## Challenges

1. [ASSUMPTION] [MATERIAL] [COST: MEDIUM]: Prompt-driven state machines degrade in practice.
The proposal assumes an LLM can strictly navigate a 5-slot sequence (Opening → Reflection → Constraints → Assumption → Meta) purely via a system prompt without external state tracking. Research on LLM instruction following shows models frequently skip steps or blend slots when managing multi-turn conversational state internally. 
*Risk of proposed change:* The model attempts to ask questions from Slot 2, 3, and 4 in a single turn because it loses its place, violating the "One question at a time" rule.
*Risk of status quo:* The current free-form bank lacks progression entirely.
*Fix:* The `preflight-adaptive.md` prompt must instruct the model to explicitly (and invisibly, via XML tags) output its current conversational state/slot before generating the user-facing response.

2. [RISK] [ADVISORY]: "Robotic empathy" via forced reflections.
Applying the MI "2:1 reflection-to-question ratio" via LLM prompting risks generating highly repetitive, formulaic dialogue. If every AI response begins with "It sounds like you're saying [X]..." or "You mentioned [Y]...", the UX will quickly feel like a therapy bot rather than an expert thought partner. The prompt must explicitly constrain reflections to be brief, synthesizing, and varied in phrasing.

3. [UNDER-ENGINEERED] [ADVISORY]: Unenforceable token targets.
The proposal sets a "[ESTIMATED] 200-500 tokens" target for the context block composition. LLMs cannot count tokens and are notoriously bad at adhering to strict length constraints. The prompt should instead use structural constraints (e.g., "Maximum 3 bullet points per section," "Maximum 2 sentences for the Tension") to enforce the desired compression ratio.

## Concessions
1. Removing user-selected "tracks" in favor of system-inferred domains dramatically reduces adoption friction. Users don't know what track they need until they've answered questions.
2. The "Adaptive Question Count" matrix perfectly right-sizes the friction, solving the universal complaint of AI forcing 5 questions on an already well-specified prompt.
3. Separating "Constraints" (negative) from "Situation" (positive) in the context block is a highly sophisticated, empirically backed way to prevent LLMs from hallucinating outside the user's bounds.

## Verdict
APPROVE

The proposal is exceptionally well-researched, replaces a rigid/unvalidated v5 flow with an evidence-based adaptive sequence, and the implementation requires only prompt/documentation changes.

---
