---
decision: D8
original: "Upgrade /status with smart routing instead of creating /next"
verdict: REVIEW
audit_date: 2026-04-15
judge_model: gpt-5.4
reviewer_models: claude-opus-4-6,gemini-3.1-pro,gpt-5.4
judge_accepted: 1
judge_dismissed: 4
---

# D8 Audit

## Original Decision

Enhance the existing `/status` skill with a context-aware routing table (13 priority-ordered conditions + overlays) instead of creating a new `/next` command. Routing reads git state, artifacts, context budget, and audit log to suggest the specific next skill and mode.

## Original Rationale

Three alternatives evaluated: (a) advisory rule text, (b) auto-nudge hooks, (c) new `/next` command. Advisory text rejected because it drops under context pressure. Hooks rejected as "annoying" and "binary block/allow." `/next` rejected as duplicating `/status` purpose.

## Audit Findings

**Finding 1 (ACCEPTED — MATERIAL):** Hook rejection rationale was premature and later falsified.

D8 characterized hooks as "binary block/allow" and "annoying." This was SPECULATIVE. D16 subsequently implemented `hook-intent-router.py` — non-blocking, advisory-only routing suggestion injection that fires on every user message without being annoying or binary. The stated reason for rejecting hooks is directly contradicted by what D16 proved possible. The correct framing: hooks alone were not sufficient, but hooks as a complement to skill-level routing are valid and proven. This is consistent with conservative bias in the original pipeline.

**Finding 2 (DISMISSED):** Core routing table approach holds.

The 12-condition priority-ordered routing table with overlays now lives in `/start` (absorbed via D12). This is the D8 vision realized. EVIDENCED by current system state.

**Finding 3 (DISMISSED):** `/next` concern is retrospective drift.

D12 merged `/status` away, making the anti-duplication argument obsolete in retrospect. But no current deficiency from `/next` not existing — the routing need is solved by `/start` + `hook-intent-router.py` together.

**Finding 4 (DISMISSED):** Advisory text rejection was correct.

L25 confirmed advisory rules fail silently under context pressure. This rejection was validated.

## Verdict

**REVIEW**

The architectural direction was correct — the routing table design is live, working, and validated. The implementation outcome holds. One finding accepted: the hook rejection rationale was wrong (conservative bias, speculative characterization). D16 already patched the gap by adding hooks as a complement.

## Risk Assessment

**Risk of keeping D8 as-is:** Low for architecture. Moderate for rationale precedent — if future decisions cite D8's hook rejection as justification for avoiding hooks, they'll be misled.

**Risk of reversing D8:** High and unnecessary. Removing routing from `/start` would undo both D8 and D12 consolidation.

**Required action:** Annotate D8 rationale — "rejection of hooks as a category does not hold; the correct framing is hooks alone were insufficient, but hooks as advisory complement to skill-level routing are valid and proven (see D16)."
