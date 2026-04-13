---
debate_id: litellm-fallback
created: 2026-04-12T20:47:30-0700
mapping:
  Judge: gpt-5.4
  A: claude-opus-4-6
  B: gemini-3.1-pro
  C: gpt-5.4
---
# litellm-fallback — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gemini-3.1-pro', 'C': 'gpt-5.4'}
Consolidation: 25 raw → 14 unique findings (from 3 challengers, via claude-sonnet-4-6 via local)

## Judgment

### Challenge 1: Anthropic API key availability is unverified and likely absent
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.96
- Rationale: This is a real flaw in the proposal’s core assumption. The proposal’s fallback depends on `ANTHROPIC_API_KEY`, but tool-verified evidence shows the codebase does not currently reference that key and only loads `LITELLM_MASTER_KEY`; if Claude Code auth is OAuth-only, the fallback may fail for exactly the onboarding users it aims to help.
- Evidence Grade: A (tool-verified via code search and env-loading verification)
- Required change: The proposal must define a concrete credential strategy before proceeding: either require and document `ANTHROPIC_API_KEY` explicitly, detect and message its absence clearly, or choose a fallback transport/provider that can actually use credentials available in the target environment.

### Challenge 2: Custom Anthropic HTTP client introduces an unnecessary third calling convention
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.86
- Rationale: The proposal’s specific implementation choice is under-justified. Tool-verified evidence confirms `llm_client.py` already has two transport paths; adding a third protocol shape and auth/error/usage mapping increases maintenance burden, and the proposal does not explain why reuse of an existing abstraction is infeasible.
- Evidence Grade: A (tool-verified existing dual call paths; alternative feasibility is reasoned but credible)
- Required change: Revise the implementation plan to reuse an existing client abstraction where possible, or explicitly justify why a separate Anthropic Messages API path is necessary. The preferred revision is to minimize new transport conventions in `llm_client.py`.

### Challenge 3: Fallback trigger interacts badly with existing retry loop
- Challenger: A/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.93
- Rationale: This is a concrete behavioral gap. Tool-verified evidence shows network-class failures are retried with exponential backoff, and the proposal’s “fallback on first LLM call failure” does not specify bypassing or narrowing that logic, so users may sit through retries before fallback or trigger fallback on the wrong class of failure.
- Evidence Grade: A (tool-verified retry classification and loop behavior)
- Required change: Specify exact fallback conditions and where they are evaluated. The design should distinguish hard local LiteLLM unavailability (e.g. connection refused to localhost proxy) from transient upstream/network failures, and should avoid full retry-backoff before entering fallback mode.

### Challenge 4: Bypass location for persona/model routing is unspecified, risking incorrect audit metadata
- Challenger: A/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Rationale: The proposal promises identical artifact structure but does not resolve how requested persona models vs actual fallback model will be represented. Tool-verified evidence confirms artifacts include `model: {model}`, so a silent client-side substitution could misstate provenance and mislead governance consumers.
- Evidence Grade: A (tool-verified artifact model field; routing ambiguity is directly tied to proposal text)
- Required change: The proposal must specify the bypass point and how actual model provenance is recorded. At minimum, artifact/frontmatter and any logs must reflect fallback mode and the actual model used, not the original persona-mapped model names.

### Challenge 5: Command-level gating in `debate.py` is not addressed
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.88
- Rationale: This challenge is valid. Tool-verified evidence shows there are preflight errors for missing `LITELLM_MASTER_KEY`; if commands fail before reaching `llm_client.py`, a transport-only fallback cannot satisfy the proposal’s stated command coverage.
- Evidence Grade: A (tool-verified presence of preflight key checks, with partial function-location verification)
- Required change: Update the proposal to include entrypoint-level gating changes in `debate.py` for all commands intended to support fallback, not just transport changes in `llm_client.py`.

### Challenge 6: Judge independence is silently violated without warning
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.79
- Rationale: The concern is real because the proposal explicitly collapses multiple roles onto one model, and tool-verified evidence shows the codebase already treats judge/author overlap as meaningful. Since independence is part of the review pipeline’s trust model, silently weakening it should not happen without an explicit warning or metadata downgrade.
- Evidence Grade: A (tool-verified existing independence-check logic)
- Required change: The proposal must define fallback behavior for `judge` explicitly: emit a stronger warning and record reduced independence in metadata, or constrain/disable judge semantics in fallback mode.

### Challenge 7: Rate limits and concurrency under single-key fallback are not addressed
- Challenger: B
- Materiality: MATERIAL
- Decision: DISMISS
- Confidence: 0.62
- Rationale: The latency/rate-limit tradeoff is worth noting, but the proposal already states sequential execution in fallback mode, which is a reasonable mitigation for concurrency-driven 429 risk. The specific claim about likely Anthropic Tier 1 rate-limit failures is not tool-verified here, so it is not strong enough to require proposal changes on its own.
- Evidence Grade: C (concurrency is tool-verified; rate-limit severity is not)
- Required change: None

### Challenge 8: `single_review_default` config contradicts Anthropic-only fallback
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.75
- Rationale: Not judged materially. It is a reasonable design consistency note, but the proposal can intentionally choose a different fallback source than `single_review_default` if that config serves a different purpose.
- Evidence Grade: A (tool-verified config value)

### Challenge 9: Artifact metadata does not record fallback mode
- Challenger: A/C
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.82
- Rationale: This is a good advisory, but the material part of the provenance problem is already captured in Challenge 4. As a standalone challenge, it does not add a separate blocking flaw beyond the accepted requirement to record actual model provenance/fallback mode.
- Evidence Grade: A (tool-verified artifact model field)

### Challenge 10: No test plan for fallback logic
- Challenger: C
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.84
- Rationale: Advisories are noted but not judged materially. Still, this is sensible implementation guidance given verified existing coverage in `tests/test_llm_client.py`.
- Evidence Grade: A (tool-verified existing test coverage)

### Challenge 11: Single-model review quality advantage is asserted, not evidenced
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.87
- Rationale: Advisories are noted but not judged materially. This is a framing issue, not a blocking design flaw; the proposal can proceed if it presents the quality claim as a hypothesis rather than a proven fact.
- Evidence Grade: C (reasonable argument, not directly tool-verifiable)

## Spike Recommendations
None

## Evidence Quality Summary
- Grade A: 9
- Grade B: 0
- Grade C: 2
- Grade D: 0

## Summary
- Accepted: 6
- Dismissed: 5
- Escalated: 0
- Spiked: 0
- Overall: REVISE with accepted changes
