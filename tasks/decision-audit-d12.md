---
decision: D12
original: "Skill rename uses rip-and-replace (no aliases) because solo user means zero backward-compat overhead"
verdict: HOLDS
audit_date: 2026-04-15
models: claude-opus-4-6, gemini-3.1-pro, gpt-5.4
judge: gpt-5.4
accepted_challenges: 0
dismissed_challenges: 2
---

# D12 Audit

## Original Decision

Consolidate 25 skills to 15 with clean renames and merges (no aliases, no compatibility shims). Old skill directories deleted entirely. Renames: define→think, refine→polish, wrap-session→wrap, capture→log, doc-sync→sync. Merges: recall+status→start, review+review-x+qa+governance→check, 4 design skills→design. Challenge gained --deep; plan gained --auto. 12 old directories deleted.

**Date:** 2026-04-11

## Original Rationale

Solo developer, no external users of the skill names. Aliases add maintenance debt and confusing dual-path behavior for zero benefit. Rip-and-replace is the cleanest path when you control all consumers.

## Audit Findings

**Three-model review (claude-opus-4-6, gemini-3.1-pro, gpt-5.4):** Unanimous HOLDS.

Two advisory-only challenges were raised and dismissed by the independent judge:

1. **Temporary migration aid omitted** (Reviewer A) — Dismissed. Labeled minor and not decisive by the reviewer. D14's subsequent 193-reference rename proves the workflow handles rip-and-replace without migration aids.

2. **Future team growth invalidates zero-backward-compat assumption** (Reviewer B) — Dismissed. Forward-looking caveat, not a flaw in D12 as scoped. Any future multi-developer scenario is a new decision, not a retroactive invalidation.

Key reinforcing evidence reviewed:
- Skills are prompt documents (D3), not code modules — no import paths or package registries to break
- lint_skills.py validates all 22 current skills pass; provides ongoing safety net
- D14 (2026-04-11) applied the same pattern at larger scale: 193 cross-references across 39 files, no systemic breakage
- Skill count grew from post-D12 "15" to current 22 organically — the consolidated structure absorbed new skills without friction

## Verdict

**HOLDS**

Rationale is matched to actual system constraints. Aliases would add maintenance surface and mask stale references rather than force their cleanup. The rip-and-replace pattern has been validated empirically by D14.

## Risk Assessment

**Risk of keeping D12:** Low. Linter enforces canonical structure. Rename operations are bounded to the repository. No external blast radius.

**Risk of changing D12:** Medium and unjustified. Reintroducing aliases would: create dual naming paths, complicate lint_skills.py resolution, clutter the / menu, and impose maintenance cost with no user benefit.

**One forward condition to watch:** If BuildOS gains additional developers or is published as a template/framework, the solo-user assumption breaks. That would be a new decision at that time (L27 applies: scope expansion = new proposal).
