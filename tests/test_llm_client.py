#!/usr/bin/env python3.11
"""Unit tests for scripts/llm_client.py.

Tests error classification, retry logic, URL normalization, and key loading
without making any actual HTTP or LLM calls.

Run with: python3.11 tests/test_llm_client.py
Exit 0 = all tests pass.
Exit 1 = at least one test failed.
"""

import os
import sys
import urllib.error
from pathlib import Path

# Add scripts/ to import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from llm_client import (
    LLMError,
    _categorize_error,
    _get_base_url,
    _is_retryable,
    _load_api_key,
)


def _make_http_error(code, msg="error"):
    return urllib.error.HTTPError(
        url="http://test", code=code, msg=msg, hdrs={}, fp=None
    )


def test_llm_error_has_category():
    """LLMError stores category and str() returns the message."""
    for cat in ("timeout", "rate_limit", "auth", "network", "parse", "unknown"):
        err = LLMError(f"test {cat}", category=cat)
        assert err.category == cat, f"expected category={cat}, got {err.category}"
        assert str(err) == f"test {cat}", f"str mismatch for {cat}"


def test_categorize_error_timeout():
    """TimeoutError and messages containing 'timeout' -> 'timeout'."""
    assert _categorize_error(TimeoutError("timed out")) == "timeout"
    assert _categorize_error(Exception("connection timeout occurred")) == "timeout"


def test_categorize_error_rate_limit():
    """HTTP 429 -> 'rate_limit'."""
    assert _categorize_error(_make_http_error(429)) == "rate_limit"


def test_categorize_error_auth():
    """HTTP 401 and 403 -> 'auth'."""
    assert _categorize_error(_make_http_error(401)) == "auth"
    assert _categorize_error(_make_http_error(403)) == "auth"


def test_categorize_error_network():
    """URLError and ConnectionError -> 'network'."""
    assert _categorize_error(urllib.error.URLError("no host")) == "network"
    assert _categorize_error(ConnectionError("refused")) == "network"


def test_categorize_error_unknown():
    """Generic ValueError -> 'unknown'."""
    assert _categorize_error(ValueError("bad value")) == "unknown"


def test_is_retryable_transient():
    """429, 503, ConnectionError, TimeoutError are all retryable."""
    assert _is_retryable(_make_http_error(429)) is True
    assert _is_retryable(_make_http_error(503)) is True
    assert _is_retryable(ConnectionError("refused")) is True
    assert _is_retryable(TimeoutError("timed out")) is True


def test_is_retryable_permanent():
    """400, 404, ValueError are not retryable."""
    assert _is_retryable(_make_http_error(400)) is False
    assert _is_retryable(_make_http_error(404)) is False
    assert _is_retryable(ValueError("bad")) is False


def test_get_base_url_normalization():
    """LITELLM_URL without /v1 gets it appended; trailing slash handled."""
    old = os.environ.get("LITELLM_URL")
    try:
        os.environ["LITELLM_URL"] = "http://localhost:4000"
        assert _get_base_url() == "http://localhost:4000/v1"

        os.environ["LITELLM_URL"] = "http://localhost:4000/"
        assert _get_base_url() == "http://localhost:4000/v1"

        os.environ["LITELLM_URL"] = "http://localhost:4000/v1"
        assert _get_base_url() == "http://localhost:4000/v1"
    finally:
        if old is None:
            os.environ.pop("LITELLM_URL", None)
        else:
            os.environ["LITELLM_URL"] = old


def test_load_api_key_from_env():
    """LITELLM_MASTER_KEY env var is returned by _load_api_key."""
    old = os.environ.get("LITELLM_MASTER_KEY")
    try:
        os.environ["LITELLM_MASTER_KEY"] = "test-key-abc123"
        assert _load_api_key() == "test-key-abc123"
    finally:
        if old is None:
            os.environ.pop("LITELLM_MASTER_KEY", None)
        else:
            os.environ["LITELLM_MASTER_KEY"] = old


def test_no_credential_leakage_in_error():
    """LLMError str/repr must not leak the real LITELLM_MASTER_KEY."""
    fake_key = "sk-test-secret-key-12345"
    err = LLMError(f"API call failed with key {fake_key}", category="auth")

    # The fake key is in the message (that's fine -- it's fake).
    # The real key must NOT appear.
    real_key = _load_api_key()
    if real_key:
        assert real_key not in str(err), "real API key leaked in str(LLMError)"
        assert real_key not in repr(err), "real API key leaked in repr(LLMError)"

    # Verify the error still carries the message we gave it
    assert fake_key in str(err)


TESTS = [
    test_llm_error_has_category,
    test_categorize_error_timeout,
    test_categorize_error_rate_limit,
    test_categorize_error_auth,
    test_categorize_error_network,
    test_categorize_error_unknown,
    test_is_retryable_transient,
    test_is_retryable_permanent,
    test_get_base_url_normalization,
    test_load_api_key_from_env,
    test_no_credential_leakage_in_error,
]


def main():
    failures = []
    for fn in TESTS:
        name = fn.__name__
        try:
            fn()
            print(f"PASS: {name}")
        except AssertionError as e:
            print(f"FAIL: {name} — {e}", file=sys.stderr)
            failures.append((name, str(e)))
        except Exception as e:
            print(f"ERROR: {name} — {type(e).__name__}: {e}", file=sys.stderr)
            failures.append((name, f"{type(e).__name__}: {e}"))

    if failures:
        print(f"\n{len(failures)} test(s) failed", file=sys.stderr)
        return 1
    print(f"\nAll {len(TESTS)} tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
