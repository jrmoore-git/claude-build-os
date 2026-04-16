---
topic: context-optimization-v2
type: proposal
status: complete
implementation_status: partial
created_at: 2026-04-16T12:30:00-0700
producer: claude-opus-4-6
depends_on: context-optimization-v1 (shipped: 65d3368, 340f27e)
---

# Context Optimization V2 — Proposal

## Background

V1 shipped 4 changes targeting runtime context waste:
- `/start` bootstrap efficient reads: ~39K tokens saved per bootstrap (session-log tail, decisions grep, lessons tail)
- Ruff hook output truncation: ~800-1200 tokens saved per noisy Python edit
- Context-inject session dedup cache: ~400 tokens saved per repeat edit (avoids re-gathering)
- debate.py stdout trimming: explore + pressure-test no longer dump full LLM responses to stdout
- Reference rules moved to on-demand: ~3.6K tokens saved from static auto-load every session

V1 total estimated savings: **~43K tokens per session** (dominated by /start bootstrap fix).

This proposal covers 3 remaining high-confidence optimizations identified through deep exploration.

---

## Proposal 1: Context-Inject Silent Cache Hit

### Problem

`hooks/hook-context-inject.py` fires on every PreToolUse Write|Edit for Python files. V1 added a session-level cache so the hook doesn't re-gather context on repeat edits to the same file. However, **the cache hit path still re-injects the full additionalContext** (~2,500 chars) into the conversation every time.

After the first edit to a file, Claude already has the test names, import signatures, and git history in conversation. Re-injecting identical content is pure waste.

### Current code (lines 230-239 of `hooks/hook-context-inject.py`)

```python
if file_path in cache:
    result = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "additionalContext": cache[file_path],  # <-- re-injects every time
        }
    }
    print(json.dumps(result))
    sys.exit(0)
```

### Proposed fix

On cache hit, return allow without additionalContext:

```python
if file_path in cache:
    # Context already injected on first edit — don't re-inject
    sys.exit(0)
```

Silent exit = hook didn't output anything = Claude Code treats it as allow with no additional context.

### Savings

- Per repeat edit: ~2,500 chars (~625 tokens) eliminated
- Typical 10-edit session across 3 files: 7 repeat edits x 2,500 = **~17,500 chars saved (~4,375 tokens)**
- Context-inject was 78% of all hook output in a typical session. This eliminates most of it.

### Risk

- After compaction, Claude may have lost the initial injection. Subsequent edits to the same file won't re-inject.
- Mitigation: The context is still available through normal means (reading the test file, reading imports). The hook is additive context, not required context.
- Risk level: **Low**. The hook worked fine before it existed. Losing it after compaction is acceptable.

### Effort

2-line change. No tests needed (existing behavior: hook fires, allows edit — same outcome).

---

## Proposal 2: /design Mode Splitting

### Problem

`/design` is 97,644 bytes (~24,411 tokens) — the largest skill by far. It has 4 modes (consult, review, variants, plan-check) but loads the entire file regardless of which mode is invoked. You only use one mode at a time.

### Structure analysis

| Component | Lines | Bytes | Loads for |
|-----------|-------|-------|-----------|
| Preamble (frontmatter, routing, Q protocol, safety) | 1-79 | ~5,200 | All modes |
| MODE: CONSULT | 80-545 | ~18,200 | consult only |
| MODE: REVIEW | 546-1202 | ~28,600 | review only |
| MODE: VARIANTS | 1203-1477 | ~15,200 | variants only |
| MODE: PLAN-CHECK | 1478-2053 | ~31,600 | plan-check only |
| Shared rules (design critique format, AI slop, hard rules) | scattered | ~5,000 | review + plan-check |

### Separability: 85% clean

- Zero cross-mode references ("see review mode for..." appears nowhere)
- Each mode's procedure is self-contained
- Only shared elements: preamble (~5.2K), design critique format (~400B), AI slop rules (~3K)
- Output dependency: consult writes `app/DESIGN.md`, other 3 modes read it — but each handles its absence gracefully

### Proposed structure

```
.claude/skills/design/
  SKILL.md           # Preamble + routing table + shared rules (~10K)
                     # Router reads the mode-specific file on demand
  mode-consult.md    # 18.2K — consult procedure
  mode-review.md     # 28.6K — review procedure  
  mode-variants.md   # 15.2K — variants procedure
  mode-plan-check.md # 31.6K — plan-check procedure
```

### Per-invocation load after split

| Mode | Current | After split | Reduction |
|------|---------|-------------|-----------|
| consult | 97.6K (24.4K tok) | 28.4K (7.1K tok) | **71%** |
| review | 97.6K (24.4K tok) | 38.8K (9.7K tok) | **60%** |
| variants | 97.6K (24.4K tok) | 25.4K (6.4K tok) | **74%** |
| plan-check | 97.6K (24.4K tok) | 41.8K (10.5K tok) | **57%** |

### Open question: Does Read content work as skill instructions?

Claude Code loads `SKILL.md` natively and follows it as instructions. If the router in SKILL.md says "Read `mode-consult.md` and follow its procedure," we need to verify Claude actually follows the Read content with the same fidelity as directly-loaded SKILL.md content.

**This needs a spike before full implementation.** Proposed spike:
1. Create a trivial test skill with a router SKILL.md that reads a mode file
2. Invoke it and verify the mode file's instructions are followed
3. Test edge cases: does it follow multi-step procedures? Does it respect safety rules in the mode file?

If Read content is NOT followed reliably, the alternative is a build step that assembles mode-specific SKILL.md files — more complex but guaranteed to work.

### Savings

- Per /design invocation: **14-18K tokens saved** (varies by mode)
- /design is used ~2-4 times per project cycle

### Risk

- **Medium**. Depends on spike results. If Read content isn't followed reliably, need to fall back to build-step approach.
- Mode files could drift from shared rules if edited independently. Mitigated by keeping shared rules in SKILL.md (the always-loaded router).

### Effort

- Spike: 1 hour
- Implementation (if spike passes): 2-3 hours (mostly careful splitting + testing each mode)
- Implementation (build-step fallback): 4-5 hours

---

## Proposal 3: Shared Skill Boilerplate Extraction

### Problem

Multiple skills duplicate the same boilerplate blocks. The top offenders:

| Boilerplate block | ~Bytes | Duplicated in |
|-------------------|--------|---------------|
| Interactive Question Protocol | ~2,000 | design, challenge, review, investigate, start, elevate, think |
| Safety Rules (near-identical) | ~850 | design, challenge, review, investigate, healthcheck, plan, ship |
| OUTPUT SILENCE rule | ~200 | design, challenge, review, investigate, healthcheck, plan, ship, think |
| Completion Status Protocol | ~400 | challenge, review, investigate, healthcheck, plan |

Each skill that includes these pays the full token cost. For a session that invokes 2-3 skills, you're loading the same ~3K of boilerplate 2-3 times.

### Proposed approach

Extract shared blocks to a single reference file:

```
docs/reference/skill-shared-rules.md
```

Contains:
- Interactive Question Protocol (canonical version)
- Standard Safety Rules (canonical version)
- Output Silence rule
- Completion Status Protocol

Each skill replaces the inline block with a one-line pointer:
```
**Rules:** Follow the Interactive Question Protocol and Safety Rules in `docs/reference/skill-shared-rules.md`.
```

### Savings

Per skill invocation: ~2-3K bytes saved (replacing inline blocks with pointers). Across a session invoking 3 skills: **~6-9K bytes saved**.

However — this has a **fidelity risk**. Skills follow their SKILL.md content with high reliability because it's loaded as system-level instructions. A pointer to "read this file and follow it" adds a hop. If Claude doesn't read the file or doesn't follow it with the same fidelity, you lose safety rule enforcement.

### Risk assessment

- **Interactive Q Protocol:** Medium risk. These rules prevent bad UX (empty answers, vague responses). If missed, user experience degrades but nothing breaks.
- **Safety Rules:** Higher risk. "NEVER output text between tool calls" and "NEVER modify files outside designated paths" are guardrails. If missed, skills become noisy or destructive.
- **OUTPUT SILENCE:** High risk. This is the most frequently violated rule. Moving it further from the action point makes violations more likely.

### Recommendation

**Defer until after /design mode split.** The mode split will test whether Read content is followed as instructions. If it is, this extraction becomes safe. If not, inline duplication is the correct trade-off (reliability > efficiency).

### Effort

- If spike passes: 2-3 hours (extract, replace pointers, test each skill)
- Testing: verify each skill still follows the rules via manual invocation

---

## Implementation Order

| # | Change | Tokens saved | Risk | Effort | Status |
|---|--------|-------------|------|--------|--------|
| 1 | Context-inject silent cache hit | ~4.4K/session | Low | 5 min | **SHIPPED** |
| 2 | /design mode split spike | — (validation only) | None | 1 hr | **SHIPPED** (4/5 passed) |
| 3 | /design mode split | ~14-18K/invocation | Medium | 3 hr | **SHIPPED** |
| 4 | Shared boilerplate extraction | ~3K/session | Medium | 3 hr | **REJECTED** |

Items 1-3 shipped. Item 4 rejected after /explore analysis — see below.

---

## What was evaluated and rejected

These were pressure-tested during the V1 session and rejected:

| Idea | Why rejected |
|------|-------------|
| Context-inject signal quality redesign (assertions, callers, return types) | Test assertions trivial in this codebase. Filtered imports break "import X" pattern. Return types have 0% annotation coverage. |
| Intent-router static pattern trimming | Actual cost only ~500 chars/session (0.08% of context). Deterministic routing has value. |
| Memory file cleanup (delete gstack, perplexity, consolidate feedback) | All 3 proposals wrong: gstack should update not delete, perplexity actively used, feedback files encode distinct failure modes. |
| Review --output flag | 6-9KB savings, simpler dual-output alternative exists, not a pain point yet. |
| Hook consolidation (merge 4 write gates into 1, etc.) | Only ~2.3K chars/session savings. Not worth engineering risk of combining unrelated enforcement logic. |
| Moving platform.md to on-demand | No "read me when X" pointer in auto-loaded rules. Contains 6+ silent-failure prevention rules. The 990 tokens are earned. |
| Shared boilerplate extraction (P3) | Measured only ~120 extractable lines (~3K tokens) — 14x smaller than V1 savings. OUTPUT SILENCE is already the most-violated rule; moving it further from action point worsens adherence. 6/16 Safety Rules blocks have skill-specific prohibitions mixed in and can't be extracted. Spike T3 failure (conditional branching drift) is the exact failure mode extraction would hit. 4-model /explore converged on reject. See `tasks/boilerplate-extraction-explore.md`. |

---

## Summary

V1 shipped ~43K tokens/session in savings (dominated by /start bootstrap). V2 results:
- **Context-inject silent cache:** ~4.4K tokens/session — **SHIPPED**
- **/design mode split:** ~14-18K tokens/invocation — **SHIPPED** (spike passed 4/5, full split deployed)
- **Shared boilerplate:** rejected — ~3K tokens/session was too marginal for the risk

V2 total shipped savings: **~18-22K tokens/session** (cache hit + mode split).
Combined V1+V2: **~61-65K tokens/session**.
