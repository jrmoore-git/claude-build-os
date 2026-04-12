---
debate_id: gstack-integration-findings
created: 2026-04-11T21:02:36-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# gstack-integration-findings — Challenger Reviews

## Challenger A — Challenges
I have sufficient data. Here's my review.

---

## Challenges

1. **ASSUMPTION [MATERIAL]**: The proposal claims "3 gstack skills already symlinked into BuildOS (/browse, /connect-chrome, /setup-browser-cookies)" — I cannot verify this. Searching the skills file set for `connect-chrome`, `setup-browser`, and `gstack` all return zero matches. Only `browse` (2 matches) is present. If the symlink precedent doesn't actually exist, the "adopt complementary skills via symlink" tier (Tier 2) is not an extension of an established pattern but a new integration mechanism that needs its own justification and testing.

2. **UNDER-ENGINEERED [MATERIAL]**: `browse.sh` as a ~20-line wrapper around a 58MB compiled binary in `~/.claude/skills/gstack/browse/dist/browse` creates a hard dependency on an external, unversioned, user-home-directory path that BuildOS doesn't control. There is no proposal for:
   - **Version pinning**: How does BuildOS know which gstack browse binary version it's wrapping? The binary could change semantics between 0.14.5 and 0.16.3.
   - **Existence checking**: What happens when the binary isn't installed (CI, new machine, teammate onboarding)?
   - **Interface contract**: What arguments does the binary accept? What output format does it produce? A 20-line wrapper with no contract documentation is a 20-line coupling to an undocumented external API.
   
   Risk of NOT fixing: 3 `/design` modes remain broken. This is real. But the fix needs at minimum a version check and a graceful failure path.

3. **RISK [MATERIAL]**: Tier 3 (version upgrade 0.14.5 → 0.16.3) is sequenced *after* browse.sh is built and tested against 0.14.5. But the proposal doesn't address what happens if the browse binary's CLI interface changes between versions. You'd be building browse.sh against 0.14.5, then upgrading the binary underneath it. The proposal should either: (a) build against 0.16.3 from the start, or (b) specify the interface contract that must be stable across versions.

4. **ASSUMPTION [ADVISORY]**: The proposal states "gstack equivalents are weaker (single-model vs cross-model debate)" as justification for Tier 4 (keep BuildOS versions). This is plausible given debate.py's 3674-line multi-model pipeline, but the claim about gstack's capabilities is unverifiable from this codebase. If gstack's review skills improve in future versions, the "keep BuildOS versions" decision should be re-evaluated — but the proposal treats it as permanent.

5. **RISK [ADVISORY]**: Tier 2 proposes symlinks for `/benchmark`, `/canary`, `/investigate` — none of which currently exist in the skills directory (verified: zero matches for all three). These are described as filling "real gaps in the post-`/ship` pipeline," but there's no specification of what these skills actually do, what they depend on, or how they interact with BuildOS's existing `/ship` skill. Symlinks to external skills are low-cost to add but create invisible dependencies that break silently when the upstream changes.

6. **OVER-ENGINEERED [ADVISORY]**: The four-tier structure (finish → adopt → upgrade → keep) is a reasonable mental model but may be over-formalized for what amounts to: (a) write one shell script, (b) maybe symlink some stuff later. Tiers 2-4 are contingent on Tier 1 working and could be deferred to separate proposals rather than pre-committed here.

## Concessions

1. **The core problem is real and well-diagnosed.** `scripts/browse.sh` doesn't exist (verified), the design skill references it (verified), and 3 modes are therefore non-functional. This is a genuine broken-window that should be fixed.

2. **The "simplest version" framing is correct.** Starting with browse.sh and validating `/design review` against a real page before expanding scope is the right sequencing. The proposal resists the temptation to do everything at once.

3. **The non-goals are well-chosen.** Not forking gstack, not replacing BuildOS skills, not building a competing browser — these boundaries prevent the most likely failure modes of framework integration.

## Verdict

**REVISE** — The core fix (browse.sh) is clearly needed and low-risk, but the proposal must address the hard dependency on an unversioned external binary: add existence/version checking to browse.sh, define the CLI contract being wrapped, and either build against 0.16.3 from the start or document the stable interface assumption. Tiers 2-4 should be deferred to separate proposals contingent on Tier 1 success rather than pre-approved here.

---

## Challenger B — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL]: The proposal adds a new trust boundary by wrapping BuildOS skill inputs into an external browser binary, but it does not specify any guardrails on URL handling. If `scripts/browse.sh` passes arbitrary arguments from `/design` directly into gstack's browser, you risk SSRF/local file access patterns (`file://`, localhost/internal admin panels, cloud metadata endpoints) and accidental browsing with authenticated cookies. This matters because the stated plan explicitly enables visual review/consult flows on real pages, and gstack already includes browser/cookie-related skills. Minimum guardrails should include scheme allowlisting (`http/https`), explicit denylist for localhost/private RFC1918/link-local/meta-data targets, and careful handling of cookie-bearing browser profiles.

2. [ASSUMPTION] [MATERIAL]: The symlink strategy assumes gstack skills are safe to expose inside BuildOS without reviewing how they handle secrets, external network calls, logs, and browser state. I verified the proposal’s target skills (`/benchmark`, `/canary`, `/investigate`) are not already present in BuildOS skills, but the proposal does not verify what those imported skills do with production URLs, telemetry, stack traces, or deployment credentials. Since these are post-deploy/monitoring/debugging workflows, the main security risk is data exfiltration to logs or external services and privilege creep from “read production status” into “act on production systems.”

3. [UNDER-ENGINEERED] [ADVISORY]: Version-upgrading gstack after the wrapper works is operationally reasonable, but from a security perspective the proposal should pin an exact version and define an update/rollback mechanism instead of “0.14.5 → 0.16.3+”. The “+” leaves behavior open-ended, and browser/network-interception capabilities increase the blast radius if a later release changes defaults. This is advisory because pinning is cheap and doesn’t need to block the fast path.

4. [ASSUMPTION] [ADVISORY]: The proposal states concrete baseline failures for `/design` modes, and I verified `skills/design/SKILL.md` references `scripts/browse.sh` and includes `bash scripts/browse.sh goto`. However, the operational claims about installed gstack version, binary location/size, run frequency, and number of active/symlinked skills were not verified with available tools, so those quantitative/asset-inventory details should be treated as SPECULATIVE and not used to justify broader integration scope without confirmation.

5. [ALTERNATIVE] [ADVISORY]: A safer fast path is to ship only tier 1 first: implement `scripts/browse.sh` as a tightly constrained adapter for the specific `/design` use cases, then defer symlinking `/benchmark`, `/canary`, and `/investigate` until each imported skill is reviewed for credential use, logging, and external calls. This still fixes the verified current failure while limiting new trust and exfiltration surfaces.

## Concessions
- The proposal correctly identifies a real, verified integration gap: `skills/design/SKILL.md` references `scripts/browse.sh`, and no such script currently exists in `scripts`.
- Keeping BuildOS-native review/planning/challenge workflows avoids replacing stronger internal controls with weaker overlapping tooling.
- The staged approach reduces risk versus a wholesale migration, especially by avoiding gstack source forks and custom browser runtime work.

## Verdict
REVISE — ship the thin `browse.sh` wrapper first, but add minimal URL/cookie guardrails and defer symlinking monitoring/debug skills until their secret handling and data-exposure behavior are reviewed.

---

## Challenger C — Challenges
## Challenges
1. [OVER-ENGINEERED] [MATERIAL]: Creating a `scripts/browse.sh` wrapper [ESTIMATED: assumes ~20 lines of basic argument passing] is redundant. The proposal notes that the gstack `/browse` skill is *already* symlinked into BuildOS. The `/design` skill should be refactored to compose with the existing `/browse` skill rather than wrapping the underlying compiled binary with a custom shell script. This eliminates unnecessary glue code and reduces the maintenance surface.
2. [RISK] [MATERIAL]: Coupling the gstack version upgrade (0.14.5 → 0.16.3) with the initial browser integration (Step 3) introduces severe regression risk. If the newer gstack version alters the browser binary's CLI arguments or output format, the newly fixed `/design` modes will immediately break. The upgrade must be a separate, isolated validation step.
3. [ASSUMPTION] [ADVISORY]: Adopting `/canary`, `/benchmark`, and `/investigate` via symlink assumes developers will organically discover and use these post-deploy tools. Without hooking these into the successful execution of `/ship` or existing CI/CD pipelines, they risk becoming unused shelfware that adds clutter rather than value.

## Concessions
1. Fixing the 3 broken modes in the `/design` skill restores immediate, tangible user value for visual tasks.
2. Drawing a hard boundary between BuildOS's strengths (multi-model debate, planning) and gstack's strengths (browser runtime, data scraping) avoids massive duplication of effort.
3. Relying on an externally maintained headless browser binary (~58MB compiled, [EVIDENCED]) is vastly superior to attempting to build and maintain a custom native browser tool.

## Verdict
REVISE to update the `/design` skill to directly utilize the already-symlinked `/browse` skill instead of building a redundant shell wrapper, and isolate the gstack version upgrade into a separate deployment phase.

---
