# Recall — Session Bootstrap

Load a compact working brief to orient the current session. Invoked by `/recall`, "catch me up", or at session start.

## Procedure

Read each file below. If a file is missing, skip it silently — do not mention it.

1. **Current state** — `docs/current-state.md`

2. **Handoff notes** — `tasks/handoff.md` (skip if missing)

3. **Recent sessions** — `tasks/session-log.md`
   Read the whole file, extract the **last 5 entries** (entries are separated by `---`).

4. **Active phase** — `docs/build-plan.md`
   From the phase status in current-state.md, identify the current in-progress phase. Read only that phase's section from `docs/build-plan.md`. Skip if phase is unclear or file is missing.

5. **Open decisions** — `tasks/decisions.md`
   Scan for any entry marked undecided, blocked, or lacking a resolution. Extract only those.

6. **Recent lessons** — `tasks/lessons.md`
   Read the last 10 rows of the table (highest lesson numbers).

7. **Topic search** (optional) — If the session involves a specific domain, run:
   ```
   python3 scripts/recall_search.py [domain keywords] --files lessons,decisions
   ```
   Extract any results with score > 0.1 and include in the brief under a **Relevant prior context** section.
   If BM25 returns zero results or all scores < 0.5, try semantic fallback:
   ```
   python3 scripts/recall_search.py [domain keywords] --semantic --files lessons,decisions
   ```
   Include results with similarity > 0.5 under "Relevant prior context."
   Semantic search is speculative — treat results below 0.55 as low-confidence.

## Output Format

Write a single compact brief, under 2000 tokens. Use this structure:

```
## Status
[1–3 bullets: what phase we're in, what's working, what's broken]

## Last Session
[2–4 bullets: what was done, what was decided, what was NOT finished]

## Open Decisions
[bullets: only genuinely undecided items — skip if none]

## Lessons (recent)
[5–10 bullets: most useful recent lessons, paraphrased short]

## Next
[1–3 bullets: what to do first this session]
```

**Rules:**
- No essays. Bullets only. One line per bullet.
- Skip any section that has nothing real to say.
- Do not quote raw message content from personal channels.
- Do not surface file contents verbatim — synthesize.
- If context is thin (files sparse), say so in one line and stop.
