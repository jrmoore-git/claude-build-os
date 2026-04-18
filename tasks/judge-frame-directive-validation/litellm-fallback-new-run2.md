---
debate_id: litellm-fallback
created: 2026-04-18T09:20:50-0700
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
- Finding: The proposal assumes direct Anthropic API access is the right fallback because users are “running Claude Code,” but does not establish that BuildOS is entitled to or technically able to reuse Claude Code credentials.
- Why this changes the verdict: This is broader than just `ANTHROPIC_API_KEY` presence. Even if a key sometimes exists, the proposal’s core onboarding story depends on a credential-sharing model that may not hold. That makes the central “zero additional setup” claim unproven.
- Severity: MATERIAL

## Judgment

### Challenge 1: Unverified `ANTHROPIC_API_KEY` availability
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.96
- Evidence Grade: A (tool-verified via code search showing no `ANTHROPIC_API_KEY` usage in scripts; proposal itself provides no verification)
- Rationale: This is the strongest challenge. The proposal’s value proposition is “works on first session with just Claude Code installed,” but it offers no evidence that Claude Code exposes a shell-usable Anthropic API key. The challengers engaged directly with the proposal’s premise and identified a likely hard failure mode that defeats the onboarding goal.
- Required change: The proposal must replace the assumption with an explicit credential strategy: either detect a usable Anthropic credential before entering fallback, define the user-facing error if absent, or choose a fallback mechanism that does not depend on Claude Code exporting `ANTHROPIC_API_KEY`.

### Challenge 2: Custom Anthropic HTTP client introduces unnecessary third calling convention
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.84
- Evidence Grade: B (supported by repository structure plus plausible architectural alternatives, but alternatives themselves are not tool-verified in-repo)
- Rationale: The challengers persuasively show the proposal adds a new transport/schema path in an already multi-path client, increasing maintenance cost. The proposal did not justify why raw Anthropic Messages API via `urllib` is preferable to reusing an OpenAI-compatible path or a simpler library approach. This is a real design flaw, not generic “simpler is better” conservatism.
- Required change: Revise the implementation plan to minimize protocol surface area: prefer reuse of the existing OpenAI-compatible dispatch path or another already-supported abstraction, and explicitly justify any new calling convention if still needed.

### Challenge 3: Fallback trigger fires after full retry cycle and is too broad
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.92
- Evidence Grade: A (tool-verified retry behavior cited from `llm_client.py`)
- Rationale: The proposal’s desired behavior is fast graceful degradation on local proxy unavailability, but the cited retry logic would likely delay that and may catch unrelated transient failures. The challengers engaged the concrete implementation path rather than offering generic skepticism. Without narrowing the trigger, the fallback could become both slow and semantically wrong.
- Required change: Specify precise fallback activation criteria: detect local LiteLLM unavailability specifically (e.g., localhost connection-refused) before or outside the general retry loop, and do not trigger fallback for generic network-class failures.

### Challenge 4: Command-level `LITELLM_MASTER_KEY` gating not addressed
- Challenger: B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.94
- Evidence Grade: A (tool-verified early gating in `debate.py`)
- Rationale: This is a concrete correctness issue. If some commands fail before reaching `llm_client.py`, then an implementation limited to transport fallback cannot satisfy the proposal’s claimed scope. The proposal did say `debate.py` would change, but it did not address this specific gating behavior, so the challengers correctly identified a missing required modification.
- Required change: Update the proposal to explicitly modify command entrypoint gating so fallback-eligible commands can proceed without `LITELLM_MASTER_KEY` when a valid fallback path is available.

### Challenge 5: “No artifact degradation” claim is incorrect; metadata semantics change
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Evidence Grade: A (tool-verified artifact/model metadata behavior in `debate.py`)
- Rationale: The proposal is right that downstream structure should remain stable, but wrong to imply semantic equivalence. A 3-persona single-model run is not the same as a multi-model run, and failing to mark that would mislead audit/log/governance consumers. The challengers engaged the proposal’s own “same artifact” claim and narrowed it appropriately.
- Required change: Preserve schema compatibility but add explicit degraded-run metadata, such as `fallback_mode: true`, actual model used per persona, and any loss of independence where relevant.

### Challenge 6: Judge independence violation not handled
- Challenger: A/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.86
- Evidence Grade: A (tool-verified existing author/judge independence guard in `debate.py`)
- Rationale: The proposal explicitly includes `judge` in fallback, but does not address the existing system’s concern for model independence. That is not merely a quality degradation; it changes the meaning of the judge step. Challengers correctly identified that the proposal needs policy behavior here rather than silently reusing the same model.
- Required change: Define fallback behavior for judge explicitly: either skip independent-judge claims, emit a strong non-independent warning/metadata flag, or suppress judge in fallback mode unless an actually distinct model is available.

### Challenge 7: Concurrency, rate limits, and sequential execution not specified
- Challenger: A/B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.78
- Evidence Grade: B (tool-verified current concurrency; rate-limit concern is reasoned rather than directly measured)
- Rationale: The proposal states sequential fallback behavior but does not explain how current concurrency is disabled or what UX impact follows. The challengers are not just asking for polish; execution mode affects correctness, latency, and likelihood of rate-limit failures. This is a legitimate implementation gap.
- Required change: Specify fallback execution policy: whether persona calls become sequential, how concurrency is disabled, what retry/backoff applies for direct-provider rate limits, and what user-visible latency expectations are.

### Challenge 8: `single_review_default` config points to non-Anthropic model
- Challenger: C
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.72
- Evidence Grade: B
- Rationale: This is a useful design observation, but not material on its own. A fallback can reasonably choose a separate mechanism from an existing “single review default” config if the proposal explains why. Since the proposal already frames this as a direct-Anthropic emergency path, the omitted config reference is not enough to block the work.
- Required change: N/A

### Challenge 9: No tests specified for new fallback paths
- Challenger: A/C
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.8
- Evidence Grade: C
- Rationale: The concern is sensible, but it is process guidance rather than a defect in the product decision itself. Test additions should happen, but the absence of a test plan in this short proposal should not independently drive a material verdict.
- Required change: N/A

### Challenge 10: “Single-model review is much better than no review” stated as fact
- Challenger: A/C
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.77
- Evidence Grade: C
- Rationale: This is mostly framing. The proposal’s comparative claim is not rigorously proven, but the challengers themselves concede that graceful degradation is better than hard failure. The stronger issues are about credentials, metadata, and independence—not this rhetorical overstatement.
- Required change: N/A

### Challenge 11: Core onboarding claim rests on reuse of Claude Code credentials without proving entitlement/availability
- Challenger: JUDGE-FRAME
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.91
- Evidence Grade: B
- Rationale: This is the frame-level version of Challenge 1. The proposal is built around “just Claude Code installed” implying usable direct Anthropic access, but that is neither technically established nor product-assumption-safe. Even if some environment setups happen to expose a key, the proposal has not demonstrated a reliable or supported credential-sharing model.
- Required change: Reframe the proposal so the fallback promise is conditional on an explicitly available supported credential, or redesign the fallback to avoid assuming Claude Code authentication can be repurposed by BuildOS.

## Spike Recommendations
None

## Evidence Quality Summary
- Grade A: 5
- Grade B: 3
- Grade C: 2
- Grade D: 0

## Summary
- Accepted: 8
- Dismissed: 3
- Escalated: 0
- Spiked: 0
- Frame-added: 1
- Overall: REVISE with accepted changes
