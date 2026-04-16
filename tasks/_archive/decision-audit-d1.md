---
decision: D1
original: "BuildOS defaults to Python + Shell; TypeScript/Bun allowed when there's a concrete reason"
verdict: HOLDS
panel_models: claude-opus-4-6, gemini-3.1-pro, gpt-5.4
panel_votes: HOLDS, HOLDS, HOLDS
judge: single-model fallback (judge step failed: challenge file has no frontmatter mapping)
audit_date: 2026-04-15
---
# D1 Audit

## Original Decision
Python 3.11+ and Bash remain the default for new scripts. TypeScript/Bun is allowed per-script when adapting existing TypeScript reference code or when types deliver real value. Skills remain Markdown with YAML frontmatter.

## Original Rationale
- Existing Python codebase is large and operational: debate.py (4,136 lines), 17 hooks, sim infrastructure, LiteLLM dependency (Python-only)
- Rewriting for language consistency is churn with no functional gain
- New tooling should not be blocked from TypeScript when the reference implementation (e.g., gstack, 1,573 lines) is TypeScript
- Per-script decision is more pragmatic than a project-wide edict; language is not the bottleneck

## Audit Findings

All three models independently returned **HOLDS**.

**Key panel findings:**

1. **The revised D1 already corrects for conservative bias.** The original decision (2026-03-01) was a full TS/JS ban — likely the conservative-bias outcome. The 2026-04-15 revision loosened it based on concrete evidence (gstack reference system). The current decision is the already-corrected form.

2. **Rationale holds with full context.** LiteLLM is a hard Python dependency. Rewriting 4,136+ lines of working code for language purity is textbook churn. Operational evidence was present and engaged by the decision.

3. **Alternatives were rejected for concrete reasons, not reflex.** Full TS migration rejected on hard dependency grounds (EVIDENCED). Strict Python-only rejected as artificially restrictive (EVIDENCED). TS-for-all-new-code rejected because most new scripts interact with the Python core (EVIDENCED).

4. **Minor concern flagged (not verdict-changing):** The "concrete reason" gate is mildly subjective. Adding explicit criteria would reduce ambiguity — e.g., "adapting substantial existing TS reference code," "script is mostly standalone with no Python interop," or "static typing delivers measurable schema-safety."

## Verdict: HOLDS

The decision is pragmatically sound. The conservative bias bug, if anything, would have produced the strict-Python-only outcome — the revision that produced the current D1 moved in the opposite direction from the bias. No action required. Optional: tighten the "concrete reason" examples in decisions.md for future reference.

## Risk Assessment
- Risk of keeping: Low. Mixed-language toolchain adds minor cognitive overhead, and "concrete reason" can drift toward subjectivity over time. Nothing currently broken.
- Risk of changing: Moderate to high in either direction. Reverting to strict Python-only recreates the overconstrained original decision; moving to TS-first breaks integration with the Python-centered operational core.
