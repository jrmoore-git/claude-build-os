# Handoff — 2026-04-17 (evening wrap: drift recovery)

## Session Focus
Session began with B (lessons triage) + A (/think discover on dual-mode generalization). B completed as a false-alarm grep fix. A drifted off-scope into a retrospective ROI audit of the whole debate system. User called the drift; this wrap captures state so next session can pick up on the correct task.

## ⚠ READ THIS FIRST — SCOPE CORRECTION
**The previous handoff (`0701c17`) named the task clearly:**
> "Apply the n=5 paired-output-quality audit method (per L44) across all other personas: architect (Opus 4.7), security (GPT-5.4), pm (Gemini 3.1 Pro). For each: tools-on vs tools-off on the same 5 historical proposals. Determine where the verification-vs-reasoning tool-posture axis from L43 generalizes."

**This is a dual-mode generalization question.** Methodology already exists (`frame-lens-validation` Round 1). Scoped work. ~15 paired runs.

**This is NOT:** a retrospective audit of every past `/challenge` finding to decide if the debate system "earns its cost." That became commit `1c40d6c` after I misread the user's mid-conversation "is it worth it" framing as a scope pivot rather than a motivation statement. See **L45**.

**When you start next session, re-read the "Next Session Should" section below verbatim before touching any design doc already on disk.**

## Decided
- **L45 added** — `/think discover` must re-read handoff before Phase 4 (alternatives generation). Evaluative language mid-conversation names the criterion, not a new scope. Pause and check if unsure.
- `/start` skill lesson-count grep fixed — awk-scoped to Active section before `## Promoted` header. (Task B resolution.)
- No architectural decisions. No D-entry added. The ROI-audit framing was not load-bearing enough to encode as a decision.

## Implemented
- `.claude/skills/start/SKILL.md` — grep fix for lesson count (commit `1c40d6c`)
- `tasks/lessons.md` — L45 on drift pattern (this wrap commit)
- `tasks/multi-model-skills-roi-audit-design.md` — design doc (**OFF-SCOPE**, kept as history)
- `tasks/multi-model-skills-roi-audit-phase0.md` — feasibility data (**useful regardless of scope** — `/challenge` corpus map: 451 MATERIAL findings across 66 auditable runs)
- `tasks/multi-model-skills-roi-audit-rubric.md` — labeling rubric (**OFF-SCOPE**, kept for the day ROI audit is actually asked for)

## NOT Finished
- **Dual-mode generalization audit** — the actual task. Not started. See "Next Session Should" below.
- Autopilot `debate-efficacy-study-*` file pile — 25+ untracked files, autopilot-generated earlier today, never absorbed into session-log. Triage (keep / commit / delete) deferred.
- 18 new lines in `stores/debate-log.jsonl` from autopilot activity — uncommitted; next session's /wrap will capture if it runs something that touches the log.

## Next Session Should
1. **Re-read this handoff's "⚠ READ THIS FIRST" block AND last-prior handoff's "Next Session Should" (item 1) before anything else.** The dual-mode generalization task is the live one.
2. **`/think refine` or go straight to `/plan`** on the dual-mode generalization: for each of architect / security / pm personas, run paired tools-on + tools-off on the same 5 proposals used in frame-lens-validation Round 1 (autobuild, explore-intake, learning-velocity, streamline-rules, litellm-fallback). Compare mode-exclusive MATERIAL findings per persona. Decide per-persona whether dual-mode should adopt.
3. **If dual-mode generalizes to all 3 personas:** extend the debate.py persona expansion logic (already built for Frame) to the other personas. Follow the Frame lens implementation as template. Ship with paired-validation evidence.
4. **If dual-mode generalizes to only some:** ship only for those, document why others don't benefit, add to L43.
5. **Separately, if desired:** triage the autopilot `debate-efficacy-study-*` pile (absorb, commit, or delete). This is its own small task, not blocking.
6. **Separately, if desired:** the ROI audit is a real question for a LATER session. `tasks/multi-model-skills-roi-audit-design.md` is a valid starting point when that day comes. Do not let it bleed into the dual-mode generalization task.

## Key Files Changed This Session
- `.claude/skills/start/SKILL.md` — lesson count grep (shipped in `1c40d6c`)
- `tasks/multi-model-skills-roi-audit-design.md` — off-scope design (shipped in `1c40d6c`)
- `tasks/multi-model-skills-roi-audit-phase0.md` — off-scope feasibility (shipped in `1c40d6c`)
- `tasks/multi-model-skills-roi-audit-rubric.md` — off-scope rubric (this wrap)
- `tasks/lessons.md` — L45 (this wrap)
- `docs/current-state.md` — state snapshot (this wrap)
- `tasks/session-log.md` — session entry (this wrap)

## Doc Hygiene Warnings
- ⚠ Commit `1c40d6c` is off-scope for the user's actual ask. Kept in history for honesty (no silent revert) — next session must NOT treat it as work-in-progress.
- ⚠ `tasks/multi-model-skills-roi-audit-rubric.md` kept on disk but is for the WRONG question (finding-level ROI labels, not dual-mode generalization). Do not use.
- ⚠ Large pile of untracked autopilot artifacts (`debate-efficacy-study-*`, scripts, config) — not this session's work, still on disk.
