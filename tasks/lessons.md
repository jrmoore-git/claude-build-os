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
| L17 | Field name mismatches between docs and data are silent failures — `.get('mode')` returns `?` forever when the field is `phase` | Audit Batch 2 review caught operational-context.md and /status skill using `mode`/`status` while debate-log.jsonl uses `phase`/`debate_id` | When referencing JSONL/DB fields in docs or skills, verify against actual data (`tail -1 file | python3.11 -c "import json,sys; print(json.loads(sys.stdin.read()).keys())"`) |
| L18 | Standalone test scripts invisible to pytest = invisible to pre-commit = linter violations ship uncaught | `test_tool_loop_config.py` and `test_debate_smoke.py` use `if __name__ == "__main__"` custom runners. `run_all.sh` only ran `pytest tests/`. 3 inline temperature violations shipped in explore/pressure-test because the linter never ran at commit time. | `run_all.sh` now runs both pytest AND standalone scripts. If adding a test file, verify `bash tests/run_all.sh` discovers it. |
| L19 | Cross-model evaluation loops are too slow — 30+ min for 6 rounds frustrates users and blocks iteration | Explore intake eval: 6 rounds × 3 serial model calls × 2-4 min each = ~60 min. Then 5 persona sims at ~3 min each, 3 run serially. Total post-fix eval: ~75 min wall clock. The iteration loop (change → eval → triage → change) is inherently serial but individual model calls and persona sims are embarrassingly parallel. | Three fixes needed: (1) parallelize independent API calls within each round, (2) batch multiple fixes per round instead of one-fix-per-round, (3) run all persona sims concurrently. Root cause is debate.py's serial-by-default execution model + the session's serial orchestration of debate.py calls. |

---

## Promoted lessons

When a lesson has been promoted to a `.claude/rules/` file or a hook, remove it from the active table above and record the promotion here. This keeps the active list lean (target: ≤30 entries) while preserving provenance. See [the enforcement ladder](../docs/the-build-os.md#part-v-the-enforcement-ladder) for when to escalate.

Before promoting a lesson, state how you would catch a violation of the resulting rule. If you can't describe a concrete test, the lesson isn't ready for promotion.

| # | Promoted to | Date |
|---|---|---|
| L12 (original) | `.claude/rules/security.md` — "Use HttpOnly cookies, never auth in URLs" | 2026-03-01 |
