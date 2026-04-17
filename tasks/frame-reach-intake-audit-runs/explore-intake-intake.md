---
debate_id: explore-intake-intake
created: 2026-04-17T16:17:13-0700
mapping:
  A: claude-sonnet-4-6
  B: gpt-5.4
personas:
  A: frame-structural
  B: frame-factual
---
# explore-intake-intake — Challenger Reviews

## Challenger A (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:MEDIUM]**: The proposal assumes the primary failure mode is *question design* — that better intake questions will produce meaningfully different explore outputs. This is unverified. The actual failure chain is: intake questions → user answers → context block composition → LLM direction generation. The proposal has no evidence that the current system's weak link is question design rather than context block composition or the downstream explore prompts themselves. A poorly composed context block from good answers is equally broken. The proposal treats these as coupled but only redesigns the intake side in detail; the composition rules are described but not validated against actual explore output quality. If the bottleneck is actually in `explore-diverge.md` or `explore-synthesis.md` (not mentioned in the manifest), the entire intake redesign is solving the wrong problem.
   - SPECULATIVE: No data on where current explore outputs actually fail (too similar? wrong domain? missing constraints?).

2. **ASSUMPTION [MATERIAL] [COST:SMALL]**: The proposal treats "50+ sources, 8 questioning domains, 15+ AI products" as evidence for the *specific slot sequence design*, but the research findings are about general questioning principles, not about AI-assisted explore intake specifically. The 2:1 reflection ratio is from Motivational Interviewing (behavior change counseling). The Mom Test is for customer discovery interviews. The FBI elicitation technique is for interrogation. These are being imported wholesale into a context (LLM-mediated async text intake for open-ended exploration) that differs on every dimension: no real-time adaptation, no vocal cues, no relationship, no stakes. The proposal acknowledges the Righting Reflex is an LLM-specific problem but doesn't acknowledge that most of its source material is human-to-human and may not transfer.

3. **ALTERNATIVE [MATERIAL] [COST:SMALL]**: A missing candidate is **post-hoc intake** — run explore with the stated question, then ask 2-3 targeted questions based on what the initial directions reveal. This is how Perplexity's follow-up and OpenAI Deep Research's refinement actually work in practice. The proposal cites these products but adopts only their pre-flight pattern, not their iterative refinement pattern. Post-hoc intake has a key advantage: the user sees concrete directions first, which dramatically improves their ability to articulate what's wrong or missing. The proposal's own research notes "people correct wrong framings more readily than they generate accurate ones" — this applies equally to showing draft directions as to offering a tentative frame. This alternative is not evaluated.

4. **ALTERNATIVE [MATERIAL] [COST:TRIVIAL]**: A missing candidate is **structured form intake** — a short, fixed 3-question form (goal, constraints, what-you've-tried) presented simultaneously rather than sequentially. The proposal cites Typeform's 3.5x completion rate for one-at-a-time delivery, but Typeform is a *consumer* product with cold users. The explore skill's users are developers/practitioners who have already invoked `/explore` — they are warm, motivated, and familiar with the tool. The completion-rate argument may not apply. A structured form would be faster, more predictable, and easier to compose into a context block. This is not evaluated as a candidate.

5. **OVER-ENGINEERED [MATERIAL] [COST:MEDIUM]**: The 5-slot adaptive sequence with per-slot adaptation rules, delivery rules, composition rules, and a mapping table is being specified as a *prompt document* (`preflight-adaptive.md`) that an LLM must follow during a live conversation. This is a significant amount of behavioral specification being loaded into a system prompt. The proposal has no evidence that the current LLM (Claude) reliably follows 8 delivery rules + 5 slot adaptation rules + 7 composition rules simultaneously without degradation. The "Righting Reflex" defense is a structural rule in the protocol — but the protocol is itself a prompt, and the Righting Reflex is an RLHF-level bias. A prompt rule cannot reliably override a training-level bias. The proposal cites Google Research 2025 on this exact problem but then proposes a prompt-level solution to it.

6. **ASSUMPTION [ADVISORY]**: The 200-500 token target for the context block is presented as research-backed ("context rot research"), but the cited mechanism (performance degrades with length) applies to *retrieval* tasks where the relevant content is buried in long context. Explore's context block is not a retrieval task — it's a generation task where the model uses the full context block as a seed. The "lost in the middle" finding (U-shaped attention) applies when the relevant content is in the middle of a long document, not when the entire document is the relevant content. The token target may be correct but the research basis is misapplied.
   - SPECULATIVE: No data on how explore output quality varies with context block length in this specific system.

7. **ASSUMPTION [ADVISORY]**: The proposal frames the current v5 as having "no structured sequence, no composition rules for the context block, and no evidence base for question selection." This is stated as fact but the proposal author wrote v5 (implied by "Revert preflight-adaptive.md to v5" in rollback). The framing inflates the gap between v5 and v6 to justify the scope. The actual delta — adding reflection ratio, slot sequence, meta-question, composition rules — may be a SMALL upgrade to v5 rather than a redesign. This doesn't change the direction but affects scope justification.

8. **UNDER-ENGINEERED [ADVISORY]**: The proposal specifies no evaluation criteria for whether v6 is better than v5. The verification command is `python3.11 scripts/debate.py explore --help` — this only verifies the CLI exists, not that the intake produces better context blocks or better explore outputs. "Test end-to-end with a real /explore run" is the entire test plan. For a proposal citing 50+ sources and claiming specific effect sizes (OR=1.55, 3.5x completion, Cohen's d > 0.8), the absence of any measurable success criterion is a significant gap.

---

## Concessions

1. **The research synthesis is genuinely useful.** The identification of the Righting Reflex as an LLM-specific failure mode, the 2:1 reflection ratio as a structural defense against interrogation, and the "offer a frame and invite correction" technique are all actionable and non-obvious. Even if the full slot architecture is over-specified, these three findings alone justify updating v5.

2. **The context block composition rules are the strongest part of the proposal.** The separation of CONSTRAINTS from SITUATION, the TENSION as the anchor, and the ASSUMPTIONS TO CHALLENGE section feeding Direction 3 are concrete, testable, and address a real gap (current context blocks are likely concatenation, not composition). This section could be implemented independently of the intake redesign.

3. **Replacing the 5-track fixed system with adaptive slots is the right direction.** The argument against fixed tracks (classification burden, inability to adapt to prior answers) is sound and well-supported. The slot-based approach is more flexible without being unconstrained.

---

## Verdict

**REVISE** — The proposal's frame conflates two separable problems (intake question design and context block composition) and proposes a single large redesign when the composition rules could be implemented immediately and the intake protocol could be validated incrementally. The missing candidates (post-hoc intake, structured form) are not evaluated, and the core assumption — that question design is the bottleneck — is unverified. Recommend splitting into: (1) implement context block composition rules now (high confidence, low risk), (2) add the three highest-signal intake changes to v5 (reflection ratio, adaptive count, meta-question) as a v5.1, and (3) validate before committing to the full 5-slot architecture.

---

## Challenger B (frame-factual) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal’s implementation plan targets files that do not appear to be part of the current shipped explore path. It proposes rewriting `config/prompts/preflight-adaptive.md`, removing `config/prompts/preflight-tracks.md`, and updating `.claude/skills/explore/SKILL.md`, but the current `cmd_explore` implementation loads only `explore.md`, `explore-diverge.md`, and `explore-synthesis.md` via `_load_prompt(...)` in `scripts/debate_explore.py:84-87`; searches for `preflight-adaptive.md` and `preflight-tracks.md` in repo code/docs returned no matches. As written, the proposal would not change runtime behavior unless it also adds/updates the actual loading/invocation path for intake.  
   Evidence: `scripts/debate_explore.py:84-87`; `check_code_presence("preflight-adaptive.md") -> 0 matches`; `check_code_presence("preflight-tracks.md") -> 0 matches`.

2. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal treats `scripts/debate.py` as the surface to change for explore behavior, but `cmd_explore` has already been extracted into `scripts/debate_explore.py`; `scripts/debate.py` now only re-exports it (`from debate_explore import cmd_explore`). A change plan centered on `scripts/debate.py` risks editing the wrong file and missing the live implementation.  
   Evidence: `scripts/debate.py:3337`; `scripts/debate_explore.py:16-19`; recent commit `6bbde96` (“extract cmd_explore to scripts/debate_explore.py”).

3. [UNDER-ENGINEERED] [MATERIAL] [COST:MEDIUM]: The proposal recommends “test end-to-end with a real /explore run,” but the live explore module currently has no direct test file mapped to it (`check_test_coverage` reports none), even though behavior is exercised indirectly through `tests/test_debate_commands.py`. A redesign that adds adaptive intake/composition logic should include explicit tests for the new parsing/composition rules in `scripts/debate_explore.py`; otherwise the risk of prompt-format drift and context parsing regressions remains high.  
   Evidence: `check_test_coverage("scripts/debate_explore.py") -> has_test: false`; current parsing logic is in `scripts/debate_explore.py:40-78`.

4. [ALTERNATIVE] [ADVISORY]: The proposal frames context composition as largely missing, but the current implementation already supports a structured pre-flight channel: it parses `DIMENSIONS:` and `PRE-FLIGHT CONTEXT:` / `CONTEXT:` from `--context`, builds a dimensions block, and injects both context and dimensions into the prompts. That means an incremental path exists: extend the current structured context grammar (e.g. add `ASSUMPTIONS TO CHALLENGE:`) instead of introducing a separate preflight file/protocol that is not yet wired into runtime.  
   Evidence: `scripts/debate_explore.py:40-78`, `89-92`, `119-123`, `149`.

## Concessions
- The proposal is directionally right that the current shipped explore path lacks explicit support for an `ASSUMPTIONS TO CHALLENGE` section; code search found no such handling.
- It is also right that context composition is fairly lightweight today: current code mainly splits `DIMENSIONS:` from narrative context rather than performing the richer translation/compression the proposal describes.
- The motivation to improve divergence quality is consistent with the implementation: current prompts explicitly try to force “fundamentally different” directions.

## Verdict
REVISE — the design may be useful, but the proposal is materially stale about which files drive explore today and omits the actual runtime wiring/testing needed for the redesign to take effect.

---
