---
version: 2
last_updated: 2026-04-10
changelog: "v2: Rewritten as GStack-style adaptive forcing questions. One at a time, push until specific, red flags for vague answers. Replaces v1 batch questionnaire."
---
# Pre-Flight: Product Opportunity

Ask these questions ONE AT A TIME. Wait for the answer. Push if the answer is vague. Move on when the answer is specific enough.

## Routing

Read the user's input and assess their stage:

- **Pre-product** (idea stage, nothing built or only a prototype): Ask Q2, Q3, Q5
- **Has users** (people use it but no revenue): Ask Q2, Q3, Q4
- **Has revenue** (paying customers): Ask Q1, Q3, Q5

Always include Q3 (Different Job) — it's the strongest reframer. Skip any question whose answer is already clear from what the user has said.

## Questions

### Q1: The Blocker
"What would make someone NOT use this — even if they agree it's valuable? What's the adoption barrier?"

**Push until you hear:** A specific friction point — setup time, learning curve, workflow disruption, team buy-in. This surfaces the go-to-market problem, not just the value prop.
**Red flag:** "Nothing — it's great." Push: "Think about the busiest, most skeptical person on the team. What would they say when you showed them this?"

### Q2: The Burn
"Tell me about the last time this problem actually burned someone — not theoretically, but a specific incident. What happened, how long did recovery take, and what did it cost?"

**Push until you hear:** A concrete story with names, timelines, and consequences. Stories reveal real pain better than cost estimates.
**Red flag:** "It's generally painful" or cost estimates without incidents. Push: "Give me the specific moment — what went wrong, when, and what happened next?"
**If the user says "nobody's getting burned":** Switch to the soft variant: "What's the most someone has struggled with this? Not a crisis — the biggest frustration or time sink." Low-pain products still have real friction; the question just needs to meet them where they are.
**Follow-up if time allows:** "And what's the janky workaround you're using right now to prevent it happening again?" The workaround reveals the real competitor.

### Q3: Different Job, Different Buyer
"You described this as [category they used]. Forget that label — who is a COMPLETELY DIFFERENT person who'd use the same capabilities for a completely different reason?"

**Push until you hear:** A different job title, different industry, or different use case. Not "also developers but bigger ones."
**Red flag:** They can only think of variations on their current user. Push harder: "What if you couldn't sell to [current user] at all — who else would want these capabilities?"

### Q4: The Real Job
"Forget the product for a second. What does this person actually want to be doing with their day? Not 'using your tool' — the thing your tool lets them get back to."

**Push until you hear:** An activity that has nothing to do with your product category. Priya wants to be selling. Dev wants to be doing client work. James wants to stop defending AI adoption. The product that gets them back to THAT is the real product.
**Red flag:** They describe using the product. Push: "No — what would they rather be doing instead of thinking about this problem at all?"

### Q5: The 10x Version
"Forget what exists today. What's the biggest version of this — the version that would make people say 'holy shit, this changes everything'? Not incremental improvement — a different order of magnitude."

**Push until you hear:** Something that sounds unreasonable or uncomfortable. The first answer is always conservative.
**Red flag:** They describe a slightly better version of what exists. Push: "No — what would make you nervous to describe because it sounds too ambitious?"

## After Questions

Compose the answers into a context block:

```
PRE-FLIGHT CONTEXT:
Stage: [pre-product / has users / has revenue]
Demand evidence: [Q1 answer]
Current workaround: [Q2 answer]
Different buyer/job: [Q3 answer]
Downstream activity: [Q4 answer]
10x version: [Q5 answer]
```

This context replaces the category-anchored description as input to the AI.
