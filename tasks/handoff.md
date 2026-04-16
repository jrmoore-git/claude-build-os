# Handoff — 2026-04-16

## Session Focus
Fixed explore command in debate.py to rotate models across directions instead of locking to a single model, matching the cross-model philosophy used by every other debate command.

## Decided
- Explore should rotate models like refine does — single-model divergence is weaker than cross-model divergence
- Claude should not generate explore directions since it judges the synthesis — avoids grading its own homework
- Default rotation: GPT → Gemini → GPT (GPT wraps instead of Gemini since Gemini is least reliable)

## Implemented
- Model rotation in cmd_explore: each direction uses next model in rotation
- Fallback chain: explore_rotation → refine_rotation → hardcoded default
- `--model` override still locks all rounds to one model
- Frontmatter outputs `models:` list instead of single `model:`
- Audit log records model list

## NOT Finished
- ⚠ Lessons at 31/30 — triage overdue
- Context injection hook (Priority 1 from prior session) not started
- No `explore_rotation` key added to debate-models.json yet (falls through to refine_rotation)

## Next Session Should
1. Triage lessons.md (over 30 target)
2. Continue Priority 1 (context injection hook) or Priority 2 (use gstack /qa)

## Key Files Changed
- scripts/debate.py

## Doc Hygiene Warnings
- ⚠ decisions.md not updated — explore model rotation decision not captured (minor, captured in commit message and handoff)
- ⚠ Lessons at 31/30 — approaching triage threshold
