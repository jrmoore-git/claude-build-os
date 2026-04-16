---
debate_id: debate-tools-fix-review-debate
created: 2026-04-16T11:35:50-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# debate-tools-fix-review-debate — Challenger Reviews

## Challenger A — Challenges


# Code Review: debate-tools-fix

## Summary

This diff addresses a concrete failure (session 18: challengers couldn't discover hooks, tests, rules, or docs via debate tools, leading to false absence claims). It expands file set coverage, adds a deterministic repo manifest injected into LLM context, fixes an `lstrip` bug, adds prefix-glob test coverage discovery, and includes 20+ new tests. It also changes stdout output format for `cmd_explore` and `cmd_pressure_test`.

---

## PM/Acceptance

### Positive Compliance

1. **[ADVISORY]** The core problem — challengers making false claims about missing files/functions — is directly addressed by (a) expanding `ALLOWED_FILE_SETS` and `ALLOWED_SNIPPET_PATHS`, and (b) injecting a deterministic manifest. This is well-targeted.

2. **[ADVISORY]** Test coverage is thorough: 20+ new tests covering file set consistency, manifest generation, manifest formatting, test coverage discovery, and trust header presence.

### Scope Creep

3. **[MATERIAL]** The `cmd_explore` and `cmd_pressure_test` stdout output format changes (from printing full text to printing JSON status) are **unrelated to the debate-tools-fix scope**. These change the contract for any downstream consumer parsing stdout. The commit message and session description don't mention these as intentional. If orchestrator scripts or skills parse the previous stdout format, this is a breaking change.

   Evidence: `cmd_explore` changed from `print(output_text)` to `print(json.dumps({"status": "ok", ...}))`. `cmd_pressure_test` changed similarly in both single-model and multi-model paths, and removed a `print(output_text)` call entirely.

4. **[ADVISORY]** The manifest injection increases token consumption for every `cmd_challenge` and `cmd_review` call. Based on the manifest structure (directories + ~100 files + exports for ~40 Python files + test coverage mapping), this is ESTIMATED at 2,000–4,000 tokens per invocation. For multi-model challenges with 3+ challengers, this multiplies. No cost guard or opt-out flag exists. The `_estimate_cost` function exists but wasn't updated to account for this.

---

## Security

### Trust Boundary: Manifest as Prompt Injection Surface

5. **[MATERIAL]** The manifest is generated from filesystem contents (filenames, function/class names) and injected directly into the LLM prompt without sanitization. If a file or function name contains prompt injection payloads (e.g., a file named `ignore_previous_instructions.py` or a function named with embedded markdown/instructions), these flow directly into the LLM context.

   The `format_manifest_context` function does no escaping:
   ```python
   lines.append(f"  {fpath}: {', '.join(names)}")
   ```
   
   While the repo is presumably trusted, this creates a latent injection vector if any contributor adds adversarially-named files. The existing `TOOL_INJECTION_DEFENSE` mechanism (confirmed present in debate.py) doesn't cover manifest content.

### File Exposure Expansion

6. **[ADVISORY]** Adding `"rules": ".claude/rules/"` and `"docs": "docs/"` to `ALLOWED_SNIPPET_PATHS` means challengers can now read the full content of governance rules and documentation. This is intentional for review quality but expands the data egress surface. The module docstring states "Deny-by-default data egress: tools return only structured metadata, booleans, counts, and aggregates. Never raw code or DB rows." The `_read_file_snippet` function already returns raw file content (up to 50 lines), so this docstring is already inaccurate, but the expansion makes it more so.

7. **[ADVISORY]** The `ALLOWED_FILE_SETS` for hooks is `"hooks/*.py"` — this excludes `.sh` hook files (confirmed: `hooks/hook-guard-env.sh`, `hooks/hook-plan-gate.sh`, etc. exist per manifest). Challengers searching for shell hooks via `check_code_presence(file_set='hooks')` will get false negatives. This partially recreates the original problem for shell-based hooks.

### lstrip Bug Fix Correctness

8. **[MATERIAL]** The `lstrip("./")` → `file_path[2:]` fix in `_read_file_snippet` is correct and important. The old `lstrip("./")` would strip any leading combination of `.` and `/` characters, which would mangle `.claude/rules/...` paths into `claude/rules/...`. However, the **same bug exists in `_check_test_coverage`**:

   Line 126 (confirmed via tool): `_check_test_coverage` still contains `module_path.lstrip("./")` (confirmed present). If someone passes `./scripts/debate.py`, the lstrip could theoretically mangle it, though in practice the leading `./` case is the common one. More critically, if a path like `.special/foo.py` were passed, it would be mangled. The fix should be applied consistently.

---

## Architecture

### Manifest Generation: Performance and Caching

9. **[ADVISORY]** `generate_repo_manifest()` performs filesystem walks, reads every Python file in hooks/ and scripts/ to extract exports via regex, and does glob-based test coverage discovery — all synchronously on every `cmd_challenge` and `cmd_review` invocation. For a repo with ~22 hooks + ~22 scripts, this means ~44 file reads plus glob operations. ESTIMATED at 50-200ms per call, which is negligible compared to LLM latency, but the manifest is identical across calls within a session. No caching mechanism exists.

10. **[MATERIAL]** The manifest generation duplicates logic that already exists in `_check_test_coverage`. The test coverage mapping in `generate_repo_manifest` (lines 366-385) reimplements the exact-match + prefix-glob logic from `_check_test_coverage` (lines 128-149). This creates a maintenance burden — if the test discovery heuristic changes, it must be updated in two places. Extract a shared helper.

### Manifest Injection Placement

11. **[ADVISORY]** In `cmd_challenge`, the manifest is prepended to `proposal` before `_apply_posture_floor` processes it. The posture floor function scans the proposal text for security-sensitive patterns. The manifest content (filenames like `hook-guard-env.sh`, function names like `_load_credentials`) could trigger false posture floor escalations. Verify that `_apply_posture_floor` doesn't pattern-match on these strings.

12. **[ADVISORY]** In `cmd_review`, the manifest is injected into `input_text` after the `enable_tools` check but before `tool_defs` assignment. The ordering is correct, but the manifest injection is inside a conditional block (`if enable_tools`) while in `cmd_challenge` it's also gated on `enable_tools`. This is consistent.

### Output Format Breaking Changes

13. **[MATERIAL]** (Reiterating from PM section for architectural impact) `cmd_explore` and `cmd_pressure_test` now emit JSON to stdout instead of full output text. The full text is still written to `args.output` file. Any orchestration code that captures stdout from these commands will break. The `cmd_pressure_test` single-model path previously printed the result JSON to stderr (`file=sys.stderr`) and now prints to stdout — this is a stream change that could break piping.

### Manifest Content Completeness

14. **[ADVISORY]** The manifest's `MANIFEST_DIRS` includes `"skills": ".claude/skills"` but lists skills by subdirectory name only (not file contents). This is intentional and good for token economy. However, the manifest doesn't include top-level files (e.g., `CLAUDE.md`, `.claude/settings.json`) which challengers might also make false claims about.

15. **[ADVISORY]** The `format_manifest_context` trust header instructs the LLM: "Do not use tool calls to re-verify existence claims from this manifest." This is a soft instruction — LLMs may ignore it, wasting tool calls. But it's a reasonable optimization hint with no downside risk.

### Export Extraction Regex

16. **[ADVISORY]** The export extraction regex `r"^(?:def|class)\s+([a-zA-Z_]\w*)"` captures all top-level and nested function/class definitions, not just exports. For a 4,619-line file like `debate.py`, this could capture many internal helpers. The `[:30]` cap mitigates token bloat but means the manifest may omit important exports for large files. This is acceptable given the token budget constraint.

---

## Risk Assessment

**Risk of the change:** Moderate. The stdout format changes are breaking. The manifest injection increases token cost. The duplicated test-discovery logic creates maintenance debt. The prompt injection surface via filenames is a latent risk.

**Risk of NOT changing:** High. Challengers making false absence claims undermines the entire debate/review system's reliability. The `lstrip` bug silently breaks `.claude/` path access. Limited file sets mean challengers can't verify hooks, tests, rules, or docs — the core review artifacts.

**Recommendation:** Accept with fixes for the three MATERIAL items: (1) apply the `lstrip` fix consistently to `_check_test_coverage`, (2) extract shared test-discovery logic, (3) either revert the stdout format changes or document them as intentional with migration notes.

---

## Challenger B — Challenges
PM/Acceptance

- [MATERIAL] `scripts/debate.py` includes unrelated CLI output contract changes in `cmd_explore` and `cmd_pressure_test`, but the stated change set is “debate-tools-fix” and the file summary only mentions “manifest injection in cmd_challenge + cmd_review.” This is scope creep with real acceptance risk: callers that previously consumed the human-readable stdout payload now receive JSON instead. The diff shows no accompanying tests for these command-level contract changes and no spec/user-facing note justifying them. If these output changes are intentional, they should be split into a separate change with explicit acceptance criteria; otherwise revert them from this PR.

- [ADVISORY] The manifest injection is only added for `cmd_challenge` and `cmd_review`. That matches the stated scope, but the manifest rationale in comments is broader (“challengers never guess about repo structure”). Risk of not changing: false absence claims continue in those tool-enabled flows. Risk of current change: similar guesswork may still persist in other tool-using flows if they exist, so the fix is targeted rather than systemic. That seems right-sized for now, but worth documenting as an intentional partial rollout rather than a complete repo-structure solution.

Security

- [MATERIAL] `scripts/debate_tools.py:124` still uses `module_path = module_path.lstrip("./")` in `_check_test_coverage`. This has the same class of bug the patch explicitly fixed in `_read_file_snippet`: `lstrip("./")` removes any leading `.` or `/` characters, not just a single `./` prefix. That can rewrite user input in unexpected ways and weakens path normalization guarantees at the trust boundary. Even if the current allowlist/traversal checks reduce exploitability, the architectural/security contract should normalize deterministically with `startswith("./")` and slicing, as done for snippets.

- [ADVISORY] The new manifest trust header says “Every file, directory, and function listed below exists. Do not use tool calls to re-verify existence claims from this manifest.” That improves prompt behavior, but it also creates a stronger trust boundary around a regex-derived export list (`re.finditer(r"^(?:def|class)...")`). Since the export extraction is syntactic and non-AST-based, nested defs or unusual formatting could still be surfaced as “exists.” I don’t see a direct security vulnerability here, but the wording overstates certainty relative to the extraction method. Safer phrasing would limit the guarantee to “filesystem entries and parsed top-level signatures generated by code” or similar.

Architecture

- [MATERIAL] `generate_repo_manifest()` now truncates each category to `MAX_MANIFEST_FILES = 50` before export/test-coverage derivation (`manifest["files"][category] = files[:MAX_MANIFEST_FILES]`, then later exports/coverage iterate only that truncated list). This means the manifest’s “ground-truth” model silently degrades once a directory exceeds 50 files: later files disappear entirely from file listings, exported symbol listings, and test coverage mappings. That is an architectural inconsistency because the injected manifest is framed as authoritative. If token budget requires truncation, the output should explicitly disclose truncation per category (for example, “showing first 50 of N”), or derive exports/coverage from full sets while separately truncating rendered text.

- [ADVISORY] There is duplicated test-coverage discovery logic in `_check_test_coverage()` and `generate_repo_manifest()` with slightly different responsibilities but the same matching rules (exact names + `test_<module>_*.py` glob). This increases maintenance risk: future fixes to coverage matching can easily land in one path and not the other. Consider centralizing this into a helper used by both tool execution and manifest generation.

- [ADVISORY] The manifest generation walks and parses a substantial portion of the repo on every tool-enabled `cmd_challenge` and `cmd_review` invocation. I don’t have timing data here, so any latency claim would be SPECULATIVE, but structurally this couples prompt assembly to repeated filesystem scans and regex parsing. Risk of changing: some startup overhead on every run; risk of not changing: continued LLM hallucinations about repo structure. Given the user-value, the tradeoff may be acceptable, but a cache keyed by repo root + mtimes would keep the design scalable as docs/tests/scripts grow.

Spec extraction / violation check

No separate spec document was included in the prompt beyond the change summary, so there are no EXCEPTION / MUST NOT / EXPLICITLY EXCLUDED clauses to extract or verify. The only notable scope boundary present is the summary “manifest injection in cmd_challenge + cmd_review”; the unrelated stdout contract changes called out above conflict with that stated scope and are flagged as PM/Acceptance scope creep.

---

## Challenger C — Challenges
### Architecture
* **[MATERIAL]** The standard output of `cmd_explore` and `cmd_pressure_test` in `scripts/debate.py` has been changed from printing raw output text to printing a JSON string (`print(json.dumps(...))`). This changes the CLI contract. If any bash scripts, CI pipelines, or test harnesses are parsing the standard output expecting raw text, they will break. (ESTIMATED failure risk if callers aren't updated).
* **[ADVISORY]** The `generate_repo_manifest()` function opens and reads the contents of all Python files in `hooks/` and `scripts/` to run regex searches for exports on every `cmd_challenge` and `cmd_review` invocation. While this is acceptable at current repository scale (EVIDENCED by the manifest showing exactly 22 scripts and 22 hooks), it will introduce disk I/O and processing latency that scales linearly as the codebase grows. Consider caching this manifest for the duration of a session.

### Security
* **[ADVISORY]** Good defense-in-depth in `generate_repo_manifest()` by explicitly filtering files using `SECRET_PATTERNS` and `SNIPPET_BLOCKED_EXTENSIONS`. This appropriately protects the trust boundary by preventing environment files (`.env`, `.key`, etc.) from being accidentally leaked into the LLM context.
* **[ADVISORY]** The modification in `_read_file_snippet` to strip `./` is safe because `ALLOWED_SNIPPET_PATHS` requires matches to start with explicitly defined, trailing-slash directories (e.g., `config/`). This properly mitigates basic path traversal risks.

### PM/Acceptance
* **[ADVISORY]** Injecting a deterministic repository manifest into the prompt is an excellent, right-sized solution to a concrete user friction point. As EVIDENCED by the diff comments ("L33: session 18 failure"), agents were struggling with false absence claims. Providing trusted, ground-truth data upfront effectively eliminates the need for speculative tool calls, significantly reducing latency and token costs.

---
