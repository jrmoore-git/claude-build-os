# V2 Pipeline Baseline Diagnostic — /explore (SKILL.md)

Date: 2026-04-15
Executor input: SKILL.md (8,537 chars — generic skill definition)

## Scores vs eval_intake.py baseline

| Dimension | eval_intake (5 personas) | V2 SKILL.md (3 personas) | Delta |
|-----------|--------------------------|--------------------------|-------|
| register_match | 4.40 | 2.67 | -1.73 |
| flow | 4.80 | 3.67 | -1.13 |
| sufficiency_timing | 4.80 | 3.67 | -1.13 |
| context_block_quality | 4.80 | 2.67 | -2.13 |
| hidden_truth_surfacing | 4.80 | 3.33 | -1.47 |
| feature_test | 4.80 | 2.67 | -2.13 |

**All 6 dimensions fail the 0.5-point gate.**

## Root Cause

The executor receives the raw SKILL.md, which is a generic skill definition covering all phases of /explore (context assessment, pre-flight, research, cross-model synthesis). It lacks:

1. **Register matching rules** — eval_intake.py's protocol has 10+ specific rules (match case, punctuation, message length, word count test, examples of right vs wrong)
2. **Sufficiency gate mechanics** — internal checklist for when to stop asking
3. **Thread-and-steer instructions** — how to thread from the user's last answer
4. **Reframe trigger** — specific mechanics for when/how to reframe
5. **Context block template** — exact format for composing the output

The SKILL.md tells the executor *what* /explore does, not *how* to do the intake conversation.

## Conclusion

The V2 pipeline infrastructure works (IR compilation, persona loading, rubric loading, turn loop, judging all function correctly). The quality gap is entirely in the executor prompt content — it needs the refined protocol, not the generic SKILL.md.

Next: Re-run with --protocol tasks/explore-intake-refined.md
