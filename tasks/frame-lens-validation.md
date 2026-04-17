---
topic: frame-lens-validation
created: 2026-04-17
related_plan: tasks/frame-lens-plan.md
related_lessons: [L43, L44]
---

# Frame Lens Validation

Empirical validation of the Frame lens added to `/challenge`. Three rounds of paired comparisons grounded the design decisions in n≥4 evidence rather than n=1.

## Round 1: Tools-on vs tools-off (n=4)

**Hypothesis:** Tool access biases frame critique toward positive-space enumeration.

**Method:** Same persona prompt run twice per proposal — once with `--enable-tools`, once without. Compared MATERIAL finding counts and content.

**Proposals:** gbrain-adoption (known-bad frame), buildos-improvements, gstack-vs-buildos, managed-agents-dispatch.

**Results:**

| Proposal | Tools-on MATERIAL | Tools-off MATERIAL | Mode-exclusive findings |
|---|---|---|---|
| gbrain | 2 | 3 | ≥2 each direction |
| buildos | 2 | 3 | ≥2 each direction |
| gstack | 3 | 3 | ≥2 each direction |
| managed | 2 | 3 | ≥2 each direction |

**Tools-on uniquely caught factual contradictions** (commit staleness, config mismatches). Tools-off uniquely caught structural reasoning gaps (problem inflation, missing compositional candidates, premature abstraction). Findings were ≥2 mode-exclusive on every proposal — neither mode dominated.

**Latency:** Tools-on ~75s and ~28 tool calls per run; tools-off ~31s and 0 tool calls. Tools added 2.4x latency.

**Decision:** Adopt dual-mode (run BOTH halves in parallel) rather than picking one. Both catch real defects of different kinds. Captured as L43.

## Round 2: New dual-frame vs historical 3-persona panel (n=5)

**Hypothesis:** The dual-mode Frame lens adds findings beyond what the original 3-persona panel (architect, security, pm) catches.

**Method:** Ran new dual-mode frame on 5 historical proposals that already had `/challenge` outputs on disk. Compared frame-only findings against the historical 3-persona findings.

**Proposals:** autobuild, explore-intake, learning-velocity, streamline-rules, litellm-fallback.

**Results:**

| Proposal | Historical verdict | Frame added (novel MATERIAL) | Notes |
|---|---|---|---|
| autobuild | REVISE | 6 | binary framing, /plan --auto unverified, SKILL.md constraint conflict, rollback gap, fabricated CloudZero/gstack citations |
| explore-intake | REVISE | 6 | intake may not be binding constraint, composition-only candidate missing, preflight-tracks.md doesn't exist, cmd_explore actual location |
| learning-velocity | REVISE | 5 | age-vs-wrongness unverified, change-coupled trigger, lesson_events.py already exists, prune-candidates already shipped, hook count 17→23 |
| streamline-rules | REVISE | 7 | Phase-1-only candidate, inline-compression alternative, 2-of-4 contradictions already resolved, hook-mismatch governance drift |
| litellm-fallback | REVISE | 1 critical + 4 others | **Feature already shipped — verdict flipped to REJECT** |

**Net: ~30 novel MATERIAL findings across 5 proposals. Zero regressions on historical findings. One verdict shift (REVISE → REJECT) prevented a wasted sprint.**

**Frame-unique catches by class:**
- **"Already shipped" detection (5/5)** — original 3-persona panel caught this 0/5 times
- **Binary framing / missing compositional candidates (4/5)** — architect critiques structure, not the candidate set
- **Source-driven proposals (3/5)** — meta-pattern none of architect/security/pm look for
- **Problem inflation / Phase-2 over-engineering (3/5)** — pm checks scope but not whether scope is justified by problem severity

**Historical-unique catches (frame doesn't replace existing personas):**
- Security: prompt injection from user-derived context (explore-intake), prompt injection from freeform lesson text (learning-velocity)
- Concurrency: 429 risk on parallel persona dispatch (litellm-fallback)
- Trust boundaries (multiple)
- Retry-loop UX interactions

**Decision:** Frame is additive, not substitutive. Add it to the default persona list alongside architect, security, pm.

## Round 3: Cross-family vs same-family (n=5)

**Hypothesis (initial):** Routing frame-factual to a different model family than frame-structural reduces correlation between halves.

**Method:** Same 5 historical proposals. Same-family configuration: structural=sonnet, factual=sonnet. Cross-family: structural=sonnet, factual=gpt-5.4. Compared finding quality (not count, not speed).

**Results — quality comparison:**

| Proposal | Cross-family BETTER? | Why |
|---|---|---|
| autobuild | Yes | GPT caught architectural critiques (`/plan --auto` not verified, SKILL.md ≤500-line constraint conflicts with stateful needs). Sonnet caught more nits but missed structural problems. |
| explore-intake | Yes | GPT named the actual extracted module (`debate_explore.py` per commit `6bbde96`); identified existing `DIMENSIONS:` block parsing falsifying "no context composition" claim. Sonnet's findings were thinner. |
| learning-velocity | Tie | Same critical staleness catches; different secondary findings of similar weight. |
| streamline-rules | Yes (different shape) | GPT caught "orchestration.md edit would create new rule/hook mismatch" — meta-level governance drift. Sonnet caught more individual file mismatches but missed the meta-issue. |
| litellm-fallback | Yes | Both caught "already shipped." GPT also caught two nuanced gaps: `_FALLBACK_MODEL` is hardcoded contradicting "session's own Claude model" claim, tool-loop paths reject Anthropic fallback. Sonnet just confirmed shipped status. |

**4/5 cross-family BETTER (more architectural, higher precision per finding, better synthesis of staleness implications). 1/5 TIE. Zero regressions.**

**Speed (secondary observation):** Cross-family runs averaged ~34s wall vs same-family ~102s wall (~3x faster). Caused by GPT-5.4 converging on consequential findings in fewer tool calls (15-21 vs Sonnet's 40-58). Speed is a side effect of better convergence, not the primary justification.

**Outlier:** litellm-fallback frame-structural (Sonnet, no tools) ran 324s on the cross-family pass — exceeded the 180s parallel deadline. Unrelated to cross-family change (structural has tools forcibly off). Tracked as a separate Sonnet latency issue.

**Decision:** Default `frame_factual_model` to `gpt-5.4` in `config/debate-models.json`. Same-family remains available via config override.

## Cost summary

| Metric | Before (3-persona) | After (3-persona + dual-frame cross-family) | Delta |
|---|---|---|---|
| Wall time per /challenge | ~60-90s | ~95-120s | +30-50s |
| API cost per /challenge | ~$0.10-0.15 | ~$0.15-0.25 | +$0.05-0.10 |
| Code surface added | — | ~80 lines in debate.py, 1 new prompt, 1 config field | minimal |
| Maintenance burden | — | Low — reuses existing dispatch | minimal |
| Risk added | — | Purely additive; single git revert restores prior behavior | minimal |

## Lessons captured

- **L43:** Tool access biases frame critique toward positive-space enumeration. Dual-mode (structural tools-off + factual tools-on) catches distinct failure classes. Cross-family reduces correlation.
- **L44:** N=1 is not data. LLM tuning decisions must ground in paired output-quality comparisons across n≥3 (ideally 5+) representative inputs. Quality first; speed/cost secondary.

## Caveats and validation hygiene

The Round 1 gbrain test included `docs/current-state.md` in the model's tool scope, where the original failure mode was self-documented. GPT-5.4 explicitly cited that file. This is a **validation artifact**, not a production concern (fresh proposals don't have pre-written post-mortems). For future calibration: hold out self-documented failure files, or use proposals whose outcomes aren't on disk. The frame-factual prompt now instructs the model to weight code/config/commit history over retrospective notes, but doesn't structurally prevent the read.

## Open research questions

- Does the verification-vs-reasoning tool-posture axis generalize to other personas (architect, pm)? Paired audit across all 4 personas on 2-3 proposals would test it.
- Sonnet structural latency outlier (324s on litellm-fallback): one-off or pattern? Worth tracking.

## Artifacts

- Round 1 outputs: `/tmp/frame-pairs/*.md` (8 files, n=4 paired)
- Round 2 outputs: `/tmp/frame-historical/*-dual.md` (5 files, same-family dual-mode)
- Round 3 outputs: `/tmp/frame-crossfamily/*.md` (5 files, cross-family dual-mode)
- Final reference run: `/tmp/frame-crossfamily-gbrain.md` (gbrain with cross-family default)
