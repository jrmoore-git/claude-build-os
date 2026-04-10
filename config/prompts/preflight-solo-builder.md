---
version: 2
last_updated: 2026-04-10
changelog: "v2: Rewritten as GStack-style adaptive forcing questions. One at a time, push until specific."
---
# Pre-Flight: Solo Builder

Ask these questions ONE AT A TIME. Wait for the answer. Push if the answer is vague. Move on when the answer is specific enough.

## Routing

Read the user's input and assess their situation:

- **Workflow pain** (they described a frustration or bottleneck): Ask Q1, Q2, Q3
- **Idea-driven** (they want to build something specific): Ask Q2, Q4, Q5
- **Vague** ("I want to automate stuff"): Ask Q1 first, then route based on answer

Skip any question whose answer is already clear from what the user has said.

## Questions

### Q1: The Specific Pain
"Walk me through the last time this frustrated you. What were you doing, what went wrong, and how long did you spend on it?"

**Push until you hear:** A specific incident with real time or real consequence. Not "it's generally annoying."
**Red flag:** They describe a pain they've felt once. Once isn't a pattern. Ask: "How often does this happen? Weekly? Daily?"

### Q2: The Bottleneck
"Is this actually your bottleneck — the thing that determines how fast your most valuable work gets done? Or is it annoying but not rate-limiting?"

**Push until you hear:** Either "yes, this is the bottleneck because [specific reason]" or "no, the real bottleneck is [something else]." If the latter, explore the real bottleneck.
**Red flag:** "It wastes time." Time waste ≠ bottleneck. A task can waste 30 minutes a week and not matter. Ask: "If you eliminated this entirely, what would change about your output?"

### Q3: The Current Workaround
"How are you handling this now? Show me the ugly version — the spreadsheet, the manual process, the thing you're embarrassed by."

**Push until you hear:** A specific workflow. The workaround reveals the real requirement better than the wish list.
**Red flag:** "I'm not handling it." If there's no workaround, the pain may not be real enough to justify building.

### Q4: The Simple Version
"What's the absolute simplest thing that would make this better? Not the dream version — the version you'd build in one afternoon that gets you 80% of the value."

**Push until you hear:** Something genuinely simple — one script, one automation, one integration. The first answer is usually too complex.
**Red flag:** They describe a platform. Push: "No — what's the one-afternoon version?"

### Q5: The Failure Mode
"If you build this and it breaks silently — gives wrong output, skips items, corrupts data — how would you know? What's the blast radius?"

**Push until you hear:** A specific detection mechanism or an honest "I wouldn't know." The honest answer often kills the project — and that's good.
**Red flag:** "It would be fine." Nothing is fine if it fails silently. Push: "What if it ran for a week with wrong output before you noticed?"

## After Questions

Compose the answers into a context block:

```
PRE-FLIGHT CONTEXT:
Situation: [workflow pain / idea-driven]
Specific pain: [Q1 answer]
Bottleneck: [Q2 answer]
Current workaround: [Q3 answer]
Simplest useful version: [Q4 answer]
Failure mode: [Q5 answer]
```
