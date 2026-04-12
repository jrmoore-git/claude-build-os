# Evidence: Eval Loop Speed Investigation (L19 Claim)

## The Claim (L19)
"Cross-model evaluation loops are too slow -- 30+ min for 6 rounds. Explore intake eval: 6 rounds x 3 serial model calls x 2-4 min each = ~60 min. Then 5 persona sims at ~3 min each, 3 run serially. Total: ~75 min."

## Evidence Collected

### E1: debate.py refine is inherently serial (CONFIRMED)
- `cmd_refine()` at line 2374 uses `for i in range(rounds)` -- plain serial loop
- Each round calls `_call_litellm()` or `llm_tool_loop()` sequentially
- This is correct by design: round N+1 input depends on round N output
- BUT: the claim says "6 rounds x 3 serial model calls" -- refine uses 1 model per round (rotating gemini -> gpt -> claude), NOT 3 models per round. So the claim's math is wrong for refine.

### E2: debate.py uses ThreadPoolExecutor for challenge and review-panel (CONFIRMED)
- `challenge` at line 1144: `ThreadPoolExecutor(max_workers=len(challengers))` -- parallel
- `review-panel` at line 2915: `ThreadPoolExecutor(max_workers=len(personas))` -- parallel
- `review` (single persona) at line ~2830: single serial call -- no parallelism possible
- `explore` at line 3246: `for i in range(2, directions_count + 1)` -- serial (by design, needs previous directions)

### E3: Debate log shows 37 serial `review` calls, NOT `review-panel` (CONFIRMED)
- Date: 2026-04-11, 17:44:59 to 18:32:45 = 47.8 minutes wall clock
- All 37 calls hit `tasks/explore-intake-refined.md`
- Model distribution: gpt-5.4 (13), gemini-3.1-pro (12), claude-opus-4-6 (12)
- Pattern: 3 serial `review` calls per eval round (one per model), NOT `review-panel` (which would be 1 call with 3 parallel workers)
- Average per call: 77s (~1.3 min)
- 37 calls / 3 models per round = ~12 eval rounds (not 6 as claimed)

### E4: eval_intake.py DOES have parallelism (CONFIRMED)
- `run_all()` uses `ThreadPoolExecutor(max_workers=min(len(persona_files), 3))` at line 365
- 5 persona files exist in config/eval-personas/
- Max 3 parallel, so 2 batches (3+2) when using --run-all
- Each persona sim is multi-turn: up to 8 turns x 2 LLM calls/turn + 1 judge = ~13-17 LLM calls per persona
- The claim says "3 run serially" -- this likely means the SESSION orchestrated 3 individual `eval_intake.py` runs serially instead of using `--run-all`

### E5: D13 decision already identified root cause
- D13 in decisions.md confirms: "Root cause: 18 serial API calls (6 rounds x 3 models) when each round's 3 calls are independent"
- D13's "18 serial API calls" matches the claim's "6 rounds x 3 serial model calls"
- But the log shows 37 calls across 12+ rounds, not 18 across 6

### E6: Per-call latency from token analysis (explore-intake refine run)
- Refine run completed at 2026-04-11T10:50:09 with 6 calls (6 rounds, 1 model each)
- gemini-3.1-pro: 2 calls, avg 6047 completion tokens
- gpt-5.4: 2 calls, avg 5152 completion tokens  
- claude-opus-4-6: 2 calls, avg 6150 completion tokens
- At typical generation speeds (50-150 tok/s), each call takes 40-120s = ~1-2 min

### E7: LLM timeouts configured
- Non-tool-loop calls: timeout=300s (5 min)
- Tool-loop calls: timeout=240s (4 min)
- Per-call: 120s timeout in eval_intake.py for interviewer/persona calls, 180s for judge

## Hypotheses

### H1: The 75-min total is caused by using `review` (serial) instead of `review-panel` (parallel)
Evidence FOR: E3 shows 37 serial `review` calls over 47.8 min. `review-panel` would have parallelized each triplet, reducing wall-clock by ~2/3 per round.
Evidence AGAINST: Even with `review-panel`, each ROUND is still serial (change input between rounds).
Estimated savings: From ~48 min to ~16-20 min (3x speedup on the parallel portion).

### H2: The session orchestrated persona sims serially instead of using `eval_intake.py --run-all`
Evidence FOR: The claim says "3 run serially." `eval_intake.py --run-all` parallelizes with max_workers=3. If the session ran 5 individual invocations of `eval_intake.py --persona`, they'd be serial.
Evidence AGAINST: No direct log evidence of individual persona sim timing -- `eval_intake.py` doesn't log to `debate-log.jsonl`.
Impact: Moderate (~5-10 min saved if parallelized).

### H3: The claim's math is inaccurate -- actual numbers differ from stated
Evidence FOR: 
- Claim says "6 rounds" but log shows 12+ eval rounds (37 calls / 3 models)
- Claim says "3 serial model calls per round" which matches (3 `review` calls per round) 
- Claim says "2-4 min each" but actual avg is 1.3 min per call
- Claim says total "~60 min for refine" but actual serial review block was 47.8 min
- The refine command itself (debate.py refine, 6 rounds with 1 model per round) takes much less than 60 min
Evidence AGAINST: The 75 min total wall-clock is plausible given the 47.8 min review block plus persona sims plus overhead.
