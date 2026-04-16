---
mode: pressure-test
created: 2026-04-16T11:08:46-0700
model: gpt-5.4
prompt_version: 1
---
# Pressure-Test

## The Premise Is Wrong Because...

The strongest version of “you’re solving the wrong problem” is: this is not primarily a search-path bug, it’s a reliability-architecture bug. Session 18 failed because the system let external models infer absence from incomplete evidence, then let a judge amplify that error with high confidence. Expanding file sets fixes one concrete blind spot, but the deeper issue is that your verifier layer is too open-ended for factual questions that should be answered deterministically.

The better question is not “how do we add hooks/ to debate_tools.py?” It’s “which factual claims should never depend on model-led discovery in the first place?” If the answer is “existence of directories, files, functions, rules, docs,” then the right direction is a canonical repo-manifest or indexed verifier API, not continued patching of search surfaces one directory at a time.

That said, if the decision is about this proposal specifically, the key question is whether this patch meaningfully improves outcomes now without deepening the wrong abstraction.

## Core Assumptions

First, this assumes the failure was mainly caused by missing search coverage rather than bad challenger reasoning. It fails if models continue to make “not found therefore does not exist” claims even after broader access, because they still search poorly or stop early. The signal today is mixed: both Opus and GPT-5.4 converged on the same false claim after constrained tools, which suggests tool design mattered a lot.

Second, this assumes broader discovery tools will improve accuracy more than they increase noise. It fails if adding hooks, tests, docs, rules, and list_files just gives models more places to wander, raising call volume and token use without improving judgment. The signal today is the 54-call thrash: the current models already over-search when uncertain, so more surface area could either help or worsen that tendency.

Third, this assumes your deny-by-default security posture still holds after expanding readable/searchable areas. It fails if docs or rules contain governance plans, internal rationale, or operational details you’re comfortable passing in prompts but not systematically exposing to third-party models on every challenge. The signal today is that you already accept snippet exposure for hooks and tests, which supports the proposal, but docs/rules are a category expansion, not just a consistency fix.

## Demand-Side Forces

The push is obvious: users will abandon or distrust /challenge if it produces confident factual errors, wastes 20 minutes, and drives wrong recommendations. Reliability, not capability, is the pain.

The pull is also clear: this proposal promises a more grounded debate where challengers can actually inspect the relevant repo areas and discover what exists before making claims.

The anxiety is that each added tool and directory makes the system feel less bounded: more external exposure, more complexity, more chances for strange failure modes. Users may fear they’re building a brittle mini-agent platform instead of a dependable verifier.

The habit is that people are used to accepting “LLM review” as probabilistic and compensating manually. Even when they complain, they often keep using familiar workflows and mentally discount the bad outputs rather than switching architectures.

The proposal is mostly ignoring habit and a bit of anxiety. It assumes fixing the obvious gap is enough to restore trust. But users who got burned by a 0.98-confidence falsehood may not care that hooks are now searchable; they’ll care whether the system is now structurally prevented from making that class of mistake.

## Competitive Response

If this works, platform vendors will not copy “debate_tools.py.” They’ll move toward native repository-grounded verification: built-in codebase search, project maps, and claim-checking tools inside their coding agents. Anthropic, OpenAI, and Google are all better positioned to bundle deterministic repo introspection directly into their agents, with lower latency and no external orchestration.

The nearest competitor response is faster: governance or coding-agent frameworks will adopt a simpler pattern like indexed repo manifests, symbol maps, or policy-aware retrieval rather than cross-model tool debates. If they can say “our verifier never asks a model to guess whether hooks exist; it queries an index,” that’s a stronger product claim.

Does the thesis survive? As a tactical patch, yes. As a strategic differentiator, no. “We exposed more directories to challenger models” is not durable once platform-native repo reasoning improves.

## Counter-Thesis

I’d pursue “deterministic repo index first” instead.

Instead of expanding model-driven discovery, build a canonical repository manifest generated locally before any debate: directories, files, exported functions, hooks present, rules present, docs present. Then let challengers query that index, and reserve read_file_snippet for interpretation, not existence checks.

Why this is better: it attacks the actual failure mode — false absence claims from incomplete search — at the root. It also scales better than adding more file sets over time, lowers tool-call thrash, and gives the judge harder evidence to reason from. In other words, move factual verification down into deterministic preprocessing and keep model debate for interpretation and tradeoffs.

## Timing

You should do something now, because the current behavior is actively undermining trust and wasting time. The window closing is credibility: once users believe /challenge is theatrically rigorous but factually brittle, recovery gets harder.

But the full strategic window for a larger architecture shift is also open now. You’ve already identified deterministic checks as superior for verifiable facts. That’s a clue not to stop at a surface patch.

So: fix the inconsistency immediately, but don’t confuse that with completing the job. I would not wait on the patch. I would wait on broader expansion of model-readable surfaces until you decide whether the real architecture is indexed verification.

## My Honest Take

If this were my decision, I would approve a narrower version of this proposal now and pair it with a follow-on redesign.

Specifically: add hooks and tests to the searchable file sets immediately, because that is a clear inconsistency and directly addresses the proven failure. I would be more cautious about adding docs and rules in the same move unless you’re sure they belong in the same trust boundary. And I would only add list_files if it is framed as a temporary bridge, not the foundation.

Then I’d make the next priority a deterministic repo manifest or symbol index and update debate/judge behavior so absence claims require hard evidence from that layer. That is the strategic fix.

So the core direction of “close the discovery gap” is sound. The core direction of “solve this by giving models broader search tools” is only partially sound. Use this patch as triage, not as the thesis.