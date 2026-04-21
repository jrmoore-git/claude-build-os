#!/usr/bin/env python3.11
"""Audit the skill graph for reachability, orphans, and trigger collisions.

Parses `.claude/rules/natural-language-routing.md` and cross-references it against
`.claude/skills/*/SKILL.md`. Reports:
  - Orphan skills: exist on disk, absent from routing table
  - Phantom routes: referenced in routing table, no skill directory
  - Trigger collisions: identical user-phrase mapped to 2+ skills outside the
    disambiguation section
  - Description-overlap advisories: pairs of skills whose frontmatter descriptions
    share 3+ non-stopword content words (MECE probe)

Usage:
  python3.11 scripts/skill_reachability.py            # human-readable report
  python3.11 scripts/skill_reachability.py --json     # JSON for /healthcheck

Exit codes:
  0 — no issues
  1 — orphan or phantom found (hard issues)
  2 — only advisories (collisions, overlap)
"""

import json
import re
import sys
from pathlib import Path

ROUTING_FILE = Path(".claude/rules/natural-language-routing.md")
SKILLS_DIR = Path(".claude/skills")

SKILL_TOKEN_RE = re.compile(r"`?/([a-z][a-z0-9-]*)(?:\s+[a-z-]+)?`?")
TRIGGER_SPLIT_RE = re.compile(r'"\s*,\s*"')
STOPWORDS = {
    "a", "an", "and", "or", "the", "to", "for", "of", "in", "on", "with",
    "use", "when", "this", "that", "is", "are", "be", "by", "from", "at",
    "as", "it", "its", "not", "no", "run", "skill", "skills", "task", "tasks",
    "user", "users", "need", "needs", "mode", "modes", "three", "two", "four",
    "defers", "defer", "deferred", "one", "new", "use", "using", "used",
    "work", "tool", "tools",
}


def parse_routing_table(path: Path) -> tuple[dict[str, list[str]], set[str]]:
    """Return (triggers_by_skill, disambiguated_skills).

    triggers_by_skill: {skill_name: [trigger_phrase, ...]}
    disambiguated_skills: skills that appear in a Disambiguating section
        (collisions between them are expected, not errors).
    """
    if not path.exists():
        return {}, set()

    text = path.read_text()
    triggers_by_skill: dict[str, list[str]] = {}
    disambiguated: set[str] = set()

    in_disambig = False
    for line in text.split("\n"):
        if re.match(r"^##\s+Disambiguat", line, re.IGNORECASE):
            in_disambig = True
            heads = re.findall(r"/([a-z][a-z0-9-]*)", line)
            disambiguated.update(heads)
            continue
        if line.startswith("## "):
            in_disambig = False
            continue

        if not line.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        if cells[0].lower().startswith("user says") or cells[0].lower().startswith("artifact state"):
            continue
        if cells[0].lower().startswith("you observe"):
            continue

        triggers_cell = cells[0]
        route_cell = cells[1]

        triggers = [
            t.strip().strip('"').strip("'").lower()
            for t in TRIGGER_SPLIT_RE.split(triggers_cell)
            if t.strip().strip('"').strip("'")
        ]
        if not triggers or triggers == [triggers_cell.lower()]:
            quoted = re.findall(r'"([^"]+)"', triggers_cell)
            if quoted:
                triggers = [q.lower() for q in quoted]

        skills = [m.group(1) for m in SKILL_TOKEN_RE.finditer(route_cell)]
        if not skills:
            continue
        primary = skills[0]

        if in_disambig:
            disambiguated.update(skills)

        triggers_by_skill.setdefault(primary, []).extend(triggers)

    return triggers_by_skill, disambiguated


def parse_skill_frontmatter(path: Path) -> dict:
    """Lightweight frontmatter parse (no PyYAML — not installed)."""
    if not path.exists():
        return {}
    content = path.read_text()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            fm[key] = val
    return fm


def list_skills(skills_dir: Path) -> dict[str, dict]:
    """Return {skill_name: {description, path}} for every skill on disk."""
    out = {}
    if not skills_dir.exists():
        return out
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        name = skill_md.parent.name
        fm = parse_skill_frontmatter(skill_md)
        out[name] = {
            "description": fm.get("description", ""),
            "path": str(skill_md),
        }
    return out


def detect_collisions(triggers_by_skill: dict[str, list[str]], disambiguated: set[str]) -> list[dict]:
    """Phrases that map to 2+ skills outside the disambiguation section."""
    phrase_to_skills: dict[str, set[str]] = {}
    for skill, phrases in triggers_by_skill.items():
        for p in phrases:
            phrase_to_skills.setdefault(p, set()).add(skill)

    collisions = []
    for phrase, skills in phrase_to_skills.items():
        if len(skills) < 2:
            continue
        if skills.issubset(disambiguated):
            continue
        collisions.append({"phrase": phrase, "skills": sorted(skills)})
    return collisions


def content_words(text: str) -> set[str]:
    words = re.findall(r"[a-z][a-z-]{2,}", text.lower())
    return {w for w in words if w not in STOPWORDS}


def detect_description_overlap(skills: dict[str, dict], threshold: int = 3) -> list[dict]:
    """Pairs of skills whose descriptions share >= threshold content words."""
    names = sorted(skills.keys())
    word_sets = {n: content_words(skills[n]["description"]) for n in names}
    pairs = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = word_sets[a] & word_sets[b]
            if len(shared) >= threshold:
                pairs.append({
                    "skills": [a, b],
                    "shared_words": sorted(shared),
                    "count": len(shared),
                })
    pairs.sort(key=lambda p: -p["count"])
    return pairs


def build_report(skills_dir: Path = SKILLS_DIR, routing_file: Path = ROUTING_FILE) -> dict:
    triggers_by_skill, disambiguated = parse_routing_table(routing_file)
    skills = list_skills(skills_dir)

    skill_names = set(skills.keys())
    routed_names = set(triggers_by_skill.keys())

    orphans = sorted(skill_names - routed_names)
    phantoms = sorted(routed_names - skill_names)
    collisions = detect_collisions(triggers_by_skill, disambiguated)
    overlaps = detect_description_overlap(skills)

    return {
        "skills_on_disk": len(skill_names),
        "skills_routed": len(routed_names),
        "orphans": orphans,
        "phantoms": phantoms,
        "trigger_collisions": collisions,
        "description_overlaps": overlaps,
        "disambiguated_skills": sorted(disambiguated),
    }


def print_human(report: dict) -> int:
    """Print a human-readable report. Return exit code."""
    print(f"Skills on disk: {report['skills_on_disk']}")
    print(f"Skills with routing entries: {report['skills_routed']}")
    print()

    orphans = report["orphans"]
    phantoms = report["phantoms"]
    collisions = report["trigger_collisions"]
    overlaps = report["description_overlaps"]

    had_hard = False
    if orphans:
        had_hard = True
        print("ORPHAN SKILLS (on disk, not in routing table):")
        for s in orphans:
            print(f"  - {s}")
        print()
    if phantoms:
        had_hard = True
        print("PHANTOM ROUTES (routed but no skill directory):")
        for s in phantoms:
            print(f"  - {s}")
        print()

    had_advisory = False
    if collisions:
        had_advisory = True
        print("TRIGGER COLLISIONS (phrase maps to 2+ skills, not disambiguated):")
        for c in collisions:
            print(f'  - "{c["phrase"]}" -> {", ".join(c["skills"])}')
        print("  (add a disambiguation block, or tighten trigger phrasing)")
        print()

    if overlaps:
        had_advisory = True
        print("DESCRIPTION OVERLAPS (>= 3 shared content words — MECE probe):")
        for o in overlaps[:10]:
            print(f"  - {o['skills'][0]} <-> {o['skills'][1]}: {o['count']} shared "
                  f"({', '.join(o['shared_words'][:6])}{'...' if len(o['shared_words']) > 6 else ''})")
        if len(overlaps) > 10:
            print(f"  ... and {len(overlaps) - 10} more")
        print("  (shared words alone don't prove overlap — read descriptions to judge)")
        print()

    if not had_hard and not had_advisory:
        print("OK — no orphans, phantoms, collisions, or suspicious overlaps.")
        return 0

    return 1 if had_hard else 2


def main() -> int:
    want_json = "--json" in sys.argv[1:]
    report = build_report()
    if want_json:
        print(json.dumps(report, indent=2))
        if report["orphans"] or report["phantoms"]:
            return 1
        if report["trigger_collisions"] or report["description_overlaps"]:
            return 2
        return 0
    return print_human(report)


if __name__ == "__main__":
    sys.exit(main())
