---
debate_id: buildos-improvements-findings
created: 2026-04-16T21:36:22-0700
mapping:
  Judge: claude-sonnet-4-6
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# buildos-improvements-findings — Independent Judgment

Judge model: claude-sonnet-4-6 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gpt-5.4', 'C': 'gemini-3.1-pro'}
Consolidation: 22 raw → 17 unique findings (from 3 challengers, via claude-sonnet-4-6 via local)

## Judgment

### Challenge 1: PostToolUse:Write|Edit granular event type may not exist in the platform
- Challenger: A, C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.85
- Rationale: Tool-verified (Grade A): neither `PostToolUse:Write` nor `PostToolUse:Edit` appears anywhere in hooks or config. All 8 existing PostToolUse hooks use the generic event and filter internally on tool name. The implementation must therefore parse input JSON to distinguish writes from reads — this is feasible but changes the implementation shape and likely invalidates the "~60 lines" estimate. The falsification of the `hook-post-tool-test.sh` example slightly weakens the challenger's framing but doesn't undermine the core finding. The latency/race condition concern from Challenger C is lower weight (speculative) but the event-type finding is solid.
- Required change: Proposal must clarify that `PostToolUse:Write|Edit` is not a distinct platform event; the hook will use generic `PostToolUse` with internal JSON parsing to filter for write/edit tools. The implementation estimate and description should be updated accordingly. The "~60 lines" estimate should be revised upward.
- Evidence Grade: A (tool-verified via check_code_presence returning match_count: 0 for both variants)

---

### Challenge 2: Re-fire policy after user ignores suggestion is unspecified — same suppression failure as L25
- Challenger: A, B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.80
- Rationale: The existing `already_suggested()` guard is tool-verified (Grade A) and the `review-proactive` path exists. The proposal's counter-based hook doesn't specify what happens after the threshold fires and is ignored — the same suppression failure that created L25 could recur. This is not a reason to reject #1 but is a genuine design gap: without a specified re-fire policy (e.g., re-fire every K prompts, or require explicit dismissal), the hook could either annoy repeatedly or silently stop enforcing. The "10 edits" threshold being explicitly provisional without a post-rollout review plan compounds this. Both challengers converge on the same structural gap, though the underlying evidence (the `already_suggested` function) is tool-verified, not just asserted.
- Required change: Proposal must specify the re-fire policy explicitly: what happens when the threshold fires and the user ignores the suggestion? Options to pick from: (a) re-fire every N prompts until a review artifact exists, (b) require explicit `/skip-review` dismissal to suppress, (c) escalate to commit-gate block. The chosen policy must be documented in the hook's design comment and the threshold (10 edits) must be flagged for telemetry review after the first 2 weeks.
- Evidence Grade: A (already_suggested function tool-verified; review-proactive path tool-verified)

---

### Challenge 3: Session-scoped state flag has no specified trust boundary or file permission model
- Challenger: B
- Materiality: MATERIAL
- Decision: DISMISS
- Confidence: 0.72
- Rationale: The threat model requires a lower-trust actor on the same machine who can guess session IDs and write to `/tmp` files. The proposal's context is explicitly single-developer personal projects with one external pilot (Scott). This is a low-threat environment — the attack surface for a malicious local actor spoofing session state flags is essentially zero in the described deployment. The concern is technically valid in the abstract but the proposal's own framing ("solo user, rip-and-replace") and D12's explicit single-developer scoping make this a non-material risk for the current deployment context. If the framework later expands to multi-user or shared environments, this becomes material.
- Evidence Grade: B (existing /tmp/claude- pattern tool-verified; risk assessment is contextual reasoning)

---

### Challenge 4: Change #1 could be replaced by a trivial fix to the existing intent-router's suppression guard
- Challenger: A
- Materiality: MATERIAL
- Decision: DISMISS
- Confidence: 0.70
- Rationale: The challenger's alternative (fix `already_suggested()` in the existing UserPromptSubmit hook) is a legitimate alternative, but the proposal's rationale for a new PostToolUse hook is architecturally sound: it fires at a different point in the workflow (after each write, not after each user prompt), catching the gap *between* prompts where silent drift accumulates. L37's lesson ("enforcement has to live in a single owned surface") and D24's pattern ("single owned surface for user-visible signals") support the new hook approach. The intent-router fix would still only fire on user prompts — it would miss the case where a plan ships without any further user prompts triggering the router. The two mechanisms are complementary, not substitutes. The challenger's "5-line fix" framing undersells what's lost by not having build-boundary detection.
- Evidence Grade: B (review-proactive and already_suggested tool-verified; architectural reasoning from documented lessons)

---

### Challenge 5: Change #2's pruning metric (fire_rate × block_rate) is wrong for advisory/injection hooks and ignores hook severity
- Challenger: A, B, C (unanimous)
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.90
- Rationale: This is the strongest challenge in the set. All three challengers independently identify the same structural flaw: advisory/injection hooks (intent-router, context-inject, session-telemetry) have `block_rate = 0` by design, so the metric would incorrectly flag them for removal. Additionally, rare-but-critical enforcement hooks (credential leakage, protected-file edits) would be pruned by volume-based metrics despite having high failure cost. The unanimous convergence here is substantive — the flaw is real and the metric as specified would produce wrong pruning decisions. This doesn't kill #2 (telemetry-then-prune is still the right approach) but the pruning rubric must be redesigned before execution.
- Required change: Replace `(fire_rate × block_rate)` with a two-class rubric: (a) Advisory/injection hooks: pruning criterion is "does this hook change user behavior in measurable ways?" — requires qualitative review, not volume metrics. (b) Enforcement hooks: pruning criterion is `fire_rate × block_rate` only for hooks guarding low-severity paths; high-severity hooks (credential, structural drift, protected files) are exempt from volume-based pruning regardless of fire rate. The telemetry plan must tag each hook with its class and severity before the 2-week run.
- Evidence Grade: A (hook types and filter patterns tool-verified; the block_rate=0 structural issue follows directly from verified hook behavior)

---

### Challenge 6: "2 weeks then prune" timeline assumes session volume that likely won't materialize
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.75
- Rationale: The proposal is single-developer with one external pilot. Two calendar weeks may produce 10-20 sessions, which is insufficient to get stable fire rate distributions for 21 hooks, especially low-frequency enforcement hooks. The calendar-time gate is the wrong operationalization — a minimum session count is more appropriate. This is a modest but real design gap that could result in premature pruning based on noise. The fix is small (replace "2 weeks" with "minimum N sessions, target 30").
- Required change: Replace the "2-week" pruning gate with a minimum session count (recommend: 30 sessions or 4 calendar weeks, whichever comes later). Define "session" as a complete think→build→commit cycle for counting purposes.
- Evidence Grade: C (plausible reasoning from proposal's own stated deployment context; no tool verification needed for this arithmetic point)

---

### Challenge 7: Change #3's automated dismissed-finding feedback loop is unjustified complexity with no existing infrastructure
- Challenger: A, C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.78
- Rationale: Tool-verified (Grade A): `review-log.jsonl` doesn't exist, `review_feedback.py` doesn't exist, `finding_tracker.py` operates on debate findings not review findings. The "one JSONL store and one script" estimate is materially understated — `cmd_review` would need structured finding ID emission, a dismiss UI surface would need to be built, and the integration with `finding_tracker.py` would require either extension or a parallel system. The proposal's own L32 lesson supports the simpler alternative: manually append concrete failures as negative examples directly into `.claude/rules/`. The automated retrieval system is over-engineered for a single-developer framework at this stage. However, the *goal* of #3 (review learns from dismissed findings) is valid — the implementation should be descoped to the manual approach.
- Required change: Descope #3 to: (a) append dismissed findings as explicit negative examples to the relevant lens section in `.claude/rules/review-protocol.md` manually after each `/review` run, (b) add a one-line reminder in the `/review` skill output ("If you dismiss findings, add them to review-protocol.md as negative examples"). Drop `stores/review-log.jsonl`, `review_feedback.py`, and the `/log --dismiss-finding` flow from this proposal. The automated retrieval system can be revisited after the telemetry data from #2 provides evidence that dismissed-finding volume justifies automation.
- Evidence Grade: A (tool-verified: review-log.jsonl missing, review_feedback.py missing, finding_tracker.py scope confirmed)

---

### Challenge 8: Change #3 introduces unsanitized prompt-injection path from low-trust review artifacts
- Challenger: B
- Materiality: MATERIAL
- Decision: DISMISS
- Confidence: 0.78
- Rationale: This concern is valid in principle but is mooted by the decision to ACCEPT Challenge 7 (descope #3 to manual annotation in rules files). If the automated retrieval system is dropped, the injection path doesn't exist. Additionally, even in the original design, the threat model (single developer annotating their own dismissed findings) makes prompt injection from "malicious findings" implausible — the author is the source of both the findings and the annotations. The concern would be material in a multi-user context but not here.
- Evidence Grade: C (plausible reasoning; mooted by Challenge 7 acceptance)

---

### Challenge 9: Change #4 (tiered install) has no test coverage path
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS (as advisory, noted)
- Confidence: 0.70
- Rationale: The concern is valid (tool-verified: `/setup` skill has no test file) but rated ADVISORY by the challenger. The combinatorial surface (3 tiers × N files) is real but manageable with a simple validation script that lists expected files per tier. This is a good implementation note, not a blocking concern.
- Evidence Grade: A (tool-verified: check_test_coverage returned has_test: false for setup.md)

---

### Challenge 10: Change #4 assumes reducing default install surface won't weaken baseline protections
- Challenger: B
- Materiality: ADVISORY
- Decision: DISMISS (as advisory, noted)
- Confidence: 0.72
- Rationale: The concern is valid but the proposal explicitly addresses it: Tier 1 includes "2 advisory hooks (read-before-edit, pre-commit-tests)" which are the baseline protections. The trade-off is already made explicit in the proposal's tier design. The recommendation to "err conservative for first-time users" is a reasonable implementation note.
- Evidence Grade: C (contextual reasoning; proposal text addresses the concern)

---

### Challenge 11: Change #7 should be removed from the numbered list entirely
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS (as advisory, noted)
- Confidence: 0.65
- Rationale: The challenger is correct that a 7-item proposal with one explicitly held item is effectively a 6-item proposal. However, keeping #7 visible in the numbered list with explicit "hold" status serves a documentation function — it explains *why* this obvious extension isn't being built now, which prevents future sessions from re-proposing it without context. The scope creep risk is real but manageable given the explicit "hold" framing.
- Evidence Grade: C (editorial judgment; no tool verification needed)

---

## Evidence Quality Summary
- Grade A: 6 (Challenges 1, 2, 5, 7, 9 — tool-verified findings)
- Grade B: 3 (Challenges 3, 4, 5 partial — governance context and indirect tool evidence)
- Grade C: 5 (Challenges 6, 8, 10, 11 — plausible reasoning without direct verification)
- Grade D: 0

---

## Spike Recommendations

**None.** All material challenges are resolvable through design specification changes, not empirical tests. Challenge 6's session-volume concern could theoretically be spiked (run 2 weeks and measure actual session count), but the fix (replace calendar gate with session count gate) is trivially correct regardless of the measurement outcome.

---

## Summary

- Accepted: 5 (Challenges 1, 2, 5, 6, 7)
- Dismissed: 6 (Challenges 3, 4, 8, 9, 10, 11)
- Escalated: 0
- Spiked: 0

**Overall: REVISE with accepted changes**

The proposal's core architecture is sound and the prioritization (ship #1 and #2 first) is correct. The five accepted changes are all specification gaps or design flaws that can be addressed without restructuring the proposal:

1. **#1 implementation**: Clarify that the hook uses generic `PostToolUse` with internal JSON parsing; update the line-count estimate; specify the re-fire policy explicitly.
2. **#2 pruning rubric**: Replace `(fire_rate × block_rate)` with a two-class rubric (advisory vs. enforcement) with severity exemptions; replace the 2-week calendar gate with a 30-session minimum.
3. **#3 descope**: Drop the automated retrieval system; replace with manual annotation to `review-protocol.md` with a skill-level reminder. This is the most significant change — it reduces #3 from a new infrastructure build to a 2-line skill change and a documentation convention.

Changes #4, #5, #6 are unaffected. Change #7 stays as-is (explicitly held). The "simplest version" instinct (ship #1 and #2 first) remains correct and is strengthened by the accepted changes — the revised #3 is now small enough to bundle with #1 and #2 if desired.
