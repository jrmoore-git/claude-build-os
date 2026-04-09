# Proposal: BuildOS Upstream Propagation

## Problem
BuildOS is a shared Claude Code governance framework distributed via GitHub. Improvements are discovered during daily production work in OpenClaw (the downstream project) but don't flow back upstream. OpenClaw is ~4 months ahead. The bottleneck: generalization is hard (stripping project-specific references) and the framework/project boundary is blurry.

## Why Now
Other users actively pull BuildOS from GitHub. Every day without sync means consumers run stale governance — missing battle-tested hook improvements, rule refinements, and skill upgrades.

## Proposed Approach
**Layered Architecture with structural boundary enforcement.** Redesign OpenClaw so framework files and project files are separated by directory structure, not convention. Framework files (`.claude/rules/`, `.claude/skills/`, framework scripts, hooks) never contain project-specific references. Project customization lives in override directories (`.claude/rules/reference/`, top-level `skills/`, project scripts). A simple `buildos-sync.sh` copies framework-layer files to the claude-build-os repo — no generalization transforms needed because the files are already clean.

This pattern already exists partially (`.claude/rules/reference/` is the project override layer). The work is extending it consistently and writing the sync script.

Design doc: `tasks/buildos-upstream-propagation-design.md` (9.2/10 from 3-reviewer panel)
