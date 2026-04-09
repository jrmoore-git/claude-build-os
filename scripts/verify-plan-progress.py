#!/usr/bin/env python3.11
"""
verify-plan-progress.py — Verify project memory claims against plan artifacts on disk.

Called by /recall after loading memory. For each active project memory that
references a plan file, reads the plan and checks which sessions/phases are
complete based on:
1. Plan file existence and structure (sessions with completion markers)
2. Session log entries mentioning the plan topic
3. Artifact files (design, challenge, elevate, plan, review) on disk

Output: JSON to stdout with corrections for stale memory.

Usage:
    python3.11 scripts/verify-plan-progress.py [--memory-dir DIR]
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def get_repo_root():
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return Path.cwd()
    return Path(result.stdout.strip())


REPO = get_repo_root()
TASKS = REPO / "tasks"

# Memory dir is project-specific — derive from CLAUDE_PROJECT or fall back
# to scanning ~/.claude/projects/ for a match
def find_memory_dir():
    # Check CLI arg
    if "--memory-dir" in sys.argv:
        idx = sys.argv.index("--memory-dir")
        if idx + 1 < len(sys.argv):
            return Path(sys.argv[idx + 1])

    # Check env var
    env_dir = os.environ.get("CLAUDE_MEMORY_DIR")
    if env_dir:
        return Path(env_dir)

    # Scan ~/.claude/projects/ for a directory matching this repo
    projects_dir = Path.home() / ".claude" / "projects"
    if projects_dir.exists():
        repo_name = REPO.name
        for d in projects_dir.iterdir():
            if d.is_dir() and repo_name in d.name:
                memory = d / "memory"
                if memory.exists():
                    return memory

    return None


MEMORY_DIR = find_memory_dir()
SESSION_LOG = TASKS / "session-log.md"

# Pipeline artifact suffixes in execution order
PIPELINE_ARTIFACTS = [
    ("design", "/define discover"),
    ("think", "/define refine"),
    ("elevate", "/elevate"),
    ("challenge", "/challenge"),
    ("plan", "/plan"),
    ("review", "/review"),
]


def find_project_memories():
    """Find all project-type memory files with plan references."""
    if not MEMORY_DIR or not MEMORY_DIR.exists():
        return []

    projects = []
    for f in MEMORY_DIR.glob("project_*.md"):
        content = f.read_text()
        if not content.startswith("---"):
            continue
        end = content.index("---", 3)
        frontmatter = content[3:end]
        if "type: project" not in frontmatter:
            continue

        plan_refs = re.findall(r'tasks/(\S+)-plan\.md', content)
        if not plan_refs:
            continue

        projects.append({
            "file": str(f),
            "filename": f.name,
            "content": content,
            "plan_topics": plan_refs,
        })
    return projects


def check_pipeline_artifacts(topic):
    """Check which pipeline artifacts exist for a topic."""
    found = {}
    for suffix, skill_name in PIPELINE_ARTIFACTS:
        path = TASKS / f"{topic}-{suffix}.md"
        if path.exists():
            lines = path.read_text().split("\n")[:10]
            found[suffix] = {
                "exists": True,
                "skill": skill_name,
                "header": next((l for l in lines if l.startswith("# ")), ""),
            }
    return found


def check_plan_sessions(topic):
    """Read the plan file and identify session structure + completion evidence."""
    plan_path = TASKS / f"{topic}-plan.md"
    if not plan_path.exists():
        return None

    content = plan_path.read_text()
    sessions = []

    for match in re.finditer(r'###\s+Session\s+(\d+)[:\s]+(.+)', content):
        session_num = int(match.group(1))
        session_title = match.group(2).strip()
        sessions.append({
            "number": session_num,
            "title": session_title,
        })

    return sessions


def check_session_log_for_topic(topic):
    """Search session log for entries mentioning this topic."""
    if not SESSION_LOG.exists():
        return []

    content = SESSION_LOG.read_text()
    entries = content.split("---")

    keywords = topic.replace("-", " ").split()

    relevant = []
    for entry in entries:
        entry_lower = entry.lower()
        if any(kw in entry_lower for kw in keywords):
            date_match = re.search(r'##\s+(\d{4}-\d{2}-\d{2})', entry)
            date = date_match.group(1) if date_match else "unknown"

            has_implemented = "**implemented" in entry_lower or "implemented:" in entry_lower
            has_decided = "**decided" in entry_lower or "decided:" in entry_lower
            session_match = re.search(r'session\s+(\d+)', entry_lower)
            session_num = int(session_match.group(1)) if session_match else None

            relevant.append({
                "date": date,
                "has_implementation": has_implemented,
                "session_referenced": session_num,
            })

    return relevant


def extract_memory_status_claim(content):
    """Extract what the memory file claims the current status is."""
    status_match = re.search(r'##\s+Status[:\s]+(.+)', content)
    if status_match:
        return status_match.group(1).strip()

    next_match = re.search(r'Session\s+(\d+)\s+next', content, re.IGNORECASE)
    if next_match:
        return f"Claims Session {next_match.group(1)} is next"

    return None


def verify_project(project):
    """Verify a single project memory against disk artifacts."""
    corrections = []
    seen_topics = set()

    for topic in project["plan_topics"]:
        if topic in seen_topics:
            continue
        seen_topics.add(topic)

        artifacts = check_pipeline_artifacts(topic)
        sessions = check_plan_sessions(topic)
        log_entries = check_session_log_for_topic(topic)
        memory_claim = extract_memory_status_claim(project["content"])
        max_session_in_plan = max((s["number"] for s in sessions), default=0) if sessions else 0

        pipeline_steps = []
        for suffix, skill_name in PIPELINE_ARTIFACTS:
            if suffix in artifacts:
                pipeline_steps.append(skill_name)

        if memory_claim:
            if "planned" in memory_claim.lower() or "next" in memory_claim.lower():
                if len(artifacts) >= 3:
                    corrections.append({
                        "topic": topic,
                        "memory_file": project["filename"],
                        "memory_claims": memory_claim,
                        "actual_pipeline": pipeline_steps,
                        "actual_artifacts": list(artifacts.keys()),
                        "session_log_entries": len(log_entries),
                        "sessions_in_plan": [s["title"] for s in sessions] if sessions else [],
                        "severity": "STALE",
                        "message": (
                            f"Memory says '{memory_claim}' but {len(artifacts)} pipeline "
                            f"artifacts exist on disk ({', '.join(artifacts.keys())}). "
                            f"Pipeline appears to have completed: {' → '.join(pipeline_steps)}."
                        ),
                    })

            next_session_match = re.search(r'Session\s+(\d+)\s+next', memory_claim, re.IGNORECASE)
            if next_session_match:
                claimed_next = int(next_session_match.group(1))
                completed_sessions = set()
                for entry in log_entries:
                    if entry["session_referenced"] is not None and entry["has_implementation"]:
                        completed_sessions.add(entry["session_referenced"])

                if claimed_next in completed_sessions:
                    max_completed = max(completed_sessions) if completed_sessions else 0
                    likely_next = min(max_completed + 1, max_session_in_plan) if max_session_in_plan else max_completed + 1
                    if likely_next > max_session_in_plan and max_session_in_plan > 0:
                        next_label = f"all {max_session_in_plan + 1} sessions may be complete"
                    else:
                        next_label = f"Session {likely_next}"
                    corrections.append({
                        "topic": topic,
                        "memory_file": project["filename"],
                        "memory_claims": f"Session {claimed_next} is next",
                        "evidence": f"Session log shows sessions {sorted(completed_sessions)} have implementation entries",
                        "sessions_in_plan": max_session_in_plan + 1,
                        "likely_next": next_label,
                        "severity": "STALE",
                        "message": (
                            f"Memory says Session {claimed_next} is next, but session log "
                            f"shows Session {claimed_next} was completed. Plan has "
                            f"Sessions 0-{max_session_in_plan}. Likely next: {next_label}."
                        ),
                    })

    return corrections


def main():
    projects = find_project_memories()
    if not projects:
        json.dump({"corrections": [], "message": "No active project memories with plan references."}, sys.stdout, indent=2)
        return

    all_corrections = []
    for project in projects:
        corrections = verify_project(project)
        all_corrections.extend(corrections)

    if all_corrections:
        messages = [c["message"] for c in all_corrections]
        json.dump({
            "has_stale_memory": True,
            "correction_count": len(all_corrections),
            "corrections": all_corrections,
            "message": "\n".join(messages),
        }, sys.stdout, indent=2)
    else:
        json.dump({
            "has_stale_memory": False,
            "corrections": [],
            "projects_checked": len(projects),
            "message": f"Checked {len(projects)} project memories — all consistent with disk.",
        }, sys.stdout, indent=2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        json.dump({
            "has_stale_memory": False,
            "error": str(e),
            "message": f"verify-plan-progress error: {e}",
        }, sys.stdout)
