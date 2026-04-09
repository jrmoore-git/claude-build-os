---
debate_id: build-os-gaps3
created: 2026-03-13T17:17:47-0700
mapping:
  A: gpt-5.4
  B: gemini-3.1-pro
---
# build-os-gaps3 — Challenger Reviews

## Challenger A — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL]: The proposal assumes `.claude/commands/*.md` is still stable enough to deliberately model, even while explicitly calling it “legacy” and acknowledging SKILL.md as the current standard. That is internally inconsistent. “Still works” is not a strong architectural criterion for a framework repo that claims to teach durable patterns. The unconsidered alternative is to migrate at least one command end-to-end to SKILL.md as the canonical example while perhaps keeping legacy examples for minimal tiers. The failure mode is teaching users a format that Anthropic de-emphasizes, forcing downstream migration and undermining the repo’s “feature currency” goal. This is under-engineered on future compatibility and over-engineered on preserving current repo layout convenience.

2. [RISK] [MATERIAL]: Group C adds many platform-specific details that are likely to drift quickly: hook types/events, session commands, auto memory semantics, skills metadata, subagent capabilities. The proposal recognizes maintenance burden but responds mostly by asserting the detail level is “right.” That is not a mitigation plan. The alternative not considered is a versioned compatibility matrix or a single “platform features snapshot” page with last-verified dates and explicit links-out, rather than scattering details across Parts III, VIII, X, examples, and the Team Playbook. The failure mode is partial staleness: some pages get updated, others lag, and the framework becomes less trustworthy precisely because it mixes timeless principles with unstable product specifics.

3. [UNDER-ENGINEERED] [MATERIAL]: The proposal says Fix C1 clarifies that CLAUDE.md and rules are advisory, but it does not actually commit to removing or revising existing “HARD RULE” phrasing in the templates and examples that created the contradiction. That is a direct gap. If the current repo language overstates enforceability, adding one explanatory paragraph elsewhere does not solve the user-facing inconsistency. The alternative is to update all normative wording in CLAUDE.md templates, command text, and rule examples so enforcement claims match reality. The failure mode is that users continue copying misleading language, and the repo still teaches the wrong mental model despite the new caveat.

4. [ALTERNATIVE] [MATERIAL]: For the missing `.claude/rules/` examples, the proposal chooses two small illustrative files, but it does not consider whether a single paired example set would better teach the core distinction: advisory rule vs enforced hook for the same policy. Since the repo’s unique value is the enforcement ladder, splitting examples into “security” and “code-quality” may optimize topical coverage at the expense of conceptual clarity. A stronger alternative would be a minimal “same rule, three enforcement levels” example. The failure mode is that users see path matchers and rule syntax but still miss when to escalate from rules to hooks.

5. [OVER-ENGINEERED] [ADVISORY]: Twelve fixes across multiple docs, examples, commands, and bootstrap flows is a lot for what is partly a currency refresh. The claim that groups are independent is only partly true; several depend on shared terminology and cross-links remaining consistent. A leaner alternative would be to do bootstrap integrity plus one consolidated platform-features page first, then expand examples in a second pass. The current plan risks creating cross-reference churn and review overhead disproportionate to the immediate repo audit findings.

6. [UNDER-ENGINEERED] [ADVISORY]: The session-log template is presented as a missing artifact, but the proposal only adds a 15-line template without addressing lifecycle: when it should be created, who updates it, how it relates to handoff, and whether it is superseded by native session management or auto memory. The alternative not considered is documenting decision criteria for using session-log vs handoff vs memory. The failure mode is yet another artifact users half-adopt, increasing process clutter rather than improving continuity.

7. [ASSUMPTION] [ADVISORY]: The proposal repeatedly leans on claims like “nobody else has published a framework” and “Build OS is the only thing that teaches why and when.” Even if directionally true, those claims are not necessary to justify the fixes and are not substantiated in a way that matters architecturally. The failure mode is rhetorical overreach: it biases decisions toward preserving uniqueness rather than adopting the strongest current patterns from the ecosystem.

## Concessions
- It correctly identifies a real contradiction between advisory guidance and enforced controls, and ties that to the existing enforcement ladder.
- It prioritizes concrete repo integrity issues first: broken bootstrap, unwired commands, missing examples.
- It avoids dumping full reference docs into the repo and generally tries to link out for exhaustive platform details.

## Verdict
REVISE — the proposal fixes real gaps, but it underestimates documentation drift risk, does not fully resolve the advisory/enforcement contradiction in copied artifacts, and makes a weak case for retaining legacy command format as the modeled default.

---

## Challenger B — Challenges
## Challenges

1. [ALTERNATIVE] [MATERIAL]: Refusal to adopt the `SKILL.md` standard. The proposal explicitly admits that `.claude/commands/` is a legacy format and `SKILL.md` is the current standard, yet it chooses to teach the legacy format to avoid "directory-per-command overhead" (Fix A1 / Fix C2). A reference framework cannot knowingly teach legacy patterns as its default foundation. If the directory overhead is high, the framework's tooling (like the `/setup` command) should generate it, rather than forcing users to learn a deprecated pattern only to migrate later. 

2. [UNDER-ENGINEERED] [MATERIAL]: Contradictory "HARD RULE" language left in templates. Fix C1 accurately notes that `CLAUDE.md` and rules are advisory and compliance drops at scale. However, the proposal explicitly questions (in the evaluation section) whether to update the templates themselves, effectively leaving "HARD RULE" language in the artifacts. Burying the "rules are advisory" truth in Part III documentation while shipping templates that scream "HARD RULE" creates severe cognitive dissonance. The templates must be refactored to match the documentation.

3. [ASSUMPTION] [MATERIAL]: Unverified harmony between native Auto Memory and framework files. Fix C1 states that Claude's native `MEMORY.md` "complements your disk-based files (decisions.md, lessons.md)." This assumes the LLM won't duplicate context by writing to both, or get confused by conflicting directives. The proposal provides no mechanism, rule, or instruction to prevent native auto-memory from cannibalizing or contradicting the Build OS's manual disk-based files, risking massive context bloat.

## Concessions
1. Adding `examples/rules/` with `paths:` frontmatter perfectly bridges the gap between abstract concepts and practical, context-saving implementation.
2. Clarifying the enforcement ladder (rules are advisory, hooks are laws) is a vital architectural distinction that elevates this above standard "kitchen sink" repos.
3. Intentionally omitting highly experimental features (plugins, agent teams) is a smart move that protects the framework's stability.

## Verdict
REVISE because knowingly teaching a legacy command format and failing to strip contradictory "HARD RULE" language from the templates undermines the repo's authority as a best-practice framework.

---
