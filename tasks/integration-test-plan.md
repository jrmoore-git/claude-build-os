---
scope: "Comprehensive integration test of all new systems built 2026-04-10"
created: 2026-04-10
---

# Integration Test Plan — 2026-04-10 New Systems

## Systems Under Test

| System | File | What's New |
|--------|------|------------|
| debate.py — challenge | scripts/debate.py | Multi-model adversarial review (3 personas) |
| debate.py — judge | scripts/debate.py | Independent judgment + consolidation + MA option |
| debate.py — refine | scripts/debate.py | 6-round cross-model iterative refinement |
| debate.py — explore | scripts/debate.py | **NEW** — divergent directions + synthesis |
| debate.py — pressure-test | scripts/debate.py | **NEW** — counter-thesis + premortem frame |
| debate.py — pre-mortem | scripts/debate.py | **NEW** — prospective failure analysis |
| debate.py — review-panel | scripts/debate.py | Multi-persona anonymous panel review |
| managed_agent.py | scripts/managed_agent.py | **NEW** — Anthropic Managed Agents consolidation |
| check_conviction_gate.py | scripts/check_conviction_gate.py | **NEW** — recommendation field validation |
| Config prompts | config/prompts/*.md | **NEW** — explore, pressure-test, preflight prompts |
| debate.py — check-models | scripts/debate.py | Model availability validation |

## Test Matrix

| # | Name | Commands Exercised | Domain | Personas | Key Verification |
|---|------|--------------------|--------|----------|------------------|
| 1 | Full Pipeline | challenge → judge → refine | API caching layer | architect, security, pm | All 3 stages produce output; refine improves on judgment |
| 2 | Explore | explore (3 directions + synthesis) | Build vs buy analytics | N/A (single model) | 3 distinct directions + synthesis section present |
| 3 | Pressure-Test | pressure-test --frame challenge | Webhook retry system | N/A (single model) | Counter-thesis identifies weaknesses |
| 4 | Pre-mortem | pre-mortem | Notification routing plan | N/A (single model) | Failure scenarios identified from plan |
| 5 | Review Panel | review-panel (4 personas) | Auth/JWT migration | architect, security, pm, product | >= 3 personas respond with [MATERIAL]/[ADVISORY] tags |
| 6 | Conviction Gate | check_conviction_gate.py + pressure-test --frame premortem | Dev velocity optimization | N/A | Gate catches intentional fixture flaws (empty owner, TBD why-now) |
| 7 | Managed Agents | challenge → judge --use-ma-consolidation + judge --no-consolidate | Email pipeline redesign | architect, security, pm | MA path used or fallback triggered; no-consolidate baseline works |

## Test Fixtures

All in `tests/fixtures/`:

| Fixture | Domain | Purpose | Intentional Issues |
|---------|--------|---------|-------------------|
| proposal-caching-layer.md | Infrastructure | Full pipeline stress test | None — clean proposal |
| proposal-webhook-retry.md | Reliability | Pressure-test target | None — clean proposal |
| proposal-auth-migration.md | Security/compliance | Security-heavy review panel | Legal deadline creates urgency tension |
| proposal-email-pipeline.md | Automation | MA consolidation test | None — clean proposal |
| proposal-metrics-dashboard.md | Observability | (Available for ad-hoc runs) | Over-engineering risk |
| proposal-conviction-gate-sample.md | Process | Conviction gate validation | Empty Owner (#4), TBD why-now (#2), generic team owner (#2) |
| plan-notification-system.md | Infrastructure | Pre-mortem input | Coupling risk, rate limit gaps |

## What Each Test Validates

### Test 1: Full Pipeline
- `challenge` produces findings from 3 independent models (via personas)
- Challenge output has YAML frontmatter with model mapping
- `judge` consolidates multi-challenger findings (dedup + corroboration)
- `--verify-claims` runs claim verification pass
- `refine` iterates 6 rounds across 3 model families (gemini → gpt → claude)
- Refined output is substantively different from raw proposal
- All 3 outputs written to disk; debate-log.jsonl has entries

### Test 2: Explore
- 3 distinct divergent directions generated (not just rephrasing)
- Synthesis pass integrates across directions
- Custom `--context` (market data) is reflected in output
- Output follows explore prompt template structure

### Test 3: Pressure-Test (Challenge Frame)
- Counter-thesis identifies genuine weaknesses in the proposal
- Output follows pressure-test prompt template structure
- Different from explore output (adversarial vs divergent)

### Test 4: Pre-mortem
- Assumes the plan failed and writes retrospective
- Identifies failure modes specific to the plan's architecture
- Different from pressure-test (future failure vs present weakness)

### Test 5: Review Panel
- 4 personas respond independently (architect, security, pm, product)
- Findings tagged [MATERIAL] or [ADVISORY]
- Security persona catches JWT-specific risks
- Product persona evaluates migration UX impact
- `--enable-tools` gives reviewers read-only verifier access

### Test 6: Conviction Gate
- `check_conviction_gate.py` parses `## Recommendations` section
- Catches: empty Owner on recommendation #4
- Catches: "TBD" in Why-now on recommendation #2
- Catches: "Platform Team" as generic team name (not individual) on #2
- JSON output mode works (`--json`)
- Premortem frame produces failure analysis on same proposal

### Test 7: Managed Agents
- If `MA_API_KEY` set: MA consolidation runs, session created, environment cleaned up
- If `MA_API_KEY` not set: graceful fallback to local consolidation
- stderr shows MA dispatch/fallback status (operator visibility)
- `--no-consolidate` baseline produces judgment without consolidation step
- debate-log.jsonl includes `consolidation_source` and `ma_fallback` fields

## Running

```bash
# All 7 tests (expect ~15-25 min with LiteLLM)
./tests/run_integration.sh

# Specific tests only
./tests/run_integration.sh 2 3 4    # just explore, pressure-test, pre-mortem

# Single test
./tests/run_integration.sh 7        # just MA path
```

## Prerequisites

- LiteLLM proxy running with claude-opus-4-6, gpt-5.4, gemini-3.1-pro
- `MA_API_KEY` in environment (for test 7 MA path — fallback tested either way)
- python3.11 available
- Unit tests pass (pre-flight check)

## Pass Criteria

- All 7 tests produce output files >= 15-20 lines
- No command exits non-zero (except conviction gate, which should reject the flawed fixture)
- debate-log.jsonl gains entries for each debate.py invocation
- MA path either succeeds or falls back gracefully (both are PASS)
- Review panel gets >= 3 persona responses
