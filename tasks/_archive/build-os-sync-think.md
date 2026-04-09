## Problem Statement

The local openclaw repo has months of battle-tested upgrades to the build OS framework (skills, hooks, scripts, rules, docs) that the public claude-build-os GitHub repo doesn't have. The GitHub repo was a one-time extraction that's now stale. We need to sync all framework-level upgrades — stripping every OpenClaw/Jarvis-specific reference — so the GitHub repo becomes the canonical build OS for future projects (CloudZero engineers, Innovius team, Justin's future builds).

## Proposed Approach

Incremental sync in 5 ordered batches, each with a security scan before push:

1. **README + CLAUDE.md + infrastructure docs** — Rewrite README prose to reflect what we actually learned. Add Prerequisites with install commands. Update pipeline tables, script tables, hook tables. Update CLAUDE.md infrastructure references. Add `.env.example`, `config/litellm-config.example.yaml`, `docs/infrastructure.md`.

2. **Scripts + hooks** — Update 14 already-diverged files (6 scripts, 3 hooks). Add 2 new scripts (`multi_model_debate.py`, `model_conversation.py`). Add 8 new hooks. Follow established generalization pattern: `python3` not `python3.11`, dynamic root detection, no hardcoded paths.

3. **Skills** — Add 8 local-only Claude Code skills: `/debate`, `/design-consultation`, `/design-review`, `/plan-design-review`, `/qa`, `/ship`, `/status`, `/wrap-session`. Upgrade existing 5 shared skills (`/challenge`, `/plan`, `/recall`, `/review`, `/think`) with local improvements. Strip all project-specific references.

4. **Rules + docs** — Add 7 rules files (code-quality, design, orchestration, review-protocol, session-discipline, skill-authoring, workflow). Update existing docs. Add new docs (contract-tests.md, Operating-Reference.md, review-protocol.md, SKILL-CONTRACT-STANDARD.md).

5. **Contract tests + deploy templates** — Add 8 contract test scripts + helpers. Add deploy script patterns (deploy_all.sh, deploy_skills.sh, verify_state.py as generalized templates).

## README Prose Updates (Batch 1)

The essay (lines 78-214) was written as theory before we had real implementations. It needs to reflect what we actually learned:

### Sections to update with concrete examples:
- **"Treating Claude like a chatbot"** — add semantic search (Ollama + embeddings), session bootstrap pattern
- **"Where the model stops"** — add two-pass extraction pattern, parameterized toolbelt architecture, email pipeline boundary as examples
- **"Move state to disk"** — add plan artifact pattern (YAML frontmatter + hook validation), findings tracker (append-only JSONL state machine)
- **"Guidance vs governance"** — update from 3 hooks → 11 hooks, add three-strikes escalation pattern (lesson → rule → hook → architecture), add gate gaming detection
- **"Complexity drift"** — add `/challenge` as operationalized solution, mandatory decomposition analysis, anti-slop vocabulary
- **"Testing and release control"** — add cross-model debate pipeline, contract tests (8 invariants), deploy pattern (build → restart → smoke → verify), concrete cost patterns

### New sections to add:
- **Design governance** — AI slop detection, 94-item design checklist, `/design-review`. A whole dimension that didn't exist in v1
- **Cross-model review** — using different model families to avoid self-preference bias. Central to `/challenge`, `/debate`, `/review`
- **Skill authoring discipline** — output silence, cron output contracts, single output format

### Structural updates:
- Pipeline table: 11 commands → 19 commands
- Scripts table: 6 → 8 scripts
- Hooks table: 3 → 11 hooks
- Prerequisites section with actual install commands
- New "Rules" section referencing `.claude/rules/`
- Further Reading: add new docs

## What's IN scope (framework = how you build)

- `debate.py`, `tier_classify.py`, `recall_search.py`, `finding_tracker.py`, `enrich_context.py`, `artifact_check.py`, `multi_model_debate.py`, `model_conversation.py`
- All 11 hook scripts (generalized)
- All 13 Claude Code skills (generalized)
- `.claude/rules/*.md` — 7 files (stripped of project specifics)
- Contract test framework (8 test scripts + helpers)
- Deploy script patterns (deploy_all.sh, deploy_skills.sh, verify_state.py as templates)
- README prose rewrite + CLAUDE.md update
- Infrastructure docs: `.env.example`, `litellm-config.example.yaml`, `docs/infrastructure.md`
- Existing docs updates: team-playbook.md, advanced-patterns.md, etc.

## What's OUT of scope (application = what you built)

- All gateway skills (morning-briefing, email-triage, etc.)
- All *_tool.py toolbelt scripts (briefing_tool, outbox_tool, etc.)
- email_pipeline.py, openclaw_mcp_server.py
- Jarvis web app (jarvis-app/)
- Browse tool
- Docker compose (project-specific)
- All .env files, database schemas, contact configs
- Integration-specific gotchas (gog, Granola, Affinity, Slack, Telegram specifics)
- `.claude/rules/integration-gotchas.md` (39 refs, too project-specific)
- `.claude/rules/platform.md` (entirely macOS/path-specific)
- `.claude/rules/security.md` (contact tiers, channel rules, user-specific policies)
- `scripts/health_daemon.sh` (142 refs, deeply coupled)
- `scripts/cron_preflight.py` (OpenClaw cron internals)
- `scripts/deploy_jarvis.sh` (app-specific)
- `docs/skill-owner-manual.md` (144 refs, project examples throughout)
- `tests/contracts/test_degradation.sh` (tests project-specific degradation)
- `tests/contracts/test_email_validation.sh` (tests project email validation)

## Key Assumptions

- The established generalization pattern (python3, dynamic root, no hardcoded paths) is correct — verified on 9 files already
- The GitHub repo should be the canonical source of truth going forward — untested
- No one is currently using the GitHub repo in production — verified (0 stars, 1 fork)
- Security scan (grep for tokens, emails, phone numbers, names) is sufficient — verified by audit
- The README voice/structure is good — update content, don't rewrite from scratch

## Risks

- Missed sensitive reference in a generalized file (mitigated by security scan per batch)
- Rules files contain project-specific operational details mixed with general methodology — need line-by-line editing
- Some skills reference specific debate models (GPT-5.4, Gemini 3.1 Pro) — keep as defaults but document as configurable
- README prose updates could introduce inconsistencies with docs that reference the old content
- README is the front door — bad prose = bad first impression. Review carefully.

## Infrastructure Documentation Gap

Someone cloning the repo today can't run `/challenge` or `/debate` without discovering through failure that they need:

**Core dependencies (must document + validate in /setup):**
- Python 3.x
- `gh` CLI (GitHub)
- LiteLLM proxy (local or Docker) — the debate engine routes through it
- API keys: OpenAI, Google AI, Anthropic — debate uses 3 model families
- `.env` file with key names documented

**Optional dependencies:**
- Ollama + nomic-embed-text (semantic recall in `/recall`)
- Docker (for containerized LiteLLM)

**Deliverables:**
- README "Prerequisites" section with install commands
- `config/litellm-config.example.yaml` (model routing template)
- `.env.example` (key names, no values)
- `/setup` skill update to validate environment and report what's missing
- `docs/infrastructure.md` — what each dependency does and why

## File Manifest

### Modify (19 files)
README.md, CLAUDE.md, .gitignore, config/protected-paths.json, scripts/debate.py, scripts/tier_classify.py, scripts/recall_search.py, scripts/finding_tracker.py, scripts/enrich_context.py, scripts/artifact_check.py, hooks/hook-plan-gate.sh, hooks/hook-review-gate.sh, hooks/hook-tier-gate.sh, .claude/skills/challenge/SKILL.md, .claude/skills/plan/SKILL.md, .claude/skills/recall/SKILL.md, .claude/skills/review/SKILL.md, .claude/skills/think/SKILL.md, docs/team-playbook.md

### Add (45 files)
**Skills (8):** debate, design-consultation, design-review, plan-design-review, qa, ship, status, wrap-session
**Hooks (8):** decompose-gate, guard-env, post-tool-test, prd-drift-check, pre-commit-tests, pre-edit-gate, ruff-check, syntax-check-python
**Scripts (2):** multi_model_debate.py, model_conversation.py
**Rules (7):** code-quality, design, orchestration, review-protocol, session-discipline, skill-authoring, workflow
**Infra scripts (3):** deploy_all.sh, deploy_skills.sh, verify_state.py
**Contract tests (9):** helpers.sh + 8 test scripts
**Docs (4):** contract-tests.md, Operating-Reference.md, review-protocol.md, SKILL-CONTRACT-STANDARD.md
**Config/templates (3):** .env.example, litellm-config.example.yaml, docs/infrastructure.md
**Settings (1):** .claude/settings.json (hook wiring)

### Skip (9 files)
integration-gotchas.md, platform.md, security.md, health_daemon.sh, cron_preflight.py, deploy_jarvis.sh, skill-owner-manual.md, test_degradation.sh, test_email_validation.sh

## Simplest Testable Version

Batch 1 (README + CLAUDE.md + infra docs) first. This is the front door — validates voice, structure, and completeness before we push code. If the prose reads well and the Prerequisites actually work on a clean machine, batches 2-5 are mechanical.
