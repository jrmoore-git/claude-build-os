---
debate_id: learning-velocity-tools-on
created: 2026-04-17T14:51:08-0700
mapping:
  A: gpt-5.4
personas:
  A: security
---
# learning-velocity-tools-on — Challenger Reviews

## Challenger A (security) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes `/healthcheck` is a safe place to auto-run `/investigate --claim`, but that crosses a trust boundary from a local maintenance scan into outbound LLM/API calls with repo content. The repo already has external-call tooling (`scripts/research.py` loads `PERPLEXITY_API_KEY` from env or `.env` and sends request bodies off-box), so adding automatic investigation during a routine scan materially increases unintended data exfiltration risk unless the exact prompt/input surface is constrained, redacted, and explicitly opt-in for networked verification. Risk of changing: a low-frequency housekeeping command now transmits lesson content and possibly surrounding repository context to third parties. Risk of not changing: stale lessons remain undetected unless manually investigated. Recommendation change: keep measurement local by default; gate auto-investigation behind an explicit flag or a “network-enabled” mode with prompt/input minimization.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: “Top 2-3 stalest lessons” is selected from `tasks/lessons.md`, which is effectively untrusted freeform content authored by humans. If that content is passed into `/investigate --claim` without strong delimiting, this creates a prompt-injection path from markdown into the model workflow. The recent state file already documents stale/wrong lessons in active governance (`docs/current-state.md`), which is exactly the kind of contaminated source that could poison an automated verifier. Risk of changing: malicious or simply malformed lesson text can steer the verifier, cause over-broad file reads, or bias recommendations. Risk of not changing: manual reviewers still face the same content quality issue, but the blast radius stays human-mediated. The implementation should treat lesson text as hostile input: extract only structured fields, quote them as data, and avoid sending arbitrary neighboring markdown/context.

3. [UNDER-ENGINEERED] [MATERIAL] [COST:MEDIUM]: The pruning idea depends on “has this hook fired in the last 30 days?”, but the current telemetry store is append-only, best-effort, and silent-on-error (`scripts/telemetry.py` swallows all exceptions). `hooks/hook-session-telemetry.py` is explicitly advisory/observer-only and also swallows failures. That means absence of hook-fire data is not reliable evidence that a hook is unused; it may just reflect logging gaps, local retention differences, branch isolation, or disabled hooks. Risk of changing: you create false pruning candidates from incomplete telemetry and may remove load-bearing controls. Risk of not changing: governance bloat remains unmeasured. Recommendation change: classify these as weak signals only, require a confidence indicator (“no observed fires in available telemetry”), and do not let this metric drive pruning without coverage checks or an explicit hook-enabledness audit.

4. [ASSUMPTION] [ADVISORY]: The proposal says “no new infrastructure,” but the repo already contains a purpose-built lesson event system (`scripts/lesson_events.py`) that computes velocity metrics from structured lifecycle events rather than git-log inference. An all-git implementation may be simpler initially, but it assumes commit history on `tasks/lessons.md` accurately reflects lesson lifecycle transitions; squashed commits, batch edits, and unrelated formatting changes weaken that signal. This does not block the proposal, but the decision should be explicit: simpler-but-noisier git math versus more accurate structured events.

5. [ALTERNATIVE] [ADVISORY]: For redundancy detection (“does a hook already enforce this?”), a purely semantic or heuristic comparison risks false positives that encourage weakening defenses. A safer first pass is narrower: detect explicit references/ownership links between rules and hooks, then surface only “possible overlap” rather than “redundant governance.” Risk of changing: reviewers over-trust an imprecise redundancy label. Risk of not changing: governance duplication remains manual to spot.

## Concessions
- The measurement-only first step is appropriately low-risk because it can remain entirely local and avoids introducing new secrets or services.
- The proposal correctly avoids auto-pruning; keeping pruning as a flag-only recommendation preserves a human decision point at a privilege boundary.
- Limiting verification to a small stale subset is a reasonable cost-control idea, though the quoted `/investigate --claim` cost/frequency remains ESTIMATED from the proposal rather than evidenced in code.

## Verdict
REVISE — the local metrics addition looks sound, but automatic investigation and telemetry-driven pruning need explicit controls for outbound-data exposure, prompt-injection handling, and weak-signal interpretation before they should be folded into `/healthcheck`.

---
