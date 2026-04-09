---
debate_id: buildos-agent-gaps-v3-comparison
created: 2026-04-04
v1_date: 2026-04-02
v3_date: 2026-04-04
v1_models: {A: gemini-3.1-pro, B: gpt-5.4, C: gemini-3.1-pro}
v3_models: {A: gemini-3.1-pro, B: gpt-5.4, C: claude-opus-4-6}
judge_model: gpt-5.4
---

# BuildOS Agent Gaps — v1 vs v3 Debate Comparison

## 1. Model Composition

| Slot | v1 | v3 | Change |
|------|----|----|--------|
| Challenger A | gemini-3.1-pro | gemini-3.1-pro | Same |
| Challenger B | gpt-5.4 | gpt-5.4 | Same |
| Challenger C | gemini-3.1-pro | claude-opus-4-6 | Changed — added third model family |
| Judge | gpt-5.4 | gpt-5.4 | Same |

**v1** had only two model families (Gemini, GPT). **v3** has full three-family coverage (Gemini, GPT, Claude), matching the `debate-models.json` persona map. This is the intended configuration per `review-protocol.md`.

## 2. Proposal Enrichment

v3 added three data-backed sections not present in v1:

| Section | Data Source | Key Finding |
|---------|-------------|-------------|
| Current System Failures | `grep -r` across scripts/ and skills/ | Zero matches for all 10 claimed features — strong negative evidence |
| Operational Context | `config/debate-models.json` | Cross-model diversity is deliberate architectural choice, directly relevant to Gap 6 evaluation |
| Baseline Performance | `stores/audit.db` 30-day query | Single model (claude-opus-4-6, 54 calls) in audit log; debate calls invisible (route through LiteLLM) |

## 3. Challenge Quality

### Volume and Tagging

| Metric | v1 | v3 |
|--------|----|----|
| Total challenges | 14 | 19 |
| MATERIAL challenges | 10 | 13 |
| ADVISORY challenges | 4 | 6 |
| Concessions per challenger | 2-3 | 2-3 |
| Verdicts | REJECT, REVISE, REJECT | REVISE, REVISE, APPROVE (with revisions) |

v3 produced more challenges overall and shifted the verdict distribution: no outright REJECTs, one conditional APPROVE.

### Thematic Coverage

| Theme | v1 Coverage | v3 Coverage | Delta |
|-------|-------------|-------------|-------|
| Hallucinated features | All 3 challengers flagged | All 3 challengers flagged | Same core finding, but v3 uses codebase search as evidence |
| Gap 1 already documented | All 3 challengers caught | All 3 challengers caught | No change — consistently identified |
| Gap 6 architectural downgrade | A and C flagged | A and C flagged; B proposed hybrid alternative | B's hybrid nuance is new |
| Verification methodology critique | Not raised | B raised (repo absence ≠ product nonexistence) | New — v3 challenges the evidence standard itself |
| Process failure (meta-problem) | Not raised | C raised (why did hallucinated analysis enter pipeline?) | New — systemic fix recommendation |
| Decision framework missing | Not raised | B and C raised (what actions follow classification?) | New — v3 demands concrete remediation plan |
| Gap 8 headless unverified | Not raised | B raised (author claims "real" without source evidence) | New — catches author's own unverified assumption |
| Gap 3 conflation risk | Not raised | B raised (Bash backgrounding ≠ subagent backgrounding) | New — more precise feature-level analysis |
| Cost tracking blind spot | Not raised | C raised (debate costs invisible in audit.db) | New — operational audit finding |

**v3 introduced 6 new themes** not present in v1, while preserving all 3 core v1 themes.

## 4. Judgment Quality

| Metric | v1 Judge | v3 Judge |
|--------|----------|----------|
| Accepted | 9 | 10 |
| Dismissed | 5 | 1 |
| Escalated | 1 (Gap 2 built-in subagents) | 0 |
| Overall verdict | REVISE | REVISE |
| Confidence range | 0.56–0.99 | 0.72–0.97 |

Key differences:
- **v1 escalated** Gap 2 (built-in subagents like Explore/Plan) because the corpus couldn't resolve whether the feature exists. **v3 did not escalate** — the codebase search evidence and stronger challenger arguments made escalation unnecessary.
- **v1 dismissed 5 challenges** (all ADVISORY). **v3 dismissed only 1** (hybrid subagent prep idea), suggesting v3 challengers produced more substantive material.
- **v3 confidence floor is higher** (0.72 vs 0.56), indicating the enriched evidence base reduced ambiguity.

## 5. New Required Changes (v3 only)

These required changes appeared only in the v3 judgment:

1. **Define acceptable evidence explicitly** — vendor docs, changelog, reproducible command/config, feature status (GA/beta/experimental)
2. **Add per-gap disposition table** — status, evidence source, document or close, priority, required follow-up
3. **Add process control** — codebase and product-source verification before model-generated gap analyses enter proposal pipeline
4. **Downgrade Gap 8** from "likely real" to "unverified pending product-source confirmation"
5. **Split Gap 3** into separate claims; close unsupported subagent-specific claims
6. **Revise evidentiary language** — repo absence triggers external verification, not definitive proof of nonexistence

## 6. Convergent Findings (Both Versions)

These findings were stable across both debates — high confidence they are correct:

1. **~50% of claimed gaps are hallucinated.** Gaps 3 (background subagents), 4 (TeammateIdle), 5 (agent-memory), 7 (/loop, /schedule), and 9 (/plugin) reference non-existent features.
2. **Gap 1 is already documented.** `.claude/agents/` appears in both platform-features.md §7 and team-playbook.md §2. At most needs expansion, not new documentation.
3. **Gap 6 (review swarm) is architecturally inferior** to the current cross-model debate.py approach.
4. **Gap 10 (stale tree) is minor housekeeping.**
5. **The "F" grading scale is misleading** — should be dropped or replaced with priority weighting.

## 7. Overall Assessment

| Dimension | v1 | v3 | Winner |
|-----------|----|----|--------|
| Model diversity | 2 families | 3 families | v3 |
| Evidence quality | Appendix text only | Appendix + codebase search + config data + audit metrics | v3 |
| Challenge depth | 3 core themes | 9 themes (3 core + 6 new) | v3 |
| New actionable findings | 0 beyond v1 proposal | 6 new required changes | v3 |
| Judge resolution | 1 escalation, 5 dismissals | 0 escalations, 1 dismissal | v3 |
| Process recommendations | None | Upstream verification gate for model-generated analyses | v3 |
| Verdict convergence | Both REVISE | Both REVISE | Tie |

**Bottom line:** The v3 debate with enriched evidence and three-family model coverage produced materially better results. It identified the same core problems as v1 (hallucinated features, misclassified Gap 1, Gap 6 architectural downgrade) but added six new themes and six new required changes — particularly the process-level recommendation to gate model-generated gap analyses before they enter the proposal pipeline. The judge required zero escalations, indicating the enriched evidence resolved ambiguities that v1 could not.

The enriched proposal's codebase search was the highest-leverage addition: it transformed "needs verification" hedging into concrete negative evidence that challengers and the judge could reference directly.
