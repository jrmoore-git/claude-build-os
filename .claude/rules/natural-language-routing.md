# Natural Language Routing

**The primary interface is natural language, not slash commands.** Users should never need to memorize skill names. When a user describes what they want to do, route them to the right skill automatically.

## Routing Table

| User says something like... | Route to |
|---|---|
| "I want to build X", "new feature", "add support for" | `/think discover` (or `/think refine` if scope is already clear) |
| "What should we build?", "explore options", "what are our choices" | `/explore` |
| "Is this worth building?", "should we do this?", "evaluate this proposal" | `/challenge` |
| "Think bigger", "is this ambitious enough?", "expand scope" | `/elevate` |
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
| "Is this plan solid?", "what could go wrong?", "devil's advocate" | `/pressure-test` |
| "Log this decision", "capture this" | `/log` |
| "Update the docs", "sync docs" | `/sync` |
| "What is this?", "classify this", "where does this go?" | `/triage` |
| "Audit this codebase", "what's in here?" | `/audit` |

## How to Route

Match intent, not keywords. Invoke directly — don't explain the skill first. When ambiguous, ask one question. Chain skills automatically when one outputs another's input. One suggestion per pattern per session.

## Proactive Routing — Pattern Recognition

| You observe... | Suggest |
|---|---|
| Same error or failure appears 2+ times | `/investigate` — "This keeps recurring. Want me to do a proper root-cause analysis?" |
| User retries the same approach after failure | `/investigate` — "Let me step back and diagnose why this keeps failing." |
| User describes unexpected behavior ("that's weird", "it used to work") | `/investigate` in drift mode — "Something changed. Want me to trace what diverged?" |
| User is making changes without a plan, touching 3+ files | `/plan` — "This is getting complex. Want me to write a plan before we go further?" |
| User asks "is this good enough?" or hesitates before shipping | `/review` — "Let me run a proper review before you ship." |
| Build succeeds but user seems uncertain about quality | `/pressure-test` — "Want me to try to break this?" |
| User mentions something they learned from a meeting or conversation | `/log` — "Want me to capture that as a decision/lesson?" |
| Session is getting long, lots of context consumed | `/wrap` — "We've covered a lot. Want to save state before we lose context?" |

**The rule:** if you see a pattern that a skill is designed to handle, suggest it once. Don't nag — one suggestion per pattern per session. If the user declines, drop it.
