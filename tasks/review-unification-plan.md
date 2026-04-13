---
scope: "Merge review and review-panel subcommands into a single smart review command"
surfaces_affected: "scripts/debate.py, .claude/rules/reference/debate-invocations.md, .claude/skills/review/SKILL.md, .claude/skills/healthcheck/SKILL.md, .claude/skills/think/SKILL.md, .claude/skills/investigate/SKILL.md, tests/test_debate_smoke.py, tests/run_integration.sh, docs/how-it-works.md, CLAUDE.md"
verification_commands: "python3.11 scripts/debate.py review --help && python3.11 scripts/debate.py review-panel --help && python3.11 -m pytest tests/test_debate_smoke.py -v"
rollback: "git revert <sha>"
review_tier: "Tier 1.5"
verification_evidence: "smoke tests 6/6 pass, review --help shows unified flags, review-panel alias works with deprecation notice, --persona/--model/--models paths verified, mutual exclusion confirmed, syntax check passes"
challenge_skipped: true
---

# Plan: Review Unification

Task brief: `~/debates/tasks/buildos-review-unification.md` (reviewed by Opus, Jarvis, Gemini, GPT).

## Build Order

### 1. Unified argument parser (debate.py)

Replace both `review` and `review-panel` parsers with a single `review` parser.

- Register `review` with all 4 model-selection flags in a mutually exclusive group (`--persona`, `--personas`, `--model`, `--models`)
- Add `--prompt`/`--prompt-file` as mutually exclusive (preserve existing validation)
- Add `--enable-tools`, `--allowed-tools` (available for all model-selection modes)
- Register `review-panel` as hidden alias (`help=argparse.SUPPRESS`) pointing to the same parser

### 2. `_resolve_reviewers` helper (debate.py)

New function that normalizes all 4 flags to a list of `(label, model, use_persona_framing)` tuples:

| Flag | Output |
|------|--------|
| `--persona X` | `[("X", model_from_config, True)]` |
| `--personas X,Y,Z` | `[("X", ..., True), ("Y", ..., True), ("Z", ..., True)]` |
| `--model M` | `[("reviewer", M, False)]` |
| `--models M1,M2` | `[("model-1", M1, False), ("model-2", M2, False)]` |

Comma parsing: split on `,`, strip whitespace, reject empty entries.

### 3. Unified `cmd_review` (debate.py)

Replace both `cmd_review` and `cmd_review_panel` with a single function:

```
if len(reviewers) == 1 and not enable_tools:
    → Single-reviewer path (current cmd_review logic)
    → Output: ## Reviewer\n\n{response}
    → Log phase: "review"
else:
    → Panel path (current cmd_review_panel logic)
    → ThreadPoolExecutor, position randomization, anonymous labels
    → For N=1 with tools: use panel execution but output "## Reviewer" (not "## Reviewer A")
    → Log phase: "review-panel" for N>1, "review" for N=1
```

### 4. Deprecation notice for alias

In the dispatch block, when `args.command == "review-panel"`:
```python
print("NOTE: 'review-panel' is now 'review' — this alias will be removed in a future version.", file=sys.stderr)
```

### 5. Update callers (fan-out)

| File | Change |
|------|--------|
| `.claude/rules/reference/debate-invocations.md` | Rewrite review section: unified `review` with all flags documented |
| `.claude/skills/review/SKILL.md` | `review-panel --models` → `review --models` |
| `.claude/skills/healthcheck/SKILL.md` | Update any `review-panel` references |
| `.claude/skills/think/SKILL.md` | Update any `review-panel` references |
| `.claude/skills/investigate/SKILL.md` | Update any `review-panel` references |
| `tests/test_debate_smoke.py` | Keep `review-panel` in subcommand list (alias still works), add `review --help` test coverage |
| `tests/run_integration.sh` | `review-panel` invocation stays (tests alias path), add comment noting it tests deprecation alias |
| `docs/how-it-works.md` | Update references |
| `CLAUDE.md` | Update infrastructure reference if needed |
| `scripts/debate.py` docstring | Update subcommand list |

### 6. Delete dead code

Remove `cmd_review_panel` function after unified `cmd_review` is confirmed working.

## Files

| File | Action | Scope |
|------|--------|-------|
| `scripts/debate.py` | Modify | Parser, dispatch, new helper, merge functions |
| `.claude/rules/reference/debate-invocations.md` | Modify | Rewrite review/review-panel section |
| `.claude/skills/review/SKILL.md` | Modify | Update invocation examples |
| `.claude/skills/healthcheck/SKILL.md` | Modify | Update references |
| `.claude/skills/think/SKILL.md` | Modify | Update references |
| `.claude/skills/investigate/SKILL.md` | Modify | Update references |
| `tests/test_debate_smoke.py` | Modify | Keep alias test, add unified review test |
| `tests/run_integration.sh` | Modify | Annotate as alias test |
| `docs/how-it-works.md` | Modify | Update references |
| `CLAUDE.md` | Modify | Update infrastructure reference |

## Execution Strategy

**Decision:** sequential
**Reason:** All core changes are in `debate.py` (single file). Caller updates depend on the parser being finalized. Integration test depends on working code.

## Verification

1. `python3.11 scripts/debate.py review --help` — shows all 4 model-selection flags, --enable-tools, --allowed-tools
2. `python3.11 scripts/debate.py review-panel --help` — works (alias), not shown in main --help
3. `python3.11 -m pytest tests/test_debate_smoke.py -v` — all subcommand help tests pass
4. Manual: `debate.py review --model gemini-3.1-pro --prompt "test" --input <file>` — single reviewer, no persona
5. Manual: `debate.py review --models gemini-3.1-pro,gpt-5.4 --prompt "test" --input <file>` — panel mode
6. Manual: `debate.py review-panel --models gemini-3.1-pro --prompt "test" --input <file>` — alias + deprecation notice
