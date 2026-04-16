---
decision: D20
original: "Keep sim infrastructure and generalize eval_intake.py — no external tool meets the requirements"
verdict: REVIEW
audit_date: 2026-04-15
models_used: claude-opus-4-6, gemini-3.1-pro, gpt-5.4
judge: gpt-5.4
judge_result: REVISE (6 accepted, 2 dismissed, 1 escalated)
---
# D20 Audit

## Original Decision

Keep all V2 sim scripts (sim_compiler.py, sim_persona_gen.py, sim_rubric_gen.py, sim_driver.py). Do not adopt external tools. Generalize eval_intake.py's proven 3-agent architecture across interactive skills. This is the corrected version of D20 — it reversed a prior "don't build" verdict that was made without operational evidence (L28).

## Original Rationale

eval_intake.py proved iterative 3-agent simulation produces quality improvements (17 rounds, 3.3→4.5/5) that no other approach replicates. Deep investigation of 7 external tools found none support structured persona hidden state, information asymmetry at the architecture level, or agent procedure testing. The "commodity" label was wrong at the specific requirement level.

## Audit Findings

**What holds (EVIDENCED):**
- Core build-vs-buy direction is correct. eval_intake.py's 17-round track record is real operational evidence.
- External tool gap is genuine. All 7 tools evaluated fail on structured hidden state and agent procedure testing.
- Cost of inaction is real: without simulation, interactive-skill quality validation remains manual, slow, and proven inadequate.
- The "commodity label at wrong abstraction level" insight (L28) correctly explains the original panel failure.

**What requires revision:**

1. **"Keep all V2 scripts" overclaims.** sim_persona_gen.py and sim_rubric_gen.py have 0 tests and have never been reviewed. sim_driver.py has passing tests but was never reviewed. No end-to-end pipeline wiring exists. "Keep all V2 scripts" conflates "capability is proven" with "implementation is validated." (EVIDENCED — proposal admits these gaps; judge confidence 0.92)

2. **sim-generalization-proposal.md not /challenge gated.** The generalization plan was intentionally deferred but is now sitting unchallenged. This is the exact L27 failure pattern: treating a 4x scope expansion as an "evolution" and skipping the gate. (EVIDENCED — proposal context states this directly; judge confidence 0.90)

3. **Generalization from N=1 to 8-10 skills is estimated, not proven.** eval_intake.py proves the architecture works for one skill. The inference to all interactive skills is reasonable but unvalidated. A second skill needs to prove out before broad rollout commitment. (ESTIMATED — judge confidence 0.79)

4. **Inspect AI was dismissed without testing the hybrid option.** The dismissal ("you write the sim loop yourself — no savings") doesn't address whether Inspect AI could serve as substrate/orchestration layer while BuildOS writes the simulation logic. The proposal itself calls it the "closest fit" without doing a direct comparison. (ESTIMATED — judge confidence 0.76)

5. **Cost is undocumented.** ~500K-800K tokens per full run is not addressed in D20. Whether this is "trivially cheap" depends on run frequency and organizational context. An operating-cost section with triggers, cadence, and guardrails is missing. (EVIDENCED — judge confidence 0.88; cost interpretation escalated as human-required)

## Verdict: REVIEW

D20's strategic direction holds. The corrected "build vs. buy" conclusion survives full context evaluation. The original "kill it" verdict was correctly reversed.

But the decision overreaches in two ways: it commits to V2 implementation artifacts that haven't been validated, and it treats one skill's success as proof of generalization. The required changes are process completions, not strategic reversals.

**D20 stands as written for: keep simulation capability, reject external tools as replacements.**

**D20 requires revision for: "keep all V2 scripts" → "treat V2 as candidate assets pending review/test/challenge."**

## Required Actions (before D20 fully holds)

1. Run `/review` on V2 scripts — particularly sim_persona_gen.py and sim_rubric_gen.py (0 tests each)
2. Run `/challenge` on `tasks/sim-generalization-proposal.md` using D21's judge step
3. Wire and validate the end-to-end pipeline against eval_intake.py's /explore baseline (within 0.5 points on all rubric dimensions)
4. Validate on one additional skill (/investigate or /plan) before committing to 8-10 skill rollout
5. Add operating-cost section to D20: run frequency, when to use smoke-test vs full quality-eval, token budget guardrails
6. Add Inspect AI hybrid analysis: specific API-level comparison showing whether substrate adoption reduces maintenance burden

## Risk Assessment

| Risk | Direction | Severity |
|---|---|---|
| V2 scripts need major rework after /review | Keeping | Medium — sunk cost is ~1,626L, manageable |
| Second skill shows no improvement from simulation | Keeping | Medium — would require scoping down to proven skills only |
| Cost at scale (8-10 skills × 17 rounds) becomes a bottleneck | Keeping | Low — estimated $400-1,360 total, but needs explicit governance |
| Reverting to "kill it" loses the only proven quality mechanism | Reversing | High — eval_intake.py findings are not replicable with external tools |
| Inspect AI adoption creates impedance mismatch | Reversing | Medium — integration cost could exceed savings |

Asymmetry favors keeping: downside of keeping is manageable rework; downside of reversing is losing a proven quality mechanism with no replacement.
