# Handoff — 2026-04-16 (Frame lens plan on disk, ready to build)

## Session Focus
Recovered the Frame lens design that was being worked on in a prior session (1678d9f8) but never committed. Pulled validation artifacts from the Jarvis project on macmini, confirmed the failure mode from real debate output, and wrote the implementation plan.

## Decided
- Frame lens implemented as a 4th persona slot (not a separate phase). Same parallel-execution machinery as architect/security/pm. Output uses existing `## Challenges` format with `ALTERNATIVE` and `ASSUMPTION` type tags.
- Model: `claude-sonnet-4-6`. Frame critique is focused reasoning, not wide synthesis. Opus 4.6 is the fallback if Sonnet produces weak critiques during validation.
- Validation gate: replay gbrain proposal through the new lens. Must surface ≥1 of (Candidate E either/or framing, missing hybrid/compositional storage, Question 1 pre-bakes SQLite). Plus false-positive check on `tasks/buildos-improvements-proposal.md`.
- No separate `/challenge` cycle on this plan — the case for building came from a real failure (gbrain debate), and the previous session's conversation already debated and approved the 4-part fix.

## Implemented
- `tasks/frame-lens-plan.md` — full implementation plan with valid frontmatter (scope, surfaces_affected, verification_commands, rollback, review_tier, verification_evidence, allowed_paths). Lists 7 file changes + validation procedure + rollback path.
- Pulled from macmini to `/tmp/gbrain-validation/`: `gbrain-adoption-proposal.md`, `gbrain-adoption-judgment.md`, `gbrain-adoption-refined.md`, `hybrid-knowledge-arch-design.md`. These are the validation inputs.

## NOT Finished
- No code changes yet. The plan is the deliverable for this session.
- Frame lens implementation (changes 1-7 from the plan) — execute next session.
- Validation runs (gbrain replay + buildos-improvements false-positive) — execute after changes 1-3 land.
- `/review` on the implementation diff — required before commit (skill + rule are protected paths).

## Next Session Should
1. Read `tasks/frame-lens-plan.md` first.
2. Execute changes 1-3 atomically (`debate_common.py` + `debate.py` + `config/debate-models.json`). The persona only works if all three land together.
3. Run gbrain validation: `python3.11 scripts/debate.py challenge --proposal /tmp/gbrain-validation/gbrain-adoption-proposal.md --personas frame --enable-tools --output /tmp/frame-lens-gbrain-replay.md`
4. If validation passes: ship Step 6 skill update + lesson L41 + rule + tests, run `/review`, commit.
5. If validation fails: iterate on the prompt in `FRAME_PERSONA_PROMPT` (debate.py), re-run, then proceed.

## Key Files Changed
- `tasks/frame-lens-plan.md` (new)
- `docs/current-state.md` (overwritten)
- `tasks/handoff.md` (this file)
- `tasks/session-log.md` (appended)

## Doc Hygiene Warnings
None. The "source-driven proposals inherit the source's frame" lesson is queued as L41 inside the plan and ships when the Frame lens ships (per the plan's Change 6).
