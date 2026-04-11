# Lessons

Mistakes, surprises, and patterns worth remembering. Each entry is a lesson learned from real work on this project.

**Convention:** Titles are assertions, not topics. "Long sessions silently eat their own corrections -- compact at 50-70% context" -- not "Session quality." The title IS the takeaway.

**Target:** Keep this file under 30 active entries. When it grows beyond that, promote recurring lessons to `.claude/rules/` files and archive one-offs.

---

| # | Lesson | Source | Rule |
|---|---|---|---|
| L1 | Slack API rate limits hit during bulk DM delivery -- batch sends with 1-second delays between messages | Sent 45 DMs at once during 5-team test, got rate-limited after 20. Slack's `chat.postMessage` allows ~1 msg/sec for bot tokens in bulk. APScheduler job now staggers sends with `time.sleep(1)` between each DM. | Add explicit rate-limit handling for any Slack API call that scales with team size. Don't trust "it worked in dev with 3 people." |
| L2 | Store timestamps in UTC and convert at display time -- timezone math at write time causes drift when DST changes | First implementation stored "9am local" as a pre-computed UTC offset per user. When DST shifted, half the team got their pulse at 8am or 10am. Fix: store everything UTC, compute local time at send time using `zoneinfo` with the member's IANA timezone from Slack's `users.info`. | Never pre-compute timezone offsets. Always store UTC and resolve to local time at the moment of use. Python `zoneinfo` handles DST correctly; manual offset arithmetic does not. |
