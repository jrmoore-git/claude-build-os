---
scope: "Ship bundle 1 of BuildOS improvements: structural review gate hook (#1), hook-class tagging + pruning rubric doc + telemetry-query rubric awareness (#2 post-shipped-telemetry), /review dismissed-finding convention (#3-descoped). Applies 5 inline fixes from buildos-improvements-challenge.md."
surfaces_affected: "hooks/hook-post-build-review.py, hooks/hook-intent-router.py, .claude/settings.json, docs/reference/hook-pruning-rubric.md, scripts/session_telemetry_query.py, hooks/hook-*.py, hooks/hook-*.sh, .claude/skills/review/SKILL.md, .claude/rules/review-protocol.md"
verification_commands: "python3.11 hooks/hook-post-build-review.py --selftest && python3.11 -m pytest tests/ -k 'not integration' -q && python3.11 scripts/session_telemetry_query.py hook-fires --window 7d && grep -l '# hook-class:' hooks/hook-*.py hooks/hook-*.sh | wc -l && test -f docs/reference/hook-pruning-rubric.md && grep -q 'negative example' .claude/rules/review-protocol.md"
rollback: "git revert per commit (3 logical commits: B hygiene, C convention, A review-gate hook). Each commit is self-contained; reverting A alone leaves B and C in place safely."
review_tier: "Tier 2"
verification_evidence: "PENDING"
allowed_paths:
  - hooks/hook-post-build-review.py
  - hooks/hook-intent-router.py
  - .claude/settings.json
  - docs/reference/hook-pruning-rubric.md
  - scripts/session_telemetry_query.py
  - hooks/hook-*.py
  - hooks/hook-*.sh
  - .claude/skills/review/SKILL.md
  - .claude/rules/review-protocol.md
  - tasks/buildos-improvements-bundle-1-plan.md
  - tasks/buildos-improvements-*.md
  - tasks/session-log.md
  - tasks/handoff.md
  - docs/current-state.md
  - tests/test_hook_post_build_review.py
components:
  - Hook-class tagging + pruning rubric doc + telemetry query awareness
  - Review learning convention (manual annotation to rules file)
  - Structural review gate hook (PostToolUse counter + flag + intent-router injection)
challenge_artifact: tasks/buildos-improvements-challenge.md
parent_proposal: tasks/buildos-improvements-proposal.md
---

# BuildOS Improvements — Bundle 1

## Context

**What shipped in other sessions (matters to this plan):**
- `fee8ee0` — Session telemetry is live. `scripts/telemetry.py`, `scripts/telemetry.sh`, `scripts/session_telemetry_query.py`, `hooks/hook-session-telemetry.py` all present. 6 enforcement hooks emit `hook_fire` events.
- `d2a0da2` — Opus 4.6→4.7 bump across production. No conflict with this plan.

**What this plan is:** layers the pruning rubric and review-gate on top of shipped telemetry. Does not re-plan telemetry itself.

**Change mapping:**
- Original #1 (structural review gate) → Component A
- Original #2 (telemetry-then-prune) → Component B (rubric-only, since telemetry already shipped)
- Original #3 (review learns from dismissed findings, descoped) → Component C
- Original #4, #5, #6 → deferred to `buildos-improvements-bundle-2` (hygiene, separate plan)
- Original #7 → held

## Inline fixes from challenge (must land in this plan)

| Fix | From Challenge | Applied in |
|---|---|---|
| 1 | `PostToolUse:Write\|Edit` isn't a platform event; use generic `PostToolUse` + JSON filter | Component A, Step A2 |
| 2 | Specify re-fire policy (re-fire every 5 edits past threshold until review artifact) | Component A, Step A1 + A3 |
| 3 | Replace `fire_rate × block_rate` with two-class rubric | Component B, Steps B1 + B3 |
| 4 | Replace "2 weeks" with ≥30-session gate | Component B, Step B3 |
| 5 | Descope #3 to manual annotation convention | Component C (entire scope) |

## Execution Strategy

**Decision:** sequential (in main session, no worktree fan-out)
**Pattern:** linear — B → C → A
**Reason:** Combined scope is <250 lines net. Worktree overhead exceeds savings. Components are logically independent but shipping B first means the class tags exist before Component A's new hook needs to declare its own class. Component C is pure doc — slots anywhere. Component A last because it has the most test surface.

| Subtask | Files | Depends on | Isolation |
|---|---|---|---|
| B1 — rubric doc | `docs/reference/hook-pruning-rubric.md` (new) | — | main session |
| B2 — class tags | all `hooks/hook-*.{py,sh}` + `pre-commit-banned-terms.sh` | B1 | main session |
| B3 — query script awareness | `scripts/session_telemetry_query.py` | B2 | main session |
| C — review convention | `.claude/skills/review/SKILL.md`, `.claude/rules/review-protocol.md` | — | main session |
| A1 — hook-post-build-review | `hooks/hook-post-build-review.py` (new) | B2 (needs own class tag) | main session |
| A2 — intent-router read | `hooks/hook-intent-router.py` | A1 | main session |
| A3 — settings.json register | `.claude/settings.json` | A1, A2 | main session |
| A4 — tests | `tests/test_hook_post_build_review.py` (new) | A1-A3 | main session |

**Synthesis:** run full verification suite after each commit (B, C, A) before proceeding.

## Build Order

### Component B — Hook class tags + pruning rubric

#### B1: Write `docs/reference/hook-pruning-rubric.md` (~1 page)

Content structure:
- **Why two classes:** `fire_rate × block_rate` breaks for advisory/injection hooks where `block_rate = 0` by design.
- **Three classes defined:**
  - **advisory/injection** — emits `decision=warn` or never fires `hook_fire` at all (e.g., context-inject, intent-router, decompose-gate, new post-build-review). Pruning criterion: qualitative — "does this change observable agent behavior?" Not volume-based.
  - **enforcement-low** — can `decision=block` but on low-stakes paths (skill-lint, syntax-check, ruff). Pruning criterion: `fire_count < 5` in 30+ sessions AND `block_rate < 10%`.
  - **enforcement-high** — blocks on high-stakes paths (guard-env, plan-gate, review-gate, pre-edit-gate, agent-isolation, memory-size-gate, bash-fix-forward). **Exempt from volume-based pruning regardless of fire rate.** A zero-fire rate on a high-stakes enforcement hook means the guard is working, not that it's dead weight.
- **Session-count gate:** do not attempt pruning until `≥30 sessions` observed in telemetry (defined as sessions with a `session_start` event + any subsequent `hook_fire` OR `session_outcome`).
- **Classification source of truth:** each hook file carries a `# hook-class: <class>` comment on a top line. Query script reads from file, not from a separate registry (avoids drift).

#### B2: Tag every hook file

Add to the top of each hook file (after shebang, before docstring):

```python
# hook-class: advisory | enforcement-low | enforcement-high
```

Tagging decisions (pre-classified against the rubric):

| Hook | Class | Rationale |
|---|---|---|
| hook-guard-env.sh | enforcement-high | Blocks secret exposure |
| hook-plan-gate.sh | enforcement-high | Blocks commit on protected paths without plan |
| hook-review-gate.sh | enforcement-high | Blocks commit on protected paths without review artifact |
| hook-pre-edit-gate.sh | enforcement-high | Blocks edits outside allowed_paths |
| hook-agent-isolation.py | enforcement-high | Blocks cross-worktree writes |
| hook-memory-size-gate.py | enforcement-high | Blocks memory file over limit |
| hook-bash-fix-forward.py | enforcement-high | Blocks destructive shortcuts (rm .git/index.lock, kill -9) |
| hook-tier-gate.sh | enforcement-high | Blocks when tier declaration missing |
| hook-pre-commit-tests.sh | enforcement-low | Runs tests, reports, doesn't hard-block typical flows |
| hook-skill-lint.py | enforcement-low | Validates skill YAML; typo-level blocks |
| hook-syntax-check-python.sh | enforcement-low | Blocks syntax errors |
| hook-ruff-check.sh | enforcement-low | Blocks lint failures |
| pre-commit-banned-terms.sh | enforcement-low | Blocks banned vocabulary; candidate for removal in bundle-2 |
| hook-post-tool-test.sh | enforcement-low | Runs post-write smoke checks |
| hook-prd-drift-check.sh | enforcement-low | Warns on PRD drift |
| hook-spec-status-check.py | enforcement-low | Warns on missing shipped-status in specs |
| hook-read-before-edit.py | advisory | Injects context; doesn't block |
| hook-context-inject.py | advisory | Injects test/import/git context |
| hook-intent-router.py | advisory | Routes intent; suggestion injection only |
| hook-decompose-gate.py | advisory | Advisory nudge (emits warn but never blocks) |
| hook-error-tracker.py | advisory | Observer only |
| hook-session-telemetry.py | advisory | Observer only |
| hook-post-build-review.py (new, A1) | advisory | Counter + flag; never blocks |

Total: 23 hook files classified. 8 enforcement-high, 8 enforcement-low, 7 advisory.

#### B3: Update `scripts/session_telemetry_query.py`

Changes:
1. Add `_load_hook_classes() -> dict[str, str]` — scans `hooks/hook-*.{py,sh}` at script startup, greps for `# hook-class: X`, returns `{hook_name: class}` map. Unknown hooks default to `"unknown"`.
2. Modify `cmd_hook_fires` — add `class` column between `hook` and `allow`; group output by class (enforcement-high first, then enforcement-low, then advisory, then unknown); keep existing columns.
3. Add `_session_count() -> int` — counts unique `session_id`s with a `session_start` event in the window.
4. Add `cmd_prune_candidates(args)` — new subcommand. If `session_count < 30`, prints: "Insufficient data: N sessions observed, 30 minimum. Re-run after more sessions accrue." and exits. Otherwise, applies rubric:
   - **enforcement-high:** never a candidate regardless of fire rate (prints "exempt — enforcement-high" line).
   - **enforcement-low:** candidate if `fire_count < 5` AND `block_rate < 10%`.
   - **advisory:** never a volume-based candidate; prints "qualitative review required — no volume signal".
5. Footer unchanged.

Existing `cmd_context_reads` and `cmd_outcome_correlate` are untouched.

**Commit B:** "Hook class tags + pruning rubric (#2 from buildos-improvements)"

### Component C — Review learning convention (descoped #3)

#### C1: Edit `.claude/skills/review/SKILL.md`

Add one line to the skill's output template (the block that describes what `/review` prints at completion):

```
> If you dismissed findings from this review, append each to `.claude/rules/review-protocol.md` under the "Negative Examples from Dismissed Findings" section before commit.
```

#### C2: Edit `.claude/rules/review-protocol.md`

Add new section at the end of the file:

```markdown
## Negative Examples from Dismissed Findings

When a `/review` finding is dismissed (confirmed false positive), append it here under the relevant lens. Future `/review` runs read this section and treat these as patterns to not re-flag.

### PM lens negative examples
<!-- append dismissed PM-lens findings as markdown list items -->

### Security lens negative examples
<!-- append dismissed Security-lens findings -->

### Architecture lens negative examples
<!-- append dismissed Architecture-lens findings -->
```

(Current `scripts/debate.py cmd_review` does not yet read this section — that wiring is a future bundle. For bundle-1, the convention and section exist; accumulated examples become the data to wire later.)

**Commit C:** "Review learning convention: dismissed findings → review-protocol.md (#3-descoped)"

### Component A — Structural review gate hook

#### A1: Write `hooks/hook-post-build-review.py`

Pseudocode:

```python
#!/usr/bin/env python3.11
# hook-class: advisory
"""Post-build review gate — tracks edits since last /review within active plan.

Flow:
  PostToolUse (Write|Edit) → read payload → filter on tool_name →
    if no active plan: exit 0 (no counter maintained)
    else: increment counter in /tmp/claude-review-${SESSION_ID}.json
    if counter >= 10 AND no review artifact for plan topic: set flag=needs_review
    if counter >= 10 + 5k AND flag still set: re-fire (bump re_fire_count)

State file schema:
  {
    "session_id": str,
    "plan_topic": str | null,
    "edit_count": int,
    "last_review_check_count": int,
    "flag": "clear" | "needs_review",
    "re_fire_count": int
  }

Active plan detection:
  Scan tasks/*-plan.md; pick most-recent with implementation_status != shipped.
  Topic = frontmatter topic field or slug from filename.

Review artifact check:
  test -f tasks/<plan-topic>-review.md.
  If exists and mtime > plan mtime: flag = "clear", reset counter.

Telemetry emission:
  Every invocation: log_event('hook_fire', hook_name='post-build-review',
    tool_name=tool_name, decision='allow', reason=<'plan-active'|'no-plan'|'flag-set'|'flag-clear'>)
"""
```

Concrete behavior:
- Always exits 0. Never blocks.
- Silent on errors (telemetry.log_event is silent-on-error).
- State file is per-session; cleaned up naturally when `/tmp` rolls.
- Includes `--selftest` entrypoint that simulates 15 Write payloads and verifies counter behavior + flag transitions.

Estimated LOC: 100-130 (per revised Fix 1 estimate).

#### A2: Modify `hooks/hook-intent-router.py`

Read the state flag on every UserPromptSubmit invocation:

```python
# After existing proactive-suggestion logic:
flag_file = Path(f"/tmp/claude-review-{session_id()}.json")
if flag_file.exists():
    state = json.loads(flag_file.read_text() or "{}")
    if state.get("flag") == "needs_review":
        # Non-suppressible. Bypass already_suggested() for this key.
        suggestions.append(
            "PROACTIVE ROUTING: You've made {edit_count} edits in plan '{plan_topic}' "
            "without running /review. Run /review before commit. "
            "(This reminder re-fires every 5 edits until a review artifact exists — "
            "it doesn't go away silently.)"
        )
```

Key distinction: **do not call `already_suggested("review-post-build")`**. That's the whole point — this suggestion must repeat, not de-duplicate.

Estimated LOC delta: 15-20 lines.

#### A3: Update `.claude/settings.json`

Add a new PostToolUse.Write|Edit handler entry after the existing hook-session-telemetry.py entry. Structure (insertion point already identified from inspection):

```json
{
  "type": "command",
  "command": "python3 \"$CLAUDE_PROJECT_DIR/hooks/hook-post-build-review.py\"",
  "timeout": 2
}
```

No other handlers change.

#### A4: Write `tests/test_hook_post_build_review.py`

Cover:
- No active plan → counter stays 0, telemetry emits `reason=no-plan`.
- Active plan, <10 edits → counter increments, no flag.
- Active plan, 10 edits → flag=needs_review, telemetry `reason=flag-set`.
- Active plan, 15 edits, flag still set → re_fire_count = 1.
- Active plan, review artifact created → flag clears, counter resets.
- Malformed state file → hook exits cleanly, regenerates state.
- Non-Write/Edit tool (e.g., Read) → no counter increment.

Estimated: 6-8 test functions, ~120 lines.

**Commit A:** "Structural review gate: post-build hook + re-fire policy (#1 from buildos-improvements)"

## Files

| Status | Path | Scope |
|---|---|---|
| **create** | `hooks/hook-post-build-review.py` | new advisory hook, counter + flag |
| **create** | `docs/reference/hook-pruning-rubric.md` | two-class rubric + 30-session gate |
| **create** | `tests/test_hook_post_build_review.py` | A4 tests |
| **modify** | `hooks/hook-intent-router.py` | read flag, inject non-suppressible suggestion |
| **modify** | `.claude/settings.json` | register new hook on PostToolUse.Write\|Edit |
| **modify** | `scripts/session_telemetry_query.py` | class-aware output, prune-candidates subcommand, session-count gate |
| **modify** | `.claude/skills/review/SKILL.md` | one-line reminder in output template |
| **modify** | `.claude/rules/review-protocol.md` | new "Negative Examples" section |
| **modify** | all 22 existing hook files in `hooks/` | `# hook-class: X` tag |

## Verification

### Per-commit checks

**After B:**
- `grep -c '^# hook-class:' hooks/hook-*.{py,sh} | cut -d: -f2 | sort -u` → verify all 23 files tagged
- `python3.11 scripts/session_telemetry_query.py hook-fires --window 7d` → output includes `class` column, groups shown
- `python3.11 scripts/session_telemetry_query.py prune-candidates` → prints "Insufficient data" message (current session count is low)
- `test -f docs/reference/hook-pruning-rubric.md`

**After C:**
- `grep -q "Negative Examples from Dismissed Findings" .claude/rules/review-protocol.md`
- `grep -q "append each to.*review-protocol.md" .claude/skills/review/SKILL.md`

**After A:**
- `python3.11 hooks/hook-post-build-review.py --selftest` exits 0
- `python3.11 -m pytest tests/test_hook_post_build_review.py -v` → all pass
- Full test suite stays green: `python3.11 -m pytest tests/ -k 'not integration' -q`
- Synthetic session: create `tasks/fake-plan.md` with status draft, feed 15 Write payloads via `--selftest`, verify flag set at edit 10 and re-fires at edit 15, then create `tasks/fake-review.md` and verify flag clears.
- Inspect `stores/session-telemetry.jsonl` tail — new `hook_fire` events with `hook_name=post-build-review`.

### Definition of Done
- [ ] 23 hook files tagged with `# hook-class:`
- [ ] Rubric doc exists
- [ ] telemetry-query script has class column + prune-candidates subcommand + session-count gate
- [ ] /review skill output has reminder line
- [ ] review-protocol.md has Negative Examples section template
- [ ] hook-post-build-review.py exists + self-test passes
- [ ] intent-router reads flag + emits non-suppressible suggestion
- [ ] settings.json registers new hook
- [ ] Tests for new hook pass
- [ ] Full test suite green (923+ tests)
- [ ] No edits to telemetry engine code (`scripts/telemetry.py`, `hooks/hook-session-telemetry.py`) — those are stable
- [ ] No edits to historical plan doc (`tasks/session-telemetry-plan.md`) — that's a past artifact

## Non-goals

- No changes to `scripts/debate.py` or the monolith extraction workstream
- No wiring of the review-protocol.md negative examples into `cmd_review` prompt (future bundle)
- No edits to telemetry emission infrastructure (`scripts/telemetry.py`, `hooks/hook-session-telemetry.py`)
- No hook deletions — pruning decisions happen after this ships and data accrues
- No changes to Opus model references (done in d2a0da2)
- No migration of `stores/` JSONL format

## Rollback

Each commit is independent:
- Revert A → review-gate hook disappears; B's rubric + C's convention stay intact
- Revert B → hook tags + rubric + query awareness disappear; A and C stay intact
- Revert C → docs reminder + negative-examples section disappear; A and B stay intact

If all three revert: zero net change vs pre-plan state.
