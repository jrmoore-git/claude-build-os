---
debate_id: explore-intake
created: 2026-04-11T10:55:38-0700
mapping:
  A: claude-opus-4-6
  B: gemini-3.1-pro
  C: gpt-5.4
---
# explore-intake — Challenger Reviews

## Challenger A — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL]:** The 200-500 token budget for the context block is stated as research-backed ("context rot research shows performance degrades with length"), but the cited evidence (Chroma Research, Lost in the Middle) addresses *total context window* degradation, not a specific 200-500 token optimum for a structured input block within a larger prompt. The actual explore prompt will contain the context block *plus* system instructions, divergence templates, and synthesis scaffolding — likely 3,000-10,000 tokens total. At that scale, whether the context block is 300 or 700 tokens is unlikely to be the binding constraint on quality. The 200-500 target is a reasonable heuristic for compression discipline, but it's **ESTIMATED** — not evidenced as a performance cliff. This matters because Recommendation 6's hard pass/fail criterion ("≤500 tokens") could cause a well-composed 550-token block to fail verification when it would produce better output than a 490-token block with lossy compression.

2. **RISK [MATERIAL]:** The classification rule is presented as deterministic ("decision rule, not a guideline"), but the classification itself is inherently subjective. What makes an input "well-specified" vs. "moderate"? The example for well-specified ("Should we use Postgres or DynamoDB for our 10M-row analytics workload with JSON support?") is clear, but real inputs will cluster at tier boundaries. An LLM classifying "How should we handle auth for our new microservices?" could reasonably land in well-specified or moderate. The document treats classification as solved but only specifies it by example. This is the same trust-detection problem Round 3 flagged for Slot 4 — now elevated to the routing layer. A misclassification at this stage cascades: too few questions on an ambiguous input produces a weak context block; too many on a clear input triggers user frustration.

3. **UNDER-ENGINEERED [MATERIAL]:** The proposal has no feedback mechanism. After the explore output is generated, there's no way to learn whether the intake produced good directions. Recommendation 6 proposes a one-time verification with 3 test prompts, but there's no ongoing signal. Without instrumentation (e.g., did the user engage with all 3 directions? Did they immediately re-run with different framing?), the system can't self-correct. The classification thresholds, slot selection heuristics, and token budget are all tunable parameters presented as fixed rules — but they were derived from external research, not from this system's actual usage. The risk of NOT having feedback: the team ships v6, declares victory based on 3 test runs, and never learns whether the 30/60-word engagement thresholds or the 4-tier classification actually work in practice.

4. **RISK [ADVISORY]:** The Slot 4 engagement-based selection heuristic (under 30 words → soft frame, over 60 words → direct challenge, 30-60 words → default to frame unless emotional language) is a reasonable starting point, but "emotional language" detection by an LLM is unreliable and culturally variable. A user writing "this is a disaster" in a technical context may be using hyperbole, not expressing emotion. The fallback ("when in doubt, default to frame-and-correct") is the right safety valve, but the 30/60-word thresholds are **SPECULATIVE** — no cited source supports these specific numbers.

5. **ALTERNATIVE [ADVISORY]:** The proposal eliminates `preflight-tracks.md` entirely in favor of a universal sequence with domain variation through slot phrasing. This is architecturally cleaner, but it discards the ability to encode domain-specific knowledge (e.g., "for technical architecture questions, always ask about scale requirements; for organizational questions, always ask about stakeholder alignment"). The slot adaptation rules partially cover this, but they rely on the LLM's in-context judgment rather than explicit domain heuristics. If certain domains consistently produce weak context blocks, the fix under v6 is to tune slot phrasing in a single file — which is simpler but also means domain-specific improvements compete for space in one prompt rather than being isolated.

6. **OVER-ENGINEERED [ADVISORY]:** The 10-item failure modes list is thorough but several items (Socratic Fatigue, Confirmation Drift) are defended by rules already specified in the protocol. Listing them as failure modes is fine for documentation, but the document spends ~200 words on failure modes that are already structurally prevented by the design. This is a minor length concern, not a design flaw.

7. **ASSUMPTION [ADVISORY]:** The proposal assumes the confirmation checkpoint adds value without adding friction. The cited products (OpenAI Deep Research, Perplexity) use confirmation, but those products have longer generation times (minutes) that justify a pause. For explore mode, if generation takes 10-30 seconds, the checkpoint adds a mandatory round-trip that most users will rubber-stamp. The "maximum one revision pass" rule mitigates runaway confirmation, but the base case — user says "looks good" — is pure friction. The document doesn't consider making the checkpoint optional or skippable.

## Concessions

1. **The 5-slot sequence with fixed purposes is a genuine improvement over a free-form question bank.** It gives the system a predictable structure while preserving adaptability through skip rules. The slot purposes (broad opener → reflection → constraints → assumption challenge → meta-question) follow a well-supported funnel pattern.

2. **The composition rules and context block template are the strongest part of the proposal.** Separating facts, constraints, tension, and assumptions into distinct sections — with explicit handling of unknowns — directly addresses the "compose, don't concatenate" principle. The mapping table to explore prompts makes the data flow traceable.

3. **The mandatory reflection-before-asking rule is a high-leverage intervention.** It structurally prevents the interrogation failure mode and is well-supported by the MI research base. This single rule likely does more for intake quality than the rest of the protocol combined.

## Verdict

**REVISE**: The design is architecturally sound and well-researched, but the deterministic framing of inherently fuzzy decisions (classification tiers, word-count thresholds, token budget as hard pass/fail) creates brittleness that the proposal's own evidence base doesn't support — add classification guidance beyond examples, soften the 500-token criterion to a target with a stated tolerance, and define a lightweight feedback mechanism for post-ship learning.

---

## Challenger B — Challenges
## Challenges

1. [RISK] [MATERIAL]: **LLM state tracking across turns.** The proposal relies on `preflight-adaptive.md` and `SKILL.md` (both prompts) to enforce a rigid 5-slot sequence across multiple conversational turns. Pure LLM prompting is notoriously bad at acting as a strict state machine across a chat history; it is highly likely to skip slots, repeat slots, or hallucinate which slot it is currently executing unless the underlying Python backend (`scripts/debate.py`) actually tracks the state and injects the current slot instruction into the system prompt per turn.
2. [RISK] [MATERIAL]: **Broken rollback path.** The document states the rollback path is: "Revert preflight-adaptive.md to v5, remove preflight-tracks.md". However, Recommendation 2 states: "Delete config/prompts/preflight-tracks.md". If the rollout deletes the file, the rollback must *restore* it, not remove it. Reverting to v5 without restoring the tracks file will likely break the system.
3. [RISK] [ADVISORY]: **Latency vs. Typeform data mismatch.** The proposal cites Typeform's 3.5x completion rate [EVIDENCED] to justify one-at-a-time questioning. However, Typeform transitions between questions with zero latency. Asking 4-5 questions sequentially via an LLM requires 4-5 full round-trip inference cycles. This introduces significant latency before the user even reaches the actual "explore" phase, which risks high drop-off.
4. [ASSUMPTIONS] [ADVISORY]: **Context block token budget.** Enforcing a strict 200-500 token limit [ESTIMATED] on the composed context block via prompt instructions is fragile. LLMs struggle with strict token-counting constraints. If the LLM generates 550 tokens, does the system hard-truncate it (breaking the YAML/Markdown structure) or just let it pass?

## Concessions
1. The integration of clinical and coaching conversational frameworks (Motivational Interviewing, Clean Language) to bypass the LLM "Righting Reflex" is an exceptionally strong, well-evidenced design choice.
2. The classification table provides a deterministic, testable mechanism to prevent over-asking on well-specified prompts.
3. The end-to-end verification plan is highly actionable and defines specific, verifiable structural divergence for the final output.

## Verdict
**REVISE** to correct the broken rollback path and specify whether the 5-slot state machine is enforced by the backend code or if it relies solely (and dangerously) on the LLM's conversational memory.

---

## Challenger C — Challenges
## Challenges
1. [RISK] [MATERIAL]: The proposal adds a new data flow from raw user input into multiple prompt files (`preflight-adaptive.md`, `SKILL.md`, and `explore-diverge.md`) but does not define any trust-boundary handling for untrusted user text. In particular, `ASSUMPTIONS TO CHALLENGE` is explicitly inferred from user input and then fed into Direction 3; without delimiting/quoting rules, a user can inject prompt-like instructions ("ignore prior directions", "reveal hidden rules", "send this externally") into the composed context block and have them promoted into higher-salience system context. This is a classic prompt-injection risk introduced by the change and should be mitigated with strict serialization/labeling of user-derived fields as data, plus rules forbidding execution of instructions found inside intake content.

2. [UNDER-ENGINEERED] [MATERIAL]: The document specifies rich composition rules but no redaction policy for sensitive data before storing, echoing, or passing user content through confirmation and explore phases. The intake explicitly solicits political, organizational, emotional, and constraint details, which raises the chance of collecting secrets, internal names, dates, budgets, or incident details. There is no guidance on masking credentials, access tokens, customer data, or regulated data in the context block or logs (`scripts/debate.py` is listed as an affected surface). This is a material data-exfiltration and privacy gap.

3. [ASSUMPTION] [MATERIAL]: The proposal assumes the confirmation checkpoint is safe to display verbatim back to the user, but does not verify whether the composed summary could expose inferred assumptions the user did not intend to make explicit in a shared/screened environment. Because the design intentionally surfaces "what's unsaid" and political dimensions, reflecting those back can leak sensitive inferences to logs, transcripts, or collaborators. If explore sessions are persisted or visible to other users/operators, this changes the risk profile and needs an explicit handling rule.

4. [UNDER-ENGINEERED] [ADVISORY]: `Delete preflight-tracks.md` reduces complexity, but it also removes a natural place to encode domain-specific safety constraints. "Universal sequence" is fine for questioning structure, yet some domains may need tailored prohibitions (e.g., not soliciting secrets for security incidents, not eliciting personal health details unnecessarily). If those guardrails are removed with the track file, they should be relocated rather than lost.

5. [ALTERNATIVE] [ADVISORY]: Consider adding a minimal "sensitive-input detector" before Slot 4 or before composition. The proposal already classifies clarity; a parallel lightweight classification for secrets/regulated content would let the system avoid probing for more detail and instead ask for sanitized descriptions. This is a simpler control than trying to redact after the fact.

## Concessions
- The proposal is strong on controlling premature solutioning and limiting free-form behavior; that reduces some classes of unintended model action.
- The one-question-at-a-time structure and explicit skip behavior improve predictability over an unstructured adaptive bank.
- The document is unusually concrete about affected files, rollback, and verification, which is good change hygiene.

## Verdict
REVISE — strong design work, but the change materially increases prompt-injection and sensitive-data handling risk unless user-derived context is explicitly treated as untrusted data with redaction and serialization rules.

---
