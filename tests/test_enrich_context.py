"""Tests for scripts/enrich_context.py — proposal enrichment."""
import json
import os
import subprocess
import sys
import tempfile

PYTHON = sys.executable
SCRIPT = "scripts/enrich_context.py"
CWD = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True
).stdout.strip() or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_enrich(proposal_content, extra_args=None):
    """Write a temp proposal and run enrich_context.py against it."""
    tasks_dir = os.path.join(CWD, "tasks")
    os.makedirs(tasks_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", dir=tasks_dir,
                                      delete=False, prefix="test-proposal-") as f:
        f.write(proposal_content)
        path = f.name
    try:
        cmd = [PYTHON, SCRIPT, "--proposal", path]
        if extra_args:
            cmd.extend(extra_args)
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=CWD, timeout=15)
        return result, json.loads(result.stdout) if result.stdout.strip() else None
    finally:
        os.unlink(path)


def test_valid_json_output():
    """Output is valid JSON with expected keys."""
    proposal = "# Build process improvements\n\nAdd review and debate tooling.\n"
    result, data = run_enrich(proposal)
    assert result.returncode == 0
    assert "keywords" in data
    assert "lessons" in data
    assert "decisions" in data
    assert isinstance(data["lessons"], list)
    assert isinstance(data["decisions"], list)


def test_empty_proposal():
    """Empty proposal returns empty results gracefully."""
    result, data = run_enrich("")
    assert result.returncode == 0
    assert data["lessons"] == []
    assert data["decisions"] == []


def test_frontmatter_scope_extraction():
    """Keywords extracted from frontmatter scope field."""
    proposal = '---\nscope: "Hook refactor and tier classification"\n---\n\n# Hook Refactor\n\nReplace inline classification with tier_classify.py.\n'
    result, data = run_enrich(proposal)
    assert result.returncode == 0
    assert len(data["keywords"]) > 0
    keywords = data["keywords"]
    assert any("hook" in k or "tier" in k or "refactor" in k for k in keywords)


def test_known_topic_matches():
    """A proposal about debate/review should match relevant content."""
    proposal = "# Cross-model debate pipeline\n\nImprove the debate and review process with enrichment.\n"
    result, data = run_enrich(proposal)
    assert result.returncode == 0
    for item in data["lessons"]:
        assert "id" in item
        assert "score" in item
        assert "text" in item


def test_top_k_limits():
    """--top-k limits results per source."""
    proposal = "# Build process improvements\n\nReview debate enrichment tier hook.\n"
    result, data = run_enrich(proposal, ["--top-k", "2"])
    assert result.returncode == 0
    assert len(data["lessons"]) <= 2
    assert len(data["decisions"]) <= 2


def test_missing_proposal_exits_1():
    """Missing proposal file exits with error."""
    result = subprocess.run(
        [PYTHON, SCRIPT, "--proposal", "tasks/nonexistent-proposal.md"],
        capture_output=True, text=True, cwd=CWD,
    )
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert "error" in data
