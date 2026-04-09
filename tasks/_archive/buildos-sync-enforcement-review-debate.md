---
debate_id: buildos-sync-enforcement-review-debate
created: 2026-04-03T21:46:11-0700
mapping:
  A: gemini-3.1-pro
  B: gpt-5.4
  C: claude-opus-4-6
---
# buildos-sync-enforcement-review-debate — Challenger Reviews

## Challenger A — Challenges
Here is the review of the BuildOS sync enforcement changes.

### PM/Acceptance
- **[MATERIAL]** In `deploy_all.sh`, the newly added Step 6 correctly handles the `buildos-sync.sh` exit codes, specifically catching exit code 1 (banned-terms) to block deployment while allowing other failures (like network issues) to merely warn. This ensures we don't leak sensitive data to the upstream generic repo while keeping deployments resilient.
- **[ADVISORY]** The `SKILL.md` update correctly promotes Gate 8 to a HARD gate and updates the dashboard template. Ensure that the AI parsing logic in the actual `/ship` implementation correctly identifies the "0 changed, 0 new, 0 missing" string as specified.

### Security
- **[MATERIAL]** Blocking the deploy on `SYNC_EXIT -eq 1` (banned-terms scan failure) is a crucial security control. It ensures that proprietary or sensitive terms accidentally introduced into generic framework files are caught before they are pushed to the upstream repository.

### Architecture
- **[ADVISORY]** The step numbering in `deploy_all.sh` was correctly updated from `/5` to `/6` across all echo statements. Updating `STEPS_COMPLETED` at each phase maintains accurate state tracking if the script fails midway.

---

## Challenger B — Challenges
## PM/Acceptance

- [MATERIAL] The implementation does not match the new documented acceptance criteria that BuildOS sync is now a HARD gate and should block deploy when repos are out of sync. In `SKILL.md`, `/ship` now says “If any files are changed, new, or missing — repos are out of sync. Block deploy,” and explicitly suggests `deploy_all.sh` because it “includes sync as Step 6.” But in `scripts/deploy_all.sh`, Step 6 treats most sync failures as non-blocking and continues the deploy for anything except exit code `1`. That means the standard deployment path can still succeed while BuildOS remains unsynced, which contradicts the promoted HARD gate behavior.

- [MATERIAL] The failure semantics are underspecified and likely inconsistent with the documented gate. The doc gate is based on drift detection from `buildos-sync.sh --dry-run` (“changed/new/missing”), but `deploy_all.sh` only branches on the sync script’s exit code and assumes only exit code `1` is blocking. If drift, dirty repo state, push rejection, or other sync-preventing conditions do not map exactly to `1`, deploy will continue despite the gate being documented as blocking. Either the sync script must expose explicit blocking exit codes for all “out of sync” conditions, or `deploy_all.sh` must perform and enforce the documented dry-run gate before any deploy work.

## Security

- [ADVISORY] Relying on a single magic exit code (`1`) for the “security gate” is brittle unless `buildos-sync.sh` has a stable, documented exit-code contract. If that script changes or already uses `1` for generic failures, you may either over-block or under-block releases. Consider defining named exit codes and documenting them alongside the HARD gate.

## Architecture

- [ADVISORY] The current ordering makes sync happen after all deployment and test steps. If BuildOS sync is a release gate, enforcing it only at the very end causes partial rollout before the final gate is evaluated. That is especially awkward now that `/ship` presents sync as a prerequisite to ship readiness. Consider moving the sync pre-check earlier, or splitting it into: (1) a preflight `--dry-run` hard gate before deployment, and (2) a post-deploy `--push` action only after all other gates pass.

- [ADVISORY] `deploy_all.sh` now carries policy knowledge about specific `buildos-sync.sh` failure classes (“banned-terms scan failed” vs “network, dirty repo”). That couples the deploy orchestrator to internal sync-script behavior. A cleaner design is for `buildos-sync.sh` to expose a clear machine-readable outcome model, with `deploy_all.sh` simply enforcing “blocking” vs “non-blocking” outcomes.

---

## Challenger C — Challenges
# Code Review: BuildOS Sync Enforcement

## PM/Acceptance

**[MATERIAL] Exit code 1 semantics are fragile and undocumented as a contract**

The error handling in Step 6 assigns specific meaning to exit code 1 ("banned-terms scan failed") vs. other codes. This assumes `buildos-sync.sh` has a stable, documented exit code contract. If that script uses `set -e` or calls subcommands that happen to exit with code 1 for unrelated reasons (e.g., `grep` returning 1 for "no match", `diff` returning 1 for "files differ"), the deploy will incorrectly hard-fail as a "banned-terms" violation. This needs to be verified against the actual exit code behavior of `buildos-sync.sh`, or the sync script needs to use a distinctive exit code (e.g., 78 or another non-colliding value).

**[ADVISORY] SOFT gate list may be incomplete or inconsistent**

The updated note says "SOFT gates (QA dimensions, docs, git) are advisory" — but the original Gate 8 description was the only gate explicitly labeled SOFT. Confirm that the QA dimensions gate is indeed formally labeled SOFT somewhere; otherwise this note introduces an implicit demotion without a corresponding gate definition change.

**[ADVISORY] The "Verify fail" fix suggestion was added to the blocking section but isn't part of this diff's stated purpose**

The addition of `- Verify fail → "Adversarial probe failed: <detail>. Fix and /ship again."` and the note about verification never being bypassed appear to be unrelated fixes bundled into this change. Not a problem per se, but worth calling out for traceability — these should ideally be in their own commit or at minimum noted in the PR description.

## Security

**[MATERIAL] Non-security sync failures silently degrade the HARD gate promise**

The SKILL.md now declares BuildOS sync as a **HARD** gate that must "block deploy." But `deploy_all.sh` only blocks on exit code 1 and explicitly continues on all other failures (`"deploy continues, sync manually later"`). This means running `/ship` via `deploy_all.sh` can succeed with BuildOS out of sync — directly contradicting the HARD gate contract. Either:
1. The `/ship` gate check (which runs `--dry-run` separately) is the actual enforcement point and `deploy_all.sh` is best-effort, in which case this should be documented clearly, or
2. `deploy_all.sh` should fail on any sync failure to honor the HARD gate.

As written, a developer reading SKILL.md will believe sync is enforced, but a network blip during deploy silently skips it.

**[ADVISORY] `--push` runs after deploy is already live**

Step 6 runs *after* the gateway, MCP server, and frontend are already deployed and tests have passed. If the sync push fails with a security gate (banned terms), the deploy has already gone live. The HARD gate in `/ship` (which runs `--dry-run` *before* deploy) is the real pre-deploy check, so this ordering is probably fine in practice — but it means `deploy_all.sh` alone doesn't provide the pre-deploy guarantee that SKILL.md implies.

## Architecture

**[MATERIAL] `STEPS_COMPLETED` was not updated after Step 5 in the original code — this diff fixes it but doesn't call it out**

The addition of `STEPS_COMPLETED="gateway, mcp-server, frontend, app-tests, contract-tests"` after Step 5 is a bug fix (previously `STEPS_COMPLETED` still said `"gateway, mcp-server, frontend, app-tests"` after contract tests ran). This is good but should be noted as a fix, and it raises the question: is `STEPS_COMPLETED` actually used anywhere downstream (e.g., in error reporting)? If it's only set but never read, it's dead code.

**[ADVISORY] The `SYNC_EXIT` variable capture is incorrect**

```bash
if bash "$SCRIPT_DIR/buildos-sync.sh" --push; then
    ...
else
    SYNC_EXIT=$?
```

When the `if` command's condition fails, `$?` reflects the exit status of the `bash ...` command, so this does work correctly in bash. However, if `set -e` or an ERR trap is active (the script sources common setup and uses `set -e` at the top based on the error handling pattern), the `if` construct protects against `set -e` but the pattern is worth a comment for maintainability since it's non-obvious.

**[ADVISORY] Step numbering is a maintenance burden**

Hardcoded "Step N/6" strings across the file require manual updates every time a step is added or removed. Consider computing the total dynamically or using a constant.

---
