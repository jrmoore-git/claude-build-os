---
debate_id: debate-system-improvements-final
created: 2026-04-08T20:38:36-0700
phase: refine
rounds: 6
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: no
---
# debate-system-improvements-final — Refined Document

## Round 1 (gemini-3.1-pro)
The document is in excellent shape. The previous revisions successfully integrated operational safeguards, chunking fallbacks, and cost/verification clarity. The distinction between engine, config, and process changes is crisp, and the evidence from the downstream post-mortem remains intact. 

I have performed a final light polish for readability and flow, particularly in the "Gap Taxonomy" and "Chunked Refinement" sections, to ensure the mechanics are as unambiguous as possible. No major structural changes were needed, and all operational data and estimates have been preserved exactly as requested.

## Round 2 (gpt-5.4)
The current revision is strong: it has a clear thesis, good prioritization, and it preserves the key operational evidence from the real downstream post-mortem. The closed-loop proposal is materially improved over a vague “fix the judge/refine handoff” suggestion because it now includes trigger conditions, loop bounds, trust boundaries, and fallbacks for access-constrained gaps.

Remaining issues and improvements made in the revised document:
- **Clarified the remediation decision path.** The prior version implied classification but did not fully separate “finding type” from “tool-closeable vs. access-constrained.” The revised draft makes this decision flow more explicit.
- **Tightened the closed-loop scope.** I preserved the “one pass, no recursive remediation” constraint and made the handoff to refinement more concrete so it is easier to implement and test.
- **Improved structure and consistency.** The revised document standardizes wording across “problem / proposed fix / scope / risk,” which improves scanability.
- **Added a small amount of implementation specificity where it helps correctness.** In particular, the remediation step now clearly outputs structured artifacts for refinement, and chunking guidance better emphasizes preserving tables/code/list boundaries.
- **Reduced minor ambiguity in the cost section.** “Negligible” and “None” are retained where already present; new quantitative claims were not introduced beyond what was already in the document.
- **Preserved evidence-bearing sections.** The operational context, measurements, and observed failures remain intact and are not collapsed.

No major regressions were present in the prior revision. The main opportunities were better flow, slightly sharper definitions, and making a few operational behaviors easier to reason about.

## Round 3 (claude-opus-4-6)
The previous revision is strong — well-structured, precise, and thorough. The evidence-tagging, gap taxonomy, trust boundary, and verification sections are all well-developed. I identified the following issues to address:

1. **Redundancy in Section 1 sub-sections:** The control flow (B), trust boundary (C), and data handling (D) sections are important but their relationship to each other could be clearer. Section 1 is significantly longer than all other sections combined, which makes the proposal feel top-heavy. However, the detail is warranted for a T1 engine change — the fix is to improve scanability, not cut content.

2. **Missing failure mode in chunked refinement:** The proposal doesn't address what happens if the coherence pass itself introduces regressions (e.g., "fixing" a cross-section contradiction by choosing the wrong version). A brief note on this would strengthen it.

3. **Thesis-required proposal routing logic is slightly under-specified:** The proposal says thesis-less documents "skip refinement by default" but doesn't clarify whether they still go through the full challenge→judge pipeline or get a reduced version. This matters for implementation.

4. **Verification table could be sharper:** Some success criteria are subjective ("challenges shift toward decision relevance"). Where possible, these should be made more concrete.

5. **Minor structural issue:** The "What This Does Not Propose" section is well-placed but the second bullet's explanation is slightly confusing — "the existing `/challenge` gate in the pipeline already provides a challenge step before execution" could be read as circular.

6. **Cost table evidence tags:** The previous reviewer correctly tagged cost estimates. I'll preserve these and tighten the language slightly.

7. **The "Scope" sub-section in item 1 (E) feels disconnected** from the preceding sub-sections A–D. It reads more like a summary than a scope statement. I'll tighten it.

No factual errors or regressions were introduced by the previous reviewer. The operational context, measurements, and system failure descriptions are accurate and well-preserved.

## Round 4 (gemini-3.1-pro)
The previous revision is excellent. It successfully structured the closed-loop architecture into logical sub-components (Taxonomy, Control Flow, Trust Boundary, Data Handling) and provided clear, actionable implementation steps. The operational context and baseline performance data from the downstream project were perfectly preserved. 

Improvements in this pass are minor and focused on readability:
- Standardized list formatting and bolding for easier scanning.
- Slightly tightened the wording in the "Trigger conditions" and "Coherence pass failure mode" sections for maximum clarity.
- Ensured the "Verification" table aligns perfectly with the proposed changes.

No new quantitative claims were introduced, so no new evidence tags were required.

## Round 5 (gpt-5.4)
The current revision is substantially improved: it identifies the core architectural failure clearly, preserves operational context from the post-mortem, and prioritizes changes sensibly. The new closed-loop section is especially stronger because it adds taxonomy, loop bounds, trust boundaries, and data-handling constraints rather than treating remediation as a vague extra step.

Remaining issues are mostly about precision and consistency:

1. **A few implementation boundaries were still implicit.**
   - The document said no behavior changes to `/challenge`, `/polish`, or `/check` individually, but other sections proposed prompt changes and skill updates for challenge/polish. That is a contradiction. I resolved it by distinguishing the closed-loop scope from the broader proposal scope.

2. **The routing logic for thesis-less proposals needed a bit more clarity.**
   - The current version introduced a “data report tier,” but did not fully explain that this is a process classification, not necessarily a new engine mode. I clarified that to reduce implementation ambiguity.

3. **Some success criteria were slightly too absolute for v1.**
   - For persona diversity and decision relevance, strict deterministic wording could create brittle tests. I tightened wording while keeping the intent and preserving the observed failures.

4. **Minor phrasing and flow improvements were available.**
   - I smoothed transitions, reduced a few repeated statements, and made section headings and scope statements more internally consistent.

5. **Quantitative claims were already tagged appropriately where newly introduced.**
   - I preserved those tags and avoided adding unsupported new quantitative claims.

## Round 6 (claude-opus-4-6)
The previous revision is strong — well-structured, clearly scoped, and preserves all operational evidence from the post-mortem. The proposal reads as a credible engineering document. Here are my observations:

**Improvements made by the previous reviewer:**
- Excellent gap taxonomy (Section 1A) with two independent axes
- Clear control flow bounds (Section 1B) preventing recursive remediation
- Trust boundary and execution constraints (Section 1C) are well-specified
- Data handling/redaction concerns (Section 1D) are addressed
- Chunking edge cases are handled (Section 2)
- Cost estimates are properly tagged with evidence basis
- Verification table maps directly to observed failures

**Remaining issues I'm addressing:**

1. **Remediation output schema is underspecified.** Section 1 describes what remediation "produces" but doesn't show the actual JSON task schema mentioned in 1C. Even a sketch would make the allowlisting constraint concrete and reviewable.

2. **The "data report tier" in Section 4 is ambiguous.** It says "This is a process classification, not necessarily a separate engine implementation" — but then the verification table expects automatic routing behavior. Needs to clarify whether this is a flag, a detection heuristic, or a manual classification.

3. **Section 3 prompt examples are too vague to implement.** The prompt "intent" is described but the actual system prompt injection pattern isn't specified. A concrete example would help implementers.

4. **Coherence pass in Section 2 lacks a specification.** It "checks for cross-section contradictions, duplicated recommendations, broken references, and formatting drift" — but how? Is this an LLM call with a specific prompt, a rule-based check, or both?

5. **The "What This Does Not Propose" section could preempt one more likely question:** What about human-in-the-loop review of remediated data before it reaches the refiner? Section 1D requires approval for sensitive artifacts in final documents, but the general case of reviewing remediation quality before refinement isn't addressed.

6. **Minor structural issue:** The scope/risk notes at the end of each subsection in Item 1 (Section E) feel disconnected from the subsections above them. They apply to all of Item 1, not just to subsection E.

7. **Verification table success criteria for the closed-loop test is slightly circular** — "tool-closeable gaps produce new collected evidence" restates the design rather than defining an observable outcome. Tightened this.

## Final Refined Document

---
scope: debate-system-improvements
tier: T1
thesis: "The debate system finds problems but doesn't fix them. A closed-loop architecture — where judge-accepted findings trigger data collection and remediation before refinement — is the single highest-leverage change. Secondary improvements (chunked refinement, audience context, thesis-required proposals) compound on the closed loop."
surfaces_affected:
  - scripts/debate.py
  - .claude/skills/challenge/SKILL.md
  - .claude/skills/polish/SKILL.md
  - config/debate-models.json
origin: "Post-mortem from velocity analysis project (downstream). Full adversarial pipeline ran against a real 336-repo engineering analysis. Compared output to a human analyst (Scott) who produced a more useful document. 8 structural failures identified."
---

# Proposal: Debate System Improvements — From Open Loop to Closed Loop

## Current System Failures

The debate system was tested end-to-end on a real velocity analysis project. It ran the full pipeline: collect data → analyze → propose → challenge → judge → refine. The output was compared against a human analyst who worked from the same data sources.

**Results:** The human analyst produced a document titled "How Do We Go Faster?" that drove CEO decisions. The pipeline produced a document titled "Engineering Activity & AI Adoption Analysis" that was methodologically careful but strategically useless.

**Root cause:** The pipeline is linear and open-loop. Adversarial findings become footnotes instead of triggering remediation.

## Proposal Summary

The highest-leverage change is to close the loop between judging and refinement: when the system agrees that a material gap exists, it should attempt to fix that gap before rewriting the document.

The remaining changes improve the quality and usefulness of that loop:
- **Chunked refinement** makes large-document rewriting reliable.
- **Audience and decision context** steers challenge and refinement toward usefulness, not just correctness.
- **Thesis-required proposals** ensure the system is refining arguments, not just annotating neutral reports.
- **Persona design** improves challenge diversity, but is a secondary lever relative to the closed loop.

## Proposed Changes (5 items, priority-ordered)

### 1. Closed-Loop Architecture (Engine Change)

**Problem:** Judge accepts a finding (for example, "missing quality metrics data") → refinement writes a caveat about it → the final document still contains the identified gap.

**Proposed fix:** Add a `remediate` step between `judge` and `refine`. When the judge ACCEPTs a challenge that indicates a fixable gap, the system generates a remediation task and executes it before refinement begins.

**New pipeline:** challenge → judge → **remediate** → refine

Remediation produces structured output that the refiner consumes:

```json
{
  "gap_id": "string — unique identifier for the accepted finding",
  "finding_type": "DATA_GAP | METHODOLOGY | UNDER-ENGINEERED",
  "closure_mode": "TOOL_CLOSEABLE | ACCESS_CONSTRAINED",
  "description": "string — what the judge accepted",
  "task": {
    "tool": "string — one of the approved tools (e.g., git_log, grep, find, file_read)",
    "args": ["string — tool arguments"],
    "target": "string — path or scope"
  },
  "result": {
    "status": "SUCCESS | PARTIAL | FAILED",
    "collected_evidence": "string — summarized/redacted data, not raw artifacts",
    "failure_reason": "string | null",
    "remaining_caveat": "string | null — caveat for the refiner if gap is not fully closed"
  }
}
```

**Trigger conditions:** Remediation runs *only* when an accepted finding meets both criteria in the gap taxonomy below (Section A).

#### A. Gap Taxonomy and Decision Path

Each accepted finding is evaluated along two independent axes:

1. **Finding type**
   - `DATA_GAP` — Missing data that the document needs.
   - `METHODOLOGY` — Flawed or incomplete analytical method.
   - `UNDER-ENGINEERED` — Correct direction but insufficiently developed.
   - *Other critique types* (framing, tone, structure) — Not remediable through data collection. These pass directly to the refiner as context.

2. **Closure mode**
   - **Tool-closeable:** Data or evidence is accessible via the existing approved toolchain (e.g., running `git log` on a local repository, grepping local documentation, or querying an explicitly connected local database).
   - **Access-constrained:** Resolution requires external human context or unauthorized systems (e.g., interviewing a developer, reading private Slack channels, or fetching external vendor metrics).

**Execution rule:** Only findings that are both (a) a remediable type and (b) tool-closeable trigger autonomous remediation.

**Fallback for access-constrained gaps:** The system halts autonomous collection, prompts the user for approval or manual data provision, and — if input is not provided — falls back to appending a specific caveat in the final document describing exactly what data was needed and why it could not be obtained.

#### B. Control Flow and Loop Bounds

- **Max depth:** Remediation is limited to exactly one pass (`depth=1`) for v1. No recursive remediation.
- **No auto re-challenge:** Remediated output passes directly to refinement. It is not automatically re-challenged in the same run unless the user explicitly invokes another challenge round.
- **Failure handling:** If a remediation task fails or returns partial data, the pipeline continues. Partial data and the failure note are passed to the refiner as context rather than halting the entire run.
- **Remediation review:** By default, the user is shown a summary of remediation results before refinement proceeds. The `--auto` flag skips this review for non-sensitive contexts. This is distinct from the per-artifact approval gate in Section D, which applies specifically to sensitive raw data.

#### C. Trust Boundary and Execution Constraints

Free-form judge text is untrusted and must not be executed directly.

- **Allowlisted schema:** Accepted findings are translated by an LLM into the fixed JSON task schema shown above. Only tasks matching this schema — with a recognized `tool` value and valid `args` — are executed. Malformed or unrecognized tasks are logged and skipped.
- **Approved tools only:** Execution is limited to a predefined set of read-only tools (e.g., `git log`, `grep`, `find`, local file reads). The initial approved set is:
  - `git_log` — read commit history
  - `git_diff` — read diffs between refs
  - `grep` / `ripgrep` — search file contents
  - `find` — locate files by name or pattern
  - `file_read` — read file contents
  - `wc` / `cloc` — count lines or code metrics
- **Explicit bans:** Destructive operations (`git reset`, file deletions) are banned. External network access and high-cost API actions require explicit, per-action user approval.

#### D. Data Handling and Redaction

Automated data collection increases the risk of oversharing sensitive artifacts with model providers.

- **Minimization:** Remediation scripts collect only the minimum data needed. Raw artifacts are summarized or redacted locally before being appended to prompts.
- **Logging:** Only task definitions, metadata, and schemas are logged permanently. Raw collected content is excluded from standard telemetry.
- **Approval for injection:** User approval is required before injecting potentially sensitive raw artifacts into final documents or refinement prompts.

#### E. Scope, Risk, and Implementation Notes

**Scope of change:** New `remediate` subcommand in `debate.py`; new step in the `/challenge --deep` skill. This closed-loop change does not require changing `/challenge` or `/check` behavior in isolation, though other proposal items below introduce separate prompt and skill updates for challenge/polish.

**Risk:** Remediation increases API and data-collection cost. The v1 design bounds this through a strict one-pass limit, explicit approval gates, and narrow tool permissions.

**Implementation sequence:** (1) Define the task schema and approved tool registry. (2) Implement the LLM-based finding-to-task translator with schema validation. (3) Implement the tool executor with the allowlist. (4) Wire the remediate step into the pipeline between judge and refine. (5) Add the user review checkpoint.

### 2. Chunked Refinement for Large Documents (Engine Change)

**Problem:** Refinement truncated a contributor table mid-row. Round 3 (Opus) timed out. Documents over ~200 lines exceed comfortable context for single-pass rewriting.

**Proposed fix:** Add `--chunk` mode to `debate.py refine`. When enabled:
1. Split the document at `## ` headers into sections.
2. Refine each section independently using the same judgment context.
3. Reassemble the refined sections into a single document.
4. Run one final coherence pass over the assembled result.

**Chunking rules and edge cases:**
- If a document has fewer than 3 `## ` headers, fall back to size-based chunking (target: ~150 lines per chunk).
- If a single section exceeds ~300 lines, subdivide it at the next-level header (`### `) or by size.
- Tables, lists, and code blocks are kept intact during splitting to prevent formatting regressions. The splitter treats these as atomic units: if a chunk boundary would fall inside a table/list/code fence, the boundary moves to the end of that block.
- The final coherence pass is a single LLM call that receives the full reassembled document plus the judgment context. Its prompt instructs it to check for and fix: cross-section contradictions, duplicated recommendations, broken cross-references, inconsistent terminology, and formatting drift. It outputs the corrected document or returns the input unchanged if no issues are found.

**Coherence pass failure mode:** If the coherence pass introduces a regression (detectable via diff review), the damage is bounded to one additional rewrite. For v1, this is an acceptable trade-off. A future version could add automated regression detection by comparing section checksums before and after the coherence pass.

**Scope of change:** Engine change to `debate.py refine`. Optional flag; default behavior unchanged.
**Risk:** Section-by-section refinement can lose cross-section coherence. The final coherence pass mitigates this but adds one API call.

### 3. Audience and Decision Context (Engine + Skill Change)

**Problem:** Challengers and refiners defaulted to "is this technically accurate?" because they lacked context about the audience or the decision being supported.

**Proposed fix:** Add `--audience` and `--decision` flags to `debate.py challenge` and `debate.py refine`. These values are injected into system prompts.

**System prompt injection pattern:**

For challengers, the following block is prepended to the existing challenge system prompt when flags are provided:

```
## Context for this challenge round
- **Target audience:** {audience}
- **Decision this document must support:** {decision}

Prioritize challenges that would matter to this audience in the context of
this decision. Technical accuracy challenges are still valid, but rank them
below challenges that affect whether the document is *useful* for the stated
decision. If the document is technically sound but would not help {audience}
make the decision described above, that is the most important challenge.
```

For refiners, the following block is prepended:

```
## Context for this refinement
- **Target audience:** {audience}
- **Decision this document must support:** {decision}

Preserve and strengthen content that helps {audience} make this decision.
Do not dilute prescriptive recommendations with excessive hedging. When
technical detail does not serve the stated audience, summarize it or move
it to an appendix.
```

When flags are omitted, no context block is injected and behavior is unchanged.

**Scope of change:** New optional flags in `debate.py`, prompt changes to challenge/polish system prompts, and skill updates to `.claude/skills/challenge/SKILL.md` and `.claude/skills/polish/SKILL.md`.
**Risk:** Low. Optional flags with no behavior change when omitted.

### 4. Thesis-Required Proposal Template (Process Change)

**Problem:** The velocity analysis proposal was deliberately neutral. This made refinement ineffective: there was no argument to improve, only data to annotate.

**Proposed fix:** Update the proposal template used by `/challenge --deep` to require:
- A `## Thesis` section with a falsifiable claim.
- A `## Recommendations` section with specific actions.

**Detection and routing logic:** When a proposal enters the `/challenge --deep` pipeline, the system checks for the presence of a `## Thesis` section (or a section containing an explicit falsifiable claim, detected via a simple LLM classification call). Proposals without a thesis are classified as **data reports** and routed accordingly:

- **Data reports:** Pass through challenge → judge for rigor and completeness. Refinement is skipped by default because there is no argument to sharpen. The user sees a message: *"No thesis detected. This proposal will be treated as a data report. Refinement skipped. Use `--force-refine` to override."*
- **Thesis-bearing proposals:** Follow the full pipeline including refinement (and remediation, if the closed loop is enabled).

**Scope of change:** Template and process change. One additional LLM classification call for thesis detection (negligible cost — short prompt, binary output).
**Risk:** Exploratory proposals without a thesis are handled gracefully by the data report path instead of being forced through an unhelpful refinement step. False negatives (thesis present but not detected) are low-cost: the user can add `--force-refine` or restructure the proposal.

### 5. Persona Design Over Model Diversity (Config + Documentation)

**Problem:** Three model families (Opus, Gemini, GPT) converged on the same issues. Model diversity did not create meaningful perspective diversity.

**Proposed fix:**
- Document that `--personas` matters more than `--models` for challenge quality.
- Add domain-specific persona sets to `config/debate-models.json`:
  - `data-analysis`: skeptical-statistician, engineering-vp, risk-officer
  - `architecture`: architect, security-engineer, product-manager
  - `product`: product-manager, designer, user-advocate
- Update `/challenge` and `/challenge --deep` skills to select a persona set based on proposal domain (detected from frontmatter tags or inferred from content).

**Persona prompt structure:** Each persona is defined as a system prompt prefix that establishes the challenger's perspective, expertise, and priorities. For example:

```
You are a skeptical statistician reviewing this analysis. You prioritize:
- Sample size adequacy and selection bias
- Causal claims vs. correlational evidence
- Whether confidence intervals or error bounds are reported
- Whether the methodology would survive peer review
```

Persona sets are stored in `config/debate-models.json` alongside model configurations. The persona is injected into the system prompt *before* the audience/decision context (if present), so both layers compose.

**Scope of change:** Config and documentation changes, plus persona prompt selection logic in `debate.py challenge`.
**Risk:** Persona-to-model mapping becomes slightly more complex. Mitigated by keeping persona definitions in a single config file.

## What This Does Not Propose

- **Slack or comms-data integration** — Project-specific, not a general debate-system change.
- **Mandatory second challenge gate** — The existing pipeline already includes a challenge step before execution, and v1 of the closed loop should remain bounded. Users who want a second round can invoke `/challenge` again manually.
- **Removing model diversity** — Multiple model families may still provide value for `/check`, even if persona design is the stronger lever for `/challenge`.
- **Automated remediation quality assessment** — v1 relies on user review of remediation results (Section 1B) rather than an automated quality gate. A future version could add LLM-based assessment of whether remediated data actually closes the identified gap.

## Operational Context

These changes are motivated by specific, observed failures in a production run. The velocity analysis project involved:
- 336 repositories analyzed
- Full adversarial pipeline execution (challenge → judge → refine, 3 rounds)
- 3 model families used as challengers (Opus, Gemini, GPT)
- Direct comparison against a human analyst working from the same data sources
- 8 structural failures identified in the post-mortem

The human analyst's output drove executive decisions. The pipeline's output was shelved. The gap was not in data quality or analytical rigor — it was in the system's inability to act on its own findings and its lack of orientation toward a decision-maker's needs.

## Cost Estimate

These are rough planning estimates for prioritization, not budgeting.

| Change | Development effort | Per-run cost impact |
|---|---|---|
| Closed loop | ~2 sessions | +$0.05–0.50 per remediation *(ESTIMATED: assumes 1–3 tool-closeable gaps per run, each requiring one LLM call for task generation + one for summarization; range reflects variation in gap count and data volume)* |
| Chunked refinement | ~1 session | +$0.02 per run *(ESTIMATED: assumes one coherence pass at ~2K tokens on a mid-tier model)* |
| Audience/decision flags | ~0.5 session | Negligible |
| Thesis template | ~0.5 session | Negligible *(one short classification call)* |
| Persona sets | ~0.5 session | None |

## Verification

Each test maps to a specific failure observed in the velocity analysis post-mortem.

| Observed failure | Test | Success criterion |
|---|---|---|
| Accepted data-gap findings became caveats, not fixes | Re-run the velocity analysis with the closed-loop pipeline; compare output to the original open-loop result. | At least one previously-caveated gap now contains collected data (e.g., quality metrics from `git log`) in the final document. Access-constrained gaps produce an explicit user-facing prompt or a specific caveat naming the missing data source. |
| Refinement truncated a contributor table at ~200 lines | Run `/polish` on a 300+ line document with and without `--chunk`. | Chunked path completes without truncation; all tables and lists remain intact; row counts match between input and output. |
| Challenges targeted technical accuracy instead of decision relevance | Run `/challenge` with `--audience ceo --decision "where to invest engineering resources"` on a technical proposal. | At least one challenge finding explicitly references the decision context or audience needs, rather than only methodological correctness. |
| Neutral proposal produced ineffective refinement | Create a thesis-less proposal and run it through `/challenge --deep`. | Proposal is automatically classified as a data report; refinement is skipped by default; `--force-refine` overrides the skip and produces a refined output. |
| Three model families converged on identical issues | Run `/challenge` with domain-specific personas vs. default personas on the same proposal. | Persona-driven challenges surface at least one materially different concern (different category or framing) not present in default-persona output. |

## Recommended Implementation Order

1. **Closed-loop architecture** — Fixes the core failure where the system identifies gaps but does not act on them.
2. **Chunked refinement** — Makes refinement reliable on the document sizes that matter in practice.
3. **Audience and decision context** — Steers the system toward the right optimization target.
4. **Thesis-required proposal template** — Ensures proposals are structured for effective refinement.
5. **Persona design improvements** — Tunes challenger diversity through persona engineering.

Items 3–5 are independent of each other and can be parallelized. Items 1 and 2 should be sequential: the closed loop may produce longer documents that benefit from chunked refinement.
