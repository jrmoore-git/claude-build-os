# Handoff — 2026-04-11

## Session Focus
Designed the explore intake UX: a 5-track routing question with fixed forcing questions per track, layered on existing adaptive delivery. Research session — no code changes.

## Decided
- Explore intake uses a routing question: "What do you want to think through?" with 5 tracks
- Each track has 5 fixed forcing questions (gstack-style: conversational, challenging, with parenthetical pushback)
- Delivery is hybrid: fixed question backbone + adaptive protocol (use their words, push once if vague, skip covered ground)
- Track list: Building something new / Fixing what's broken / Making a decision / Rethinking an approach / Research or refining thinking

## Designed (not yet implemented)

### Intake menu
"What do you want to think through?"
- **Building something new** — new product, feature, or side project
- **Fixing what's broken** — something isn't working and you're not sure why
- **Making a decision** — multiple options, need to pick one
- **Rethinking an approach** — it works but feels wrong
- **Something else** — research, or refining your thinking on something

### Questions per track (5 each, asked one at a time, adapted to prior answers)

**Building something new:**
1. Who needs this — a specific person, not a market segment? What's their day look like?
2. What are they doing right now to solve this — even if it's ugly? Spreadsheet, manual process, just ignoring it?
3. What's the smallest version someone would actually use — this week, not after you build the full thing?
4. What existing thing is closest to what you're building — and where does it fall short?
5. What's the version that makes you excited — the one you'd stay up late for?

**Fixing what's broken:**
1. When did you first notice — and what were you doing when it hit?
2. Have you seen it work correctly before — what was different then?
3. How are people working around it right now — or are they just stuck?
4. What's your best guess on the cause — and what makes you unsure?
5. If you fixed this perfectly, what changes for the person using it tomorrow?

**Making a decision:**
1. What are the actual options — not theoretical ones, the ones you'd realistically do?
2. Gun to your head, which way do you lean — before overthinking it?
3. What's the worst that happens if you pick wrong — and how hard is it to reverse?
4. What information would make this obvious — and can you get it before deciding?
5. Who else does this affect — and do they see the same options you do?

**Rethinking an approach:**
1. What made you start questioning it — specific moment, or a slow build?
2. What's actually working — what would you keep no matter what?
3. If you started over with what you know now, what would be different?
4. What's the part you're most afraid to change — the thing that feels load-bearing?
5. What's the cost of leaving it as-is for another six months?

**Research / refining thinking:**
1. What's the question you're actually trying to answer — in one sentence?
2. What do you already believe about this — and what would change your mind?
3. Why now — what made you think about this today, not last week?
4. What have you read or heard that shaped your current thinking?
5. What would change if you had a clear answer?

## NOT Implemented
- `config/prompts/preflight-tracks.md` — the fixed question sets above need to be written to this file
- Wire preflight-tracks into preflight-adaptive.md as the backbone
- Update SKILL.md Step 3a to reference track routing
- Still need: real /debate --explore end-to-end test of the conversation flow

## Carried Over
- Direction 1-2 overlap (architectural)
- gstack 0.14.5 → 0.16.3 update
- browse.sh wrapper
- deploy_all.sh customization
- Audit findings 11-13
- /define discover live test

## Next Session Should
1. Read this handoff — the full question design is here
2. Implement preflight-tracks.md with the 5 track question sets
3. Wire into adaptive preflight and SKILL.md
4. Run a real /debate --explore end-to-end to test the full flow

## Key Files Changed
docs/current-state.md
tasks/handoff.md
tasks/session-log.md

## Doc Hygiene Warnings
⚠ decisions.md not updated — design decision on fixed+adaptive intake tracks not yet recorded as a numbered decision
