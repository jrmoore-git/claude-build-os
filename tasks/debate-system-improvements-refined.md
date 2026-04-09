---
debate_id: debate-system-improvements
created: 2026-04-08T20:29:46-0700
phase: refine
rounds: 3
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: yes
---
# debate-system-improvements — Refined Document

## Round 1 (gemini-3.1-pro)
The original proposal identifies a critical flaw in the debate system (open-loop findings becoming mere footnotes) and proposes a highly leveraged solution (closed-loop remediation). However, the initial design for the closed-loop architecture left critical operational, security, and data-handling mechanics undefined. 

To address the accepted challenges, Section 1 has been significantly expanded to explicitly define:
1. **Control Flow & Bounds:** Capping remediation at a single pass, defining failure states, and explicitly preventing infinite loops.
2. **Gap Taxonomy:** Distinguishing between gaps the toolchain can autonomously close (e.g., local codebase queries) and those requiring human access (e.g., Slack context).
3. **Trust Boundaries:** Ensuring judge text isn't blindly executed by enforcing an allowlisted task schema and strict tool constraints.
4. **Data Handling:** Implementing minimization, redaction, and approval gates to prevent sensitive data leakage during automated remediation.

The rest of the document, including all operational context and cost estimates, has been preserved and lightly polished for consistency.

## Round 2 (gpt-5.4)
The current revision is already strong: it clearly identifies the core failure mode, prioritizes changes, and preserves important operational context from the downstream post-mortem.

Main improvements made in this revision:
- It sharpened the thesis around the open-loop vs. closed-loop problem.
- It added important operational safeguards for remediation: taxonomy, bounds, trust boundaries, and data handling.
- It kept the proposal practical by separating engine, process, and config changes.

Remaining issues and opportunities:
1. The document says the thesis emphasizes “secondary improvements (chunked refinement, audience context, thesis-required proposals),” but the proposal lists five items including persona design. That is fine, but the intro can better frame item 5 as supportive rather than central.
2. “Does not affect /challenge, /refine, or /review” under closed loop conflicts slightly with the earlier statement that `/debate` skill gains a new remediation step. Better to say it does not require behavioral changes to those other skills, aside from integration in `/debate`.
3. The remediation trigger is slightly ambiguous: it mentions both accepted UNDER-ENGINEERED challenges and “identifies a data gap.” This should be normalized into explicit trigger conditions.
4. The chunking proposal is good, but “split document at `## ` headers” is a bit brittle. It should specify fallback behavior when headers are sparse or sections are too large.
5. The “Cost Estimate” includes quantitative claims without evidence. Under the evidence-tagging rule, newly introduced quantitative claims should be tagged. Since these claims are already in the document, they need not be newly tagged, but the table would be stronger if reframed as rough planning estimates rather than precise expectations.
6. Verification can be improved by tying success criteria to the failures described earlier: not just “re-run,” but what outcomes would demonstrate the change worked.

## Round 3 (claude-opus-4-6)
The current revision is strong — well-structured, clearly argued, and preserves the operational evidence from the original post-mortem. The previous reviewer did good work organizing the closed-loop architecture into sub-sections (gap taxonomy, control flow, trust boundaries, data handling) and making the pipeline changes concrete.

Remaining issues I want to address:

1. **Section 1 is disproportionately long relative to the others.** The closed-loop architecture section is ~60% of the proposal body. The sub-sections (A–D) are well-organized, but the sheer length makes it harder to scan. I'll tighten prose without removing any operational constraints or design decisions.

2. **"Blast radius" terminology is used inconsistently.** It appears in some sections but not others, and sometimes conflates "what files change" with "what behavior changes." I'll normalize this across all five changes.

3. **Cost table lacks evidence tagging.** The per-run cost figures ($0.05–0.50, $0.02) are presented without basis. These should be marked as estimates with stated assumptions so a reader can evaluate them.

4. **Verification section could be tighter.** The functional verification list and success criteria list partially overlap. I'll consolidate without losing any test case.

5. **Minor clarity issues:**
   - The "What This Does Not Propose" section's second bullet ("Mandatory plan-level challenge — already addressed by the existing `/challenge` gate") is ambiguous about what "already addressed" means.
   - The thesis-required section doesn't specify what happens if a user *wants* to refine a data report anyway.
   - The chunked refinement section doesn't address what "too few headers" or "too large" means concretely.

6. **No regressions detected** from the previous revision. All original failure data, pipeline descriptions, and measurements are intact.

## Final Refined Document

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

## Proposal Summary

The highest-leverage change is to close the loop between judging and refinement: when the system agrees that a material gap exists, it should try to fix that gap before rewriting the document.

The remaining changes improve the quality of that loop:
- **Chunked refinement** makes large-document rewriting reliable.
- **Audience and decision context** steers challenge and refinement toward usefulness, not just correctness.
- **Thesis-required proposals** ensure the system is refining arguments, not just annotating neutral reports.
- **Persona design** improves challenge diversity, but is a secondary lever relative to the closed loop.

## Proposed Changes (5 items, priority-ordered)

### 1. Closed-Loop Architecture (Engine Change)

**Problem:** Judge accepts a finding (e.g., "missing quality metrics data") → refinement writes a caveat about it → final document has a gap that was identified but never fixed.

**Proposed fix:** Add a `remediate` step between `judge` and `refine`. When the judge ACCEPTs a challenge that indicates a fixable gap, the system generates a remediation task and executes it before refinement begins.

New pipeline: challenge → judge → **remediate** → refine

**Trigger conditions:** Remediation runs only when an accepted finding is classified as `DATA_GAP`, `METHODOLOGY`, or `UNDER-ENGINEERED`, *and* the finding is judged tool-closeable per the rules below.

#### A. Gap Taxonomy and Fallbacks

Not all gaps can be closed autonomously. Each accepted finding is classified into one of two categories:

- **Tool-closeable:** Data is accessible via the existing approved toolchain — running `git log` on a local repository, grepping local documentation, querying an explicitly connected local database. The system attempts autonomous remediation.
- **Access-constrained:** Data requires external human context or unauthorized systems — interviewing a developer, reading private Slack channels, fetching external vendor metrics.

**Fallback for access-constrained gaps:** The system halts autonomous collection, prompts the user for approval or manual data provision, and — if unprovided — falls back to appending a specific caveat in the final document describing exactly what data was needed and why it could not be obtained.

#### B. Control Flow and Loop Bounds

- **Max depth:** Remediation is limited to exactly one pass (`depth=1`) for v1. No recursive remediation.
- **No auto re-challenge:** Remediated output passes directly to refinement. It is not automatically re-challenged in the same run unless the user explicitly invokes another challenge round.
- **Failure handling:** If a remediation task fails or returns partial data, the pipeline continues: partial data and the failure note are passed to the refiner as context, rather than halting the entire run.

#### C. Trust Boundary and Execution Constraints

Free-form judge text is untrusted and must not be executed directly.

- **Allowlisted schema:** Accepted findings are translated by an LLM into a fixed, allowlisted JSON task schema. Only tasks matching this schema are executed.
- **Approved tools only:** Execution is limited to a predefined set of read-only tools.
- **Explicit bans:** Destructive operations (`git reset`, file deletions, etc.) are banned. External network access and high-cost API actions require explicit, per-action user approval.

#### D. Data Handling and Redaction

Automated data collection increases the risk of oversharing sensitive artifacts with model providers.

- **Minimization:** Remediation scripts collect only the minimum data needed. Raw artifacts (large log files, code snippets) are summarized or redacted locally before being appended to prompts.
- **Logging:** Only task definitions, metadata, and schemas are logged permanently. Raw collected content is excluded from standard telemetry.
- **Approval for injection:** User approval is required before injecting potentially sensitive raw artifacts (e.g., unredacted API payloads) into final documents or refinement prompts.

**Scope of change:** New subcommand in `debate.py`; new step in the `/debate` skill. No behavioral changes to `/challenge`, `/refine`, or `/review` beyond normal integration with the updated `/debate` flow.

**Risk:** Remediation increases API and data-collection cost. The v1 design bounds this through a strict one-pass limit, explicit approval gates, and narrow tool permissions.

### 2. Chunked Refinement for Large Documents (Engine Change)

**Problem:** Refinement truncated a contributor table mid-row. Round 3 (Opus) timed out. Documents over ~200 lines exceed comfortable context for single-pass rewriting.

**Proposed fix:** Add `--chunk` mode to `debate.py refine`. When enabled:
- Split the document at `## ` headers into sections.
- Refine each section independently using the same judgment context.
- Reassemble the refined sections into a single document.
- Run one final coherence pass over the assembled result.

**Edge cases:**
- If a document has fewer than 3 `## ` headers, fall back to size-based chunking (target: ~150 lines per chunk).
- If a single section exceeds ~300 lines after header-based splitting, subdivide it at the next-level header (`### `) or by size.
- Tables, lists, and code blocks are kept as intact units during splitting to prevent formatting regressions.

**Scope of change:** Engine change to the `debate.py refine` subcommand. Optional flag; default behavior unchanged. Benefits both `/debate` and `/refine`.

**Risk:** Section-by-section refinement can lose cross-section coherence (e.g., a claim in one section conflicting with another). The final coherence pass mitigates this but adds one additional API call.

### 3. Audience and Decision Context (Engine + Skill Change)

**Problem:** Challengers and refiners defaulted to "is this technically accurate?" because they had no context about who the document was for or what decision it needed to support. The system optimized for methodological defensibility when the audience was a CEO.

**Proposed fix:** Add `--audience` and `--decision` flags to `debate.py challenge` and `debate.py refine`. These values are injected into system prompts:

- **Challengers:** "The audience is {audience}. The document must support this decision: {decision}. Challenge findings that would matter to this audience, not just technical accuracy."
- **Refiners:** "The audience is {audience}. Preserve strategic framing and prescriptive content that helps them make this decision: {decision}."

**Scope of change:** New optional flags in `debate.py`, prompt changes to challenge and refine system prompts, skill updates to pass through user input.

**Risk:** Low. These are optional flags with no behavior change when omitted.

### 4. Thesis-Required Proposal Template (Process Change)

**Problem:** The velocity analysis proposal was deliberately neutral ("no conclusions, no editorializing"). This made refinement ineffective: there was no argument to improve, only data to annotate. Refinement works best on a strong claim.

**Proposed fix:** Update the proposal template used by `/debate` to require:
- A `## Thesis` section with a falsifiable claim.
- A `## Recommendations` section with specific actions.

Proposals without a thesis are routed to **data report** tier: they can still be challenged for rigor, but they skip refinement by default because there is no argument to sharpen. Users can override this with `--force-refine` if they want refinement on a data report anyway.

**Scope of change:** Template and process change only. No engine changes. Affects `/debate` skill procedure.

**Risk:** Some legitimate proposals are exploratory and do not have a thesis yet. The **data report** tier handles this: those documents are still challenged for rigor but are not subjected to argument-sharpening refinement unless explicitly requested.

### 5. Persona Design Over Model Diversity (Config + Documentation)

**Problem:** Three model families (Opus, Gemini, GPT) all converged on the same issues. The Gemini challengers produced fewer and less detailed challenges than Opus. Model diversity did not create meaningful perspective diversity.

**Proposed fix:**
- Document that `--personas` matters more than `--models` for challenge quality.
- Add domain-specific persona sets to `config/debate-models.json`:
  - `data-analysis`: skeptical-statistician, engineering-vp, risk-officer
  - `architecture`: architect, security-engineer, product-manager
  - `product`: product-manager, designer, user-advocate
- Update `/challenge` and `/debate` skills to select a persona set based on proposal domain.

**Scope of change:** Config and documentation changes, plus persona prompt selection logic in `debate.py`. No core engine changes.

**Risk:** More personas create maintenance overhead, and persona-to-model mapping becomes more complex. Start with the three curated sets above and expand only if usage supports it.

## What This Does Not Propose

- **Slack or comms-data integration** — project-specific, not a general debate-system change.
- **Mandatory plan-level challenge** — the existing `/challenge` gate in the pipeline already provides a challenge step before execution; this proposal does not add a second mandatory gate.
- **Removing model diversity** — multiple model families may still provide value for `/review` even if persona design matters more for `/challenge` quality.

## Cost Estimate

These are rough planning estimates for prioritization, not budgeting. All per-run figures are estimates based on the assumptions stated.

| Change | Development effort | Per-run cost impact |
|---|---|---|
| Closed loop | ~2 sessions | +$0.05–0.50 per remediation *(ESTIMATED: assumes 1–3 tool-closeable gaps per run, each requiring one LLM call for task generation + one for summarization; range reflects variation in gap count and data volume)* |
| Chunked refinement | ~1 session | +$0.02 per run *(ESTIMATED: assumes one coherence pass at ~2K tokens on a mid-tier model)* |
| Audience/decision flags | ~0.5 session | Negligible (prompt injection only) |
| Thesis template | ~0.5 session | None (process change) |
| Persona sets | ~0.5 session | None (config change) |

## Verification

Each test maps to a specific failure observed in the velocity analysis post-mortem.

| Observed failure | Test | Success criterion |
|---|---|---|
| Accepted data-gap findings became caveats, not fixes | Re-run the velocity analysis with the closed-loop pipeline; compare output to the original open-loop result | Tool-closeable gaps produce new collected evidence; access-constrained gaps produce an explicit user-facing request for input, not just a caveat |
| Refinement truncated a contributor table at ~200 lines | Run `/refine` on a 300+ line document with and without `--chunk` | Chunked path completes without truncation; tables and lists remain intact |
| Challenges targeted technical accuracy instead of decision relevance | Run `/challenge` with `--audience ceo --decision "where to invest engineering resources"` on a technical proposal | Challenges shift toward decision relevance, not only technical rigor |
| Neutral proposal produced ineffective refinement | Create a thesis-less proposal and verify routing | Proposal routes to **data report** tier; refinement is skipped unless `--force-refine` is used |
| Three model families converged on identical issues | Run `/challenge` with domain-specific personas vs. default personas on the same proposal | Persona-driven challenges surface at least one materially different concern not raised by default personas |

## Recommended Implementation Order

1. **Closed-loop architecture** — fixes the core failure where the system identifies gaps but does not act on them.
2. **Chunked refinement** — makes refinement reliable on the document sizes that matter in practice.
3. **Audience and decision context** — steers the system toward the right optimization target.
4. **Thesis-required proposal template** — ensures proposals are structured for effective refinement.
5. **Persona design improvements** — tunes challenger diversity through persona engineering.
