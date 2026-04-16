---
name: audit-2026-04-16-fresh-eyes
description: Fresh-eyes audit from Claude 4.7 — structural/strategic findings not surfaced by the earlier 2026-04-16 audit
type: audit
date: 2026-04-16
---

# Audit: 2026-04-16 (fresh eyes, Claude 4.7)

Complementary to `tasks/audit-2026-04-16.md`. That audit focused on line-level discrepancies (doc counts, missing files, untested hooks). This one focuses on **structural posture** — things that look right at the line level but wrong at the system level.

No critical findings. BuildOS is fundamentally healthy. These are debts accumulating quietly.

---

## Findings

### F1: debate.py is a 4,629-line monolith

- **Severity:** warning
- **Source:** inspected
- **Evidence:** `scripts/debate.py` is 4,629 lines with 43 top-level functions. Six subcommand handlers dominate: `cmd_judge` (515 lines, 1718–2233), `cmd_refine` (385L), `cmd_review` (275L), `cmd_pressure_test` (262L), `cmd_challenge` (265L), `cmd_explore` (193L). Total: ~1,895 lines inside six functions that share boilerplate but are not factored.
- **Why fresh eyes:** The prior audit counted tests on debate.py (41 new tests) and called it "improved." Test count is not a substitute for testability. A monolith with 41 tests has worse ROI per test than a package with 41 tests spread across focused modules, because every test loads the whole import graph.
- **Against the simplicity override:** CLAUDE.md says "Simplicity is the override rule. No speculative abstraction." That protects against over-engineering. It does NOT protect against under-factoring. A 4.6K single-file command dispatcher is not "simple" — it's undifferentiated.
- **Recommendation:** Split into `scripts/debate/` package: `_common.py` (LLM call wrappers, prompt loading, frontmatter, redaction), one module per subcommand. Keep `debate.py` as thin entry point. No behavior change. Estimate: a few hours, big diff, zero feature risk because tests pin behavior.
- **Not a finding about:** the feature set. The feature set may be right. The file structure isn't.

### F2: Test infrastructure lies about its state (degraded mode invisible)

- **Severity:** warning
- **Source:** inspected
- **Evidence:**
  - Prior audit (line 6) claims "24 Python test files (819 tests, all passing)".
  - `python3.11 -c "import pytest"` → `ModuleNotFoundError: No module named 'pytest'`. No pytest in `/opt/homebrew/lib/python3.11/site-packages/`, no pytest binary on `PATH`.
  - `bash tests/run_all.sh` just now: `pytest not installed — skipping pytest suite`. Six smoke tests from `test_debate_smoke.py` and `test_tool_loop_config.py` ran. Exit code 0.
  - `tests/run_all.sh` lines 8–14: `if command -v pytest &>/dev/null; then pytest tests/ -q; else echo "pytest not installed — skipping pytest suite"; fi`.
- **Why fresh eyes:** The Essential Eight includes "degraded mode visible." The test runner's degraded mode (no pytest → run 6 of 819 tests, exit 0) is **not visible** in any aggregate. Hooks don't fail CI. The run_all.sh exit code stays green. An audit claiming "819 passing" while 813 weren't executed is exactly the lie this invariant was supposed to prevent.
- **Recommendation:**
  1. Add `requirements.txt` (or `requirements-dev.txt`) pinning `pytest`, `pytest-asyncio`. Addresses prior F11 simultaneously.
  2. Change `tests/run_all.sh`: when pytest is missing, **exit non-zero** and print a loud banner. Current silent skip is the bug.
  3. Never cite test counts in an audit without re-running the suite. Prior audit's "819 tests passing" either was stale when written or ran in a different environment. Either way, the number is not meaningful without a replay command.

### F3: Task artifact accumulation outpaces archival (170 active / 79 archived)

- **Severity:** warning
- **Source:** inspected
- **Evidence:**
  - `ls tasks/*.md | wc -l` → 170 active markdown files.
  - `ls tasks/_archive | wc -l` → 79.
  - Many active topics look shipped-or-rejected: `autobuild-*` (6 files), `audit-batch2-*` (6), `context-optimization-v2-proposal.md`, `gstack-vs-buildos-retest-v2/v3/v4.md`, `buildos-feedback-explore.md`, `boilerplate-extraction-explore.md`, `canonical-skill-sections-*` (4).
  - `/start` routing reads `ls -t tasks/*-review.md tasks/*-plan.md ...` (from `.claude/skills/start/SKILL.md:130`). Every stale artifact is a potential false routing match that Step 2b has to filter out.
- **Why fresh eyes:** The prior audit counted artifacts and moved on. The issue is the derivative — artifacts are accruing faster than they get archived, and `/start` pays the cost every session. Step 2b ("Verify candidate actions before recommending") exists *because* of this. The hook is treating a symptom.
- **Recommendation:** Define an archival criterion ("topics with a `-review.md` status=passed AND commit hash recorded are movable to `_archive/`"). Run it as a manual pass monthly or as a step inside `/wrap`. Target: `ls tasks/*.md` under 50 at any given time. Anything older than 30 days without an active follow-up goes to archive.

### F4: 21 `decision-audit-dN.md` files — one-time artifact still in live space

- **Severity:** info
- **Source:** inspected
- **Evidence:** `ls tasks/decision-audit-d*.md | wc -l` → 21 files, one per decision D1–D21. `tasks/decisions.md` is 157 lines (the canonical source). The per-decision audit files appear to be outputs from a one-time cleanup exercise.
- **Why fresh eyes:** Duplicate surface area. If decisions.md is canonical, these are cruft. If the per-decision audits have ongoing value, they should be referenced from decisions.md (they aren't — grep returns no cross-refs).
- **Recommendation:** Move `decision-audit-d*.md` to `tasks/_archive/` unless any are still in-flight. One-command fix: `mv tasks/decision-audit-d*.md tasks/_archive/`.

### F5: Session discipline erosion visible — ~40% of recent sessions skip `/wrap`

- **Severity:** info
- **Source:** inspected
- **Evidence:** `git log --oneline -30 | grep "\[auto\]"` → 9 of the last 30 commits are auto-captures from the Stop hook ("Session work captured 2026-04-16 …"). These fire when a session ends without `/wrap`. The auto-commit message template says "Review and enrich in the next session" — meaning the next session has to clean up. The session-log tail shows 4 of the last 10 entries are `[auto-captured: session ended without /wrap-session]`.
- **Why fresh eyes:** This is L25 (review-after-build has no enforcement) repeating at a different layer. The `/wrap` skill is advisory. Under context pressure, the Stop hook catches the work, but the enrichment debt accumulates. The framework's own core discipline rule has degraded into a catch-net. That's a lesson, not a hook; it needs to either become a hook (session-end check that blocks) or get structurally accepted (reframe `/wrap` as optional, let the Stop hook be the contract).
- **Recommendation:** Decide: promote or demote. Either (a) move wrap to a Stop-hook check that fails if session state wasn't summarized, or (b) officially relegate `/wrap` to "optional polish" and make auto-capture the real contract. Current state (hard rule in session-discipline.md, advisory in practice) is the worst of both.

### F6: Seven hooks chained on PreToolUse:Write|Edit — no latency measurement

- **Severity:** info
- **Source:** inspected
- **Evidence:** `.claude/settings.json` PreToolUse:Write|Edit block has 7 hooks: decompose-gate, guard-env, tier-gate, pre-edit-gate, memory-size-gate, read-before-edit, context-inject. Declared timeouts sum to 38s worst-case per Edit. No telemetry on actual cumulative hook latency anywhere — no `stores/hook-timings.jsonl`, no `hook-error-tracker.py` output for successful runs, just errors.
- **Why fresh eyes:** Recent commits ("Reduce runtime context waste", "hook dedup cache + ruff truncation", "Move 4 reference files to on-demand loading") show the user is already feeling this. But the optimization is proceeding without measurement — which means it's guessing at hotspots. The value each hook adds vs its latency cost is unmeasured. Claude 4.7's perspective: hooks are the right architectural primitive, but the enforcement ladder (lesson → rule → hook → architecture) has no retirement path. Nothing demotes. A hook that was worth it at L3 may be redundant once an adjacent hook lands.
- **Recommendation:** Add a one-liner to each hook: append `{hook, elapsed_ms, blocked}` to `stores/hook-timings.jsonl`. Once a week, query for hooks with high latency and low block rate — those are candidates for demotion. Without this, the hook count only goes up.

### F7: The framework is its own main user (meta-gravity)

- **Severity:** info (structural, not actionable this sprint)
- **Source:** inferred (from tasks/ contents, session-log topics)
- **Evidence:**
  - 22 active task topics are BuildOS itself: `debate-engine-upgrades`, `debate-py-bandaid-cleanup`, `canonical-skill-sections`, `context-optimization-v2`, `skill-rename-spec`, `review-unification-plan`, `tier-aware-plan`, `gstack-vs-buildos`, `buildos-feedback-explore`, etc.
  - The PRD (`docs/project-prd.md`) is still the template (prior audit F10 — unresolved across two audits).
  - `/elevate`, `/challenge`, `/pressure-test`, `/polish` — the full ambition apparatus — is being applied to developing BuildOS, not to a product BuildOS governs.
- **Why fresh eyes:** This isn't a bug, but it changes the calibration of every other finding. When the governance framework's main customer is itself, complexity additions always pencil ("we'll use it"), because the framework is also the test-bed. The pressure to simplify has to come from outside — from an actual product built on top. Without a real downstream consumer, BuildOS risks becoming a perfect tool for building BuildOS.
- **Recommendation:** Stand up one non-framework project using BuildOS end-to-end (even a trivial one — a personal todo app, a newsletter pipeline). Use it for a week. Any BuildOS friction that shows up there is a real priority; any friction that only shows up when building BuildOS itself is lower-priority. This also gives the PRD something to describe.

### F8: Contract-test coverage is shallow (green checkmarks on trivial invariants)

- **Severity:** info
- **Source:** inspected (prior audit lines 155–173) + reasoning about what's tested
- **Evidence:** Prior audit declares "Idempotency: YES — debate.py config loading, help output deterministic" and "Audit completeness: YES — debate-log.jsonl integrity verified". Config loading and help output are not the meaningful idempotency claim. JSONL well-formedness is not audit completeness.
- **Why fresh eyes:** The Essential Eight are structural contracts. The current tests verify that the *data at rest* is well-formed, not that the system's *writes* satisfy the invariant. Meaningful tests: "run the same `debate.py challenge` twice with the same inputs → produces one log entry, not two" (idempotency). "For every skill that writes to debate-log.jsonl, verify every invocation produced a row" (audit completeness). Those aren't in `tests/contracts/` based on file names.
- **Recommendation:** Low-urgency. When next touching `tests/contracts/`, upgrade at least idempotency + audit-completeness to assert against actual system behavior, not artifact well-formedness.

---

## Not findings, but worth naming

- **PRD still blank** — prior audits F3 → F10, still unresolved. Not re-filing; F7 above subsumes it.
- **`audit.db` missing** — prior F9, still unresolved. Decide (a) wire it up or (b) delete references.
- **Deploy stubs** — prior F7, still empty. Intentional per prior audit, accept.

## Summary

- **Critical:** 0
- **Warning:** 3 (F1 monolith, F2 test lies, F3 artifact accumulation)
- **Info:** 5 (F4 decision-audit cruft, F5 wrap discipline, F6 hook latency, F7 meta-gravity, F8 shallow contracts)

## Biggest lift / smallest diff wins

1. **F2** — add `requirements.txt`, make run_all.sh exit non-zero on missing pytest. ~15 minutes. Closes prior F11 too.
2. **F3 + F4** — archive sweep. ~15 minutes. Makes `/start` faster every future session.
3. **F1** — debate.py split. Half a day. Permanent ROI on every future change to that file.

## What I did NOT check

- Actual hook latencies (no telemetry to read).
- Whether `tests/contracts/` assertions are correct (only read file names from prior audit).
- Cross-model rate limits / cost patterns in `stores/debate-log.jsonl` (didn't parse the 379 entries).
- Any file in `examples/` or `templates/`.
- Whether skills correctly defer to each other per the routing table (would need simulated invocations).
