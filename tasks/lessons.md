# Lessons

Mistakes, surprises, and patterns worth remembering. Each entry is a lesson learned from real work on this project.

**Convention:** Titles are assertions, not topics. "Long sessions silently eat their own corrections — compact at 50-70% context" — not "Session quality." The title IS the takeaway.

**Target:** Keep this file under 30 active entries. When it grows beyond that, promote recurring lessons to `.claude/rules/` files and archive one-offs.

---

| # | Lesson | Source | Rule |
|---|---|---|---|
| L10 | Adversarial process injects its own risk preferences when no posture is specified — security dominated output when user wanted speed | Pipeline over-rotated on security controls in a speed-focused analysis | Use --security-posture flag; default to 2 for product work, 4 for infra/auth |
| L11 | Adversarial validation produces bug lists when applied to strategic questions — wrong cognitive tool for the job | Strategic debate: challengers grepped codebase to verify file counts instead of pressure-testing the business thesis | Match the thinking mode to the question type: validate for implementation, pressure-test for strategy, explore for options |
| L16 | Multi-model doesn't beat single-model for divergent thinking — prompt design is the variable, not model diversity | 3 different models converged on same direction; 1 model asked 3x with forced divergence produced genuinely different output | Reserve multi-model for review/judging (proven). Use single-model with better prompts for thinking modes. |
| L13 | LLMs skip the obvious-but-correct answer when prompted to be "interesting" or "creative" — novelty bias | Explore prompt said "pick the most interesting direction." Model brainstormed the right answer as option #1 but developed option #7 instead | Prompt for "most likely to succeed" not "most interesting." Or present multiple options and let human pick. |
| L14 | The framing of the input determines the solution space more than the prompt or model — garbage frame in, garbage options out | Every explore run with a narrow frame produced narrow variations. Pre-flight reframe produced completely different directions | Pre-flight discovery conversation is the highest-leverage intervention. Better framing > better prompts > better models. |
| L15 | 5 questions dumped at once feels like a form, not a conversation — users reject it | Built v1 pre-flight as numbered list of 5 questions. User said "these are weird questions" and didn't engage | One question at a time, adapted to prior answers. GStack style. Max 4 questions. |
| L17 | [ARCHIVED — healthcheck 2026-04-11] Field name mismatches between docs and data are silent failures | Fix shipped in audit-batch2, verified. All code now uses `phase`/`debate_id`. | Verify JSONL fields against actual data before referencing in docs. |
| L18 | [ARCHIVED — healthcheck 2026-04-11] Standalone test scripts invisible to pytest | Fix shipped: `run_all.sh` runs pytest + standalone scripts. Structurally fragile (hardcoded list). | Verify `bash tests/run_all.sh` discovers new test files. |
| L20 | [PROMOTED -> rules/skill-authoring.md] Stop organizing test personas and validation around communication style | 5+ violations. Promoted to memory, then to rule (healthcheck 2026-04-11). | See `.claude/rules/skill-authoring.md` "Persona Definition" section. |
| L21 | [ARCHIVED — healthcheck 2026-04-11] review-panel personas are model selectors, not system prompts | All instances fixed (review doc mode, investigate, think Phase 5.5). D15 encodes this structurally. | For non-code content, use `--models` directly. |
| L19 | Cross-model evaluation loops are too slow — 37 serial `review` calls when `review-panel` exists | Investigation (2026-04-11) corrected the decomposition: NOT 6 refine rounds × 3 calls. Actually 37 serial `debate.py review` calls across 12+ eval rounds, averaging 1.3 min each (~48 min total). `review-panel` already parallelizes via ThreadPoolExecutor — the fix is at the orchestration layer (use `review-panel` instead of 3× serial `review`), not in debate.py itself. D13 already prescribes this fix. | Use `review-panel` for independent multi-model evaluation. Never call `review` 3× serially on the same input (D13). The parallelism infrastructure exists — the orchestration layer must use it. |
| L23 | [Resolved 2026-04-11] Security posture modifier not applied to `--models` challengers in debate.py | Healthcheck auto-verify found `--models` challengers skipped posture modifier (L10's fix was incomplete). Judge path was actually wired (panel's claim about judge was wrong — verified lines 1506-1509). Fixed: `--models` path now applies `SECURITY_POSTURE_CHALLENGER_MODIFIER`. | Verify cross-model panel claims before acting — panels can be wrong about specific code paths. |
| L22 | YAML multiline `|` in skill description breaks Claude Code's `/` menu — shows literal `|` instead of the description text | 6 of 18 skills (design, elevate, investigate, research, sync, think) used `description: \|` multiline format. Claude Code's skill loader doesn't expand YAML block scalars — it only reads quoted single-line strings. Orphaned YAML lines (like `Benefits from:` left between fields) further corrupt frontmatter, causing fallback to the first H2 heading as description. | Always use `description: "single line quoted string"` in skill frontmatter. Never use YAML `\|` or `>` block scalars for the description field. After editing frontmatter, verify the `/` menu shows the correct text. |

---

## Promoted lessons

When a lesson has been promoted to a `.claude/rules/` file or a hook, remove it from the active table above and record the promotion here. This keeps the active list lean (target: ≤30 entries) while preserving provenance. See [the enforcement ladder](../docs/the-build-os.md#part-v-the-enforcement-ladder) for when to escalate.

Before promoting a lesson, state how you would catch a violation of the resulting rule. If you can't describe a concrete test, the lesson isn't ready for promotion.

| # | Promoted to | Date |
|---|---|---|
| L12 (original) | `.claude/rules/security.md` — "Use HttpOnly cookies, never auth in URLs" | 2026-03-01 |
