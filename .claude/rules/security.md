---
description: Credential handling, secrets, trust boundaries, privacy, external updates
globs:
  - ".env*"
  - "config/**"
  - "docker/**"
  - "skills/**"
  - "package*.json"
  - "scripts/*.sh"
---

# Security Rules

- NEVER print secret values in tool output. Use Write tool for .env files. Use `echo "REDACTED"` in Bash. Treat every tool output as potentially logged.
- NEVER hallucinate user details. If you don't know something about the user, leave it blank or ask. Only use facts from their own words, config files, or the PRD.
- Docker socket mount = security violation. Agent container never gets Docker socket; health daemon restarts externally.
- Web auth: cookie-based only, HttpOnly. No tokens in URLs (query-param auth leaks tokens).
- Verify exact email addresses against actual OAuth tokens. Never assume from domain (lesson: `@company.com` vs `@companycapital.com`, `user@` vs `user.name@`).
- Never interpolate untrusted text into Python `-c` source strings. Pass untrusted data via `sys.argv`. SQL escaping (`'` → `''`) does NOT protect Python string literals from quote-escape injection.
- LIKE wildcards (`%`, `_`) need separate escaping from SQL injection. Escape as `\%`, `\_` with `ESCAPE '\'` on all LIKE clauses that include user input.
- Audit log `summary` fields must never include untrusted content (meeting titles, email subjects, transcript excerpts). These fields are later read by LLMs and injected into prompts — stored untrusted content becomes prompt injection persistence. Store only metadata: IDs, counts, dates, contact names.
- Never put API keys in `curl -u ":$KEY"` or `curl -H "Authorization: $KEY"` as shell arguments. The key is visible in `ps`, `top`, and process listings. Use Python `urllib.request` with the key in an `Authorization` header set via code, or write the key to a temp file and pass `-K @file`.
- Allowlist check pattern: use `if allowlist is not None and value not in allowlist` — NOT `if allowlist and value and value not in allowlist`. The latter has two bypasses: empty string (`value=""`) passes because `bool("")` is False, and `None` value passes because `bool(None)` is False. The correct check explicitly tests membership.
- `csv.DictWriter` with `QUOTE_MINIMAL` (the default) does not protect against spreadsheet formula injection. Cells starting with `=`, `+`, `-`, or `@` are treated as formulas by Excel/Sheets. If the CSV will be opened in a spreadsheet, sanitize: prefix any such values with a single quote, or use `quoting=csv.QUOTE_ALL`.
- Trust boundary enforcement must be consistent across ALL access paths. If a restricted user can reach the same data via a different command or skill, the boundary is bypassed. Check every path, not just the obvious one.

## Safety Rules Block Pattern

When a rule keeps being violated, create an explicit prohibitions block near the action point — not at the top of a long prompt. Example for a skill or automation component:

```markdown
## Safety Rules
- NEVER call send, deliver, or message tools
- NEVER reference files not explicitly listed above
- NEVER run open-ended searches without a result limit
- Output text only. Do not take action.
```

This pattern is especially important for skills and tool-using components. A rule buried in early instructions may not survive to the relevant step.

## Hook Safety

Hooks run with user permissions. A `.claude/settings.json` committed to a repo can execute arbitrary commands the moment Claude Code opens that repo. Review hook configs the way you would review CI scripts or Dockerfiles. Don't trust repo hook configs blindly.

## LLM Boundary

LLMs classify, summarize, draft, parse intent, and analyze sentiment. Everything else — SQL queries, API calls, state transitions, routing, file operations — is deterministic code.

**The rule:** LLM outputs must be structured (JSON), validated, and applied by deterministic code. If the LLM can cause irreversible state changes, it must not be the actor.

**Invocation layer:** Hardening the toolbelt with parameterized SQL is not enough if the calling code passes untrusted data through shell strings. Every argument from a skill to a tool must go through stdin JSON or validated positional args — never shell string interpolation of untrusted data.

**The test:** For every operation: "If the LLM hallucinates or misformats its output, what's the worst that happens?" If the answer involves data corruption, unauthorized access, or silent data loss — that operation must be deterministic code.

## External Updates Policy

No code from outside this repo is applied without review:
- Version upgrades, Docker image updates, npm/pip package additions
- MCP server additions or updates, community skills, runtime upgrades

**Security has BLOCKING VETO** on external updates that touch sensitive data.

**Review checklist:**
1. What new network access does this introduce?
2. What new data does it read? Audit every file/DB/env var access.
3. Does the changelog describe the full diff? If not, read the diff.
4. Does it pin its own dependencies? Transitive dependencies are attack surface.
5. What's the rollback plan? Pin the current version before upgrading.

**Auto-updates are banned.** `:latest` tags, unpinned pip installs, and auto-update flags are prohibited. Every version must be pinned.

## MCP Supply Chain Evaluation

Before adding or replacing any MCP server, document in tasks/decisions.md:

1. **What it can read** — which data sources (databases, files, APIs, env vars) does it access?
2. **What it can write** — which state can it modify? Does it have INSERT/UPDATE/DELETE on any DB?
3. **What credentials it holds** — which tokens, API keys, or auth material does it use? What scope do those credentials grant?
4. **External network calls** — does it phone home, send telemetry, or make outbound requests? To whom?
5. **Maintainer** — official vendor (first-party), well-known open source (auditable), or community/anonymous? Link to source repo + last commit date.

**Security has BLOCKING VETO** on MCP additions — same as other external code.

**Document format** (add to tasks/decisions.md as D##):
```
### D##: Add/Replace MCP — [name]
Reads: [list data sources]
Writes: [list state it can modify, or "read-only"]
Credentials: [token names + scope granted]
Network: [outbound hosts, or "loopback only"]
Maintainer: [vendor/repo link, last commit]
Decision: [approved/rejected + rationale]
```
