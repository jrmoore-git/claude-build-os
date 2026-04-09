#!/usr/bin/env python3
"""
llm_client.py — Shared LLM client for Build OS

Routes all model calls through LiteLLM (OpenAI-compatible) at localhost:4000.
Replaces per-file urllib.request boilerplate with a 3-function API.

Functions:
    llm_call()      — returns text content (raises LLMError on failure)
    llm_call_json() — returns parsed JSON (raises LLMError on failure)
    llm_call_raw()  — returns dict with content, model, usage (raises LLMError on failure)

Errors:
    LLMError        — structured exception with .category attribute
                      (timeout, rate_limit, auth, network, parse, unknown)

Retries transient errors (429, 5xx, network) with exponential backoff (3 attempts).
Set BUILDOS_LLM_LEGACY=1 to fall back to raw urllib (rollback path).
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Structured error
# ---------------------------------------------------------------------------

class LLMError(Exception):
    """Raised when an LLM call fails. Preserves error category and original cause."""

    def __init__(self, message, *, category="unknown"):
        super().__init__(message)
        self.category = category  # timeout, rate_limit, auth, network, parse, unknown

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_DEFAULT_MODEL = "claude-sonnet-4-6"
_DEFAULT_URL = "http://localhost:4000/v1"
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_api_key():
    """Load LITELLM_MASTER_KEY from env, falling back to .env file."""
    key = os.environ.get("LITELLM_MASTER_KEY")
    if key:
        return key
    env_path = _PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("LITELLM_MASTER_KEY=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip("'\"")
    return None


def _get_base_url():
    """Get LiteLLM base URL."""
    url = os.environ.get("LITELLM_URL", "http://localhost:4000")
    # Normalize: ensure /v1 suffix for OpenAI SDK
    url = url.rstrip("/")
    if not url.endswith("/v1"):
        url += "/v1"
    return url


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0  # seconds


def _is_retryable(exc):
    """Check if an exception is transient and worth retrying."""
    # OpenAI SDK errors with status codes
    if hasattr(exc, "status_code") and exc.status_code in (429, 500, 502, 503, 504):
        return True
    # urllib HTTP errors — check BEFORE URLError (HTTPError is a subclass of URLError)
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in (429, 500, 502, 503, 504)
    # Network / connection errors (URLError without HTTP status, plus others)
    if isinstance(exc, (urllib.error.URLError, ConnectionError, TimeoutError, OSError)):
        return True
    # OpenAI SDK exception class names (avoid importing them)
    if type(exc).__name__ in ("RateLimitError", "APIConnectionError", "InternalServerError"):
        return True
    return False


def _categorize_error(exc):
    """Classify an exception into an error category for LLMError."""
    if isinstance(exc, TimeoutError) or "timeout" in str(exc).lower():
        return "timeout"
    if type(exc).__name__ == "RateLimitError":
        return "rate_limit"
    if hasattr(exc, "status_code") and exc.status_code == 429:
        return "rate_limit"
    if isinstance(exc, urllib.error.HTTPError) and exc.code == 429:
        return "rate_limit"
    if type(exc).__name__ == "AuthenticationError":
        return "auth"
    if hasattr(exc, "status_code") and exc.status_code in (401, 403):
        return "auth"
    if isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 403):
        return "auth"
    if isinstance(exc, (urllib.error.URLError, ConnectionError)):
        return "network"
    if type(exc).__name__ == "APIConnectionError":
        return "network"
    return "unknown"


def _call_with_retry(fn, *args, **kwargs):
    """Call fn with exponential backoff retry for transient errors.

    Raises LLMError on final failure with category and original cause preserved.
    """
    last_exc = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt < _MAX_RETRIES and _is_retryable(e):
                delay = _RETRY_BASE_DELAY * (2 ** attempt)
                print(
                    f"LLM transient error (attempt {attempt + 1}/{_MAX_RETRIES + 1}): "
                    f"{type(e).__name__}: {e}. Retrying in {delay:.0f}s...",
                    file=sys.stderr,
                )
                time.sleep(delay)
                continue
            category = _categorize_error(e)
            raise LLMError(
                f"LLM call failed ({type(e).__name__}): {e}", category=category
            ) from e
    # Unreachable, but satisfy type checkers
    raise LLMError(f"LLM call failed: {last_exc}", category="unknown")


# ---------------------------------------------------------------------------
# Markdown fence stripping
# ---------------------------------------------------------------------------

def _strip_markdown_fences(text):
    """Strip ```json ... ``` or ``` ... ``` wrappers from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        # Remove first line (```json or ```)
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        # Remove trailing ```
        text = text.rsplit("```", 1)[0].strip()
    return text


def _extract_json(text):
    """Parse JSON from LLM text, handling markdown fences and embedded JSON."""
    text = _strip_markdown_fences(text)

    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Look for JSON array in text
    match = re.search(r'\[\s*\{.*?\}\s*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Look for JSON object in text
    match = re.search(r'\{\s*".*?\s*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


# ---------------------------------------------------------------------------
# Legacy urllib path (BUILDOS_LLM_LEGACY=1)
# ---------------------------------------------------------------------------

def _legacy_call(system, user, *, model, temperature, max_tokens, timeout,
                 base_url, api_key):
    """Raw urllib call matching the old pattern. Returns (content, model_used, usage)."""
    url = base_url.rstrip("/")
    # Strip /v1 suffix for legacy path which appends /chat/completions
    if url.endswith("/v1"):
        url = url[:-3]
    url = f"{url}/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    resp = urllib.request.urlopen(req, timeout=timeout)
    body = json.loads(resp.read().decode())
    content = body["choices"][0]["message"]["content"]
    model_used = body.get("model", model)
    usage = body.get("usage", {})
    return content, model_used, usage


# ---------------------------------------------------------------------------
# OpenAI SDK path (default)
# ---------------------------------------------------------------------------

def _sdk_call(system, user, *, model, temperature, max_tokens, timeout,
              base_url, api_key):
    """OpenAI SDK call via LiteLLM. Returns (content, model_used, usage)."""
    from openai import OpenAI

    client = OpenAI(base_url=base_url, api_key=api_key)

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "timeout": timeout,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    response = client.chat.completions.create(**kwargs)

    content = response.choices[0].message.content
    model_used = response.model or model
    usage = {}
    if response.usage:
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
    return content, model_used, usage


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def _normalize_url(url):
    """Ensure URL has /v1 suffix for OpenAI SDK compatibility."""
    url = url.rstrip("/")
    if not url.endswith("/v1"):
        url += "/v1"
    return url


def _dispatch(system, user, *, model, temperature, max_tokens, timeout,
              base_url, api_key):
    """Route to SDK or legacy based on feature flag."""
    base_url = _normalize_url(base_url)
    if os.environ.get("BUILDOS_LLM_LEGACY") == "1":
        return _legacy_call(system, user, model=model, temperature=temperature,
                            max_tokens=max_tokens, timeout=timeout,
                            base_url=base_url, api_key=api_key)
    return _sdk_call(system, user, model=model, temperature=temperature,
                     max_tokens=max_tokens, timeout=timeout,
                     base_url=base_url, api_key=api_key)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def llm_call(system, user, *, model=_DEFAULT_MODEL, temperature=0.0,
             max_tokens=None, timeout=90, base_url=None, api_key=None):
    """Single-shot LLM call. Returns text content.

    Raises LLMError on failure (with category: timeout, rate_limit, auth, network, parse, unknown).
    """
    base_url = base_url or _get_base_url()
    api_key = api_key or _load_api_key()
    if not api_key:
        raise LLMError("LITELLM_MASTER_KEY not set", category="auth")

    content, _, _ = _call_with_retry(
        _dispatch, system, user, model=model, temperature=temperature,
        max_tokens=max_tokens, timeout=timeout,
        base_url=base_url, api_key=api_key,
    )
    return content.strip() if content else ""


def llm_call_json(system, user, *, model=_DEFAULT_MODEL, temperature=0.0,
                  max_tokens=None, timeout=90, base_url=None, api_key=None):
    """Single-shot LLM call. Returns parsed JSON.

    Raises LLMError on LLM failure or JSON parse failure (category='parse').
    """
    text = llm_call(system, user, model=model, temperature=temperature,
                    max_tokens=max_tokens, timeout=timeout,
                    base_url=base_url, api_key=api_key)

    result = _extract_json(text)
    if result is None:
        raise LLMError(
            f"JSON parse failed. Response: {text[:500]}", category="parse"
        )
    return result


def llm_call_raw(system, user, *, model=_DEFAULT_MODEL, temperature=0.0,
                 max_tokens=None, timeout=90, base_url=None, api_key=None):
    """Single-shot LLM call. Returns dict with 'content', 'model', 'usage' keys.

    Raises LLMError on failure.
    """
    base_url = base_url or _get_base_url()
    api_key = api_key or _load_api_key()
    if not api_key:
        raise LLMError("LITELLM_MASTER_KEY not set", category="auth")

    content, model_used, usage = _call_with_retry(
        _dispatch, system, user, model=model, temperature=temperature,
        max_tokens=max_tokens, timeout=timeout,
        base_url=base_url, api_key=api_key,
    )
    return {
        "content": content.strip() if content else "",
        "model": model_used,
        "usage": usage,
    }
