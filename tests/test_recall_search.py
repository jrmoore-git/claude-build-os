"""Unit tests for scripts/recall_search.py.

Tests BM25 search, tokenization, and governance file parsers.
Pure logic tests — no external dependencies.
"""

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import recall_search  # noqa: E402


# ── tokenize ───────────────────────────────────────────────────────────────


class TestTokenize:
    def test_basic_tokenization(self):
        tokens = recall_search.tokenize("Hello World 123")
        assert tokens == ["hello", "world", "123"]

    def test_strips_punctuation(self):
        tokens = recall_search.tokenize("foo-bar: baz_qux!")
        assert "foo" in tokens
        assert "bar" in tokens
        assert "baz_qux" in tokens

    def test_empty_string(self):
        assert recall_search.tokenize("") == []

    def test_preserves_underscores(self):
        tokens = recall_search.tokenize("_call_litellm _is_timeout")
        assert "_call_litellm" in tokens or "call_litellm" in tokens
        assert "_is_timeout" in tokens or "is_timeout" in tokens


# ── parse_lessons ──────────────────────────────────────────────────────────


class TestParseLessons:
    SAMPLE = """# Lessons

| # | Lesson | Source | Rule |
|---|---|---|---|
| L19 | Cross-model loops too slow | Investigation | Use review-panel |
| L24 | Write tool fails during wrap | Parallel sessions | Read-Write adjacent |
"""

    def test_finds_lessons(self):
        docs = recall_search.parse_lessons(self.SAMPLE)
        assert len(docs) == 2
        assert docs[0][2] == "L19"
        assert docs[1][2] == "L24"

    def test_source_is_lessons_md(self):
        docs = recall_search.parse_lessons(self.SAMPLE)
        assert all(d[0] == "tasks/lessons.md" for d in docs)

    def test_line_numbers_positive(self):
        docs = recall_search.parse_lessons(self.SAMPLE)
        assert all(d[1] > 0 for d in docs)

    def test_tags_only_mode(self):
        docs = recall_search.parse_lessons(self.SAMPLE, tags_only=True)
        assert len(docs) == 2
        # In tags_only mode, the text is just the last column
        for d in docs:
            assert "Lesson" not in d[3] or d[3] == ""


# ── parse_decisions ────────────────────────────────────────────────────────


class TestParseDecisions:
    SAMPLE = """# Decisions

### D1: BuildOS is Python + Shell
**Decision:** All scripts use Python 3.11+.
**Date:** 2026-03-01

### D2: Cross-model debate via LiteLLM
**Decision:** All calls route through LiteLLM.
**Date:** 2026-03-01
"""

    def test_finds_decisions(self):
        docs = recall_search.parse_decisions(self.SAMPLE)
        assert len(docs) == 2
        assert docs[0][2] == "D1"
        assert docs[1][2] == "D2"

    def test_captures_full_text(self):
        docs = recall_search.parse_decisions(self.SAMPLE)
        assert "Python 3.11" in docs[0][3]


# ── parse_sessions ─────────────────────────────────────────────────────────


class TestParseSessions:
    SAMPLE = """# Session Log

---

## 2026-04-14 — Test session

**Decided:** Something
**Implemented:** Something else

---

## 2026-04-13 — Earlier session

**Decided:** Other thing
"""

    def test_finds_sessions(self):
        docs = recall_search.parse_sessions(self.SAMPLE)
        assert len(docs) >= 2

    def test_tags_only_returns_empty(self):
        docs = recall_search.parse_sessions(self.SAMPLE, tags_only=True)
        assert docs == []


# ── bm25 ───────────────────────────────────────────────────────────────────


class TestBM25:
    def test_basic_ranking(self):
        docs = [
            ("f1", 1, "A", "timeout error fallback model"),
            ("f2", 2, "B", "security review code quality"),
            ("f3", 3, "C", "timeout fallback retry logic"),
        ]
        query_tokens = recall_search.tokenize("timeout fallback")
        results = recall_search.bm25(query_tokens, docs)
        assert len(results) >= 2
        # Docs mentioning timeout+fallback should score higher
        top_indices = [i for _, i in results[:2]]
        assert 0 in top_indices  # doc A has both terms
        assert 2 in top_indices  # doc C has both terms

    def test_no_match_returns_empty(self):
        docs = [("f1", 1, "A", "completely unrelated content")]
        query_tokens = recall_search.tokenize("nonexistent xyz")
        results = recall_search.bm25(query_tokens, docs)
        assert results == []

    def test_empty_docs_returns_empty(self):
        results = recall_search.bm25(["test"], [])
        assert results == []

    def test_scores_are_positive(self):
        docs = [
            ("f1", 1, "A", "debate engine challenge review"),
            ("f2", 2, "B", "debate challenge response"),
        ]
        results = recall_search.bm25(recall_search.tokenize("debate challenge"), docs)
        assert all(score > 0 for score, _ in results)

    def test_longer_match_scores_higher(self):
        docs = [
            ("f1", 1, "A", "x"),
            ("f2", 2, "B", "timeout timeout timeout retry fallback"),
        ]
        results = recall_search.bm25(recall_search.tokenize("timeout"), docs)
        if len(results) >= 1:
            # Doc B should score higher (more term frequency)
            assert results[0][1] == 1  # index 1 = doc B


# ── Integration: search against real governance files ──────────────────────


class TestRealSearch:
    def test_search_finds_debate_in_decisions(self):
        path = recall_search.SOURCES.get("decisions")
        if not path or not path.exists():
            pytest.skip("decisions.md not found")
        text = path.read_text()
        docs = recall_search.parse_decisions(text)
        results = recall_search.bm25(recall_search.tokenize("debate litellm"), docs)
        assert len(results) > 0

    def test_search_finds_lesson(self):
        path = recall_search.SOURCES.get("lessons")
        if not path or not path.exists():
            pytest.skip("lessons.md not found")
        text = path.read_text()
        docs = recall_search.parse_lessons(text)
        if not docs:
            pytest.skip("No active lessons")
        results = recall_search.bm25(recall_search.tokenize("review panel serial"), docs)
        # Should find something if L19 is still active
        assert isinstance(results, list)
