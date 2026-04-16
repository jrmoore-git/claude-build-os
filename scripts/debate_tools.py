#!/usr/bin/env python3.11
"""debate_tools.py -- Read-only verifier tools for debate challengers.

Deny-by-default data egress: tools return only structured metadata,
booleans, counts, and aggregates. Never raw code or DB rows.
"""
import glob
import json
import os
import re
from datetime import datetime

# Resolve project root
try:
    import subprocess
    PROJECT_ROOT = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
    ).strip()
except (subprocess.CalledProcessError, FileNotFoundError):
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Safety constants ---


ALLOWED_FILE_SETS = {
    "scripts": "scripts/*.py",
    # Skills live under .claude/skills/, not skills/. Earlier value
    # 'skills/*/SKILL.md' silently matched zero files, causing every
    # check_code_presence(file_set='skills') call to return exists=false.
    "skills": ".claude/skills/*/SKILL.md",
    "config": "config/*.json",
    "hooks": "hooks/*.py",
    "tests": "tests/*.py",
    "rules": ".claude/rules/*.md",
    "docs": "docs/*.md",
}

ALLOWED_CONFIG_KEYS = {"judge_default", "refine_rotation", "persona_model_map",
                       "single_review_default", "version"}

SECRET_PATTERNS = {"key", "secret", "token", "password", "credential", "api_key"}

MAX_SUBSTRING_LEN = 200
MAX_RESULT_LEN = 5000  # increased to support read_file_snippet (50 lines)
MAX_SNIPPET_LINES = 50

ALLOWED_SNIPPET_PATHS = {
    "scripts": "scripts/",
    "config": "config/",
    "tests": "tests/",
    "hooks": "hooks/",
    "rules": ".claude/rules/",
    "docs": "docs/",
}
SNIPPET_BLOCKED_EXTENSIONS = {".env", ".key", ".pem", ".p12", ".json.bak"}


# --- Tool implementations ---

def _get_job_schedule(args):
    name = args.get("job_name", "")
    if not name or not isinstance(name, str):
        return json.dumps({"error": "job_name must be a non-empty string"})
    path = os.path.join(PROJECT_ROOT, "config", "jobs-config.json")
    with open(path) as f:
        data = json.load(f)
    for job in data.get("jobs", []):
        if job.get("name") == name:
            sched = job.get("schedule", {})
            return json.dumps({
                "name": job["name"],
                "schedule_expr": sched.get("expr", ""),
                "timezone": sched.get("timezone", "America/Los_Angeles"),
                "enabled": bool(job.get("enabled", False)),
            })
    return json.dumps({"error": "job not found"})


def _check_code_presence(args):
    substring = args.get("substring", "")
    file_set = args.get("file_set", "")
    if file_set not in ALLOWED_FILE_SETS:
        return json.dumps({"error": f"file_set not allowed: {file_set}"})
    if not substring or len(substring) > MAX_SUBSTRING_LEN:
        return json.dumps({"error": f"substring must be 1-{MAX_SUBSTRING_LEN} chars"})
    pattern = os.path.join(PROJECT_ROOT, ALLOWED_FILE_SETS[file_set])
    matches = 0
    for filepath in glob.glob(pattern):
        try:
            with open(filepath, "rb") as f:
                head = f.read(1024)
                if b"\x00" in head:
                    continue
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                if substring in f.read():
                    matches += 1
        except OSError:
            continue
    return json.dumps({"exists": matches > 0, "match_count": matches})


def _read_config_value(args):
    key = args.get("key", "")
    if key not in ALLOWED_CONFIG_KEYS:
        return json.dumps({"error": f"key not allowed: {key}"})
    if any(p in key.lower() for p in SECRET_PATTERNS):
        return json.dumps({"error": "key matches secret pattern"})
    path = os.path.join(PROJECT_ROOT, "config", "debate-models.json")
    with open(path) as f:
        data = json.load(f)
    if key not in data:
        return json.dumps({"error": f"key not found in config: {key}"})
    return json.dumps({"key": key, "value": data[key]})


def _find_test_files(module_path):
    """Find test files for a module by scanning tests/ and normalize-matching.

    Instead of guessing candidate filenames (which breaks on naming mismatches
    like hyphens vs underscores), scan the actual test directory and match
    with normalization. Used by both check_test_coverage and manifest.
    """
    name_no_ext = os.path.splitext(os.path.basename(module_path))[0]
    # Normalize: hyphens → underscores (Python convention for test files)
    normalized = name_no_ext.replace("-", "_")

    test_dir = os.path.join(PROJECT_ROOT, "tests")
    if not os.path.isdir(test_dir):
        return []

    found = []
    for entry in sorted(os.listdir(test_dir)):
        if not entry.endswith(".py"):
            continue
        entry_norm = entry.replace("-", "_")
        # Exact match: test_hook_bash_fix_forward.py
        if entry_norm == f"test_{normalized}.py":
            found.append(os.path.join("tests", entry))
        # Suffix match: test_hook_bash_fix_forward_test.py
        elif entry_norm == f"{normalized}_test.py":
            found.append(os.path.join("tests", entry))
        # Prefix match: test_debate_commands.py for debate.py
        elif entry_norm.startswith(f"test_{normalized}_"):
            found.append(os.path.join("tests", entry))

    return found


def _check_test_coverage(args):
    module_path = args.get("module_path", "")
    if not module_path or len(module_path) > 200:
        return json.dumps({"error": "module_path must be 1-200 chars"})
    if ".." in module_path or module_path.startswith("/"):
        return json.dumps({"error": "invalid path: traversal or absolute not allowed"})

    # Strip leading ./ if present (not lstrip — that strips individual chars)
    if module_path.startswith("./"):
        module_path = module_path[2:]

    found = _find_test_files(module_path)
    return json.dumps({"module": module_path, "has_test": len(found) > 0, "test_files": found})


def _get_recent_commits(args):
    file_paths = args.get("file_paths", [])
    limit = min(max(int(args.get("limit", 10)), 1), 50)

    if not isinstance(file_paths, list) or not file_paths or len(file_paths) > 5:
        return json.dumps({"error": "file_paths must be a list of 1-5 paths"})

    for fp in file_paths:
        if ".." in fp or fp.startswith("/"):
            return json.dumps({"error": f"invalid path: {fp}"})

    try:
        cmd = ["git", "log", "--oneline", f"-{limit}", "--"] + file_paths
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return json.dumps({"error": "git log failed"})

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split(" ", 1)
            commits.append({"hash": parts[0][:7], "message": (parts[1] if len(parts) > 1 else "")[:100]})

        return json.dumps({"files": file_paths, "commit_count": len(commits), "commits": commits})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "git log timeout"})


def _check_function_exists(args):
    identifier = args.get("identifier", "")
    file_set = args.get("file_set", "")

    if not identifier or len(identifier) > 100:
        return json.dumps({"error": "identifier must be 1-100 chars"})
    if file_set not in ALLOWED_FILE_SETS:
        return json.dumps({"error": f"file_set not allowed: {file_set}"})
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_.]*$", identifier):
        return json.dumps({"error": "invalid identifier format"})

    pattern = os.path.join(PROJECT_ROOT, ALLOWED_FILE_SETS[file_set])
    matches = []
    search_name = identifier.split(".")[0]  # For Class.method, search for class name

    for filepath in glob.glob(pattern):
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if re.search(rf"^(?:def|class)\s+{re.escape(search_name)}\s*[\(:]", content, re.MULTILINE):
                matches.append(filepath.replace(PROJECT_ROOT, "").lstrip("/"))
        except OSError:
            continue

    return json.dumps({"identifier": identifier, "exists": len(matches) > 0, "files": matches})


def _read_file_snippet(args):
    """Read a scoped snippet from a file. Returns line-numbered content."""
    file_path = args.get("file_path", "")
    start_line = int(args.get("start_line", 1))
    max_lines = min(int(args.get("max_lines", MAX_SNIPPET_LINES)), MAX_SNIPPET_LINES)

    if not file_path or len(file_path) > 200:
        return json.dumps({"error": "file_path must be 1-200 chars"})
    if ".." in file_path or file_path.startswith("/"):
        return json.dumps({"error": "invalid path: traversal or absolute not allowed"})
    if start_line < 1:
        start_line = 1

    # Check file is in an allowed directory
    # Strip leading ./ but not bare . (preserves .claude/ paths)
    if file_path.startswith("./"):
        file_path = file_path[2:]
    allowed = False
    for prefix in ALLOWED_SNIPPET_PATHS.values():
        if file_path.startswith(prefix):
            allowed = True
            break
    if not allowed:
        return json.dumps({"error": f"file not in allowed directories: {list(ALLOWED_SNIPPET_PATHS.keys())}"})

    # Block sensitive extensions
    _, ext = os.path.splitext(file_path)
    if ext in SNIPPET_BLOCKED_EXTENSIONS:
        return json.dumps({"error": f"blocked extension: {ext}"})

    # Block files with secret-like names
    basename = os.path.basename(file_path).lower()
    if any(p in basename for p in SECRET_PATTERNS):
        return json.dumps({"error": "file name matches secret pattern"})

    full_path = os.path.join(PROJECT_ROOT, file_path)
    if not os.path.isfile(full_path):
        return json.dumps({"error": f"file not found: {file_path}"})

    try:
        with open(full_path, "rb") as f:
            head = f.read(1024)
            if b"\x00" in head:
                return json.dumps({"error": "binary file, cannot read"})

        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()

        total_lines = len(all_lines)
        end_line = min(start_line + max_lines - 1, total_lines)
        snippet_lines = all_lines[start_line - 1:end_line]

        numbered = []
        for i, line in enumerate(snippet_lines, start=start_line):
            numbered.append(f"{i:4d} | {line.rstrip()}")

        snippet_text = "\n".join(numbered)
        return json.dumps({
            "file": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "total_lines": total_lines,
            "content": snippet_text,
        })
    except OSError as e:
        return json.dumps({"error": str(e)})


# --- Repo manifest (deterministic discovery) ---


MAX_MANIFEST_FILES = 50

# Directories included in the manifest. Challengers see these as
# ground-truth facts about repo structure — no tool calls needed.
MANIFEST_DIRS = {
    "scripts": "scripts",
    "hooks": "hooks",
    "tests": "tests",
    "skills": ".claude/skills",
    "rules": ".claude/rules",
    "config": "config",
    "docs": "docs",
}


def generate_repo_manifest():
    """Build a deterministic repo manifest: directories, files, and exports.

    Returns a dict with:
      directories: list of top-level dirs that exist
      files: {category: [relative paths]}
      exports: {file: [function/class names]}  (Python files only)
    """
    manifest = {"directories": [], "files": {}, "exports": {}}

    # Top-level directories
    try:
        entries = os.listdir(PROJECT_ROOT)
    except OSError:
        return manifest
    manifest["directories"] = sorted(
        e for e in entries
        if os.path.isdir(os.path.join(PROJECT_ROOT, e)) and not e.startswith(".")
    )
    # Include .claude since skills/rules live there
    if os.path.isdir(os.path.join(PROJECT_ROOT, ".claude")):
        manifest["directories"].append(".claude")
        manifest["directories"].sort()

    # Files per category
    for category, dirpath in MANIFEST_DIRS.items():
        full_dir = os.path.join(PROJECT_ROOT, dirpath)
        if not os.path.isdir(full_dir):
            continue
        files = []
        for entry in sorted(os.listdir(full_dir)):
            entry_path = os.path.join(full_dir, entry)
            if os.path.isfile(entry_path):
                # Skip secret-like files
                if any(p in entry.lower() for p in SECRET_PATTERNS):
                    continue
                _, ext = os.path.splitext(entry)
                if ext in SNIPPET_BLOCKED_EXTENSIONS:
                    continue
                rel = os.path.join(dirpath, entry)
                files.append(rel)
        # For skills, list subdirectory names instead of files
        if category == "skills":
            files = []
            for entry in sorted(os.listdir(full_dir)):
                skill_dir = os.path.join(full_dir, entry)
                if os.path.isdir(skill_dir) and os.path.isfile(
                    os.path.join(skill_dir, "SKILL.md")
                ):
                    files.append(entry)
        total = len(files)
        manifest["files"][category] = files[:MAX_MANIFEST_FILES]
        if total > MAX_MANIFEST_FILES:
            manifest.setdefault("truncated", {})[category] = total

    # Exports for Python files (hooks + scripts)
    for category in ("hooks", "scripts"):
        for rel_path in manifest["files"].get(category, []):
            full_path = os.path.join(PROJECT_ROOT, rel_path)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except OSError:
                continue
            exports = []
            for match in re.finditer(
                r"^(?:def|class)\s+([a-zA-Z_]\w*)", content, re.MULTILINE
            ):
                exports.append(match.group(1))
            if exports:
                manifest["exports"][rel_path] = exports[:30]

    # Test coverage mapping: script → test files
    manifest["test_coverage"] = {}
    for category in ("hooks", "scripts"):
        for rel_path in manifest["files"].get(category, []):
            test_files = _find_test_files(rel_path)
            if test_files:
                manifest["test_coverage"][rel_path] = test_files

    return manifest


def format_manifest_context(manifest):
    """Format a manifest dict as text suitable for injection into LLM context."""
    lines = [
        "## Repository Structure (deterministic — generated by code, not a model)",
        "",
        "This manifest was produced by walking the filesystem. Every file, directory,",
        "and function listed below exists. Do not use tool calls to re-verify existence",
        "claims from this manifest. Use tools only to read file contents or understand",
        "implementation details.",
        "",
    ]

    lines.append("### Directories")
    for d in manifest.get("directories", []):
        lines.append(f"  {d}/")
    lines.append("")

    for category, files in sorted(manifest.get("files", {}).items()):
        if not files:
            continue
        truncated = manifest.get("truncated", {})
        if category in truncated:
            lines.append(f"### {category} (showing {len(files)} of {truncated[category]} files)")
        else:
            lines.append(f"### {category} ({len(files)} files)")
        for f in files:
            lines.append(f"  {f}")
        lines.append("")

    exports = manifest.get("exports", {})
    if exports:
        lines.append("### Exported functions/classes")
        for fpath, names in sorted(exports.items()):
            lines.append(f"  {fpath}: {', '.join(names)}")
        lines.append("")

    test_cov = manifest.get("test_coverage", {})
    if test_cov:
        lines.append("### Test coverage")
        for fpath, tests in sorted(test_cov.items()):
            lines.append(f"  {fpath} -> {', '.join(tests)}")
        lines.append("")

    return "\n".join(lines)


_TOOL_DISPATCH = {
    "get_job_schedule": _get_job_schedule,
    "check_code_presence": _check_code_presence,
    "read_config_value": _read_config_value,
    "check_test_coverage": _check_test_coverage,
    "get_recent_commits": _get_recent_commits,
    "check_function_exists": _check_function_exists,
    "read_file_snippet": _read_file_snippet,
}


# --- OpenAI function-calling format definitions ---

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_job_schedule",
            "description": "Look up the cron schedule for a named job.",
            "parameters": {
                "type": "object",
                "properties": {"job_name": {"type": "string"}},
                "required": ["job_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_code_presence",
            "description": (
                "Check if a literal substring exists in a file set. "
                "Matching is EXACT byte-for-byte substring, NOT regex, NOT word-boundary, NOT case-insensitive. "
                "Searching for 'foo' will match 'foo', '_foo', 'foobar', and 'find_foo_bar'. "
                "Searching for 'def foo' will NOT match 'def _foo' or 'def foo_bar'. "
                "If you want to know whether a name exists in any form (function, variable, dict key), "
                "search the bare name without prefix/suffix decorations and check the match_count. "
                "If a search returns exists=false, try variants (with leading underscore, with 'def ', as a string literal) "
                "before concluding the name is absent."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "substring": {
                        "type": "string",
                        "maxLength": MAX_SUBSTRING_LEN,
                        "description": "Literal substring to search for. Not a regex.",
                    },
                    "file_set": {
                        "type": "string",
                        "enum": list(ALLOWED_FILE_SETS),
                        "description": f"One of: {', '.join(repr(k) for k in sorted(ALLOWED_FILE_SETS))}. Non-recursive single-glob per directory.",
                    },
                },
                "required": ["substring", "file_set"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_config_value",
            "description": "Read a single key from debate-models.json.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "enum": list(ALLOWED_CONFIG_KEYS)},
                },
                "required": ["key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_test_coverage",
            "description": "Find test files for a given module path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "module_path": {"type": "string", "description": "Relative path to module (e.g., 'scripts/enrich_context.py')"}
                },
                "required": ["module_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_commits",
            "description": "Show recent commits affecting specific files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of relative file paths (max 5)"
                    },
                    "limit": {"type": "integer", "description": "Max commits to return (1-50, default 10)"}
                },
                "required": ["file_paths"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_function_exists",
            "description": "Check if a function or class definition exists in the codebase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "identifier": {"type": "string", "description": "Function or class name (e.g., 'enrich_context' or 'LLMError')"},
                    "file_set": {"type": "string", "enum": list(ALLOWED_FILE_SETS)}
                },
                "required": ["identifier", "file_set"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file_snippet",
            "description": "Read a snippet of source code from a file. Returns line-numbered content. Use this to inspect actual code, function implementations, config files, or test logic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": f"Relative path to file (e.g., 'scripts/debate.py', 'hooks/hook-context-inject.py'). Allowed directories: {', '.join(sorted(ALLOWED_SNIPPET_PATHS.keys()))}."
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Line number to start reading from (default: 1)",
                        "minimum": 1,
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximum lines to return (default: 50, max: 50)",
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["file_path"],
            },
        },
    },
]


def execute_tool(name, args):
    """Execute a verifier tool. Returns JSON string."""
    if name not in _TOOL_DISPATCH:
        return json.dumps({"error": f"unknown tool: {name}"})
    try:
        result = _TOOL_DISPATCH[name](args)
        if len(result) > MAX_RESULT_LEN:
            result = result[:MAX_RESULT_LEN] + '..."}'
        return result
    except Exception as e:
        return json.dumps({"error": str(e)})


