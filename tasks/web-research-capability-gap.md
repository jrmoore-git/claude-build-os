# Problem: Web Research is Too Slow for Deep Multi-Source Synthesis

## The Problem

When a session needs exhaustive research across multiple domains (e.g., "research effective questioning techniques across 8+ fields"), the current tooling (WebSearch + WebFetch) takes 7-20 minutes per research agent. Three parallel agents doing deep research took ~20 minutes total wall-clock. This is 5-10x slower than purpose-built research tools.

## Root Cause

WebSearch and WebFetch are serial tools designed for spot lookups, not literature reviews:
- Each WebSearch returns a page of results
- Each WebFetch downloads and processes one URL at a time
- A deep research agent does 50-70 tool calls (searches + fetches) sequentially
- No batching, no parallel fetches, no result caching across searches

## What We Need

A research capability that can:
1. Take a multi-faceted research question
2. Search across many sources in parallel
3. Read and synthesize findings
4. Return a structured research document in 2-5 minutes instead of 15-20

## Candidate Solutions to Evaluate

### Option A: Perplexity API (Deep Research mode)
- Purpose-built for multi-source synthesis
- Has a "deep research" mode that does exactly what we need
- API available at api.perplexity.ai
- Pricing: per-query, relatively affordable
- Would replace the "research agent" pattern entirely

### Option B: OpenAI Deep Research API
- Gold standard per our own research (separate clarification model from research model)
- API supports clarifying questions + research plan + execution
- More expensive but highest quality
- 3-6 "pivotal unknowns" approach matches our intake design

### Option C: Google Gemini Deep Research
- Google Search integration = broadest web coverage
- Grounding with Google Search is a built-in feature
- Available via Gemini API

### Option D: You.com Research API
- Agentic multi-source search
- Research-focused API endpoint
- Cheaper than OpenAI/Perplexity for this use case

### Option E: Tavily / Exa / SerpAPI + parallel fetching
- Lower-level building blocks
- Could build a custom research pipeline in scripts/
- More control, more work to build
- Tavily is specifically designed for AI agent web search

### Option F: MCP server for web research
- Wrap one of the above APIs in an MCP server
- Integrates natively with Claude Code
- Could replace WebSearch/WebFetch for research tasks
- firecrawl MCP server exists and handles deep crawling

## Evaluation Criteria

1. **Speed**: Must complete a "research 8 domains, read 20+ sources, synthesize" task in under 5 minutes
2. **Quality**: Must produce source-attributed, structured findings (not just summaries)
3. **Cost**: Research tasks happen ~2-5 times per session, budget ~$0.50-2.00 per research task
4. **Integration**: Must work from Claude Code (MCP server, script, or direct API call)
5. **Reliability**: Must handle rate limits, timeouts, and failed fetches gracefully

## Current Architecture (for reference)

Research is done by spawning Agent subagents with WebSearch/WebFetch tools. The agent:
1. Runs WebSearch queries (10-20 per research task)
2. Fetches promising URLs with WebFetch (20-40 per task)
3. Synthesizes findings into a markdown document
4. Returns the document

The agent pattern itself is fine -- it's the WebSearch/WebFetch throughput that's the bottleneck.

## Desired End State

A `/research` capability (script, MCP server, or skill) that:
- Takes a research question + desired output structure
- Returns a sourced research document in <5 minutes
- Can be called from skills (like /debate --explore pre-flight) or directly
- Costs <$2 per deep research task

## Evaluation (2026-04-11)

### Option A: Perplexity Sonar Deep Research — RECOMMENDED

**Pricing:** $2/M input, $8/M output, $3/M reasoning, $2/M citation tokens, $5/K search queries. Per-request fee: $5-12 per 1K requests depending on context depth. Typical deep research query: ~$0.40-0.80.

**Speed:** Async mode available (POST /v1/async/sonar, poll for results). Designed for multi-minute deep research — does 50-100+ source reads internally and returns a synthesized report. Replaces our "spawn agent with 50 WebSearch/WebFetch calls" pattern entirely.

**Integration:** OpenAI-compatible API. Can call via Python requests or wrap in an MCP server. Also available through OpenRouter (`perplexity/sonar-deep-research`). 128K context window.

**Recent features (2026):** Async mode, reasoning effort parameter, academic mode for scholarly sources, richer citations with title/URL/date.

**Verdict:** Best fit. Purpose-built for exactly our use case. $0.40-0.80/query is well within the $2 budget. Async mode means we fire it and poll. Quality is the unknown — needs a head-to-head test against our current agent pattern.

### Option B: OpenAI Deep Research API — TOO EXPENSIVE

**Pricing:** o3-deep-research: $10/M input, $40/M output. o4-mini-deep-research: $2/M input, $8/M output. Real-world costs: **~$10/query (o3) or ~$1/query (o4-mini)**. One benchmark spent $100 across 10 o3 queries.

**Quality:** Highest quality per the previous session's research. Separate clarification model from research model.

**Verdict:** o3 is a non-starter at $10/query. o4-mini at ~$1/query is viable but 2-3x Perplexity for likely comparable quality on research synthesis tasks. Worth testing as a fallback if Perplexity quality disappoints.

### Option C: Tavily — GOOD FOR SEARCH LAYER, NOT DEEP RESEARCH

**Pricing:** Search: $0.005-0.008/query. Research API: 15-250 credits/query (Pro) = $0.12-2.00 per research request. Free tier: 1,000 credits/month.

**MCP server:** Official `tavily-mcp` with one-line setup: `claude mcp add --transport http tavily https://mcp.tavily.com/mcp/?tavilyApiKey=KEY`. Tools: search, extract, map, crawl.

**Verdict:** The search/extract tools are a direct upgrade over WebSearch/WebFetch for spot lookups (faster, better structured). The Research API (Pro) is newer and less proven than Perplexity for deep synthesis. Best as a complementary tool, not the primary research engine.

**Ownership note:** Nebius acquired Tavily in Feb 2026. Future pricing/roadmap uncertain.

### Option D: Firecrawl MCP — COMPLEMENTARY, NOT PRIMARY

**Setup:** `claude mcp add firecrawl -e FIRECRAWL_API_KEY=KEY -- npx -y firecrawl-mcp`. Tools: scrape, crawl, extract, map.

**Pricing:** Free tier: 10 scrapes/min, 5 searches/min.

**Verdict:** Good for crawling/scraping specific sites (documentation, specific domains). Not a research synthesis tool — it fetches and extracts, doesn't search and synthesize. Complements Perplexity or Tavily.

### Recommendation

**Phase 1 (quick win):** Add Tavily MCP server for better search/extract in normal sessions. One-line setup, free tier for testing, direct replacement for WebSearch/WebFetch spot lookups.

**Phase 2 (research capability):** Build a `scripts/research.py` that calls Perplexity Sonar Deep Research API. Input: research question + output structure. Output: sourced markdown document. Wire it into a `/research` skill or make it callable from other skills. Test quality head-to-head against current 3-agent pattern using the "questioning techniques across 8 domains" task as benchmark.

**Phase 3 (if Perplexity disappoints):** Try o4-mini-deep-research as fallback. 2-3x cost but potentially higher quality.

**Skip:** OpenAI o3 deep research (too expensive), Firecrawl as primary (wrong tool for synthesis), building a custom pipeline from scratch (Perplexity already did the hard work).

## Implementation Status (2026-04-11) — DONE

All three phases completed in a single session:

### Built
- `scripts/research.py` — standalone CLI wrapping Perplexity Sonar Deep Research API
  - Async (deep) and sync (quick) modes
  - --effort, --academic, --system, --output flags
  - Tested: 2m50s for 8-domain research task (vs 15-20min agent pattern)

### Integrated
1. **`/research` skill** (`.claude/skills/research/SKILL.md`) — standalone user-invocable skill
2. **`/define discover` Phase 2.75** — replaced broken web_search.py with research.py sonar
3. **`/debate` explore Step 3c** — research enrichment before divergent exploration

### Benchmark results
| Metric | 3-Agent Pattern | Perplexity Deep Research |
|---|---|---|
| Time | ~15-20 min | 2 min 50 sec |
| Sources | 43 | 48 |
| PMC citations | 5 | 9 |
| Cost | ~$3-5 | ~$0.40 |
| Integration section | None | 8 synthesized principles |
| Failure modes | Per-domain only | Dedicated taxonomy |

## Session Context

This came up during a session researching "effective questioning techniques for AI intake" across Socratic method, MI, JTBD, coaching, CBT, journalism, and academic research. Three parallel research agents completed the work with good quality but took 7-20 minutes each. The quality was fine -- the speed was not.
