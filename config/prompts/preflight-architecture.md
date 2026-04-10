---
version: 2
last_updated: 2026-04-10
changelog: "v2: Rewritten as GStack-style adaptive forcing questions. One at a time, push until specific."
---
# Pre-Flight: Architectural Decision

Ask these questions ONE AT A TIME. Wait for the answer. Push if the answer is vague. Move on when the answer is specific enough.

## Routing

Read the user's input and assess:

- **Green field** (new system, no existing constraints): Ask Q1, Q2, Q3
- **Migration/refactor** (existing system, considering change): Ask Q1, Q4, Q5
- **Build vs. buy** (evaluating an external option): Ask Q2, Q3, Q5

Skip any question whose answer is already clear from what the user has said.

## Questions

### Q1: Hard Constraints
"What absolutely cannot change? Existing data model, regulatory requirements, team size, timeline, budget — what's fixed?"

**Push until you hear:** Concrete constraints with reasons. Not "we're flexible" — nobody is fully flexible.
**Red flag:** "No constraints." Push: "What about timeline? Team size? Existing data you can't migrate? Contracts with vendors?"

### Q2: Reversibility
"If this decision turns out to be wrong in 6 months, what does recovery look like? Is this a config change or a data migration?"

**Push until you hear:** A specific recovery scenario with estimated effort. The answer determines how much deliberation this deserves.
**Red flag:** "We can always change it later." Push: "Walk me through exactly what 'changing it later' involves. Who does what? How long? What breaks?"

### Q3: The Optimization Target
"You're going to be bad at something. What are you explicitly willing to sacrifice? Name the one thing you're optimizing for and the things that lose."

**Push until you hear:** A forced ranking, not "we want all of them." Performance vs. simplicity. Speed-to-ship vs. long-term maintainability. Flexibility vs. consistency.
**Red flag:** "We need high performance AND simplicity AND flexibility." Push: "If you could only have one, which one? The other two become 'good enough.'"

### Q4: Second-Order Effects
"If you make this change, what becomes harder later? Not 'what could go wrong' — what future work becomes more expensive or more complex because of this choice?"

**Push until you hear:** A specific downstream consequence. Every architectural choice closes doors.
**Red flag:** "Nothing — this is strictly better." Push: "What's the thing the team will complain about in a year because of this decision?"

### Q5: The Boring Option
"What's the most boring, conventional way to solve this? The thing a senior engineer would do if they had to ship it by Friday with no drama."

**Push until you hear:** A specific boring solution. Then ask: "Why isn't that good enough?" The answer reveals what actually matters.
**Red flag:** They can't name a boring option. If there's no conventional solution, you're in genuinely novel territory and should slow down.

## After Questions

Compose the answers into a context block:

```
PRE-FLIGHT CONTEXT:
Decision type: [green field / migration / build-vs-buy]
Hard constraints: [Q1 answer]
Reversibility: [Q2 answer]
Optimization target: [Q3 answer]
Second-order effects: [Q4 answer]
Boring option: [Q5 answer]
```
