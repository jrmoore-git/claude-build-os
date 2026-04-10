# Landscape — Managed Agents for BuildOS

## Layer 1: What everyone already knows
- Managed Agents = Anthropic-hosted agent infrastructure (public beta April 2026)
- Durable sessions, sandboxed containers, built-in tools, event streaming
- $0.08/hour active session time + standard token costs
- Claude-only (no GPT, no Gemini)
- MCP server integration supported (both local and remote transports)

## Layer 2: What the current discourse says
- "Start with subagents, move to Agent Teams only when parallelism is measured as beneficial" — subagents are cheaper
- Multi-agent orchestration (agent spawning agents) is research preview, NOT production-ready
- Early adopters shipping 10x faster by offloading infrastructure (Notion, Rakuten, Sentry)
- Async subagent spawning works — background agents continue working after main agent finishes
- Key gotcha: don't over-parallelize early. Coordination overhead eats gains.
- MCP Connector is cloud-native — no separate client needed, configure at init or via .mcp.json

## Layer 3: Given what WE know — is the conventional approach wrong?
- **Conventional**: Use Managed Agents to replace your agent infrastructure entirely.
- **Our situation**: BuildOS's debate system REQUIRES cross-model diversity (GPT + Gemini + Claude). Managed Agents is Claude-only. We cannot replace the debate pipeline.
- **The insight**: Managed Agents is additive, not replacement. It handles the Claude-only legs of our pipeline (refine, single-model review, consolidation) while the multi-model legs stay local via LiteLLM.
- **Second insight**: The persistent session model maps perfectly to Jarvis's always-on aspiration. Instead of cron → fire-and-forget → handoff.md, a Managed Agent session could maintain continuous state across email/calendar/promise monitoring.
- **Third insight**: BuildOS's session management infrastructure (wrap-session, handoff.md, current-state.md, compaction protocol) exists because Claude Code sessions are ephemeral. If Managed Agent sessions are truly durable, some of that infrastructure becomes redundant — but only for workloads that move to the cloud.

## Assessment
No eureka moment that invalidates conventional wisdom. The conventional approach (offload infrastructure) is sound. Our twist: hybrid architecture where multi-model work stays local and single-model long-running work goes to cloud. This is additive, not transformative.
