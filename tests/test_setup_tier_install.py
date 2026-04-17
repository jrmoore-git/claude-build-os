#!/usr/bin/env python3.11
"""Tier-install drift test for /setup skill.

Catches the case where someone adds a template without wiring it into the
setup skill's Step 3 (or vice versa). Does not enforce behavior — just
detects drift between declared tier-files and templates on disk.

Background: the setup skill at .claude/skills/setup/SKILL.md contains a
Step 3 that lists, per tier, the files to create in a new BuildOS project.
Each file typically has a starter template at templates/<basename>.md.
When the two drift out of sync, new users get incomplete installs with no
compile-time warning.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SETUP_SKILL = REPO_ROOT / ".claude" / "skills" / "setup" / "SKILL.md"
TEMPLATES_DIR = REPO_ROOT / "templates"

# Tier 2 listings that intentionally point at examples/ instead of templates/ —
# these don't need a corresponding template file.
TIER2_EXAMPLE_REFERENCES = {
    ".claude/rules/security.md",
    ".claude/settings.json",
}

# Templates not expected to appear in setup Step 3 — they serve other workflows
# (session bootstrap, skill scaffolding) and are created by /start, /wrap, or
# skill authors, not by /setup.
TEMPLATES_OUTSIDE_SETUP = {
    "session-log.md",     # created/updated by /wrap, not /setup
    "skill-tier1.md",     # skill authoring template
    "skill-tier2.md",     # skill authoring template
}


def _read_skill() -> str:
    assert SETUP_SKILL.exists(), f"setup skill missing at {SETUP_SKILL}"
    return SETUP_SKILL.read_text()


def _extract_tier_files(skill_text: str) -> dict[str, list[str]]:
    """Parse Step 3 subsections and return {tier_label: [file_path, ...]}.

    Only captures lines starting with '- `filepath`' under each ### Tier N
    heading. Ignores explanatory text.
    """
    tiers: dict[str, list[str]] = {}
    current: str | None = None
    for line in skill_text.splitlines():
        tier_match = re.match(r"^###\s+(Tier\s+\d)", line)
        if tier_match:
            current = tier_match.group(1)
            tiers.setdefault(current, [])
            continue
        if current is None:
            continue
        if line.startswith("## "):
            current = None
            continue
        bullet_match = re.match(r"^-\s+`([^`]+)`", line)
        if bullet_match:
            path = bullet_match.group(1)
            if "/" in path or path.endswith((".md", ".json", ".sh")):
                tiers[current].append(path)
    return tiers


def test_setup_skill_has_tier_sections():
    """Step 3 must contain ### Tier 0, ### Tier 1, ### Tier 2 subsections."""
    text = _read_skill()
    for tier in ("Tier 0", "Tier 1", "Tier 2"):
        assert f"### {tier}" in text, f"setup SKILL.md missing '### {tier}' subsection"


def test_tier1_files_have_templates():
    """Every file declared under Tier 1 must have a matching basename in templates/."""
    tiers = _extract_tier_files(_read_skill())
    tier1 = tiers.get("Tier 1", [])
    assert tier1, "Tier 1 file list is empty — setup skill drift?"
    missing = []
    for path in tier1:
        basename = Path(path).name
        template = TEMPLATES_DIR / basename
        if not template.exists():
            missing.append((path, str(template.relative_to(REPO_ROOT))))
    assert not missing, (
        "Tier 1 files declared in setup but missing from templates/: "
        + ", ".join(f"{p} (expected {t})" for p, t in missing)
    )


def test_tier2_files_have_templates_or_are_example_refs():
    """Every Tier 2 file either has a template, or is in TIER2_EXAMPLE_REFERENCES."""
    tiers = _extract_tier_files(_read_skill())
    tier2 = tiers.get("Tier 2", [])
    assert tier2, "Tier 2 file list is empty — setup skill drift?"
    missing = []
    for path in tier2:
        if path in TIER2_EXAMPLE_REFERENCES:
            continue
        basename = Path(path).name
        template = TEMPLATES_DIR / basename
        if not template.exists():
            missing.append((path, str(template.relative_to(REPO_ROOT))))
    assert not missing, (
        "Tier 2 files declared in setup but missing from templates/ "
        "(and not listed in TIER2_EXAMPLE_REFERENCES): "
        + ", ".join(f"{p} (expected {t})" for p, t in missing)
    )


def test_no_orphan_templates():
    """Every template in templates/ is either declared by setup or in TEMPLATES_OUTSIDE_SETUP."""
    tiers = _extract_tier_files(_read_skill())
    declared_basenames: set[str] = set()
    for file_list in tiers.values():
        for path in file_list:
            declared_basenames.add(Path(path).name)

    orphans = []
    for template in sorted(TEMPLATES_DIR.glob("*.md")):
        if template.name in declared_basenames:
            continue
        if template.name in TEMPLATES_OUTSIDE_SETUP:
            continue
        orphans.append(template.name)

    assert not orphans, (
        "Templates on disk but not declared in any setup tier (and not in "
        "TEMPLATES_OUTSIDE_SETUP whitelist): " + ", ".join(orphans)
    )
