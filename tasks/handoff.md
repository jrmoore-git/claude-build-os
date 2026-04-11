# Handoff — 2026-04-11

## Session Focus
Redesigned explore mode to be domain-agnostic. Previously hardcoded for product-market strategy; now works for engineering, organizational, research, strategy, process, career, and multi-domain questions.

## Decided
- D11: Explore mode uses adaptive dimensions derived from problem domain, not hardcoded product dimensions
- Pre-flight becomes adaptive tree (no 3-bucket classification menu)
- Direction 2 forced to differ on mechanism; Direction 3 forced to challenge premise
- Existing pre-flight files (product, solo-builder, architecture) become reference material
- Strategic questions adaptive: Why now + Workaround required, others optional per domain
- ERRC grid optional (use when it adds insight)

## Implemented
- `config/prompts/explore.md` v3 — domain-agnostic, adaptive questions
- `config/prompts/explore-diverge.md` v4 — {dimensions} variable, premise-challenge, direction-aware rules
- `config/prompts/explore-synthesis.md` v4 — {dimensions} variable, tension check, Bet A defends conventional
- `config/prompts/preflight-adaptive.md` v5 — dimension derivation section added
- `scripts/debate.py` — domain-agnostic fallback prompts, "Context" label (was "Market Context"), dimension parsing from context, direction_number/total_directions passed to diverge
- `.claude/skills/debate/SKILL.md` Step 3a — adaptive tree replaces 3-option menu
- `tasks/explore-redesign-proposal.md` — original proposal
- `tasks/explore-redesign-refined.md` — 6-round cross-model refinement
- `tasks/explore-adaptive-plan.md` — implementation plan
- D11 added to decisions.md

## Test Results (8 experiments, 5 iteration rounds)
| Domain | Start | Final | 
|--------|-------|-------|
| Product (regression) | 4.2 | 4.2 |
| Engineering | 4.4 | 4.4 |
| Organizational | 3.4 | 4.4 |
| Research | 4.4 | 4.4 |
| Strategy | 4.4 | 4.4 |
| Process | 4.6 | 4.6 |
| Multi-domain | 3.8 | 4.4 |
| Career | 4.0 | 5.0 |

Domain appropriateness: 5.0 on all non-product experiments (zero product-language leakage)
Specificity: 5.0 across all domains

## NOT Finished (carried over)
- **Direction 1-2 overlap** — Directions 1 and 2 still tend to share mechanism DNA. Further prompt iteration has diminishing returns; may need architectural change (independent prompts per direction)
- **Update gstack 0.14.5.0 → 0.16.3.0** — gets browser data platform
- **Create `scripts/browse.sh`** — thin wrapper, fixes two broken design skills
- deploy_all.sh customization for BuildOS
- Audit findings 11-13
- `/define discover` live test

## Next Session Should
1. Read this handoff
2. Run a real `/debate --explore` end-to-end on an actual problem to verify the adaptive pre-flight works in conversation (experiments tested the engine directly, not the SKILL.md interaction flow)
3. Consider whether Direction 1-2 overlap is worth addressing (architectural change) or acceptable at 4.4 avg
4. Pick up carried-over items (gstack update, browse.sh)

## Key Files Changed
config/prompts/explore.md
config/prompts/explore-diverge.md
config/prompts/explore-synthesis.md
config/prompts/preflight-adaptive.md
scripts/debate.py
.claude/skills/debate/SKILL.md
tasks/decisions.md
tasks/explore-redesign-proposal.md
tasks/explore-redesign-refined.md
tasks/explore-adaptive-plan.md
