#!/usr/bin/env python3.11
# hook-class: advisory
"""PreToolUse hook: inject relevant context before Write/Edit.

Gathers test file names, local import signatures, and recent git history
for the target file. Returns additionalContext so Claude has better
information before writing code.

Tier: T0 (always active, informational only, never blocks)
Event: PreToolUse Write|Edit
"""

import json
import os
import re
import subprocess
import sys


# Context budget: cap total injected context
MAX_CONTEXT_CHARS = 3000
MAX_TEST_NAMES = 15
MAX_IMPORT_MODULES = 5
MAX_SIGS_PER_MODULE = 10
MAX_GIT_LOG_ENTRIES = 5


def get_project_root():
    """Get git project root."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def find_test_file(file_path, project_root):
    """Find the test file for a given source file."""
    basename = os.path.basename(file_path)
    rel_dir = os.path.relpath(os.path.dirname(file_path), project_root)

    candidates = [
        os.path.join(project_root, "tests", f"test_{basename}"),
        os.path.join(project_root, rel_dir, "tests", f"test_{basename}"),
        os.path.join(project_root, rel_dir, f"test_{basename}"),
    ]

    for candidate in candidates:
        candidate = os.path.normpath(candidate)
        if os.path.isfile(candidate):
            return candidate
    return None


def get_test_context(file_path, project_root):
    """Extract test function/class names from the test file."""
    test_file = find_test_file(file_path, project_root)
    if not test_file:
        return None

    try:
        with open(test_file, "r") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return None

    names = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def test_") or stripped.startswith("class Test"):
            sig = stripped.split("(")[0]  # "def test_foo" or "class TestFoo"
            names.append(sig)
            if len(names) >= MAX_TEST_NAMES:
                break

    if not names:
        return None

    rel_test = os.path.relpath(test_file, project_root)
    header = f"Test file ({rel_test}):"
    body = "\n".join(f"  {n}" for n in names)
    return f"{header}\n{body}"


def resolve_local_module(module_name, source_file, project_root):
    """Resolve a Python module name to a local file path."""
    parts = module_name.split(".")
    source_dir = os.path.dirname(source_file)

    candidates = [
        os.path.join(source_dir, *parts) + ".py",
        os.path.join(project_root, *parts) + ".py",
        os.path.join(project_root, *parts, "__init__.py"),
    ]

    for candidate in candidates:
        candidate = os.path.normpath(candidate)
        if os.path.isfile(candidate):
            return candidate
    return None


def extract_signatures(file_path):
    """Extract function and class signatures from a Python file."""
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return []

    sigs = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def ") or stripped.startswith("class "):
            # Take up to the colon, strip trailing colon
            sig = stripped.split("#")[0].rstrip()
            if sig.endswith(":"):
                sig = sig[:-1]
            sigs.append(sig)
            if len(sigs) >= MAX_SIGS_PER_MODULE:
                break
    return sigs


def get_import_context(file_path, project_root):
    """Extract local imports and their function/class signatures."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return None

    # Match: "from X import ..." and "import X"
    import_re = re.compile(
        r"^(?:from\s+(\S+)\s+import|import\s+(\S+))", re.MULTILINE
    )
    matches = import_re.findall(content)

    sections = []
    seen_modules = set()
    for from_mod, import_mod in matches:
        module_name = from_mod or import_mod
        if module_name in seen_modules:
            continue
        seen_modules.add(module_name)

        module_path = resolve_local_module(module_name, file_path, project_root)
        if not module_path:
            continue

        sigs = extract_signatures(module_path)
        if not sigs:
            continue

        rel_path = os.path.relpath(module_path, project_root)
        sections.append(f"  {rel_path}:")
        for sig in sigs:
            sections.append(f"    {sig}")

        if len(sections) > MAX_IMPORT_MODULES * (MAX_SIGS_PER_MODULE + 1):
            break

    if not sections:
        return None
    return "Local import signatures:\n" + "\n".join(sections)


def get_git_context(file_path):
    """Get recent git log for the file."""
    try:
        result = subprocess.run(
            ["git", "log", f"--oneline", f"-{MAX_GIT_LOG_ENTRIES}", "--", file_path],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            body = "\n".join(f"  {line}" for line in lines)
            return f"Recent changes:\n{body}"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def main():
    raw = sys.stdin.read()
    try:
        input_data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    # Only Python files for v1
    if not file_path.endswith(".py"):
        sys.exit(0)

    # Skip new file creation
    if not os.path.isfile(file_path):
        sys.exit(0)

    project_root = get_project_root()
    if not project_root:
        sys.exit(0)

    # Skip files outside project
    try:
        os.path.relpath(file_path, project_root)
    except ValueError:
        sys.exit(0)

    # Session-level dedup: skip re-gathering if already injected for this file
    session_id = os.environ.get("CLAUDE_SESSION_ID", str(os.getppid()))
    cache_file = f"/tmp/claude-context-inject-{session_id}.json"
    cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file) as cf:
                cache = json.load(cf)
        except (json.JSONDecodeError, OSError):
            cache = {}

    if file_path in cache:
        # Context already injected on first edit — don't re-inject
        sys.exit(0)

    # Gather context sections
    parts = []

    test_ctx = get_test_context(file_path, project_root)
    if test_ctx:
        parts.append(test_ctx)

    import_ctx = get_import_context(file_path, project_root)
    if import_ctx:
        parts.append(import_ctx)

    git_ctx = get_git_context(file_path)
    if git_ctx:
        parts.append(git_ctx)

    if not parts:
        sys.exit(0)

    rel_file = os.path.relpath(file_path, project_root)
    context = f"Context for {rel_file}:\n" + "\n".join(parts)

    # Cap size
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[: MAX_CONTEXT_CHARS - 3] + "..."

    # Cache for this session
    cache[file_path] = context
    try:
        with open(cache_file, "w") as cf:
            json.dump(cache, cf)
    except OSError:
        pass

    result = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "additionalContext": context,
        }
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
