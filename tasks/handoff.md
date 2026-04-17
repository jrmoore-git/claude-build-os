# Handoff — 2026-04-16 (Opus 4.7 temperature workaround)

## Session Focus
Get the Opus 4.7 bump (commit 321323a) actually working end-to-end. The model entry was in the proxy config but the running container hadn't reloaded it; once reloaded, requests still failed because Opus 4.7 deprecates `temperature` and the proxy's `drop_params` doesn't yet strip it for this model.

## Decided
- Patch `_sdk_call` and `_legacy_call` inline (no helper) — two call sites with a one-line check; helper would be premature abstraction.
- Skip `_anthropic_call` — fallback model is hardcoded to `claude-sonnet-4-20250514`, opus-4-7 unreachable on that path today.
- Tag the patch `[TRIVIAL]` and self-review (single-model through 3 lenses) rather than running cross-model debate on an 8-line defensive patch.

## Implemented
- `scripts/llm_client.py` — conditional skip of `temperature` for `claude-opus-4-7` in both `_sdk_call` and `_legacy_call` (commit `92d2e3e`).
- `tasks/opus-47-temperature-review.md` — review artifact, status `passed`.
- `tasks/lessons.md` — L40 captures the gotcha with smoke-test guidance for future model bumps.
- macmini `litellm-proxy` Docker container restarted; `claude-opus-4-7` now in `/v1/models`.

## NOT Finished
- **Rotate `ANTHROPIC_API_KEY` and `LITELLM_MASTER_KEY`** — both leaked into the assistant transcript via `cat ~/.zprofile`. Rotate at Anthropic console, regenerate `LITELLM_MASTER_KEY`, update macmini `~/.zprofile` + `~/openclaw/config/litellm.env`, then restart the proxy container.
- The patch is temporary. When LiteLLM proxy gains `drop_params` support for opus-4-7 (likely via image bump from current SHA `59a2736ac848` dated 2026-04-08), the conditional and comments in `_sdk_call` / `_legacy_call` should be removed.

## Next Session Should
1. Rotate the two leaked keys (Anthropic console + macmini files + container restart).
2. Verify `debate.py judge` runs cleanly against opus-4-7 via the standard pipeline.
3. (Lower priority) Watch for litellm release notes adding opus-4-7 `drop_params` support; revert the workaround when it lands.

## Key Files Changed
- `scripts/llm_client.py` (patched, committed as 92d2e3e)
- `tasks/opus-47-temperature-review.md` (new, untracked)
- `tasks/lessons.md` (L40 added, untracked)
- `docs/current-state.md`, `tasks/handoff.md`, `tasks/session-log.md` (this wrap)

## Doc Hygiene Warnings
None. Lessons at 10 active (well under 30). Decisions.md not updated — no architectural decision this session.
