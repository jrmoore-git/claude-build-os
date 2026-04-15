---
debate_id: next-build-priorities-findings
created: 2026-04-15T14:04:40-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# next-build-priorities-findings — Challenger Reviews

## Challenger A — Challenges
I have enough data to render a verdict.

## Challenges

1. **RISK** [MATERIAL] [COST:TRIVIAL]: **The proposal claims debate.py is "not being actively modified" — commit history shows the opposite.** The last 10 commits affecting these files include 7 substantive changes to debate.py: timeout hardening, synthesis restructuring, fallback logic, critique mode, graceful degradation, and intent routing. A 4,136-line file with 12+ subcommands, zero tests, and active weekly modifications is the highest-risk component in this codebase. The proposal's prioritization is built on a false premise. Fix: update the assessment to acknowledge active modification, which changes the risk calculus for candidate #3.

2. **ASSUMPTION** [MATERIAL] [COST:SMALL]: **The `## Output` regex "issue" may not be a real bug.** The proposal frames `^##\s+Output\b` matching `## Output Contract` as a false positive. But `## Output Contract` *is* an output specification section — matching it seems correct. The 3 skills using `## Output Contract` would fail if the regex were tightened to exclude them, requiring either skill edits or a new allowlist entry. The proposal should verify whether `## Output Contract` is a canonical heading before "fixing" this. If it is canonical, the regex is already correct and the linter hardening scope shrinks to just writing tests.

3. **UNDER-ENGINEERED** [MATERIAL] [COST:MEDIUM]: **Deferring debate.py tests is the wrong call given the evidence.** 4,136 lines, 0 tests, 7 substantive changes in the last ~5 days, and it's the engine behind 5+ user-facing skills running 5-10 times/day. The proposal correctly identifies this as a candidate but dismisses it based on "not being actively modified" and "no recent bugs." The commit history refutes the first claim, and the second is unfalsifiable without tests — you can't observe bugs you aren't testing for. At minimum, the pure-function utilities (argument parsing, prompt assembly, log formatting) could get unit tests without mocking LLM calls. This is a higher-value investment than the regex fix.

4. **OVER-ENGINEERED** [ADVISORY]: **IR extraction (candidate #1) is correctly deferred.** Generating reference IRs for 19 skills, defining breaking-change criteria, and building diff logic is a LARGE investment for a technique that has no consumer. The proposal is right to skip this.

5. **ALTERNATIVE** [ADVISORY]: **Linter tests and debate.py tests aren't mutually exclusive.** The proposal frames this as pick-one. lint_skills.py is 246 lines with 9 checks — writing 18 test cases is a half-day task. debate.py utility tests (parsing, formatting, non-LLM logic) could be scoped to another half-day. Both could ship in one session.

## Concessions

1. **Correct triage of sim-compiler work.** Only 1 commit, no production consumers, correctly deferred. The sessions 7-8 analysis that persona_gen/rubric_gen/driver are commodity is sound.
2. **Linter tests are genuinely needed.** A pre-commit gate with 9 checks and 0 tests is a regression waiting to happen. This is a valid priority.
3. **The "simplest version" framing is disciplined.** The instinct to scope small and ship is correct — the issue is which small thing to ship.

## Verdict

**REVISE**: The proposal's dismissal of debate.py test coverage is based on the factually incorrect claim that it's "not being actively modified" — 7 substantive commits in ~5 days contradict this. A 4,136-line, zero-test file under active modification is a higher risk than a regex edge case affecting 3 skills. Revise to: (a) correct the debate.py activity assessment, (b) scope a minimal debate.py test suite (pure-function utilities only, no LLM mocking) alongside the linter tests, and (c) verify whether `## Output Contract` is actually a non-canonical heading before changing the regex.

---

## Challenger B — Challenges
## Challenges
1. [UNDER-ENGINEERED] [ADVISORY]: The proposal is sound, but linter hardening should include at least one regression test for the known `^##\s+Output\b` false-match in `scripts/lint_skills.py` rather than just a regex tweak. Because this linter is already wired as a hook, a bad pattern can create noisy gate failures across trusted author workflows; tests are the cheap guardrail that keeps the hook from becoming an availability/usability problem. [EVIDENCED: proposal states the linter runs on every SKILL.md write/edit via PostToolUse hook; `scripts/lint_skills.py` contains the current regex issue and `check_test_coverage` was not provided for this module, so test presence for it is unverified.] [MATERIAL] [COST:SMALL]: Add targeted tests for the known false-positive and core checks before promoting further reliance on the hook.
2. [ASSUMPTION] [ADVISORY]: “debate.py has been running in production for weeks without issues” is not the same as “low risk to leave untested.” The recent commit history shows multiple substantive changes touching `scripts/debate.py`, including timeout hardening, fallback behavior, synthesis, and critique-mode changes, so the proposal’s deprioritization depends on an unstated premise that operational usage is sufficient validation. That said, given the stated speed-with-guardrails posture and no evidence of failures, this is not a blocker to the recommendation to do #2 first. [EVIDENCED: recent commits affecting `scripts/debate.py` include “Gemini timeout hardening: per-model timeout + automatic fallback,” “Challenge synthesis...,” and “Refine critique mode...” ; `check_test_coverage` reports no tests for `scripts/debate.py`.]
3. [ALTERNATIVE] [ADVISORY]: If you want one extra low-cost security/robustness step while touching test infrastructure, consider adding a tiny smoke test around `debate.py` argument parsing or failure handling for missing `LITELLM_MASTER_KEY`, since `scripts/debate.py` explicitly depends on that environment variable. This does not change the priority order, but it would reduce credential-handling regressions without committing to full coverage. [EVIDENCED: `scripts/debate.py` documents `LITELLM_MASTER_KEY` as required.]

## Concessions
- The proposal correctly prioritizes the only item with a concrete, verified defect: the `## Output` matcher issue exists in `scripts/lint_skills.py`.
- Deferring sim-compiler investment is reasonable because `scripts/sim_compiler.py` exists but the proposal states it is not wired to any automated workflow, so the risk of not building #1/#4 now is low.
- The proposal avoids speculative infrastructure work and keeps scope aligned with current operational relevance.

## Verdict
APPROVE with the caveat that #2 should include regression tests, because it addresses a real known defect in an active hook while the deferred items lack evidence of current pain or security urgency.

---

## Challenger C — Challenges
## Challenges
1. OVER-ENGINEERED [MATERIAL] [COST:TRIVIAL]: Dedicating a build cycle to write 18 test cases for a linter that has "0 observed failures" (EVIDENCED) is a misallocation of effort. The linter was just completed; building a comprehensive test suite before actual usage patterns and edge cases emerge is premature. The known regex false-positive risk (`## Output Contract`) should just be fixed in one line without gating the project on test infrastructure. 
2. RISK [ADVISORY]: Leaving `debate.py` untested while it powers 5 core skills (EVIDENCED) and runs 5-10 times/day (ESTIMATED: assumes daily usage based on proposal text) is an acceptable tradeoff *only* because it is not actively being modified. Any future feature work on the debate engine will immediately inherit this technical debt.

## Concessions
1. Correctly shelves the `sim_compiler.py` IR extraction (Candidate 1) — generating 19 reference models for an unused tool is massive overhead with zero current user value.
2. Correctly recognizes that adding tests to stable, untouched code (`debate.py`) yields no immediate product value.
3. Successfully narrows down a bloated backlog into the smallest actionable unit.

## Verdict
REVISE. Fix the single known regex issue inline (a trivial change), scrap the 18 test cases since the linter has no observed failures, and move directly to product work.

---
