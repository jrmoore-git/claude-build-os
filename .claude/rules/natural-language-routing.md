# Natural Language Routing

<!-- Enforced-By: hooks/hook-intent-router.py -->

**The primary interface is natural language, not slash commands.** Users should never need to memorize skill names. When a user describes what they want to do, route them to the right skill automatically.

## Routing Table

| User says something like... | Route to |
|---|---|
| "I want to build X", "new feature", "add support for" | `/think discover` (or `/think refine` if scope is already clear) |
| "What should we build?", "explore options", "what are our choices" | `/explore` |
| "Is this worth building?", "should we do this?", "evaluate this proposal" | `/challenge` (pre-plan go/no-go gate) |
| "Think bigger", "is this ambitious enough?", "expand scope" | `/elevate` |
| "Generate a PRD", "write requirements", "PRD from design doc", "create a PRD" | `/prd` |
| "Plan this", "how should we build it?", "implementation plan" | `/plan` |
| "Something broke", "this isn't working", "debug this", "why is X happening" | `/investigate` |
| "Review this", "check my code", "is this ready?" | `/review` |
| "Ship it", "deploy", "release this" | `/ship` |
| "Design this", "what should it look like", "UI review" | `/design` (infer mode from context) |
| "Improve this", "make this better", "polish this doc" | `/polish` |
| "Research X", "what do we know about", "find out about" | `/research` |
| "What happened?", "catch me up", "where are we?" | `/start` |
| "I'm done", "wrap up", "end session" | `/wrap` |
| "What can I do?", "help", "I'm lost", "how does this work" | `/guide` |
| "Is this plan solid?", "what could go wrong?", "devil's advocate" | `/pressure-test` (post-plan adversarial analysis) |
| "Log this decision", "capture this" | `/log` |
| "Update the docs", "sync docs" | `/sync` |
| "What is this?", "classify this", "where does this go?" | `/triage` |
| "Audit this codebase", "what's in here?" | `/audit` |

## Disambiguating /challenge vs /pressure-test

These two skills overlap in language ("is this a good idea?", "sanity check", "risks"). Route by **pipeline position**, not keywords:

| Artifact state | Default route | Rationale |
|---|---|---|
| Proposal exists, no challenge artifact | `/challenge` | Go/no-go gate hasn't fired yet — run it first |
| Challenge artifact exists, no plan | `/pressure-test` | Already gated — now stress-test the approach |
| Plan exists, no premortem | `/pressure-test --premortem` | Plan is concrete — assume it failed, write the post-mortem |
| Challenge + plan + premortem all exist | Ask the user | Everything's been run — clarify what they want revisited |
| No artifacts on disk | `/challenge` | First gate in the pipeline |

**Key distinction:** `/challenge` asks "should we build this?" (multi-model, gates `/plan`). `/pressure-test` asks "what could go wrong with this approach?" (single-model, adversarial). A user who already decided to build something doesn't need `/challenge` — they need `/pressure-test`.

The intent router hook (`hook-intent-router.py`) detects artifact state on disk and adjusts its suggestions accordingly. When the hook fires a dynamic suggestion, follow it unless the user's language clearly overrides.

## How to Route

Match intent, not keywords. Invoke directly — don't explain the skill first. When ambiguous, check artifact state before asking. Chain skills automatically when one outputs another's input. One suggestion per pattern per session.

## Proactive Routing — Pattern Recognition

| You observe... | Suggest |
|---|---|
| Same error or failure appears 2+ times | `/investigate` — "This keeps recurring. Want me to do a proper root-cause analysis?" |
| User retries the same approach after failure | `/investigate` — "Let me step back and diagnose why this keeps failing." |
| User describes unexpected behavior ("that's weird", "it used to work") | `/investigate` in drift mode — "Something changed. Want me to trace what diverged?" |
| User is making changes without a plan, touching 3+ files | `/plan` — "This is getting complex. Want me to write a plan before we go further?" |
| User asks "is this good enough?" or hesitates before shipping | `/review` — "Let me run a proper review before you ship." |
| Build succeeds but user seems uncertain about quality | `/pressure-test` — "Want me to try to break this?" |
| Proposal exists on disk but no challenge artifact | `/challenge` — "There's a proposal but it hasn't been challenged yet. Want me to run the go/no-go gate?" |
| Plan exists on disk but no premortem | `/pressure-test --premortem` — "Plan's written but hasn't been pressure-tested. Want me to run a pre-mortem?" |
| User says "is this a good idea?" and no challenge artifact exists | `/challenge` — route to go/no-go gate (see disambiguation table above) |
| User says "is this a good idea?" and plan already exists | `/pressure-test` — route to adversarial analysis (see disambiguation table above) |
| User mentions something they learned from a meeting or conversation | `/log` — "Want me to capture that as a decision/lesson?" |
| Session is getting long, lots of context consumed | `/wrap` — "We've covered a lot. Want to save state before we lose context?" |

**The rule:** if you see a pattern that a skill is designed to handle, suggest it once. Don't nag — one suggestion per pattern per session. If the user declines, drop it.
