"""Tests for scripts/skill_reachability.py — skill-graph audit."""
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

PYTHON = sys.executable
REPO_ROOT = Path(subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True, check=True
).stdout.strip())

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from skill_reachability import (  # noqa: E402
    build_report,
    detect_collisions,
    detect_description_overlap,
    list_skills,
    parse_routing_table,
    parse_skill_frontmatter,
)


def _write_skill(skills_dir: Path, name: str, description: str) -> None:
    skill_dir = skills_dir / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(textwrap.dedent(f"""\
        ---
        name: {name}
        description: "{description}"
        version: 1.0.0
        ---
        # {name}
        ## Procedure
        Do the thing.
        DONE.
    """))


def _write_routing(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(body))


# ── parse_routing_table ──────────────────────────────────────────────────────

def test_parse_routing_table_extracts_triggers_by_skill(tmp_path):
    routing = tmp_path / "routing.md"
    _write_routing(routing, """\
        # Natural Language Routing

        ## Routing Table

        | User says something like... | Route to |
        |---|---|
        | "debug this", "something broke" | `/investigate` |
        | "ship it", "deploy" | `/ship` |
    """)
    triggers, disambig = parse_routing_table(routing)
    assert "investigate" in triggers
    assert "ship" in triggers
    assert "debug this" in triggers["investigate"]
    assert "ship it" in triggers["ship"]
    assert disambig == set()


def test_parse_routing_table_marks_disambiguation_skills(tmp_path):
    routing = tmp_path / "routing.md"
    _write_routing(routing, """\
        ## Routing Table
        | User says something like... | Route to |
        |---|---|
        | "ship" | `/ship` |

        ## Disambiguating /challenge vs /pressure-test

        | Artifact state | Default route |
        |---|---|
        | Plan exists | `/pressure-test` |
        | No plan | `/challenge` |
    """)
    _, disambig = parse_routing_table(routing)
    assert "challenge" in disambig
    assert "pressure-test" in disambig


# ── Orphan and phantom detection ─────────────────────────────────────────────

def test_orphans_when_skill_exists_but_not_routed(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    _write_skill(skills_dir, "alpha", "Use when alpha")
    _write_skill(skills_dir, "beta", "Use when beta")

    routing = tmp_path / "routing.md"
    _write_routing(routing, """\
        ## Routing Table
        | User says something like... | Route to |
        |---|---|
        | "do alpha" | `/alpha` |
    """)

    report = build_report(skills_dir=skills_dir, routing_file=routing)
    assert report["orphans"] == ["beta"]
    assert report["phantoms"] == []


def test_phantoms_when_routed_but_no_skill(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    _write_skill(skills_dir, "alpha", "Use when alpha")

    routing = tmp_path / "routing.md"
    _write_routing(routing, """\
        ## Routing Table
        | User says something like... | Route to |
        |---|---|
        | "do alpha" | `/alpha` |
        | "do ghost" | `/ghost` |
    """)

    report = build_report(skills_dir=skills_dir, routing_file=routing)
    assert report["orphans"] == []
    assert report["phantoms"] == ["ghost"]


# ── Collision detection ──────────────────────────────────────────────────────

def test_collision_when_phrase_maps_to_two_skills_outside_disambig():
    triggers = {
        "investigate": ["debug this", "something broke"],
        "audit": ["debug this", "poke around"],
    }
    disambig = set()
    collisions = detect_collisions(triggers, disambig)
    assert len(collisions) == 1
    assert collisions[0]["phrase"] == "debug this"
    assert collisions[0]["skills"] == ["audit", "investigate"]


def test_no_collision_when_both_skills_are_disambiguated():
    triggers = {
        "challenge": ["is this a good idea"],
        "pressure-test": ["is this a good idea"],
    }
    disambig = {"challenge", "pressure-test"}
    collisions = detect_collisions(triggers, disambig)
    assert collisions == []


# ── Description overlap ──────────────────────────────────────────────────────

def test_description_overlap_detects_shared_content_words():
    skills = {
        "alpha": {"description": "Use when you need to plan a new feature with discovery"},
        "beta": {"description": "Use when you need to plan a new feature with premise review"},
    }
    overlaps = detect_description_overlap(skills, threshold=3)
    assert len(overlaps) == 1
    assert set(overlaps[0]["skills"]) == {"alpha", "beta"}
    assert overlaps[0]["count"] >= 3


def test_description_overlap_respects_threshold():
    skills = {
        "alpha": {"description": "Use when debugging"},
        "beta": {"description": "Use when shipping"},
    }
    overlaps = detect_description_overlap(skills, threshold=3)
    assert overlaps == []


# ── Frontmatter parsing ──────────────────────────────────────────────────────

def test_parse_skill_frontmatter_extracts_quoted_description(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text(textwrap.dedent("""\
        ---
        name: x
        description: "Use when doing X"
        version: 1.0.0
        ---
        body
    """))
    fm = parse_skill_frontmatter(skill)
    assert fm["name"] == "x"
    assert fm["description"] == "Use when doing X"


# ── list_skills integration ──────────────────────────────────────────────────

def test_list_skills_returns_all_skill_directories(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    _write_skill(skills_dir, "alpha", "Use when alpha")
    _write_skill(skills_dir, "beta", "Use when beta")

    skills = list_skills(skills_dir)
    assert set(skills.keys()) == {"alpha", "beta"}
    assert skills["alpha"]["description"] == "Use when alpha"


# ── CLI contract ─────────────────────────────────────────────────────────────

def test_cli_json_output_is_valid():
    result = subprocess.run(
        [PYTHON, "scripts/skill_reachability.py", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    payload = json.loads(result.stdout)
    assert "skills_on_disk" in payload
    assert "skills_routed" in payload
    assert "orphans" in payload
    assert "phantoms" in payload
    assert "trigger_collisions" in payload
    assert "description_overlaps" in payload
    assert "disambiguated_skills" in payload


def test_cli_exit_code_semantics():
    """Exit 0 = clean; 1 = orphan/phantom (hard); 2 = only advisories."""
    result = subprocess.run(
        [PYTHON, "scripts/skill_reachability.py", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    payload = json.loads(result.stdout)
    if payload["orphans"] or payload["phantoms"]:
        assert result.returncode == 1
    elif payload["trigger_collisions"] or payload["description_overlaps"]:
        assert result.returncode == 2
    else:
        assert result.returncode == 0
