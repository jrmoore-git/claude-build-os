---
topic: debate-py-bandaid-cleanup
created: 2026-04-09
scope: Cleanup of scattered inline literals, exception tuples, and dead-code config paths in scripts/debate.py before Phase 1b adds new LLM call sites. Behavior normalization, not pure refactor.
surfaces_affected:
  - scripts/debate.py
  - tests/test_tool_loop_config.py
  - tests/test_debate_smoke.py
  - config/debate-models.json
verification_commands:
  - python3.11 tests/test_tool_loop_config.py
  - python3.11 tests/test_debate_smoke.py
  - python3.11 -c "import scripts.debate as d; assert hasattr(d, 'LLM_SAFE_EXCEPTIONS'); assert hasattr(d, 'LLM_CALL_DEFAULTS'); print('OK')"
  - python3.11 scripts/debate.py challenge --help
  - python3.11 scripts/debate.py judge --help
  - python3.11 scripts/debate.py refine --help
  - python3.11 scripts/debate.py compare --help
  - python3.11 scripts/debate.py review-panel --help
  - python3.11 scripts/debate.py check-models
rollback: git revert HEAD; or git checkout HEAD~1 -- scripts/debate.py tests/test_tool_loop_config.py tests/test_debate_smoke.py config/debate-models.json
review_tier: cross-model
verification_evidence: pending — populated after execution
---
# Plan — debate.py Band-Aid Cleanup

## Origin

`tasks/debate-py-bandaid-cleanup-challenge.md` (REVISE verdict from 3 cross-model challengers, 2 REVISE + 1 conditional APPROVE). All four open questions decided autonomously per memory `feedback_no_decision_punting.md`.

## Decisions locked in (with model attribution)

| Decision | Choice | Source |
|---|---|---|
| Wrapper-routing for `_call_litellm` | YES | Opus item 5, GPT item 5 (convergent) |
| Investigate `compare` intent | DONE — treat as legitimately lighter | Opus A.2 + git blame (3dd13b0, no rationale comment) |
| Smoke tests for affected commands | YES, ~30-60 min | Opus item 3, GPT item 4 (convergent) |
| `_call_litellm` per-model temperature | Preserve current behavior; introduce `judge_temperature` (0.7) and `challenger_temperature` (per-model) keys; document the asymmetry as intentional | Synthesizing Fix 4 rationale (Gemini tool-calling needs 1.0) with judge-determinism principle |
| Drop item D (startup LiteLLM validation) | YES | UNANIMOUS — Opus item 4, GPT item 3, Gemini item 2 |
| Keep broad `except Exception` at 2 best-effort sites | YES, with traceback logging | Opus item 6, GPT item 6 |
| `author_models` config-ification | DEFER — inline comment only | Opus item 8 |
| Model-name whitelist linter | DROP — too brittle | GPT item 8 |

## Steps

### Step 1 — Add `LLM_SAFE_EXCEPTIONS` constant (B')

**File:** `scripts/debate.py`

1. Add module-level constant near `TOOL_LOOP_DEFAULTS` (around line 1351):
   ```python
   # Recoverable LLM-call errors. Network, API, parsing, and protocol-level
   # failures from llm_client + urllib + the LLM itself. Does NOT include
   # KeyboardInterrupt or SystemExit (those inherit from BaseException and
   # escape upward as intended). Add new exception types here, not at call
   # sites — see tasks/root-cause-queue.md entry #3.
   LLM_SAFE_EXCEPTIONS = (
       LLMError,
       urllib.error.HTTPError,
       urllib.error.URLError,
       TimeoutError,
       RuntimeError,
   )
   ```

2. Replace 8 inline tuple sites with `except LLM_SAFE_EXCEPTIONS as e:`:
   - Lines 861, 954, 1233, 1770, 1878, 1982, 2100, 2179.

3. At the 2 broad-catch sites (1076, 1117), keep `except Exception` but:
   - Drop the redundant `LLMError` from the tuple (`except Exception as e:`).
   - Add `import traceback` near the existing imports if not present.
   - Add `traceback.print_exc(file=sys.stderr)` after the existing print line.
   - Add an inline comment: `# Best-effort enrichment path: never crash the pipeline. Broad catch is intentional; logged via traceback for debugging.`

### Step 2 — `LLM_CALL_DEFAULTS` + wrapper routing (A')

**File:** `scripts/debate.py`

1. Add new module-level constant near `TOOL_LOOP_DEFAULTS`:
   ```python
   # LLM_CALL_DEFAULTS — single source of truth for non-tool-loop llm_call sites
   # in debate.py. Parallel to TOOL_LOOP_DEFAULTS but for one-shot calls
   # (judge, compare, consolidation) instead of tool-using calls.
   #
   # Why this is separate from TOOL_LOOP_DEFAULTS:
   #   - Tool loops need longer timeouts because they make multiple API calls
   #     in series (one per turn).
   #   - One-shot calls don't iterate and can use a tighter timeout.
   #   - Tool loops need higher max_tokens to accommodate tool-call overhead
   #     plus output; one-shot calls only need output budget.
   #
   # Why per-role temperatures:
   #   - Judges should be more deterministic (lower temperature) so verdicts
   #     are reproducible round-to-round.
   #   - Challengers benefit from diversity (higher temperature) for
   #     adversarial coverage. Gemini specifically needs 1.0 per Google's
   #     tool-calling docs (Fix 4).
   #   - The asymmetry between judge-mode and challenger-mode for the same
   #     model is INTENTIONAL — preserved during the 2026-04-09 cleanup.
   LLM_CALL_DEFAULTS = {
       "timeout": 300,        # one-shot calls; tool loops use 240
       "max_tokens": 16384,   # match TOOL_LOOP_DEFAULTS for parity
       "judge_temperature": 0.7,  # all judge models — deterministic verdicts
       "challenger_temperature_default": 0.7,
       "challenger_temperature_per_model": {
           "gemini-3.1-pro": 1.0,  # Fix 4 — Google docs
       },
       "consolidation_max_tokens": 4000,  # consolidation produces tight summaries
   }
   ```

2. Refactor `_call_litellm` (line 632):
   ```python
   def _call_litellm(model, system_prompt, user_content, litellm_url, api_key,
                     temperature=None, max_tokens=None, timeout=None):
       """Call LiteLLM chat completions. Returns response text or raises LLMError.

       Defaults pulled from LLM_CALL_DEFAULTS — caller can override per-call.
       Temperature defaults to LLM_CALL_DEFAULTS["judge_temperature"] (0.7) since
       most _call_litellm callers are judge-mode paths. Challenger paths that
       need per-model temperature must pass it explicitly.
       """
       if temperature is None:
           temperature = LLM_CALL_DEFAULTS["judge_temperature"]
       if max_tokens is None:
           max_tokens = LLM_CALL_DEFAULTS["max_tokens"]
       if timeout is None:
           timeout = LLM_CALL_DEFAULTS["timeout"]
       return llm_call(system_prompt, user_content, model=model,
                       temperature=temperature, max_tokens=max_tokens,
                       timeout=timeout, base_url=litellm_url, api_key=api_key)
   ```

3. Refactor `_consolidate_challenges` (line 1098-1116) to call `_call_litellm` instead of `llm_call` directly. Pass `max_tokens=LLM_CALL_DEFAULTS["consolidation_max_tokens"]`. Note `_consolidate_challenges` does not currently take `litellm_url` and `api_key` as params — needs to either pull from environment or take them as new args. Plan: take them as args, propagate from `cmd_judge` and any other caller.

### Step 3 — Config dead-code fix + targeted model centralization (C')

**File:** `scripts/debate.py`

1. Fix `judge` argparse default (line 2343):
   ```python
   jg.add_argument("--model", default=None,
                    help="Judge model (default: from config[\"judge_default\"], currently gpt-5.4)")
   ```
2. Fix `compare` argparse default (line 2414):
   ```python
   cp.add_argument("--model", default=None,
                    help="Judge model (default: from config[\"compare_default\"], currently gemini-3.1-pro)")
   ```
3. Inside `cmd_compare` (around line 1861), replace `judge_model = args.model or "gemini-3.1-pro"` with:
   ```python
   config = _load_config()
   judge_model = args.model or config.get("compare_default", "gemini-3.1-pro")
   ```
4. Inside `cmd_judge` (look for the existing config lookup near line 1159), ensure `args.model or config["judge_default"]` actually fires now that argparse no longer shadows it. Verify by reading the function.
5. Remove the function-signature default in `_consolidate_challenges` (line 1098):
   ```python
   def _consolidate_challenges(challenge_body, litellm_url, api_key, model=None):
       if model is None:
           config = _load_config()
           model = config.get("verifier_default", "claude-sonnet-4-6")
   ```
6. Add inline comment at `author_models` (line 1162):
   ```python
   # author_models is a fact about the deployment (which model authored the
   # proposal in the IDE), not a runtime configurable. Update here when the
   # team switches their primary coding assistant. Per challenge synthesis
   # 2026-04-09, do NOT route through config — it would create false
   # configurability.
   author_models = {"claude-opus-4-6", "litellm/claude-opus-4-6"}
   ```

**File:** `config/debate-models.json`

7. Add `compare_default` key:
   ```json
   "compare_default": "gemini-3.1-pro"
   ```
8. Verify `judge_default` exists; if not, add `"judge_default": "gpt-5.4"`.
9. Add `verifier_default: "claude-sonnet-4-6"` if not present.

### Step 4 — Linter extension (E')

**File:** `tests/test_tool_loop_config.py`

1. Read the existing AST scanner.
2. Extend it to also scan `llm_call(` call sites for inline `timeout=`, `max_tokens=`, `temperature=` literals. Same pattern as the existing `llm_tool_loop` scanner.
3. Optionally extend to scan `except (` patterns for the inline tuple form. This is a stretch goal; if the AST traversal is awkward, defer to a follow-up.
4. Add positive test fixtures (intentional violations) inline in the test file to prove the linter actually rejects bad patterns. Currently the test only proves the *current* code passes — it doesn't prove the linter would catch a regression.

### Step 5 — Smoke tests (G')

**File:** `tests/test_debate_smoke.py` (NEW)

```python
"""Smoke tests for scripts/debate.py.

Catches argparse-wiring, import, and constant-existence regressions.
NOT a behavioral test — it doesn't run actual LLM calls. Pairs with the AST
linter (test_tool_loop_config.py) which catches static-pattern regressions.

Why this exists: debate.py has 2473 lines and historically had no behavioral
test coverage. The 2026-04-09 cleanup touches ~30 sites; smoke tests are
the cheapest possible regression guard.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEBATE_PY = REPO_ROOT / "scripts" / "debate.py"


def test_constants_exist():
    """LLM_SAFE_EXCEPTIONS and LLM_CALL_DEFAULTS must exist with expected shape."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        import debate
        assert hasattr(debate, "LLM_SAFE_EXCEPTIONS"), "LLM_SAFE_EXCEPTIONS missing"
        assert isinstance(debate.LLM_SAFE_EXCEPTIONS, tuple)
        assert debate.LLMError in debate.LLM_SAFE_EXCEPTIONS

        assert hasattr(debate, "LLM_CALL_DEFAULTS"), "LLM_CALL_DEFAULTS missing"
        for key in ("timeout", "max_tokens", "judge_temperature",
                    "challenger_temperature_default",
                    "challenger_temperature_per_model",
                    "consolidation_max_tokens"):
            assert key in debate.LLM_CALL_DEFAULTS, f"missing key: {key}"

        assert hasattr(debate, "TOOL_LOOP_DEFAULTS"), "TOOL_LOOP_DEFAULTS missing"
    finally:
        sys.path.pop(0)


def _run_help(subcommand):
    result = subprocess.run(
        ["python3.11", str(DEBATE_PY), subcommand, "--help"],
        capture_output=True, text=True, timeout=15,
    )
    return result


def test_subcommand_help_works():
    """Every subcommand must respond to --help without crashing."""
    subcommands = ["challenge", "judge", "refine", "review", "review-panel",
                   "compare", "check-models", "outcome-update", "stats"]
    failures = []
    for sub in subcommands:
        result = _run_help(sub)
        if result.returncode != 0:
            failures.append(f"{sub}: exit {result.returncode}\nstderr: {result.stderr[:500]}")
    assert not failures, "Subcommand --help failures:\n" + "\n".join(failures)


def test_top_level_help_works():
    result = subprocess.run(
        ["python3.11", str(DEBATE_PY), "--help"],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, f"top-level --help failed: {result.stderr[:500]}"


if __name__ == "__main__":
    test_constants_exist()
    print("PASS: constants_exist")
    test_top_level_help_works()
    print("PASS: top_level_help_works")
    test_subcommand_help_works()
    print("PASS: subcommand_help_works")
    print("\nAll smoke tests passed.")
```

### Step 6 — Closeout audit (replaces F)

Before commit:
1. `grep -n 'llm_tool_loop(' scripts/debate.py` — every result must use `**TOOL_LOOP_DEFAULTS` or pull keys from it.
2. `grep -n 'llm_call(' scripts/debate.py` — every result must go through `_call_litellm` or pull from `LLM_CALL_DEFAULTS`.
3. `grep -n 'except (' scripts/debate.py` — every LLM-error tuple must be `LLM_SAFE_EXCEPTIONS`. Bare `except Exception` only at the 2 documented best-effort sites.
4. `grep -n 'gemini-3.1-pro\|gpt-5.4\|claude-sonnet-4-6\|claude-opus-4-6' scripts/debate.py` — every literal must be in a declaration site (`_DEFAULT_*`, `MODEL_PROMPT_OVERRIDES`, `author_models`) or a help string.
5. Run all 8 verification commands in the frontmatter.
6. Update `tasks/root-cause-queue.md`: mark #1 RESOLVED (add closure date), mark #2/#3/#4 RESOLVED, leave #5 OPEN with note "deferred per cleanup synthesis 2026-04-09 — startup validation rejected, see tasks/debate-py-bandaid-cleanup-challenge.md item D".
7. Update `tasks/handoff.md` and `docs/current-state.md` per the Commit Doc Update Rule.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Smoke tests don't catch behavioral regressions in actual LLM calls | Smoke tests are explicitly NOT a substitute for production validation. Run a real `/challenge` invocation post-commit before declaring done. |
| `_consolidate_challenges` signature change ripples to callers | Grep for all callers, update signatures atomically in the same commit. |
| AST linter extension breaks the existing test | Add new positive-fixture tests first; verify both old and new patterns fail correctly before running against `debate.py`. |
| `_call_litellm` temperature default change affects judge output deterministically | Preserve current 0.7 default (no change). Per-model challenger temperatures only used when caller passes them explicitly. |
| `compare_default` config key not loaded by older config files | `_load_config` already supplies defaults via `defaults` dict — add `compare_default` there too. |

## Definition of done

- [ ] All 8 verification commands pass.
- [ ] `grep` audit (Step 6) returns zero unauthorized inline literals.
- [ ] `tests/test_debate_smoke.py` exists, passes, and is registered (callable as `python3.11 tests/test_debate_smoke.py`).
- [ ] `tests/test_tool_loop_config.py` extended with `llm_call(` scanner; passes.
- [ ] `tasks/root-cause-queue.md` updated with closures.
- [ ] `tasks/handoff.md` and `docs/current-state.md` updated.
- [ ] Cross-model `/review` run on the diff.
- [ ] Commit message follows the Commit Doc Update Rule with explicit doc updates listed.
- [ ] Real post-commit validation: run `python3.11 scripts/debate.py challenge --help` and one actual challenge invocation against an existing proposal to catch import-time regressions the smoke tests might miss.

## Estimated effort

- Step 1 (B'): ~30 min
- Step 2 (A'): ~60 min (signature changes ripple)
- Step 3 (C'): ~30 min
- Step 4 (E'): ~30 min
- Step 5 (G'): ~30 min
- Step 6 (closeout): ~30 min
- `/review` + commit + doc updates: ~60 min

**Total: ~4 hours.** Within the original 3-5 hour estimate.
