---
scope: debate-system-improvements
tier: T1
thesis: "The debate system finds problems but doesn't fix them. A closed-loop architecture — where judge-accepted findings trigger data collection and remediation before refinement — is the single highest-leverage change. Secondary improvements (chunked refinement, audience context, thesis-required proposals) compound on the closed loop."
surfaces_affected:
  - scripts/debate.py
  - .claude/skills/debate/SKILL.md
  - .claude/skills/refine/SKILL.md
  - .claude/skills/challenge/SKILL.md
  - config/debate-models.json
origin: "Post-mortem from velocity analysis project (downstream). Full adversarial pipeline ran against a real 336-repo engineering analysis. Compared output to a human analyst (Scott) who produced a more useful document. 8 structural failures identified."
---

# Proposal: Debate System Improvements — From Open Loop to Closed Loop

## Current System Failures

The debate system was tested end-to-end on a real velocity analysis project. It ran the full pipeline: collect data → analyze → propose → challenge → judge → refine. The output was compared against a human analyst who worked from the same data sources.

**Results:** The human analyst produced a document titled "How Do We Go Faster?" that drove CEO decisions. The pipeline produced a document titled "Engineering Activity & AI Adoption Analysis" that was methodologically careful but strategically useless.

**Root cause:** The pipeline is linear and open-loop. Adversarial findings become footnotes instead of triggering remediation.

## Proposed Changes (5 items, priority-ordered)

### 1. Closed-Loop Architecture (Engine Change)

**Problem:** Judge accepts a finding (e.g., "missing quality metrics data") → refinement writes a caveat about it → final document has a gap that was identified but never fixed.

**Proposed fix:** Add a `collect-more` step between `judge` and `refine`. When the judge ACCEPTs a challenge tagged UNDER-ENGINEERED or identifies a data gap, the system generates a remediation task and executes it before refinement begins.

New pipeline: challenge → judge → **remediate** → refine

The remediate step would:
- Parse ACCEPT findings from the judgment
- Classify each as: DATA_GAP (need more data), METHODOLOGY (need different analysis), SCOPE (need to narrow/widen), FRAMING (need different perspective)
- For DATA_GAP and METHODOLOGY: generate a collection/analysis task, execute it, append results to the proposal
- For SCOPE and FRAMING: pass directly to refine as seeded focus areas (current behavior)

**Blast radius:** New subcommand in debate.py. New step in /debate skill. Does not affect /challenge, /refine, or /review.

**Risk:** Remediation could be expensive (additional API calls, data collection). Needs a cost ceiling and user confirmation for expensive remediation tasks.

### 2. Chunked Refinement for Large Documents (Engine Change)

**Problem:** Refinement truncated a contributor table mid-row. Round 3 (Opus) timed out. Documents over ~200 lines exceed comfortable context for single-pass rewriting.

**Proposed fix:** Add `--chunk` mode to `debate.py refine`. When enabled:
- Split document at `## ` headers into sections
- Refine each section independently with the judgment context
- Reassemble into the final document
- Run one final "coherence pass" on the assembled document

**Blast radius:** Engine change to debate.py refine subcommand. Optional flag — default behavior unchanged. Benefits both /debate and /refine skills.

**Risk:** Section-by-section refinement may lose cross-section coherence (e.g., a finding in Section 3 that contradicts Section 6). The coherence pass mitigates this but adds one more round of API calls.

### 3. Audience and Decision Context (Engine + Skill Change)

**Problem:** Challengers and refiners defaulted to "is this technically accurate?" because they had no context about who the document was for or what decisions it needed to support. The system optimized for methodological defensibility when the audience was a CEO.

**Proposed fix:** Add `--audience` and `--decision` flags to debate.py challenge and refine subcommands. These get injected into system prompts:
- Challengers: "The audience is {audience}. The document must support this decision: {decision}. Challenge findings that would matter to this audience — not just technical accuracy."
- Refiners: "The audience is {audience}. Preserve strategic framing and prescriptive content that helps them make this decision: {decision}."

**Blast radius:** New optional flags in debate.py. Prompt changes to challenge and refine system prompts. Skills pass through from user input.

**Risk:** Low. Optional flags with no behavior change when omitted.

### 4. Thesis-Required Proposal Template (Process Change)

**Problem:** The velocity analysis proposal was deliberately neutral ("no conclusions, no editorializing"). This made refinement useless — there was no argument to improve, only data to annotate. Refinement works best on a strong claim.

**Proposed fix:** Update the proposal template (used by /debate) to require:
- A `## Thesis` section with a falsifiable claim
- A `## Recommendations` section with specific actions
- Mark proposals without a thesis as "data report" tier — they can be challenged but skip refinement (nothing to refine)

**Blast radius:** Template/process change. No engine changes. Affects /debate skill procedure.

**Risk:** Some legitimate proposals are genuinely exploratory and don't have a thesis yet. The "data report" tier handles this — they get challenged but not refined, which is appropriate.

### 5. Persona Design Over Model Diversity (Config + Documentation)

**Problem:** Three model families (Opus, Gemini, GPT) all converged on the same issues. The Gemini challengers produced fewer and less detailed challenges than Opus. Model diversity didn't produce perspective diversity.

**Proposed fix:**
- Document that `--personas` matters more than `--models` for challenge quality
- Add domain-specific persona sets to config/debate-models.json:
  - `data-analysis`: skeptical-statistician, engineering-vp, risk-officer
  - `architecture`: architect, security, pm (current default)
  - `product`: pm, designer, user-advocate
- Update /challenge and /debate skills to select persona set based on proposal domain

**Blast radius:** Config and documentation. Persona prompts in debate.py. No engine changes.

**Risk:** More personas to maintain. Persona-to-model mapping becomes more complex. Start with 2-3 sets and expand based on usage.

## What This Does NOT Propose

- Slack/comms data integration — this is project-specific, not a debate system change
- Mandatory plan-level challenge — already addressed by existing /challenge gate in the pipeline
- Removing model diversity — three families still provide value for review (/review) even if persona design matters more for challenge

## Cost Estimate

| Change | Development | Per-run cost impact |
|---|---|---|
| Closed loop | ~2 sessions | +$0.05-0.50 per remediation (depends on data gaps found) |
| Chunked refinement | ~1 session | +$0.02 per coherence pass |
| Audience/decision flags | ~0.5 session | None (prompt injection only) |
| Thesis template | ~0.5 session | None (process change) |
| Persona sets | ~0.5 session | None (config change) |

## Verification

- Re-run the velocity analysis with closed-loop pipeline, compare output to original
- Run /refine on a 300+ line document with and without --chunk, verify no truncation
- Run /challenge with --audience ceo on a technical proposal, verify challenge focus shifts
- Create a thesis-less proposal, verify it routes to "data report" tier
