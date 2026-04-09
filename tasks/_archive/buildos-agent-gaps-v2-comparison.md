---
comparison: buildos-agent-gaps v1 vs v2
created: 2026-04-04
v1_debate: tasks/buildos-agent-gaps-debate.md
v1_judgment: tasks/buildos-agent-gaps-judgment.md
v2_challenge: tasks/buildos-agent-gaps-v2-challenge.md
v2_judgment: tasks/buildos-agent-gaps-v2-judgment.md
---
# BuildOS Agent Gaps — v1 vs v2 Debate Comparison

## Setup Differences

| Dimension | v1 (Original) | v2 (Re-run) |
|-----------|---------------|-------------|
| Challenger models | A: gemini-3.1-pro, B: gpt-5.4, C: gemini-3.1-pro | A: gemini-3.1-pro, B: gpt-5.4, C: claude-opus-4-6 |
| Judge model | gpt-5.4 | gpt-5.4 |
| Tools enabled | No | Yes (--enable-tools) |
| Successful challengers | 3 of 3 | 3 of 3 |
| Proposal warnings | None shown | 3 warnings (missing sections) |

## Verdict Counts

| Metric | v1 Challenge | v2 Challenge |
|--------|-------------|-------------|
| Challengers | 3 (Gemini, GPT-5.4, Gemini) | 3 (Gemini, GPT-5.4, Claude Opus) |
| Challenger verdicts | REJECT, REVISE, REJECT | REJECT, REVISE, REVISE |
| Total challenges raised | 14 | 12 |

| Metric | v1 Judgment | v2 Judgment |
|--------|------------|------------|
| Accepted | 9 | 11 |
| Dismissed | 5 (4 ADVISORY + 1 overlap) | 1 |
| Escalated | 1 | 0 |
| Spiked | 0 | 0 |
| Overall | REVISE | REVISE |

## Claude (Challenger C) Status

| Dimension | v1 | v2 |
|-----------|----|----|
| Model | gemini-3.1-pro (duplicate -- no Claude) | claude-opus-4-6 |
| Challenges raised | 4 | 8 |
| Tools used | No (tools not available) | Yes (grep-based codebase verification) |
| Evidence tags | None -- assertions only | EVIDENCED tags with grep results, SPECULATIVE tags for unverified claims |
| Gap validity table | Not present | Present (10-row table with verdict + evidence basis per gap) |

v1 had a mapping error: both Challenger A and Challenger C were gemini-3.1-pro. Claude was absent entirely, so the debate lacked a third model family. v2 corrected this with all three families participating.

## Tool Usage

v2 ran with `--enable-tools` (tool loop limit raised to 10, fallback to no-tools on crash). Claude (Challenger C) used tools to grep the codebase for claimed features:
- `agent-memory` -> 0 matches (disproved Gap 5)
- `/loop`, `/schedule`, `Channels` -> 0 matches (disproved Gap 7)
- `/plugin` -> 0 matches (disproved Gap 9)
- `TeammateIdle` -> 0 matches (disproved Gap 4 partially)
- `Ctrl+B`, `run_in_background` -> 0 matches (questioned Gap 3)
- `Explore` -> 0 matches in config (questioned Gap 2)
- `persona_model_map` -> found cross-model review evidence (supported Gap 6 critique)

Gemini (A) and GPT (B) did not use tools in either version. Tool usage is model-dependent in the debate engine.

## Evidence Tags

| Tag Type | v1 Count | v2 Count |
|----------|---------|---------|
| EVIDENCED | 0 | 8+ (Claude C used grep results as proof) |
| SPECULATIVE | 0 | 4 (Claude C tagged unverifiable claims) |
| Symmetric risk framing | 0 | 2 (Challenger A: risk-of-change vs risk-of-not-change; Challenger B: security surface analysis) |

v1 challengers made the same observations but as unsupported assertions. v2 Claude grounded claims in codebase evidence.

## Symmetric Risk Assessment

v1: Not present. Challengers described risks of the proposal but did not frame both sides.

v2: Challenger A included explicit symmetric framing: "Risk of changing: Documenting these will destroy the framework's credibility. Risk of not changing: Users continue using the actual, supported features." Challenger B added a new security-surface dimension (injection paths, secret exposure, privilege escalation for newly documented capabilities) -- absent entirely from v1.

## ESCALATE Usage

| Version | Escalations | Detail |
|---------|-------------|--------|
| v1 | 1 | Challenge 12 -- judge could not determine if Gap 2 (built-in Explore/Plan subagents) was real or hallucinated from the supplied corpus. Confidence 0.56. Sent to human. |
| v2 | 0 | Same Gap 2 question was resolved: Claude C grep'd for `Explore` in config (0 matches), judge accepted the "unverified" classification at 0.84 confidence instead of escalating. |

Tool evidence eliminated the need for human escalation on the one ambiguous point from v1.

## Confidence Distribution

| Range | v1 Count | v2 Count |
|-------|----------|----------|
| 0.90+ | 7 | 8 |
| 0.80-0.89 | 4 | 3 |
| 0.70-0.79 | 1 | 1 |
| < 0.70 | 1 (escalated, 0.56) | 0 |
| Mean confidence | 0.88 | 0.89 |

v2 eliminated the low-confidence tail (the 0.56 escalation) through evidence.

## Key Differences

1. **Model diversity restored.** v1 ran two Gemini instances (mapping bug). v2 ran Gemini + GPT + Claude -- the intended three-family design.

2. **Evidence-grounded challenges.** Claude's tool access turned "these features look hallucinated" into "these features return 0 grep matches in the codebase." The judge's confidence scores were consistently higher in v2.

3. **Higher acceptance rate.** v2 judge accepted 11/12 challenges (92%) vs 9/14 (64%) in v1. Fewer ADVISORY-level challenges were raised -- challengers focused on MATERIAL issues.

4. **No escalations needed.** v1's one ESCALATE (Gap 2 ambiguity) was resolved by tool evidence in v2, removing the need for human intervention.

5. **Security dimension added.** GPT-5.4 (Challenger B) raised a new MATERIAL challenge absent from v1: security implications of documenting new capabilities without trust boundary guidance (injection paths, secret exposure, privilege escalation). The judge accepted this at 0.78 confidence.

6. **Gap 6 treatment diverged.** v1 dismissed the review-swarm critique as ADVISORY. v2 accepted a narrower version (correlated-failure risk of same-platform subagents) as MATERIAL at 0.76 confidence, while dismissing the broader "wrong direction" framing.

7. **Grading methodology challenge retained.** v1 Challenger C raised this; v2 Claude C also raised it (as challenge 6, ADVISORY). Both versions flagged the binary F-grading as misleading.

8. **Claude C produced a gap validity table.** A structured 10-row breakdown with per-gap verdicts (Already documented / Unverified / Hallucinated / Likely real / Trivially fixable) and evidence basis. This artifact has no equivalent in v1.

## Assessment

Both rounds reached the same overall verdict -- REVISE -- and agreed on the core finding: the gap analysis is contaminated with hallucinated features and cannot be used as-is. The v2 run was materially stronger in three ways: (1) it restored the missing third model family (Claude), giving genuine three-family diversity; (2) tool access let Claude prove hallucination claims with codebase evidence rather than assertion, raising judge confidence and eliminating the one escalation from v1; and (3) challengers raised higher-signal challenges with fewer ADVISORY fillers, producing a 92% acceptance rate vs 64%. The actionable output is unchanged -- only Gaps 8 (headless mode) and 10 (stale tree) survive as worth pursuing, both pending external verification.
