# Security — External Updates & MCP Evaluation

Detailed checklists for evaluating external code and MCP servers. Read when adding dependencies, MCP servers, or upgrading versions.

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
