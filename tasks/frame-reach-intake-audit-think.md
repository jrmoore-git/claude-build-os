---
generated_by: /think refine
generated_on: 2026-04-17
branch: main
status: DRAFT
related: tasks/frame-lens-validation.md, tasks/dual-mode-generalization-results.md, tasks/lessons.md (L43, L44, L45)
---

# Brief: Frame-Reach Intake Audit

## Problem Statement
Frame persona catches frame errors only inside `/challenge`. When a proposal has a frame error (binary framing, missing compositional candidate, problem inflation, source-driven candidate set, stale citation), Frame catches it during challenge — but only AFTER architect, security, and pm personas have already burned compute critiquing the frame-broken proposal. On the n=5 proposals in the frame-lens-validation corpus, 5/5 showed some frame-level issue Frame caught; in 1/5 (litellm-fallback) Frame flipped the verdict REVISE → REJECT because the feature was already shipped. That verdict flip is value that arrived too late — three other personas wrote full critiques of a proposal that shouldn't have gotten past intake.

Moving frame-checking to proposal intake (before `/challenge` runs) would catch these errors earlier, save downstream compute, and allow proposal authors to revise before the expensive debate pipeline fires.

## Proposed Approach
Pre-commit an audit methodology before designing the code change.

**Audit mechanics:**
1. Use the same 5 proposals from `frame-lens-validation.md` (autobuild, explore-intake, learning-velocity, streamline-rules, litellm-fallback). These already have known frame findings from Frame-inside-challenge (Round 2 results).
2. Design an **intake-frame-check** prompt that adapts Frame's existing prompts (frame-structural + frame-factual in `scripts/debate.py:621-690`) to run as a pre-challenge gate. The prompt asks: "Before this proposal enters `/challenge`, is the candidate set right? Is the problem frame right? Are cited claims stale?"
3. Run the intake frame-check dual-mode (tools-on + tools-off, Frame precedent) on each of the 5 proposals.
4. Compare intake findings against Frame-in-challenge findings from `frame-lens-validation.md` (same 5 proposals). Tag each MATERIAL finding as:
   - **reproduced**: intake catches same frame error Frame-in-challenge caught
   - **novel**: intake catches frame error Frame-in-challenge missed
   - **regression**: intake misses frame error Frame-in-challenge caught
5. Apply pre-committed threshold. Ship if passes.

**Threshold options to pre-commit at `/plan` time** (listing here — final selection at planning):
- **Strict:** On all 5/5 proposals: intake reproduces ≥1 MATERIAL Frame-in-challenge finding AND catches ≥1 novel MATERIAL finding. Zero regressions.
- **Moderate (likely default):** On 5/5 proposals: intake reproduces ≥80% of Frame-in-challenge MATERIAL findings. On ≥3/5 proposals: intake catches ≥1 novel MATERIAL finding. Zero regressions.
- **Lenient:** On 5/5: intake reproduces ≥1 Frame-in-challenge finding. Novel findings are upside, not required. Adoption justified on compute-savings alone.

## Key Assumptions
1. **Frame's existing prompts port to the intake stage with minor adaptation.** The frame-structural prompt asks about candidate framing; the frame-factual prompt verifies claims. Both remain appropriate before `/challenge` runs — we're asking the same questions, earlier. If prompt adaptation is non-trivial, the experiment is bigger than this brief scopes.
2. **The 5-proposal corpus covers enough frame-error variety.** These 5 were selected for the frame-lens-validation because they represent diverse failure modes (binary framing, already-shipped, problem inflation, source-driven, etc.). Not all frame-error classes, but the known-defect set.
3. **Frame-in-challenge findings from frame-lens-validation Round 2 are a reliable ground-truth baseline.** They passed peer review and were the basis for Frame's adoption. If those findings are wrong or incomplete, this audit's comparison is off.
4. **"Intake" as a stage has a clear insertion point.** Before `/challenge` runs, a skill or hook can execute the intake check. Mechanism: (a) a new `debate.py intake-check` subcommand called by a skill wrapper around `/challenge`, OR (b) a hook on the `/challenge` skill, OR (c) a lightweight pre-challenge step inside the skill body. Design decision for `/plan`.
5. **~10 new debate.py runs is the total audit cost.** 5 proposals × 2 modes (dual-mode intake). Phase 1 of the audit. Tagging against Round 2 data is Phase 2.

## Risks
1. **Threshold re-fitting after seeing data (L45).** The audit's decision rule must be locked before the 10 runs execute. If the moderate threshold passes only because we soften it to moderate after seeing results, we're doing rationalization, not science.
2. **Frame-in-challenge ground truth may be incomplete.** Round 2 of frame-lens-validation may have missed findings that a fresh eye would raise. If intake catches "novel" findings that are actually real but were just missed by Round 2, we could over-credit intake. Mitigation: two-reviewer tagging on ambiguous "novel" classifications.
3. **The "catch earlier = better" claim assumes no false positives.** An intake frame-check that falsely rejects a well-framed proposal costs more than a delayed Frame-in-challenge catch. Need to measure false-positive rate across the 5 proposals (even those Frame-in-challenge passed cleanly — did intake raise nonexistent issues?).
4. **Prompt-porting may change behavior in unexpected ways.** Frame-inside-challenge has context (it's reading the proposal alongside architect/security/pm reasoning). Frame-at-intake has only the proposal. The "same prompt, earlier" claim is load-bearing; if behavior shifts, the comparison isn't clean.
5. **Scope creep to judge/refine/premortem.** This brief explicitly defers those three. If intake passes, they become separate, later audits with their own threshold pre-commits. If intake fails, we learn something about where frame-checking does/doesn't work, which informs later designs.

## Simplest Testable Version
**Phase 0 (design + commit threshold):** `/plan` on this brief. Plan must:
- Specify the intake-frame-check prompt (or prompt diff from Frame's existing prompts)
- Lock the decision threshold (pick strict / moderate / lenient) before any runs
- Define the mechanism for running intake (subcommand? hook? inline skill step?)
- Specify the false-positive check (intake must not raise MATERIAL findings on cleanly-framed proposals — how is this tested? Possibly a 6th proposal as negative control?)

**Phase 1 (audit runs):** 10 `debate.py` calls (5 proposals × 2 modes). Output to `tasks/frame-reach-intake-audit-runs/{proposal}-intake-{mode}.md`.

**Phase 2 (tagging):** Compare each proposal's intake findings against `frame-lens-validation.md` Round 2 findings. Tag reproduced / novel / regression. Build per-proposal table. Apply threshold.

**Phase 3 (conditional ship):** If threshold passes — ship intake frame-check as the chosen mechanism (subcommand / hook / skill-step). If threshold fails — document what we learned and defer judge/refine/premortem as separate audits.

## Next Action
`/plan` on this brief. Key open design decisions for the plan:
1. Intake prompt — adopt Frame prompts verbatim, or adapt for "pre-challenge" context?
2. Mechanism — new debate.py subcommand vs. hook vs. skill-step wrapper around `/challenge`?
3. Final threshold — strict, moderate, or lenient (and if lenient, what's the separate false-positive control)?
4. What to do with the dual-mode-generalization evidence (30 runs + architect-adopt verdict). Shelved or committed as research artifacts?
