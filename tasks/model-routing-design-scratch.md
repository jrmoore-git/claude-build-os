# Model Routing — Scratch Notes

## Evidence from this session

- GPT caught argparse `default=None` blocker (implementation precision)
- Gemini produced 13 items vs GPT's 15 but different coverage focus (edge cases)
- Claude (me) focused on strategic coherence and UX risks
- Perplexity available for web research via PERPLEXITY_API_KEY in .env
- Current routing: all ad-hoc, skills hardcode `--models claude-opus-4-6,gemini-3.1-pro,gpt-5.4`
- Config has persona→model map but no task_type→model map
- orchestration.md says "Match model cost to task complexity" but no enforcement

## User feedback during session
- "What I really want is the system to be smart" — tool should figure out the right thing
- "Different models have different strengths" — routing should be deliberate
- Perplexity reminder: available for web research when codebase knowledge insufficient
- User rejected multi-question intake — problem is obvious from context, don't over-process
