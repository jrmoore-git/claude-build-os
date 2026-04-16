---
name: design
description: "Unified design skill with 4 modes: consult, review, variants, plan-check. Use when designing UI, auditing visual quality, exploring design variants, or checking a plan for design completeness. Defers to /think for problem definition, /review for code review."
version: 2.0.0
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# /design — Unified Design Skill

## Procedure

### Mode Routing

Parse the user's invocation to select a mode:

| Invocation | Mode | What it does |
|---|---|---|
| `/design consult` | Consult | Design system builder — creates or upgrades DESIGN.md |
| `/design review` | Review | Visual QA with browser automation, 94-item audit, letter grades, fix loop |
| `/design variants` | Variants | AI design variant exploration, comparison board, structured feedback |
| `/design plan-check` | Plan-Check | Designer's eye on a plan — rates 0-10 across 7 dimensions, fixes gaps |
| `/design` (no mode) | Auto-detect | See inference rules below |

### Auto-detect rules (when no mode specified)

1. If localhost is running (`curl -s -o /dev/null -w "%{http_code}" http://localhost:3000` returns 200) → **Review**
2. If a plan file exists for the current topic (`tasks/<topic>-plan.md`) → **Plan-Check**
3. If the user said "explore designs", "show me options", "design variants", or "visual brainstorm" → **Variants**
4. Otherwise → **Consult**

State which mode was selected and why. If ambiguous, ask the user.

---

## Interactive Question Protocol

These rules apply to EVERY AskUserQuestion call in this skill:

1. **Text-before-ask:** Before every AskUserQuestion, output the question, all options,
   and context as regular markdown. Then call AskUserQuestion. Options persist if the
   user discusses rather than picks immediately.

2. **Recommended-first:** Mark the recommended option with "(Recommended)" and list it
   as option A. If no option is clearly better (depends on user intent), omit the marker.

3. **Empty-answer guard:** If AskUserQuestion returns empty/blank: re-prompt once with
   "I didn't catch a response — here are the options again:" and the same options.
   If still empty: pause the skill — "Pausing — let me know when you're ready."
   Do NOT auto-select any option.

4. **Vague answer recovery:** If the user says "whatever you think" / "either is fine" /
   "up to you": state "Going with [recommended] since no strong preference. Noted as
   assumption." Proceed with recommended.

5. **Topic sanitization:** Before constructing any file path with `<topic>`, sanitize to
   lowercase alphanumeric + hyphens only (`[a-z0-9-]`). Strip `/`, `..`, spaces, and
   special characters. This prevents path traversal in scratch/landscape file writes.

## Safety Rules

- NEVER output text between tool calls — all user-facing output goes through AskUserQuestion or final write steps.
- NEVER modify files outside designated output paths without asking.
- NEVER add features, pages, or components — design skills produce design artifacts, not code (except in Review fix loop).
- Respect `.claude/rules/design.md` anti-slop checklist in all recommendations.
- No AI slop vocabulary (see `.claude/rules/code-quality.md`).
- **Output silence** — Do not emit text between tool calls. Single formatted output at the end only.

---

## Mode Execution

After selecting the mode, Read the corresponding mode file from this skill's directory and follow its procedure exactly:

- **Consult:** Read `.claude/skills/design/mode-consult.md` and follow its procedure.
- **Review:** Read `.claude/skills/design/mode-review.md` and follow its procedure.
- **Variants:** Read `.claude/skills/design/mode-variants.md` and follow its procedure.
- **Plan-Check:** Read `.claude/skills/design/mode-plan-check.md` and follow its procedure.

The Interactive Question Protocol and Safety Rules above apply to ALL modes.

## Output Format

Output varies by mode:
- **Consult:** Writes `app/DESIGN.md` with the complete design system specification.
- **Review:** Writes `tasks/<topic>-design-review.md` with audit scores, findings, and fix results.
- **Variants:** Writes `tasks/<topic>-variants.md` with variant descriptions, comparison board, and selected direction.
- **Plan-Check:** Writes updated plan file with design dimension scores and completion summary.
