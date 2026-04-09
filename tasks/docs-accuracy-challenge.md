---
debate_id: docs-accuracy
created: 2026-03-26T14:47:35-0700
mapping:
  A: gpt-5.4
  B: gemini-3.1-pro
---
# docs-accuracy — Challenger Reviews

## Challenger A — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL]: `docs/how-it-works.md` claims `debate.py challenge` supports persona `pm` in the CLI help text “architect,staff,security” plus the example mapping includes `pm → gemini-3.1-pro`. The source `PERSONA_MODEL_MAP` does include `pm`, but the argparse help for `--personas` omits `pm` and instead documents only `(architect,staff,security)`. The docs present the interface as fully documented when the shipped CLI help does not; at minimum this is an inconsistency users will hit.

2. [RISK] [MATERIAL]: `docs/how-it-works.md` states personas sharing a model are deduplicated so `--personas architect,security` produces one challenger. The provided source only shows the argparse/constants section and contains no implementation proving deduplication. This is an unverified behavioral claim and should not be documented as fact from the supplied evidence.

3. [ASSUMPTION] [MATERIAL]: `docs/how-it-works.md` asserts `challenge` redacts author metadata, uses role-specific prompts, emits YAML frontmatter fields `debate_id`, `created`, `mapping`, and prints JSON status with `status`, `challengers`, `mapping`, `warnings`. None of those output-shape/processing claims are verifiable from the provided `debate.py` excerpt. They may be true, but they are unsupported by the review corpus and therefore inaccurate for an “accuracy review.”

4. [ASSUMPTION] [MATERIAL]: `docs/how-it-works.md` says `judge` shuffles challenger sections, issues decisions only on MATERIAL challenges, warns if judge model matches author model, and prints JSON with `accepted`, `dismissed`, `escalated`, `needs_human`. The provided source verifies only flags/defaults, not these behaviors. These should be treated as unverified.

5. [ASSUMPTION] [MATERIAL]: `docs/how-it-works.md` claims `refine` “each round produces review notes and a complete revised document” and that the output contains per-round review notes. The code excerpt only proves flags/defaults and model rotation constant. Output format and note generation are not shown.

6. [ASSUMPTION] [ADVISORY]: `docs/how-it-works.md` says `compare` scores on five named dimensions and outputs METHOD_A / METHOD_B / TIE verdict. Only the subcommand/default model are verified; scoring dimensions/verdict format are not shown.

7. [ASSUMPTION] [MATERIAL]: `docs/how-it-works.md` claims “All events are logged to `stores/debate-log.jsonl`.” No such behavior appears in the provided `debate.py` section. This is a concrete filesystem side-effect claim without evidence.

8. [ASSUMPTION] [MATERIAL]: `docs/how-it-works.md` says `debate.py` reads env vars “or `.env` in the project root.” The source only mentions environment variables and imports no dotenv loader. Since the repo promises “pure stdlib Python, no pip dependencies,” implicit `.env` loading is especially dubious and unverified.

9. [UNDER-ENGINEERED] [MATERIAL]: `docs/how-it-works.md` omits a real CLI discrepancy: the `challenge` help text says personas are `architect,staff,security`, but examples and constants support `pm`. This is exactly the kind of factual mismatch the docs should call out or avoid papering over.

10. [RISK] [MATERIAL]: `docs/how-it-works.md` says Tier 1.5 includes “hook scripts,” and “Used by” says `hook-review-gate.sh` and `hook-tier-gate.sh` both call `tier_classify.py`. The actual Tier 1.5 hook pattern is `^scripts/hook-.*\.sh$`, but the provided hooks live under `hooks/`, not `scripts/`. So the classifier does not classify the actual hook scripts as Tier 1.5. That makes the docs materially inaccurate about behavior and path coverage.

11. [ASSUMPTION] [MATERIAL]: `docs/how-it-works.md` says `tier_classify.py` Tier 1 covers “security rules” plural and “database schema/migrations.” In code, Tier 1 only matches `.claude/rules/security.md` exactly, plus regexes `schema.*\.sql$` and `migration.*\.sql$`. The docs overgeneralize; other security rules files and many schema-like filenames would not match.

12. [UNDER-ENGINEERED] [ADVISORY]: `docs/how-it-works.md` describes `CORE_SKILLS` as something to populate, which is correct, but omits that it is a single regex alternation string, not a JSON/list structure. Minor, but relevant for customization accuracy.

13. [ASSUMPTION] [MATERIAL]: `docs/how-it-works.md` says semantic search in `recall_search.py` “requires Ollama running locally and a pre-built embeddings database” and uses threshold `0.5`; that part is supported. But it also says semantic mode’s `--top-k` “uses its own default of 5.” In code, `semantic_search(..., top_k=5)` exists, but `main()` ignores `args.top_k` entirely when calling `semantic_search(" ".join(args.terms), file_filter)`. So the docs imply configurable semantic top-k semantics that do not exist.

14. [RISK] [MATERIAL]: `docs/how-it-works.md` says `--json` is “BM25 mode only — semantic mode always outputs formatted text.” While behaviorally true in current code, the parser does not reject `--json --semantic`; it silently ignores `--json`. The docs should note the flag is ignored in semantic mode, not just unavailable.

15. [ASSUMPTION] [MATERIAL]: `docs/how-it-works.md` claims `finding_tracker.py import` imports all ACCEPT findings as open, is idempotent, and that the store records `state_history`, `summary`, `decision`, `confidence`. The provided source shows only argparse and transition constants; none of the parsing/store-field/idempotency claims are verifiable.

16. [ASSUMPTION] [MATERIAL]: `docs/how-it-works.md` says `artifact_check.py` falls back to counting ACCEPT lines in the judgment file and validates challenge artifacts by requiring YAML frontmatter with `debate_id` and `MATERIAL` tag. Actual code sets `has_material` separately but `valid` only checks frontmatter; it does not require `MATERIAL` for validity. The docs overstate challenge validation.

17. [RISK] [MATERIAL]: `docs/how-it-works.md` says `artifact_check.py` checks staleness against “the newest file changed since `--base` ref.” The code computes `scope_mtime = _newest_scope_mtime(args.base)` but that helper is not shown. More importantly, the per-artifact comparison is against `scope_mtime`, not explicitly “newest changed file since base” in the visible code. This should be softened unless helper code is supplied.

18. [RISK] [MATERIAL]: `docs/hooks.md` says the repo ships “three enforcement hooks,” and “each is a shell script that fires as a Claude Code PreToolUse hook.” The wiring example uses matcher `Write|Edit` for `hook-tier-gate.sh`, but unlike the Bash hooks it does not show how Claude evaluates matcher regexes against tool names. This may be true, but the docs present it as established without evidence from settings schema. More importantly, both plan and review hooks are Bash-only matchers, so they only run on Bash invocations, not all PreToolUse events.

19. [RISK] [MATERIAL]: `docs/hooks.md` says `hook-plan-gate.sh` “Only activates when staged files match protected globs from `config/protected-paths.json`.” True broadly, but it omits a notable behavior: malformed or unreadable JSON also fails open in both the protected-path detection and plan validation blocks. That omission matters because it weakens enforcement.

20. [ASSUMPTION] [MATERIAL]: `docs/hooks.md` says a valid plan artifact requires YAML frontmatter containing “all required fields AND `verification_evidence` is not `PENDING`.” Actual code only requires fields from `required_plan_fields` in config; `verification_evidence` is optional. If the field is absent entirely, the artifact still passes. The docs materially overstate enforcement.

21. [RISK] [MATERIAL]: `docs/hooks.md` says `[EMERGENCY]` bypass “is logged and audited in weekly review.” The code only emits a stderr warning. No logging or audit trail implementation is shown.

22. [ASSUMPTION] [MATERIAL]: `docs/hooks.md` says `hook-review-gate.sh` requires “valid debate artifacts (challenge, resolution, or review file) newer than the staged files” for Tier 1. That matches code. But it also describes Tier 1.5 or “risk-flagged Tier 2” as warning conditions. The implementation’s Tier 2 warning heuristic is a substring search over file-path keys (`'skill'`, `_tool.py`, `.claude/rules/`, `hook-`, `security`) and can miss or spuriously match paths. The docs present a policy-grade classification, but the actual implementation is heuristic and lossy.

23. [RISK] [MATERIAL]: `docs/hooks.md` states “[EMERGENCY] bypass is only available in hook-plan-gate. Neither hook-review-gate nor hook-tier-gate support it.” This is accurate from code, but the docs omit a stronger issue: `hook-review-gate.sh` allows `[TRIVIAL]` bypass unconditionally before checking staged files, so a commit touching Tier 1 files can bypass review merely by including `[TRIVIAL]`. That is an important omitted behavior.

24. [ASSUMPTION] [MATERIAL]: `docs/hooks.md` says `hook-tier-gate.sh` checks whether a debate artifact exists in `tasks/` “that is newer than the current session start.” The code uses a shared `/tmp/build-os-tier-gate/session_start` file and compares artifact mtime `< session_start`; artifacts with equal/greater mtime pass. More importantly, the session marker is global, not project-specific, so session boundaries can leak across repos/users on the same machine. The docs do not mention this failure mode.

25. [RISK] [MATERIAL]: `docs/hooks.md` describes session dedup “Once a tier has been classified and cleared (or warned) for a session, the gate passes for 4 hours.” In code, the marker is per tier only (`tier1_passed`, `tier15_passed`), not per file or project. Clearing one Tier 1 file causes all Tier 1 edits in any repo sharing `/tmp/build-os-tier-gate` to pass for 4 hours. The docs materially understate the breadth of the bypass.

26. [UNDER-ENGINEERED] [MATERIAL]: `docs/hooks.md` claims tier gate’s Tier 1 block condition is “without any valid debate artifact from the current session.” Because any `-judgment.md` or `-resolution.md` file newer than session start passes with no content validation, “valid” is inaccurate. Only challenge files are partially validated.

27. [RISK] [ADVISORY]: The configuration section in `docs/hooks.md` correctly lists `required_plan_fields` from config, but because the actual gate separately checks `verification_evidence` outside config, the docs imply all enforceable requirements live in JSON when they do not.

## Concessions
- The documented `debate.py` subcommands and default models/rounds shown in argparse/constants are mostly correct.
- The `tier_classify.py` examples, overall JSON shape, and ambiguity semantics match the source.
- `recall_search.py` source-file mappings, BM25 default mode, semantic threshold, and `enrich_context.py`’s keyword extraction sources are documented substantially correctly.

## Verdict
REVISE — There are multiple material accuracy problems, especially around unverified `debate.py` behaviors, incorrect hook/tier classification details, and overstated enforcement semantics in the hook docs.

---

## Challenger B — Challenges
## Challenges

1. [UNDER-ENGINEERED] [MATERIAL]: The `hook-tier-gate.sh` script assumes the tool input always contains a `file_path` key (`ti.get('file_path', '')`). Claude's actual bash/file editing tools often use different parameter names depending on the specific tool (e.g., `path`, `file`, or just passing it as an argument to `sed`/`echo`). If the key is missing, the hook silently fails open (`print('ALLOW')`), completely bypassing the Tier 1/1.5 gate.

2. [RISK] [MATERIAL]: `hook-plan-gate.sh` and `hook-review-gate.sh` extract the `COMMAND` using a simple json parse of `tool_input.command`. If the user/model runs `git commit -m "Fix bug [EMERGENCY]"` but the actual command string executed in the shell tool is slightly different (e.g., wrapped in a bash script or aliased), the grep will still match *any* occurrence of `[EMERGENCY]` or `[TRIVIAL]` in the entire command payload, potentially triggering accidental bypasses if the string appears in a diff or file content being echoed in the same tool call. 

3. [UNDER-ENGINEERED] [ADVISORY]: `enrich_context.py` keyword extraction is extremely naive. It splits words, removes a hardcoded list of ~50 stopwords, and takes the first 8 remaining words. Words like "proposal", "update", "fix", "change", or "implement" are not in the stopword list and will easily consume the 8-keyword budget, leading to useless BM25/semantic search queries.

## Concessions
1. The documentation accurately reflects the CLI subcommands, flags, and default model assignments in `debate.py`.
2. The tier classification logic described in `docs/how-it-works.md` perfectly matches the regex patterns and severity ordering in `tier_classify.py`.
3. The artifact validation requirements (e.g., `verification_evidence != "PENDING"`) are correctly documented and faithfully implemented in the bash hooks.

## Verdict
REVISE. The documentation accurately describes the code, but the code itself has a material flaw in `hook-tier-gate.sh`'s parameter parsing that will cause the gate to fail open during actual Claude tool use.

---
