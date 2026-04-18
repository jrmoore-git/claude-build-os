---
topic: debate-arm-comparison
type: scope-expansion-addendum
parent: tasks/debate-arm-comparison-design-refined.md
created: 2026-04-18
status: DRAFT — addendum for new session to expand per-skill before execution
---

# Scope Expansion — 4-Skill Comparison

## Approved by user (2026-04-18, this session)

Original design covers `/challenge` only. Approved expansion: test **all four multi-model skills**, not just `/challenge`. Each skill gets its own arm-B'-fair vs arm-D-production comparison.

## Per-skill arm definitions — to finalize in new session

| Skill | Current multi-model form (arm D) | B'-fair form (all-Claude) | Sample |
|---|---|---|---|
| `/challenge` | 4-persona cross-family + gpt-5.4 judge | 4 Claude persona calls + Claude consolidate | 10 proposals per main design |
| `/refine` | 6 rounds rotating gemini-3.1-pro → gpt-5.4 → claude-opus | 6 rounds all Claude Opus (same prompts, same seed, same rotation mechanic) | 5 refines from log with full history |
| `/review` | 3 cross-family persona reviewers (architect + security + pm on claude-opus + gpt-5.4 + gemini-3.1-pro) | 3 Claude Opus reviewers (same personas, same prompts) | 5 review runs with downstream outcomes |
| `/pressure-test` | Multi-model mode (3 models + synthesis model) | Single Claude Opus + same synthesis prompt | 5 pressure-test runs |

`/think` excluded per D5 (already validated as single-model by design).

## What the new session needs to produce before execution

1. **Per-skill arm-B'-fair config** — each skill needs its own all-Claude config or CLI path. May require parallel `--config` flag work per subcommand.
2. **Sample selection per skill** — 5 runs per non-`/challenge` skill from `stores/debate-log.jsonl` with rich outcome evidence. Same selection criteria as main design: outcome clarity + type diversity + arm-independent downstream signal.
3. **Outcome extraction for non-`/challenge` runs** — fresh-session extraction per run, same methodology as main design's Phase 1.
4. **Per-skill 7-dimension rubric** — the 7 impact dimensions apply across skills with minor wording adjustments (e.g., `/refine` dim #2 is "nuance caught across rounds" not "nuance caught across personas"). Small-effort customization per skill.
5. **Cross-skill aggregation plan** — after per-skill verdicts, answer: does multi-model win uniformly, split by skill, or flip? If split, produce per-skill routing rules (e.g., "keep cross-family for /challenge, drop for /refine").

## Sanity-check pair (true-Claude-Code-session test)

For the `/challenge` skill's secondary sanity check (true Claude Code session spawning persona subagents via Agent tool vs primary B'-fair via `debate.py` all-Claude config), the 2-proposal pair is:
- **sim-generalization** (REVERSED outcome per D22, highest-signal case)
- **buildos-improvements** (SHIPPED-AS-2-BUNDLES per D26, different outcome class)

## 10 retrospective proposals for the /challenge arm (confirmed)

Ranked by outcome clarity + evidence richness + type diversity:

| # | Topic | Type | Outcome | Decision |
|---|---|---|---|---|
| 1 | explore-intake | Architecture/workflow | SHIPPED-REVISED | D11 |
| 2 | litellm-fallback | Code/infra | REJECTED (pre-shipped at 37440d9) | (frame) |
| 3 | autobuild | Governance | SHELVED | (no ship) |
| 4 | sim-generalization | Research/methodology | REVERSED | D22 |
| 5 | buildos-improvements | Multi-track | SHIPPED-AS-2-BUNDLES | D26 |
| 6 | refine-critique-mode | Architecture/skill | SHIPPED | D17 |
| 7 | debate-common | Code refactor | SHIPPED | D25 |
| 8 | read-before-edit-hook | Hook/architecture | SHIPPED | (hook shipped) |
| 9 | managed-agents-dispatch | Architecture | UNKNOWN — verify before execution | — |
| 10 | learning-velocity | Governance/telemetry | SHIPPED-DESCOPED | D22 + D26 + L34 |

Plus negative control: `negative-control-verbose-flag` as 11th-slot check (both arms must flag the deliberately-bad proposal). User decision: **replace** pattern — keeps n=10 clean, negative-control used only as a verification not a data point.

## Dropped from earlier picks (rationale)

- `streamline-rules` — atomization-pathological governance proposal
- `review-lens-linkage-design` — this-session recent work, contamination risk
- `model-routing-design`, `explore-redesign-proposal`, `multi-model-skills-roi-audit-design`, `judge-stage-frame-reach-audit-proposal` — design docs only, no full pipeline history, weaker test cases

## Efficiency gate — BEFORE execution

Per D34, the new session must complete this sequence BEFORE running any study runs:

1. **Verify prompt caching quality-neutral** (Anthropic docs confirm byte-exact cache; model sees identical input). Zero quality risk.
2. **Implement prompt caching** in `scripts/debate.py` / `scripts/llm_client.py`. Likely targets: shared persona prompts + proposal text + tool definitions (cached across personas) + conversation history (cached within persona's tool-use turns).
3. **Measure caching savings** on 3-5 test runs. Expected: ~60-70% input-token reduction. Confirm empirically.
4. **Ship caching** if savings verify. If not, investigate implementation before study starts.
5. **THEN** run the 4-skill comparison study.

Deferred efficiency ideas (quality risk — NOT for this session):
- Per-persona model reassignment (e.g., PM → Sonnet): quality risk, needs its own study
- Tool-call budget caps: quality risk, could terminate verification prematurely
- Batch API for retrospective runs: zero quality risk but latency cost; consider after caching

## Budget estimate (post-caching)

At expected $0.60/call post-caching:
- 10 proposals × 2 arms × `/challenge` = 20 runs = $12
- 5 runs × 2 arms × `/refine` (at ~$0.15/round × 6 rounds post-cache) = $9
- 5 runs × 2 arms × `/review` (at ~$0.20/call × 3 personas) = $6
- 5 runs × 2 arms × `/pressure-test` (at ~$0.30/call × 3 models + synth) = $12
- Variance reruns (3 proposals × 2 arms × 2 reps × all 4 skills, sampled): $15
- Judge scoring (210 scorings × 3 judges × $0.05 post-cache) = ~$30
- Outcome extraction (30 extractions × cheap model): $5
- Normalization (~$3 post-cache)
- Contingency: $15

**Total estimate: ~$105 post-caching** (down from ~$250-350 at current rates).
