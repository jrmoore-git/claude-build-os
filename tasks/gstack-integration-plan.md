---
scope: "Create scripts/browse.sh wrapper to unblock /design modes that depend on gstack's headless browser"
surfaces_affected: "scripts/browse.sh"
verification_commands: "bash scripts/browse.sh goto 'about:blank' && echo OK"
rollback: "git revert <sha> — single new file, no existing files modified"
review_tier: "Tier 2"
verification_evidence: "status/goto/screenshot all pass, missing binary fails gracefully, empty env var falls back to default, no-args shows help"
challenge_artifact: "tasks/gstack-integration-challenge.md"
challenge_recommendation: "SIMPLIFY"
---
# Plan: gstack-integration

## Build order

1. **Create `scripts/browse.sh`** — thin wrapper (~25 lines) that:
   - Locates the gstack browse binary via `BROWSE_CLI` env var (set by `setup-design-tools.sh`) or fallback to `~/.claude/skills/gstack/browse/dist/browse`
   - Checks binary exists and is executable — exits 1 with clear error if missing
   - Passes all arguments through to the binary unchanged
   - No URL guardrails (posture 2, advisory — the binary itself runs headless Chromium, same trust level as the user opening a browser)

2. **Test** — `bash scripts/browse.sh goto "about:blank"` should return clean, `bash scripts/browse.sh status` should show daemon info

## Files

| File | Action | Scope |
|------|--------|-------|
| `scripts/browse.sh` | Create | Thin wrapper: locate binary, existence check, passthrough |

## What this does NOT do (deferred per challenge)
- No symlinks for `/benchmark`, `/canary`, `/investigate`
- No gstack version upgrade (0.14.5 → 0.16.3)
- No design binary integration
- No changes to `/design` SKILL.md (it already handles `BROWSE_UNAVAILABLE`)

## Execution Strategy

**Decision:** sequential
**Reason:** Single file creation + verification. Below parallelization threshold.

## Verification
```bash
# Binary found and responds
bash scripts/browse.sh goto "about:blank" && echo "BROWSE_READY" || echo "BROWSE_UNAVAILABLE"

# Matches what /design expects
bash scripts/browse.sh screenshot /tmp/test-browse.png && ls -la /tmp/test-browse.png
```
