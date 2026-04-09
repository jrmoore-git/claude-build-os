---
name: sync
description: Update all affected source-of-truth documents after changes
user-invocable: true
---

# Sync Upstream Docs

After approved changes, update all affected source-of-truth documents in one pass.

## Procedure

Check each of these and update if relevant:

1. **`docs/project-prd.md`** — Did behavior change? Did scope change? Update the relevant section.
2. **`tasks/decisions.md`** — Were decisions made? Add numbered entries with assertion-style titles.
3. **`tasks/lessons.md`** — Were there surprises? Mistakes? Add entries.
4. **`docs/current-state.md`** — Did project truth change? Update.
5. **`tasks/handoff.md`** — Is work incomplete? Update for the next session.
6. **`.claude/rules/`** — Should any lesson become a rule?
7. **`CLAUDE.md`** — Should any project-specific rule be added?

## Output

List what was updated and what was not:

```
## Sync Results
- Updated: [files]
- No change needed: [files]
- Skipped (not applicable): [files]
```

## Rules
- Do not update docs with speculative or unverified changes. Only sync what actually happened.
- If the PRD changed, note the section and what changed.
- **Sequencing:** Run `/sync` after review. Then run `/handoff` last. `/sync` updates state; `/handoff` reads that state to write the forward-looking handoff. Running them in the wrong order produces a stale handoff.
- `/sync` may note "work incomplete" in `handoff.md` item 5, but the full handoff document is owned by `/handoff`.
