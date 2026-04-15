---
topic: next-build-priorities
created: 2026-04-15
---
# Next Build Priorities — Post-Linter

## Problem
Session 10 completed the skill linter (22/22 skills conforming, hook wired). Four items are carried forward from prior sessions. Need to decide which, if any, are worth building next — or whether infrastructure investment should pause in favor of product work.

## Candidates

### 1. Wire IR extraction into pre-commit diff
- `sim_compiler.py` extracts structured interaction models (states, transitions, branching) from SKILL.md procedures
- Would catch procedure-level drift (logic changes, lost branching paths) that the section-level linter misses
- Identified as "differentiated asset" in sessions 7-8 (novel technique — no tools extract structured IRs from agent procedures)
- Requires: generate reference IRs for 19 more skills (only 3 exist), define "breaking change" criteria, build diff logic

### 2. Linter hardening
- Tighten `## Output` regex (current regex `^##\s+Output\b` false-matches `## Output Contract`)
- Add automated tests for `lint_skills.py` (9 checks, each needs positive/negative cases)
- Small scope, prevents regressions, makes linter trustworthy for pre-commit gate promotion

### 3. debate.py test coverage
- Cross-model engine powering /challenge, /review, /polish, /explore, /pressure-test (5+ skills)
- Currently 0 tests
- Has been running in production for weeks without issues
- Not being actively modified

### 4. sim-compiler /review
- 4 scripts built in sessions 7-8: sim_compiler.py, sim_persona_gen.py, sim_rubric_gen.py, sim_driver.py
- Sessions 7-8 decided persona_gen, rubric_gen, driver are commodity (DeepEval/LangSmith/MLflow all have equivalents)
- Only sim_compiler.py (IR extraction) was kept as worth investment
- Never reviewed via /review

## Proposed Approach
Build #2 (linter hardening) as the only concrete, small-scoped item with a known issue. Skip the rest until they become relevant to active work.

## Simplest Version
Fix the regex, write ~18 test cases (9 checks x pass/fail), done.

### Current System Failures
- No failures observed from the linter yet (just built). The `## Output` regex issue is a known false-positive risk identified during self-review (advisory finding).
- No failures from debate.py (stable, running weeks).
- No failures from sim-compiler (mostly unused).
- IR extraction has never been wired, so no failures from absence.

### Operational Context
- Linter runs on every SKILL.md write/edit via PostToolUse hook
- debate.py runs ~5-10 times/day across challenge, review, explore, polish, pressure-test
- sim_compiler.py is not wired to any hook or automated workflow
- 22 skills conform to canonical spec as of session 10

### Baseline Performance
- Linter: 22/22 skills passing, 0 violations, 9 validation checks, tier classification working
- debate.py: functional, no test coverage, no recent bugs
- sim-compiler: built but unused in production workflows
