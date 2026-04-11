# Handoff — 2026-04-10

## Session Focus
Evaluated gstack (Garry Tan's Claude Code framework) vs BuildOS. Identified browser suite as the high-value complement — not the skills (mostly duplicates or weaker than ours).

## Decided
- gstack's browser suite is the main thing worth leveraging — `/browse`, `/setup-browser-cookies`, `/qa`, `/qa-only`, `/benchmark`, `/canary`, `/connect-chrome`
- No skill conflicts for browser skills (no BuildOS name collisions)
- BuildOS keeps its own versions of overlapping skills (`/review`, `/ship`, `/autoplan`, `/design-*`, `/doc-sync`) — ours are stronger (cross-model debate, hook enforcement)
- For Jarvis: browser value is authenticated web browsing for meeting prep, deal research, article extraction. Four prerequisites from web-search-tooling debate must close first.
- For BuildOS: browser value is web app QA testing, perf benchmarks, post-deploy canary, design review

## Current State of gstack Install
- gstack cloned at `~/.claude/skills/gstack/` — version 0.14.5.0 (current upstream: 0.16.3.0)
- Browse + design binaries built and executable (~58MB each)
- `BROWSE_CLI` and `DESIGN_CLI` env vars set in ~/.zshrc
- Browse daemon running (PID 68623, since Apr 2)
- **Missing: `scripts/browse.sh`** — wrapper needed by `/design-review` and `/design-consultation`

## NOT Finished (carried over + new)
- **Update gstack 0.14.5.0 → 0.16.3.0** — gets browser data platform (`scrape`, `data`, `media`, network interception)
- **Create `scripts/browse.sh`** — thin wrapper around `$BROWSE_CLI`, fixes two broken skills
- **Jarvis browser prerequisites** (scope in Jarvis project, not here): prompt injection mitigations, audit logging, outbound query policy, web_search.py spike closure
- deploy_all.sh customization for BuildOS (carried over)
- Audit findings 11-13 (carried over)
- `/define discover` live test (carried over)

## Next Session Should
1. Read this handoff + the gstack evaluation context below
2. Update gstack to 0.16.3.0 and create `scripts/browse.sh`
3. Test `/browse` and `/qa` on a real target to verify the suite works end-to-end
4. Then pick up carried-over items (deploy_all.sh, /define discover test)

## gstack Evaluation Summary (for next session context)
- gstack = 30 skills + headless browser daemon. 69K GitHub stars. MIT licensed.
- 8 skills duplicate BuildOS (we're stronger on all 8). ~20 are complementary.
- Browser suite = the real value. 50+ commands, ~100ms/call, persistent Chromium, cookie import, network interception.
- gstack shipped 35 commits last week: browser data platform (v0.16), security hardening (22 fixes), multi-host platform, adaptive review gating.
- BuildOS advantages: hook enforcement, cross-model adversarial debate, graduated pipeline tiers, lesson promotion. These don't exist in gstack.
- Architecture difference: gstack trusts prompts, BuildOS trusts hooks. Complementary, not competing.

## Key Files
scripts/setup-design-tools.sh (gstack installer)
~/.claude/skills/gstack/ (gstack install dir)
.claude/skills/design-shotgun/SKILL.md (uses $DESIGN_CLI, $BROWSE_CLI)
.claude/skills/design-review/SKILL.md (references missing scripts/browse.sh)
.claude/skills/design-consultation/SKILL.md (references missing scripts/browse.sh)
