---
debate_id: learning-velocity-tools-off
created: 2026-04-17T14:50:51-0700
mapping:
  A: gpt-5.4
personas:
  A: security
---
# learning-velocity-tools-off — Challenger Reviews

## Challenger A (security) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes `git log` on `tasks/lessons.md` is a trustworthy proxy for “learning velocity,” but a single shared file is a weak measurement boundary: unrelated edits, formatting churn, bulk reordering, or archival cleanup can look like learning progress or regress. If these metrics are used to drive governance decisions, they can produce false confidence or false alarms. The risk of changing is bad decisions from noisy signals; the risk of not changing is continued blindness. Mitigation: define exactly which edit types count, ignore cosmetic diffs, and label the output as directional until validated.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: Auto-running `/investigate --claim` from `/healthcheck` introduces a new outbound execution path against content derived from lessons, which are effectively semi-trusted/untrusted text. If lesson text is passed into prompts for the panel call, this creates a prompt-injection and data-exfiltration surface that does not exist in a purely local metric scan. The proposal does not state any sanitization, scope restriction, or redaction before sending claims to external models. Risk of changing: stale or malicious lesson content could cause leakage of repo/context or manipulate verification. Risk of not changing: stale lessons remain unverified. Add explicit prompt isolation/redaction rules and limit what repo context `/investigate` may include.

3. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The “top 2-3 stalest” heuristic assumes age is the best predictor of poisoning risk, but your own examples include structurally wrong lessons, not merely old ones. A recently edited but incorrect lesson would evade this check, while an old but harmless lesson gets priority. This does not invalidate scheduled verification, but it changes the recommendation: age alone is insufficient as the trigger. Add at least one additional signal such as recent references, recurrence count, contradiction with current files, or “resolved but still active” state.

4. [UNDER-ENGINEERED] [ADVISORY]: The hook-pruning signal “has this fired in the last 30 days?” is not, by itself, evidence that a hook is unnecessary. Some hooks exist precisely to prevent rare, high-severity failures; low firing frequency may mean they are effective or the risky path is uncommon. Treat this only as a weak review hint, not an “earning its keep” metric.

5. [ASSUMPTION] [ADVISORY]: “Does a hook already enforce this?” is a semantic equivalence question, not a string-matching one. A rule can still carry intent, rationale, or preconditions that the hook cannot express. If implemented naively, this check will generate noisy “redundant governance” candidates and waste review time.

6. [ALTERNATIVE] [ADVISORY]: The staged rollout in “Simplest Version” is sound, but the proposal could be sharper by explicitly gating phases 2 and 3 on observed usefulness of phase-1 metrics plus verified false-positive rate from a few manual dry runs. That reduces the risk of automating a bad heuristic.

## Concessions
- It correctly targets a real gap: the current system captures failures and governance artifacts but lacks a feedback loop on whether they reduce recurrence.
- It keeps pruning human-in-the-loop, which avoids unsafe automatic deletion of controls.
- It reuses `/healthcheck` instead of introducing new infrastructure, limiting operational and security complexity.

## Verdict
REVISE with one-sentence rationale: the direction is good, but scheduled verification needs explicit prompt/data-boundary safeguards and the proposed metrics/triggers need tighter validation so noisy heuristics don’t drive governance decisions.

---
