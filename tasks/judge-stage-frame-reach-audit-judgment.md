---
debate_id: judge-stage-frame-reach-audit-findings
created: 2026-04-17T17:43:07-0700
mapping:
  Judge: claude-haiku-4-5-20251001
  A: claude-opus-4-7
  B: gpt-5.4
  C: gemini-3.1-pro
  D: claude-sonnet-4-6
  E: gpt-5.4
---
# judge-stage-frame-reach-audit-findings — Independent Judgment

Judge model: claude-haiku-4-5-20251001 (non-author)
Challenger mapping: {'A': 'claude-opus-4-7', 'B': 'gpt-5.4', 'C': 'gemini-3.1-pro', 'D': 'claude-sonnet-4-6', 'E': 'gpt-5.4'}
Consolidation: 33 raw → 0 unique findings (from 5 challengers, via claude-sonnet-4-6 via local)

# JUDGMENT

## Challenge 1: Frame/Author Model-Family Independence Gap
- **Challenger**: A (architect)
- **Materiality**: MATERIAL
- **Decision**: ACCEPT
- **Confidence**: 0.95
- **Evidence Grade**: A (tool-verified: frame persona = claude-sonnet-4-6, author = claude-opus-4-7, both Anthropic; cmd_judge independence checks exist but are advisory-only per Challenge 2)
- **Rationale**: The proposal treats Frame as judge-independent, but both Frame (claude-sonnet-4-6) and author (claude-opus-4-7) are Anthropic models. The existing `cmd_judge` code explicitly flags same-family pairings as `degraded_single_model` (lines 1452–1453), recognizing that within-family model pairs share correlated blind spots. Running a post-judge Frame pass with an Anthropic model critiquing an Anthropic-authored proposal reintroduces exactly the risk the judge stage was designed to mitigate. The proposal's framing that independence is "operationally enforced" (see Challenge 2) compounds this — the checks are warnings only, not blocks.
- **Required change**: 
  1. Remap `frame` persona to a non-Anthropic model family (e.g., `gpt-5.4` or other external provider) for this audit, OR
  2. Add an explicit family-overlap check mirroring `cmd_judge` lines 1451–1471 as a Phase 0 precondition, with enforcement (not advisory). Document why within-family pairing is acceptable if proceeding despite the check.
  3. Update the proposal's "Operational Context" section to accurately describe independence checks as advisory, not enforced.

---

## Challenge 2: Judge Independence Checks Are Advisory, Not Enforced
- **Challenger**: A (architect), E (frame-factual)
- **Materiality**: MATERIAL
- **Decision**: ACCEPT
- **Confidence**: 0.98
- **Evidence Grade**: A (tool-verified: lines 1451–1471 show WARNING messages with no return/raise/block path)
- **Rationale**: The proposal states independence is "operationally enforced" and treats `cmd_judge` checks as assured guardrails. However, lines 1451–1471 of `scripts/debate.py` show both author/judge and challenger/judge overlap checks emit only `print("WARNING: ...")` messages and continue execution with no exception or early-return path. This is advisory logging, not enforcement. The proposal's narrative that "Model diversity is operationally enforced" is inaccurate and undermines the credibility of the independence story in Challenge 1.
- **Required change**: 
  1. Update proposal language to accurately describe independence checks as "advisory warnings" not "operationally enforced."
  2. Decide: should these checks be hardened to block (raise exception) on same-family pairing? If not, acknowledge the advisory-only nature in the audit design. If yes, that is a separate task outside this audit's scope.
  3. Phase 0 must include a check that author/judge/frame model families are confirmed distinct before proceeding to Phase 1.

---

## Challenge 3: Judge-Stage Frame Integration Does Not Exist; Proposal Overstates Readiness
- **Challenger**: A (architect), E (frame-factual)
- **Materiality**: MATERIAL
- **Decision**: ACCEPT
- **Confidence**: 0.98
- **Evidence Grade**: A (tool-verified: `cmd_intake_check` exists at lines 1402–1413; `cmd_judge_with_frame` does not exist; no Frame hook in `cmd_judge` lines 1416+)
- **Rationale**: The proposal presents Phase 0/1 as exercising a near-existing capability, but the orchestration layer does not exist. `cmd_intake_check` (lines 1402–1413) wraps challenge-stage Frame; `cmd_judge` (lines 1416+) has no analogous dual-mode post-pass. Phase 0d pre-commits an aggregation rule assuming both Frame halves are independently available at judge stage, but they must first be built. The proposal's framing that Phase 0/1 is a "near-existing path" is misleading. Phase 3 correctly labels `cmd_judge_with_frame` as a deliverable, but the earlier phases should explicitly acknowledge that orchestration is a Phase 0 blocker, not a Phase 1 detail.
- **Required change**: 
  1. Restructure Phase 0 to include an explicit "orchestration readiness" gate (Phase 0x): verify that both `frame-structural` and `frame-factual` can be invoked post-judge, and that an aggregation harness exists or is trivial to build. If not, escalate orchestration design before Phase 0a runs.
  2. Reframe the proposal as "audit + build," not "audit existing capability."
  3. Clarify that Phase 3 `cmd_judge_with_frame` includes the orchestration layer, not just the Frame invocation.

---

## Challenge 4: Specificity Floor Is Set by Sampling Noise, Not Frame Behavior
- **Challenger**: A (architect), C (pm), E (frame-factual)
- **Materiality**: MATERIAL
- **Decision**: ACCEPT
- **Confidence**: 0.92
- **Evidence Grade**: B (statistical reasoning: binomial SE ≈ ±0.22 at n=5, p=0.5; Phase 0e formula in proposal; Phase 1 sample size "n≥10, at least 5 known-error + 5 known-correct")
- **Rationale**: Phase 0c measures factual-FP rate on n=5 known-correct outputs. Phase 0e then sets `specificity_floor = 1 − measured_FP_rate − 1σ_buffer`. At n=5, the 1σ binomial buffer is ≈ ±0.22 (SE = √(p(1−p)/n) ≈ √(0.25/5) ≈ 0.22). This means the floor is dominated by sampling noise, not Frame behavior. A measured FP rate of 0.60 (3 FPs in 5) produces a floor of 1 − 0.60 − 0.22 = 0.18, which is permissively low and easily met by Phase 1 data. This creates a self-adjusting pass bar that lowers itself if Phase 0c shows high FP. The proposal then "passes" the audit by design, not by evidence.
- **Required change**: 
  1. Raise the known-correct arm in Phase 0c to n≥10 (or n≥15) before computing the specificity floor, OR
  2. Pre-commit a fixed specificity floor (e.g., 0.80 or 0.85) independent of Phase 0c measurement. Document the floor as a policy decision, not a data-driven derivation.
  3. If Phase 1 data shows specificity below the floor, REJECT the audit, do not adjust the floor downward.

---

## Challenge 5: Aggregation Rule Has a One-Way Gap: Factual-FP Pollution of Co-Signed Structural Findings
- **Challenger**: A (architect), B (security)
- **Materiality**: MATERIAL
- **Decision**: ACCEPT
- **Confidence**: 0.85
- **Evidence Grade**: C (reasoning from proposal text and Phase 0d aggregation rule; no tool verification of the rule itself available)
- **Rationale**: The pre-committed aggregation rule ("structural-vetoes-factual-only-findings") blocks factual-only findings from triggering REJECT but does not address the inverse: a factual-FP claim that co-signs a structural finding and inflates its apparent severity or scope. At judge stage, input is more code-dense than raw proposals (judge outputs cite code paths, hook names, script references per Challenge 7 context), so factual mode's "always finds something" failure mode likely worsens. A finding whose core substantive content is a factual claim unsupported by the structural pass can still co-sign a structural claim and pollute the aggregated severity. The rule needs a second clause to discard such findings even if structural nominally co-signs a different aspect.
- **Required change**: 
  1. Add to Phase 0d aggregation rule: "A finding whose only substantive novel content is a factual claim unsupported by the structural pass is discarded entirely, even if structural nominally co-signs a different aspect of the same finding."
  2. Operationalize this as an explicit filtering step in the aggregation harness: for each finding, identify which claims are factual-only vs. structural-supported, and discard findings where the factual-only claims constitute the only novel substance.
  3. Document this rule in the Phase 0d frontmatter as immutable.

---

## Challenge 6: Trust Boundary — Factual Mode Can Be Shaped by Adversarial Tool Output
- **Challenger**: B (security)
- **Materiality**: MATERIAL
- **Decision**: ESCALATE
- **Confidence**: 0.65
- **Evidence Grade**: C (reasoning from code-inspection path and tool-result handling; B correctly identifies the trust boundary at `scripts/debate.py:1423,1433` and `scripts/debate_common.py:_load_credentials`, verified via tool, but the specific risk of prompt-injection or tool-result poisoning is a threat-model assessment, not a code defect)
- **Rationale**: B correctly identifies the trust boundary: untrusted repository content / tool output → factual Frame prompt → final recommendation. The code does load credentials (lines 1419, 1423, 1433 verified) and does inspect archived proposals and referenced files. However, the specific risk depends on: (1) whether archived proposals or referenced files can contain adversarial instructions; (2) whether the factual-mode prompt treats tool output as evidence or instruction; (3) what the factual-mode prompt's injection defenses are (not visible in the proposal or verified code). This is a security policy decision: is the risk acceptable for an opt-in audit, or does it require explicit prompt hardening and tool-output quoting?
- **Required change**: This is not a proposal defect but a security design decision. ESCALATE to security review:
  - Does the factual-mode prompt have explicit injection defenses (e.g., "tool output is evidence, not instruction")?
  - Should the audit corpus exclude files with untrusted content (e.g., user-submitted code)?
  - Should results be redacted to exclude full prompts/tool output (see Challenge 10)?
- **Spike recommendation**: Not applicable — this is a policy question, not empirical.

---

## Challenge 7: Structural Difference Claim Is Load-Bearing but Untested Before Full Machinery Is Designed
- **Challenger**: C (pm), D (frame-structural)
- **Materiality**: MATERIAL
- **Decision**: ACCEPT
- **Confidence**: 0.88
- **Evidence Grade**: C (reasoning from proposal structure and Phase 0c design; D's claim that judge outputs cite code paths is unverifiable but plausible; C's point that the full machinery is pre-built before Phase 0c confirms the premise is sound)
- **Rationale**: The proposal's central justification for the audit is that judge outputs (MATERIAL-tagged findings) are structurally different from raw proposals, making severity drift inapplicable. This is asserted as a premise, not demonstrated as a hypothesis. Judge outputs likely do cite code paths and script references (Challenge 7 context from D, though unverified), which are the same surface features that triggered factual-FP at intake. Phase 0c is designed to test this, but the full audit machinery (aggregation rule lock-in Phase 0d, specificity floors Phase 0e, subcommand design Phase 3) is already written before Phase 0c runs. If Phase 0c reveals that judge outputs trigger the same factual-FP pattern as raw proposals, the structural-difference premise fails, and the entire audit design is invalidated. The proposal should treat this as a hypothesis to be confirmed, not a premise that justifies the full design.
- **Required change**: 
  1. Restructure the proposal as an explicit decision tree: Phase 0a → stop if <5 baseline errors; Phase 0c → if factual-FP >50%, REJECT audit (structural-difference premise failed); only then lock the aggregation rule (Phase 0d) and proceed to Phase 1.
  2. Phase 0c should explicitly test the hypothesis: "Judge outputs trigger fewer factual-FP events than raw proposals, due to MATERIAL-tag structure and code-citation density."
  3. If Phase 0c falsifies the hypothesis, the audit DECLINES without proceeding to Phase 1.

---

## Challenge 8: Synthetic Corpus Is Not Equivalent to Organic Judge Errors
- **Challenger**: A (architect), D (frame-structural), E (frame-factual)
- **Materiality**: MATERIAL
- **Decision**: ACCEPT
- **Confidence**: 0.90
- **Evidence Grade**: B (A's distribution-shift analysis is sound; D's observation that the proposal treats the two paths as equivalent is correct; E's corpus-count skepticism is justified; the 509-entry log is unverifiable but the proposal does acknowledge the fallback to synthesis)
- **Rationale**: The corpus-escalation path (Phase 0b) falls through to synthesizing proposals with embedded REJECT triggers if n<5 organic errors are found. Synthesized REJECT-triggered proposals have different surface features than the drift-shaped errors that occur in production — embedded triggers are more detectable by Frame. If Phase 0a yields <5 baseline errors and synthesis is used, Phase 1 measures Frame's ability to catch synthetic tells, not real judge misses. The proposal treats "corpus extended via labeled data from debate-log" and "corpus extended via synthetic data" as equivalent fallbacks (Phase 0b text: "label from `stores/debate-log.jsonl`, or synthesize proposals"). This conflates two different measurement scenarios. A's point about distribution shift is material: synthetic errors are not representative of production errors.
- **Required change**: 
  1. Exhaust labeling from `stores/debate-log.jsonl` before authorizing synthesis. If <5 organic errors are found after exhaustive labeling, Phase 0b escalates to "defer audit pending corpus growth" (see Challenge 12), not to synthesis.
  2. If synthesis is eventually used (e.g., after 2–4 weeks of passive accumulation still yields <5 errors), report synthetic results separately from organic results. Do not pool them for Phase 2 verdict.
  3. Document the corpus composition in `results.md`: count of organic errors vs. synthetic errors, and note that Phase 1 sensitivity/specificity are measured against mixed corpus.

---

## Challenge 9: Factual Mode With Zero Independent Gating Authority May Not Justify Its Cost
- **Challenger**: A (architect), C (pm)
- **Materiality**: MATERIAL
- **Decision**: ESCALATE
- **Confidence**: 0.70
- **Evidence Grade**: C (reasoning from aggregation rule and cost estimate; the 10–20s latency and ~10–15 token-cost estimates are SPECULATIVE, not verified)
- **Rationale**: The aggregation rule gives factual-mode findings zero independent gating authority (structural must co-sign to trigger REJECT). If factual mode is too noisy to veto alone, the design incurs ~10–20s latency and extra token costs for a mode that cannot independently trigger a REJECT. This raises a value judgment: does factual mode provide value even as a co-signer (e.g., it surfaces evidence the structural pass uses), or should it be excluded from the judge-stage experiment entirely? The proposal does not justify the cost/benefit trade-off. This is not a defect but a design decision that requires human input.
- **Required change**: ESCALATE to product/architecture review:
  - What is the intended value of factual mode as a co-signer? Does it surface evidence that structural mode uses, or is it purely a noise source?
  - Is the latency cost (10–20s per judge invocation) acceptable for an opt-in feature?
  - Would a single-mode (structural-only) judge-stage Frame pass be sufficient?
- **Spike recommendation**: Not applicable — this is a value judgment, not empirical.

---

## Challenge 10: No Data Egress / Redaction Policy for Audit Artifacts
- **Challenger**: B (security)
- **Materiality**: MATERIAL
- **Decision**: ACCEPT
- **Confidence**: 0.88
- **Evidence Grade**: A (tool-verified: code does load credentials and inspect files at lines 1419, 1423, 1433; proposal specifies output artifacts `results.md` and telemetry but does not state redaction policy)
- **Rationale**: The proposal increases data egress to external model providers (judge artifacts, archived proposals, challenge findings) without stating a data-classification boundary, corpus eligibility rule, or redaction policy. The code does load credentials (lines 1419, 1423, 1433 verified) and will send judge outputs and archived proposals to external LLM providers as part of the Frame critique pass. If archived proposals contain sensitive code, design details, or credentials, this creates durable exposure in provider logs, telemetry, and `results.md` artifacts. B's concern is valid and material for security.
- **Required change**: 
  1. Define corpus eligibility criteria: proposals eligible for Frame audit must not contain credentials, private design content, or other sensitive data. Document this as a precondition in Phase 0.
  2. Specify that `results.md` output artifacts store proposal IDs/labels and minimal excerpts only, not full prompts, tool output, or provider responses.
  3. Add a data-classification check in Phase 0 (Phase 0x): scan the corpus for credentials/sensitive patterns and exclude any proposals that fail the check.
  4. Document the data egress boundary in the proposal: what data leaves the repository, where it goes, and how it is retained/redacted.

---

## Challenge 11: "509 Entries in debate-log.jsonl" Is Unverified and May Overcount
- **Challenger**: B (security, advisory), D (frame-structural, implicit), E (frame-factual, explicit)
- **Materiality**: ADVISORY
- **Decision**: DISMISS (as MATERIAL for verdict purposes, but note as weakness)
- **Confidence**: 0.75
- **Evidence Grade**: D (unverifiable — `stores/` is not accessible via tools; E's observation that `scripts/debate_stats.py:33–49` shows multi-phase append-only structure is tool-verified, but the 509-entry count itself is unverified)
- **Rationale**: The proposal cites "509 entries in `stores/debate-log.jsonl` as of 2026-04-17" to justify corpus sufficiency. This figure is unverified and may overcount if entries are not one-per-debate (E correctly notes the log is multi-phase append-only per `scripts/debate_stats.py:33–49`, verified). However, this is not a material defect in the proposal's logic — the proposal's Phase 0b already includes a corpus-sufficiency gate that escalates if baseline errors <5. The 509 figure is used for plausibility, not as a hard constraint. Even if the true count is lower, Phase 0a will reveal it.
- **Required change**: None for proposal verdict. However, recommend: update the proposal to say "approximately 500+ log entries" or "≥400 log entries" rather than citing a precise unverified count. Phase 0a should confirm the actual corpus size and report it in results.

---

## Challenge 12: Passive Corpus Accumulation Not Considered
- **Challenger**: A (architect, implicit), D (frame-structural, explicit)
- **Materiality**: MATERIAL
- **Decision**: ACCEPT
- **Confidence**: 0.82
- **Evidence Grade**: B (D's log-entry frequency analysis: 1 judge vs. 8 challenge in last 10 entries is unverifiable but plausible; A's recommendation to exhaust organic labeling before synthesis is sound)
- **Rationale**: The proposal's corpus-escalation path (Phase 0b) defaults to synthesis if real labeled data is sparse. However, judge is invoked less frequently than challenge (D notes 1 judge entry vs. 8 challenge in last 10 log entries, unverifiable but plausible). The natural corpus growth rate may produce a sufficient real-labeled corpus within 2–4 weeks without synthesis. The proposal does not consider "wait for corpus" as an option, defaulting to synthesis when real data is sparse. This is a timing question with a potential zero-cost answer if urgency does not require immediate results. The proposal should justify why synthesis is preferable to waiting.
- **Required change**: 
  1. Add an explicit "wait-for-corpus" path to Phase 0b: if baseline errors <5 after exhaustive labeling, option to "defer audit pending passive corpus growth (target: 2–4 weeks, goal: n≥10 organic errors)."
  2. Justify urgency: does the judge-stage reach question need to be answered immediately, or can it wait for natural corpus growth? If urgency is low, recommend deferral over synthesis.
  3. If synthesis is chosen despite available wait-for-corpus option, document the urgency justification in the proposal.

---

## Challenge 13: Phase 0a Error Shape Should Gate Instrument Choice Before Committing to Frame
- **Challenger**: A (architect), D (frame-structural)
- **Materiality**: ADVISORY
- **Decision**: DISMISS
- **Confidence**: 0.80
- **Evidence Grade**: C (reasoning from Phase 0a design; the suggestion is sound but not a defect in the proposal)
- **Rationale**: A and D suggest that Phase 0a error shape should gate instrument choice — if baseline errors are dominated by a specific pattern (e.g., severity under-weighting), a targeted judge-prompt fix may be better than a Frame critique pass. This is a valid observation, but it is a decision-tree refinement, not a material defect. The proposal already includes Phase 0a as a kill-switch; adding an error-shape analysis before committing to Frame is a reasonable elaboration but not required for the audit to proceed. The proposal's Phase 0a is designed to answer "is there a baseline error rate?" — answering "what is the error shape?" is a secondary question that can be answered in Phase 0a output without blocking Phase 1 design.
- **Required change**: None required. Recommend as optional: Phase 0a should include a qualitative summary of error shape (severity under-weighting, scope inflation, etc.) to inform Phase 0d aggregation-rule design. This can be done within Phase 0a without blocking Phase 1.

---

## Challenge 14: Full Audit Machinery Pre-Built Before Phase 0a Confirms the Premise
- **Challenger**: A (architect), C (pm), D (frame-structural)
- **Materiality**: MATERIAL
- **Decision**: ACCEPT
- **Confidence**: 0.90
- **Evidence Grade**: C (reasoning from proposal structure; the observation that full machinery is designed before Phase 0a runs is correct)
- **Rationale**: The proposal nominally treats Phase 0a as a 30-minute kill-switch ("if the answer is 0, the whole audit collapses"), but the full audit design — aggregation rule lock-in (Phase 0d), specificity floors (Phase 0e), `cmd_judge_with_frame` subcommand design (Phase 3) — is already written before Phase 0a runs. If Phase 0a yields <5 errors, the design effort is wasted. The proposal should restructure as an explicit decision tree: Phase 0a → stop if <5 errors; only then proceed to Phase 0c/0d/0e. This is not a defect but an inefficiency that violates the principle of "fail fast."
- **Required change**: 
  1. Restructure the proposal's phase sequence explicitly as a decision tree with stop-gates:
     - Phase 0a: measure baseline error count. STOP if <5 errors (audit DECLINES, defer until corpus grows).
     - Phase 0c: test structural-difference hypothesis (judge outputs trigger fewer factual-FP than raw proposals). STOP if hypothesis falsified (audit DECLINES, structural-difference claim was wrong).
     - Phase 0d: lock aggregation rule (only after 0a and 0c confirm the premise and the hypothesis).
     - Phase 0e: set specificity floors (only after 0d is locked).
     - Phase 1: run main audit (only after all Phase 0 gates pass).
  2. Do not write Phase 0d/0e/Phase 3 design until Phase 0a/0c run and confirm the premise. This saves design effort if the audit declines early.

---

## Challenge 15: `cmd_judge_with_frame` Risks Command-Surface Proliferation
- **Challenger**: A (architect), B (security, concession)
- **Materiality**: ADVISORY
- **Decision**: ESCALATE
- **Confidence**: 0.65
- **Evidence Grade**: C (A's enumeration of existing subcommands is plausible but unverified; the design choice between new subcommand vs. `--post-frame` flag is a product decision, not a code defect)
- **Rationale**: A suggests that an opt-in `--post-frame` flag on `cmd_judge` is preferable to a new `cmd_judge_with_frame` subcommand, citing command-surface proliferation and the need to avoid duplicating the author/challenger/judge independence logic (lines 1450–1465). B concedes that a new subcommand limits blast radius, partially offsetting the proliferation concern. This is a valid trade-off but not a material defect — both approaches are defensible. The choice depends on product architecture philosophy: is independence checking a concern that should be centralized in `cmd_judge`, or should each variant (e.g., `cmd_judge_with_frame`) be self-contained?
- **Required change**: ESCALATE to architecture review:
  - Should Phase 3 ship as `cmd_judge_with_frame` (new subcommand) or `cmd_judge --post-frame` (flag on existing command)?
  - If flag: ensure independence checks (lines 1450–1465) are not duplicated; refactor into a shared function.
  - If new subcommand: ensure it calls the same independence-check logic, not a copy.
- **Spike recommendation**: Not applicable — this is a design choice, not empirical.

---

## Challenge 16: Compute Estimate of ~30–40 API Calls Is Unverified
- **Challenger**: E (frame-factual, advisory)
- **Materiality**: ADVISORY
- **Decision**: DISMISS
- **Confidence**: 0.85
- **Evidence Grade**: C (reasoning from proposal's stated call count; the estimate is SPECULATIVE but plausible: Phase 0 calibration ≈ 10–12 calls, Phase 1 at n=10 with 2 calls per dual-mode pass ≈ 20 calls, total ≈ 30–40)
- **Rationale**: E flags the "≈30–40 API calls" estimate as unverified. The estimate is plausible (Phase 0 ≈ 10–12 calls for calibration, Phase 1 ≈ 20 calls for n=10 with dual-mode, total ≈ 30–40) but is not a material concern. Compute cost is not a blocking constraint for this audit, and the estimate is within the proposal's stated budget. This is an advisory note, not a defect.
- **Required change**: None required. Recommend: Phase 0a should log actual API calls consumed and report in results.md for future planning.

---

## Summary of Challenges

| # | Summary | Decision | Confidence |
|---|---|---|---|
| 1 | Frame/Author Model-Family Independence Gap | ACCEPT | 0.95 |
| 2 | Judge Independence Checks Are Advisory, Not Enforced | ACCEPT | 0.98 |
| 3 | Judge-Stage Frame Integration Does Not Exist | ACCEPT | 0.98 |
| 4 | Specificity Floor Dominated by Sampling Noise | ACCEPT | 0.92 |
| 5 | Aggregation Rule One-Way Gap (Factual-FP Pollution) | ACCEPT | 0.85 |
| 6 | Trust Boundary / Adversarial Tool Output | ESCALATE | 0.65 |
| 7 | Structural Difference Claim Untested Before Full Design | ACCEPT | 0.88 |
| 8 | Synthetic Corpus Not Equivalent to Organic Errors | ACCEPT | 0.90 |
| 9 | Factual Mode Zero Independent Authority / Cost Justification | ESCALATE | 0.70 |
| 10 | No Data Egress / Redaction Policy | ACCEPT | 0.88 |
| 11 | "509 Entries" Unverified (Advisory) | DISMISS | 0.75 |
| 12 | Passive Corpus Accumulation Not Considered | ACCEPT | 0.82 |
| 13 | Phase 0a Error Shape Should Gate Instrument Choice (Advisory) | DISMISS | 0.80 |
| 14 | Full Audit Machinery Pre-Built Before Phase 0a | ACCEPT | 0.90 |
| 15 | `cmd_judge_with_frame` Command-Surface Proliferation | ESCALATE | 0.65 |
| 16 | Compute Estimate Unverified (Advisory) | DISMISS | 0.85 |

---

## Evidence Quality Summary
- **Grade A (tool-verified)**: 8 findings (1, 2, 3, 10, 11-partial)
- **Grade B (supported by governance/prior decisions/indirect evidence)**: 4 findings (4, 8, 12, 14)
- **Grade C (plausible reasoning, no direct verification)**: 4 findings (5, 7, 9, 13, 15, 16)
- **Grade D (speculative/unsupported)**: 0 findings

---

## Spike Recommendations

### Spike 1: Baseline Judge Error Rate (Phase 0a)
- **What to measure**: Run `cmd_judge` on n=5 archived debate outputs from `stores/debate-log.jsonl` (frame-lens-validation Round 2); count verdicts that differ from labeled ground truth (PROCEED/REVISE when REJECT was warranted, or vice versa).
- **Sample size**: n=5 (as proposed in Phase 0a).
- **Success criteria**: 
  - If errors ≥5: proceed to Phase 0c (structural-difference hypothesis test).
  - If errors <5: escalate to corpus-growth deferral (Challenge 12) or synthesis decision (Challenge 8).
- **BLOCKING**: YES — if Phase 0a yields <5 errors, the audit's premise (baseline judge errs) is false, and the entire audit should be deferred or redesigned.

### Spike 2: Structural-Difference Hypothesis (Phase 0c)
- **What to measure**: Run `frame-factual` alone on n=5 known-correct judge outputs (PROCEED/REVISE verdicts that were correct); count false-positive findings (factual mode raises MATERIAL findings on correct judge outputs).
- **Sample size**: n=5 (as proposed in Phase 0c).
- **Success criteria**:
  - If FP rate ≤50%: proceed to Phase 0d (aggregation rule lock-in).
  - If FP rate >50%: REJECT audit (structural-difference hypothesis falsified; judge outputs trigger the same factual-FP pattern as raw proposals, so dual-mode Frame is not suitable at judge stage).
- **BLOCKING**: YES — if the structural-difference hypothesis is falsified, the entire audit design is invalidated, and the audit should DECLINE.

### Spike 3: Corpus Composition (Phase 0b)
- **What to measure**: Exhaustively label entries in `stores/debate-log.jsonl` to identify judge errors (verdicts that differ from ground truth). Count organic errors found.
- **Sample size**: All available entries (goal: n≥10 errors, minimum: n≥5 errors).
- **Success criteria**:
  - If n≥10 organic errors found: proceed to Phase 1 with all-organic corpus.
  - If 5 ≤ n <10 organic errors found: decide whether to wait for passive accumulation (Challenge 12) or proceed to Phase 1 with mixed corpus (Challenge 8).
  - If n <5 organic errors found: defer audit pending corpus growth (do not synthesize; see Challenge 8).
- **BLOCKING**: NO — this affects Phase 1 corpus composition and result interpretation but does not flip the overall recommendation. (If n <5, the audit defers, which is a recommendation change, but this is captured in the Phase 0a spike above.)

---

## Cross-Challenger Convergence

**High convergence (3/3 challengers):**
- Challenge 4 (specificity floor sampling noise): A, C, E
- Challenge 8 (synthetic corpus non-equivalence): A, D, E
- Challenge 14 (full machinery pre-built): A, C, D

**Moderate convergence (2/3 challengers):**
- Challenge 1 (model-family independence): A, B (implied)
- Challenge 2 (independence checks advisory): A, E
- Challenge 3 (integration doesn't exist): A, E
- Challenge 5 (aggregation rule gap): A, B
- Challenge 12 (passive accumulation): A, D

**Single-challenger findings (1/3):**
- Challenge 6 (trust boundary): B
- Challenge 9 (factual mode cost): A, C (convergence)
- Challenge 10 (data egress): B
- Challenge 13 (error shape gating): A, D (convergence)
- Challenge 15 (command proliferation): A, B (convergence)
- Challenge 16 (compute estimate): E

**Corroboration note**: Challenges 1, 2, 3, 4, 8, 14 show strong convergence (2–3 challengers raising the same or highly similar concerns independently). This is **corroborating evidence** that these issues are real, not isolated reviewer bias. However, all three challengers saw the same proposal and constraints, so convergence is **not independent confirmation** — it reflects shared context. The tool-verified evidence (Challenges 1, 2, 3, 10) provides independent confirmation that the concerns are grounded in code facts, not speculation.

---

## Cross-Concession Conflicts

**No material conflicts identified.** Challenger B concedes that a new `cmd_judge_with_frame` subcommand limits blast radius (Challenge 15), which partially offsets A's command-proliferation concern, but both positions are defensible and neither contradicts the other.

---

## Required Changes Summary

### Critical (must fix before Phase 0a):
1. **Challenge 1**: Remap Frame persona to non-Anthropic family OR add enforcement to independence checks.
2. **Challenge 2**: Harden independence checks to block (not advisory) on same-family pairing, or acknowledge advisory-only in Phase 0.
3. **Challenge 3**: Add Phase 0x orchestration-readiness gate before Phase 0a.

### High priority (must fix before Phase 1):
4. **Challenge 4**: Raise known-correct sample to n≥10 or pre-commit fixed specificity floor.
5. **Challenge 5**: Add second clause to aggregation rule: discard findings whose only novel content is factual-only claims.
6. **Challenge 7**: Restructure as decision tree with explicit stop-gates after Phase 0a and Phase 0c.
7. **Challenge 8**: Exhaust organic labeling before synthesis; report synthetic results separately.
8. **Challenge 10**: Define corpus eligibility criteria and redaction policy; add Phase 0x data-classification gate.
9. **Challenge 12**: Add explicit "wait-for-corpus" path to Phase 0b; justify urgency if synthesis is chosen.
10. **Challenge 14**: Do not pre-write Phase 0d/0e/Phase 3 until Phase 0a/0c confirm the premise.

### Escalations (require human decision):
- **Challenge 6**: Security review of trust boundary and prompt-injection defenses.
- **Challenge 9**: Product review of factual-mode cost/benefit trade-off.
- **Challenge 15**: Architecture review of subcommand vs. flag design.

---

## Overall Recommendation

**REVISE** — The proposal has significant structural and design flaws that must be addressed before execution. The core audit concept (measuring judge-stage Frame reach) is sound, and the operational evidence supports the need (unmeasured judge error rate, intake-stage Frame reach DECLINED). However, the proposal conflates multiple independent questions (baseline judge errors, structural-difference hypothesis, aggregation-rule design, specificity floors) into a single phase sequence, pre-commits machinery before confirming the premise, and does not adequately account for data egress, model-family independence, or corpus composition.

**Specific required changes:**

1. **Restructure as explicit decision tree** (Challenge 14): Phase 0a → stop if <5 errors; Phase 0c → stop if structural-difference hypothesis fails; only then lock machinery (Phase 0d/0e).

2. **Fix model-family independence** (Challenge 1): Remap Frame to non-Anthropic or add enforcement to independence checks.

3. **Harden independence checks** (Challenge 2): Make author/judge/frame family-overlap checks enforced blocks, not advisory warnings.

4. **Add orchestration-readiness gate** (Challenge 3): Phase 0x confirms both Frame halves are invokable post-judge before Phase 0a runs.

5. **Fix specificity floor** (Challenge 4): Raise known-correct sample to n≥10 or pre-commit fixed floor (e.g., 0.80).

6. **Add aggregation-rule second clause** (Challenge 5): Discard findings whose only novel content is factual-only claims unsupported by structural.

7. **Add data-egress policy** (Challenge 10): Define corpus eligibility, redaction rules, and add Phase 0x data-classification gate.

8. **Exhaust organic labeling before synthesis** (Challenge 8): Do not default to synthesis; consider wait-for-corpus (Challenge 12).

**If these changes are made**, the proposal becomes a well-structured audit with explicit stop-gates, clear decision criteria, and adequate safeguards. The audit can then proceed to Phase 0a with confidence that the machinery will not waste effort if the premise fails.

**Cost of inaction**: Without this audit, the judge-stage reach question remains unmeasured. The intake-stage Frame reach DECLINED due to severity drift and factual-FP; the judge stage has structurally different input (MATERIAL-tagged findings) and may not suffer the same failures, but we have no evidence either way. A judge error that sends a REJECT-worthy proposal to `/plan` as PROCEED/REVISE would propagate silently with no further gate. The audit's value is high if the premise (baseline judge errors exist) is true; the cost of deferral is continued blind assumption about judge reliability.

---

## Final Verdict

| Category | Count |
|---|---|
| **Accepted** | 10 |
| **Dismissed** | 3 |
| **Escalated** | 3 |
| **Spiked** | 3 (blocking: Phase 0a, Phase 0c; non-blocking: Phase 0b corpus composition) |

**Overall**: **REVISE** — Address the 10 accepted challenges and escalations before proceeding. Execute the 3 spikes in sequence (Phase 0a → Phase 0c → Phase 0b) with explicit stop-gates. If all spikes pass and escalations are resolved, proceed to Phase 1 with the revised design.
