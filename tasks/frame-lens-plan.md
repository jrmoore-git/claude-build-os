---
scope: "Add a Frame lens (4th persona) to /challenge that critiques what the proposal's candidate set is missing — false-binary framings, unstated assumptions, hybrid/compositional options never enumerated."
surfaces_affected:
  - .claude/skills/challenge/SKILL.md
  - scripts/debate.py
  - scripts/debate_common.py
  - config/debate-models.json
  - .claude/rules/review-protocol.md
  - tasks/lessons.md
  - tests/test_debate_pure.py
verification_commands:
  - "python3.11 -m pytest tests/ -q"
  - "python3.11 scripts/debate.py challenge --proposal /tmp/gbrain-validation/gbrain-adoption-proposal.md --personas frame --enable-tools --output /tmp/frame-dual-gbrain.md"
rollback: "git revert <commit>. The Frame lens is additive — removing it returns /challenge to the prior 3-persona panel. No schema changes, no data migrations."
review_tier: "debate"
verification_evidence: "n=5 paired validation across historical proposals (autobuild, explore-intake, learning-velocity, streamline-rules, litellm-fallback). Dual-mode frame caught ~30 novel MATERIAL findings beyond the 3-persona panel; flipped 1 verdict (litellm-fallback REVISE → REJECT, feature already shipped). Cross-family configuration (sonnet structural + gpt-5.4 factual) BETTER on 4/5 proposals (more architectural, higher precision per finding) and TIED on 1/5. See tasks/frame-lens-validation.md for full data."
implementation_status: shipped
shipped_commit: pending
allowed_paths:
  - .claude/skills/challenge/SKILL.md
  - scripts/debate.py
  - scripts/debate_common.py
  - config/debate-models.json
  - .claude/rules/review-protocol.md
  - tasks/lessons.md
  - tasks/frame-lens-plan.md
  - tasks/frame-lens-validation.md
  - tests/test_debate_pure.py
---

## Refinement after validation (2026-04-17)

The original plan called for a single `frame` persona. Validation surfaced two refinements adopted before ship:

1. **Dual-mode expansion when `--enable-tools` is on:** evidence showed tool access biases frame critique toward positive-space enumeration (see L43). Frame now expands to `frame-structural` (no tools, structural reasoning from proposal) + `frame-factual` (tools on, verifies claims against codebase) running in parallel. Each catches a distinct failure class.

2. **Cross-family models for diversity:** factual half routes to `gpt-5.4` (config key `frame_factual_model`), structural half stays on `claude-sonnet-4-6`. Validated as better-quality findings on 4/5 historical proposals — GPT produces fewer but more architectural findings with precise citations.

3. **Validator scope fix (orthogonal):** discovered during testing that `_validate_challenge` was scanning the entire response for type tags, false-flagging Concessions section narrative items. Fixed to scope to `## Challenges` block only.

4. **Frontmatter dict serialization fix (orthogonal):** `_build_frontmatter` was emitting Python dict repr for nested values, producing invalid YAML. Fixed to expand dicts as nested key/value pairs.

# Plan: Frame Lens for /challenge

## Problem

`/challenge` runs 3 adversarial personas (architect, security, pm) that critique the candidates inside the proposal. None of them critique the **frame** — whether the candidate set is complete, whether options are presented as false binaries, whether unstated assumptions pre-bake the conclusion.

Concrete failure: gbrain-adoption proposal (Jarvis project, 2026-04-16) framed Candidate E as "store knowledge as markdown files in a git repo **instead of** SQLite." All 3 challengers correctly rejected wholesale replacement. Judge consolidated 23 findings → 14, 6 accepted, 0 dismissed. Recommendation: "reject git-markdown." But the right answer was a compositional pattern (SQLite + gbrain-shaped narrative as a TEXT column) that nobody surfaced because the proposal never enumerated it. Justin found it via independent research after the debate finished.

Artifacts (on macmini, also at `/tmp/gbrain-validation/`):
- `tasks/gbrain-adoption-proposal.md` — the bad frame
- `tasks/gbrain-adoption-judgment.md` — confirms all 3 models missed it
- `tasks/hybrid-knowledge-arch-design.md` — the right answer landed on later

## Approach

Add `frame` as a 4th persona in `/challenge`. Same parallel-execution machinery as the existing 3 personas. Its prompt critiques **the candidate set**, not the candidates. Output uses the existing `## Challenges` format with the existing `ALTERNATIVE` type tag (good fit — frame findings are "approaches not considered").

### Change 1: `scripts/debate_common.py`

Add `"frame"` to `VALID_PERSONAS`. Add to `_DEFAULT_PERSONA_MODEL_MAP` with `"claude-sonnet-4-6"` (focused critique, not wide synthesis — Sonnet is right cost/quality fit).

### Change 2: `scripts/debate.py`

Add `FRAME_PERSONA_PROMPT` to `PERSONA_PROMPTS`. The prompt's job is exclusively frame critique:

```
You are an adversarial frame reviewer. You do NOT critique the candidates in the proposal.
Instead, critique whether the candidate set itself is the right set.

Focus on:
- What option is missing from the candidate list? Especially hybrid, compositional, or
  partial-adoption variants that combine elements of the proposed candidates.
- What unstated assumption is the candidate set built on? (e.g., "the storage medium
  must be one technology" — when split-storage is viable.)
- What different question should this proposal have asked? Is the framing forcing a
  binary choice when the real space is multi-dimensional?
- Was any candidate framed as either/or against the status quo when a partial or
  compositional adoption would be cheaper and capture most of the value?
- Did the proposer fetch external context (a library, a codebase, a paper) and inherit
  its frame instead of evaluating from the problem? "Source-driven proposals" enumerate
  what the source contains, not what solves the problem.

If the proposal's frame is sound — candidates are MECE, no obvious composition is
missing, no unstated assumption is doing load-bearing work — say so. APPROVE is valid.

[same type-tag, materiality, and output-format instructions as other personas]
```

Type tags work as-is. Most frame findings will use `ALTERNATIVE` (approach not considered) or `ASSUMPTION` (unstated premise). MATERIAL/ADVISORY split applies normally.

### Change 3: `config/debate-models.json`

Add `"frame": "claude-sonnet-4-6"` to `persona_model_map`. Bump `version`.

### Change 4: `.claude/skills/challenge/SKILL.md`

Step 6 update — change "Always: **architect**, **security**, **pm**" to "Always: **architect**, **security**, **pm**, **frame**".

Step 7 — no command change required; `--personas architect,security,pm,frame` is a string addition.

### Change 5: `.claude/rules/review-protocol.md`

Add a paragraph to Stage 1 (`/challenge`): "Debate output quality is bounded by proposal frame quality. Three frontier models cannot escape a flawed frame — they optimize within it. The Frame lens is the structural fix: a 4th persona whose only job is to critique what the candidate set is missing."

### Change 6: `tasks/lessons.md`

Add lesson L41 (next free slot): "Source-driven proposals inherit the source's frame. When an agent composes a proposal by fetching external content (a repo, a library, a paper), the candidate set will be outward-in (what's in the source) rather than problem-inward (what solves the problem). Status: Promoted (Frame lens persona shipped, commit `<TBD>`)."

### Change 7: `tests/test_frame_persona.py`

Unit tests:
- `frame` is in `VALID_PERSONAS`
- `frame` resolves to a model in `persona_model_map`
- `PERSONA_PROMPTS["frame"]` exists and contains the words "missing", "candidate set", "compositional"
- `cmd_challenge` accepts `--personas frame` without error (mock the LLM call)

Integration test (manual, in plan verification): replay gbrain proposal through Frame lens.

## Validation

**Gold-standard test (gbrain replay):**

```bash
python3.11 scripts/debate.py challenge \
  --proposal /tmp/gbrain-validation/gbrain-adoption-proposal.md \
  --personas frame \
  --enable-tools \
  --output /tmp/frame-lens-gbrain-replay.md
```

PASS criteria — Frame lens output must surface at least one of:
1. Candidate E is framed as either/or against SQLite; a hybrid option (markdown-on-disk + SQLite-derived-index, gbrain's actual architecture) was never enumerated.
2. A compositional option (SQLite + gbrain's compiled-truth information shape as a TEXT column) was never enumerated.
3. Question 1 pre-bakes SQLite as the storage decision while pretending to ask about format.

If 0 of 3 surface, the lens prompt needs rework before merge.

**False-positive test (buildos-improvements-proposal):**

```bash
python3.11 scripts/debate.py challenge \
  --proposal tasks/buildos-improvements-proposal.md \
  --personas frame \
  --enable-tools \
  --output /tmp/frame-lens-buildos-falsepos.md
```

PASS criteria — ≤2 MATERIAL findings on a well-framed proposal. If the lens generates >2 MATERIAL findings on a proposal that already considered alternatives, it's noisy and the prompt needs a stronger "APPROVE is valid" anchor.

Both validation runs write to `tasks/frame-lens-validation.md` with the actual outputs and pass/fail assessment.

## Non-Goals

- Not changing the judge or refine phases. Frame findings flow into the judge same as other persona findings.
- Not gating `/plan` on frame findings differently from other findings. MATERIAL/ADVISORY split applies as-is.
- Not implementing a "frame quality score" or pre-flight check. The 4th persona IS the check.
- Not back-fixing the gbrain-adoption-refined.md spec — that's a Jarvis-repo concern, separate task.
- Not building a separate `cmd_frame_review` subcommand. Persona slot is sufficient.

## Rollback

Single git revert. The Frame lens is purely additive:
- New persona slot in config — removing it falls back to defaults
- New entry in `PERSONA_PROMPTS` dict — removing it falls back to `ADVERSARIAL_SYSTEM_PROMPT`
- One-word change to skill Step 6 — trivially reversible
- Lesson and rule are documentation-only

No schema migration, no data backfill, no API contract change.

## Review Tier

`debate`. Touches a protected skill (`.claude/skills/challenge/SKILL.md`) and protected rule file. Requires `/review` before commit. The fix itself emerged from a real failure (gbrain debate), so the case for building has empirical grounding — no separate `/challenge` cycle needed on this plan.

## Implementation Order

1. Add `frame` to `VALID_PERSONAS` + config + prompt template (atomic — all three or none).
2. Update skill Step 6.
3. Run validation: gbrain replay + buildos-improvements false-positive test. Capture in `tasks/frame-lens-validation.md`.
4. If both validations pass: add lesson + rule + tests, commit, run `/review`.
5. If gbrain validation fails: iterate on prompt, re-run, then proceed.
