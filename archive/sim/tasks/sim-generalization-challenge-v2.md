---
topic: sim-generalization
created: 2026-04-15
recommendation: PAUSE
complexity: medium
review_backend: cross-model
challengers: claude-opus-4-6, gemini-3.1-pro, gemini-3.1-pro
judge: gpt-5.4
security_posture: 2
---
# Challenge Gate v2: Should We Continue Building the Sim Generalization Pipeline?

## Recommendation: PAUSE — Run One Blocking Experiment Before Deciding

The panel and judge converge on a clear verdict: **don't continue as-is, don't abandon yet, test the one thing that wasn't tested.**

## What the Panel Said

| Challenger | Model | Verdict |
|---|---|---|
| A | claude-opus-4-6 | REVISE — add turn_hooks, test once more |
| B | gemini-3.1-pro | REVISE — prove it finds real bugs in 2 skills first |
| C | gemini-3.1-pro | REJECT — either fix to trustworthy quality or delete the code |

**Judge (GPT-5.4):** SPIKE — one blocking experiment before deciding.

## Key Findings

### 1. The gap is structural but fixable (ACCEPTED + SPIKE)
The 1.62-point quality gap decomposes into two specific missing features: (a) no mid-loop intervention mechanism in sim_driver.py, (b) thin persona cards. Both are bounded problems. The pipeline was tested *without* the feature that eval_intake.py most depends on (sufficiency/register reminders at turn 2+). Concluding generalization doesn't work from this test is like testing a car without spark plugs and concluding the engine design is flawed.

**Blocking spike:** Add `turn_hooks` callback to `run_simulation()`, inject eval_intake-style reminders, run 5 times on /explore. Success: overall mean improves by ≥0.75, hidden_truth_surfacing improves by ≥1.0, at least 4/6 dimensions within 0.5 of baseline.

### 2. Option C (smoke test) is invalid (ACCEPTED, confidence 0.91)
The current pipeline scores a known-good skill at 3.1/5. Using it as a smoke test would produce untrustworthy signal — no way to distinguish "broken skill" from "weak simulation." The panel unanimously rejected this framing until the pipeline is calibrated against known-good AND known-bad skills with explicit thresholds.

### 3. The pipeline is overbuilt for smoke testing (ACCEPTED, confidence 0.84)
If the goal is just catching gross failures, 1,520 lines of multi-agent infrastructure at 500K-800K tokens per skill is the wrong tool. Deterministic fixture-based tests or single-agent dry runs would be cheaper and more reliable for coarse coverage.

### 4. Token costs are uncertain (ACCEPTED, confidence 0.79)
500K-800K per skill is estimated, not measured. sim_driver defaults to 15 turns vs eval_intake's 8. Running 5 skills could be 4-5M tokens for an unvalidated signal. Must measure actual costs before approving multi-skill runs.

### 5. Option D (protocol overlays) was missing (ACCEPTED, confidence 0.76)
The proposal's own diagnosis says quality comes from protocol-specific tuning. The `--protocol` flag already exists. The correct middle path is: keep the generic infrastructure but acknowledge that high-quality simulation requires per-skill protocol overlays + intervention hooks + enriched personas. This isn't "generalize everything automatically" or "stop." It's "generalize the plumbing, customize the recipes."

## Decision Framework

```
                          Run the spike experiment
                                  │
                    ┌─────────────┼──────────────┐
                    ▼              ▼               ▼
            Spike passes     Spike partially    Spike fails
           (≥0.75 lift,      passes (some      (no meaningful
            4/6 dims)        dims improve)      lift)
                │                 │                │
                ▼                 ▼                ▼
           Option D:         Investigate       Option B:
        Protocol overlay   persona format,     Stop. Delete
        architecture.      then decide.        V2 scripts.
        Per-skill recipes                      Keep eval_intake.
        + generic plumbing.                    Build bespoke
                                               per high-value skill.
```

## Cost of Inaction

If we stop entirely:
- 8-10 interactive skills remain with zero interactive quality validation
- Each new bespoke harness costs ~2 days per skill  
- Register mismatch, timing bugs, protocol drift stay invisible
- 1,520 lines of tested infrastructure get deleted

If we pause for the spike:
- 1-2 hours of work (add turn_hooks, run 5 comparisons)
- Clear go/no-go signal with measured evidence
- No further investment until the data justifies it

## What To Do Now

1. **Add `turn_hooks` parameter to `run_simulation()`** — callback invoked at each turn with turn number and conversation history. ~30-40 lines.
2. **Write one hook** that reproduces eval_intake's sufficiency/register reminders. ~20 lines.
3. **Run 5 /explore simulations** with the hook enabled, same anchor personas.
4. **Measure the delta.** If ≥0.75 overall lift and ≥1.0 on hidden_truth_surfacing → proceed with Option D. If not → stop.
5. **Do NOT run against 5 untested skills** until the spike passes.

## Complexity: MEDIUM
One experiment, bounded scope, clear success criteria.
