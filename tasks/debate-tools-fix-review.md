---
topic: debate-tools-fix
review_tier: cross-model
status: revise
git_head: 65d3368
producer: claude-opus-4-6
created_at: 2026-04-16T11:36:00-0700
scope: scripts/debate_tools.py, scripts/debate.py, tests/test_debate_tools.py
findings_count: 3
spec_compliance: false
---

## PM / Acceptance
- [MATERIAL] `cmd_explore` and `cmd_pressure_test` stdout format changes (text -> JSON) are unrelated scope creep — already committed in 4a9a717 as prior session work. Not part of debate-tools-fix scope. Flagged by all 3 models.
- [ADVISORY] Manifest injection adds ~2K-4K tokens per invocation. No opt-out flag. Acceptable given the value (eliminates false absence claims) but `_estimate_cost` not updated.
- [ADVISORY] Manifest injection only in cmd_challenge and cmd_review. Intentionally scoped — other flows don't use `--enable-tools`.

## Security
- [MATERIAL] `_check_test_coverage` still uses `module_path.lstrip("./")` (line 124) — same bug class fixed in `_read_file_snippet`. Should apply consistent `startswith("./")` fix. Flagged by A and B.
- [ADVISORY] `ALLOWED_FILE_SETS["hooks"]` glob is `hooks/*.py` — excludes `.sh` hooks. Challengers searching hooks via code_presence won't find shell hooks (hook-guard-env.sh, hook-plan-gate.sh, etc.).
- [ADVISORY] Manifest filenames/function names injected unsanitized into prompt. Low risk in trusted repo but latent injection vector.
- [ADVISORY] Trust header wording ("every file...exists") slightly overstates regex-based export extraction certainty.

## Architecture
- [MATERIAL] Duplicated test-coverage discovery logic in `_check_test_coverage()` and `generate_repo_manifest()`. Same exact-match + prefix-glob pattern in two places. Extract shared helper. Flagged by A and B.
- [MATERIAL] `MAX_MANIFEST_FILES=50` truncation happens before export/test-coverage derivation. Silently degrades manifest authority without disclosure. Should note truncation in output. Flagged by B.
- [ADVISORY] No caching for `generate_repo_manifest()`. Acceptable at current scale (~44 file reads) but could add session-level cache later.
- [ADVISORY] Export regex is syntactic (not AST-based). Captures nested defs. Acceptable given `[:30]` cap and token budget.
