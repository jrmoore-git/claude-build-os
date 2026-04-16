---
debate_id: sim-generalization-findings
created: 2026-04-15T17:53:18-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# sim-generalization-findings — Challenger Reviews

## Challenger A — Challenges


## Challenges

1. **RISK** [MATERIAL] [COST:MEDIUM]: **eval_intake.py has battle-hardened interaction logic that sim_driver.py doesn't replicate.** eval_intake.py contains a `sufficiency_reminder` system injection starting at turn 2 (lines 152-156) with terse-user detection, word-count-based register enforcement, and protocol-specific mid-conversation steering. sim_driver.py has none of this — it runs a generic executor↔persona loop with completion/abandonment signal detection (lines 50-56, 58-62) but no mid-conversation coaching. The proposal's Phase 1 success criterion ("within 0.5 points on all 6 rubric dimensions") will likely fail not because the architecture is wrong, but because eval_intake.py's quality comes from these hardcoded interventions. The generalized harness either needs a mechanism for skill-specific mid-loop injections, or the baseline comparison will be misleading. This is the core abstraction problem: what made eval_intake.py work isn't just the 3-agent architecture — it's the protocol-specific scaffolding baked into the loop.

2. **UNDER-ENGINEERED** [MATERIAL] [COST:SMALL]: **sim_persona_gen.py and sim_rubric_gen.py have zero tests.** Confirmed via tool: both modules have no test files. These are LLM-calling generators whose output quality directly determines simulation validity. sim_persona_gen.py has validation logic (lines 100-108 check hidden_state fields, lines 150-153 check diversity) but none of it is tested. sim_rubric_gen.py has deduplication logic (lines 150-154 with keyword sets) also untested. The proposal acknowledges "never reviewed" but Phase 1 says "review + validate" without explicitly requiring test coverage as a gate condition. Given L25 ("review-after-build has no enforcement"), this needs to be an explicit Phase 1 deliverable.

3. **ASSUMPTION** [MATERIAL] [COST:MEDIUM]: **The V2 scripts have no pipeline wiring and no shared interface contract.** Confirmed: `import sim_` and `from sim_` appear zero times across scripts. No `run_pipeline` function exists. Each script is a standalone CLI tool. The proposal says "wire the pipeline end-to-end" but doesn't specify the integration surface. Will this be a shell script chaining CLIs via file I/O? A new orchestrator script? A Python API layer? The choice matters for error handling, intermediate validation, and debuggability. eval_intake.py is a single 485-line file with everything inline — the V2 approach splits across 4 files with no defined contract between them. This integration layer is the actual new work, and it's unscoped.

4. **RISK** [ADVISORY]: **LLM-generated rubrics may not be comparable to eval_intake.py's hand-authored rubric.** sim_rubric_gen.py generates archetype-specific dimensions via LLM (lines 50-56) with 3 universal dimensions plus generated ones. eval_intake.py uses a hand-authored 6-dimension rubric tuned over 17 rounds. The Phase 1 baseline comparison assumes rubric equivalence, but a generated rubric will have different dimension names, descriptions, and scoring anchors. "Within 0.5 points" is meaningless if the dimensions don't align. The proposal should specify: use eval_intake.py's exact rubric for the baseline comparison, then separately validate the generated rubric.

5. **RISK** [MATERIAL] [COST:SMALL]: **The `hidden_truth` field exists in persona cards but has weak structural enforcement.** `hidden_truth` appears only twice in scripts (confirmed via tool), and `"hidden_truth"` with quotes appears zero times — meaning the references are in string interpolation or comments, not in validation code. sim_persona_gen.py validates `hidden_state` fields (knowledge, urgency, patience, trust, cooperativeness — line 32) but `hidden_truth` is not in the required fields list. Yet hidden truth surfacing is the signature capability that distinguishes this from external tools. The persona schema needs `hidden_truth` as a required field with structural validation, not just a convention.

6. **ALTERNATIVE** [ADVISORY]: **Phase 1 could validate against a second skill instead of only /explore.** The proposal validates the generalized pipeline against eval_intake.py's /explore baseline, but the whole point is generalization. Running /explore through the pipeline proves it can match a bespoke harness on the skill the bespoke harness was built for — that's necessary but not sufficient. Adding one non-explore skill (e.g., /investigate, which already has a reference IR in fixtures) to Phase 1 would test generalization earlier and cheaper than waiting for Phase 2.

7. **OVER-ENGINEERED** [ADVISORY]: **The 3-model separation (Claude/Gemini/GPT) is treated as proven architecture, but the evidence is from a single skill.** The proposal says "3-model architecture is proven" based on eval_intake.py's /explore results. This is N=1. For skills with different interaction patterns (e.g., /think discover which is more analytical than conversational), the model assignments might need to be different. The proposal correctly doesn't change this, but it should note that model assignment per role is a tunable parameter, not a fixed architectural decision.

## Concessions

1. **The problem statement is well-evidenced.** The eval_intake.py track record (3.3→4.5/5 over 17 rounds, specific findings like register mismatch and sufficiency timing) is concrete operational evidence, not hand-waving. The external tools evaluation is thorough and the gap analysis is specific.

2. **The phased approach with an explicit gate is correct.** Phase 1 validates before generalizing, Phase 2 proves generalization on 2-3 skills before wiring into /simulate. The "simplest version" is genuinely the simplest version. This respects L27 (scope expansion = new gate).

3. **The existing V2 code is a real asset.** 1,355 lines across 4 scripts with 48 passing tests (sim_compiler: 26, sim_driver: 22) and reference IRs for 3 skills. This isn't starting from scratch — it's reviewing and wiring existing work. The sim_compiler.py IR extraction is genuinely novel (no external tool does structured IR extraction from procedure documents).

## Verdict

**REVISE** — The proposal is architecturally sound but has three material gaps that should be addressed before Phase 1 begins: (1) define how skill-specific mid-loop interventions (eval_intake.py's secret sauce) will be represented in the generalized harness, (2) make test coverage for sim_persona_gen.py and sim_rubric_gen.py an explicit Phase 1 gate condition, and (3) specify the pipeline integration surface (orchestrator script vs. CLI chaining vs. Python API). None of these are reasons to reject — they're scoping clarifications that prevent Phase 1 from failing at the baseline comparison for the wrong reasons.

---

## Challenger B — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposal does not include a security review of prompt-boundary handling before wiring untrusted SKILL.md content, generated IR, persona cards, and transcripts into three cross-model prompts. Verified code shows `sim_compiler.py` injects raw SKILL.md into `llm_call_json` (`scripts/sim_compiler.py:91-97`), `sim_driver.py` injects full skill content into the executor system prompt (`87-102`), and persona/rubric generation likewise forwards raw IR to models (`scripts/sim_persona_gen.py:82-90`, `scripts/sim_rubric_gen.py:83-97`). That creates real prompt-injection risk across trust boundaries: a malicious or merely malformed skill/persona fixture could steer the executor, persona, or judge into ignoring rules, leaking hidden state, or contaminating scores. The proposal should add explicit delimitering, role separation, and adversarial tests for “untrusted document says ignore prior instructions” before Phase 1 sign-off.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: Information-asymmetry is stated as a key requirement, but the validation plan does not verify it as an invariant. The current code comments say the persona “sees ONLY their card” (`scripts/sim_driver.py:105-109`), but the proposal’s success criteria focus only on score matching and findings surfaced. Without dedicated tests/log checks proving the persona never receives skill procedure/rubric and the executor never receives persona hidden state, a wiring mistake in the end-to-end pipeline could silently collapse the main security and validity boundary. Add a build condition for transcript/prompt fixture tests that assert exact prompt composition per role.

3. [UNDER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: Two of the four V2 components proposed for immediate reuse have no tests in repo: `scripts/sim_persona_gen.py` and `scripts/sim_rubric_gen.py` lack test coverage, while `sim_compiler.py` and `sim_driver.py` do have tests. Because these untested modules generate untrusted inputs consumed by other models, this is not just a quality issue; malformed outputs can propagate into judge corruption, hidden-state leaks, or unsafe logging. The proposal already says “run /review,” but it should explicitly gate Phase 1 on adding minimum schema/negative tests for those two modules.

4. [ASSUMPTION] [ADVISORY]: The quantitative cost claim “~500K-800K tokens per full run” is **ESTIMATED**: assumes ~10 simulations/skill and similar token usage to one `/challenge --deep`, but no repository-backed cost telemetry was provided. Fine for planning, but it should not drive rollout cadence or budget decisions until measured on actual Phase 1 runs.

5. [ALTERNATIVE] [ADVISORY]: Keep Phase 1 narrower by validating only handcrafted anchor personas first, and defer LLM-generated personas until after baseline parity is demonstrated. That reduces exposure to compounding prompt-injection/noise sources during the proof step and makes score-delta analysis easier. Risk of not doing this: if parity fails, you will not know whether the fault is compiler extraction, persona generation, rubric generation, or driver behavior.

## Concessions
- The proposal correctly identifies the core trust property the external tools miss: enforced information asymmetry between executor, persona, and judge.
- The staged gate for `/explore` baseline comparison is sound and limits blast radius before broader rollout.
- Keeping `eval_intake.py` as the gold-standard fallback is a good risk-control choice.

## Verdict
REVISE — the direction is sound, but Phase 1 needs explicit prompt-boundary hardening and invariant tests for information asymmetry before the generalized harness should be trusted.

---

## Challenger C — Challenges
## Challenges
1. [OVER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposed pipeline (`compiler` → `IR` → `persona_gen` & `rubric_gen`) introduces a 3-stage LLM "telephone game". If the LLM extracting the IR misses a nuance from `SKILL.md`, the generated personas and rubrics will structurally inherit that blindspot. *ALTERNATIVE:* Consider skipping the intermediate IR extraction for persona/rubric generation and instead pass the raw `SKILL.md` directly into the generation prompts.
2. [RISK] [MATERIAL] [COST:TRIVIAL]: The proposal explicitly states it will *not* replace `eval_intake.py` even if Phase 1 is successful. If the generalized `persona-sim` mode proves it can match the handcrafted `eval_intake.py` baseline within 0.5 points (Phase 1 success criteria), keeping the hardcoded version introduces duplicate code and divergent testing paths for `/explore`. `eval_intake.py` should be deprecated if Phase 1 succeeds.
3. [ASSUMPTION] [ADVISORY]: The proposal assumes that the 3-agent loop optimized for an "intake" protocol (gathering state from a user) will map cleanly to other interactive skills like `/plan` (where the user is likely reviewing/critiquing output rather than just providing hidden state). The "interaction archetype" concept in the IR needs to do heavy lifting here.

## Concessions
1. **Excellent empirical gate:** Pinning Phase 1 success to matching the known, proven `eval_intake.py` baseline (within 0.5 points) is a textbook example of safe, evidence-based rollout.
2. **Correct tool assessment:** The conclusion that external evaluation tools (like DeepEval or LangSmith) fail at structured hidden state and procedure testing is accurate and justifies the custom build.
3. **Solves a real blindspot:** Identifying that structural linting catches 0% of interactive quality failures, and bounding the token cost to match `--deep` runs, proves the ROI is understood.

## Verdict
APPROVE. The Phase 1 validation gate effectively boxes in the risk of the unreviewed V2 scripts by forcing them to prove their worth against a known, high-quality baseline before expanding scope.

---
