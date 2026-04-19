#!/usr/bin/env python3.11
"""arm_study_orchestrator.py — Track F of the arm-comparison study.

Runs a 2-arm comparison for a single proposal as two separate subprocesses
(process-level session isolation) and writes outputs to disk with obfuscated
labels so the downstream scorer cannot tell which arm is which until after
scoring completes.

Arms:
  arm_a  — Claude-only debate  (--config config/study/arm-claude-only.json)
  arm_b  — production multi-model debate  (no --config; uses config/debate-models.json)

Obfuscated labels on disk: arm-x / arm-y. Mapping stored in
stores/arm-study/<run_id>/labels.json, read by the scorer ONLY after scoring
completes.

Usage:
    python3.11 scripts/arm_study_orchestrator.py --proposal <path> [--run-id <id>] [--dry-run]
"""

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import random
import re
import subprocess
import sys
import time


# All paths are relative to the repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STUDY_ROOT_REL = pathlib.Path("stores/arm-study")
CLAUDE_ONLY_CONFIG_REL = pathlib.Path("config/study/arm-claude-only.json")
DEBATE_SCRIPT_REL = pathlib.Path("scripts/debate.py")
AUDIT_LOG_REL = STUDY_ROOT_REL / "orchestrator-log.jsonl"

# Personas passed to debate.py challenge. Matches the production persona set so
# Arm A (Claude-only config) and Arm B (production config) invoke the same set
# of roles — only the model mapping differs.
DEFAULT_PERSONAS = "architect,security,pm,frame"

# Obfuscated labels used on disk.
OBFUSCATED_LABELS = ["arm-x", "arm-y"]

# Strings that leak arm identity in captured logs/files. Scrubbed post-hoc.
LEAK_TOKENS = [
    "arm-claude-only.json",
    "arm_a",
    "arm_b",
    "arm-a",
    "arm-b",
    "Claude-only",
    "claude-only",
]


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def _iso_z(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_run_id():
    return _now_utc().strftime("run-%Y%m%d-%H%M%S")


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _assign_labels():
    """Randomly map arm_a / arm_b to arm-x / arm-y. Uses SystemRandom.
    Returns (arm_a_label, arm_b_label) — the obfuscated label each arm gets.
    The persisted labels.json is written separately as {neutral: semantic}
    so the scorer's `unblind()` can consume it directly."""
    labels = list(OBFUSCATED_LABELS)
    random.SystemRandom().shuffle(labels)
    return labels[0], labels[1]


def _strip_leaks(text):
    """Remove arm-identifying substrings from captured text."""
    if not text:
        return text
    out = text
    for token in LEAK_TOKENS:
        out = out.replace(token, "[REDACTED]")
    # Also strip any config=<path>arm-claude-only style mentions that survive token replacement
    out = re.sub(r"--config\s+\S+", "--config [REDACTED]", out)
    return out


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _build_command(proposal_rel, output_rel, config_rel=None):
    """Build the debate.py challenge command with relative paths."""
    cmd = [
        sys.executable,
        str(DEBATE_SCRIPT_REL),
        "challenge",
        "--proposal", str(proposal_rel),
        "--personas", DEFAULT_PERSONAS,
        "--output", str(output_rel),
    ]
    if config_rel is not None:
        cmd.extend(["--config", str(config_rel)])
    return cmd


def _run_arm(arm_name, cmd, output_dir_abs, output_rel, dry_run):
    """Run a single arm as a subprocess. Returns a result dict.

    Each call is a separate subprocess.run() — no Python object is reused
    between arms. That is the session-isolation mechanism.
    """
    output_dir_abs.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    if dry_run:
        # Echo the command; create placeholder files instead of invoking.
        # Intentionally do NOT label the line with arm_a/arm_b — that would
        # print the obfuscated mapping to stdout.
        print(f"[DRY-RUN] {' '.join(cmd)}")
        placeholder = output_dir_abs / output_rel.name
        _write_text(
            placeholder,
            "[DRY-RUN FIXTURE]\n"
            f"# Placeholder challenge output for {output_rel.name}\n",
        )
        wall = time.time() - t0
        return {
            "exit_code": 0,
            "stdout_bytes": 0,
            "stderr_bytes": 0,
            "files_generated_count": 1,
            "wall_time_sec": round(wall, 3),
            "command": cmd,
        }

    # Real invocation. cwd=REPO_ROOT so relative paths resolve.
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        exit_code = completed.returncode
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
    except FileNotFoundError as e:
        # python3.11 or debate.py missing on PATH — record failure, keep going.
        exit_code = 127
        stdout = ""
        stderr = f"subprocess launch failed: {e}\n"

    wall = time.time() - t0

    # Scrub leaks from captured streams before persisting.
    stdout_clean = _strip_leaks(stdout)
    stderr_clean = _strip_leaks(stderr)

    _write_text(output_dir_abs / "stdout.log", stdout_clean)
    _write_text(output_dir_abs / "stderr.log", stderr_clean)

    # Scrub leaks from the primary output file (if debate.py wrote it).
    primary = output_dir_abs / output_rel.name
    if primary.exists():
        original = primary.read_text()
        scrubbed = _strip_leaks(original)
        if scrubbed != original:
            primary.write_text(scrubbed)

    files_generated_count = sum(1 for _ in output_dir_abs.iterdir())

    return {
        "exit_code": exit_code,
        "stdout_bytes": len(stdout_clean.encode("utf-8")),
        "stderr_bytes": len(stderr_clean.encode("utf-8")),
        "files_generated_count": files_generated_count,
        "wall_time_sec": round(wall, 3),
        "command": cmd,
    }


def _list_files(directory):
    if not directory.exists():
        return []
    # Walk recursively — output is now nested under <proposal_stem>/ per the
    # plan's per-proposal directory layout. Emit paths relative to `directory`.
    return sorted(
        str(p.relative_to(directory))
        for p in directory.rglob("*")
        if p.is_file()
    )


def _append_audit(entry):
    audit_path = REPO_ROOT / AUDIT_LOG_REL
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--proposal", required=True,
        help="Path to proposal markdown file (relative to repo root)",
    )
    parser.add_argument(
        "--run-id", default=None,
        help="Run identifier (default: timestamp-based run-YYYYMMDD-HHMMSS)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=False,
        help="Do not invoke real subprocesses; create fixture outputs",
    )
    args = parser.parse_args()

    run_id = args.run_id or _default_run_id()
    proposal_rel = pathlib.Path(args.proposal)
    proposal_abs = REPO_ROOT / proposal_rel

    # Validate proposal exists for real runs (dry-run tolerates missing file).
    proposal_sha256 = None
    if args.dry_run:
        if proposal_abs.exists():
            proposal_sha256 = _sha256_file(proposal_abs)
        else:
            proposal_sha256 = "DRY_RUN_NO_FILE"
    else:
        if not proposal_abs.exists():
            raise FileNotFoundError(
                f"proposal not found: {proposal_rel} "
                f"(resolved to {proposal_abs})"
            )
        proposal_sha256 = _sha256_file(proposal_abs)

    # Validate Claude-only config exists for real runs.
    config_abs = REPO_ROOT / CLAUDE_ONLY_CONFIG_REL
    if not args.dry_run and not config_abs.exists():
        raise FileNotFoundError(
            f"Arm A config not found: {CLAUDE_ONLY_CONFIG_REL}. "
            f"Track A ships this file; it must exist before a non-dry-run "
            f"orchestrator invocation."
        )

    # Set up run directory.
    run_dir_rel = STUDY_ROOT_REL / run_id
    run_dir_abs = REPO_ROOT / run_dir_rel
    run_dir_abs.mkdir(parents=True, exist_ok=True)

    # Obfuscated label assignment. labels.json maps neutral -> semantic
    # (arm-x -> arm-a, arm-y -> arm-b) — the shape scorer.unblind() expects.
    arm_a_label, arm_b_label = _assign_labels()
    labels_map = {arm_a_label: "arm-a", arm_b_label: "arm-b"}
    (run_dir_abs / "labels.json").write_text(
        json.dumps(labels_map, indent=2, sort_keys=True) + "\n"
    )

    # Per-proposal subdir keeps the run dir extensible to multi-proposal runs
    # and matches the plan's `stores/arm-study/<run_id>/arm-x/<proposal>/` layout.
    proposal_stem = proposal_rel.stem
    arm_a_dir_abs = run_dir_abs / arm_a_label / proposal_stem
    arm_b_dir_abs = run_dir_abs / arm_b_label / proposal_stem
    arm_a_dir_abs.mkdir(parents=True, exist_ok=True)
    arm_b_dir_abs.mkdir(parents=True, exist_ok=True)

    # Both arms write their challenge markdown to a neutral filename.
    challenge_filename = "challenge.md"
    arm_a_output_rel = run_dir_rel / arm_a_label / proposal_stem / challenge_filename
    arm_b_output_rel = run_dir_rel / arm_b_label / proposal_stem / challenge_filename

    started_at = _now_utc()
    total_t0 = time.time()

    # Arm A: Claude-only config.
    cmd_a = _build_command(
        proposal_rel, arm_a_output_rel, config_rel=CLAUDE_ONLY_CONFIG_REL
    )
    result_a = _run_arm("arm_a", cmd_a, arm_a_dir_abs, arm_a_output_rel, args.dry_run)

    # Arm B: production config (no --config flag).
    cmd_b = _build_command(proposal_rel, arm_b_output_rel, config_rel=None)
    result_b = _run_arm("arm_b", cmd_b, arm_b_dir_abs, arm_b_output_rel, args.dry_run)

    completed_at = _now_utc()
    total_wall_sec = round(time.time() - total_t0, 3)

    # Obfuscate manifest: route results by label, not by arm_a/arm_b identity.
    per_label = {
        arm_a_label: {
            "exit_code": result_a["exit_code"],
            "stdout_bytes": result_a["stdout_bytes"],
            "stderr_bytes": result_a["stderr_bytes"],
            "files_generated_count": result_a["files_generated_count"],
            "wall_time_sec": result_a["wall_time_sec"],
        },
        arm_b_label: {
            "exit_code": result_b["exit_code"],
            "stdout_bytes": result_b["stdout_bytes"],
            "stderr_bytes": result_b["stderr_bytes"],
            "files_generated_count": result_b["files_generated_count"],
            "wall_time_sec": result_b["wall_time_sec"],
        },
    }

    files_per_label = {
        label: _list_files(run_dir_abs / label)
        for label in OBFUSCATED_LABELS
    }

    manifest = {
        "run_id": run_id,
        "proposal_path": str(proposal_rel),
        "proposal_sha256": proposal_sha256,
        "started_at": _iso_z(started_at),
        "completed_at": _iso_z(completed_at),
        "total_wall_time_sec": total_wall_sec,
        "obfuscated_labels": list(OBFUSCATED_LABELS),
        "per_label": per_label,
        "files_per_label": files_per_label,
        "dry_run": bool(args.dry_run),
    }
    (run_dir_abs / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )

    # Determine overall status.
    any_failure = result_a["exit_code"] != 0 or result_b["exit_code"] != 0
    status = "failure" if any_failure else "success"

    _append_audit({
        "timestamp": _iso_z(completed_at),
        "run_id": run_id,
        "proposal": str(proposal_rel),
        "status": status,
        "total_wall_time_sec": total_wall_sec,
        "dry_run": bool(args.dry_run),
    })

    # Emit the run directory path so callers can pipe to scorer.
    print(f"run_dir: {run_dir_rel}")
    print(f"status: {status}")

    return 1 if any_failure else 0


if __name__ == "__main__":
    sys.exit(main())
