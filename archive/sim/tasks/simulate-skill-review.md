---
topic: simulate-skill
review_tier: cross-model
status: revise
git_head: e44d3af
producer: claude-opus-4-6
created_at: 2026-04-15T03:00:00-07:00
scope: .claude/skills/simulate/SKILL.md,.claude/skills/elevate/SKILL.md,CLAUDE.md,hooks/hook-intent-router.py,.claude/rules/natural-language-routing.md
findings_count: 7
spec_compliance: false
---

## PM / Acceptance
- [ADVISORY] P-1: Scope is well-sized — two modes, clean integration, skill count correct (22)
- [ADVISORY] P-2: Elevate mktemp fix is a legitimate bug fix, not scope creep
- [ADVISORY] P-3: Quoted filler string check uses "or similar" — non-deterministic but acceptable for LLM procedure
- [ADVISORY] P-4: Risk of NOT shipping — 22 skills remain untestable without this
- [ADVISORY] P-5: High INCONCLUSIVE rate likely for smoke-test on stateful skills (Gemini)
- [ADVISORY] P-6: Artifact files (tasks/<target>-simulate.md) slightly weaken "zero-config" promise (GPT)

## Security
- [MATERIAL] S-1: Denylist incomplete — missing `eval`, `source`, `pip install`, `npm install`, `curl -o` to non-tmp, `tee`, `dd` (all 3 models)
- [MATERIAL] S-2: Env scrub misses `DATABASE_URL`, `*_DSN`, credential-bearing URLs (Claude + Gemini)
- [MATERIAL] S-3: Quality-eval passes target SKILL.md verbatim as instructions to inner agent without safety constraints — contradicts "treat as untrusted" (Claude)
- [ADVISORY] S-4: Env scrub is helpful but can't prevent file-based secret access (GPT)

## Architecture
- [MATERIAL] A-1: Hardcoded absolute path `/Users/macmini/claude-build-os` — non-portable (all 3 models)
- [MATERIAL] A-2: Shell quoting vulnerability — `bash -c '<COMMAND>'` breaks if command contains single quotes (Gemini)
- [MATERIAL] A-3: `mktemp /tmp/simulate-scenario-XXXXXX.md` — BSD mktemp requires template to end in X; .md suffix may fail (Gemini)
- [MATERIAL] A-4: Intent router regex `smoke.?test` too broad — could false-positive on non-skill contexts (Claude)
- [ADVISORY] A-5: No test coverage for new intent router pattern (Claude + GPT)
- [ADVISORY] A-6: Quality-eval agent-in-agent architecture is fragile at recursion boundaries (Claude)
- [ADVISORY] A-7: Two modes with different safety models in one skill file — maintenance risk (GPT)

## Cross-Model Consensus

### Consensus (all 3 models agree)
1. **Hardcoded path** (A-1) — all 3 flagged as MATERIAL
2. **Incomplete denylist** (S-1) — Claude and GPT as MATERIAL, Gemini as MATERIAL (phrased differently)
3. **Scope is correct** — all 3 agree the feature is valuable and well-scoped

### High-confidence (2/3 agree)
4. **Env scrub gaps** (S-2) — Claude + Gemini
5. **Shell quoting** (A-2) — Gemini only, but structurally correct
6. **mktemp BSD** (A-3) — Gemini only, but factually verifiable

## Summary

7 MATERIAL findings, 9 ADVISORY. Must-fix before commit:
1. Replace hardcoded path with dynamic project root detection
2. Expand denylist (eval, source, pip/npm install, curl -o, tee, dd)
3. Expand env scrub pattern (DATABASE_URL, *_DSN, credential URLs)
4. Add safety constraints to quality-eval inner agent prompt
5. Fix shell quoting (write to file, not bash -c with single quotes)
6. Fix mktemp template (BSD requires ending in X)
7. Tighten intent router regex (scope to skill context)
