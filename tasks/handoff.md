# Handoff — 2026-04-13

## Session Focus
LiteLLM graceful degradation: single-model fallback via ANTHROPIC_API_KEY. Full adversarial pipeline (challenge → judge → refine → implement → review → ship).

## Decided
- Fallback transport: urllib to Anthropic Messages API (zero new deps)
- Pre-activation when no LITELLM_MASTER_KEY (skip wasted proxy connection)
- Fallback model configurable via ANTHROPIC_FALLBACK_MODEL env var
- grep --exclude only matches basenames — CI excluded tasks/ dir via --exclude-dir instead

## Implemented
- `scripts/llm_client.py`: fallback transport, connection-refused detection, state management
- `scripts/debate.py`: _load_credentials helper (replaces 10 hard-exit checks), artifact metadata, judge degradation
- `docs/infrastructure.md`: fallback documentation
- `tests/test_llm_client.py`: 18 tests (7 new), all pass
- Cross-model review: pass-with-warnings (0 material after investigation)
- CI banned-terms fix: removed sk-ant- from source files, excluded tasks/ dir

## NOT Finished
- Prior session work still pending: live test of intent router end-to-end, L13/L14/L15 staleness

## Next Session Should
1. Verify CI is green after banned-terms fix (commit 137d904)
2. Resume prior work: test intent router, verify L13/L14/L15 in lessons.md
3. Consider: streamline-rules challenge artifacts exist (tasks/streamline-rules-*.md) but were not acted on

## Key Files Changed
scripts/llm_client.py, scripts/debate.py
docs/infrastructure.md, tests/test_llm_client.py
hooks/pre-commit-banned-terms.sh, .github/workflows/banned-terms.yml
tasks/litellm-fallback-{proposal,challenge,judgment,refined,review-debate,review}.md

## Doc Hygiene Warnings
None
