---
topic: Back-port enforcement patterns from OpenClaw to claude-build-os template
type: architecture
author: claude-opus
date: 2026-03-25
scope: "GitHub template repo jrmoore-git/claude-build-os"
---

# Proposal: Add Enforcement Patterns to claude-build-os Template

## Context

`claude-build-os` is a public GitHub template repo that describes a governance framework for Claude Code projects. It covers Tier 0–3 governance, the enforcement ladder (advisory → rules → hooks → architecture), and core principles. However, it ships theory without implementation — no working hooks, no settings.json example, no config files.

OpenClaw has been running this framework at Tier 3 for weeks and has learned hard lessons about what actually works. Four specific patterns are worth back-porting as concrete examples.

## Proposed Additions

### 1. Example `.claude/settings.json`

Add a starter settings.json showing hook wiring syntax. The template currently describes hooks conceptually but doesn't show the actual JSON structure Claude Code expects.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/pre-edit-gate.sh",
            "timeout": 10
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/plan-gate.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Location: `examples/settings.json`

### 2. Protected Paths Config + Pre-Edit Gate Hook

Add a working pre-edit gate hook that reads from a config file and blocks edits to protected paths without a matching plan artifact.

Key design decisions (validated by two cross-model debates):
- Config-driven path matching (not hardcoded patterns — they go stale)
- Only `*-plan.md` files count as authorization (proposals lack structured scope metadata)
- `surfaces_affected` in plan frontmatter must exactly match the target file (fnmatch or literal)
- 24-hour modification window AND content match required (historical artifacts don't permanently authorize)
- Fail closed on parse errors or missing fields

Files:
- `examples/config/protected-paths.json` — declares protected globs and exempt patterns
- `examples/hooks/pre-edit-gate.sh` — PreToolUse hook implementation

### 3. Plan Artifact Schema

Document the YAML frontmatter format that plan artifacts must follow. This is the contract between the hook and the developer.

```yaml
---
scope: "What this change does"
surfaces_affected: "scripts/outbox_tool.py, scripts/email_pipeline.py"
verification_commands: "pytest tests/test_outbox.py"
rollback: "git checkout scripts/outbox_tool.py"
review_tier: "Tier 1|Tier 1.5|Tier 2"
verification_evidence: "568 tests pass, smoke test green"
---
```

Key constraints:
- `surfaces_affected` must use exact file paths or globs (no prose descriptions)
- `verification_evidence` must not be "PENDING" at commit time
- Plan must exist BEFORE code edits to protected paths

Location: Add to `templates/review-protocol.md` or new `templates/plan-artifact.md`

### 4. "Artifact Must Match Target" Pattern in Docs

Document the false-pass bug pattern: a gate that checks for *any* recent artifact instead of a *matching* artifact will silently pass for unrelated edits. This is a non-obvious failure mode that took a cross-model debate to properly fix.

Location: Add to `docs/advanced-patterns.md` under enforcement patterns.

## What We Are NOT Adding

- Project-specific rules (integration gotchas, platform quirks, contact privacy)
- The debate.py script (too coupled to specific API keys and model routing)
- Full production settings.json (the example should be minimal and instructive)
- OpenClaw-specific skill authoring rules

## Risks

1. **Template bloat.** The template's philosophy is "start minimal, grow organically." Adding too many concrete examples may violate this principle. Mitigation: all additions go in `examples/` — they're reference implementations, not required config.

2. **Maintenance burden.** If Claude Code's hook API changes, example hooks become stale. Mitigation: hooks use simple shell + Python stdlib patterns with no external dependencies.

3. **Over-prescription.** Different projects have different protected paths. The example should demonstrate the pattern, not prescribe specific paths. Mitigation: example uses generic paths (`src/**/*.py`, `config/*.json`) not OpenClaw-specific ones.

4. **False sense of security.** Shipping a hook example might suggest that running it is sufficient for Tier 2+ governance. Mitigation: docs must state that hooks are one layer, not the whole story.

## Success Criteria

A new Claude Code project can copy the example files, customize `protected-paths.json` for their codebase, and have working plan-before-code enforcement within 10 minutes.
