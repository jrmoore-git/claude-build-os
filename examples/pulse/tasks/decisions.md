# Decisions

Settled architectural and product decisions. Each entry records what was decided, why, and what alternatives were considered.

**Convention:** Titles are assertions, not topics. "Web auth must use HttpOnly cookies because query-param tokens leak" -- not "Auth decision." The title IS the takeaway.

---

### D1: Slack-only distribution because engineers already live there -- email and web forms add friction without adding reach
**Decision:** Deliver pulse surveys exclusively via Slack DM. No email fallback, no web form, no mobile app.
**Rationale:** Sarah's team checks Slack 40+ times per day. The HR engagement survey (delivered via email link to a web form) gets 35% response rates with constant reminders. Slack DMs get read within minutes. Adding email as a fallback doubles the integration surface for a channel that reaches maybe 2 people who aren't on Slack -- and those 2 people aren't the target user.
**Alternatives considered:** (a) Email + Slack dual delivery (rejected: doubles integration work, email response rates are poor for this audience), (b) Web form with Slack notification linking to it (rejected: extra click kills response rate -- the interaction must happen inside the DM), (c) Mobile app (rejected: nobody installs another app for a 3-question weekly survey)
**Date:** 2026-03-15

### D2: Anonymous by default because named responses kill candor in teams under 15 people
**Decision:** Responses are anonymized at the storage layer. The database stores `(team_id, week, question_id, score)` with no user identifier. Minimum 3 responses required to display aggregates.
**Rationale:** Sarah's team is 8-12 people. In a team that size, named responses are effectively public -- the manager can narrow down who said what. Research on psychological safety (Edmondson) shows that perceived anonymity matters more than actual anonymity for candid feedback. The 3-response minimum prevents inference attacks on weeks with low participation.
**Alternatives considered:** (a) Named by default with opt-in anonymity (rejected: opt-in anonymity signals distrust -- "why are you hiding?"), (b) Anonymous with manager override (rejected: the override exists = responses are not actually anonymous, and people know it), (c) Fully anonymous with no minimum threshold (rejected: a team of 4 with 1 response that week is de facto named)
**Date:** 2026-03-15

### D3: Fixed question bank over custom questions because bad questions produce worse data than no questions
**Decision:** Ship V1 with exactly 3 fixed questions: workload, support, and priority clarity. No customization.
**Rationale:** The three questions map to the top predictors of voluntary attrition in engineering teams (overwork, isolation, unclear direction). Custom questions sound good but create two problems: (1) managers write leading questions ("How great is our team culture?"), and (2) changing questions breaks trend comparability. The fixed bank was validated against Gallup Q12 and Google's gDNA research for the highest signal-to-noise items in a 3-question format.
**Alternatives considered:** (a) Fully customizable question bank (rejected: breaks trend lines when questions change, managers write bad questions), (b) Fixed bank + 1 custom slot (rejected: the custom slot becomes the only question managers care about, and it's usually the worst one), (c) Rotating questions from a larger fixed pool (rejected: can't trend a question you only ask every 4th week)
**Date:** 2026-03-16
