# Session Log

Historical record of what happened across sessions. Each entry is appended, never overwritten.

**When to create:** First session. Append an entry at the end of every session.
**Session log vs handoff:** The session log is a historical record (what happened, append-only, never overwritten). The handoff is forward-looking transfer state (what to do next, overwritten each session). Both capture "done" and "not done" — session-log for posterity, handoff for action. See `docs/file-ownership.md`.
**Native `--continue`/`--resume`** preserves conversation history but not structured context. The session log ensures decisions and outcomes survive even without native session continuity.

---

## YYYY-MM-DD — [session topic in 5-8 words]

**Decided:**
- [Key decisions made, or "None"]

**Implemented:**
- [What was built or changed]

**Not Finished:** [What remains, blockers, or "Nothing outstanding"]

**Next Session:** [First thing to do]
