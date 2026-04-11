---
name: setup
description: Interactive project setup using the Build OS framework
user-invocable: true
---

# Interactive Project Setup

You are setting up a new project to use the Build OS framework. Guide the user through setup by asking questions and creating files based on their answers.

**Note:** This is a reference framework, not an installer. It creates governance files and points you to templates for structured artifacts. Alternatively, run `/init` in Claude Code to generate a starter CLAUDE.md from your existing codebase, then layer governance files on top using the steps below.

## Step 1: Understand the project

Ask the user:
1. **What are you building?** (one sentence)
2. **Who is the audience?** (just you, a team, external users, autonomous agent)
3. **What's the blast radius if Claude makes a mistake?** (bad file, wasted work, user-facing error, wrong email sent, data exposed)

## Step 2: Pick the governance tier

Based on their answers, recommend a tier:

- **Tier 0 (Advisory):** Personal project, just you, mistakes are easily reversible
- **Tier 1 (Structured Memory):** Multi-session project, team, or lasting more than a week
- **Tier 2 (Enforced Governance):** Production system, real users, financial or reputational consequences
- **Tier 3 (Production OS):** Autonomous agent, acts on your behalf, sensitive data

Explain your recommendation. Let the user confirm or choose differently.

## Step 3: Create the file structure

Based on the chosen tier, create these files:

### Tier 0
- Update `CLAUDE.md` with the project description and any project-specific rules

### Tier 1 (adds to Tier 0)
- `docs/project-prd.md` — with the project description as the first section
- `docs/current-state.md` — initialized with "Project just started. No blockers."
- `tasks/decisions.md` — with D1: the first decision (framework choice, tech stack, or approach)
- `tasks/lessons.md` — empty, with the format header
- `tasks/handoff.md` — empty, with the format header

### Tier 2 (adds to Tier 1)
- `docs/contract-tests.md` — with the essential eight invariants as a starting template
- `docs/review-protocol.md` — with the staged review order
- `.claude/rules/security.md` — with starter security rules (see `examples/rules/security.md` in the Build OS repo for a starting point)
- `.claude/settings.json` — with at least one hook wired (see `examples/README.md` in the Build OS repo for hook configuration)

### Tier 3 (adds to Tier 2)
- Note: Tier 3 requires custom engineering. Set up Tier 2 files and explain what Tier 3 adds (cross-model debate, model routing, kill switches, approval gating).

## Step 4: Copy skills

Tell the user: "Copy the `.claude/skills/` directory from the Build OS repo to your project. These provide session operations: `/recall`, `/plan`, `/review`, `/capture`, `/wrap-session`, `/triage`, and this `/setup` command."

## Step 5: Install design tools

Run `./scripts/setup-design-tools.sh` to install the design CLI and browser
CLI. These are required by `/design-shotgun` and useful for `/design-review`.
If the script succeeds, tell the user to restart their shell (or `source ~/.zshrc`).
If it fails, note that design skills will be unavailable but everything else works.

## Step 6: Show what was created

List every file created with a one-line description. Suggest what to do next:
- Tier 0: "Start building. Update CLAUDE.md as you learn what rules matter."
- Tier 1: "Run `/recall` at the start of each session. Update handoff.md before closing."
- Tier 2: "Add one hook (see examples/). Write your first contract test. See `docs/platform-features.md` for hook types and events."
- All tiers: "If design tools installed, try `/design-shotgun` to explore visual directions."

## Rules for this command
- Create only the files needed for the chosen tier. Do not create Tier 2 files for a Tier 0 project.
- Every file created should have real content, not just placeholders. Use the project description to populate the PRD, the first decision, etc.
- Keep it conversational. This should feel like a guided setup, not a form.
