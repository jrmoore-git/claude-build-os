---
decision: D3
original: "Skills are SKILL.md prompt documents, not executable code modules"
verdict: HOLDS
panel_models: gemini-3.1-pro, claude-opus-4-6, gpt-5.4
panel_votes: HOLDS, HOLDS, REVIEW
judge: synthesized (judge command requires debate-generated challenge artifact)
audit_date: 2026-04-15
---
# D3 Audit

## Original Decision
Each skill is a Markdown file (`.claude/skills/<name>/SKILL.md`) with YAML frontmatter and a procedure section. The Claude Code harness loads and executes them as prompts. Skills do not import each other or share code — shared logic lives in `scripts/`.

## Original Rationale
- Skills are instructions for Claude, not programs; Markdown is the natural format for LLM-consumed content
- Readable, auditable, and editable without a build step
- Code reuse belongs at the script layer (debate.py, llm_client.py), not the skill layer
- Python skill modules would require a custom loader; YAML-only is awkward for freeform procedures; skill imports create hidden coupling

## Audit Findings

Panel: 2 HOLDS (gemini-3.1-pro, claude-opus-4-6), 1 REVIEW (gpt-5.4).

**What holds across all three:**
- The core claim is sound: skills are consumed by Claude as prompts; Markdown is optimal for LLM context window; Python modules would destroy prompt transparency and require a custom loader.
- Alternatives were rejected for concrete reasons. Python modules rejected on sound grounds (EVIDENCED). YAML-only rejected correctly (EVIDENCED). Shared skill libraries rejected due to hidden coupling risk (EVIDENCED but potentially too absolute).
- No failures attributable to the Markdown format have been observed. Compensating mechanisms (authoring rules, tier templates, scripts-layer reuse) are working (EVIDENCED).

**The tension the REVIEW flag identified:**
- Skills have grown to 343–770 lines with mode detection logic and conditional bash blocks. The "readable and auditable by default" benefit is under strain (EVIDENCED).
- 15+ rules in `skill-authoring.md` exist to constrain LLM behavior that a typed format would enforce structurally. That is a code smell (ESTIMATED).
- The rejection of skill-layer reuse may be too absolute: controlled mechanisms (explicit macros, lintable includes) sit between "no reuse" and "hidden runtime imports" and were not considered in the original (ESTIMATED).
- BuildOS has no programmatic SKILL.md validation; gstack has 1,573 lines of structural tests (EVIDENCED gap).

**Conservative bias check:**
Decision was not conservative in the problematic direction. The rejected alternatives (Python modules, skill imports) are genuinely heavier options. If conservative bias were present, the decision would have gone toward stricter constraints — but the format chosen is the most lightweight viable option.

## Verdict: HOLDS

The decision is architecturally sound. Skills are prompt artifacts consumed by an LLM; Markdown is the correct serialization. No evidence of failures caused by the format. The REVIEW flag from one model identifies real watch items, but none require changing the fundamental decision.

**Required hardening (additive, not format-changing):**
1. Skill size ceiling: ~500-line soft limit, ~800-line hard limit. Skills exceeding the soft limit should be evaluated for decomposition (extract logic to scripts/) before growing further. `/review` at 770 lines is the current canary.
2. Structural linter: a lightweight `scripts/lint_skills.py` (already exists — check whether it covers frontmatter schema, required sections, and authoring rule compliance). Additive enforcement without abandoning Markdown.

## Risk Assessment
- **Risk of keeping (HOLDS):** Low-to-moderate. Skill bloat could continue; authoring rules proliferate as a substitute for structural enforcement; `/review` at 770 lines is near the attention-fidelity threshold. None of these have caused failures yet.
- **Risk of changing:** High. Migration of 22 working skills, loss of LLM legibility, risk of solving the wrong problem (linting would address the real need without a format change).
