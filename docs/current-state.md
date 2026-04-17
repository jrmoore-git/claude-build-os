# Current State — 2026-04-16 (Opus 4.7 temperature workaround)

## What Changed This Session
- Restarted `litellm-proxy` Docker container on macmini (image `ghcr.io/berriai/litellm@sha256:59a2736ac848`, started 2026-04-08) to load the `claude-opus-4-7` model entry that was already in `/Users/macmini/openclaw/config/litellm-config.yaml` but not yet hot — `claude-opus-4-7` now appears in `/v1/models`.
- Discovered Opus 4.7 returns HTTP 400 ("temperature is deprecated for this model") on any explicit `temperature` param, and the proxy's `drop_params: true` does NOT strip it for this model on the current image.
- Patched `scripts/llm_client.py:_sdk_call` and `_legacy_call` to omit `temperature` when `model.startswith("claude-opus-4-7")`. `_anthropic_call` left unpatched (fallback model is hardcoded to sonnet — opus-4-7 is unreachable on that path today). Verified across temps 0.0/0.7/0.8/1.0 plus sonnet-4-6, gemini-3.1-pro, gpt-5.4 still receiving the param. 20/20 `tests/test_llm_client.py` pass.
- Captured L40 (Opus 4.7 + drop_params gap) in `tasks/lessons.md` with smoke-test guidance for future model bumps.

## Current Blockers
- **SECURITY: rotate `ANTHROPIC_API_KEY` and `LITELLM_MASTER_KEY`** — both leaked into the assistant transcript via a `cat ~/.zprofile` ssh command earlier in the session. If transcripts are logged/synced anywhere shared, treat as exposed.

## Next Action
Rotate the two leaked keys (Anthropic console + macmini `~/.zprofile` + macmini `~/openclaw/config/litellm.env`), then restart `litellm-proxy` container so it picks up the new `LITELLM_MASTER_KEY`. After that, any pending session can run `/start`.

## Recent Commits
- `92d2e3e` llm_client: omit temperature param for Opus 4.7
- `321323a` Session wrap 2026-04-16 (overnight 3): Opus 4.6 → 4.7 bump
- `d2a0da2` Bump Opus 4.6 → 4.7 across production references
