---
topic: judge-stage-frame-reach-audit
created: 2026-04-17
review_backend: cross-model-with-judge
security_posture: 3
personas: [architect, security, pm, frame-structural, frame-factual]
judge_model: claude-haiku-4-5-20251001
challenger_models: [claude-opus-4-7, gpt-5.4, gemini-3.1-pro, claude-sonnet-4-6, gpt-5.4]
recommendation: PROCEED-WITH-FIXES
complexity: medium
related:
  - tasks/judge-stage-frame-reach-audit-proposal.md
  - tasks/judge-stage-frame-reach-audit-design.md
  - tasks/judge-stage-frame-reach-audit-findings.md
  - tasks/judge-stage-frame-reach-audit-judgment.md
---

# Challenge Synthesis — Judge-Stage Frame-Reach Audit

## Gate Decision

**PROCEED-WITH-FIXES.** The audit concept is sound and the intake-audit lesson is correctly applied (severity-drift structural argument, pre-committed gates, aggregation rule). Judge accepted 10 MATERIAL findings but each has a bounded fix — mostly doc/config/policy revisions rather than new code. Execute Phase 0a after the fixes land in a revised plan.

## Recommendation rationale

- **Not PROCEED:** 10 MATERIAL findings stand. Five are tool-verified (Grade A evidence). Three are high-convergence across 3 challengers. Proceeding without fixes repeats the intake audit's "pre-committed machinery vs. unmet premise" trap.
- **Not SIMPLIFY:** The feature (measure judge-stage Frame reach) is already appropriately scoped — Phase 0a is a 30-min kill-switch. The fixes tighten the design, they don't shrink it. Per `/challenge` anti-pattern rule: "MATERIAL finding with trivial fix = build condition, not reason to downgrade."
- **Not PAUSE:** No finding blocks execution indefinitely. The hardest fix (Phase 0x orchestration-readiness gate) is ~50 LOC of scaffold, not new subsystem.
- **Not REJECT:** Operational evidence supports the need. Judge error rate is unmeasured. If Phase 0a reveals baseline errors ≥5, the audit is justified; if <5, audit exits cleanly in 30 min — cheap information either way.

## Inline fixes required before `/plan` writes the execution plan

Eleven fixes. Each is bounded. Assess against the cost table in `/challenge` Step 9.

### Critical (must land before Phase 0a runs)

1. **Remap Frame persona to non-Anthropic model family for this audit.** [Cost: Trivial — config change]
   - Frame-structural default is `claude-sonnet-4-6`; author in Round 2 corpus is frequently `claude-opus-4-7`. Same-family = correlated blind spots (`cmd_judge` already tags this `degraded_single_model` at `scripts/debate.py:1452-1453`).
   - Fix: For this audit, set frame-structural model to `gpt-5.4` or `gemini-3.1-pro` (whichever is not the judge model). Document in audit plan frontmatter. Not a default config change.
   - Source: Judge Challenge 1 (ACCEPT, conf 0.95, Grade A).

2. **Correct proposal language: independence checks are advisory, not enforced.** [Cost: Trivial — text fix]
   - Current proposal says "Model diversity is operationally enforced." `scripts/debate.py:1451-1471` only `print("WARNING: ...")`, no block.
   - Fix: replace with "independence checks are advisory warnings; this audit additionally enforces family-overlap rejection at Phase 0x." No code change to `cmd_judge` itself (out of scope).
   - Source: Judge Challenge 2 (ACCEPT, conf 0.98, Grade A).

3. **Add Phase 0x (orchestration-readiness gate) before Phase 0a.** [Cost: Small — ~50 LOC scaffold]
   - `cmd_judge_with_frame` does not exist. `cmd_judge` has no hook for a post-hoc Frame pass. Phase 0 as-written assumes orchestration exists.
   - Fix: New Phase 0x ships a minimal orchestration harness (a Python script OR a minimal `cmd_judge --post-frame` stub — pick one in `/plan`) that can run Frame-structural + Frame-factual on judge output. Phase 0a does not run until 0x verifies orchestration works on one smoke-test proposal.
   - Source: Judge Challenge 3 (ACCEPT, conf 0.98, Grade A).

### High priority (must land before Phase 1)

4. **Restructure Phase 0 as explicit decision tree with stop-gates.** [Cost: Trivial — sequence edit in plan]
   - Current phase order treats Phase 0a/0c/0d/0e as sequential setup; doesn't spell out "STOP if X" at each gate.
   - Fix: Rewrite Phase 0 as branching decision tree: `0x orchestration OK → 0a baseline errors ≥5 → 0c factual-FP ≤50% → 0d aggregation rule lock → 0e threshold pre-commit → Phase 1`. Each stop-gate is explicit. Do NOT design Phase 0d/0e/Phase 3 details until Phase 0a and 0c confirm the premises.
   - Source: Judge Challenge 7 + 14 (both ACCEPT, conf 0.88–0.90, 3-challenger convergence).

5. **Fix specificity floor formula: pre-commit fixed value instead of data-driven.** [Cost: Trivial — formula replacement]
   - `specificity_floor = 1 − measured_FP_rate − 1σ_buffer` at n=5 is dominated by sampling noise (±0.22). Self-adjusts downward if Phase 0c measures a high FP rate.
   - Fix: Pre-commit `specificity_floor = 0.80` (absolute, policy-chosen, documented). If Phase 1 measured specificity < 0.80, audit DECLINES regardless of Phase 0c calibration. This is the policy fix the judge (Challenge 4) prefers over raising n.
   - Source: Judge Challenge 4 (ACCEPT, conf 0.92, 3-challenger convergence).

6. **Tighten aggregation rule: second clause covers factual-FP pollution within co-signed findings.** [Cost: Trivial — one sentence in plan]
   - Current rule: "structural-vetoes-factual-only-findings." Missing: what happens when a factual-FP claim co-signs an unrelated structural finding and inflates it.
   - Fix: Add to aggregation rule: "A finding whose only novel substantive content is a factual claim unsupported by the structural pass is discarded entirely, even if structural co-signs a different aspect of the same finding." Lock in Phase 0d frontmatter.
   - Source: Judge Challenge 5 (ACCEPT, conf 0.85, 2-challenger convergence).

7. **Define data-egress policy + corpus eligibility.** [Cost: Small — policy section in plan]
   - Audit sends archived proposals and judge outputs to external LLMs. No redaction rule, no eligibility check.
   - Fix: Add to plan: (a) corpus eligibility — exclude proposals containing credentials, private design content, or sensitive identifiers; (b) `results.md` artifacts store IDs/labels + minimal excerpts, not full prompts/responses; (c) Phase 0x includes a data-classification check (grep for credential patterns) before any corpus entry is used.
   - Source: Judge Challenge 10 (ACCEPT, conf 0.88, Grade A).

8. **Exhaust organic labeling before synthesis; add explicit wait-for-corpus path.** [Cost: Trivial — sequence edit]
   - Current Phase 0b treats "label from debate-log.jsonl" and "synthesize proposals with REJECT triggers" as equivalent fallbacks. Synthetic distribution ≠ organic distribution (embedded triggers are more detectable than drift-shaped errors).
   - Fix: Phase 0b sequence becomes: (a) exhaust labeling of `stores/debate-log.jsonl` first; (b) if n<5 organic errors after exhaustive labeling, default choice is **defer audit 2-4 weeks for passive corpus growth**, NOT synthesis; (c) synthesis only if urgency is explicitly justified, and synthetic results are reported SEPARATELY from organic (never pooled for verdict).
   - Source: Judge Challenges 8 + 12 (both ACCEPT, 2–3 challenger convergence).

### Escalations (flag; do not block Phase 0a)

9. **Escalate: trust boundary / prompt-injection from factual-mode tool output.** [Not blocking]
   - Factual mode reads archived proposals + code via tools. If archived content has adversarial text, it could shape Frame's assessment.
   - Disposition: Flag in plan as a known limitation for v1 audit. Constrain Phase 0x corpus to trusted in-repo content only (frame-lens-validation Round 2 proposals). Revisit if audit passes and we want to run against external corpora.
   - Source: Judge Challenge 6 (ESCALATE, conf 0.65).

10. **Escalate: factual mode cost justification if it has zero independent gating authority.** [Not blocking]
    - Aggregation rule requires structural co-sign; factual alone cannot trigger REJECT. Does factual add evidence the structural pass uses, or is it pure noise?
    - Disposition: Phase 0c's known-correct run measures factual's FP rate AND signal rate (how often factual surfaces verifiable evidence that structural then cites). If signal rate <20%, drop factual entirely (Approach C fallback from design doc).
    - Source: Judge Challenge 9 (ESCALATE, conf 0.70).

11. **Escalate: ship form (subcommand vs. flag).** [Not blocking — deferred to Phase 3]
    - `cmd_judge_with_frame` vs. `cmd_judge --post-frame` is a design choice for Phase 3 only. Audit doesn't depend on this.
    - Disposition: Defer to `/plan` when/if Phase 3 activates.
    - Source: Judge Challenge 15 (ESCALATE, conf 0.65).

## Cost of inaction

The judge correctly weighs both sides (Challenge 7 rationale):
- **Cost of building:** ~4-6 hrs audit time + orchestration scaffold. No production risk if Phase 3 remains opt-in.
- **Cost of NOT building:** Judge error rate stays unmeasured. Intake-stage Frame reach DECLINED. Without the judge-stage audit, we carry a blind assumption about judge reliability. A judge that dismisses a REJECT-worthy finding silently ships bad work with no further gate.

Phase 0a alone (30 min after Phase 0x orchestration lands) resolves the premise question. The audit structure converts "build the whole thing and see" into "build the 30-min test first; commit to the full build only if it discriminates."

## Convergent signal across personas

Judge's cross-challenger convergence analysis shows three findings raised independently by ≥3 challengers:
- Challenge 4 (specificity floor sampling noise) — A, C, E.
- Challenge 8 (synthetic corpus non-equivalence) — A, D, E.
- Challenge 14 (full machinery pre-built) — A, C, D.

When three different personas raise the same concern independently, it's not review artifact — it's a real structural weakness. All three are addressed by the inline fixes above.

## Complexity: medium

- No new subsystem (Phase 0x is a thin orchestration harness).
- One config remap (frame-structural model for this audit only).
- No new dependencies.
- Deletion cost is low: if audit declines, only the scaffold + revised plan + 1-2 hrs of run time are discarded.
- Irreversibility: none. Default `cmd_judge` unchanged regardless of outcome.

## Artifacts produced

- `tasks/judge-stage-frame-reach-audit-proposal.md` (input)
- `tasks/judge-stage-frame-reach-audit-design.md` (input from `/think discover`)
- `tasks/judge-stage-frame-reach-audit-findings.md` (raw challenge output, 5 challengers)
- `tasks/judge-stage-frame-reach-audit-judgment.md` (judge adjudication, claude-haiku-4-5-20251001)
- `tasks/judge-stage-frame-reach-audit-challenge.md` (this file — synthesized gate artifact for `/plan`)

## Next action

- `/plan judge-stage-frame-reach-audit` — incorporate all 8 high-priority inline fixes into the execution plan. Frontmatter must reflect: frame-structural model remap; Phase 0x orchestration gate; explicit decision-tree Phase 0 structure; pre-committed 0.80 specificity floor; two-clause aggregation rule; data-egress policy; exhaustion-before-synthesis sequence; wait-for-corpus as default if organic corpus is insufficient.
- Flag 3 escalations in plan as deferred decisions (trust boundary, factual mode cost, ship form).
- DO NOT write Phase 0d/0e/Phase 3 details in the initial plan. Keep `/plan`'s scope to Phase 0x + Phase 0a only. Extend the plan after Phase 0a confirms the premise.
