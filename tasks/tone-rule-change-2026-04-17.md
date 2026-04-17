# Global Tone Rule — Change Record

**Date:** 2026-04-17
**Motivation:** Opus 4.7 outputs feel more verbose / technical-jargon-heavy than 4.6. Research (see `tasks/opus-47-verbosity-research.md`) shows Anthropic actually tuned 4.7 *shorter* — the perception likely comes from (a) tokenizer inflation, (b) "more direct/opinionated" reading as denser, (c) register mirroring from dense project docs.

## What changed

Created `~/.claude/CLAUDE.md` (did not exist before) with a single `## Tone` section. Applies globally to all Claude Code sessions.

## Exact content added

```markdown
# Global CLAUDE.md

## Tone

- Plain language. Skip jargon unless it's a real term of art.
- Don't mirror the register of surrounding docs. Dense rule files and technical CLAUDE.md files are context, not a style guide.
- Match length to the question. One sentence if one suffices. Lists only when the content is actually a list.
- Confident ≠ dense. Short declarative sentences beat long qualified ones.
- No throat-clearing ("Great question", "Let me..."), no trailing summaries of what you just said, no "in conclusion".
- Kill hedges ("generally", "typically", "it depends", "in most cases") unless the uncertainty is real and load-bearing. If you don't know, say so.
- Technical terms carry weight — use one where one is needed, not three synonyms.
```

## Rollback

File did not exist before this change, so full rollback is:

```bash
rm ~/.claude/CLAUDE.md
```

Partial rollback (keep file, remove just the Tone section): edit `~/.claude/CLAUDE.md` and delete the `## Tone` block.

## How to test

1. Start a fresh session (CLAUDE.md changes don't apply mid-session — see Hard Rule in project CLAUDE.md).
2. Ask a few representative questions (meta-questions, technical questions, code questions).
3. Compare output length and register to prior sessions.
4. If it feels over-corrected (too terse, losing nuance), tune the bullets or roll back.

## Known risks

- May clip useful detail on genuinely complex questions. The "match length to question" bullet is supposed to prevent this but is subjective.
- "Confident ≠ dense" could push toward overconfident claims. The "if you don't know, say so" bullet is the counterweight.
- Conflicts with nothing in project CLAUDE.md — verified by grep for tone/verbosity/register on 2026-04-17.
