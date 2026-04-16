---
decision: D19
original: "compactPrompt is not a valid Claude Code settings.json field — only CLAUDE.md Compact Instructions works"
verdict: HOLDS
audit_date: 2026-04-15
models: claude-opus-4-6, gpt-5.4, gemini-3.1-pro
judge: gpt-5.4
---
# D19 Audit

## Original Decision

`compactPrompt` in `~/.claude/settings.json` does not exist in the schema. The only lever for controlling compaction behavior is the `## Compact Instructions` section in CLAUDE.md. Multiple web sources and model recommendations were wrong about this.

## Original Rationale

Schema validation rejected the field. Tested empirically. The `## Compact Instructions` section is re-read from disk during compaction (auto and manual), so it reliably survives.

## Audit Findings

**3-model review (claude-opus-4-6, gpt-5.4, gemini-3.1-pro):** unanimous HOLDS.

**Judge (gpt-5.4):** APPROVE proposal as-is, 0 material findings accepted.

Key evidence examined:
- Observed `~/.claude/settings.json` schema contains only `hooks`, `effortLevel`, `skipDangerousModePermissionPrompt` — no `compactPrompt` field present. (EVIDENCED)
- CLAUDE.md `## Compact Instructions` section is actively maintained and functioning. (EVIDENCED)
- No reference to `compactPrompt` anywhere in the codebase except decisions.md itself. (EVIDENCED)

One advisory finding surfaced: wording could over-claim permanence across future Claude Code versions. Not a verdict-changer.

## Verdict

**HOLDS**

D19 is a factual schema observation, not a design choice. Conservative bias does not apply — the alternative was rejected because it failed validation, not out of excessive caution. The CLAUDE.md mechanism is version-controlled, co-located with project context, and demonstrably working.

## Risk Assessment

- **Risk of keeping:** Low. If a future Claude Code version adds `compactPrompt`, the project temporarily misses a second lever — but current behavior remains functional.
- **Risk of reversing:** Moderate-high. Would inject an unsupported field into settings.json, creating config noise and false confidence that compaction is controlled through two channels when only one is active.

**Optional wording refinement** (judge recommendation, not required): restate as "In the currently observed Claude Code schema/environment, `compactPrompt` is not a valid field" to avoid implying permanence across future versions.
