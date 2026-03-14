# Example rules file — adapt to your project
# Copy to .claude/rules/security.md and modify for your needs.
# Rules here are advisory — Claude tries to follow them but compliance is not guaranteed.
# For enforcement, use hooks (see the enforcement ladder in the-build-os.md Part V).
# Rules WITHOUT a paths: frontmatter load every session.
# Rules WITH paths: load only when Claude reads matching files.

# Security Rules

## LLM boundary

LLMs classify, summarize, and draft. Deterministic code performs state transitions, API calls, and data mutations. If the LLM can cause irreversible state changes, it must not be the actor.

## Provenance over plausibility

Never construct contact data, identifiers, or URLs from inference. All source data (emails, names, IDs, dates) must come from verified systems — not model generation. Validate human-provided IDs against a known-good reference before using them.

## Secret handling

Never print secret values in tool output. Use the Write tool for .env files. Treat every tool output as potentially logged.

## Hook safety

Hooks run with user permissions. Review hook configs in `.claude/settings.json` the same way you would review CI scripts — they execute arbitrary commands.
