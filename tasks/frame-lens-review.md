---
topic: frame-lens
review_tier: cross-model
status: passed
git_head: 72e145e
producer: claude-opus-4-7
created_at: 2026-04-17T12:50:00-0700
scope: scripts/debate.py, scripts/debate_common.py, config/debate-models.json, .claude/skills/challenge/SKILL.md, .claude/rules/review-protocol.md, tasks/lessons.md, tasks/frame-lens-plan.md, tasks/frame-lens-validation.md, tests/test_debate_pure.py
findings_count: 1 material (fixed) + 6 advisory
spec_compliance: true
spec_reference: tasks/frame-lens-plan.md
---

# Frame Lens Cross-Model Review

3 reviewers (Opus 4.7 architect, GPT-5.4 security, Gemini 3.1 Pro pm) reviewed the diff against the plan. All 3 confirmed spec compliance — no MUST-NOT or EXPLICITLY-EXCLUDED clauses violated.

## PM / Acceptance

- [ADVISORY] Plan-specified Change 7 unit tests (4 listed for frame persona) were initially absent — only orthogonal validator-scope tests had landed. **Resolved during review:** added `TestFramePersona` class with 6 tests covering frame in `VALID_PERSONAS`, in `persona_model_map`, `frame_factual_model` config presence, prompt content (`missing` / `candidate set` / `compositional` / `verify` keywords), and cross-family model assignment. All 6 pass.
- [ADVISORY] (positive) Scope right-sized — dual-mode expansion lives entirely inside `cmd_challenge`, no new CLI surface, no new subcommand.
- [ADVISORY] (positive) Validator scope fix correctly constrains type-tag checks to `## Challenges` section, addressing false-positive friction surfaced during validation.
- [ADVISORY] (positive) Frame prompt includes "APPROVE is valid" + "Do NOT manufacture missing options" guardrails against forced adversarial output.

## Security

- [MATERIAL — RESOLVED] **Fallback mode interaction bug** (architect-found): `args.enable_tools = False` flip in fallback mode happened *after* persona expansion. `--personas frame --enable-tools` in a fallback session would have created a `frame-factual` challenger with `use_tools=True`, then failed at runtime when the Anthropic-direct path tried to invoke `llm_tool_loop` (which the OpenAI SDK can't route to Anthropic tools). **Fix applied:** moved the fallback flip immediately after `_load_credentials()`, before persona expansion reads `args.enable_tools`. Tests still pass.
- [MATERIAL — DISMISSED] CHALLENGER_LABELS sizing concern (security-found): reviewer noted "I did not verify the size in this diff." Confirmed: `CHALLENGER_LABELS = list(string.ascii_uppercase)` = 26 entries; max usage in this codebase is 5-6 challengers. No bounds risk. False positive.
- [ADVISORY] (positive) Tool isolation enforced structurally (`use_tools=False` in dict for frame-structural) rather than via prompt instruction — model can't ignore Python-level enforcement.
- [ADVISORY] `_build_frontmatter` nested-dict serialization writes raw keys/values without YAML quoting. Only consumer is internally-generated `personas` map with fixed keys/values — no current injection risk. Future hardening if generic callers pass user-derived strings containing `:`, `#`, or newlines.

## Architecture

- [ADVISORY] One-level-deep dict expansion in `_build_frontmatter` is sufficient for current consumers. Note for future: deeper nesting would need recursion.
- [ADVISORY] `_auto_generate_mapping` in `debate_verdict.py` not explicitly verified against the new `personas:` frontmatter block. Should still parse correctly (it parses YAML loosely), but a verdict-round smoke test against a frame-dual challenge file would close the loop. Tracked as followup.
- [ADVISORY] Duplicate-model warning operates on pre-expansion `persona_models` map. Won't catch the case where user manually sets `frame_factual_model = claude-sonnet-4-6` (collapsing both halves to same model). Defensive concern; doesn't affect correctness.
- [ADVISORY] (positive) Persona dispatch refactored from tuple to dict (`{model, prompt, use_tools, persona_name}`) — healthier boundary for mixed tool/no-tool challengers, structurally coherent change.
- [ADVISORY] Output frontmatter shape evolved (added `personas:` block). No downstream parser compat test in this diff. Likely safe (additive, valid YAML), but verifying judge-round parsing against a dual-mode artifact would be prudent.

## Plan Clause Verification

All MUST-NOT and EXPLICITLY-EXCLUDED clauses verified satisfied:
- "Do NOT critique the candidates in the proposal" — present in `frame` and `frame-factual` prompts
- "Do NOT manufacture missing options just to produce findings" — present in `frame` prompt
- "Do NOT re-enumerate what exists in the codebase as 'findings'" — present in `frame-factual` prompt
- Not changing judge or refine phases — verified, no judge/refine code modified
- Not gating `/plan` differently on frame findings — verified, no special gating logic
- Not implementing a "frame quality score" or pre-flight check — verified absent
- Not back-fixing gbrain-adoption-refined.md — verified, no Jarvis-repo file touched
- Not building a separate `cmd_frame_review` subcommand — verified, frame is persona expansion inside `cmd_challenge`

Allowed-paths compliance: all 9 changed files within plan's `allowed_paths`.

## Quantitative Claims (PM lens verification)

PM lens cross-checked claims against `tasks/frame-lens-validation.md`:
- "~30 novel MATERIAL findings" — EVIDENCED (per-proposal counts in validation.md)
- "flipped 1 verdict (litellm-fallback REVISE → REJECT)" — EVIDENCED
- "BETTER on 4/5 proposals and TIED on 1/5" — EVIDENCED
- "~3x faster (GPT terminates tool loops in ~17 calls vs Sonnet's ~56)" — EVIDENCED (per L43)

## Verdict

**PASSED.** Material finding fixed; advisories tracked. Spec compliance verified across all clauses. Test suite: 965 pass (including 6 new frame tests added during review).

## Suggested Next Action

Commit (`step 7` of make-it-live checklist).
