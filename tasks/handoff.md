# Handoff — 2026-04-17 (Frame lens shipped + n=5 validation method established)

## Session Focus
Implemented the Frame lens per recovered plan, refined via empirical n=5 paired validation, ran cross-model `/review`, and shipped. Established a methodology (L44) for grounding LLM tuning decisions in quality-first paired comparisons rather than n=1 speculation.

## Decided
- **D28** — Frame lens ships as 4th `/challenge` persona with dual-mode expansion under `--enable-tools` (frame-structural: claude-sonnet-4-6, no tools; frame-factual: gpt-5.4, tools on). Cross-family routing reduces correlation between halves.
- Refined approach beyond original plan: dual-mode + cross-family added based on n=5 paired validation evidence.
- Validator scope fix shipped alongside (orthogonal): `_validate_challenge` scoped to `## Challenges` section.
- Frontmatter dict serialization fix shipped alongside (orthogonal): `_build_frontmatter` expands nested dicts as YAML keys.

## Implemented
- `scripts/debate.py`: frame + frame-factual prompts; persona expansion; per-challenger `use_tools`; output header with persona names; validator scope fix; fallback flip moved before persona expansion (review-found bug).
- `scripts/debate_common.py`: `frame_factual_model` config schema + nested-dict frontmatter serialization.
- `config/debate-models.json`: frame + frame_factual_model keys.
- `.claude/skills/challenge/SKILL.md`: frame in default persona list (Step 1, Step 6, Step 7).
- `.claude/rules/review-protocol.md`: Frame lens paragraph in Stage 1.
- `tasks/lessons.md`: L43, L44.
- `tasks/decisions.md`: D28.
- `tasks/frame-lens-plan.md`: implementation_status: shipped, shipped_commit: bfdf4ff, refinement section.
- `tasks/frame-lens-validation.md`: full n=5 paired evidence (3 rounds).
- `tasks/frame-lens-review.md`: cross-model review artifact (PASSED).
- `tests/test_debate_pure.py`: validator scope tests + `TestFramePersona` class (6 tests).
- 965 tests pass (was 957).

## NOT Finished
- Sonnet structural latency outlier (324s on litellm-fallback in cross-family run) — separate investigation; NOT blocking ship.
- Application of paired audit to other personas — primary goal of next session.
- Lessons triage (34/30 over target — see Doc Hygiene Warnings).
- `docs/current-state.md` was updated this wrap; otherwise post-ship doc hygiene was not needed.

## Next Session Should
1. Apply the n=5 paired-output-quality audit method (per L44) across all other personas: architect (Opus 4.7), security (GPT-5.4), pm (Gemini 3.1 Pro). For each: tools-on vs tools-off on the same 5 historical proposals. Determine where the verification-vs-reasoning tool-posture axis from L43 generalizes.
2. Same audit on other multi-model dispatch systems: judge round (verdict), refine rotation (3-round refinement), `/review` lenses (PM/Security/Architecture), `/polish` rounds (6-round cross-model refinement), `/explore` directions (3+ divergent), `/pressure-test` models (counter-thesis, premortem). For each: which model family fits which task, which need tools, where cross-family vs same-family matters.
3. Triage `tasks/lessons.md` to ≤30 active entries — candidates: L41 (hook-symlink — now resolved, archive); L43 (frame-lens dual-mode — promote to `.claude/rules/` after the broader audit).
4. Optionally: investigate the Sonnet structural latency outlier (324s on litellm-fallback). Probably a one-off, but track if pattern.

## Key Files Changed
- scripts/debate.py, scripts/debate_common.py, config/debate-models.json
- .claude/skills/challenge/SKILL.md, .claude/rules/review-protocol.md
- tasks/lessons.md, tasks/decisions.md, tasks/session-log.md, tasks/frame-lens-plan.md
- tasks/frame-lens-validation.md, tasks/frame-lens-review.md, tasks/frame-lens-review-debate.md (new)
- tests/test_debate_pure.py
- stores/debate-log.jsonl

## Doc Hygiene Warnings
- ⚠ Lessons at 34/30 active — triage needed before adding more. Promotion candidates: L41 (resolved), L43 (could promote to rules/ after broader audit lands).
