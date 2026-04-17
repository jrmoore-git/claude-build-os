# Current State — 2026-04-17 (late session: dual-mode audit + frame-reach intake audit)

## What Changed This Session
- **Dual-mode generalization audit landed (research-only, architect not shipped).** Ran frame-lens Round 1 methodology (paired tools-on + tools-off) on architect, security, pm personas across 5 historical proposals. Verdicts: architect 5/5 ADOPT, security 4/5 DECLINE, pm 2/5 DECLINE. Pre-committed 5/5-bidirectional threshold held per L45.
- **User reframed scope mid-session: "improve the frame across the whole debate pipeline" ≠ "persona-level dual-mode."** Real goal was extending Frame's reach beyond `/challenge` stage. Architect ship deferred in favor of auditing the higher-leverage question.
- **Frame-reach intake audit landed, VERDICT: DECLINE.** Tested whether dual-mode Frame at proposal intake reliably reproduces Frame-inside-challenge findings. Three locked gates; two failed: (1) per-proposal reproduction ≥70% failed on autobuild (60%) and learning-velocity (40%) under strict MATERIAL-only rubric — severity-level drift between intake and challenge stages; (3) negative control raised 2 MATERIAL findings because "frame-clean ≠ factual-claim-free" — any proposal citing code subjects itself to frame-factual verification.
- **`debate.py intake-check` subcommand shipped as a composable primitive** (not wired into `/challenge`). Available for future work that accounts for severity drift + factual-FP asymmetry. Judge/refine/premortem audits deferred pending this learning.
- **L43 extended twice** with per-persona generalization evidence and intake-reach DECLINE evidence.

## Current Blockers
- None technical. Two open research questions (deferred): (a) does a lower threshold justify dual-mode for security? would require separate pre-committed audit; (b) what integration design for intake that accounts for severity drift + factual-FP? open-ended.

## Next Action
Start next session by reading this state + `tasks/handoff.md`. Decide whether to: (a) revive architect dual-mode ship (clean 5/5 pass, separate code path from the DECLINE'd intake work), (b) design intake-integration-v2 with different signal than MATERIAL count, (c) audit judge-stage frame-reach (different stage, different failure-mode structure), or (d) move on to unrelated work.

## Recent Commits
- `5e93bec` Add global tone rule to counter Opus 4.7 register mirroring
- `c69beb2` Session wrap 2026-04-17 (evening): /think discover drifted to ROI audit — dual-mode generalization still pending
- `1c40d6c` Multi-model skills ROI audit: design + Phase 0 feasibility (GO) [OFF-SCOPE from earlier session]

## Followup tracked (post-session, not blocking)
- **Autopilot `debate-efficacy-study-*` pile still on disk, uncommitted.** Carries across 3 sessions now. ~30 files. Decide: absorb, commit-as-is, or delete. NOT this session's work; not blocking current research but increasingly untidy.
- `tasks/multi-model-skills-roi-audit-*` design docs (off-scope from 2026-04-17 morning session) remain on disk — valid later-session question.
- `.claude/scheduled_tasks.lock` — expected runtime artifact, ignore.
