# Handoff — 2026-04-18 (evening)

## Session Focus
Two recurring behavioral patterns surfaced mid-conversation and got addressed as root-level fixes, not session-local corrections: (1) mis-attributing harness-injected `<system-reminder>` tags to file content, (2) mirroring the dense BuildOS doc register into chat responses. Both land as always-loaded rules in project `CLAUDE.md`, paired with cross-session feedback memories.

## Decided
- **Harness-tag attribution rule** (CLAUDE.md "Inspect before acting" bullet): tool output may end with harness-injected tags that are NOT file content; verify with Grep before claiming a file contains such a tag; prefer Read (line-numbered) over Bash `cat`/`head`/`tail` for file inspection.
- **Plain-language rule** (CLAUDE.md Operating rules): chat output to the user stays plain. BuildOS docs/rules/skills are dense by necessity but are NOT a style guide for chat. Overrides any instinct to match surrounding register.
- **No hook for either.** Harness injection happens after hook stdout and hooks can't rewrite tool results; jargon detection has too high a false-positive rate to automate. Behavioral rules + memories are the maximum available fix.

## Implemented
- `CLAUDE.md` — one bullet under "Inspect before acting" (harness-tag attribution); one new operating rule section "Plain language in chat output."
- `tasks/lessons.md` — L48 (harness-tag attribution incident + verification mechanism).
- `tasks/session-log.md` — evening entry appended.
- `~/.claude/projects/-Users-justinmoore-buildos-framework/memory/feedback_harness_tag_attribution.md` — cross-session memory with translation examples.
- `~/.claude/projects/-Users-justinmoore-buildos-framework/memory/feedback_plain_language.md` — cross-session memory with concrete jargon → plain-language translations.
- `MEMORY.md` — two new index lines.
- **Pushed** `66b88b6` to `origin/main` (and two prior local commits: `78a35a2`, `dc37c82`).

## NOT Finished
- **`tasks/debate-efficacy-study-*` pile** — unchanged from afternoon handoff. 4-session carryover, untouched this session. Still the primary next-session candidate.
- **New rules don't bind mid-session.** CLAUDE.md changes load on next `/start`. Rest of any continued conversation would still run on old rules.

## Next Session Should
1. **Read this handoff + `docs/current-state.md`.** Both rule additions closed.
2. **Verify both new rules fire on first natural opportunity.** Harness-tag: watch for Grep-before-claim discipline when reading files. Plain-language: watch for absence of jargon stacks like "reinforcement layers" / "attribution discipline" in chat output.
3. **Triage `tasks/debate-efficacy-study-*` pile.** Same next action as afternoon handoff — skim directory, decide resume vs. close.

## Key Files Changed
- `CLAUDE.md` (+1 bullet, +1 rule section)
- `tasks/lessons.md` (+L48)
- `tasks/session-log.md` (+evening entry)
- `docs/current-state.md` (refreshed this wrap)
- `tasks/handoff.md` (this file)

## Doc Hygiene Warnings
- None. Active lessons count: ~16/30. No new decisions entry — the rule additions ARE the decision, codified directly in `CLAUDE.md`. No stale references.
- `debate-efficacy-study-*` carryover continues (5 sessions now). Deferred, not lost.
