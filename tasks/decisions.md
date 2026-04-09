# Decisions

Settled architectural and product decisions. Each entry records what was decided, why, and what alternatives were considered.

**Convention:** Titles are assertions, not topics. "Web auth must use HttpOnly cookies because query-param tokens leak" — not "Auth decision." The title IS the takeaway.

---

### D1: Content cache deferred — research models use targeted reads not batch classify
**Decision:** Proceed with Phase 2 research without populating data/v3-raw/github/contents/ cache
**Rationale:** 18 other tools work fine; classify_files_by_signals still matches path patterns; models can use get_file_contents and read_files_bulk for targeted reads. Building lazy-fetch would delay pipeline 1-2h.
**Alternatives considered:** (a) Build lazy-fetch in classify (rejected: engineering time), (b) Hand-seed curated cache (rejected: picks winners before research)
**Date:** 2026-04-09

### D2: Brief thinned from 6 families to 4 directions per 3-model challenge convergence
**Decision:** Reduce analytical families from 6 named + 5 methodological guidance items to 4 broad directions + 3 epistemological notes. Add explicit "choose 2-3 and go deep" instruction.
**Rationale:** All 3 challengers flagged the original brief as too thick (de facto analysis plan). 2/3 flagged named proxy definitions as technique-level leakage. Thinning increases analyst diversity.
**Alternatives considered:** Keep 6 families with weaker guidance (rejected: still a checklist), strip to 0 families (rejected: too little guidance for meaningful analysis)
**Date:** 2026-04-09

### D3: Per-stage skip replaces all-or-nothing repo skip in pull_github.py
**Decision:** Each pull stage (commits, prs, pr_reviews, pr_comments, trees, contributors) checks its own output file. PRs loaded from disk when skipped (needed for downstream reviews/comments).
**Rationale:** All-or-nothing skip had two failure modes: (a) original coarse skip trapped partial crashes, (b) fixed all-6-files check re-pulled completed stages on retry. Per-stage avoids both.
**Alternatives considered:** (a) Coarse skip on commits only (rejected: perma-skip bug), (b) All-or-nothing on 6 files (rejected: wastes API on retry)
**Date:** 2026-04-09

### D4: Security posture is a user choice via --security-posture flag, not a pipeline default
**Decision:** Add `--security-posture` (1-5) to `debate.py`. At 1-2, security findings are advisory-only and PM is the final arbiter. At 4-5, security can block. Default: 3 (balanced). Skills ask the user before running.
**Rationale:** The v3 velocity analysis spent significant pipeline capacity injecting security controls (egress policies, approval gates, credential rotation) into a speed-focused AI rollout recommendation. The user called this "a big waste" — the goal was going faster, not going safely. Security was over-rotating as the de facto final arbiter when PM should have been.
**Alternatives considered:** (a) Remove security persona entirely at low posture (rejected: still useful for advisory), (b) Hard-code posture per topic type (rejected: user should decide), (c) No change — always balanced (rejected: proven to waste pipeline capacity on wrong priorities)
**Date:** 2026-04-10
