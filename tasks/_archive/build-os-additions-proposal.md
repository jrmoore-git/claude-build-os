# Proposal: Four Additions to the Build OS Repo

**Author:** Claude Opus (Round 1)
**Date:** 2026-03-13
**Debate type:** Architecture (3 rounds)
**Scope:** Evaluate four proposed additions to the published Build OS repo (github.com/jrmoore-git/claude-build-os). The repo has 22 files across 4 docs, 4 commands, 7 templates, 4 optional command templates, 2 hook examples, and a starter CLAUDE.md. An audit identified 4 gaps.

---

## Context

The Build OS repo is live on GitHub. It was validated by a prior 3-round cross-model debate (build-os-4doc) that established strict topic ownership across 4 docs. The repo targets engineers building with Claude Code, from solo projects to production agent systems.

An audit of the published repo found four gaps between what the docs describe and what the repo demonstrates:

1. **Hooks are described but not explained.** The enforcement ladder says "use hooks" and there are 2 example hook scripts, but no guide explains how Claude Code hooks actually work (PreToolUse, PostToolUse, matcher syntax, settings.json structure). A reader who hasn't used hooks doesn't know where to start.

2. **The LLM boundary is described but never shown in code.** "The model may decide; software must act" is the most important principle in the repo. The Build OS explains it conceptually. No file shows the pattern in code: parameterized SQL, schema validation, the `fetch → LLM → validate → apply → audit` pipeline.

3. **Review personas have no growth path.** The `/review` command has 4-5 starter questions per persona. The docs don't mention that teams should expand these into a dedicated PERSONAS.md as the project matures.

4. **Lesson promotion has no concrete example.** The promotion lifecycle (`lessons.md → .claude/rules/ → hook → architecture`) is described in Build OS Part V, but no example shows what it actually looks like to promote a lesson to a rule.

## Proposed Additions

### Addition 1: `docs/hooks-guide.md` (~80 lines)

A short guide explaining:
- What hooks are (shell commands that fire on Claude Code tool events)
- The two hook types: `PreToolUse` (can block) and `PostToolUse` (runs after)
- The `matcher` field (regex against tool names: `Write|Edit`, `Bash`, etc.)
- A complete starter `settings.json` showing both types
- When to use each type (block dangerous writes, auto-run tests, enforce gates)
- Hook safety warnings (hooks run with user permissions, review like CI scripts)
- Link to Anthropic's hook documentation

This does NOT duplicate enforcement ladder content from the Build OS. It's the practical "how" that complements the "why" already in the Build OS.

### Addition 2: `examples/toolbelt-example.py` (~60 lines)

A single Python script demonstrating the LLM boundary pattern:
- Deterministic fetch (parameterized SQL query)
- Schema validation (validate LLM output against expected structure)
- Deterministic apply (parameterized INSERT with validated data)
- Audit logging (write operation record)
- Error handling (what happens when the LLM output is malformed)

The script is self-contained, uses only stdlib (sqlite3, json, sys), and is heavily commented to explain WHY each step exists. It does not run against any real system — it's a teaching example.

### Addition 3: Persona growth note in `templates/review-protocol.md`

One paragraph added after the review order section:

> **Growing your review protocol:** As your project matures, expand each persona's questions into a dedicated `PERSONAS.md` file with domain-specific review checklists. The starter questions above cover common concerns; production systems benefit from detailed questions tuned to their specific architecture, trust boundaries, and failure modes.

### Addition 4: Promotion example in `templates/lessons.md`

One concrete example added after the format header showing what promotion looks like:

```
| # | Lesson | Source | Rule |
|---|---|---|---|
| L12 | Query-param auth leaks tokens to browser history and logs | Security review | Use HttpOnly cookies or headers |
| ~~L12~~ | [PROMOTED → .claude/rules/security.md] Lesson L12 promoted after second violation. | | |
```

With a note: "When a lesson has been violated twice, promote it to a `.claude/rules/` file and mark it as promoted here. The lesson stays in the log for history, but the rule file is now the enforcement point."

---

## What the challengers should evaluate

1. **Necessity:** Are all four additions needed? Is any one of them already adequately covered by existing files?
2. **Scope creep:** Do any additions expand the repo beyond its mission (framework for building with Claude Code)?
3. **Maintenance burden:** Do these additions create files that will drift from Anthropic's actual hook API or Claude Code behavior?
4. **Alternative approaches:** Is there a simpler way to address each gap?
5. **Topic ownership:** Do any additions violate the strict topic ownership from the prior debate?
