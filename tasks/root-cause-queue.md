# Root Cause Queue

Tracked list of band-aids that shipped with a targeted fix but have a deeper underlying cause. Each entry names the symptom, the quick fix we applied, the root cause, the proper fix, and a priority.

This file is NOT a lessons index. Lessons live in `.claude/rules/*.md`. This file tracks **engineering debt we knowingly took on** so root-cause fixes don't get lost between sessions.

## Entry format

```
## [N]. <Short name>
Status: OPEN / IN_PROGRESS / RESOLVED
Opened: YYYY-MM-DD
Closed: YYYY-MM-DD (if resolved)

**Symptom:**
<what was failing, in concrete terms>

**Quick fix applied:**
<the targeted patch we shipped, with commit/file references>

**Root cause:**
<the underlying design flaw that made the symptom possible>

**Proper fix:**
<what a root-cause solution looks like, in enough detail to execute>

**Why deferred:**
<why we didn't do the proper fix immediately>

**Priority:**
CRITICAL / HIGH / MEDIUM / LOW

**Verification:**
<how we'll know the proper fix landed and the symptom can't recur>
```

---

## 1. Tool-loop parameters have no shared source of truth

Status: RESOLVED
Opened: 2026-04-09
Closed: 2026-04-09 (session 2 — Fix 9 root-cause refactor + linter)

**Symptom:**
`debate.py cmd_challenge` and `_run_claim_verifier` and `cmd_review_panel` all call `llm_tool_loop` with `timeout=60, max_tokens=4096`. On a ~22KB plan review with tools enabled, Opus (claude-opus-4-6) reliably times out all 4 retries and fails. Refine was fixed in a prior session with `timeout=240, max_tokens=16384` and a code comment explicitly warning "60s (the challenge default) was tight even at 4K and is unworkable at 16K" — but the fix was scoped to refine only, leaving the other three call sites known-broken. I crashed into this today when Challenger A (Opus) failed on Plan v2 review with the exact timeout pattern the prior comment predicted.

**Quick fix applied:**
Fix 9 — added module-level constants `TOOL_LOOP_TIMEOUT_SECONDS = 240` and `TOOL_LOOP_MAX_OUTPUT_TOKENS = 16384` (commit pending), then updated `cmd_challenge` (line ~838), `_run_claim_verifier` (line ~1068), and `cmd_review_panel` (line ~2047) to reference the constants instead of inline literals. Verified all three sites by grep and syntax check. On the v2.1 re-challenge, all three challengers completed successfully.

**Root cause:**
There is no single source of truth for tool-loop parameters across subcommands. Every place in `debate.py` that calls `llm_tool_loop` specifies its own `timeout`, `max_tokens`, `max_turns`, `temperature` as inline literals. When a parameter turns out to be wrong for one site, it gets fixed there but the knowledge doesn't propagate. New subcommands added later copy-paste the existing pattern and ship with the same wrong defaults. The refine-only fix in the prior session is the proof — the comment said "unworkable" about challenge but nobody fixed challenge.

**Proper fix:**
1. Define `TOOL_LOOP_DEFAULTS` at module level in `debate.py`:
   ```python
   TOOL_LOOP_DEFAULTS = {
       "timeout": 240,
       "max_tokens": 16384,
       "max_turns": 20,
       "temperature": None,  # use per-model default
   }
   ```
2. Optionally extend to per-role overrides (`research`, `refine`, `challenge`, `verifier`) if different roles legitimately need different caps — but only when there's evidence, not speculation.
3. Every `llm_tool_loop(...)` call site unpacks from the dict: `llm_tool_loop(..., **TOOL_LOOP_DEFAULTS)` or `llm_tool_loop(..., timeout=TOOL_LOOP_DEFAULTS["timeout"], ...)`.
4. Add a linter / test that greps for `llm_tool_loop(` in `debate.py` and fails if any call site specifies `timeout=<number>` or `max_tokens=<number>` as inline integer literals. Enforces that future call sites can't regress.
5. Refine's own values (`REFINE_MAX_OUTPUT_TOKENS`, `REFINE_TIMEOUT_SECONDS`) either derive from `TOOL_LOOP_DEFAULTS` or get explicitly documented as role-specific overrides with a reason.

**Why deferred:**
Fix 9 was applied under time pressure during a live challenge-on-plan workflow. The symptom was blocking progress; the root-cause fix is more invasive and would have delayed the plan review further. The proper fix is now queued as the FIRST commit of Phase 1 — before adding the new `research` subcommand, which will introduce another `llm_tool_loop` call site and would otherwise inherit the copy-paste pattern immediately.

**Priority:**
CRITICAL — address before Phase 1 research subcommand is written.

**Verification:**
- `grep "llm_tool_loop(" scripts/debate.py` shows every call site uses shared config, no inline numeric literals for `timeout` or `max_tokens`
- Test `tests/test_tool_loop_config.py` scans for inline-literal regressions and fails on new violations
- The new `research` subcommand (Phase 1d) is born referencing `TOOL_LOOP_DEFAULTS`, not with a copy-pasted `timeout=240` that someone can later diverge from

---

## 2. `_call_litellm` and `_consolidate_challenges` have inline tuning literals outside the TOOL_LOOP_DEFAULTS surface

Status: RESOLVED
Opened: 2026-04-09
Closed: 2026-04-09 (session 3 — debate-py-bandaid-cleanup commit; LLM_CALL_DEFAULTS introduced, _consolidate_challenges routed through _call_litellm wrapper, linter extended to scan llm_call/_call_litellm sites)

**Symptom:**
Two non-tool-loop LLM call sites in `debate.py` have inline numeric literals for tuning parameters that the Fix 9 root-cause refactor did not cover:
- Line 635: `_call_litellm` — `timeout=300` inline
- Line 1115: `_consolidate_challenges` calling `llm_call` — `max_tokens=4000` inline

Neither value is documented. Why 300 seconds and not 240? Why 4000 tokens and not 16384? Nobody knows — they were whatever the author typed that day.

**Quick fix applied:**
None — these were discovered during the audit after Fix 9 shipped. Logging for follow-up rather than touching them under time pressure.

**Root cause:**
Same class as entry #1. `TOOL_LOOP_DEFAULTS` covers `llm_tool_loop` call sites but not `llm_call` sites. The underlying principle — single source of truth for tuning parameters across call sites — was applied narrowly to one function. There should be a shared config surface for ALL LLM invocations in this file, whether they use the tool loop or not.

**Proper fix:**
1. Extend `TOOL_LOOP_DEFAULTS` to a more general `LLM_CALL_DEFAULTS` dict that covers both tool-loop and non-tool-loop sites, with role-specific overrides where legitimately needed (e.g., `consolidation` might want a smaller max_tokens because it produces a tight summary).
2. Document the rationale for every value in the dict (why 300? why 4000?).
3. Refactor `_call_litellm` and `_consolidate_challenges` to pull from the shared config.
4. Extend `tests/test_tool_loop_config.py` to also scan `llm_call(` call sites for inline literals.

**Why deferred:**
Fix 9 root-cause refactor already landed and is tested. Extending it here is a natural follow-up but not blocking for Phase 1 — the research subcommand uses `llm_tool_loop`, not `llm_call`, so it's born clean under the current narrow guard.

**Priority:**
MEDIUM — not blocking Phase 1, but should land before any additional `llm_call` call sites are added to prevent the same drift pattern from recurring on the non-tool-loop surface.

**Verification:**
- Extended linter scans both `llm_tool_loop(` and `llm_call(` call sites
- `_call_litellm` and `_consolidate_challenges` reference shared config
- Every value in the shared config has an inline comment explaining why

---

## 3. The tuple `(LLMError, urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError)` is duplicated at 8 call sites

Status: RESOLVED
Opened: 2026-04-09
Closed: 2026-04-09 (session 3 — LLM_SAFE_EXCEPTIONS module-level constant; all 8 sites converted to `except LLM_SAFE_EXCEPTIONS as e:`; linter scans for inline tuple regressions)

**Symptom:**
Eight separate `except` clauses in `debate.py` use the identical exception tuple:
```
except (LLMError, urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as e:
```
at lines 861, 954, 1233, 1770, 1878, 1982, 2100, 2179. That's 8 copies of the same tuple. Adding a new recoverable exception type requires editing all 8 sites, and any one that gets missed silently diverges.

**Quick fix applied:**
None — logged during the audit.

**Root cause:**
No shared `LLM_SAFE_EXCEPTIONS = (...)` constant. Each call site re-specifies the full tuple, so the set of "errors we gracefully handle vs errors we let crash" is implicitly defined 8 times instead of once. This is the same class of problem as entry #1 — scattered inline literals instead of a single source of truth, but for exception types instead of timeout numbers.

**Proper fix:**
1. Define at module level:
   ```python
   # Recoverable errors from LLM calls — network, API, parsing, and
   # protocol-level failures. Does NOT include KeyboardInterrupt or
   # SystemExit; those escape upward.
   LLM_SAFE_EXCEPTIONS = (
       LLMError,
       urllib.error.HTTPError,
       urllib.error.URLError,
       TimeoutError,
       RuntimeError,
   )
   ```
2. Replace all 8 call sites with `except LLM_SAFE_EXCEPTIONS as e:`.
3. Add a linter test that scans for the inline tuple pattern and fails if found.

**Why deferred:**
Not urgent — none of the 8 call sites are actively broken. But any new subcommand will copy-paste the inline tuple unless there's a constant to reference. This is pre-emptive debt cleanup, not a fix for a live bug.

**Priority:**
MEDIUM — bundle with entry #2 as a "config surface cleanup" commit.

**Verification:**
- `grep -c "except (LLMError," scripts/debate.py` returns 0
- `grep -c "except LLM_SAFE_EXCEPTIONS" scripts/debate.py` returns 8 (or whatever the correct count is)
- Linter test catches any new inline tuple

---

## 4. `except (LLMError, Exception) as e:` is redundant and unnecessarily broad

Status: RESOLVED (with revision)
Opened: 2026-04-09
Closed: 2026-04-09 (session 3)
Resolution: Per cross-model challenge synthesis (debate-py-bandaid-cleanup, decision A.6/B.6), the broad catch at the 2 affected sites (`_run_claim_verifier`, `_consolidate_challenges`) was retained — both are best-effort enrichment paths that must never crash the pipeline. The redundant `LLMError` was dropped from the tuple (`except Exception as e:`), and `traceback.print_exc(file=sys.stderr)` was added so silent failures stay debuggable. Inline comments document the intent at both sites.

**Symptom:**
Lines 1076 (`_run_claim_verifier`) and 1117 (`_consolidate_challenges`) both have:
```
except (LLMError, Exception) as e:
```
`LLMError` is a subclass of `Exception`, so including it in the tuple is redundant — the `Exception` clause already catches it. More importantly, catching `Exception` broadly means the code silently swallows errors it might want to surface (e.g., bugs in downstream code, AttributeError from typos, ValueError from unexpected data shapes). The developer wanted to catch LLM errors but ended up catching "everything."

**Quick fix applied:**
None — logged during the audit.

**Root cause:**
Pattern copy-paste (someone wanted the catch-all behavior but didn't realize `LLMError` was redundant) OR defensive programming without thinking about what SHOULD escape. The `except Exception:` pattern is listed in `.claude/rules/code-quality-detail.md` as an anti-pattern for a reason.

**Proper fix:**
1. Replace `except (LLMError, Exception)` with `except LLM_SAFE_EXCEPTIONS` (entry #3's shared constant).
2. Audit whether these two functions actually needed the broad catch. If they did (e.g., because they call into arbitrary tool code), keep the broad catch but at least log the traceback instead of just the exception message, so silent failures are debuggable.
3. Ensure `KeyboardInterrupt` and `SystemExit` still escape (they already do, since they inherit from `BaseException`, not `Exception`).

**Why deferred:**
Not urgent. No evidence these call sites are silently eating bugs today. Logged for cleanup as part of the exception-handling pass in entry #3.

**Priority:**
LOW — cosmetic cleanup bundled with entry #3.

**Verification:**
- `grep "except (LLMError, Exception)" scripts/debate.py` returns 0
- Any remaining broad catches are explicitly documented with a reason

---

## 5. `config/debate-models.json` has only a generic `persona_model_map` with no validation

Status: REJECTED
Opened: 2026-04-09 (audit finding, not currently breaking)
Closed: 2026-04-09 (session 3 — rejected by cross-model challenge)
Resolution: Cross-model challenge synthesis (debate-py-bandaid-cleanup, decision item D) UNANIMOUSLY rejected startup validation against LiteLLM. Reasons: (a) adds latency + new failure mode (LiteLLM down → debate.py won't start) — Opus item 4; (b) creates new SSRF-prone trust boundary on `LITELLM_URL` (env-controlled, untrusted at startup) — GPT item 3; (c) duplicates `check-models` subcommand which already does this on demand — Gemini item 2. If we want this safety, add a separate `--validate-models` flag to existing commands; do NOT put it on the startup path. Status: REJECTED, not deferred — the cross-model verdict was that this should not be built.

**Symptom:**
`config/debate-models.json` defines persona → model mapping but has no schema validation. A typo in a model name (`"claude-opus-4-7"` instead of `"claude-opus-4-6"`) would not be caught until runtime. The `check-models` subcommand compares configured models against LiteLLM availability but runs only on demand, not at startup of every subcommand.

**Quick fix applied:**
None.

**Root cause:**
Config files are not validated at debate.py startup. Missing validation on external config is a class of silent-failure bug — the kind where "the test passed but the wrong thing ran."

**Proper fix:**
1. Add a startup validation in `_load_config` that cross-references persona_model_map values against `check-models` results (or against a cached snapshot of LiteLLM's model list).
2. Fail loudly on typos or unavailable models.
3. Add a unit test that validates `config/debate-models.json` against the schema.

**Why deferred:**
Low priority — the current system catches model typos as LLM API errors at first call, which is visible but not pretty.

**Priority:**
LOW — quality-of-life improvement, not blocking anything.

**Verification:**
- A deliberate typo in `persona_model_map` fails `debate.py challenge` at startup with a clear error, not at the first LLM call with a generic HTTP error.

---

## 6. Model name literals scattered across 15+ sites with config-shadow drift

Status: RESOLVED
Opened: 2026-04-09 (audit finding during debate-py-bandaid-cleanup)
Closed: 2026-04-09 (session 3 — bundled into the same cleanup commit)

**Symptom:** Model name strings (`claude-opus-4-6`, `claude-sonnet-4-6`, `gpt-5.4`, `gemini-3.1-pro`) appeared as literals at 15+ sites. Most went through `_load_config()`, but several bypassed it with hardcoded inline fallbacks or argparse defaults. Worst case: `judge` argparse default of `"gpt-5.4"` shadowed `_DEFAULT_JUDGE` and `config["judge_default"]`, making the config path **dead code** — editing `debate-models.json` to set a different judge silently had no effect.

**Resolution:** Argparse defaults for `--model` on both `judge` and `compare` set to `None`. `cmd_judge` falls back to `config["judge_default"]`. `cmd_compare` falls back to a new `config["compare_default"]` key (default `gemini-3.1-pro`, documented as intentionally lighter-weight than the adversarial judge per challenge synthesis A.2). `_consolidate_challenges` function-signature default removed; falls back to `config["verifier_default"]`. The `author_models` set kept inline with a documented intent comment (deployment fact, not runtime configurable, per challenge synthesis A.8).

**Verification:** `tests/test_debate_smoke.py` includes `test_judge_default_is_none_not_hardcoded` and `test_compare_default_is_none_not_hardcoded`.

---

## 7. `_call_litellm` hardcoded `timeout=300` + `temperature=0.7` with no rationale

Status: RESOLVED
Opened: 2026-04-09 (audit finding during debate-py-bandaid-cleanup)
Closed: 2026-04-09 (session 3)

**Symptom:** `_call_litellm` hardcoded `timeout=300, temperature=0.7` with no documentation. `_call_litellm` is the wrapper for judge, verdict, and consolidation calls. The `temperature=0.7` silently overrode the per-model temperature logic used elsewhere (`MODEL_PROMPT_OVERRIDES` tunes Gemini to 1.0 for tool-calling per Fix 4). So Gemini-as-judge ran at 0.7, while Gemini-as-challenger ran at 1.0 — a behavior asymmetry that was never explicitly chosen.

**Resolution:** `_call_litellm` rewritten to read defaults from `LLM_CALL_DEFAULTS`. Per cross-model challenge synthesis decision #4, the asymmetry was preserved as INTENTIONAL (judges should be deterministic at 0.7, challengers benefit from diversity at per-model temperatures). Rationale documented in the `LLM_CALL_DEFAULTS` block comment. New `_challenger_temperature(model)` helper exposes per-model challenger temperatures for paths that explicitly need challenger-mode behavior.

---

## 8. `_call_litellm` vs `llm_call` asymmetric usage

Status: RESOLVED
Opened: 2026-04-09 (audit finding during debate-py-bandaid-cleanup)
Closed: 2026-04-09 (session 3)

**Symptom:** `_call_litellm` was a thin wrapper supplying defaults, but `_consolidate_challenges` called `llm_call` directly, bypassing the wrapper. Asymmetric usage across the same file — no clear "one way to call LLMs from debate.py."

**Resolution:** `_consolidate_challenges` rewritten to call `_call_litellm`. Function signature updated to accept `litellm_url` and `api_key` as required positional args (caller `cmd_judge` already had them in scope). `_call_litellm` is now the canonical entry point for non-tool-loop LLM calls in debate.py. Linter (`tests/test_tool_loop_config.py`) scans both `llm_call` and `_call_litellm` call sites to enforce the wrapper boundary.

---

## Auditing for additional entries

The 2026-04-09 audit pass covered `scripts/debate.py` for: scattered config literals (resolved #2/#7), exception tuple duplication (resolved #3/#4), model name literals (resolved #6), wrapper asymmetry (resolved #8). Patterns NOT yet audited:
- Hardcoded URLs (e.g., `DEFAULT_LITELLM_URL`)
- Inline prompt strings that could move to a prompt registry (deferred — substantially larger refactor, not a band-aid pattern)
- Magic numbers in parsing regexes
- Retry counts (none found in debate.py — retries live in `llm_client.py`)

File new entries here as they're found.
