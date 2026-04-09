# Lessons

Mistakes, surprises, and patterns worth remembering. Each entry is a lesson learned from real work on this project.

**Convention:** Titles are assertions, not topics. "Long sessions silently eat their own corrections — compact at 50-70% context" — not "Session quality." The title IS the takeaway.

**Target:** Keep this file under 30 active entries. When it grows beyond that, promote recurring lessons to `.claude/rules/` files and archive one-offs.

---

| # | Lesson | Source | Rule |
|---|---|---|---|
| L1 | [Assertion-style title] | [What happened] | [What to do about it] |

---

## Promoted lessons

When a lesson has been promoted to a `.claude/rules/` file or a hook, remove it from the active table above and record the promotion here. This keeps the active list lean (target: ≤30 entries) while preserving provenance. See [the enforcement ladder](../docs/the-build-os.md#part-v-the-enforcement-ladder) for when to escalate.

Before promoting a lesson, state how you would catch a violation of the resulting rule. If you can't describe a concrete test, the lesson isn't ready for promotion.

| # | Promoted to | Date |
|---|---|---|
| L12 | `.claude/rules/security.md` — "Use HttpOnly cookies, never auth in URLs" | 2026-03-01 |
