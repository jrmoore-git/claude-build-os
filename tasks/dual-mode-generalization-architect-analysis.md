---
persona: architect
model: claude-opus-4-7
threshold: 5/5 bidirectional
verdict: ADOPT
---

# Architect Persona Dual-Mode Analysis

## Per-Proposal Tagging

### Proposal: autobuild

**Tools-off MATERIAL findings:**
1. Scope containment has no enforcement mechanism; `surfaces_affected` is aspirational without a PreToolUse hook checking Edit/Write paths against the plan.
2. 3-attempt iteration limit has no per-step rollback/checkpoint; escalation leaves a half-broken tree.

**Tools-on MATERIAL findings:**
1. Proposal silently contradicts `docs/orchestrator-contract.md`, which externalizes the build loop to a runner ("BuildOS does NOT do test execution, git operations").
2. Proposal conflates `surfaces_affected` with `allowed_paths`; only `allowed_paths` is enforced by `hook-pre-edit-gate.sh`. Need to verify `/plan --auto` emits the enforced field.
3. 3-tier classification (Mechanical/Taste/User Challenge) claimed to be "reused" but `check_code_presence` shows it lives only in the `plan` skill body, not in `rules/`.
4. Decompose gate is advisory only (`hook-class: advisory`); parallel tracks without forced worktree isolation = corruption risk in autonomous mode.

**Classification:**
| Finding (brief) | Mode | tools-on-exclusive | tools-off-exclusive | shared |
|---|---|---|---|---|
| Scope enforcement gap (off #1) | off | | | X (overlaps on #2 — `allowed_paths` field naming) |
| Per-step rollback/checkpoint (off #2) | off | | X | |
| Contract contradiction (on #1) | on | X | | |
| surfaces_affected vs allowed_paths (on #2) | on | | | X (same defect family as off #1: scope enforcement) |
| Tier classification not in rules/ (on #3) | on | X | | |
| Decompose gate advisory, parallel corruption (on #4) | on | X | | |

**Mode-exclusive count:** tools-on 3 | tools-off 1
**BIDIRECTIONAL:** YES
**Reason:** Tools-off uniquely flagged per-step rollback; tools-on uniquely flagged contract contradiction, tier classification drift, and decompose-gate-advisory corruption risk.

### Proposal: explore-intake

**Tools-off MATERIAL findings:**
1. 13+ conditional rules at runtime will decay under Righting Reflex; need per-turn output scaffold (REFLECTION: / QUESTION:) to make violations visible.
2. Adaptive question count table claim "just 4" (Slot 4 alone) is structurally incoherent — Slot 4 challenges prior answers.
3. Classification step ("clear enough to act on") has no rubric; model will over-classify as "well-specified" to skip intake.
4. No verification that v6 produces more divergent directions than v5; `--help` isn't a test.

**Tools-on MATERIAL findings:**
1. Context-block sections (PROBLEM/SITUATION/TENSION/ASSUMPTIONS) are NOT parsed as discrete fields by `debate_explore.py` — only `{context}` and `{dimensions}` are templated. `explore-diverge.md`/`explore-synthesis.md` were not listed for update; the new structure is aesthetic unless those prompts reference section headers by name.
2. Rollback references `preflight-adaptive.md` but the file isn't in the config manifest; "v5" may be aspirational. Rollback clause non-executable.
3. Context composition ("3:1-5:1 compression, resolves contradictions") has no named owner — second LLM call? Intake final turn? Template-fill? Cost/latency/failure modes differ.

**Classification:**
| Finding (brief) | Mode | tools-on-exclusive | tools-off-exclusive | shared |
|---|---|---|---|---|
| Rule-density decay, need output scaffold (off #1) | off | | X | |
| Slot 4 cold-start incoherence (off #2) | off | | X | |
| Classification rubric missing (off #3) | off | | X | |
| Unverified divergence claim (off #4) | off | | | X (overlaps on #1 — both challenge whether new structure actually changes behavior) |
| Prompt templates don't consume new sections (on #1) | on | X | | |
| Rollback references nonexistent files (on #2) | on | X | | |
| Composition step has no named owner (on #3) | on | X | | |

**Mode-exclusive count:** tools-on 3 | tools-off 3
**BIDIRECTIONAL:** YES
**Reason:** Tools-off uniquely flagged runtime-rule-decay scaffolding, Slot 4 incoherence, and classification rubric. Tools-on uniquely flagged prompt-template gap, rollback file non-existence, and unnamed composition owner.

### Proposal: learning-velocity

**Tools-off MATERIAL findings:**
1. "Stalest + no activity" selection heuristic unvalidated — no evidence age correlates with staleness.
2. Rule-vs-hook redundancy check has no specified matching mechanism (string? tags? LLM?).

**Tools-on MATERIAL findings:**
1. Pruning heuristic duplicates and regresses existing `scripts/session_telemetry_query.py cmd_prune_candidates` (4-class rubric, two-gate test, block_rate signal, enforcement-high exemption). The proposed "fired in 30d?" flags correctly-calibrated hooks for deletion.
2. Measurement via git log on `tasks/lessons.md` duplicates existing `scripts/lesson_events.py` (log_event, compute_metrics, seed_from_lessons, dedicated event store). Git-log math can't distinguish promoted/archived/typo.
3. Problem reframed: capabilities exist but aren't wired into `/healthcheck`. Scope shrinks from "build three capabilities" to "integrate three existing scripts."
4. Auto-verify on stalest lessons will re-verify same lessons each scan without a "don't re-verify within N days" guard.

**Classification:**
| Finding (brief) | Mode | tools-on-exclusive | tools-off-exclusive | shared |
|---|---|---|---|---|
| Staleness heuristic unvalidated (off #1) | off | | X | |
| Redundancy match mechanism unspecified (off #2) | off | | | X (overlaps on #1/#2 in theme but different defect: off flags "no rule," on flags "rule exists but wrong") — I classified as exclusive (off) because it targets the redundancy-check specifically, whereas on #1/#2 target the lesson-pruning + metrics scripts. Reclassified: **off-exclusive**. |
| Pruning duplicates session_telemetry_query (on #1) | on | X | | |
| Metrics duplicate lesson_events.py (on #2) | on | X | | |
| Scope reframe: integration not build-new (on #3) | on | X | | |
| Re-verify guard missing (on #4) | on | X | | |

**Mode-exclusive count:** tools-on 4 | tools-off 2
**BIDIRECTIONAL:** YES
**Reason:** Tools-off uniquely flagged staleness heuristic validation and redundancy-match mechanism. Tools-on uniquely flagged existing-script duplication (session_telemetry_query, lesson_events.py), scope reframe, and re-verify guard.

### Proposal: streamline-rules

**Tools-off MATERIAL findings:**
1. Cross-file references create new failure mode if CLAUDE.md is loaded without referenced files; 2A/2G move the imperative sentence itself out (not just elaboration).
2. Phase 1A "before implementing" creates gap for mid-implementation decisions (discovered constraints, pivots).
3. No rollback/validation plan; no way to verify "same governance" claim. Should be per-phase PRs.

**Tools-on MATERIAL findings:**
1. Proposal's "current state" is stale — verified against live tree, Phase 1C, 1D, 2C, 2D, 2E, 2G are already done in rules/.
2. Claimed 1A contradiction is misquoted: session-discipline.md line 9 actually says "after deciding on them and before implementing them" — already consistent.
3. `/plan --skip-challenge` quote has zero matches in rules/ — source unverified or fabricated.

**Classification:**
| Finding (brief) | Mode | tools-on-exclusive | tools-off-exclusive | shared |
|---|---|---|---|---|
| Inline directive vs reference (off #1) | off | | X | |
| "Before implementing" wording gap (off #2) | off | | X | |
| Rollback/per-phase PR discipline (off #3) | off | | X | |
| Phase 1/2 items already shipped (on #1) | on | X | | |
| 1A contradiction misquoted (on #2) | on | X | | |
| skip-challenge quote unverified (on #3) | on | X | | |

**Mode-exclusive count:** tools-on 3 | tools-off 3
**BIDIRECTIONAL:** YES
**Reason:** Tools-off uniquely flagged design-level concerns (reference-replaces-directive, wording gap, rollback discipline). Tools-on uniquely flagged verifiable-against-repo issues (stale baseline, misquote, fabricated quote) that require filesystem access.

### Proposal: litellm-fallback

**Tools-off MATERIAL findings:**
1. Proposal assumes `ANTHROPIC_API_KEY` is in environment; Claude Code OAuth/Max users often don't have it set. Fallback must gracefully handle missing key.
2. Silent correlated-blind-spot: artifacts "identical structure" whether 3 or 1 model. Add `review_mode: single_model | multi_model` frontmatter field.

**Tools-on MATERIAL findings:**
1. Proposal's core premise is contradicted by shipped code — `debate_common._load_credentials`, `llm_client.activate_fallback`, `_anthropic_call` already exist with tests at `tests/test_debate_fallback.py` (264 lines). Proposal reinvents ~80% of existing infrastructure.
2. Detection trigger mismatch: proposal specifies runtime detection on connection failure; shipped version detects at startup by credential presence. Real gap is "LiteLLM configured but proxy down mid-session" — `_is_connection_refused` exists but doesn't call `activate_fallback`.

**Classification:**
| Finding (brief) | Mode | tools-on-exclusive | tools-off-exclusive | shared |
|---|---|---|---|---|
| ANTHROPIC_API_KEY missing handling (off #1) | off | | X | |
| review_mode frontmatter field (off #2) | off | | X | |
| Feature already implemented (on #1) | on | X | | |
| Runtime vs startup detection gap (on #2) | on | X | | |

**Mode-exclusive count:** tools-on 2 | tools-off 2
**BIDIRECTIONAL:** YES
**Reason:** Tools-off uniquely flagged Claude Code OAuth key-absence failure mode and artifact-labeling for downstream gates. Tools-on uniquely flagged that the feature is already shipped and that the real gap is runtime proxy-down detection (not missing credentials).

## Cross-Proposal Summary Table

| Proposal | Tools-off MATERIAL | Tools-on MATERIAL | tools-on-exclusive | tools-off-exclusive | BIDIRECTIONAL |
|---|---|---|---|---|---|
| autobuild | 2 | 4 | 3 | 1 | YES |
| explore-intake | 4 | 3 | 3 | 3 | YES |
| learning-velocity | 2 | 4 | 4 | 2 | YES |
| streamline-rules | 3 | 3 | 3 | 3 | YES |
| litellm-fallback | 2 | 2 | 2 | 2 | YES |

## Persona Verdict

**VERDICT: ADOPT** — All 5/5 proposals show mode-exclusive MATERIAL findings in both directions. Pre-committed threshold met.

## Notes

- **Tools-on consistently raises "already shipped / already exists" findings.** Three of five proposals (autobuild, learning-velocity, litellm-fallback, and partially streamline-rules — so actually four of five) had tools-on surface defects of the form "proposal reinvents existing infrastructure" or "proposal's current-state is stale." This is the factual-verification axis that no-tools cannot reach.
- **Tools-off consistently raises structural/design concerns** that don't require filesystem access: wording gaps, rollback discipline, correlated-blind-spot abstractions, rule-density decay under runtime pressure. These are reasoning-from-proposal-alone defects.
- **Ambiguous classification resolved:** In learning-velocity, the off finding on "redundancy match mechanism unspecified" overlapped thematically with on findings about existing pruning scripts. I classified off as exclusive because the specific defect (no match rule specified) is orthogonal to on's defect (wrong script being proposed). Different defects = not shared per rubric rule 4.
- **Ambiguous classification resolved:** In autobuild, the off finding #1 (scope enforcement gap) and on finding #2 (surfaces_affected vs allowed_paths) both target scope enforcement; I classified as shared because they point at the same mechanism (pre-edit hook enforcement against plan frontmatter). Off finding #2 (per-step rollback) has no on-side counterpart.
- **Litellm-fallback is the tightest case** at 2/2 exclusive each. Both modes produced high-signal findings; the dual-mode value was clearest here (tools-on caught "feature already shipped," tools-off caught the OAuth-key-absence failure mode that requires knowing Claude Code's auth surface).
