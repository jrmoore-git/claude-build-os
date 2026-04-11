# Product Requirements -- Pulse

## 1. What we're building

Pulse is a weekly team health check delivered through Slack. Every Monday at 9am local time, each team member gets a DM with 3 questions on a 1-5 scale. Responses feed a trend dashboard that shows team leads where morale is heading before it becomes a resignation. It exists because Sarah Chen's team lost two engineers in Q3 with zero warning -- the skip-level 1:1s weren't catching problems early enough.

## 2. Who it's for

Sarah Chen, engineering team lead at a Series B startup. She manages 8-12 direct reports across two squads. She got promoted because her teams ship on time and retention is high. She gets fired if attrition spikes or delivery stalls. Her current process: monthly skip-level 1:1s, quarterly engagement surveys from HR that arrive 6 weeks late. She checks Slack 40+ times per day. She has never voluntarily opened the HR portal.

## 3. Core requirements

1. Users can install Pulse as a Slack app to their workspace with a single OAuth flow.
2. Users can configure which Slack channels represent teams (one channel = one team).
3. The system delivers 3 pulse questions via Slack DM to every member of configured teams every Monday at 9am in each member's local timezone.
4. Users can respond to each question with a 1-5 scale using Slack interactive buttons (no typing required).
5. The system confirms receipt immediately after the last response with a single-message acknowledgment.
6. Users can view a trend dashboard showing team averages per question over the last 12 weeks.
7. The system flags teams where any question's 4-week moving average drops below 3.0 (attention threshold).
8. The system anonymizes individual responses -- team leads see only aggregate scores (minimum 3 responses to display).

## 4. Acceptance criteria

- [ ] Given a workspace admin, when they click "Add to Slack" on the landing page, then the OAuth flow completes and the app appears in the workspace within 5 seconds.
- [ ] Given a configured team with 8 members, when Monday 9am arrives in each member's timezone, then all 8 members receive the pulse DM within 2 minutes of their local 9am.
- [ ] Given a pulse DM, when a user taps a rating button for all 3 questions, then the system stores the response and sends a confirmation message within 1 second.
- [ ] Given a team with 12 weeks of responses, when the team lead opens the dashboard, then the trend chart loads within 2 seconds showing weekly averages per question.
- [ ] Given a team where "workload" averages 2.8 over the last 4 weeks, when the team lead opens the dashboard, then the workload row is flagged with an attention indicator.
- [ ] Given a team with only 2 responses in a week, when the team lead views that week's data, then individual scores are hidden and the week shows "insufficient responses."
- [ ] Given a workspace with 3 configured teams, when the admin views the dashboard, then they see only their own teams' data.

## 5. Constraints

- Slack API only -- no email, SMS, or web form delivery. All interaction happens inside Slack.
- PostgreSQL 15+ for data storage. No ORM -- use parameterized queries directly.
- Responses must be anonymized at the storage layer. The database stores `(team_id, week, question_id, score)` -- never `(user_id, score)`.
- Minimum 3 responses per team per week to display aggregates (prevents de-anonymization of small teams).
- Fixed question bank of 3 questions. V1 ships with: (1) "How manageable is your workload?" (2) "How supported do you feel by your team?" (3) "How clear are your priorities this week?"
- Dashboard must work in Chrome 120+, Safari 17+, and Firefox 121+.
- No CI/CD pipeline required for V1 -- deploy manually via `docker compose up`.

## 6. Out of scope

- HRIS integration (BambooHR, Workday, Rippling). Team membership comes from Slack channels.
- Custom questions. The question bank is fixed for V1 to prevent survey fatigue from poorly written questions.
- Email or web form fallback for non-Slack users.
- Push notifications outside Slack (mobile push, browser notifications).
- AI-powered sentiment analysis or automated recommendations.
- Manager-of-managers roll-up views (skip-level dashboards).
- Historical data import from prior survey tools.
- SSO/SAML -- authentication is Slack OAuth only.

## 7. Technical decisions

- **Slack SDK:** Slack Bolt for Python 3.11. Handles OAuth, events, and interactive messages. See D1.
- **Dashboard:** Next.js 14 with Chart.js for trend visualization. Static export served from the same container.
- **Database:** PostgreSQL 15. Schema: `teams`, `team_members`, `pulse_weeks`, `responses`. No ORM.
- **Deployment:** Single `docker-compose.yml` with two services (api, dashboard) and a PostgreSQL container.
- **Scheduling:** `APScheduler` running inside the Bolt process. Checks member timezones and dispatches DMs at each member's local 9am.
- **Anonymization:** Responses stored without user_id. The Bolt handler maps `slack_user_id` to `team_id` for routing, then drops the user identifier before INSERT.

## 8. Success criteria

- 3 pilot teams onboarded within 2 weeks of deploy.
- 70%+ response rate sustained over 4 consecutive weeks (measured as responses received / DMs sent).
- Team lead NPS > 30 at 4-week check-in (survey the 3 pilot team leads directly).
- Zero privacy incidents -- no individual responses exposed in dashboard or logs.
- Dashboard page load < 2 seconds on a standard office connection.

## 9. Verification plan

- **Requirement 1 (Slack install):** Integration test using Slack's sandbox workspace. Verify OAuth redirect, token storage, and app presence in workspace.
- **Requirement 2 (Team config):** Automated test: configure a channel, verify `teams` table row created with correct `slack_channel_id`.
- **Requirement 3 (DM delivery):** Integration test: trigger scheduler for a test team, verify DMs sent via Slack API audit log. Manual check: confirm DM arrives in sandbox workspace.
- **Requirement 4 (Response buttons):** Automated test: simulate button click payload, verify response stored in `responses` table.
- **Requirement 5 (Confirmation):** Automated test: submit 3 responses, verify confirmation message sent via Slack API.
- **Requirement 6 (Trend dashboard):** Seed database with 12 weeks of test data. Automated test: hit `/api/trends?team_id=X`, verify JSON contains 12 weekly data points. Manual check: open dashboard in browser, verify chart renders.
- **Requirement 7 (Attention flags):** Automated test: seed a team with 4 weeks averaging 2.8 on workload, hit the trends API, verify `attention: true` flag on that question.
- **Requirement 8 (Anonymization):** Automated test: INSERT a response through the Bolt handler, query `responses` table, verify no `user_id` or `slack_user_id` column exists. Code review: verify the handler drops user identity before the INSERT statement.
