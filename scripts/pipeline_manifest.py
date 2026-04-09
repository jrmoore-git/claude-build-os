#!/opt/homebrew/bin/python3.11
"""Pipeline manifest utility — create, read, and validate stage manifests."""

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

TOPIC_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PACIFIC = ZoneInfo("America/Los_Angeles")


def project_root():
    """Detect project root via git or fallback to parent of scripts/."""
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    fallback = os.path.dirname(scripts_dir)
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, cwd=scripts_dir,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return fallback


def manifest_path(root, topic):
    return os.path.join(root, "tasks", f"{topic}-manifest.json")


def now_pacific_iso():
    return datetime.now(PACIFIC).isoformat()


def validate_topic(topic):
    if not TOPIC_RE.match(topic):
        print(f"Error: invalid topic '{topic}' — must match {TOPIC_RE.pattern}", file=sys.stderr)
        sys.exit(1)


def validate_artifact(artifact):
    if os.path.isabs(artifact):
        print(f"Error: artifact must be a relative path: {artifact}", file=sys.stderr)
        sys.exit(1)
    if ".." in artifact.split(os.sep):
        print(f"Error: artifact path must not contain '..': {artifact}", file=sys.stderr)
        sys.exit(1)
    if not artifact.startswith("tasks/"):
        print(f"Error: artifact must start with 'tasks/': {artifact}", file=sys.stderr)
        sys.exit(1)


def atomic_write(path, data):
    """Write JSON atomically via temp file + rename."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.rename(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def load_manifest(path):
    with open(path) as f:
        return json.load(f)


# --- subcommands ---

def cmd_add(args):
    root = project_root()
    validate_topic(args.topic)
    validate_artifact(args.artifact)

    extras = {}
    for item in (args.extra or []):
        if "=" not in item:
            print(f"Error: --extra must be key=value, got: {item}", file=sys.stderr)
            sys.exit(1)
        k, v = item.split("=", 1)
        extras[k] = v

    stage = {
        "skill": args.skill,
        "artifact": args.artifact,
        "status": args.status,
        "timestamp": now_pacific_iso(),
        "recommendation": args.recommendation,
    }
    if extras:
        stage["extra"] = extras

    path = manifest_path(root, args.topic)
    now = now_pacific_iso()

    if os.path.exists(path):
        manifest = load_manifest(path)
        manifest["updated"] = now
        manifest["stages"].append(stage)
    else:
        manifest = {
            "topic": args.topic,
            "created": now,
            "updated": now,
            "stages": [stage],
            "cost_summary": None,
        }

    atomic_write(path, manifest)
    print(f"Stage '{args.skill}' added to {path}")


def cmd_read(args):
    root = project_root()
    validate_topic(args.topic)
    path = manifest_path(root, args.topic)

    if not os.path.exists(path):
        print(f"Error: manifest not found: {path}", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest(path)
    json.dump(manifest, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_validate(args):
    root = project_root()
    validate_topic(args.topic)
    path = manifest_path(root, args.topic)

    if not os.path.exists(path):
        print(f"Error: manifest not found: {path}", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest(path)
    missing = []
    for stage in manifest.get("stages", []):
        artifact = stage.get("artifact", "")
        full = os.path.join(root, artifact)
        if not os.path.exists(full):
            missing.append(artifact)

    result = {"valid": len(missing) == 0, "missing": missing}
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    sys.exit(0 if result["valid"] else 1)


def main():
    parser = argparse.ArgumentParser(description="Pipeline manifest utility")
    subs = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = subs.add_parser("add", help="Add a stage to a manifest")
    p_add.add_argument("topic")
    p_add.add_argument("--skill", required=True)
    p_add.add_argument("--artifact", required=True)
    p_add.add_argument("--status", required=True)
    p_add.add_argument("--recommendation", default=None)
    p_add.add_argument("--extra", action="append", metavar="KEY=VALUE")

    # read
    p_read = subs.add_parser("read", help="Read a manifest")
    p_read.add_argument("topic")

    # validate
    p_val = subs.add_parser("validate", help="Validate artifact paths exist")
    p_val.add_argument("topic")

    args = parser.parse_args()
    {"add": cmd_add, "read": cmd_read, "validate": cmd_validate}[args.command](args)


if __name__ == "__main__":
    main()
