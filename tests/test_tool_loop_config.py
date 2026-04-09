"""Guard test for root-cause queue entries #1, #2, #3.

Scans scripts/debate.py for LLM-call patterns that should reference shared
config instead of inline literals. Three scanners:

1. llm_tool_loop call sites: timeout/max_tokens/max_turns must NOT be inline
   numeric literals (entry #1 — Fix 9, the original failure mode).

2. _call_litellm and llm_call call sites: timeout/max_tokens/temperature must
   NOT be inline numeric literals (entry #2 — same drift pattern, non-tool-
   loop call surface).

3. except clauses: the inline tuple
   `(LLMError, urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
   RuntimeError)` must NOT appear; use the LLM_SAFE_EXCEPTIONS constant
   (entry #3).

Rationale: the original Fix 9 failure mode was that cmd_challenge,
_run_claim_verifier, and cmd_review_panel all shipped with hand-tuned
`timeout=60, max_tokens=4096` inline literals while refine had already been
fixed to 240/16384. No shared config meant the fix didn't propagate. This
test is the structural enforcement that prevents the same class of bug from
recurring across the entire LLM-call surface — tool loops, one-shot calls,
and exception handling.

Two call sites are explicitly allowed to use bare `except Exception` (not
LLM_SAFE_EXCEPTIONS): _run_claim_verifier and _consolidate_challenges, both
documented as best-effort enrichment paths. The scanner allows bare
`except Exception` (no tuple) but rejects the inline tuple form.

Run with: python3.11 tests/test_tool_loop_config.py
Exit 0 = all call sites reference shared config / constants.
Exit 1 = at least one violation found.
"""

import ast
import sys
from pathlib import Path

TARGET_FILE = Path(__file__).resolve().parent.parent / "scripts" / "debate.py"

# Kwargs that must NOT be inline numeric literals at LLM call sites.
# `temperature` is guarded on BOTH surfaces because per-model challenger
# temperatures must come from LLM_CALL_DEFAULTS or _challenger_temperature(),
# never from inline constants. Caught by Gemini in 2026-04-09 cross-model
# code review (review-debate.md, advisory finding C).
TOOL_LOOP_GUARDED_KWARGS = {"timeout", "max_tokens", "max_turns", "temperature"}
LLM_CALL_GUARDED_KWARGS = {"timeout", "max_tokens", "temperature"}

# Function names whose call sites we scan for inline literals.
TOOL_LOOP_FUNCS = {"llm_tool_loop"}
# Note: _call_litellm is the wrapper — its OWN body is allowed to read from
# LLM_CALL_DEFAULTS, but external CALL SITES of _call_litellm should not pass
# inline literals. llm_call is the underlying client.
LLM_CALL_FUNCS = {"_call_litellm", "llm_call"}

# Exception tuple pattern (entry #3) — the exact inline tuple we want to ban.
BANNED_EXCEPTION_NAMES = {
    "LLMError",
    "HTTPError",
    "URLError",
    "TimeoutError",
    "RuntimeError",
}


def _is_inline_literal(val: ast.AST) -> bool:
    """True if val is an inline int/float Constant (rejected at call sites)."""
    return isinstance(val, ast.Constant) and isinstance(val.value, (int, float))


def _matches_call(node: ast.Call, target_names: set) -> bool:
    """True if node calls any function in target_names."""
    func = node.func
    if isinstance(func, ast.Name) and func.id in target_names:
        return True
    if isinstance(func, ast.Attribute) and func.attr in target_names:
        return True
    return False


def _scan_call_kwargs(tree: ast.AST, target_funcs: set, guarded_kwargs: set, label: str):
    """Find inline-literal violations at call sites of target_funcs."""
    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not _matches_call(node, target_funcs):
            continue
        for kw in node.keywords:
            if kw.arg not in guarded_kwargs:
                continue
            if _is_inline_literal(kw.value):
                violations.append((kw.lineno, label, kw.arg, kw.value.value))
    return violations


def _scan_exception_tuples(tree: ast.AST):
    """Find `except (...)` clauses containing the banned LLM-error tuple."""
    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        exc_type = node.type
        if not isinstance(exc_type, ast.Tuple):
            continue
        # Collect attribute names like LLMError, HTTPError, URLError, etc.
        names_in_tuple = set()
        for elt in exc_type.elts:
            if isinstance(elt, ast.Name):
                names_in_tuple.add(elt.id)
            elif isinstance(elt, ast.Attribute):
                names_in_tuple.add(elt.attr)
        # Violation if the tuple contains LLMError + at least 2 of the
        # network/runtime error types — that's the inline-tuple pattern from
        # entry #3. Also flags the (LLMError, Exception) redundancy from #4.
        if "LLMError" in names_in_tuple:
            other_banned = (names_in_tuple & BANNED_EXCEPTION_NAMES) - {"LLMError"}
            has_exception = "Exception" in names_in_tuple
            if len(other_banned) >= 2 or has_exception:
                violations.append((node.lineno, sorted(names_in_tuple)))
    return violations


def find_violations(path: Path):
    source = path.read_text()
    tree = ast.parse(source)

    violations = {
        "tool_loop_literals": _scan_call_kwargs(
            tree, TOOL_LOOP_FUNCS, TOOL_LOOP_GUARDED_KWARGS, "llm_tool_loop"
        ),
        "llm_call_literals": _scan_call_kwargs(
            tree, LLM_CALL_FUNCS, LLM_CALL_GUARDED_KWARGS, "llm_call/_call_litellm"
        ),
        "exception_tuples": _scan_exception_tuples(tree),
    }
    return violations


def _scan_self_test():
    """Positive-fixture test: prove the linter actually catches violations.

    Builds a synthetic AST with a known-bad pattern and confirms each scanner
    flags it. Without this, we only know the scanner doesn't false-positive
    on the current code — we don't know it would catch a regression.
    """
    bad_source = '''
def bad_tool_loop():
    llm_tool_loop(timeout=60, max_tokens=4096, max_turns=10, temperature=0.7)

def bad_llm_call():
    llm_call(prompt, timeout=300, max_tokens=4000, temperature=0.7)
    _call_litellm(model, sp, uc, url, key, timeout=300)

def bad_exception():
    try:
        pass
    except (LLMError, urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as e:
        pass

def bad_redundant_exception():
    try:
        pass
    except (LLMError, Exception) as e:
        pass
'''
    tree = ast.parse(bad_source)
    tl_v = _scan_call_kwargs(tree, TOOL_LOOP_FUNCS, TOOL_LOOP_GUARDED_KWARGS, "x")
    lc_v = _scan_call_kwargs(tree, LLM_CALL_FUNCS, LLM_CALL_GUARDED_KWARGS, "x")
    ex_v = _scan_exception_tuples(tree)

    assert len(tl_v) == 4, f"linter self-test: tool-loop scanner missed; found {len(tl_v)}/4"
    assert len(lc_v) == 4, f"linter self-test: llm_call scanner missed; found {len(lc_v)}/4"
    assert len(ex_v) == 2, f"linter self-test: exception scanner missed; found {len(ex_v)}/2"


def main():
    if not TARGET_FILE.exists():
        print(f"ERROR: target file not found: {TARGET_FILE}", file=sys.stderr)
        return 2

    # Self-test the linter before running it on the real code.
    try:
        _scan_self_test()
    except AssertionError as e:
        print(f"LINTER SELF-TEST FAILED: {e}", file=sys.stderr)
        return 2

    violations = find_violations(TARGET_FILE)
    total = sum(len(v) for v in violations.values())

    if total == 0:
        print(f"OK: {TARGET_FILE.name} clean — "
              f"no inline literals at LLM call sites and no banned exception tuples")
        print("    Scanners: tool-loop kwargs, llm_call/_call_litellm kwargs, exception tuples")
        return 0

    print(f"FAIL: {total} violation(s) in {TARGET_FILE.name}:", file=sys.stderr)

    for lineno, label, kwarg, value in violations["tool_loop_literals"]:
        print(f"  line {lineno}: {label} {kwarg}={value!r} — should reference "
              f"TOOL_LOOP_DEFAULTS", file=sys.stderr)

    for lineno, label, kwarg, value in violations["llm_call_literals"]:
        print(f"  line {lineno}: {label} {kwarg}={value!r} — should reference "
              f"LLM_CALL_DEFAULTS or pass through _call_litellm", file=sys.stderr)

    for lineno, names in violations["exception_tuples"]:
        print(f"  line {lineno}: inline exception tuple {names} — should use "
              f"LLM_SAFE_EXCEPTIONS (or bare `except Exception` if it's a "
              f"documented best-effort path)", file=sys.stderr)

    print("", file=sys.stderr)
    print("Fix: see tasks/root-cause-queue.md entries #1-#4 and "
          "tasks/debate-py-bandaid-cleanup-challenge.md for the rationale.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
