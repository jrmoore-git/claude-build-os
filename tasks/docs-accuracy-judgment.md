---
debate_id: docs-accuracy
created: 2026-03-26T14:48:23-0700
mapping:
  Judge: gpt-5.4
  A: gpt-5.4
  B: gemini-3.1-pro
---
# docs-accuracy — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'gpt-5.4', 'B': 'gemini-3.1-pro'}

## Judgment

### Challenge 1: `debate.py --personas` help omits `pm` while docs include it
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.96
- Rationale: The source shows `PERSONA_MODEL_MAP` includes `pm`, and the example/docs include `pm`, but the argparse help string for `--personas` lists only `architect,staff,security`. That is a real documentation/interface inconsistency users will encounter.
- Required change: Update either the CLI help string to include `pm` or the docs to explicitly note that `pm` is supported despite being omitted from the current help text.

### Challenge 2: Docs claim persona deduplication without visible code support
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.83
- Rationale: In the provided review corpus, only argparse/constants are shown for `debate.py`; no implementation is provided to verify deduplication. Since the task is factual verification against supplied source, this behavior should not be documented as established fact from the visible evidence.
- Required change: Remove or soften the deduplication claim unless the implementation is included and verifies it.

### Challenge 3: `challenge` behavior/output claims are unverified by provided source
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.88
- Rationale: Claims about author redaction, role-specific prompts, exact frontmatter fields, and stdout JSON structure are not supported by the excerpted `debate.py` code. For an accuracy review against provided source, these are overclaims.
- Required change: Limit docs to verified CLI/constant facts or provide the implementation section proving these behaviors.

### Challenge 4: `judge` behavior/output claims are unverified by provided source
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.88
- Rationale: The excerpt proves flags/defaults, but not section shuffling, MATERIAL-only adjudication, author-model warning behavior, or exact stdout schema. Those are material runtime claims and should not appear as verified facts without code evidence.
- Required change: Remove or qualify these implementation details unless the relevant `cmd_judge` code is supplied.

### Challenge 5: `refine` output-format claims are unverified
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.86
- Rationale: The source verifies the subcommand, defaults, and model rotation constant, but not per-round review notes or complete revised-document emission each round. The docs go beyond what the provided code proves.
- Required change: Restrict the section to verified arguments/defaults, or add source proving the output structure.

### Challenge 6: `compare` scoring dimensions/verdict format are unverified
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.93
- Rationale: This was marked advisory by the challenger and should not be judged under the requested format. Noted only: the concern overlaps with other `debate.py` overclaim issues.

### Challenge 7: Docs claim all debate events are logged to `stores/debate-log.jsonl` without evidence
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Rationale: No visible code in the provided `debate.py` excerpt supports this filesystem side effect. A concrete logging-path claim is material and currently unverified.
- Required change: Remove the logging claim or provide the implementation that writes `stores/debate-log.jsonl`.

### Challenge 8: Docs claim `.env` loading for LiteLLM settings without evidence
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.95
- Rationale: The source mentions environment variables only and imports no dotenv loader. Given the "pure stdlib Python" framing, the `.env` auto-loading claim is unsupported and likely inaccurate.
- Required change: Change docs to say settings are read from environment variables only, unless there is explicit `.env` loading code elsewhere.

### Challenge 9: Docs omit the real `pm` help-text discrepancy
- Challenger: A
- Materiality: MATERIAL
- Decision: DISMISS
- Confidence: 0.82
- Rationale: This is substantively the same issue as Challenge 1. The underlying flaw is real, but it does not require a separate accepted change beyond fixing the persona/help inconsistency already accepted.

### Challenge 10: Docs say Tier 1.5 includes hook scripts, but classifier only matches `scripts/hook-.*.sh` while actual hooks are under `hooks/`
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.97
- Rationale: This is a clear mismatch. `tier_classify.py` only treats `scripts/hook-.*\.sh` as Tier 1.5, but the actual hook files shown are in `hooks/`, so the documentation overstates current classifier coverage.
- Required change: Either update `tier_classify.py` to match `hooks/hook-.*\.sh` or correct the docs to reflect the current path-specific behavior.

### Challenge 11: Tier 1 docs overgeneralize security-rule and schema matching
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.94
- Rationale: The code matches only `.claude/rules/security.md` exactly and SQL filenames matching `schema.*\.sql` or `migration.*\.sql`. The docs describe broader categories than the regexes actually enforce.
- Required change: Narrow the docs to the exact matched paths/patterns, or broaden the regexes if broader coverage is intended.

### Challenge 12: Docs omit that `CORE_SKILLS` is a regex alternation string
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.95
- Rationale: Advisory only; not judged. Noted as a minor customization clarity issue.

### Challenge 13: Docs imply semantic `--top-k` configurability that code does not implement
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.96
- Rationale: `semantic_search` accepts `top_k`, but `main()` calls it without passing `args.top_k`, so semantic mode always uses its internal default of 5. The docs are inaccurate if they imply semantic mode has user-configurable `--top-k`.
- Required change: Document that `--top-k` applies only to BM25, or fix the code to pass `args.top_k` into `semantic_search`.

### Challenge 14: Docs should say `--json` is ignored in semantic mode rather than unavailable
- Challenger: A
- Materiality: MATERIAL
- Decision: DISMISS
- Confidence: 0.78
- Rationale: The docs say "`--json` — Output results as a JSON array (BM25 mode only — semantic mode always outputs formatted text)." That is materially consistent with actual behavior, even if the parser silently accepts and ignores the flag. This is more of a nuance/UX note than a factual inaccuracy.
- Required change: None.

### Challenge 15: `finding_tracker.py` import/store/idempotency claims are unverified by provided source
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.87
- Rationale: The provided source for `finding_tracker.py` contains argparse and transition constants only; it does not prove import behavior, persisted fields, or idempotency. Those implementation claims exceed the supplied evidence.
- Required change: Remove or qualify the unverified behavior details, or provide the omitted implementation.

### Challenge 16: Docs overstate `artifact_check.py` challenge validity requirements
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.98
- Rationale: The code sets `has_material` separately but `valid` for a challenge checks only frontmatter/debate_id presence. The docs incorrectly say validity requires both YAML frontmatter and a `MATERIAL` tag.
- Required change: Update docs to distinguish `valid` from `has_material`, matching the actual JSON fields and logic.

### Challenge 17: Staleness description for `artifact_check.py` is not fully supported by visible code
- Challenger: A
- Materiality: MATERIAL
- Decision: ESCALATE
- Confidence: 0.6
- Rationale: The visible code compares artifact mtimes to `scope_mtime`, but the helper `_newest_scope_mtime(args.base)` is omitted, so the exact semantics are not fully verifiable. The concern may be valid, but the missing helper prevents a confident ruling.
- Required change: N/A

### Challenge 18: Hooks docs overstate that hooks fire on all PreToolUse events
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.91
- Rationale: The docs say each hook "fires as a Claude Code PreToolUse hook," but the wiring clearly uses `matcher: "Bash"` for plan/review and `matcher: "Write|Edit"` for tier gate. The more precise truth is that they are PreToolUse hooks scoped by matcher, not universal on every PreToolUse event.
- Required change: Clarify that all three are configured under PreToolUse, but each runs only for tool calls matching its matcher.

### Challenge 19: Plan-gate docs omit fail-open on malformed/unreadable JSON config
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.94
- Rationale: The hook fails open not only when the config file is missing, but also when JSON parsing fails in both protected-path detection and plan validation. Omitting malformed-config fail-open behavior understates a meaningful enforcement gap.
- Required change: Expand docs to state that missing, unreadable, or invalid JSON config causes fail-open behavior.

### Challenge 20: Plan-gate docs wrongly say `verification_evidence` is required and non-PENDING
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.99
- Rationale: The hook requires only the config-listed fields; `verification_evidence` is checked only if present. If absent, the plan can still pass, so the docs materially overstate enforcement.
- Required change: Update docs to say `verification_evidence` is checked only when present, or change the hook/config to require it explicitly.

### Challenge 21: Docs claim `[EMERGENCY]` bypass is logged/audited, but code only warns to stderr
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.97
- Rationale: No logging or audit mechanism is shown in the hook. The documented audit claim is unsupported.
- Required change: Remove the logging/audit claim or implement explicit logging/audit behavior.

### Challenge 22: Review-gate docs present Tier 2 warnings as policy-grade, but implementation is heuristic substring matching
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.89
- Rationale: The docs describe a clean category ("risk-flagged Tier 2"), but the implementation uses ad hoc substring checks over file paths after classification. That mismatch matters because the heuristic can over- or under-warn.
- Required change: Document the actual heuristic triggers, or replace them with explicit classifier-backed categories.

### Challenge 23: Hooks docs omit unconditional `[TRIVIAL]` bypass in `hook-review-gate.sh`
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.98
- Rationale: The script checks `[TRIVIAL]` before inspecting staged files, so even Tier 1 commits can bypass review-gate entirely. This is a significant omitted behavior, and it directly conflicts with the stronger enforcement tone of the docs.
- Required change: Document that `[TRIVIAL]` bypass skips review-gate unconditionally, or change the hook to restrict `[TRIVIAL]` to low-risk cases only.

### Challenge 24: Tier-gate docs omit that session markers are global, not project-specific
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.93
- Rationale: The code uses shared files under `/tmp/build-os-tier-gate/` with no project scoping. The docs' "current session" phrasing hides a real cross-repo leakage risk.
- Required change: Document the global marker behavior and its implications, or namespace markers by project/repo.

### Challenge 25: Tier-gate docs understate breadth of 4-hour bypass because marker is per-tier, not per-file/project
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.97
- Rationale: Once `tier1_passed` or `tier15_passed` exists, all files of that tier can pass for 4 hours, regardless of file or repo. The docs say "once a tier has been classified and cleared," but do not make clear how broad that clearance is.
- Required change: Clarify that dedup is per tier and global to the marker directory, or change implementation to scope markers by project and path.

### Challenge 26: Tier-gate docs call judgment/resolution artifacts "valid" though they are accepted by mere presence
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.96
- Rationale: For Tier 1, any `-judgment.md` or `-resolution.md` newer than session start passes with no content validation. Calling those artifacts "valid" is inaccurate.
- Required change: Update docs to reflect the actual checks, distinguishing partial validation for challenge files from mere presence checks for judgment/resolution.

### Challenge 27: Config section may imply all plan-gate requirements live in JSON, though `verification_evidence` is checked separately
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.94
- Rationale: Advisory only; not judged. It overlaps with accepted Challenge 20.

### Challenge 1: `hook-tier-gate.sh` may fail open if Claude uses a different tool-input key than `file_path`
- Challenger: B
- Materiality: MATERIAL
- Decision: DISMISS
- Confidence: 0.84
- Rationale: This challenge relies on assumptions about external Claude tool schemas not included in the review corpus. The docs under review describe the hook's implemented behavior, and the provided wiring uses `Write|Edit`; there is insufficient evidence here that the documented claim is inaccurate relative to the supplied source.
- Required change: None.

### Challenge 2: Plan/review hooks may accidentally match bypass tokens in broader command payloads
- Challenger: B
- Materiality: MATERIAL
- Decision: DISMISS
- Confidence: 0.8
- Rationale: The code extracts only `tool_input.command`, not the entire raw JSON payload, so the described risk is overstated on the provided evidence. While command-string matching is broad, the specific scenario of matching diff/file content in the full payload is not supported by the source shown.
- Required change: None.

### Challenge 3: `enrich_context.py` keyword extraction is naive
- Challenger: B
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.97
- Rationale: Advisory only; not judged.

## Summary
- Accepted: 21
- Dismissed: 8
- Escalated: 1
- Overall: REVISE with accepted changes
