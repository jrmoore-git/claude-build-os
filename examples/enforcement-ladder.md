# The Enforcement Ladder — One Policy, Four Levels

This example shows the same policy — "don't commit secrets" — enforced at each level of the [enforcement ladder](../docs/the-build-os.md#part-v-the-enforcement-ladder). Start at Level 1 and escalate when a level fails to hold.

---

## Level 1 — Advisory (CLAUDE.md)

A line in your CLAUDE.md:

```markdown
Never commit .env files or files containing API keys, tokens, or passwords.
```

**Strength:** Zero setup. Claude sees it every session.
**Weakness:** Advisory only — Claude tries to follow it but compliance is not guaranteed. Research shows adherence drops as instruction count grows.

---

## Level 2 — Conditional Rule (.claude/rules/security.md)

A rule file that loads when Claude touches relevant files:

```markdown
---
paths:
  - ".env*"
  - "**/*.pem"
  - "**/*.key"
---

# Secret file protection

Do not read, edit, write, or commit files matching these patterns. These contain credentials. Use environment variables to reference secrets — never hardcode them.
```

**Strength:** Only loads when relevant (saves context). More prominent than a CLAUDE.md line.
**Weakness:** Still advisory. Claude reads and tries to follow, but can still slip.

---

## Level 3 — Hook (.claude/settings.json)

A PreToolUse hook that blocks the action deterministically:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$CLAUDE_FILE_PATH\" | grep -qE '\\.env|\\.pem|\\.key'; then echo 'BLOCKED: Cannot write to secret files' >&2; exit 2; fi"
          }
        ]
      }
    ]
  }
}
```

**Strength:** Deterministic. Exit code 2 = blocked. Claude cannot override this.
**Weakness:** Requires setup. Only covers the specific tool events you hook.

---

## Level 4 — Architecture (.gitignore + pre-commit)

Structural protection that doesn't depend on Claude at all:

```gitignore
# .gitignore
.env
.env.*
*.pem
*.key
```

Plus a git pre-commit hook that scans for high-entropy strings or known secret patterns.

**Strength:** Works regardless of who or what commits. Cannot be bypassed by any tool.
**Weakness:** Highest setup cost. Only catches at commit time, not at write time.

---

## When to escalate

| Signal | Action |
|---|---|
| Rule written, never violated | Stay at current level |
| Same rule violated once | Investigate — was it a context issue or a pattern? |
| Same rule violated twice | Escalate one level immediately |
| High blast radius (data exposure, sends, deletes) | Start at Level 3 or 4 — don't wait for violations |

The enforcement ladder is not about punishing failures. It is about matching the strength of the control to the cost of the failure.
