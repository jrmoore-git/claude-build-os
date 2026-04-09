---
debate_id: build-os-additions
created: 2026-03-13T14:04:28-0700
mapping:
  A: gpt-5.4
  B: gemini-3.1-pro
---
# build-os-additions — Challenger Reviews

## Challenger A — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL]: Addition 1 assumes Anthropic’s hook model is stable enough that a repo-local `docs/hooks-guide.md` will remain accurate, but that assumption is not verified and directly conflicts with your own maintenance-burden concern. If hook names, matcher semantics, or `settings.json` structure change, this repo becomes a stale quasi-reference. A safer alternative—bare minimum local explanation plus a pointer to official docs—was not seriously considered. Failure mode: users copy a now-wrong config and blame the repo. This is under-engineered on versioning and drift control, and arguably over-engineered if the official documentation already covers the mechanics better.

2. [ALTERNATIVE] [MATERIAL]: Addition 2 picks Python + sqlite as the canonical teaching vehicle for the “LLM boundary” principle without justifying why this is the best representation for a repo aimed at Claude Code users broadly, not Python users specifically. An alternative not considered is pseudocode or a language-neutral flow diagram embedded in docs, which would teach the principle without implying that SQL/schema validation/audit logging are always the right concrete pattern. Failure mode: readers mistake the example for the recommended default architecture, overfitting “LLM boundary” to database workflows. This is over-engineered as executable code for a conceptual lesson, while under-engineered in portability and representativeness.

3. [RISK] [MATERIAL]: Addition 2 also assumes a ~60-line “self-contained” script can faithfully demonstrate `fetch → LLM → validate → apply → audit` without smuggling in toy simplifications that weaken the actual lesson. The proposal says “schema validation” and “error handling,” but with stdlib only, validation is likely to be superficial and unlike production practice. Unaddressed failure mode: the example normalizes weak validation patterns while claiming to teach strong boundaries. If the point is “software must act,” a thin demo may undermine credibility more than help.

4. [UNDER-ENGINEERED] [MATERIAL]: Addition 3’s persona-growth note is too weak to solve the stated gap. The identified problem is “Review personas have no growth path,” but the proposed fix is a single paragraph telling teams to create `PERSONAS.md` someday. That is not a growth path; it is a suggestion. Missing are promotion criteria, ownership, update cadence, and an example structure for the new file. Alternative not considered: add a minimal `PERSONAS.md` template or a short subsection with triggers like “after N recurring review misses, split into domain checklist.” As proposed, this likely won’t change user behavior.

5. [ASSUMPTION] [ADVISORY]: Addition 4 hard-codes “promote after second violation” as if that threshold is generally valid, but no evidence is offered that two violations is the right trigger across domains. For some teams, one severe incident should promote immediately; for others, repeated low-severity papercuts may not merit a rule. The proposal treats a contingent process heuristic as a rule. Alternative: present multiple promotion criteria (severity, frequency, blast radius) rather than a fixed count.

6. [OVER-ENGINEERED] [ADVISORY]: The four additions collectively risk chipping away at the repo’s original strength—clear topic ownership and minimalism. You are adding one new doc, one code example, and modifying two templates to address gaps that might be closed with fewer artifacts. A simpler approach not seriously considered is consolidating all four into existing docs/templates via short examples and links. Failure mode: the repo shifts from “framework” to “mini knowledge base,” increasing navigation and maintenance cost.

7. [RISK] [MATERIAL]: The proposal does not sufficiently address topic ownership, despite explicitly listing it as an evaluation criterion. `docs/hooks-guide.md` may overlap with enforcement-ladder material; `toolbelt-example.py` may overlap with architecture docs that already explain the boundary concept; the promotion example may duplicate Part V. The assumption that these are clean complements is asserted, not demonstrated. Without a mapping of “what lives where, and what must not be repeated,” the repo may regress into duplication—the exact thing the prior debate was meant to prevent.

## Concessions
- The identified gaps are mostly real, especially the absence of any concrete hook onboarding and lack of a tangible promotion example.
- The proposal tries to preserve repo scope by keeping additions short and teaching-oriented rather than productizing new features.
- The emphasis on practical examples, if done carefully, is directionally correct for a repo meant to help users operationalize concepts.

## Verdict
REVISE — the gaps are legitimate, but at least three proposed fixes are either too brittle, too weak, or insufficiently justified in form, and need tighter scope and ownership before approval.

---

## Challenger B — Challenges
## Challenges

1. **[RISK] [MATERIAL]**: The `hooks-guide.md` duplicates Anthropic's official documentation, creating a severe maintenance liability. Claude Code is in active development; as the hook API (matchers, tool names, settings schema) evolves, this guide will inevitably drift and provide broken instructions. The repo should point to the official docs for syntax and only maintain the *strategy* of hook usage.

2. **[ALTERNATIVE] [MATERIAL]**: The `toolbelt-example.py` introduces language-specific code into a previously language-agnostic structural framework. Providing a Python script assumes the user is comfortable with Python and forces the repo to maintain executable code. A language-agnostic sequence diagram (Mermaid) or generalized pseudo-code in Markdown would illustrate the LLM boundary pattern without the overhead of standard library imports and syntax-specific boilerplate.

3. **[UNDER-ENGINEERED] [MATERIAL]**: The promotion example for `lessons.md` explicitly instructs users to leave the struck-through lesson in the file ("The lesson stays in the log for history"). This ignores the reality of LLM context windows. Over time, `lessons.md` will become bloated with dead, promoted text, wasting tokens and diluting the model's attention on active lessons. Promoted lessons should be deleted or moved to an archived file, not left to clutter the active context.

## Concessions
1. The audit correctly identifies that the "LLM boundary" (decide vs. act) is the most critical concept in the Build OS and currently lacks a concrete illustration.
2. Adding a concrete example to `lessons.md` is a highly effective way to ensure Claude actually follows the promotion lifecycle.
3. Recognizing that personas need a growth path prevents the `/review` command from stagnating on basic starter questions.

## Verdict
REVISE because while the identified gaps are accurate, the proposed implementations introduce API drift risks, language bias, and context-window bloat that undermine the framework's core principles.

---
