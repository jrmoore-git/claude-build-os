---
scope: "Add session telemetry that separates Tier 1 signal (context-file reads at session start) from Tier 2 signal (hook fires/blocks mid-execution). One new hook, one shared emit helper, one analysis script, 6 existing hooks instrumented, /wrap writes session_outcome. Enables queries: which hooks actually block real work, which context files actually get read, and whether sessions that skipped key context files produce more /review findings."
surfaces_affected: "hooks/hook-session-telemetry.py (new), scripts/telemetry.py (new), scripts/telemetry.sh (new, conditional on latency gate), scripts/session_telemetry_query.py (new), .claude/settings.json, .claude/skills/wrap/SKILL.md, hooks/hook-plan-gate.sh, hooks/hook-review-gate.sh, hooks/hook-pre-edit-gate.sh, hooks/hook-decompose-gate.py, hooks/hook-bash-fix-forward.py, hooks/hook-memory-size-gate.py, stores/session-telemetry.jsonl (data, created on first write)"
verification_commands: "python3.11 -m py_compile hooks/hook-session-telemetry.py scripts/telemetry.py scripts/session_telemetry_query.py && python3.11 scripts/session_telemetry_query.py hook-fires --window 1d && python3.11 scripts/session_telemetry_query.py context-reads --window 1d && bash -n hooks/hook-plan-gate.sh hooks/hook-review-gate.sh hooks/hook-pre-edit-gate.sh"
rollback: "git revert <sha>; rm stores/session-telemetry.jsonl (append-only log, no dependents)"
review_tier: "Tier 2"
verification_evidence: "New hook + helper + query script compile and import cleanly; running a short test session produces session_start + context_read + hook_fire + session_outcome events in stores/session-telemetry.jsonl; query script produces non-empty tables; each of 6 instrumented hooks emits hook_fire on a forced decision path; /wrap run at session close appends session_outcome with outcome_source='wrap' and populated commits+findings+lessons counts; closing terminal without /wrap produces session_outcome with outcome_source='session-end' (SessionEnd backup path); existing PostToolUse:Read hooks (spec-status-check, read-before-edit) still fire and produce their prior output after telemetry is appended to the chain."
challenge_skipped: true
challenge_skipped_reason: "Conversational gate sequence served as /challenge: user asked 'anything worth building?' twice (skepticism screen), asked what the telemetry would concretely do, asked open questions answered before plan. Scope is narrow (diagnostic infrastructure, no user-facing surface, no data mutation outside append-only log), and answers are load-bearing for cutting dead hooks."
allowed_paths:
  - hooks/hook-session-telemetry.py
  - hooks/hook-plan-gate.sh
  - hooks/hook-review-gate.sh
  - hooks/hook-pre-edit-gate.sh
  - hooks/hook-decompose-gate.py
  - hooks/hook-bash-fix-forward.py
  - hooks/hook-memory-size-gate.py
  - scripts/telemetry.py
  - scripts/telemetry.sh
  - scripts/session_telemetry_query.py
  - stores/session-telemetry.jsonl
  - .claude/settings.json
  - .claude/skills/wrap/SKILL.md
  - tasks/session-telemetry-plan.md
components:
  - emit-pipeline
  - analysis-script
---

# Plan: Session Telemetry — Separate Tier 1 from Tier 2 Signal

## Why

BuildOS has two distinct value claims — session-infrastructure (handoff / current-state / decisions files read at start) and governance (21 hooks that gate actions mid-execution) — with no current way to tell them apart. Without that split, any pilot answer ("Build OS helps" / "doesn't help") is one blended number, and internal calls about which hooks to cut are hunch-driven. This plan adds the minimum telemetry to separate the two layers.

## Store

`stores/session-telemetry.jsonl` — one JSON object per line, append-only. POSIX `O_APPEND` is atomic for writes < PIPE_BUF (4KB on macOS); events are ~200 bytes. No rotation until file exceeds 100MB (years away at realistic volume).

## Event Schema

One flat schema with `event_type` discriminator:

| event_type | fields |
|---|---|
| `session_start` | `session_id`, `ts`, `cwd`, `branch`, `topic` (first user prompt, truncated to 200 chars) |
| `context_read` | `session_id`, `ts`, `file_path` (only for watchlist files; see below) |
| `hook_fire` | `session_id`, `ts`, `hook_name`, `tool_name`, `decision` (`allow`/`block`/`warn`), `reason` (short string) |
| `session_outcome` | `session_id`, `ts_end`, `commits` (list of hashes since session_start), `review_findings_count`, `lessons_created_count`, `shipped` (bool), `outcome_source` (`wrap` \| `session-end`) |

**Context-read watchlist:** `docs/current-state.md`, `tasks/handoff.md`, `tasks/lessons.md`, `tasks/session-log.md`, `docs/project-prd.md`, `tasks/*-plan.md`. Other Read calls are not logged (keeps signal clean, keeps file small).

**Session ID resolution:** `$CLAUDE_SESSION_ID` if set, else parent PID — matches existing convention in `hook-decompose-gate.py`.

## Build Order

| # | Step | Files | Verification |
|---|---|---|---|
| 0 | Pre-flight: verify clean tree, existing hooks all pass syntax check | — | `git status --short`; `bash -n hooks/*.sh`; `python3.11 -m py_compile hooks/*.py` |
| 1 | Write `scripts/telemetry.py` — single function `log_event(event_type: str, **kwargs)`. Reads `CLAUDE_SESSION_ID` (env) with PID fallback. Auto-creates `stores/` dir if missing (`os.makedirs(stores_dir, exist_ok=True)`). Serializes JSON, opens `stores/session-telemetry.jsonl` with `O_APPEND`, writes one line, closes. ~35 LOC. | `scripts/telemetry.py` | `python3.11 -c "import sys; sys.path.insert(0,'scripts'); from telemetry import log_event; log_event('session_start', cwd='/tmp', branch='test', topic='smoke')"` → appends one line to store. Delete `stores/` dir and re-run → dir auto-created, event written. |
| 2 | Write `hooks/hook-session-telemetry.py`. Reads stdin hook payload (JSON), branches on hook event type: `SessionStart` → emit session_start (pull cwd + branch from `git`); `PostToolUse:Read` → if file in watchlist, emit context_read; `SessionEnd` → emit minimal session_outcome with `outcome_source: "session-end"`, scan git log for commits since session_start_ts, leave findings/lessons counts at 0 and `shipped: false`. Before writing session-end outcome, tail the JSONL for an existing `session_outcome` with matching `session_id` from `/wrap` — if found, skip (avoid duplicate; /wrap output is authoritative). Exits 0 silently on any error (telemetry must never break a session). ~80 LOC. | `hooks/hook-session-telemetry.py` | Simulate each event type via stdin JSON; verify correct event emitted; verify non-watchlist Read is ignored; verify SessionEnd skips write when a wrap outcome already exists for same session_id; verify error path exits 0 without writing |
| 2.5 | **Verify handler chain compatibility.** Existing `PostToolUse:Read` chain has `hook-spec-status-check.py` + `hook-read-before-edit.py`. Confirm new telemetry hook (a) runs as the last handler in the chain, (b) returns no decision (observer-only — no JSON with `decision` field, no non-zero exit that would block), (c) does not mutate stdin payload state other hooks depend on. Also confirm no existing `SessionStart` or `SessionEnd` handlers need to compose with the new one (current settings has none). | `.claude/settings.json`, `hooks/hook-session-telemetry.py` | Read current settings; manually trace handler order; dry-run telemetry hook against a real Read payload and confirm existing Read hooks' behavior is unchanged (spec-status-check still prints its warning, read-before-edit still logs) |
| 3 | Register hook in `.claude/settings.json` — add `SessionStart` handler, `SessionEnd` handler, and append telemetry as the final entry in the existing `PostToolUse:Read` chain (do NOT create a parallel Read chain; extend the existing one). Keep existing hooks intact. | `.claude/settings.json` | `jq .` parses clean; start a fresh Claude Code session; `stores/session-telemetry.jsonl` gets a session_start line within 2s; end the session by closing terminal (bypasses /wrap) → SessionEnd outcome appears with `outcome_source: "session-end"` |
| 4 | Instrument 6 existing hooks to emit `hook_fire`. Each hook adds one `telemetry.log_event("hook_fire", hook_name=..., tool_name=..., decision=..., reason=...)` call at each decision point (allow/block/warn). Do NOT change hook logic. Hooks: `plan-gate`, `review-gate`, `pre-edit-gate`, `decompose-gate`, `bash-fix-forward`, `memory-size-gate`. **Per-hook workflow (do all three for each hook before moving to next):** (a) add emit line; (b) **emission assertion** — feed a synthetic stdin payload that forces each decision path (allow/block/warn) and grep JSONL tail for a matching `hook_fire` event; fail build if missing; (c) **latency gate** — time 100 synthetic invocations with and without the emit line; if p95 delta >15ms, swap the shell-hook emitter for `scripts/telemetry.sh` (jq-based one-liner: `jq -nc --arg ... '{...}' >> stores/session-telemetry.jsonl`) before continuing to the next hook. Python hooks (`decompose-gate`, `bash-fix-forward`, `memory-size-gate`) import telemetry directly — no fork cost, no wrapper needed. | 6 hook files, conditionally `scripts/telemetry.sh` | Per-hook: synthetic payload → matching hook_fire event appears; p95 latency delta <15ms on shell hooks (or telemetry.sh in place) |
| 5 | Modify `.claude/skills/wrap/SKILL.md` — add a final procedure step: "Emit session_outcome event with `outcome_source: "wrap"`, commits (git log since session_start_ts), review_findings_count (count of `tasks/*-review.md` files with severity findings touched this session), lessons_created_count (lines added to `tasks/lessons.md` in this session's commits), shipped (true if a ship artifact was produced)." | `.claude/skills/wrap/SKILL.md` | Run `/wrap` on a test session; verify session_outcome event appears with `outcome_source: "wrap"` and populated fields |
| 6 | Write `scripts/session_telemetry_query.py` — argparse with three subcommands: `hook-fires --window Nd`, `context-reads --window Nd`, `outcome-correlate <file_path>`. Reads JSONL, groups, prints plain-text tables. **Malformed-line tolerance:** skip unparseable lines silently; emit `"N malformed lines skipped"` to stderr at end if any. **Session outcome classification:** sessions are bucketed as `wrap-completed` (outcome_source='wrap'), `session-end-backup` (outcome_source='session-end'), or `fully-abandoned` (no outcome event). `hook-fires`: per-hook block/warn/allow counts. `context-reads`: per-file read rate — denominator includes all 3 buckets. `outcome-correlate`: bucket sessions by read-vs-skipped of <file_path>, compare avg `review_findings_count` — include only `wrap-completed` sessions in numerators (they have populated findings counts); report `session-end-backup` + `fully-abandoned` counts as a separate "outcome-incomplete" row for transparency. **Candidates footer (HARD):** every output must end with: `"Findings are candidates for investigation, not evidence for deletion. Read-of-file ≠ file-actually-used-in-reasoning; outcome-correlate bucketing depends on /wrap completeness. Validate patterns before acting."` ~140 LOC. | `scripts/session_telemetry_query.py` | All 3 subcommands run without error on empty file (graceful empty output) and on a populated file from Steps 2-5 smoke runs; inject a malformed line (invalid JSON) and confirm query still runs and reports count on stderr; confirm footer appears on every subcommand output |
| 7 | Final verification: fresh session smoke test — start Claude Code, read `tasks/handoff.md`, trigger one hook block (e.g., attempt Edit with no prior Read), run `/wrap`. Verify all 4 event types appear in the JSONL and all 3 query subcommands produce sensible output. | (all above) | JSONL has session_start, ≥1 context_read, ≥1 hook_fire, 1 session_outcome; query output matches expected counts |
| 8 | Commit | (above + this plan) | `git status --short` clean except `stores/session-telemetry.jsonl` (data, expected) |

## Files

| File | Op | Notes |
|---|---|---|
| `scripts/telemetry.py` | NEW | ~30 LOC. Single `log_event` function. stdlib only. |
| `hooks/hook-session-telemetry.py` | NEW | ~80 LOC. Event routing across SessionStart / PostToolUse:Read / SessionEnd. Silent-on-error. SessionEnd branch tails JSONL to avoid duplicating /wrap's outcome. |
| `scripts/session_telemetry_query.py` | NEW | ~140 LOC. argparse + 3 subcommands. Malformed-line tolerance, session bucketing (wrap-completed / session-end-backup / fully-abandoned), candidates footer. |
| `scripts/telemetry.sh` | NEW (conditional) | Only if Step 4's latency gate triggers. ~10 LOC jq-based shell emitter for shell hooks. |
| `.claude/settings.json` | MODIFY | Add SessionStart + SessionEnd handlers; append telemetry hook as final entry in existing PostToolUse:Read chain (do not create parallel chain). |
| `.claude/skills/wrap/SKILL.md` | MODIFY | Add final procedure step to emit session_outcome. |
| `hooks/hook-plan-gate.sh` | MODIFY | +1 emit line per decision point. |
| `hooks/hook-review-gate.sh` | MODIFY | +1 emit line per decision point. |
| `hooks/hook-pre-edit-gate.sh` | MODIFY | +1 emit line per decision point. |
| `hooks/hook-decompose-gate.py` | MODIFY | +1 emit line per decision point. |
| `hooks/hook-bash-fix-forward.py` | MODIFY | +1 emit line per decision point. |
| `hooks/hook-memory-size-gate.py` | MODIFY | +1 emit line per decision point. |
| `stores/session-telemetry.jsonl` | NEW (data) | Created on first write. Not tracked in git if `stores/` is already gitignored — otherwise add to `.gitignore`. |

## Execution Strategy

**Decision:** sequential within each component; components fan out only after Step 1.
**Pattern:** pipeline with one shared dependency.
**Reason:** Every downstream step depends on `scripts/telemetry.py` (Step 1). Once the helper exists, emit-pipeline (Steps 2-5) and analysis-script (Step 6) could parallelize — but the analysis script wants real events to test against, so sequential-after-Step-5 is cleaner. Single agent, no worktree fan-out; no file collisions likely.

## Verification

```bash
# 1. Syntax check
python3.11 -m py_compile hooks/hook-session-telemetry.py scripts/telemetry.py scripts/session_telemetry_query.py
bash -n hooks/hook-plan-gate.sh hooks/hook-review-gate.sh hooks/hook-pre-edit-gate.sh

# 2. Smoke: emit one of each event type via direct invocation
python3.11 -c "
import sys; sys.path.insert(0,'scripts')
from telemetry import log_event
log_event('session_start', cwd='/tmp', branch='test', topic='smoke')
log_event('context_read', file_path='tasks/handoff.md')
log_event('hook_fire', hook_name='test', tool_name='Write', decision='block', reason='smoke')
log_event('session_outcome', commits=[], review_findings_count=0, lessons_created_count=0, shipped=False)
"
tail -4 stores/session-telemetry.jsonl  # expect 4 well-formed JSON lines

# 3. Query script runs on populated file
python3.11 scripts/session_telemetry_query.py hook-fires --window 1d
python3.11 scripts/session_telemetry_query.py context-reads --window 1d
python3.11 scripts/session_telemetry_query.py outcome-correlate tasks/handoff.md

# 4. Fresh session smoke — /wrap path (manual)
# - Start fresh Claude Code session
# - Read tasks/handoff.md
# - Attempt an Edit with no prior Read (triggers pre-edit-gate block)
# - Run /wrap
# - Expect: session_start + ≥1 context_read + ≥1 hook_fire + 1 session_outcome (outcome_source: "wrap") in JSONL

# 5. Fresh session smoke — SessionEnd backup path (manual)
# - Start fresh Claude Code session
# - Read tasks/handoff.md
# - Close terminal without /wrap
# - Expect: session_outcome with outcome_source: "session-end", commits populated, counts at 0
```

## Rollback

```bash
git revert HEAD
rm stores/session-telemetry.jsonl  # safe: append-only log, no dependents
```

No schema changes, no data migration. Removing the file and reverting the commit fully restores prior behavior — every instrumentation point is additive.

## Risk Notes

- **Hook latency.** Every tool call adds one fork + JSON append. Measured cost must stay <10ms per call. If any individual hook shows regression, revert just that hook's emit line (the helper + main telemetry hook stay in place).
- **Shell hook emission.** Shell hooks invoking python3.11 per decision add a subshell start (~30ms). Step 4's per-hook latency gate (time 100 invocations, p95 delta must be <15ms) forces the fix if needed — if triggered, swap in `scripts/telemetry.sh` (jq-based, ~10 LOC) before continuing. Not deferred.
- **Session ID collisions with PID fallback.** Short-lived sessions with recycled PIDs could theoretically collide. Accept as acceptable noise at this scale; `$CLAUDE_SESSION_ID` should be set in most cases anyway.
- **`/wrap`-dependency for outcome.** `/wrap` is the authoritative outcome writer with populated findings/lessons/shipped. `SessionEnd` hook emits a minimal backup outcome (commits only) when `/wrap` is skipped, so most sessions have some outcome event. True "abandoned" sessions (neither fires — e.g., OS crash) are labeled as such in analysis, not dropped from denominators.
- **Privacy.** Event payloads include first user prompt (truncated) and file paths. No tool arguments, no file contents, no credentials. Review before extending schema.
- **Gate-enforcement self-check.** `hook-session-telemetry.py` itself must NOT be in the `hook_fire` emit list — it's an observer, not a gate. Avoid recursion.

## Open Questions Resolved

1. **`Stop` vs `/wrap` for session_outcome** → `/wrap` is authoritative (emits `outcome_source: "wrap"` with full fields); `SessionEnd` hook emits a minimal backup outcome (`outcome_source: "session-end"`, commits only, counts at 0) if `/wrap` hasn't already written one for this session. Both are built into Steps 2-3 + 5. Sessions with no outcome event at all (neither `/wrap` nor `SessionEnd` fired — e.g., OS crash) are labeled "abandoned" in analysis output.
2. **Per-event files vs one JSONL** → one JSONL. Volume math fits; POSIX append is atomic at event size; revisit at 100MB.
3. **Retrofit existing hooks vs emit-from-today** → emit-from-today, instrument only the 6 hooks that actually gate behavior (plan-gate, review-gate, pre-edit-gate, decompose-gate, bash-fix-forward, memory-size-gate). Passive hooks (syntax-check, ruff-check, context-inject) carry no decision signal worth correlating.
