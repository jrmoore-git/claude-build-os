---
scope: "Integrate Perplexity Sonar Deep Research into BuildOS skills pipeline"
surfaces_affected:
  - .claude/skills/research/SKILL.md (new)
  - .claude/skills/think/SKILL.md (Phase 2.75)
  - .claude/skills/explore/SKILL.md (pre-flight)
verification_commands:
  - "python3.11 scripts/research.py --help"
  - "python3.11 scripts/research.py --sync --model sonar 'test query' 2>&1 | head -5"
rollback: "git revert HEAD~1"
review_tier: self
verification_evidence: "Benchmark test already completed — Perplexity vs 3-agent pattern"
---

# Plan: Perplexity Research Integration

## Context

scripts/research.py already exists and works. Benchmark shows 7x faster, better sourced,
cheaper than the 3-agent WebSearch/WebFetch pattern. Three integration points identified.

## Track 1: /research standalone skill (NEW)

Create `.claude/skills/research/SKILL.md`:
- User invokes `/research "topic"` or `/research --academic "topic"`
- Two modes: deep (async, default) and quick (sync, --quick flag)
- Calls `python3.11 scripts/research.py` with appropriate flags
- Output to `tasks/<topic>-research.md`
- Privacy gate before sending queries to Perplexity
- System prompt option for structured output

## Track 2: /think discover Phase 2.75 (MODIFY)

Replace the broken web_search.py + WebSearch fallback chain with research.py:
- Keep the privacy gate (already exists)
- Replace search commands with: `python3.11 scripts/research.py --effort medium -o tasks/<topic>-landscape.md "<generalized query>"`
- Keep the three-layer synthesis (Layer 1/2/3) and eureka check
- Keep the landscape write to `tasks/<topic>-landscape.md`
- Remove references to web_search.py and YOU_COM_API_KEY

## Track 3: /explore pre-flight (MODIFY)

Add optional research step between pre-flight questions and debate.py explore call:
- After Step 3b (compose context), before Step 4 (route to mode)
- Only for explore mode (not validate or pressure-test)
- Run: `python3.11 scripts/research.py --sync --model sonar -o /tmp/<topic>-preflight-research.md "<question>"`
- Use sync sonar (fast, cheap) not deep research — explore pre-flight needs speed
- Append research findings to PREFLIGHT_CONTEXT
- Skip if user opted out of search in pre-flight

## What NOT to change

- /challenge — enrich_context.py already handles context. Adding research would slow a quick gate.
- /elevate — strategic judgment, not evidence gathering. Would over-engineer.
- /check, /ship, /plan — codebase work, not web research.
- debate.py itself — no code changes needed. --context already works.
