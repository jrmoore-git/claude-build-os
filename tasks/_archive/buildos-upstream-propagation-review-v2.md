---
debate_id: buildos-upstream-propagation-review-v2
created: 2026-03-30T13:37:00-0700
mapping:
  A: gemini-3.1-pro
  B: gpt-5.4
  C: gemini-3.1-pro
---
# buildos-upstream-propagation-review-v2 — Challenger Reviews

## Challenger A — Challenges
### PM/Acceptance
*   **[MATERIAL] Project-specific leak in scripts:** `scripts/tier_classify.py` still contains `r"^config/(?!nicole_filter\.json)"`. "nicole_filter" appears to be a downstream project-specific reference that was missed.
*   **[ADVISORY] Project-specific leak in workflow rule:** `.claude/rules/workflow.md` still references "WebChat" in the milestone: `email → triage → draft → WebChat → approve → sends`. Consider generalizing to "app" or "client".

### Security
*   **[ADVISORY] Sync script banned-terms bypass:** The `$BANNED_PATTERN` in `scripts/buildos-sync.sh` uses `grep -inE`. Because `-i` makes it case-insensitive, you don't need to specify both `Jarvis|jarvis` or `openclaw|OpenClaw`. However, "nicole" and "WebChat" should probably be added to the banned terms list to prevent future leaks.

### Architecture
*   **[MATERIAL] Functional regression on CWD assumptions:** In multiple skills (e.g., `qa`, `wrap-session`, `status`), you removed `cd /Users/macmini/openclaw` and replaced absolute paths with relative ones (e.g., `ls tests/test_*.py`). If the agent executes these tools while deep in a subdirectory, these commands will fail. Prefix commands with `cd "$(git rev-parse --show-toplevel)"` to ensure they run from the root.
*   **[MATERIAL] `PROJECT_ROOT` dynamic initialization:** In `scripts/*.py` (e.g., `artifact_check.py`, `debate.py`), `PROJECT_ROOT = subprocess.check_output(["git", "rev-parse", "--show-toplevel"]...)` is evaluated at module import time. If these scripts are imported or run outside a git repository (or in a weird environment state), they will instantly crash with a `CalledProcessError`. Wrap this in a `try/except` or evaluate it lazily.

---

## Challenger B — Challenges
## PM/Acceptance

- [MATERIAL] `.claude/skills/design-review/SKILL.md` removed the concrete auth flow (`#token=<token>`) and replaced it with a generic “provide valid auth credentials” prompt. That is not a safe generalization unless upstream truly supports arbitrary auth; for downstream it regresses the skill’s ability to complete reviews on the default app.

- [MATERIAL] Multiple skills changed `python3.11` or absolute interpreter paths to bare `python3` (`challenge`, `debate`, `plan`, `review`, `ship`, `status`, `design-consultation`). Context says the intended generalization was `python3 → python3.11`, but the diff does the opposite in several places. That can regress execution on systems where `python3` is absent or points to the wrong minor version.

- [ADVISORY] `.claude/skills/ship/SKILL.md` hardcodes post-deploy smoke test to `app/tests/smoke_test.py`. If upstream repos don’t standardize that path, this “generalization” is still project-structure-specific and may break ship flow.

## Security

- [MATERIAL] `scripts/buildos-sync.sh` copies files into the target repo before the second banned-terms scan, and on failure only prints “reverting recommended.” That leaves potentially sensitive/project-specific content written into the upstream checkout. Scan must happen pre-copy or perform automatic rollback on failure.

- [MATERIAL] `scripts/buildos-sync.sh` banned-term gate is bypassable/incomplete: it scans only file contents, not filenames/paths/commit message, and the pattern is a brittle blacklist of literals. Project refs can leak via unlisted variants/casing/word splits or via target path mapping later. As written, this is not a robust “hard gate.”

- [ADVISORY] `scripts/buildos-sync.sh` trusts `BUILDOS_DIR` blindly. At minimum, validate it points to the expected repo/remotes before `cp`, `git add`, `git commit`, `git push origin main`, or the script can mutate/push an arbitrary local repo.

## Architecture

- [MATERIAL] `scripts/artifact_check.py`, `debate.py`, `finding_tracker.py`, `tier_classify.py`, `enrich_context.py` now resolve `PROJECT_ROOT` via `git rev-parse --show-toplevel` at import time. Any invocation outside a git repo, from tests importing the module, or from alternate cwd contexts now hard-fails during import instead of at CLI entry. That is a functional regression from a constant path.

- [MATERIAL] `.claude/skills/design-consultation`, `design-review`, `plan-design-review`, `design.md`, and `ship` generalize `jarvis-app/` to `app/`. That is only semantically correct if upstream standardizes on `app/`. Otherwise framework files still embed a repo-specific frontend root and will fail in repos using other common layouts.

- [ADVISORY] `scripts/tier_classify.py` changed `^docs/OPENCLAW-PRD` to `^docs/.*PRD` and the exempt negative lookahead similarly. This broadens matching semantics materially; it may now classify unrelated docs with “PRD” anywhere in the basename as Tier 1. Verify this is intended, not an overgeneralization.

---

## Challenger C — Challenges
### PM/Acceptance
*   **[MATERIAL] Project leak:** `scripts/tier_classify.py` still contains `r"^config/(?!nicole_filter\.json)"`. "nicole_filter" is a project-specific reference that was missed in the cleanup.
*   **[ADVISORY] Redundant regex:** In `scripts/buildos-sync.sh`, `BANNED_PATTERN` includes `Justin|Jarvis|jarvis|openclaw|OpenClaw...`. Since the `grep` command uses `-i` (case-insensitive), listing both casing variants is redundant.

### Architecture
*   **[MATERIAL] Functional regression (Path Scope):** In `skills/wrap-session/SKILL.md`, `skills/review/SKILL.md`, and `skills/status/SKILL.md`, the absolute `cd /Users/...` commands were entirely removed. If a user triggers these skills from a subdirectory, `git diff` and `git status` will scope only to that directory, missing project-wide changes. Replace with `cd "$(git rev-parse --show-toplevel)"`.
*   **[ADVISORY] Unhandled Git dependency:** Generalizing `PROJECT_ROOT` to use `subprocess.check_output(["git", "rev-parse", "--show-toplevel"])` in the Python scripts is correct, but it will throw a fatal `CalledProcessError` if the script is ever executed outside of a git repository. Consider wrapping in a try/except with a fallback to `os.getcwd()`.

### Security
*   **[ADVISORY] Brittle sync gate:** The `BANNED_PATTERN` in `buildos-sync.sh` is a hardcoded blocklist. While effective for known OpenClaw terms, blocklists are inherently brittle for preventing *future* project leaks or novel credential types from slipping into the upstream repo. Consider adding a generic high-entropy string detector or using an established secrets-scanning tool (like `trufflehog` or `gitleaks`) in the sync pipeline.

---
