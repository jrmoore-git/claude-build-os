---
persona: security
model: gpt-5.4
threshold: 5/5 bidirectional
verdict: DECLINE
---

# Security Persona Dual-Mode Analysis

## Per-Proposal Tagging

### Proposal: autobuild

**Tools-off MATERIAL findings:**
- OFF-1: Plan artifacts and `verification_commands` are treated as trusted but are untrusted instruction-bearing data; injection boundary for shell commands / paths / prompt-injection steering the build agent.
- OFF-2: "Zero-risk because human PR review" is wrong — the build loop executes code/tests before review; secrets can leak via test output, network calls, telemetry, malicious postinstall scripts. Needs runtime sandbox posture (no prod creds, restricted network, scrubbed env).
- OFF-3: Escalation trigger #4 ("check edits against `surfaces_affected`") lacks concrete enforcement — an agent can still modify non-listed files before escalation or via indirect effects (generated files, lockfiles). Needs pre-write or diff-checked enforcement.

**Tools-on MATERIAL findings:**
- ON-1: Cites `hooks/hook-read-before-edit.py` lines 59-83 + `config/protected-paths.json` — the read-before-edit hook only protects configured sensitive paths and exempts `tasks/`, `docs/`, `tests/`, `config/`, `stores/`. No pre-write scope gate exists tied to the active plan artifact; autonomous mode would rely on model self-policing.
- ON-2: Cites `config/protected-paths.json` lines 17-23 — enforcement only requires frontmatter fields exist, no hardened parser or command allowlist for plan-derived commands. Shell-injection and prompt-injection boundary.
- ON-3: Cites `hooks/hook-agent-isolation.py` lines 4-15 — hook "warns (non-blocking) when worktree agents receive absolute repo paths in their prompts, which bypasses isolation entirely." Warning-only is insufficient for autonomous parallel builds.

**Classification table:**

| Finding | Mode | Classification | Partner (if shared) |
|---|---|---|---|
| OFF-1 | tools-off | shared | ON-2 (same defect: untrusted plan text becomes executable commands) |
| OFF-2 | tools-off | **tools-off-exclusive** | runtime sandbox / secret leakage during build execution; tools-on has no MATERIAL equivalent (ON-5 is ADVISORY) |
| OFF-3 | tools-off | shared | ON-1 (same defect: scope containment lacks pre-write enforcement) |
| ON-1 | tools-on | shared | OFF-3 |
| ON-2 | tools-on | shared | OFF-1 |
| ON-3 | tools-on | **tools-on-exclusive** | absolute-path leakage to worktree subagents; tools-off only touched this as ADVISORY (OFF-4) |

**Mode-exclusive count:** tools-on 1 | tools-off 1
**BIDIRECTIONAL:** YES
**Reason:** ON-3 cites a specific warn-only hook weakness requiring code grep; OFF-2 raises runtime-sandbox/secret-scrubbing concern not appearing in tools-on MATERIAL list.

---

### Proposal: explore-intake

**Tools-off MATERIAL findings:**
- OFF-1: User-supplied intake answers/documents become untrusted data embedded into downstream prompts; prompt-injection can elevate malicious content into high-salience slots (PROBLEM, THE TENSION, ASSUMPTIONS TO CHALLENGE). Needs explicit "data not instructions" rule.
- OFF-2: "Preserve the user's exact words for The Tension" increases injection risk because exact wording is given the most prominent semantic position. Needs sanitization/neutralization of instruction-like text before insertion into prompt-control regions.

**Tools-on MATERIAL findings:**
- ON-1: Cites `scripts/debate_explore.py` — `--context` is unvalidated free-form string, spliced via `replace("{context}", context_block)`. Without delimiting / "treat as user-provided context, not instructions," malicious or messy answers can override explore behavior. Same prompt-injection defect, code-grounded.
- ON-2: Sensitive-data exfiltration — Slot 4/5 questions explicitly encourage users to reveal "the unsaid," political constraints, personnel dynamics. `cmd_explore` passes context straight into prompts sent to external LLM provider. Needs redaction/minimization before context composition, not just a token budget. Data egress defect, not injection.
- ON-3: Proposal says update `scripts/debate.py` but `explore` logic is actually in `scripts/debate_explore.py` (`from debate_explore import cmd_explore`). Wrong integration point — changes scoped only to prompt files + `debate.py` may not land in the execution path.

**Classification table:**

| Finding | Mode | Classification | Partner (if shared) |
|---|---|---|---|
| OFF-1 | tools-off | shared | ON-1 (same defect: untrusted user text promoted into prompt-control regions) |
| OFF-2 | tools-off | shared | ON-1 (same defect and same mitigation family — delimiting / "data not instructions" treatment of exact wording) |
| ON-1 | tools-on | shared | OFF-1 / OFF-2 |
| ON-2 | tools-on | **tools-on-exclusive** | sensitive-data exfiltration via Slot 4/5 sent to external LLM provider; tools-off has no MATERIAL finding about redaction/minimization of sensitive content |
| ON-3 | tools-on | **tools-on-exclusive** | wrong integration point (`scripts/debate_explore.py` vs `scripts/debate.py`); only findable via grep |

**Mode-exclusive count:** tools-on 2 | tools-off 0
**BIDIRECTIONAL:** NO
**Reason:** No tools-off MATERIAL finding raises a defect absent from tools-on. Both tools-off items collapse into the single prompt-injection defect that tools-on ON-1 also catches (with code evidence). Tools-off raised no data-exfiltration-of-sensitive-disclosures finding and no misdirected-integration-point finding.

---

### Proposal: learning-velocity

**Tools-off MATERIAL findings:**
- OFF-1: `git log` on `tasks/lessons.md` is a weak/noisy measurement boundary — unrelated edits, formatting churn, bulk reordering, archival cleanup look like learning progress/regress. Noisy signals → false confidence or false alarms in governance decisions.
- OFF-2: Auto-running `/investigate --claim` from `/healthcheck` creates prompt-injection + data-exfiltration surface on lesson content passed to external models. No sanitization/scope restriction/redaction.
- OFF-3: "Top 2-3 stalest" age-only heuristic insufficient — a recently edited but structurally wrong lesson evades check; old-but-harmless lessons get priority. Needs additional signal (recent references, recurrence, contradiction).

**Tools-on MATERIAL findings:**
- ON-1: Cites `scripts/research.py` (loads `PERPLEXITY_API_KEY`, sends request bodies off-box) — auto `/investigate` during routine scan transmits lesson content and surrounding repo context to third parties. Needs explicit opt-in networked-verification flag.
- ON-2: Lessons file is untrusted freeform text; prompt-injection path from markdown into `/investigate --claim` workflow. Cites `docs/current-state.md` showing stale/wrong lessons already in active governance — a contaminated source that could poison automated verifier.
- ON-3: Cites `scripts/telemetry.py` (swallows all exceptions, silent-on-error) + `hooks/hook-session-telemetry.py` (advisory/observer-only, swallows failures) — "has this hook fired in 30 days?" is unreliable pruning metric because telemetry absence may reflect logging gaps, retention differences, branch isolation, or disabled hooks. Creates false pruning candidates that may remove load-bearing controls.

**Classification table:**

| Finding | Mode | Classification | Partner (if shared) |
|---|---|---|---|
| OFF-1 | tools-off | **tools-off-exclusive** | git-log learning-velocity metric is noisy; tools-on only touches git-math tradeoff as ADVISORY (ON-4) |
| OFF-2 | tools-off | shared | ON-1 + ON-2 (same two defects: exfiltration + prompt-injection via auto-investigate on lessons) |
| OFF-3 | tools-off | **tools-off-exclusive** | age-only heuristic misses recently-edited-but-wrong lessons; tools-on has no MATERIAL equivalent (ON-3 is about hook-firing telemetry, a different metric entirely) |
| ON-1 | tools-on | shared | OFF-2 (exfiltration half) |
| ON-2 | tools-on | shared | OFF-2 (prompt-injection half) |
| ON-3 | tools-on | **tools-on-exclusive** | telemetry unreliability (swallowed exceptions) undermines hook-firing pruning signal; tools-off's hook-pruning concern (OFF-4) is ADVISORY |

**Mode-exclusive count:** tools-on 1 | tools-off 2
**BIDIRECTIONAL:** YES
**Reason:** ON-3 depends on reading `scripts/telemetry.py` and the session-telemetry hook to prove silent-failure behavior; OFF-1 and OFF-3 raise metric-quality concerns (git-log noise, age-only heuristic) not appearing as MATERIAL in tools-on.

---

### Proposal: streamline-rules

**Tools-off MATERIAL findings:**
- OFF-1: Cross-file references preserve behavior only if runtime always loads linked rule files with equal priority and visibility. If surfaces are conditionally loaded / summarized / truncated, "see X" weakens enforcement. Needs explicit verification of loading semantics for `CLAUDE.md` vs `.claude/rules/*.md` vs `.claude/rules/reference/*.md`.
- OFF-2: Phase 2 moves operationally important directives (verify before done, fix-forward, documentation timing) out of always-loaded / high-salience locations → prompt-instruction dilution risk even if content technically still exists. Reduced compliance via indirection. Safer to keep terse normative statements top-level, deduplicate only explanatory text.

**Tools-on MATERIAL findings:**
- ON-1: Same load-scope concern, but cites `.claude/rules/security.md` frontmatter globs specifically and names specific critical rules (secret redaction, shell argument leakage, untrusted-text handling, LLM boundary). Evidence-grounded version of OFF-1.
- ON-2: Phase 1 changes normative behavior, not just wording. Example: "update decisions.md after material decisions" → "before implementing material decisions" affects sequencing. Earlier documentation can increase exposure of unreviewed plans, security-sensitive implementation details, or credentials-adjacent context in `tasks/decisions.md` / `tasks/session-log.md` / handoff artifacts. Needs explicit definition of what must be documented early vs kept out of durable artifacts (secrets, exploits, raw untrusted content).
- ON-3: No regression method to prove semantic equivalence after compression. Needs diff-driven validation — enumerate every imperative/prohibition in source files, map each to canonical destination, fail change if any directive is lost, softened, or moved out of scope.

**Classification table:**

| Finding | Mode | Classification | Partner (if shared) |
|---|---|---|---|
| OFF-1 | tools-off | shared | ON-1 (same defect: runtime loading semantics for cross-file references; ON-1 adds code-grounded citation) |
| OFF-2 | tools-off | **tools-off-exclusive** | Phase 2 dilution of specific always-loaded directives (verify-before-done, fix-forward) via indirection; tools-on ON-2 is about Phase 1 sequencing/exposure (different phase, different threat model: earlier documentation exposing secrets vs indirection weakening compliance) |
| ON-1 | tools-on | shared | OFF-1 |
| ON-2 | tools-on | **tools-on-exclusive** | Phase 1 sequencing change (after → before implementing) exposes credentials-adjacent context earlier; tools-off has no MATERIAL finding about timing/exposure of durable artifacts |
| ON-3 | tools-on | **tools-on-exclusive** | diff-driven regression method to prove semantic equivalence; tools-off has no MATERIAL finding requiring enumeration of every imperative/prohibition |

**Mode-exclusive count:** tools-on 2 | tools-off 1
**BIDIRECTIONAL:** YES
**Reason:** ON-2 and ON-3 raise exposure-timing and regression-methodology defects absent from tools-off MATERIAL. OFF-2 raises Phase 2 indirection-dilution concern for specific directives (verify-before-done, fix-forward) absent from tools-on MATERIAL.

---

### Proposal: litellm-fallback

**Tools-off MATERIAL findings:**
- OFF-1: `ANTHROPIC_API_KEY` availability assumed because "user is running Claude Code," but trust boundary not verified — Claude Code access does not guarantee child Python process inherits usable key. Needs explicit preflight check + deterministic error message.
- OFF-2: Trigger condition "connection refused / timeout to LiteLLM proxy" too narrow — misclassifies other failures (reachable-but-unhealthy, misconfigured, 401/403/5xx, wrong routing). Narrow fallback leaves users hard-failing; broad fallback masks real auth/config issues. Needs bounded fallback policy distinguishing "proxy unavailable" vs "proxy reachable but broken."
- OFF-3: Direct Anthropic fallback changes data egress path from `localhost:4000` to external API endpoint — trust-boundary shift with privacy implications (prompts/code/artifacts users expected to traverse only local proxy now go straight to Anthropic). One-line stderr message insufficient; needs explicit disclosure that prompts are being sent directly to Anthropic + opt-out env/config flag.

**Tools-on MATERIAL findings:**
- ON-1: Cites `scripts/llm_client.py:193-207, 572-594` — `_dispatch()` only falls back on `_is_connection_refused(exc)`; `_is_retryable()` explicitly treats `TimeoutError` and `APITimeoutError` as non-retryable and does not route them into fallback. Hung/overloaded proxy still fails `/review` instead of degrading gracefully. Evidence-grounded subset of the "trigger too narrow" family.
- ON-2: Cites `scripts/llm_client.py:585-590` — proposal claims "print one line to stderr" but implemented warning is two lines; no test coverage asserts the transparency message or `degraded_single_model` marker (test search found no match). Downstream UX / operator expectations unpinned; future edits could silently remove or change the disclosure.

**Classification table:**

| Finding | Mode | Classification | Partner (if shared) |
|---|---|---|---|
| OFF-1 | tools-off | **tools-off-exclusive** | ANTHROPIC_API_KEY availability preflight; tools-on has no MATERIAL finding about secret-availability verification |
| OFF-2 | tools-off | shared | ON-1 (ON-1 is the evidenced/specific version: timeout explicitly non-retryable) |
| OFF-3 | tools-off | **tools-off-exclusive** | data-egress-path shift from local proxy to external endpoint → privacy/consent/opt-out; tools-on ON-2 is about disclosure format/test coverage (different defect: reliability of the disclosure mechanism vs the consent/egress-path concern itself) |
| ON-1 | tools-on | shared | OFF-2 |
| ON-2 | tools-on | **tools-on-exclusive** | warning format mismatch (two lines vs one) + missing test coverage for `degraded_single_model` marker; only findable via code + test grep |

**Mode-exclusive count:** tools-on 1 | tools-off 2
**BIDIRECTIONAL:** YES
**Reason:** ON-2 requires reading actual implementation and searching tests; OFF-1 raises API-key-availability preflight concern and OFF-3 raises egress-path consent/opt-out concern, neither appearing as MATERIAL in tools-on.

---

## Cross-Proposal Summary Table

| Proposal | Tools-off MATERIAL | Tools-on MATERIAL | tools-on-exclusive | tools-off-exclusive | BIDIRECTIONAL |
|---|---|---|---|---|---|
| autobuild | 3 | 3 | 1 (ON-3) | 1 (OFF-2) | YES |
| explore-intake | 2 | 3 | 2 (ON-2, ON-3) | 0 | **NO** |
| learning-velocity | 3 | 3 | 1 (ON-3) | 2 (OFF-1, OFF-3) | YES |
| streamline-rules | 2 | 3 | 2 (ON-2, ON-3) | 1 (OFF-2) | YES |
| litellm-fallback | 3 | 2 | 1 (ON-2) | 2 (OFF-1, OFF-3) | YES |

**BIDIRECTIONAL total:** 4 / 5

## Persona Verdict

**VERDICT: DECLINE** — Only 4/5 proposals show MATERIAL mode-exclusive findings in BOTH directions. Pre-committed threshold was 5/5; explore-intake fails because no tools-off MATERIAL finding raises a defect absent from tools-on.

## Notes

- **Where dual-mode won:** tools-on consistently adds code-grounded specificity (line numbers, specific hook weaknesses, wrong integration points, test-coverage gaps). autobuild ON-3, learning-velocity ON-3, streamline-rules ON-3, litellm-fallback ON-2, explore-intake ON-3 are all findings that require reading actual source and would be near-impossible to produce from proposal alone.
- **Where tools-off held its own:** OFF-mode consistently raises threat-model / trust-boundary concerns that don't require code inspection — sandbox isolation (autobuild OFF-2), signal quality (learning-velocity OFF-1 / OFF-3), consent/egress path (litellm-fallback OFF-1 / OFF-3), dilution-via-indirection (streamline-rules OFF-2). These are conceptual/policy-level critiques that don't depend on what's already shipped.
- **Explore-intake failure analysis:** The tools-off security review collapsed into a single prompt-injection concern (with two related facets about prominence/exact-words). Tools-on raised two defects that tools-off missed: sensitive-data exfiltration via Slot 4/5 (conceptual — could have been raised tools-off but wasn't), and wrong integration point (requires grep). The exfiltration-via-Slot-4/5 finding in particular was a threat-model gap tools-off *could* have caught but didn't — its token budget went to reiterating the injection concern twice.
- **Ambiguities resolved conservatively:**
  - autobuild OFF-1 vs ON-2: both about shell-injection through plan-derived commands → SHARED (same defect, different evidence depth).
  - autobuild OFF-3 vs ON-1: both about pre-write scope enforcement → SHARED.
  - litellm-fallback OFF-3 vs ON-2: treated as different defects — OFF-3 is about the privacy/egress-path consent decision; ON-2 is about whether the disclosure mechanism is reliably implemented. Both relate to disclosure but address distinct failure modes.
  - streamline-rules OFF-2 vs ON-2: treated as different defects — OFF-2 is Phase 2 indirection dilution for specific rules; ON-2 is Phase 1 sequencing change that exposes secrets earlier. Different phases, different threat models.
- **Pre-committed threshold discipline:** 4/5 is close but not 5/5. Do not loosen.
