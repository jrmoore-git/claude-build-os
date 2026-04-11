#!/usr/bin/env python3.11
"""
research.py — Deep research via Perplexity Sonar Deep Research API.

Submits a research question async, polls for completion, returns sourced markdown.

Usage:
    python3.11 scripts/research.py "What are the best practices for X?"
    python3.11 scripts/research.py --file questions.txt
    python3.11 scripts/research.py --effort high --academic "quantum computing advances 2026"
    python3.11 scripts/research.py --sync "quick factual question"

Output goes to stdout (markdown with citations). Use --output to write to a file.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
API_BASE = "https://api.perplexity.ai"


def load_api_key():
    key = os.environ.get("PERPLEXITY_API_KEY")
    if key:
        return key
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("PERPLEXITY_API_KEY=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip("'\"")
    print("ERROR: PERPLEXITY_API_KEY not found in env or .env", file=sys.stderr)
    sys.exit(1)


def api_request(method, path, key, body=None, timeout=30):
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"ERROR: HTTP {e.code} from {path}: {error_body}", file=sys.stderr)
        sys.exit(1)


def submit_async(key, messages, model="sonar-deep-research", effort="medium", academic=False):
    request_body = {
        "model": model,
        "messages": messages,
    }
    if effort != "medium":
        request_body["reasoning_effort"] = effort
    if academic:
        request_body["search_mode"] = "academic"

    # Async endpoint requires body nested under "request" key
    body = {"request": request_body}

    result = api_request("POST", "/v1/async/sonar", key, body)
    return result["id"]


def poll_async(key, request_id, poll_interval=5, max_wait=600):
    elapsed = 0
    while elapsed < max_wait:
        result = api_request("GET", f"/v1/async/sonar/{request_id}", key)

        # API may return the single request or a list — handle both
        if isinstance(result, list):
            matches = [r for r in result if r.get("id") == request_id]
            if matches:
                result = matches[0]
            else:
                time.sleep(poll_interval)
                elapsed += poll_interval
                continue

        # If result has a "requests" list (list endpoint), find ours
        if "requests" in result and isinstance(result["requests"], list):
            matches = [r for r in result["requests"] if r.get("id") == request_id]
            if matches:
                result = matches[0]

        status = result.get("status", "UNKNOWN")

        if status == "COMPLETED":
            return result
        elif status == "FAILED":
            error = result.get("error_message", "unknown error")
            print(f"ERROR: Research failed: {error}", file=sys.stderr)
            sys.exit(1)

        # Progress indicator
        print(f"  [{elapsed}s] status: {status}...", file=sys.stderr)
        time.sleep(poll_interval)
        elapsed += poll_interval

    print(f"ERROR: Timed out after {max_wait}s waiting for research", file=sys.stderr)
    sys.exit(1)


def sync_research(key, messages, model="sonar-deep-research", effort="medium", academic=False):
    body = {
        "model": model,
        "messages": messages,
    }
    if effort != "medium":
        body["reasoning_effort"] = effort
    if academic:
        body["search_mode"] = "academic"

    # Deep research can take minutes — long timeout
    return api_request("POST", "/chat/completions", key, body, timeout=300)


def format_output(result, async_mode=True):
    lines = []

    if async_mode:
        # Async result has response nested
        response = result.get("response", result)
    else:
        response = result

    # Extract content
    choices = response.get("choices", [])
    if not choices:
        return "ERROR: No content in response"

    content = choices[0].get("message", {}).get("content", "")
    lines.append(content)

    # Extract citations
    citations = response.get("citations", [])
    if citations:
        lines.append("\n---\n## Sources\n")
        for i, cite in enumerate(citations, 1):
            if isinstance(cite, dict):
                title = cite.get("title", "")
                url = cite.get("url", cite.get("link", ""))
                date = cite.get("date", "")
                date_str = f" ({date})" if date else ""
                lines.append(f"{i}. [{title or url}]({url}){date_str}")
            elif isinstance(cite, str):
                lines.append(f"{i}. {cite}")

    # Usage stats to stderr
    usage = response.get("usage", {})
    if usage:
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        print(
            f"Tokens — prompt: {prompt_tokens}, completion: {completion_tokens}, "
            f"total: {prompt_tokens + completion_tokens}",
            file=sys.stderr,
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Deep research via Perplexity Sonar")
    parser.add_argument("question", nargs="?", help="Research question")
    parser.add_argument("--file", help="Read question from file")
    parser.add_argument("--output", "-o", help="Write output to file instead of stdout")
    parser.add_argument(
        "--effort",
        choices=["minimal", "low", "medium", "high"],
        default="medium",
        help="Reasoning effort (default: medium)",
    )
    parser.add_argument("--academic", action="store_true", help="Prioritize scholarly sources")
    parser.add_argument("--sync", action="store_true", help="Use sync API (shorter timeout, simpler)")
    parser.add_argument(
        "--model",
        default="sonar-deep-research",
        help="Model name (default: sonar-deep-research)",
    )
    parser.add_argument("--system", help="System prompt to guide output structure")
    parser.add_argument("--max-wait", type=int, default=600, help="Max seconds to wait for async (default: 600)")
    parser.add_argument("--poll-interval", type=int, default=5, help="Seconds between polls (default: 5)")

    args = parser.parse_args()

    # Get question
    if args.file:
        question = Path(args.file).read_text().strip()
    elif args.question:
        question = args.question
    else:
        parser.error("Provide a question as argument or via --file")

    key = load_api_key()

    # Build messages
    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": question})

    if args.sync:
        print("Researching (sync)...", file=sys.stderr)
        result = sync_research(key, messages, args.model, args.effort, args.academic)
        output = format_output(result, async_mode=False)
    else:
        print("Submitting research (async)...", file=sys.stderr)
        request_id = submit_async(key, messages, args.model, args.effort, args.academic)
        print(f"Request ID: {request_id}", file=sys.stderr)
        result = poll_async(key, request_id, args.poll_interval, args.max_wait)
        output = format_output(result, async_mode=True)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
