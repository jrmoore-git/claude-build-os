---
debate_id: litellm-fallback
created: 2026-04-18T09:09:54-0700
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

## Frame Critique
- Category: unstated-assumption
- Finding: The proposal assumes the fallback path is worth adding without evidence that LiteLLM-unavailable failures are common enough, severe enough, and specifically due to proxy setup rather than broader credential/provider misconfiguration.
- Why this changes the verdict: Several challengers accept the onboarding-cliff framing, but none question whether the “single biggest onboarding cliff” claim is evidenced or inflated. If this is a low-frequency or already-partially-solved issue, the proposal’s scope and urgency are overstated.
- Severity: MATERIAL

## Judgment

### Challenge 1: API key availability for Anthropic fallback is unverified
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.96
- Evidence Grade: A (tool-verified via code search for `ANTHROPIC_API_KEY` / env usage, plus repository behavior cited)
- Rationale: This is the proposal’s load-bearing assumption, and the challengers directly engage it. The proposal says Anthropic is “already available since the user is running Claude Code,” but the cited repo evidence shows no existing env integration for `ANTHROPIC_API_KEY`, and OAuth-authenticated Claude Code sessions do not imply a shell-exported API key usable by this script. Without a defined credential source and absent-key behavior, the fallback can fail at the exact moment it is supposed to improve onboarding.
- Required change: Specify credential sourcing explicitly; define behavior when no direct Anthropic API key is present; do not assume Claude Code OAuth can be reused. The proposal should either (a) gate fallback on verified key presence with a clear user-facing message, or (b) choose a fallback transport/auth path that is actually available in default setups.

### Challenge 2: Adding a third HTTP calling convention is unnecessary maintenance debt
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Evidence Grade: B (repo structure/tool-supported existence of current paths; alternatives are design reasoning rather than direct verification)
- Rationale: The challengers substantively engage the implementation details and point out that the proposal’s chosen path introduces an avoidable schema/transport fork inside a shared client. The proposal does not justify why Anthropic-native `urllib` is preferable over reusing the OpenAI-compatible abstraction or another existing-compatible client path. “Graceful degradation” is a good goal, but the implementation should minimize divergence in a tested core module.
- Required change: Revise the design to reuse the existing OpenAI-compatible dispatch path if possible, or explicitly justify why a native Anthropic transport is required. The proposal should avoid introducing a third protocol shape unless there is a demonstrated blocker.

### Challenge 3: Fallback trigger conflicts with retry logic and is underspecified
- Challenger: A/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.91
- Evidence Grade: A (tool-verified retry classifications and behavior)
- Rationale: This is a real behavioral flaw, not generic skepticism. If the client retries dead localhost failures before switching, the onboarding improvement is blunted by unnecessary delay; if fallback triggers too broadly, it can silently bypass intended multi-model behavior on transient issues. The proposal does not define the trigger precisely enough for correct UX or operational behavior.
- Required change: Specify that fallback is triggered only on clear local-proxy unavailability signals (for example, connection-refused to configured localhost LiteLLM endpoint) and that this detection occurs before or outside the general retry loop. Preserve retries for transient network/provider failures.

### Challenge 4: `debate.py` command-level gating can block fallback entirely
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.88
- Evidence Grade: A (tool-verified preflight gating in command handlers)
- Rationale: This is a concrete code-path issue. If commands fail before any LLM client call occurs, a client-only fallback cannot solve the end-user problem for those flows. The proposal itself says `debate.py` will change, so the challengers’ point is stronger than the narrow wording of the concern: the proposal must explicitly cover command-level gating.
- Required change: Update the proposal to enumerate all command-entry checks that must be relaxed or reworked for degraded mode, including judge/verdict-related flows, so fallback is reachable.

### Challenge 5: Fallback interception point is unspecified and can corrupt audit semantics
- Challenger: A/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.84
- Evidence Grade: B (repo references/tool-verified model mapping usage; audit consequence is reasoned)
- Rationale: The challengers correctly identify an architectural ambiguity. If substitution happens too low in the stack, logs and artifacts can misrepresent which model actually ran; if it happens in `debate.py`, the affected call sites and judge-independence handling must be explicit. The proposal currently hand-waves “bypasses model routing entirely” without defining where truth is preserved.
- Required change: Specify the interception layer and ensure reported model metadata reflects actual execution. Also define how judge/refine flows signal reduced independence when all personas collapse to one model.

### Challenge 6: Rate limits and latency under single-key fallback are unaddressed
- Challenger: B
- Materiality: MATERIAL
- Decision: DISMISS
- Confidence: 0.63
- Evidence Grade: C (plausible reasoning, but no direct verification of actual fallback traffic levels/limits in this repo context)
- Rationale: The concern is plausible, but the proposal already says fallback runs sequentially, which is itself a mitigation for concurrency-based 429s. The remaining objection is mainly that latency will increase, but that cost is explicitly part of degraded mode and does not by itself invalidate the proposal. This is an implementation note worth documenting, not a material blocker on current evidence.
- Required change: None

### Challenge 7: Artifact metadata should record fallback mode
- Challenger: A/C
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.86
- Rationale: Not judged because advisory. The concern is well-taken and should likely be adopted, but it is informational under the supplied materiality.
- Required change: None

### Challenge 8: No test plan for fallback logic
- Challenger: C
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.9
- Rationale: Not judged because advisory. It is a sensible recommendation.
- Required change: None

### Challenge 9: “Single-model review is better than no review” is hypothesis, not fact
- Challenger: A/C
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.81
- Rationale: Not judged because advisory. As framing language, it should be softened, but it does not materially invalidate the design direction.
- Required change: None

### Challenge 10: `single_review_default` points to GPT, rationale for ignoring it is absent
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.75
- Rationale: Not judged because advisory. It may indicate a design inconsistency, but on current evidence it is not a material blocker to adding a degraded path.
- Required change: None

### Challenge 11: The proposal may be solving an inflated or insufficiently evidenced onboarding problem
- Challenger: JUDGE-FRAME
- Materiality: MATERIAL
- Decision: SPIKE
- Confidence: 0.58
- Evidence Grade: C (proposal assertion lacks supporting operational data in the provided text)
- Rationale: The proposal makes a strong prioritization claim—“single biggest onboarding cliff”—without presenting usage/failure data, and challengers did not test that framing. This does not disprove the need, but it means the scope/priority case is not well evidenced. If LiteLLM-unavailable failures are rare, or usually co-occur with missing direct provider credentials, the proposed fallback may have lower impact than claimed.
- Spike recommendation: Measure onboarding/session failures attributable specifically to unavailable LiteLLM over a representative sample of recent new-user runs. Minimum sample: 50-100 recent `/review` or `/challenge` attempts (or equivalent telemetry/log sample). Success criteria: a substantial share of failed attempts are due to local LiteLLM unavailability and would plausibly be recoverable by the proposed fallback. BLOCKING: YES

## Spike Recommendations
- Validate problem magnitude for LiteLLM-unavailable onboarding failures.
  - What to measure: Count recent `/review` and `/challenge` failures by cause: missing LiteLLM proxy, missing provider credentials, auth failures, other transport errors.
  - Sample size: 50-100 recent new-user or first-week command attempts, or equivalent support/onboarding logs.
  - Success criteria: LiteLLM-unavailability is a common enough failure mode to justify dedicated degraded-mode work, and a direct-provider fallback would actually recover a meaningful portion of those failures.
  - BLOCKING: YES

## Evidence Quality Summary
- Grade A: 3
- Grade B: 2
- Grade C: 2
- Grade D: 0

## Summary
- Accepted: 5
- Dismissed: 5
- Escalated: 0
- Spiked: 1
- Frame-added: 1
- Overall: SPIKE (test first)
