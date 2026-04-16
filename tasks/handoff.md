# Handoff — 2026-04-16

## Session Focus
Deep comparison of gstack (Garry Tan) vs BuildOS: full file-by-file inventory, skill-by-skill comparison, then ran /challenge on the analysis. The challenge session accidentally became the best evidence for the slop problem it was trying to analyze.

## Key Insight: The Slop Hierarchy

The central finding from this session — arrived at through both analysis and live demonstration — is that **slop prevention has a hierarchy of effectiveness:**

1. **Deterministic gates (hooks, tests, linters)** — instant, cheap, can't hallucinate. BuildOS's 20 hooks are its real governance story. They fire on every tool call and catch structural violations (env writes, unreviewed commits, protected path edits without plans). These are working and valuable.

2. **Context injection (pre-generation)** — the gap neither framework addresses. Most slop (hallucinated APIs, wrong imports, platform mismatches, regressions) is a context failure: Claude didn't have or didn't read the relevant information. A hook that pre-loads relevant context before code generation would prevent slop at the source. This is the highest-value improvement available.

3. **Multi-model review (post-generation)** — expensive, slow, good for subjective judgment ("is this scope right?"), bad for verifiable claims ("does this file exist?"). debate.py is a real capability but its role should be narrowed to subjective decisions, not fact-checking.

4. **Browser QA (runtime verification)** — gstack's killer feature that BuildOS lacks natively. Tests the actual app in a real browser. Catches runtime bugs that no amount of code review finds.

## What the Challenge Session Proved (Live Evidence)

We ran /challenge on the gstack-vs-buildos comparison proposal. The challenge process itself became a live demonstration of the slop problem:

- **Claude Opus (Challenger A):** 54 tool calls, 125 seconds, hit max turns. Confidently claimed BuildOS hooks don't exist — searched `scripts/` and `skills/` instead of `hooks/`. WRONG. Recommended REJECT based on false evidence.
- **GPT-5.4 (Challenger B):** 8 tool calls, 31 seconds. Same wrong conclusion about hooks. More measured — recommended REVISE instead of REJECT.
- **Gemini 3.1 Pro (Challenger C):** 503 Service Unavailable for 18 minutes through 4 retry attempts. Never responded.
- **GPT-5.4 (Judge):** Accepted the false "hooks don't exist" claim at 0.98 confidence because the tool evidence appeared strong.
- **Total cost:** ~20 minutes wall-clock, ~100K+ tokens, 2 of 5 MATERIAL findings were factually wrong.

The valid findings from the challenge:
1. All quantitative claims (LOC/day, slop rates) were speculative, not measured (TRUE)
2. Multi-model review is opt-in via debate.py, not structural/always-on (TRUE — hooks are always-on, debate is invoked)
3. Better context injection might reduce slop more than post-hoc gates (TRUE — this is the sleeper insight)
4. Trust boundaries for hybrid integration undefined (TRUE but premature — no enterprise users)
5. The proposal framed a narrow integration question as a grand philosophical comparison (FAIR — the real question is "which gstack skills should we also use?")

## Decided This Session

### D-next: Priority roadmap based on comparison findings

**Priority 1: Context injection hook** (HIGH impact, MEDIUM effort)
- PreToolUse:Write|Edit hook that auto-loads relevant context before Claude writes code
- Would inject: file's imports/type signatures, test file, recent git blame, related module files
- Prevents slop at generation time instead of catching it downstream
- This is the highest-value improvement available — the only intervention that reduces slop production rather than catching it after

**Priority 2: Adopt gstack's existing QA/deploy skills** (HIGH impact, LOW effort)
- gstack is already installed at ~/.claude/skills/gstack/ (v0.14.5.0)
- Use /qa after /review (browser-based testing BuildOS completely lacks)
- Use /ship and /land-and-deploy (deploy pipeline BuildOS lacks)
- Use /canary (post-deploy monitoring)
- This is adoption, not integration — no BuildOS code changes needed

**Priority 3: Recalibrate debate.py's role** (MEDIUM impact, LOW effort)
- debate.py is good at subjective judgment, bad at fact-checking
- Consider removing --enable-tools from challenge (54 tool calls produced false confidence)
- Document sweet spot: scope/design/architecture decisions, not verification
- Keep for /challenge and /review on subjective dimensions

**Priority 4: Measure actual slop rates** (MEDIUM impact, MEDIUM effort)
- Run 5 comparable tasks through: (A) no framework, (B) gstack, (C) BuildOS
- Count: escaped defects, rework cycles, time-to-working, lines changed post-review
- Replaces speculation with data

### NOT prioritized (explicitly deprioritized):
- Trust boundary documentation (premature, no enterprise users)
- More debate engine improvements (diminishing returns — hooks do the heavy lifting)
- Deeper gstack code integration (use gstack as-is, don't merge codebases)
- Philosophical framework comparison (done, answer is "they're complementary")

## Full Comparison Summary (Verified)

### gstack (Garry Tan) — 73K GitHub stars
- **32 skills** organized as virtual team roles (CEO, designer, eng manager, QA, release engineer)
- **Core innovation:** Persistent headless Chromium daemon (~100ms/cmd, 58MB compiled binary)
- **Philosophy:** "Boil the Lake" — completeness is cheap with AI, 10K+ LOC/day
- **Governance:** Advisory. Skills are opt-in. No hooks, no hard gates. Trust the builder.
- **Key strengths BuildOS lacks:**
  - /qa (browser-based QA — tests real app, finds bugs, fixes, re-verifies)
  - /land-and-deploy (PR to verified-in-production in one command)
  - /canary (post-deploy monitoring)
  - /benchmark (Core Web Vitals, page load baselines)
  - /design-shotgun + /design-html (mockup generation → production code)
  - /retro (weekly retrospective with per-person breakdowns)
- **Tech:** TypeScript, Bun-compiled binaries, Playwright, MIT license
- **Already installed:** ~/.claude/skills/gstack/ (v0.14.5.0)
- **Currently used by BuildOS:** Only 3 skills — /browse, /connect-chrome, /setup-browser-cookies (via scripts/browse.sh wrapper)

### BuildOS — This project
- **22 skills** + **20 always-on hooks** + cross-model debate engine
- **Core innovation:** Adversarial challenge gate + hook-enforced governance
- **Philosophy:** "Simplicity is the override rule." Challenge before planning, plan before building.
- **Governance:** Structural. 20 hooks fire on every tool call. Protected paths require plan artifacts.
- **Key strengths gstack lacks:**
  - 20 always-on hooks (deterministic, can't hallucinate, instant)
  - /challenge gate ("should we build this at all?")
  - Session continuity (/start → work → /wrap with handoff/session-log/current-state)
  - Enforcement ladder (lesson → rule → hook → architecture, 3-strikes promotion)
  - Protected path system (config-driven, requires plan artifacts)
  - Natural language routing (hook-intent-router.py maps intent to skills)
  - /research (Perplexity Sonar integration)
  - /healthcheck (governance system self-audit)
- **Key correction from challenge:** Multi-model review (debate.py) is opt-in, not always-on. The hooks are structural; the debate is a capability.

### Where they overlap (same problem, different approach)
| Capability | gstack | BuildOS |
|---|---|---|
| Problem discovery | /office-hours | /think discover |
| Scope review | /plan-ceo-review | /elevate |
| Code review | /review (single model, auto-fix) | /review (3 models via debate.py) |
| Investigation | /investigate (4 phases, auto-freeze) | /investigate (3 modes) |
| Doc sync | /document-release | /sync |
| Learning | /learn (learnings.jsonl) | /log + lessons.md |
| Safety | Opt-in /careful + /freeze | Always-on 20 hooks |
| Design | 4 dedicated skills + browser | 4 modes in 1 skill (text-based) |

## NOT Finished
- None of the 4 priorities have been started — this session was analysis only
- Conviction gate scripts archived to archive/conviction-gate/ (in progress per git status)
- debate-log.jsonl modified (new challenge/judge entries from this session)

## Artifacts Created This Session
- `tasks/gstack-vs-buildos-proposal.md` — Full comparison proposal with slop analysis
- `tasks/gstack-vs-buildos-findings.md` — Raw challenger output (2/3 models, Gemini 503'd)
- `tasks/gstack-vs-buildos-judgment.md` — Independent judge evaluation (4 ACCEPTED, 1 ESCALATED)
- `tasks/gstack-vs-buildos-challenge.md` — Synthesized challenge result (PROCEED-WITH-FIXES)

## Key Files to Read
- `tasks/gstack-vs-buildos-challenge.md` — The synthesized result with corrected findings
- `tasks/gstack-vs-buildos-proposal.md` — The full comparison (read with corrections from challenge)
- `~/.claude/skills/gstack/ARCHITECTURE.md` — gstack's technical design (if building integrations)
- `~/.claude/skills/gstack/ETHOS.md` — gstack's builder philosophy

## Next Session Should
1. **Start with Priority 1:** Design the context injection hook (PreToolUse:Write|Edit that auto-loads relevant context). This is the highest-value improvement. Run through /think refine → /challenge → /plan → build pipeline.
2. **Or start with Priority 2:** Just start using /qa after /review in the next real build task. Zero effort, immediate value. No BuildOS changes needed.
3. Read this handoff + the challenge artifact before planning anything.

## Lessons for lessons.md
- L-next: debate.py challengers with --enable-tools can produce false verification claims with high confidence (54 tool calls, wrong conclusion, judge accepted at 0.98). Deterministic checks (grep, test, hook) beat probabilistic review for verifiable claims.
- L-next: Gemini 3.1 Pro 503 outages cause debate.py to block for 15-18 minutes due to per-attempt timeouts × 4 retries. Consider adding a total wall-clock timeout or faster fallback.
- L-next: The most valuable output of a challenge session may not be the findings but what the process itself demonstrates about failure modes.
