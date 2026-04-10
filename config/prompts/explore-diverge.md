---
version: 2
last_updated: 2026-04-10
changelog: "v2: Tightened divergence to require 2+ of customer/product-form/business-model/distribution to differ. Aligned with synthesis prompt v2."
---
You will be given a question or problem statement. Previous directions have \
already been proposed.

PREVIOUS DIRECTIONS (you must NOT repeat or lightly vary any of these):

{previous_directions}

You must propose something STRUCTURALLY different. Not a cosmetic variation.

To ensure real divergence, at least 3 of these 5 dimensions must differ \
from ALL previous directions:

1. **Customer segment** — who pays? (solo dev, CTO, consultancy, vendor, \
enterprise buyer, non-technical user)
2. **Revenue model** — how do they pay? (subscription, licensing, services, \
per-seat, usage-based, free+premium)
3. **Distribution channel** — how do they find it? (direct, platform \
marketplace, channel partner, content/SEO, embedded)
4. **Product form** — what do they use? (CLI, web app, API, library, \
service, content, community)
5. **Wedge** — what single problem unlocks their wallet?

## Phase 1: Brainstorm

Before committing to a direction, brainstorm 6-8 options that satisfy the \
structural divergence requirement above. For each, note which dimensions \
differ. Include at least 2 that feel uncomfortable or contrarian. Do not \
evaluate yet.

## Phase 2: Develop

Pick the most interesting and develop it fully.

{context}

Apply the **eliminate-reduce-raise-create grid** to your direction:
- **Eliminate:** What does the current category assume is necessary that \
your direction drops entirely?
- **Reduce:** What does the category over-invest in that your direction \
does just enough of?
- **Raise:** What does the category under-invest in that your direction \
makes central?
- **Create:** What does your direction offer that nothing in the category \
has today?

Your direction must also answer:
1. **Why now?** What changed that makes this possible?
2. **What's the workaround?** What are users doing without this?
3. **10x on which axis?** Name the one dimension.
4. **Adjacent analogy:** Where did this pattern work in another market?

Rules:
- Be specific. Name the first customer, first use case, first dollar.
- Do not hedge. Make your case.
- Keep Phase 2 under 800 words.

Output format:

## Brainstorm
[6-8 one-line directions with dimension tags]

## Direction: [one-line name]

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| ... | ... | ... | ... |

## The Argument
[Why this is the right direction, answering the 4 questions above.]

## First Move
[What you'd build or do first.]

## Why This Beats the Alternatives
[What's wrong with the obvious approaches AND the previous directions.]

## Biggest Risk
[The one thing most likely to kill this.]
