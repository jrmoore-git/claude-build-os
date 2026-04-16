---
topic: context-packet-anchors
created: 2026-04-15
---
# Dynamic Evaluation Anchors for debate.py

## Project Context
BuildOS is a governance and quality framework for Claude Code. Its core engine is `scripts/debate.py` (4,136 lines), which runs cross-model challenge, review, judge, refine, explore, and pressure-test pipelines. Three models (Claude Opus, GPT-5.4, Gemini 3.1 Pro) evaluate proposals through persona-framed prompts (architect, security, PM). Context packets — project context, recent context, operational evidence — are assembled by skills and passed to debate.py as part of the proposal text.

## Recent Context
Sessions 11-12 (2026-04-15) shipped two layers of challenge pipeline fixes:
- Layer 1: Operational Evidence section in the /challenge proposal template
- Layer 2: Context packets for all 6 thin-context skills (pressure-test, elevate, polish, explore, healthcheck, simulate)
- Context budgets doubled (1-8K to 8-16K tokens) based on Databricks research showing monotonic quality improvement below saturation

A/B testing confirmed enriched context produces more specific findings (5+ unique vs 2-3), deeper tool usage, and novel concerns impossible with thin context (dead code detection, security leak identification, greenfield bias risk).

Two research-backed gaps remain unaddressed: (1) high/low evaluation anchors, (2) expected-outcome framing. Both are the top-2 highest-impact components per arXiv 2506.13639.

## Problem
debate.py tells models WHAT to evaluate (the proposal) and gives them project context, but never tells them what a GOOD vs BAD evaluation looks like for THIS specific artifact. Models default to generic evaluation patterns — "be specific," "cite evidence" — instead of calibrating their quality bar to the artifact's content. The arXiv paper shows high/low anchors outperform full rubrics and are the #2 most impactful evaluation prompt component after criteria.

## Proposed Approach
Add two pure functions to debate.py:
1. `_extract_anchor_slots(proposal_text)` — regex-based extraction of systems, metrics, failures, requirements, evidence, decisions, constraints, and project goals from the proposal text (~50 lines)
2. `_build_anchors(proposal_text, skill_type)` — selects a per-skill-type template, fills slots from extraction, returns formatted anchor text (~30-50 lines)

Anchors are injected into the system prompt between formatting instructions and the artifact. Six template files in `config/anchor-templates/` (one per skill type: challenge, review, explore, polish, healthcheck, think).

**Non-goals:**
- Per-model anchors (shared across all 3 models to preserve convergence)
- Full rubrics (research says they underperform anchors)
- Chain-of-thought instructions (research says zero benefit when criteria are clear)

### Simplest Version
Hardcode one anchor template for `/challenge` directly in debate.py. Test on one proposal. If finding specificity improves, generalize to all 6 skill types.

### Current System Failures
1. **Generic findings from thin proposals** (sessions 10-11): Challenge runs on proposals without operational evidence produced "enumerate the 6 skills" and "unverified assumptions" — findings that could apply to any project.
2. **Convergence without depth** (A/B Run A, session 12): All 3 models converged on REVISE for challenge-pipeline-fixes but with shallow reasoning — none verified whether `--verify-claims` was real code.
3. **Cost-of-inaction invisible** (L28): Models evaluate what's proposed but don't engage with what stays broken if we don't build. The anchor's "cost-of-inaction" slot would make this explicit.

### Operational Context
- debate.py runs ~5-10 times/day for challenge, review, and refine pipelines
- 95+ entries in debate-log.jsonl across all phases
- System prompts are constructed in `cmd_challenge()` (~line 1085-1230), `cmd_review()`, and similar functions
- Persona prompts (PERSONA_PROMPTS dict, line 617) already include TYPE tags, MATERIAL/ADVISORY labels, and evidence-tagging instructions
- Context packets are passed as part of the proposal text, not as separate system prompt sections

### Operational Evidence
Context packets (the precursor to anchors) were A/B tested in session 12:
- **Thin (45 lines):** 2-3 unique findings, generic reasoning, models spent tool calls on reconstruction
- **Enriched (89 lines):** 5+ unique findings, novel concerns (security leak, dead code, greenfield bias), models spent tool calls on deeper analysis
- Tool calls went UP with enriched context (Claude 34→40, GPT 13→19, Gemini 1→5) — models engaged more, not less
- The Databricks research (2,000+ experiments) confirms quality improves monotonically below saturation for all three model families

Anchors are the next step in this validated direction — giving models not just more context but calibration for what good evaluation of that context looks like.

### Baseline Performance
Current system prompts include:
- Persona framing (architect/security/PM focus areas)
- TYPE tags (RISK, ASSUMPTION, ALTERNATIVE, OVER-ENGINEERED, UNDER-ENGINEERED)
- MATERIAL/ADVISORY severity labels
- Evidence-tagging instructions
- Security posture modifiers

Missing: any artifact-specific calibration of what "good" means for THIS proposal. The quality bar is generic across all evaluations.
