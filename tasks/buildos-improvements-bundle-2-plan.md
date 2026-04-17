---
scope: "Hygiene bundle: #5 strip Essential Eight strike-throughs from CLAUDE.md, #6 promote anti-slop enforcement from rule to hook with evidence-based word list, #4 add tier-install validation test."
surfaces_affected: "CLAUDE.md, .claude/rules/code-quality.md, hooks/pre-commit-banned-terms.sh, tests/test_setup_tier_install.py"
verification_commands: "python3.11 -m pytest tests/test_setup_tier_install.py -v; python3.11 -m pytest tests/ -k 'not integration' -q; ! grep -q '~~' CLAUDE.md; bash hooks/pre-commit-banned-terms.sh"
rollback: "git revert per commit (3 independent commits: A, B, C)"
review_tier: "Tier 2"
verification_evidence: "PENDING"
allowed_paths:
  - CLAUDE.md
  - .claude/rules/code-quality.md
  - hooks/pre-commit-banned-terms.sh
  - tests/test_setup_tier_install.py
  - tasks/buildos-improvements-bundle-2-plan.md
  - tasks/buildos-improvements-*.md
  - tasks/llm-slop-vocabulary-research.md
  - tasks/session-log.md
  - tasks/handoff.md
  - docs/current-state.md
components:
  - Essential Eight line rewrite
  - Anti-slop hook promotion with evidence-based list
  - Tier-install validation test
challenge_skipped: true
challenge_skip_reason: "Parent challenge at tasks/buildos-improvements-challenge.md cleared #4/#5/#6 as dismissed advisories. Research via Perplexity (tasks/llm-slop-vocabulary-research.md) informed the revised #6 list. #5 and #4 are doc/test-only; #6 promotes enforcement up the ladder (CLAUDE.md rule → hook)."
parent_proposal: tasks/buildos-improvements-proposal.md
parent_challenge: tasks/buildos-improvements-challenge.md
research_citation: tasks/llm-slop-vocabulary-research.md
---

# BuildOS Improvements — Bundle 2 (Hygiene)

Shipped after bundle-1 (commits 4ba6912, 62e317b, 6a3fb0b, e60e35b) and the separate foundational llm_client fix (750fe9b).

## Components

### A — Essential Eight rewrite (#5)

**File:** `CLAUDE.md` (~3 line text edit)

Replace the line with strike-throughs:
```
**Essential eight invariants (6 of 8 apply to BuildOS):** idempotency · ~~approval gating~~ · audit completeness · degraded mode visible · ~~state machine validation~~ · rollback path exists · version pinning enforced · ~~exactly-once scheduling~~. Struck-through invariants require a downstream outbox (not present in BuildOS).
```
With:
```
**Five invariants apply to BuildOS:** idempotency · audit completeness · degraded mode visible · rollback path exists · version pinning enforced. (Approval gating, state-machine validation, and exactly-once scheduling apply to downstream projects with an outbox — not to BuildOS itself. Downstream CLAUDE.md files should add them when relevant.)
```

**Rationale:** struck-through text in a load-bearing doc is text pollution. The removed items aren't "N/A for BuildOS" — they're for a different architecture layer entirely, and that belongs in downstream projects' own CLAUDE.md, not as dead text here.

### B — Anti-slop hook promotion (#6)

**Files:**
- `.claude/rules/code-quality.md` (tighten list)
- `hooks/pre-commit-banned-terms.sh` (add SLOP_PATTERN + phrase check)

**Evidence source:** Perplexity research at `tasks/llm-slop-vocabulary-research.md` (8 sources including Pangram, Grammarly, Futurism's 14M biomedical abstracts analysis).

**Tier A — strict ban (hook-enforced, 10 words):**
```
delve · cutting-edge · state-of-the-art · seamless · innovative · synergy · paradigm · holistic · empower · transformative
```
First 5 have direct research evidence; last 5 are editorial-judgment marketing-empty.

**Tier B — phrase ban (hook-enforced, 2 phrases):**
```
"a testament to" · "at its core"
```

**Dropped from list (false-positive risk > slop signal):**
```
robust · comprehensive · nuanced · crucial · leverage · facilitate · utilize · streamline
```
These have legitimate technical use (`robust under concurrent writes`, `comprehensive test coverage`). Keeping them triggers false positives without meaningfully catching slop.

**Hook changes:**
1. Add new variable `SLOP_PATTERN='delve|cutting-edge|state-of-the-art|seamless|innovative|synergy|paradigm|holistic|empower|transformative'`. Case-insensitive via existing `grep -inE`.
2. Add phrase pattern `SLOP_PHRASES='a testament to|at its core'` — separate variable because phrase matching needs word-boundary handling different from the single-word pattern.
3. Add SKIP_PATTERNS entries for `.claude/rules/code-quality.md` (documents the list) and `tasks/llm-slop-vocabulary-research.md` (research doc with the words as data) — though tasks/* is already covered.
4. When SLOP_PATTERN matches: emit the same BLOCKED output as BANNED_PATTERN but with a different header ("AI slop markers") and a different exit code? No — same exit 1. The fix path is the same: rewrite.

**Rule changes:**
1. Replace the current `## Anti-Slop Vocabulary` section in `.claude/rules/code-quality.md` with a tightened list + note that enforcement lives in `hooks/pre-commit-banned-terms.sh`. Cite the research doc.
2. Remove the dropped words from the prose entirely (don't list them as "avoid when possible" — that's advisory-land we're moving away from).

### C — Tier-install validation test (#4)

**File:** `tests/test_setup_tier_install.py` (new, ~60 lines)

**What it does:** parses `.claude/skills/setup/SKILL.md` Step 3, extracts the per-tier file lists, validates that (a) every file declared for a tier has a corresponding template in `templates/`, (b) every file in `templates/` is declared for at least one tier or explicitly excluded.

**Why:** the setup skill IS already tier-aware — this catches drift when someone adds a template without wiring it into the tier logic (or vice versa). Addresses the parent challenge's Challenge 9 advisory ("no test coverage for tier-install").

**Test structure:**
```python
def test_tier0_files_exist_in_templates(): ...  # Tier 0 declared files all exist
def test_tier1_files_exist_in_templates(): ...  # Tier 1 declared files all exist
def test_no_orphan_templates(): ...             # every templates/*.md is tier-assigned
def test_skill_has_tier_sections(): ...         # structural: Step 3 has ### Tier 0, ### Tier 1 headings
```

Does NOT modify the setup skill or templates. Purely a drift-detection test.

## Execution Strategy

**Decision:** sequential (main session)
**Pattern:** linear — A → B → C, each its own commit
**Reason:** Zero file overlap between components but total scope is <100 lines net. Worktree overhead exceeds savings.

| Subtask | Files | Depends On | Isolation |
|---|---|---|---|
| A | CLAUDE.md | — | main session |
| B | .claude/rules/code-quality.md, hooks/pre-commit-banned-terms.sh | — | main session |
| C | tests/test_setup_tier_install.py | — | main session |

**Synthesis:** run verification after each commit. All three commits should land cleanly without needing reconciliation.

## Verification

### After A
- `! grep -q '~~' CLAUDE.md` (no strike-throughs)
- `grep -c 'Five invariants apply' CLAUDE.md` returns 1

### After B
- `grep -c 'SLOP_PATTERN' hooks/pre-commit-banned-terms.sh` returns at least 1
- `grep -q 'delve' hooks/pre-commit-banned-terms.sh` (pattern defined)
- `bash hooks/pre-commit-banned-terms.sh` exits 0 (no staged violations after skip-patterns apply)
- Smoke test: `echo 'We built a seamless paradigm' > /tmp/slop-test.md && git add -f /tmp/slop-test.md 2>/dev/null; bash hooks/pre-commit-banned-terms.sh` should BLOCK — then unstage.
- `grep -c 'delve\|cutting-edge\|state-of-the-art' .claude/rules/code-quality.md` returns 3+ (new list present)
- `! grep -qE '\brobust\b.*\bcomprehensive\b.*\bnuanced\b' .claude/rules/code-quality.md` (old list removed)

### After C
- `python3.11 -m pytest tests/test_setup_tier_install.py -v` → all pass
- Full suite: `python3.11 -m pytest tests/ -k 'not integration' -q` → 957+ tests pass (953 + ~4 new)

## Non-goals

- Do not modify `.claude/skills/setup/SKILL.md` logic (it's already tier-aware)
- Do not delete `hooks/pre-commit-banned-terms.sh` (it also blocks API-key prefixes — separate concern)
- Do not add linting to generated LLM output (out of scope; the hook catches pre-commit)
- Do not change the downstream project invariants that the struck-through items addressed — those belong in downstream CLAUDE.md files

## Rollback

Each commit independent:
- Revert A → CLAUDE.md restores strike-throughs; no other file affected
- Revert B → rule text + hook both revert in one commit
- Revert C → test file deleted; no runtime impact
