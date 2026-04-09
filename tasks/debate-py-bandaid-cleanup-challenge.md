---
topic: debate-py-bandaid-cleanup
created: 2026-04-09
review_backend: cross-model
challengers:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
recommendation: REVISE
complexity: medium
---
# debate-py-bandaid-cleanup — Challenge Synthesis

## Verdict

**REVISE** — 2 of 3 challengers (Opus, GPT) returned REVISE; Gemini returned APPROVE conditional on dropping D and including A. All three converge on the same revised scope. The proposal is directionally correct but mis-frames itself as a "pure refactor" and includes one item (D) all three challengers reject.

## Convergent findings (high confidence — 2 or 3 challengers agreed)

### 1. Drop item D (startup config validation against LiteLLM) — UNANIMOUS
All three challengers reject D. Reasons:
- **A**: Adds latency + new failure mode (LiteLLM down → debate.py won't start). The existing `check-models` subcommand already does this on demand.
- **B**: Creates new trust boundary on `LITELLM_URL` (env-controlled, untrusted at startup). SSRF-prone, malformed network responses block all CLI commands.
- **C**: Scope creep. Typos already fail fast and visibly on first invocation.

**Action:** Drop D from scope. If we want any safety here, add a separate `--validate-models` flag to existing commands; do not put it on the startup path.

### 2. The "simplest version" is too simple — A and C
Both flag that the simplest version (B + C-subset only, dropping A) leaves `_call_litellm` (line 634) and `_consolidate_challenges` (line 1111) with their inline literals. If Phase 1b adds new `llm_call` sites — which it almost certainly will — they will inherit or copy-paste those literals. The simplest version fails to neutralize the documented risk.

**Action:** Drop the "simplest version" fallback entirely. The minimum is now A' + B' + C' as described below.

### 3. This is NOT a "pure refactor" — A and B
The proposal claims "no observable behavior change." Both Opus and GPT call this out as wrong:
- `_call_litellm` currently forces `temperature=0.7` for all models (line 634). The `MODEL_PROMPT_OVERRIDES` system tunes Gemini to 1.0 elsewhere — so Gemini-as-judge runs at 0.7, but Gemini-as-challenger runs at 1.0. **Aligning these is a behavior change**, not a refactor.
- The judge timeout of 300 → 240 (or vice versa) is a behavior change.
- Routing `_consolidate_challenges` through the wrapper changes its model resolution path.

**Action:** Re-frame as "behavior normalization of inconsistent defaults," not "pure refactor." Accept that this changes behavior intentionally and add tests that capture the expected new behavior.

### 4. Test coverage is genuinely thin — A and B
`tests/test_tool_loop_config.py` is an AST-based static check, not a behavioral test. `check_test_coverage` confirms `debate.py` has `has_test: false`. Touching ~30 sites in a 2473-line file with zero behavioral coverage is risky.

**Action:** Add smoke tests for the affected command paths (`judge`, `compare`, `review-panel`, `refine`, possibly `consolidate`). A minimum viable smoke test imports `debate.py`, asserts `LLM_SAFE_EXCEPTIONS` is the right tuple, runs `--help` for each subcommand to catch argparse-wiring regressions. ~30-60 minutes of work.

### 5. The wrapper-extraction alternative is structurally cleaner — A and B
Both A (item 5) and B (item 5) suggest a structurally simpler approach: rather than adding `LLM_CALL_DEFAULTS` and extending the linter to a second call surface, **route everything through `_call_litellm`** (or extract its defaults into `llm_client.py`'s `llm_call`). This collapses the trust boundary to one helper instead of touching every call site.

**Action:** Adopt the wrapper-routing approach for item A. Specifically:
- `_consolidate_challenges` calls `llm_call` directly today → should call `_call_litellm` instead.
- `_call_litellm` should pull its defaults from `LLM_CALL_DEFAULTS` (or extended `TOOL_LOOP_DEFAULTS`).
- Linter extension can then be narrower: ban inline literals only at call sites of `llm_call` and `llm_tool_loop` outside `_call_litellm` itself.

## Material findings from individual challengers (worth addressing)

### A.1 — The `_DEFAULT_JUDGE` "drift" framing is technically wrong
Both `_DEFAULT_JUDGE` (line 431) and the argparse default at line 2343 are `"gpt-5.4"` today. There is no current wrong-model call. The actual bug is different and arguably more interesting: **`config["judge_default"]` is dead code**. Because argparse always populates `args.model` with `"gpt-5.4"` (its default), the `args.model or config["judge_default"]` fallback at line 1159 never fires. If someone edits `debate-models.json` to set a different judge, it silently has no effect.

**Action:** Re-frame the bug. The fix is the same (argparse default → `None`, let config resolve), but the framing should be "config-is-dead-code" not "two competing defaults." This actually strengthens the case because dead-code config is a stealth bug where the user *thinks* they configured something but didn't.

### A.2 — `compare` may legitimately differ from `judge`
The `compare` subcommand defaults to `"gemini-3.1-pro"` (line 2414). This is architecturally different from the adversarial `judge` — `compare` is a cheaper side-by-side diff tool, not the truth arbiter. Forcing both through the same default may be wrong.

**Action:** Investigate intent before changing. If `compare` is intentionally cheaper, document it and leave the default in place (or move it to config under its own key, e.g. `compare_default`). Do not blindly route to `judge_default`.

### A.6 / B.6 — Keep the broad `except (LLMError, Exception)` at best-effort sites
Both Opus and GPT flag that lines 1076 (`_run_claim_verifier`) and 1117 (`_consolidate_challenges`) are graceful-degradation paths where the broad catch is intentional. These are optional enrichment steps that should never crash the pipeline. Narrowing to `LLM_SAFE_EXCEPTIONS` could re-introduce crash risk for unexpected exceptions (`KeyError` from malformed parsing, `ValueError`, etc.).

**Action:** Keep the broad catch at these 2 sites. Add traceback logging via `traceback.print_exc(file=sys.stderr)` so silent failures are debuggable. Remove the redundant `LLMError` from the tuple (`except Exception as e:` is sufficient since `LLMError` is a subclass). Document the intent inline.

### A.8 — `author_models` set may not need config indirection
The `author_models = {"claude-opus-4-6", "litellm/claude-opus-4-6"}` set at line 1162 is used to detect self-preference bias when picking a judge. Opus argues this is a fact about the deployment (which model is the IDE author), not a runtime configurable. Routing it through config creates false configurability.

**Action:** Add an inline comment explaining intent. Defer config-ification — the maintenance cost of touching this when the team switches IDE assistants is lower than the cost of misleading config indirection.

### B.7 — Audit completeness was overstated
GPT confirmed the audit but flagged that F (the second sweep pass) is open-ended and risks scope creep. The audit found everything significant; F should be a closeout step (one more focused look) not an open-ended exploration.

**Action:** Replace F with a tighter checklist: verify no NEW inline literals in patterns we already enumerated (timeouts, max_tokens, temperatures, exception tuples, model names). Do not expand to "magic numbers, prompts, URLs."

## Revised scope (post-challenge)

### IN

**B' — Exception constant + traceback logging**
- Define `LLM_SAFE_EXCEPTIONS = (LLMError, urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError)` at module level.
- Replace 8 inline tuple sites with `except LLM_SAFE_EXCEPTIONS`.
- At the 2 broad-catch sites (1076, 1117): keep `except Exception` (drop redundant `LLMError`), add `traceback.print_exc(file=sys.stderr)`, document intent inline.

**A' — Wrapper-routed config (single helper, not two surfaces)**
- Extend `TOOL_LOOP_DEFAULTS` → `LLM_CALL_DEFAULTS` with `timeout`, `max_tokens`, `temperature`, with documented rationale per key.
- `_call_litellm` reads from `LLM_CALL_DEFAULTS`, no inline literals.
- `_consolidate_challenges` routes through `_call_litellm` (or a sibling wrapper if it needs different defaults).
- Per-model temperature: if Gemini-as-judge should use 1.0 like Gemini-as-challenger, that's a per-model override in the helper. Document the choice explicitly.

**C' — Targeted model centralization (narrower than original C)**
- Fix the `_DEFAULT_JUDGE` dead-code bug: argparse default → `None`, let `_load_config()["judge_default"]` resolve.
- Investigate `compare` intent → document or move to its own config key.
- Drop `author_models` config-ification; add intent comment instead.
- Route `_consolidate_challenges(model="claude-sonnet-4-6")` through config.

**E' — Linter extension (narrower)**
- Extend `tests/test_tool_loop_config.py` to scan `llm_call(` for inline `timeout=`, `max_tokens=`, `temperature=` literals.
- Optionally: scan `except (` patterns for the inline tuple form and `(LLMError, Exception)` redundancy.
- Skip the model-name-literal whitelist scanner — too brittle per B.8.

**G — Smoke tests (NEW)**
- Add `tests/test_debate_smoke.py`: import `debate.py`, run `--help` for each subcommand (`challenge`, `judge`, `refine`, `review-panel`, `compare`, `consolidate`), assert no crashes and no argparse errors. ~30-60 min of work.
- Assert `LLM_SAFE_EXCEPTIONS` exists and is the expected tuple.
- Assert `LLM_CALL_DEFAULTS` exists and has documented keys.

### OUT (deferred or rejected)

**D — REJECTED.** Startup config validation against LiteLLM. Drop entirely. If we want it later, add a separate `--validate-models` flag.

**F (open-ended sweep) — REPLACED** with a tight checklist as part of the commit (see B.7).

**Author-model config-ification — DEFERRED** (A.8). Add inline comment, do not route through config.

## Recommendation

**REVISE then proceed.** The revised scope (B' + A' + C' + E' + G) is still landable as one commit before Phase 1b begins. Estimated effort: 3-5 hours total. This is within the same order of magnitude as the original 2-4 hour estimate but with substantially reduced regression risk thanks to the smoke tests and structurally cleaner scope.

The cleanup is still the right move before Phase 1b — all three challengers explicitly endorsed the sequencing argument. The disagreement was on scope shape and risk framing, not on whether to do it.

## Open questions for the user

1. **Do we accept the wrapper-routing approach (A')** or stick with the original "two config surfaces" plan from the proposal? Wrapper is structurally cleaner but requires touching `_consolidate_challenges` more invasively.
2. **Investigate `compare` model intent before touching it?** If yes, that's an extra 5-10 min of git blame + reading. If no, leave the `compare` default as-is and just fix `judge`.
3. **Smoke tests are explicitly new scope.** Accept ~30-60 min for `tests/test_debate_smoke.py`?
4. **Per-model temperature in `_call_litellm`** — should Gemini-as-judge use 1.0 (matching Gemini-as-challenger) or stay at 0.7 (the current judge default)? This is a real behavior choice that needs an explicit decision.

## Artifacts

- Proposal: `tasks/debate-py-bandaid-cleanup-proposal.md`
- Raw findings: `tasks/debate-py-bandaid-cleanup-findings.md`
- This synthesis: `tasks/debate-py-bandaid-cleanup-challenge.md`

## Next

`/plan debate-py-bandaid-cleanup` (after answering the 4 open questions above) → execute → `/review` → commit → start Phase 1b.
