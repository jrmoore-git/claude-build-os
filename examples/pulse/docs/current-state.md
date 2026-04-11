# Current State -- 2026-03-29

## What Changed This Session
- Slack Bolt app handles OAuth install, DM delivery, and button responses end-to-end
- APScheduler sends pulse DMs at 9am per member's local timezone with 1-second rate-limit delay between messages
- Anonymization confirmed: `responses` table has no user_id column, handler drops `slack_user_id` before INSERT
- Dashboard shows trend chart for last 12 weeks with attention flags for averages below 3.0
- 3-response minimum enforced: weeks with fewer responses show "insufficient responses" instead of scores

## Current Blockers
- Slack sandbox workspace token expires April 12 -- need to regenerate before pilot launch
- Chart.js tooltip formatting broken on Safari 17 (works in Chrome and Firefox). Low priority -- tooltips show raw numbers, chart itself renders correctly.

## Next Action
Deploy to staging and onboard the first pilot team (Sarah's squad-alpha, 8 people). Need Sarah to run `/pulse setup #squad-alpha` in Slack to trigger the channel config flow.

## Recent Commits
a3f1d2e Fix DST drift: resolve timezone at send time, not at schedule time
b7c4e9a Add 1-second rate limit delay between Slack DM sends
c2d8f3b Enforce 3-response minimum in trends API
d9e1a4c Dashboard: attention flag styling and tooltip formatting
