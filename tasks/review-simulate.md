# Simulation Report: /review
Mode: smoke-test
Date: 2026-04-15
Target: .claude/skills/review/SKILL.md

## Summary
The /review SKILL.md contains 13 fenced bash blocks across 7 sections (code review, document review, QA mode). 7 blocks executed successfully (PASS), 1 returned non-zero due to empty grep results (PASS -- expected behavior), and 5 were SKIPPED due to placeholder variables (`<topic>`, `<temp file>`, `$POSTURE`). All referenced scripts and infrastructure files exist on disk.

## Results

| # | Block | Section | Status | Detail |
|---|-------|---------|--------|--------|
| 1 | `git diff --name-only HEAD; git diff --cached --name-only; git diff --name-only` | Step 1: Detect changes | PASS | Exit 0. No uncommitted changes (clean tree). |
| 2 | `git diff HEAD -- ':!.env' ...; git diff --cached -- ':!.env' ...` | Step 3: Get the diff | PASS | Exit 0. Empty output (clean tree). Secret exclusion pathspecs parse correctly. |
| 3 | `test -f tasks/<topic>-refined.md && echo "found" \|\| echo "none"` | Step 4: Check for spec artifact | SKIPPED | Contains `<topic>` placeholder. Cannot resolve without runtime context. |
| 4 | `python3.11 scripts/enrich_context.py --proposal <temp summary file> --scope review` | Step 4.5: Enrich context | SKIPPED | Contains `<temp summary file>` placeholder. |
| 5 | `python3.11 scripts/debate.py --security-posture $POSTURE challenge ...` | Step 5: Run cross-model review | SKIPPED | Contains `<temp file with diff + spec context>`, `<topic>`, and `$POSTURE` placeholders. Would require actual diff content, API keys, and topic resolution. |
| 6 | `python3.11 scripts/debate.py review --models ... --prompt-file <temp eval prompt> --input <path to document>` | Document Review Step 3 | SKIPPED | Contains `<temp eval prompt>` and `<path to document>` placeholders. |
| 7 | `ls -t tasks/*-plan.md tasks/*-review.md 2>/dev/null \| head -5` | QA Step 1: Detect scope | PASS | Exit 0. Found 5 artifacts (simulate-skill-review.md, simulate-skill-plan.md, debate-engine-upgrades-plan.md, refine-critique-mode-review.md, review-unification-plan.md). |
| 8 | `cat tasks/<topic>-plan.md 2>/dev/null` | QA Step 2: Load plan | SKIPPED | Contains `<topic>` placeholder. |
| 9 | `cat tasks/<topic>-review.md 2>/dev/null` | QA Step 2: Load review | SKIPPED | Contains `<topic>` placeholder. |
| 10 | `git diff HEAD --stat && git diff HEAD` | QA Step 2: Get diff | PASS | Exit 0. Empty output (clean tree). |
| 11 | `ls tests/test_*.py` | QA Step 3: Test coverage | PASS | Exit 0. Found 21 test files. |
| 12 | `git diff HEAD -- '*.py' \| grep -E '^\+.*def \|^\-.*def '` | QA Step 3: Regression risk | PASS | Exit 1. Expected: grep returns 1 when no matches (no changed functions in clean tree). |
| 13 | `bash tests/run_all.sh` | QA Step 4: Run tests | PASS | Exit 0. 562 pytest tests passed in 3.53s. 6 smoke tests passed. |

**Totals:** 7 PASS, 0 FAIL, 0 INCONCLUSIVE, 6 SKIPPED

## File Path Check
| Path | Exists | Note |
|------|--------|------|
| `scripts/debate.py` | Yes | Main debate engine. Has `challenge`, `review`, `judge`, `refine`, `explore`, `pressure-test`, `pre-mortem` subcommands. |
| `scripts/enrich_context.py` | Yes | Context enrichment for governance data. |
| `tests/run_all.sh` | Yes | Executable. Runs pytest + smoke tests. |
| `config/debate-models.json` | Yes | Model config for debate personas. |
| `tasks/` | Yes | Artifact output directory. |
| `tests/` | Yes | Test directory with 21 test files. |
| `tasks/<topic>-refined.md` | N/A | Template path. No refined artifacts currently on disk. |
| `tasks/<topic>-review-debate.md` | N/A | Template path. No review-debate artifacts currently on disk. |
| `tasks/<topic>-qa.md` | N/A | Template path. No QA artifacts currently on disk. |
| `tasks/<topic>-review-x.md` | N/A | Template path. No second-opinion artifacts currently on disk. |
| `tasks/<topic>-review-iterations.md` | N/A | Template path. No fix-loop iteration artifacts currently on disk. |

## Issues Found
| # | Issue | Severity | Evidence | Suggested Fix |
|---|-------|----------|----------|---------------|
| 1 | Block 12 grep exits 1 on no matches -- skill must handle this | Low | `grep -E` returns exit 1 when no lines match, which is normal for clean trees. The skill procedure does not explicitly note this. | Add `|| true` or document that empty grep output (exit 1) is expected when no function signatures changed. Alternatively, the skill's procedural text says "Check for changed function signatures" which implies reading the output, not checking exit code -- so this is likely fine in practice. |
| 2 | 6 of 13 blocks use `<topic>` or `<temp file>` placeholders that cannot be resolved without runtime context | Info | Blocks 3, 4, 5, 6, 8, 9 all require topic inference or temp file creation from prior steps. | Expected for a procedural skill -- these blocks are templates, not standalone commands. The skill's step-by-step procedure resolves these at runtime. |
| 3 | debate.py `challenge` subcommand used for code review instead of `review` | Info | Block 5 calls `debate.py challenge` with `--system-prompt` override to repurpose the challenge infrastructure for review. Block 6 (document review) correctly uses `debate.py review --models`. | Intentional design -- the `--system-prompt` override replaces the adversarial challenge prompt with a review-specific prompt. Works but is a non-obvious usage of the challenge subcommand. |
| 4 | `--system-prompt` flag exists but not visible in top-level help | Low | The skill passes `--system-prompt` to the `challenge` subcommand (Block 5). Verified via `debate.py challenge --help` -- the flag exists and accepts a string to override the default adversarial system prompt. Not shown in top-level `--help` (only in subcommand help), which is normal argparse behavior. | No fix needed. Flag confirmed valid. |

## Fidelity
Simulation fidelity: PARTIAL
The 7 executed blocks all target git and filesystem operations that work on any repo state (including clean trees). The 6 skipped blocks represent the core review logic (debate.py calls, enrichment, spec checking) which require runtime context (topic resolution, temp files with actual diffs, API keys for external models). A full fidelity test would require: (a) staged code changes to produce a real diff, (b) a resolved topic name, (c) working LiteLLM API keys for cross-model calls. The test suite (562 tests passing) provides indirect coverage of the underlying debate.py and enrich_context.py infrastructure.

## Metadata
Duration: 49s
Blocks extracted: 13
Blocks executed: 7
Blocks skipped: 6
