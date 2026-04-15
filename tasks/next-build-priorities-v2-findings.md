---
debate_id: next-build-priorities-v2-findings
created: 2026-04-15T14:09:01-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# next-build-priorities-v2-findings — Challenger Reviews

## Challenger A — Challenges
Now I have a thorough understanding of the codebase. Let me formulate my review.

## Challenges

1. **RISK** [MATERIAL] [COST:SMALL]: **The proposal underweights debate.py test coverage relative to its actual risk profile.** The proposal frames Candidate 3 as "insurance for stable code" and notes "no bugs have been reported." But the verified facts tell a different story: 4,136 lines, 13 subcommands (I count 13 in the dispatch block at line 4106-4131, not "12+"), 0 tests, and 10+ substantive changes in 5 days. The absence of *reported* bugs in a solo-developer project is weak evidence — the developer is the only user, and LLM output quality issues are notoriously hard to notice without regression tests. The proposal correctly identifies that pure-function utilities (argument parsing, prompt assembly, config loading, persona routing) are testable without mocking. These are exactly the functions most likely to regress during rapid iteration. A focused test suite for debate.py's pure functions (~20-30 tests covering arg parsing, prompt assembly, persona routing, config loading) would be SMALL cost and higher leverage than linter tests, because the linter is 246 lines with 9 checks that just passed 22/22 skills, while debate.py is 17x larger, changing daily, and has zero safety net. That said, this doesn't invalidate doing linter tests — it's a sequencing question.

2. **ASSUMPTION** [ADVISORY]: **The `## Output` regex is framed as a potential bug, but it's likely working as designed.** Line 198 shows `re.search(r'^##\s+Output\b', body, re.MULTILINE)`. The `\b` word boundary means `## Output Contract` *would* match (since "Output" is followed by a space, which is a word boundary). However, `## Output Contract` appears in 3 skills (EVIDENCED: `check_code_presence` returned match_count=3). These skills reference debate.py and have output specifications — matching them as having an output section is arguably *correct* behavior. The proposal already notes this ("Output Contract IS an output spec section, so matching it could be correct. Needs investigation before changing"). This investigation is likely to conclude it's not a bug, reducing the scope of Candidate 2 to just writing tests.

3. **ALTERNATIVE** [MATERIAL] [COST:TRIVIAL]: **The proposal doesn't consider a hybrid: write linter tests AND a minimal debate.py pure-function test file in the same session.** The linter has 9 checks → ~18 test cases. That's maybe 150-200 lines of test code. debate.py's pure functions (frontmatter parsing equivalent, persona routing, config loading) could get a starter test file of ~15-20 tests in another 150 lines. Both together are still a single-session scope. The proposal presents these as mutually exclusive candidates when they're complementary and both small.

4. **UNDER-ENGINEERED** [ADVISORY]: **The linter's tier classification has no test coverage and uses heuristic pattern matching.** Lines 15-74 show tier classification relies on regex patterns (`debate\.py`, `scripts/\w+\.py`, `Agent\(|subagent`, `--mode\b`, etc.) and a step-count threshold (>3 steps → tier 2). Misclassification silently skips 4 checks (Safety Rules, Output Silence, Output Format, Debate Fallback). This is the highest-risk area of the linter to leave untested — a false tier-1 classification means a workflow skill silently passes without safety checks. The proposal's test plan should prioritize tier classification edge cases.

5. **OVER-ENGINEERED** [ADVISORY]: **IR extraction (Candidate 1) is correctly deprioritized, but the proposal could be more decisive about it.** The proposal says "speculative" but doesn't close the door. The facts: sim_compiler.py exists (376 lines, 26 tests), only 3/22 reference IRs exist, no one runs it, and wiring it requires generating 19 more reference IRs + building diff logic + defining "breaking change" semantics. That's a LARGE effort for a tool that catches "logic-level drift" in skills that are already linted for structure and reviewed by cross-model panels. The honest assessment is: IR extraction is a research artifact, not a production tool. It should be explicitly parked, not left as a "maybe later."

## Concessions

1. **The prioritization logic is fundamentally sound.** Building tests for the tool you just shipped (linter) before investing in speculative new capabilities (IR extraction) or reviewing deprioritized code (sim-compiler review) is correct engineering sequencing.

2. **The proposal's self-awareness about infrastructure fatigue is valuable.** Noting "5 sessions straight of infrastructure building" and questioning whether to pause is the right instinct. The linter tests are a natural capstone that closes the linter work cleanly.

3. **The candidate evaluation framework is well-structured.** Each candidate has clear scope, rationale, current state, and what it would catch. The "Current System Failures" section honestly acknowledges that nothing is actively broken, which prevents false urgency.

## Verdict

**APPROVE** with one advisory note: consider adding a minimal debate.py pure-function test file (~15-20 tests for arg parsing, persona routing, config loading) alongside the linter tests, since both are small-scope and debate.py's 4,136 untested lines changing daily represent the project's largest latent risk. The linter-first priority is correct; the question is whether to also start the debate.py test foundation in the same session rather than deferring it entirely.

---

## Challenger B — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: Candidate 2 hardens correctness but does not address the highest operational blast radius: `scripts/debate.py` is verified at 4,136 lines, has no tests, and has 10 recent commits touching it in the last batch of history shown. This is not a security flaw by itself, but it is a production-outage and governance-integrity risk because the engine mediates `/challenge`, `/review`, and related decision flows. Risk of the proposed change: spending the next cycle only on linter tests leaves the most change-active critical path unguarded. Risk of not changing: regressions in review/judgment behavior continue to rely entirely on manual detection after shipping. Recommendation impact: still reasonable to do Candidate 2 first for speed, but pair it with a narrowly scoped “debate.py pure-functions smoke test” follow-up rather than treating debate coverage as deferrable insurance.

2. [ASSUMPTION] [ADVISORY]: The proposal assumes the `## Output` regex issue is small and isolated, but the verified code shows the current check accepts `^##\s+Output\b`, `^##\s+Output Format\b`, or `^##\s+Deliverable\b`. If `## Output Contract` is present in authoring materials, then changing this without auditing real skill files could create either false positives or false negatives in a hook-triggered validator. The plan correctly says “investigate before changing”; keep that as a required step.

3. [UNDER-ENGINEERED] [ADVISORY]: The linter runs on file edits via hook according to the proposal, but the current evidence provided here verifies only the linter script and lack of tests, not the hook implementation itself. Before promoting it to a hard pre-commit gate, verify the trust boundary around hook inputs and path handling in the actual hook code to ensure untrusted file paths or unexpected file contents cannot cause noisy failures or shell-injection-style invocation issues. This does not block Candidate 2; it just means “tested linter” is not the same as “safe gate.”

## Concessions
- The proposal is disciplined about opportunity cost: it deprioritizes unused or intentionally de-scoped sim scaffolding instead of sunk-costing into it.
- Candidate 2 is concrete and bounded: the repo verifies `scripts/lint_skills.py` exists and currently has no tests.
- The proposal explicitly evaluates risk of overbuilding infrastructure, which is appropriate after several infra-heavy sessions.

## Verdict
REVISE with one small addition: do Candidate 2 now, but explicitly schedule a minimal next slice of `debate.py` pure-function test coverage because the verified change velocity and zero-test state make “linter only” too narrow for the next-build recommendation.

---

## Challenger C — Challenges
## Challenges
1. [RISK] [MATERIAL]: **Misaligned risk prioritization.** You are choosing to harden a 246-line linter that currently has 0 reported failures and is correctly passing 22/22 skills, while ignoring `scripts/debate.py`—a 4,136-line engine that powers 5+ skills, runs 5-10 times/day, and has 0 tests. The proposal states `debate.py` has seen **10+ substantive changes in 5 days** [EVIDENCED]. The lack of bugs today is not proof of stability; it is luck. Leaving a high-churn, 4,000+ line core subsystem entirely untested while polishing a working script is a severe governance gap. [COST:MEDIUM to test pure functions in debate.py]
2. [OVER-ENGINEERED] [ADVISORY]: **Testing a script that has already proven its correctness on the entire domain.** The linter only ever runs against `.claude/skills/*/SKILL.md`. It just successfully linted all 22 existing skills and caught 116 real violations [EVIDENCED]. The problem domain is completely contained and already evaluated. Adding 18 formal test cases for 9 checks on top of this provides almost zero marginal user value.
3. [ASSUMPTION] [ADVISORY]: **Regex issue assumes a problem exists without evidence.** The proposal notes the `## Output` check matching `## Output Contract` "May or may not be a bug" and hasn't actually caused a problem. Investing engineering time into a potential non-bug while core infrastructure remains exposed is inefficient. 

## Concessions
1. Rejecting Candidate 1 (IR extraction) is a sound decision; building extraction logic without a downstream consumer is speculative over-engineering.
2. Rejecting Candidate 4 (sim-compiler review) correctly avoids wasting time reviewing commodity infrastructure the project has already decided not to invest in.
3. Hooking the linter to `PostToolUse` was an excellent architectural choice that immediately enforced the canonical spec.

## Verdict
REVISE. The proposal optimizes a functional 246-line peripheral script with zero failures while leaving a rapidly changing 4,136-line core engine completely untested. Pivot the priority to testing the pure functions in `debate.py`.

---
