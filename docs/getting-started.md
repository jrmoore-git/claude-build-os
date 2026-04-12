# Getting Started with Build OS

A guided first-hour tutorial. By the end, you'll have a defined product, an implementation plan, and a shipped first change.

---

## The Only Thing You Need to Know

**Just describe what you want to do.** You don't need to memorize any commands. Build OS has 19 skills, but the primary interface is natural language — tell Claude what you're building, what's broken, or what you need, and it routes you to the right tool.

If you ever feel lost, type `/guide` for a quick map organized by intent, or `/start` to get oriented in your current project.

The slash commands below are shown so you understand what's happening, not because you need to type them.

---

## 1. Prerequisites

You need [Claude Code](https://claude.ai/claude-code), git, and Python 3.11+. For cross-model review (`/challenge`, `/challenge --deep`, `/review`), you also need LiteLLM and API keys from Anthropic, OpenAI, and Google AI. See the [README](../README.md) for full setup details.

## 2. Clone and Setup (~5 min)

```bash
git clone https://github.com/jrmoore-git/claude-build-os.git my-project
cd my-project
./setup.sh
```

`setup.sh` detects your platform, installs git hooks, and copies template files. No interactive prompts.

Open Claude Code in the project directory and run:

```
/setup
```

This walks you through three questions (what are you building, who's the audience, what's the blast radius) and creates the right governance files for your project. It picks a governance tier automatically -- you can override if needed.

## 3. Define Your Product (~15 min)

```
/think discover
```

This is the PM phase. `/think discover` runs a structured problem discovery:

1. **Forcing questions** -- it asks hard questions about demand, status quo, target users, and scope. These aren't busywork; they surface assumptions you haven't examined.
2. **Premise challenge** -- it states the premises behind your idea and asks you to confirm or reject each one.
3. **Alternatives** -- it generates 2-3 implementation approaches with tradeoffs.
4. **Design doc** -- it writes `tasks/<topic>-design.md` with everything from the conversation.
5. **PRD generation** -- it maps the design doc into a product requirements doc at `docs/project-prd.md`. You don't need to fill in the blank template manually -- it generates the PRD from your answers and asks a few follow-up questions for gaps.

At the end, you'll have two artifacts: a design doc and a PRD. These are the source of truth for the rest of the pipeline.

**For smaller work**, use `/think refine` instead -- it asks 5 quick forcing questions and writes a brief. Use this for features where the problem is already clear.

## 4. Plan Your First Feature (~5 min)

```
/plan
```

`/plan` reads your design doc and PRD, then writes an implementation plan to `tasks/<topic>-plan.md`. The plan includes:

- File scope (what gets created or modified)
- Verification commands (how to prove it works)
- Rollback steps (how to undo if something breaks)

The plan is a file on disk, not a chat message. This means the next session can pick up where you left off.

## 5. Build

This is normal Claude Code usage. Ask Claude to implement the plan. The framework stays out of your way here, with two exceptions:

- **Hooks** run automatically on certain actions. For example, a ruff check runs on Python edits, and a plan gate blocks commits to protected paths without a plan file. If a hook blocks you, read its message -- it tells you what's missing.
- **The decomposition gate** fires once per session on your first write. It asks whether the task should be split into parallel agents. For single-track work, type "just do it" to bypass.

## 6. Review (~5 min)

```
/review
```

This sends your diff to three models from different families. Each reviews through a different lens:

- **PM lens** -- does this match the spec?
- **Security lens** -- are there vulnerabilities?
- **Architecture lens** -- is the design sound?

The review writes to `tasks/<topic>-review.md`. Fix any issues flagged, then proceed.

**Note:** `/review` requires LiteLLM and API keys. If you haven't set those up yet, do a manual review instead -- the framework doesn't block you.

## 7. Ship

```
/ship
```

`/ship` runs pre-flight gates: tests pass, review exists, verification commands succeed. If everything clears, it commits and deploys. If a gate fails, it tells you what to fix.

## 8. Pipeline Tiers -- Not Everything Needs the Full Pipeline

Match the pipeline to the task:

| Task | Pipeline |
|---|---|
| Bugfix | `/plan` --> build --> `/review` --> `/ship` |
| Small feature | `/think refine` --> `/plan` --> build --> `/review` --> `/ship` |
| New feature | `/think discover` --> `/challenge` --> `/plan` --> build --> `/review` --> `/ship` |
| New feature (UI) | `/think discover` --> `/design consult` --> `/challenge` --> `/plan` --> build --> `/design review` --> `/review` --> `/ship` |
| Big bet | `/think discover` --> `/elevate` --> `/challenge` --> `/plan` --> build --> `/review` --> `/ship` |

A typo fix doesn't need `/think discover`. A new product does. If it has a UI, wire in `/design consult` before planning and `/design review` before shipping. Use the tier that matches your risk.

## 9. What to Learn Next

| You want to... | Read |
|---|---|
| See the full skill list and governance model | [The Build OS](the-build-os.md) |
| Run parallel agents and team projects | [Team Playbook](team-playbook.md) |
| Understand hooks, rules, and enforcement | [Platform Features](platform-features.md) |
| See example project structures | [Examples](../examples/) |

---

You don't need to learn everything. Start with `/think` --> `/plan` --> build --> `/review` --> `/ship`. Add the rest as your workflow matures.
