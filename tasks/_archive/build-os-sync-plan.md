---
scope: "Sync all framework upgrades from local openclaw repo to public claude-build-os GitHub repo, stripped of all project-specific references"
surfaces_affected: "README.md, CLAUDE.md, .gitignore, .env.example, config/*, scripts/*, hooks/*, .claude/skills/*, .claude/rules/*, .claude/settings.json, docs/*, tests/contracts/*"
verification_commands: "cd /Users/macmini/claude-build-os && grep -rn 'openclaw\\|OpenClaw\\|Jarvis\\|jarvis\\|Justin\\|justin\\|Telegram\\|TELEGRAM\\|Slack\\|SLACK\\|innovius\\|Innovius\\|cloudzero\\|CloudZero\\|innoviuscapital\\|/Users/macmini\\|@innovius\\|@cloudzero\\|8387329260\\|6507037822\\|6503803830\\|9256395873\\|sk-ant\\|xoxb-\\|xapp-' . --include='*.md' --include='*.py' --include='*.sh' --include='*.json' --include='*.yaml' | grep -v '.git/' && python3 -m pytest tests/ && bash hooks/hook-plan-gate.sh --self-test 2>/dev/null"
rollback: "git revert per batch commit — each batch is an independent commit"
review_tier: "Tier 1.5"
verification_evidence: "PENDING"
challenge_skipped: true
---

# Build OS Sync Plan

Sync battle-tested framework upgrades from openclaw → claude-build-os. Strip all project-specific references. Push to GitHub.

**Working directory:** `/Users/macmini/claude-build-os/` (separate repo, separate remote)
**Source:** `/Users/macmini/openclaw/` (read-only — we copy, never modify source)

## Generalization Pattern (apply to ALL files)

Every file copied from openclaw must have these transformations:

1. `#!/usr/bin/env python3.11` → `#!/usr/bin/env python3`
2. `/opt/homebrew/bin/python3.11` → `python3`
3. `/Users/macmini/openclaw` → dynamic (`$PROJECT_ROOT`, `git rev-parse --show-toplevel`, or relative paths)
4. `jarvis-app/` → generic language ("your app", "the frontend directory", or parameterized)
5. `Jarvis` → removed or replaced with generic ("the app", "your project")
6. `Justin` → removed or replaced with "the user"
7. `Telegram`/`TELEGRAM` → removed (delivery channel is project-specific)
8. `Slack`/`SLACK` → removed (channel is project-specific)
9. `openclaw`/`OpenClaw` → removed or replaced with "the framework" / "Build OS"
10. `innovius`/`Innovius`/`cloudzero`/`CloudZero` → removed
11. Any phone numbers, Slack user IDs, API key prefixes → removed
12. `deploy_skills.sh` references to `launchctl` → generic service restart pattern
13. `litellm/claude-*` model refs → generic model name pattern or configurable

**Security scan command (run after every batch):**
```bash
grep -rn 'openclaw\|OpenClaw\|Jarvis\|jarvis\|Justin\|justin\|Telegram\|TELEGRAM\|Slack\|SLACK\|innovius\|Innovius\|cloudzero\|CloudZero\|innoviuscapital\|/Users/macmini\|@innovius\|@cloudzero\|8387329260\|6507037822\|6503803830\|9256395873\|sk-ant\|xoxb-\|xapp-\|GOG_KEYRING\|JUSTIN_TELEGRAM\|AFFINITY_API' /Users/macmini/claude-build-os/ -r --include='*.md' --include='*.py' --include='*.sh' --include='*.json' --include='*.yaml' | grep -v '.git/'
```
Must return zero results before commit.

---

## Batch 1: README + CLAUDE.md + Infrastructure Docs (6 files)

**Priority:** Highest — this is the front door.

### B1.1: README.md — Content rewrite

Keep essay structure and voice. Update content:

**Structural changes:**
- Add "## Prerequisites" section after Quick Start with install commands (Python 3, gh CLI, LiteLLM, API keys, Ollama optional)
- Pipeline table: 11 → 19 commands (add debate, design-consultation, design-review, plan-design-review, qa, ship, status, wrap-session)
- Scripts table: 6 → 8 (add multi_model_debate.py, model_conversation.py)
- Hooks table: 3 → 11 (add all 8 new hooks)
- Add "## Rules" section listing the 7 `.claude/rules/` files
- Update Further Reading with new docs

**Prose updates (update existing sections with concrete examples):**
- "Treating Claude like a chatbot" — add semantic search, session bootstrap pattern
- "Where the model stops" — add two-pass extraction, parameterized toolbelt
- "Move state to disk" — add plan artifact pattern with YAML frontmatter, findings tracker JSONL
- "Guidance vs governance" — 3→11 hooks, three-strikes escalation, gate gaming detection
- "Complexity drift" — `/challenge` as solution, decomposition analysis, anti-slop vocabulary
- "Testing and release control" — cross-model debate pipeline, contract tests, deploy pattern, cost discipline

**New prose sections:**
- "Design governance" — AI slop detection, 94-item checklist, `/design-review`
- "Cross-model review" — different model families to avoid self-preference bias
- "Skill authoring discipline" — output silence, cron contracts, single output format

### B1.2: CLAUDE.md — Update references

- Infrastructure → Scripts: add `multi_model_debate.py`, `model_conversation.py`
- Infrastructure → Hooks: add all 8 new hooks
- Infrastructure → Skills pipeline: update to show full 19-command set
- Add Rules reference section listing 7 `.claude/rules/` files
- Keep the template structure (placeholder for project description)

### B1.3: .gitignore — Expand patterns

Add from local: `stores/*.db`, `*.jsonl` (except debate-log), `.env`, `__pycache__/`, `.venv/`

### B1.4: .env.example — New file

```
# Required for cross-model debate (/challenge, /debate, /review)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
LITELLM_MASTER_KEY=

# Optional: Ollama for semantic recall search
# OLLAMA_HOST=127.0.0.1
```

### B1.5: config/litellm-config.example.yaml — New file

Template model routing config for LiteLLM with 3 model families.

### B1.6: docs/infrastructure.md — New file

What each dependency does, why it's needed, install commands, verification steps.

**Commit message:** `Upgrade README with battle-tested patterns, add prerequisites and infrastructure docs`

---

## Batch 2: Scripts + Hooks (19 files)

### B2.1: Update 6 existing scripts
Copy from local, apply generalization pattern:
- `scripts/debate.py` (1265 lines, 3 refs to strip)
- `scripts/tier_classify.py` (189 lines, 5 refs)
- `scripts/recall_search.py` (142 lines, 0 refs — shebang only)
- `scripts/finding_tracker.py` (245 lines, 1 ref)
- `scripts/enrich_context.py` (128 lines, 1 ref)
- `scripts/artifact_check.py` (194 lines, 1 ref)

### B2.2: Add 2 new scripts
- `scripts/multi_model_debate.py` (238 lines, 1 ref)
- `scripts/model_conversation.py` (481 lines, 1 ref)

### B2.3: Update 3 existing hooks
- `hooks/hook-plan-gate.sh` (166 lines, 3 refs)
- `hooks/hook-review-gate.sh` (146 lines, 5 refs)
- `hooks/hook-tier-gate.sh` (143 lines, 2 refs)

### B2.4: Add 8 new hooks
- `hooks/hook-decompose-gate.sh` (31 lines, 0 refs — clean)
- `hooks/hook-guard-env.sh` (55 lines, 1 ref)
- `hooks/hook-post-tool-test.sh` (23 lines, 2 refs)
- `hooks/hook-prd-drift-check.sh` (83 lines, 7 refs)
- `hooks/hook-pre-commit-tests.sh` (19 lines, 1 ref)
- `hooks/hook-pre-edit-gate.sh` (200 lines, 2 refs)
- `hooks/hook-ruff-check.sh` (33 lines, 0 refs — clean)
- `hooks/hook-syntax-check-python.sh` (21 lines, 0 refs — clean)

### B2.5: Update tests
- `tests/test_artifact_check.py` — sync with updated script
- `tests/test_enrich_context.py` — sync
- `tests/test_finding_tracker.py` — sync
- `tests/test_tier_classify.py` — sync

**Commit message:** `Sync scripts and hooks: 8 new enforcement hooks, multi-model debate engine`

---

## Batch 3: Skills (13 files)

### B3.1: Update 5 existing skills (local improvements → GitHub)
- `.claude/skills/challenge/SKILL.md` (108→upgraded, 3 refs)
- `.claude/skills/plan/SKILL.md` (79→143 lines, 3 refs)
- `.claude/skills/recall/SKILL.md` (40→63 lines, 0 refs)
- `.claude/skills/review/SKILL.md` (74→176 lines, 3 refs — 3-lens review)
- `.claude/skills/think/SKILL.md` (66→94 lines, 3 refs)

### B3.2: Add 8 new skills
- `.claude/skills/debate/SKILL.md` (116 lines, 4 refs)
- `.claude/skills/design-consultation/SKILL.md` (450 lines, 7 refs)
- `.claude/skills/design-review/SKILL.md` (666 lines, 6 refs)
- `.claude/skills/plan-design-review/SKILL.md` (552 lines, 9 refs)
- `.claude/skills/qa/SKILL.md` (116 lines, 7 refs)
- `.claude/skills/ship/SKILL.md` (148 lines, 5 refs)
- `.claude/skills/status/SKILL.md` (99 lines, 2 refs)
- `.claude/skills/wrap-session/SKILL.md` (153 lines, 12 refs)

**Commit message:** `Add 8 skills: debate, design system, QA, ship, status, wrap-session`

---

## Batch 4: Rules + Docs (11 files)

### B4.1: Add 7 rules files
All to `.claude/rules/`:
- `code-quality.md` (55 lines, 2 refs)
- `design.md` (28 lines, 1 ref)
- `orchestration.md` (60 lines, 0 refs — clean)
- `review-protocol.md` (86 lines, 0 refs — clean)
- `session-discipline.md` (98 lines, 2 refs)
- `skill-authoring.md` (48 lines, 4 refs)
- `workflow.md` (54 lines, 1 ref)

### B4.2: Add/update 4 docs
- `docs/contract-tests.md` (252 lines, 23 refs — needs scrub)
- `docs/Operating-Reference.md` (720 lines, 1 ref)
- `docs/review-protocol.md` (83 lines, 0 refs — clean)
- `docs/SKILL-CONTRACT-STANDARD.md` (120 lines, 16 refs — needs scrub)

**Commit message:** `Add governance rules and operational docs from production experience`

---

## Batch 5: Contract Tests + Deploy Templates (12 files)

### B5.1: Add contract test framework
- `tests/contracts/helpers.sh` (246 lines, 4 refs)
- `tests/contracts/test_approval_gating.sh` (40 lines, clean)
- `tests/contracts/test_degraded_mode.sh` (43 lines, 1 ref)
- `tests/contracts/test_exactly_once_scheduling.sh` (62 lines, 3 refs)
- `tests/contracts/test_idempotency.sh` (30 lines, clean)
- `tests/contracts/test_rollback.sh` (56 lines, 2 refs)
- `tests/contracts/test_state_machine.sh` (61 lines, clean)
- `tests/contracts/test_version_pinning.sh` (70 lines, clean)

### B5.2: Add deploy templates
- `scripts/deploy_all.sh` (76 lines, 4 refs — generalize launchctl → generic service restart)
- `scripts/deploy_skills.sh` (83 lines, 10 refs — generalize)
- `scripts/verify_state.py` (158 lines, 5 refs)

### B5.3: Add settings.json
- `.claude/settings.json` — hook wiring for all 11 hooks

**Commit message:** `Add contract test framework and deploy templates`

---

## Execution Strategy

**Decision:** hybrid
**Reason:** Batch 1 is prose work requiring coherent voice — sequential, single agent. Batches 2-5 are mechanical file generalization with zero file overlap — run as parallel agents within each batch. Batches 2-5 can also run in parallel with each other.

| Batch | Files | Depends On |
|-------|-------|------------|
| B1: README + CLAUDE.md + infra | 6 | — |
| B2: Scripts + hooks | 19 | — |
| B3: Skills | 13 | — |
| B4: Rules + docs | 11 | — |
| B5: Tests + deploy templates | 12 | — |

**Synthesis:** After all batches complete, run security scan on entire repo. Run `python3 -m pytest tests/`. Review full diff before push.

---

## Verification

After each batch:
1. Security scan (grep command above) — must return zero results
2. All files parseable (no broken YAML frontmatter, no syntax errors)

After all batches:
1. `cd /Users/macmini/claude-build-os && python3 -m pytest tests/` — all tests pass
2. Full security scan — zero results
3. `git diff --stat origin/main` — review file count and sizes
4. Manual spot-check: read README, try `/setup` flow mentally
5. Push to GitHub: `git push origin main`

---

## Files NOT included (confirmed skip)

| File | Reason |
|------|--------|
| .claude/rules/integration-gotchas.md | 39 project refs (gog, Granola, LiteLLM Docker, OpenClaw gateway) |
| .claude/rules/platform.md | Entirely macOS/OpenClaw path-specific |
| .claude/rules/security.md | Contact tiers, channel rules, user-specific policies |
| scripts/health_daemon.sh | 142 refs, deeply coupled to Telegram/Slack/OpenClaw |
| scripts/cron_preflight.py | OpenClaw cron internals |
| scripts/deploy_jarvis.sh | App-specific |
| docs/skill-owner-manual.md | 144 refs, project examples throughout |
| tests/contracts/test_degradation.sh | Tests OpenClaw-specific degradation |
| tests/contracts/test_email_validation.sh | Tests OpenClaw email validation |
