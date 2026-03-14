---
# Example: path-specific rule — only loads when Claude reads matching files.
# Adapt the paths glob to match your project's source directories.
paths:
  - "src/**/*.{ts,py,js,go}"
  - "lib/**/*.{ts,py,js,go}"
---

# Example rules file — adapt to your project
# Copy to .claude/rules/code-quality.md and modify for your needs.
# This file demonstrates path-specific loading via the paths: frontmatter above.
# It will only load when Claude reads files matching those patterns.

# Code Quality

## Simplicity override

Avoid over-engineering. Only make changes that are directly requested or clearly necessary.
- Don't add features, refactor code, or make "improvements" beyond what was asked.
- Don't add error handling for scenarios that can't happen.
- Don't create abstractions for one-time operations.
- Don't design for hypothetical future requirements.

## Readability

- No nesting deeper than 3 levels. Use guard clauses.
- Prefer explicit loops over nested comprehensions.
- Name variables for clarity, not brevity.
