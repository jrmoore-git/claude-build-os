---
topic: frame-reach-intake-audit
created: 2026-04-17
related_plan: tasks/frame-reach-intake-audit-plan.md
ground_truth: tasks/frame-lens-validation.md (Round 2)
threshold: LOCKED per plan — three gates, all must pass
verdict: DECLINE
---

# Frame-Reach Intake Audit — Results

## Verdict

**VERDICT: DECLINE** — Gate 3 (negative control 0 MATERIAL) fails: negative-control intake produced 2 MATERIAL findings. Gates 1 and 2 pass, but per plan all three gates must pass (AND, not OR). No re-fitting per L45.

## Per-Proposal Reproduction

### autobuild

**Round 2 novel MATERIAL findings (ground truth):**
- binary framing
- `/plan --auto` unverified
- SKILL.md constraint conflict
- rollback gap
- fabricated CloudZero/gstack citations

**Intake MATERIAL findings (both challengers combined):**
1. A1: 60-80 LOC estimate understates stateful multi-step loop surface (behavioral spec gap)
2. A2: Missing candidate — step-gated semi-autonomous build with explicit checkpoints
3. A3: Escalation protocol designed for planning contexts, not mid-tool-loop; unverified that it fires during implementation
4. B1: `/ship` stage and "Step 6 in /ship" referenced as existing but verify-plan-progress.py shows no ship artifact stage (already-shipped inverse: claimed-shipped-but-absent)
5. B2: Decompose gate is advisory-only, not a deterministic parallel dispatcher as proposal implies
6. B3: Scope containment claim ("no new hook needed") not implemented — hooks do not enforce plan-declared surfaces_affected
7. B4: 60-80 LOC no-new-scripts sizing is too small for promised behavior; current deterministic behavior lives in code/hooks

**Reproduction mapping:**
| Round 2 tag | Intake match? | Match evidence |
|---|---|---|
| binary framing | YES | A2 "proposal frames the choice as manual build vs. full autobuild loop. A missing middle candidate is semi-autonomous build..." |
| /plan --auto unverified | YES | B1 challenges that claimed existing-infrastructure surfaces (/ship stage, Step 6) aren't verifiable in repo; B2 pins decompose gate as advisory not deterministic — both are the same "claimed-shipped infrastructure isn't what proposal says" class |
| SKILL.md constraint conflict | YES | A1 + B4 both name the same defect: SKILL.md text cannot drive a stateful multi-step loop; behavioral spec > prose |
| rollback gap | NO | Not found — no intake finding addresses rollback/reversal story |
| fabricated CloudZero/gstack citations | PARTIAL→NO | A4 (ADVISORY only) notes CloudZero/gstack citations not verifiable; MATERIAL tier does not raise it. Counted as NO since rubric is MATERIAL-only. |

**Reproduction rate:** 3/5 = 60% (below 70%)

Note: If "/plan --auto unverified" is treated strictly (specific `/plan --auto` command staleness not directly named), the rate drops to 2/5 = 40%. Either reading puts autobuild below the 70% floor.

### explore-intake

**Round 2 novel MATERIAL findings (ground truth):**
- intake may not be binding constraint
- composition-only candidate missing
- preflight-tracks.md doesn't exist
- cmd_explore actual location

**Intake MATERIAL findings (both challengers combined):**
1. A1: Intake question design may not be the binding constraint — bottleneck may be in explore-diverge.md or explore-synthesis.md, not intake
2. A2: Research sources (Motivational Interviewing, Mom Test, FBI elicitation) are human-to-human and may not transfer to LLM async text intake
3. A3: Missing candidate — post-hoc intake (show directions first, then refine)
4. A4: Missing candidate — structured form intake (short fixed 3-question form, simultaneous)
5. A5: 5-slot adaptive sequence over-specified as prompt; LLM cannot reliably follow 8+5+7 rules simultaneously
6. B1: Target files (preflight-adaptive.md, preflight-tracks.md) don't appear in shipped explore path — cmd_explore loads explore.md, explore-diverge.md, explore-synthesis.md
7. B2: cmd_explore extracted to debate_explore.py (commit 6bbde96); debate.py only re-exports — plan targets wrong file
8. B3: No direct test file for debate_explore.py; redesign needs tests

**Reproduction mapping:**
| Round 2 tag | Intake match? | Match evidence |
|---|---|---|
| intake may not be binding constraint | YES | A1 verbatim: "unverified that the current system's weak link is question design rather than context block composition" |
| composition-only candidate missing | YES | A3 (post-hoc intake) and A4 (structured form) — compositional alternatives. A closer match: A1's suggestion that composition rules alone could be the fix. Final verdict line: "implement context block composition rules now... as v5.1" — composition-only is explicitly named. |
| preflight-tracks.md doesn't exist | YES | B1 verbatim: "searches for `preflight-adaptive.md` and `preflight-tracks.md` in repo code/docs returned no matches" |
| cmd_explore actual location | YES | B2 verbatim: "cmd_explore has already been extracted into scripts/debate_explore.py... commit 6bbde96" |

**Reproduction rate:** 4/4 = 100% (above 70%)

### learning-velocity

**Round 2 novel MATERIAL findings (ground truth):**
- age-vs-wrongness unverified
- change-coupled trigger
- lesson_events.py already exists
- prune-candidates already shipped
- hook count 17→23

**Intake MATERIAL findings (both challengers combined):**
1. A2: Passive recurrence counter missing as cheaper first step; hook-error-tracker.py already captures signatures
2. A3: /healthcheck full-scan runs infrequently — tension between metrics cadence and verification cadence
3. B1: scripts/lesson_events.py already computes learning-velocity metrics (resolution time, recurrence, 30-day counts, stale-rate) — not greenfield work
4. B2: hooks/hook-session-telemetry.py + scripts/session_telemetry_query.py already has `prune-candidates` mode with thresholds
5. B3: "Current measurement: none" is false — lesson_events.py + scripts/check-current-state-freshness.py exist

**Reproduction mapping:**
| Round 2 tag | Intake match? | Match evidence |
|---|---|---|
| age-vs-wrongness unverified | YES (ADVISORY→no) | A1 raises exactly this defect: "stale by date is a reliable proxy for likely wrong" — but tagged ADVISORY, not MATERIAL. Rubric is MATERIAL-only → counted as NO. |
| change-coupled trigger | YES (ADVISORY→no) | A1: "A git-blame-based trigger (files referenced in this lesson were modified since lesson was written) would be more precise than age alone" — exact match, but tagged ADVISORY → counted as NO. |
| lesson_events.py already exists | YES | B1 verbatim: "scripts/lesson_events.py already computes learning-velocity metrics... this is not greenfield work" |
| prune-candidates already shipped | YES | B2 verbatim: "scripts/session_telemetry_query.py already exposes ... a built-in `prune-candidates` mode" |
| hook count 17→23 | NO | Not found — no intake finding raises the hook count discrepancy |

**Reproduction rate (MATERIAL-only, strict):** 2/5 = 40% (below 70%)

Note: If ADVISORY findings that name the same defect are counted, rate becomes 4/5 = 80%. Rubric states MATERIAL-only → strict reading applies. Either way the hook count 17→23 is missed.

### streamline-rules

**Round 2 novel MATERIAL findings (ground truth):**
- Phase-1-only candidate
- inline-compression alternative
- 2-of-4 contradictions already resolved
- hook-mismatch governance drift

**Intake MATERIAL findings (both challengers combined):**
1. A1: Cross-file reference compliance unverified — Claude may not reliably load referenced files
2. A2: Not all 15 files loaded in every session; canonical placement may cause governance regression
3. A3: Missing candidate — inline annotation rather than cross-file reference (terse inline compression)
4. B1: Baseline inventory stale — CLAUDE.md not in manifest, reference path is docs/reference not .claude/rules/reference
5. B2: Several "current contradictions" already shipped (workflow.md already delegates to CLAUDE.md, security.md already tightened, orchestration.md already compressed)
6. B3: "Essential eight invariant" contradiction phrasing not verifiable — one of four headline contradictions unsupported

**Reproduction mapping:**
| Round 2 tag | Intake match? | Match evidence |
|---|---|---|
| Phase-1-only candidate | YES | A4 (ADVISORY)... wait, checking: A4 is OVER-ENGINEERED ADVISORY about Phase 3 sequencing, names Phase 1 & 3 as shippable independently. Closest MATERIAL match: A3 inline-compression candidate captures adjacent compositional framing. Counted YES because A3's "middle path" + A4's decomposition argument together reproduce "ship only Phase 1". Actually A4 is ADVISORY; A3 is MATERIAL and names Phase-bundle decomposition. Counting YES on A3. |
| inline-compression alternative | YES | A3 verbatim: "CLAUDE.md entry could be compressed to a single terse line... without creating a dependency on another file being loaded" |
| 2-of-4 contradictions already resolved | YES | B2 verbatim: "workflow.md already says... security.md already contains the tightened allowlist... orchestration.md already has the compressed relative-path guidance" |
| hook-mismatch governance drift | NO | Not found — no intake finding names the meta-level governance drift (rule edit creates new rule/hook mismatch) |

**Reproduction rate:** 3/4 = 75% (above 70%)

### litellm-fallback

**Round 2 novel MATERIAL findings (ground truth):**
- 1 critical: "Feature already shipped — verdict flipped to REJECT"
- 4 others (unnamed in ground truth)

**Intake MATERIAL findings (both challengers combined):**
1. A1: ANTHROPIC_API_KEY not guaranteed in all Claude Code configs (OAuth/SSO/keyless) — fallback silently fails same as LiteLLM down
2. A2: Missing candidate — single-model via LiteLLM itself (partial-LiteLLM case)
3. A3: Artifact format identical claim unverified — hooks gating on model diversity may silently accept lower-quality artifacts
4. B1: scripts/llm_client.py already implements direct Anthropic fallback (_dispatch detects connection-refused, loads ANTHROPIC_API_KEY, flips _FALLBACK_ACTIVE, routes to _anthropic_call with _FALLBACK_MODEL — lines 536-594, 143-149); is_fallback_active, get_fallback_model, activate_fallback already exposed
5. B2: debate.py review still resolves persona-specific models, does not collapse panel in fallback (lines 3161-3244); "review-panel" subcommand named in proposal doesn't exist
6. B3: A5 echoes this — proposal re-implements what _anthropic_call + _sdk_call already do

**Reproduction mapping:**
| Round 2 tag | Intake match? | Match evidence |
|---|---|---|
| Feature already shipped (verdict-flipping) | YES | B1 verbatim: "scripts/llm_client.py already implements direct Anthropic fallback when LiteLLM is unavailable... `is_fallback_active`, `get_fallback_model`, and `activate_fallback`, so 'add fallback path' is not net-new work." A5 also: "llm_client.py already has `_anthropic_call` and `_sdk_call` functions... The proposal appears to be re-implementing what already exists." |
| 4 others (unnamed) | N/A | Cannot tag against unnamed findings; treating only the critical already-shipped tag for this proposal per ground-truth specificity. |

**Reproduction rate:** 1/1 = 100% on the named critical finding (above 70%)

## Gate Outcomes

**Gate 1 (per-proposal ≥70%):** FAIL

| Proposal | Rate | Gate |
|---|---|---|
| autobuild | 60% (3/5) | FAIL |
| explore-intake | 100% (4/4) | PASS |
| learning-velocity | 40% (2/5, MATERIAL-only strict) | FAIL |
| streamline-rules | 75% (3/4) | PASS |
| litellm-fallback | 100% (1/1 on critical) | PASS |

Two proposals below 70% floor → Gate 1 FAILS.

**Gate 2 (litellm-fallback "already-shipped"):** PASS — litellm-fallback-intake.md Challenger B finding #1: "scripts/llm_client.py already implements direct Anthropic fallback when LiteLLM is unavailable. `_dispatch()` detects connection-refused errors, loads `ANTHROPIC_API_KEY`, flips `_FALLBACK_ACTIVE`, emits the exact warning, and routes to `_anthropic_call(...)` using `_FALLBACK_MODEL` (`scripts/llm_client.py:536-594`, `143-149`)." Specific file + line refs + function names + the "_FALLBACK_ACTIVE" global + verdict implication ("'add fallback path' is not net-new work"). Unambiguously matches the verdict-flipping finding.

**Gate 3 (negative control 0 MATERIAL):** FAIL — 2 MATERIAL findings raised on negative-control-verbose-flag:
1. Challenger B #1: "`scripts/debate.py` does have `_run_challenger` (lines 1062+), but there is no `_call_llm` function in that file anymore... the real surface spans both `_call_with_model_fallback` and tool-loop integration." [MATERIAL] [COST:SMALL]
2. Challenger B #2: "the proposed 'no changes to `debate_common.py`, `debate_tools.py`, or other modules' misses that `scripts/llm_client.py` already captures richer tool-loop data... If the goal is to print tool name + arguments + return value + running token counts, the simplest accurate implementation likely needs to consume `tool_result['tool_calls']` and `tool_result['usage']` or add hooks in `llm_client.py`." [MATERIAL] [COST:SMALL]

Expected 0, observed 2 → Gate 3 FAILS.

## Notes

- **MATERIAL-only rubric is strict.** Multiple autobuild and learning-velocity Round 2 tags (rollback gap, age-vs-wrongness, change-coupled trigger, fabricated citations) were raised at ADVISORY tier in intake, not MATERIAL. Per the explicit instruction "Count items tagged [MATERIAL] only. Ignore [ADVISORY]." these count as misses. If ADVISORY matches were admitted, autobuild would rise to 4/5 = 80% and learning-velocity to 4/5 = 80%. That relaxation would be re-fitting (forbidden per L45).
- **Negative-control failures are factual-mode frame findings.** Both MATERIAL findings on negative control come from Challenger B (frame-factual, gpt-5.4). They identify real staleness (the `_call_llm` function no longer exists; scope underestimates llm_client.py coupling) — these are genuinely useful findings, not noise. But the proposal was chosen as "cleanly framed" and the gate expects silence on clean frames. The factual-mode frame persona produces findings even on proposals the structural frame approves (Challenger A verdict: APPROVE, 0 MATERIAL). This suggests frame-factual has a higher false-positive rate on clean proposals than expected when the proposal makes specific verifiable claims about existing code.
- **litellm-fallback's "already-shipped" catch is real and decisive.** Gate 2 behaves exactly as intended — the single highest-cost finding in the corpus is reliably reproduced at intake. This is the strongest positive signal in the audit.
- **explore-intake is the cleanest pass** — 4/4 at intake, including all specific file-path claims.

## Next Action

- **DECLINE ship of intake-check subcommand.** Per plan Phase 3 step 14: "If threshold failed: stop. Document in L43/L46 why intake-stage Frame doesn't reliably reproduce challenge-stage Frame. Defer judge/refine/premortem audits pending this learning."
- Do NOT loosen thresholds to force a PASS. Per L45: re-fitting after runs is a threshold change, not an adoption.
- Subsequent step (not this task): update tasks/lessons.md L43 or add L46 documenting two failure modes observed:
  1. Intake reproduces verdict-flipping factual findings reliably (Gate 2 PASS) but misses ~20-40% of structural/advisory-tier findings on two of five proposals.
  2. frame-factual produces MATERIAL findings on proposals the structural persona approves, raising the floor of false-positive noise when the audit target makes verifiable code claims.
- Judge/refine/premortem audits deferred.
