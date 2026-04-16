---
decision: D7
original: "Pre-flight uses GStack-style adaptive questioning, not batch questionnaires"
verdict: HOLDS
models: claude-opus-4-6, gemini-3.1-pro, gpt-5.4
judge: gpt-5.4
audit_date: 2026-04-15
accepted_challenges: 0
dismissed_challenges: 7
---
# D7 Audit

## Original Decision

Before running explore or pressure-test, the system conducts a 3-4 question adaptive discovery conversation. Questions are selected one at a time based on prior answers (thread-and-steer), with push-until-specific. Not a fixed list dumped at once.

## Original Rationale

User rejected the v1 batch approach ("felt like a form"). GStack proved that one-at-a-time with push-until-specific works for high-stakes discovery. Tested across 20+ simulated personas at 4.8-5.0/5. Key rules: never state the insight, never do the math for them. Alternatives rejected: no pre-flight (wrong frames anchor output), 5-question batch (user rejected it), 1 question only (insufficient to break deep anchors per testing).

## Audit Findings

**Rationale holds.** Three independent evidence lines: (1) direct user rejection of v1 batch approach — highest-fidelity signal for a solo-user tool [EVIDENCED]; (2) 4.8-5.0/5 testing data across 20+ personas [EVIDENCED, methodology underspecified]; (3) D11 independently reaffirmed "pre-flight context quality determines output quality" one day later [EVIDENCED]. The protocol iterated to v7 with skip paths, self-seeding, terse-user mode, and three-gate sufficiency — continued investment signals ongoing value.

**Alternatives were not rejected too quickly.** The v7 implementation incorporates softened versions of all three: "no pre-flight" → skip path; "generate with available context" → self-seeding; "minimize questions" → stop-after-sufficiency. The decision record frames choices too discretely; the actual solution is a hybrid.

**Not corrupted by pipeline bias bugs.** Conservative/recency bias pushes toward "don't build" or "descope" — D7 went the opposite direction (added complex adaptive capability). If anything, the insufficient-context pipeline bug would have made evaluators undervalue D7, not overvalue it.

**One advisory flag:** Consumer abandonment statistics (20-40% at 3+ questions) are weak evidence for a solo-user internal tool. The stronger claim — which is well-supported — is that context quality drives output quality.

## Verdict

**HOLDS.** All 3 reviewers and the independent judge agree. Zero accepted challenges. The decision is well-evidenced, has matured through 7 implementation iterations, and was unaffected by the identified pipeline bugs.

## Risk Assessment

| Direction | Risk | Level |
|---|---|---|
| Keep D7 | Over-questioning when context already present | LOW — skip/self-seed/sufficiency mitigate |
| Reverse D7 | Returns system to insufficient-context failure mode | MODERATE-HIGH |

## Optional Follow-up (non-blocking)

Amend D7 rationale language: replace "consumer abandonment" framing with "minimize cognitive overhead for a solo expert user." More accurate to the deployment context. Not required — decision holds as-is.
