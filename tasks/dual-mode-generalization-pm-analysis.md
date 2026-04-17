---
persona: pm
model: gemini-3.1-pro
threshold: 5/5 bidirectional
verdict: DECLINE
---

# PM Persona Dual-Mode Analysis

## Per-Proposal Tagging

### Proposal: autobuild

**Tools-off MATERIAL findings:**
- OFF-1 [ASSUMPTION]: Autonomous build-test-iterate loop via ~80 lines of markdown prompting is unreliable; needs programmatic orchestrator.
- OFF-2 [RISK]: Context window exhaustion from single session holding plan + sequential implementation + 3-strike loops + review.

**Tools-on MATERIAL findings:**
- ON-1 [RISK]: Context window exhaustion from appending open-ended build-test-iterate loop to `/plan`; must run execution loop in a fresh session.
- ON-2 [ASSUMPTION]: Prompt-based iteration control ("max 3 attempts per step") is insufficient — LLMs hallucinate retry counts; must be enforced programmatically.

**Classification table:**
| Finding | Mode | Classification | Overlap rationale |
|---|---|---|---|
| OFF-1 | tools-off | shared with ON-2 | Both say prompt-only enforcement of iteration/loop control is unreliable, needs programmatic orchestrator. |
| OFF-2 | tools-off | shared with ON-1 | Both identify context window exhaustion from the single-session build-test loop. |
| ON-1 | tools-on | shared with OFF-2 | Same context-exhaustion defect. |
| ON-2 | tools-on | shared with OFF-1 | Same "prompting cannot enforce iteration limits" defect. |

**Mode-exclusive count:** tools-on 0 | tools-off 0
**BIDIRECTIONAL:** NO
**Reason:** Both MATERIAL findings in each mode map 1:1 to the other mode's findings (same defects: prompt-orchestration fragility + context exhaustion).

---

### Proposal: explore-intake

**Tools-off MATERIAL findings:**
- OFF-1 [ASSUMPTION]: Prompt-driven 5-slot state machine degrades; LLMs skip/blend slots without external state tracking. Fix: XML-tagged state output.

**Tools-on MATERIAL findings:**
- ON-1 [ASSUMPTION]: Same 5-slot state machine concern; must move phase tracking into the Python orchestrator (debate.py / agent loop), not pure prompts.
- ON-2 [RISK]: Mandatory 2:1 reflection-to-question ratio causes patronizing UX / "AI-splaining" fatigue; should be optional.

**Classification table:**
| Finding | Mode | Classification | Overlap rationale |
|---|---|---|---|
| OFF-1 | tools-off | shared with ON-1 | Both identify the 5-slot prompt state machine as unreliable and call for external state tracking. |
| ON-1 | tools-on | shared with OFF-1 | Same defect, different fix emphasis (orchestrator vs XML tags). |
| ON-2 | tools-on | tools-on-exclusive | UX risk about the 2:1 reflection ratio — tools-off tagged the same concern as [ADVISORY] only ("Robotic empathy"), not [MATERIAL]. Different severity = exclusive under the "only MATERIAL counts" rubric. |

**Mode-exclusive count:** tools-on 1 | tools-off 0
**BIDIRECTIONAL:** NO
**Reason:** Tools-on raised the reflection-ratio UX risk to MATERIAL; tools-off has no MATERIAL finding absent from tools-on.

---

### Proposal: learning-velocity

**Tools-off MATERIAL findings:**
- OFF-1 [ALTERNATIVE]: Simplest version builds the wrong thing — git log velocity metrics don't solve the [EVIDENCED] staleness problem; should prioritize verification/pruning over velocity.
- OFF-2 [RISK]: Pruning heuristic (hook fired in last 30 days) fails for low-frequency/high-severity guardrail hooks; needs severity awareness.

**Tools-on MATERIAL findings:**
- ON-1 [OVER-ENGINEERED]: Coupling 60-90s of blocking LLM calls to `/healthcheck` violates the healthcheck contract; move to `/audit-governance` or background job.
- ON-2 [ASSUMPTION]: Deriving velocity metrics from git log ignores existing `scripts/lesson_events.py` infrastructure with deterministic lifecycle tracking and a metrics command.

**Classification table:**
| Finding | Mode | Classification | Overlap rationale |
|---|---|---|---|
| OFF-1 | tools-off | tools-off-exclusive | "Wrong thing first — prioritize verification over velocity" is a product-sequencing critique. Not raised in tools-on (ON-2 is about *how* to compute velocity, not whether it's the right first deliverable). |
| OFF-2 | tools-off | shared with ON-3 (advisory) but ON side is ADVISORY — under rubric (MATERIAL only), OFF-2 has no MATERIAL counterpart on tools-on. tools-off-exclusive. | Tools-on raised guardrail pruning as [ADVISORY], not [MATERIAL]. |
| ON-1 | tools-on | tools-on-exclusive | Healthcheck-contract violation (latency coupling) is a distinct defect not raised in tools-off. Tools-off tagged the 60-90s latency claim as [ADVISORY] only. |
| ON-2 | tools-on | tools-on-exclusive | Cites existing `scripts/lesson_events.py` with a `metrics` command that already does this — a codebase-verification defect tools-off could not see. |

**Mode-exclusive count:** tools-on 2 | tools-off 2
**BIDIRECTIONAL:** YES
**Reason:** Tools-on caught the "already exists" infrastructure duplication (ON-2) and healthcheck-contract violation (ON-1); tools-off caught the product-sequencing issue (OFF-1) and guardrail-pruning severity gap at MATERIAL level (OFF-2).

---

### Proposal: streamline-rules

**Tools-off MATERIAL findings:**
- OFF-1 [ASSUMPTION]: Deduplicating via cross-references degrades LLM compliance; repetition increases attention. Indirection fragments attention.

**Tools-on MATERIAL findings:**
- ON-1 [RISK]: Cross-referencing degrades LLM instruction adherence (concatenation vs tool-call indirection both reduce compliance).
- ON-2 [ASSUMPTION]: Assumes all rule files are always loaded; if `.claude/rules/*.md` are attached dynamically by glob, moving invariants out of always-loaded CLAUDE.md means agent operates without them.

**Classification table:**
| Finding | Mode | Classification | Overlap rationale |
|---|---|---|---|
| OFF-1 | tools-off | shared with ON-1 | Same cross-reference-degrades-compliance defect. |
| ON-1 | tools-on | shared with OFF-1 | Same defect. |
| ON-2 | tools-on | tools-on-exclusive | Dynamic glob-loading failure mode — a codebase-specific loading-mechanism defect not surfaced by tools-off. |

**Mode-exclusive count:** tools-on 1 | tools-off 0
**BIDIRECTIONAL:** NO
**Reason:** Tools-off has no MATERIAL finding absent from tools-on.

---

### Proposal: litellm-fallback

**Tools-off MATERIAL findings:**
- OFF-1 [ASSUMPTION]: Assumes ANTHROPIC_API_KEY is in env; Enterprise/managed OAuth users may lack raw key — needs graceful error explaining both paths.
- OFF-2 [UNDER-ENGINEERED]: Anthropic Messages API has distinct structural requirements (mandatory max_tokens, system prompt extracted, user/assistant alternation); payload translation is not just a URL change.

**Tools-on MATERIAL findings:**
- ON-1 [OVER-ENGINEERED]: Proposed solution already exists — `scripts/llm_client.py` has `is_fallback_active()`, `get_fallback_model()`, `activate_fallback()`, Anthropic fallback API logic; `debate.py` has `_call_with_model_fallback`; `tests/test_debate_fallback.py` proves it works. Would duplicate/overwrite.

**Classification table:**
| Finding | Mode | Classification | Overlap rationale |
|---|---|---|---|
| OFF-1 | tools-off | tools-off-exclusive | Env-key-availability failure mode for Enterprise/OAuth users. Not raised in tools-on (which flipped the whole proposal to REJECT, making this point moot but not shared). |
| OFF-2 | tools-off | tools-off-exclusive | Anthropic API structural translation requirements. Not raised in tools-on. |
| ON-1 | tools-on | tools-on-exclusive | "Already implemented and tested" — cites specific files/functions that tools-off could not verify. Flipped verdict from APPROVE to REJECT. |

**Mode-exclusive count:** tools-on 1 | tools-off 2
**BIDIRECTIONAL:** YES
**Reason:** Tools-on caught the "already shipped" defect by verifying against the codebase; tools-off caught implementation defects (env assumption, API payload translation) that are only meaningful if the work proceeds — still MATERIAL and distinct from the "already shipped" critique.

---

## Cross-Proposal Summary Table

| Proposal | Tools-off MATERIAL | Tools-on MATERIAL | tools-on-exclusive | tools-off-exclusive | BIDIRECTIONAL |
|---|---|---|---|---|---|
| autobuild | 2 | 2 | 0 | 0 | NO |
| explore-intake | 1 | 2 | 1 | 0 | NO |
| learning-velocity | 2 | 2 | 2 | 2 | YES |
| streamline-rules | 1 | 2 | 1 | 0 | NO |
| litellm-fallback | 2 | 1 | 1 | 2 | YES |

**Bidirectional count: 2/5**

## Persona Verdict

**VERDICT: DECLINE** — Only 2/5 proposals (learning-velocity, litellm-fallback) meet the BIDIRECTIONAL bar. Pre-committed threshold was 5/5; with 3 proposals showing shared-only or tools-on-dominant findings, dual-mode does not generalize across the PM persona sample.

## Notes

- **Autobuild** is the cleanest shared-finding case: both modes independently converged on the same two defects (context exhaustion + prompt-iteration unreliability), demonstrating that the PM persona can find these without tool access.
- **Explore-intake and streamline-rules** are tools-on-dominant: tools-on caught one additional MATERIAL defect each (UX reflection-ratio risk; dynamic glob-loading assumption), but tools-off found nothing the tools-on mode missed at MATERIAL level.
- **Learning-velocity** is the strongest bidirectional case: tools-on caught a hard codebase-verification finding ("`lesson_events.py` already exists with a metrics command"), while tools-off caught a product-sequencing judgment ("build verification before velocity") that's harder to ground in tool output.
- **Litellm-fallback** is bidirectional but asymmetric in impact: tools-on's single finding was verdict-flipping ("already shipped"); tools-off's two findings were implementation-detail critiques that would still be MATERIAL if the work proceeded. Classified as bidirectional per rubric because all three are distinct defects.
- **Ambiguity handled:** In learning-velocity OFF-2 (guardrail pruning), tools-on raised the same concern but tagged it [ADVISORY], not [MATERIAL]. Per rubric rule 1 (only MATERIAL counts), this makes OFF-2 tools-off-exclusive. Same pattern applied to explore-intake's reflection-ratio finding (ON-2 MATERIAL vs OFF tagged [ADVISORY]).
- **Resolution choice:** When tools-off and tools-on findings overlap on the same mechanism but differ in *prescribed fix* (e.g., explore-intake: "XML tags" vs "Python orchestrator"), classified as shared because the defect is the same; the fix divergence is not a new defect.
