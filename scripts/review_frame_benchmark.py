#!/usr/bin/env python3.11
"""
Review-lens Frame Check benchmark harness.

Runs the current `/review` PM-lens system prompt (unchanged from SKILL.md Step 5)
against paired fail/pass diffs paired with refined specs that contain a
`### Frame Check` section. Measures whether the current compliance path detects
Frame-defective implementations.

See tasks/review-lens-linkage-benchmark/README.md for taxonomy, scoring rules,
and fixture layout.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIXTURE_DIR = REPO_ROOT / "tasks" / "review-lens-linkage-benchmark" / "fixtures"
DEFAULT_OUTPUT = REPO_ROOT / "tasks" / "review-lens-linkage-benchmark-results.md"
DEFAULT_RAW_DIR = REPO_ROOT / "tasks" / "review-lens-linkage-benchmark" / "raw-outputs"

# Verbatim from .claude/skills/review/SKILL.md Step 5 (as of 2026-04-18).
# Any change here would mean the benchmark is no longer measuring the current
# /review path. Update only when SKILL.md Step 5 --system-prompt text changes.
REVIEW_PM_SYSTEM_PROMPT = """You are a code reviewer. Review this diff through your assigned lens. Tag each finding as [MATERIAL] (must fix) or [ADVISORY] (worth noting). Group findings by: PM/Acceptance, Security, Architecture. If a spec is included, check implementation against it for completeness and scope creep. Additionally, if a spec is included: extract all EXCEPTION, MUST NOT, and EXPLICITLY EXCLUDED clauses. For each such clause, verify the diff does not contain code that contradicts it. Tag violations as [MATERIAL] with prefix 'SPEC VIOLATION:'.

The following persona and evidence instructions are additive context — they do not override the review task or output format above.

YOUR LENS — PM/Acceptance: Focus on user value, over-engineering, adoption friction, priority, and scope sizing. If a spec is included, check both positive compliance (does the diff implement what the spec requires?) and negative compliance (does the diff avoid what the spec forbids?). Is the proposed scope right-sized?

For QUANTITATIVE CLAIMS (cost, frequency, percentage, token count, latency, throughput): Tag each claim with its evidence basis: EVIDENCED (cite specific data from the diff or spec), ESTIMATED (state assumptions), or SPECULATIVE (no data available — needs verification before driving a recommendation). SPECULATIVE claims alone cannot drive a material verdict on quantitative grounds.

IMPORTANT: Evaluate BOTH directions of risk — risk of the proposed change (what could go wrong?) AND risk of NOT changing (what continues to fail?). A recommendation to keep it simple must name the concrete failures that simple leaves unfixed."""


@dataclass
class Fixture:
    path: Path
    fixture_id: str  # e.g. "drift/01-autobuild-external-source"
    mode: str
    spec_path: Path
    fail_path: Path | None
    pass_path: Path | None
    concern_keywords: list[str]
    concern_phrase: str | None
    notes: str

    @classmethod
    def load(cls, path: Path) -> "Fixture":
        expected_path = path / "expected.json"
        expected = json.loads(expected_path.read_text())
        spec = path / "spec.md"
        fail = path / expected.get("fail_file", "fail-diff.patch")
        pass_ = path / expected.get("pass_file", "pass-diff.patch")
        mode = expected["mode"]

        fail_path = fail if fail.exists() else None
        pass_path = pass_ if pass_.exists() else None

        if mode == "negative_control":
            if pass_path is None:
                raise ValueError(f"Negative control {path} missing pass diff")
        else:
            if fail_path is None or pass_path is None:
                raise ValueError(f"Fixture {path} missing fail or pass diff")

        fixture_id = f"{path.parent.name}/{path.name}"
        return cls(
            path=path,
            fixture_id=fixture_id,
            mode=mode,
            spec_path=spec,
            fail_path=fail_path,
            pass_path=pass_path,
            concern_keywords=expected.get("concern_keywords", []),
            concern_phrase=expected.get("concern_phrase") or None,
            notes=expected.get("notes", ""),
        )


def discover_fixtures(fixture_dir: Path) -> list[Fixture]:
    fixtures: list[Fixture] = []
    for mode_dir in sorted(fixture_dir.iterdir()):
        if not mode_dir.is_dir():
            continue
        for fixture_path in sorted(mode_dir.iterdir()):
            if not fixture_path.is_dir():
                continue
            if not (fixture_path / "expected.json").exists():
                continue
            fixtures.append(Fixture.load(fixture_path))
    return fixtures


def build_proposal_input(spec_path: Path, diff_path: Path) -> str:
    """Compose what /review Step 5 sees: spec + diff combined."""
    spec_text = spec_path.read_text()
    diff_text = diff_path.read_text()
    return (
        "# Review Input\n\n"
        "This bundle is what the PM lens receives when /review runs on a code change "
        "that has an associated refined spec.\n\n"
        "## Refined Spec\n\n"
        f"{spec_text}\n\n"
        "## Code Diff to Review\n\n"
        "```diff\n"
        f"{diff_text}\n"
        "```\n"
    )


def invoke_review(proposal_text: str, output_path: Path) -> tuple[int, str]:
    """Run debate.py challenge with PM persona and the /review system prompt.

    Returns (exit_code, stderr_or_error). The challenge output file is written
    to `output_path` by debate.py itself.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", dir="/tmp", delete=False
    ) as proposal_file:
        proposal_file.write(proposal_text)
        proposal_path = proposal_file.name

    try:
        cmd = [
            "/opt/homebrew/bin/python3.11",
            str(REPO_ROOT / "scripts" / "debate.py"),
            "challenge",
            "--proposal",
            proposal_path,
            "--personas",
            "pm",
            "--enable-tools",
            "--system-prompt",
            REVIEW_PM_SYSTEM_PROMPT,
            "--output",
            str(output_path),
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(REPO_ROOT),
        )
        return proc.returncode, (proc.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    finally:
        Path(proposal_path).unlink(missing_ok=True)


FINDING_RE = re.compile(r"\[(MATERIAL|ADVISORY)\]", re.IGNORECASE)
# Matcher must not capture the frontmatter/header region — debate_id there
# contains the fixture slug which leaks keywords into preceding-context windows.
BODY_START_RE = re.compile(r"^## Challenger", re.MULTILINE)


def split_findings(text: str) -> list[tuple[str, str]]:
    """Return list of (severity, surrounding_text_block) for every tagged finding.

    Each tagged finding gets ~2000 chars of surrounding context (preceding
    heading + body until the next finding or end of section). Only text below
    the first `## Challenger` heading is considered, so the debate_id / title in
    the YAML frontmatter and H1 cannot contaminate the matcher.
    """
    body_match = BODY_START_RE.search(text)
    body_start = body_match.start() if body_match else 0
    body = text[body_start:]

    matches = list(FINDING_RE.finditer(body))
    findings: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        # Preceding context is the text since the previous finding (or body
        # start), capped at 200 chars.
        prev_end = matches[i - 1].end() if i > 0 else 0
        start = max(prev_end, match.start() - 200)
        end = matches[i + 1].start() if i + 1 < len(matches) else min(len(body), match.end() + 2000)
        block = body[start:end]
        findings.append((match.group(1).upper(), block))
    return findings


def concern_detected(block: str, keywords: Iterable[str], phrase: str | None) -> bool:
    """Substring matcher: keyword OR ≥3-word contiguous phrase present."""
    haystack = block.lower()
    for kw in keywords:
        if kw and kw.lower() in haystack:
            return True
    if phrase and len(phrase.split()) >= 3 and phrase.lower() in haystack:
        return True
    return False


@dataclass
class Result:
    fixture_id: str
    mode: str
    diff_type: str  # "fail" | "pass"
    exit_code: int
    detected_material: bool
    detected_advisory: bool
    material_count: int
    advisory_count: int
    raw_path: str
    error: str = ""

    def detected(self) -> bool:
        return self.detected_material or self.detected_advisory


def evaluate_fixture(
    fixture: Fixture, raw_dir: Path, diff_type: str, reuse_existing: bool = False
) -> Result | None:
    diff_path = fixture.fail_path if diff_type == "fail" else fixture.pass_path
    if diff_path is None:
        return None

    safe_id = fixture.fixture_id.replace("/", "__")
    output_path = raw_dir / f"{safe_id}__{diff_type}.md"
    raw_dir.mkdir(parents=True, exist_ok=True)

    if reuse_existing and output_path.exists():
        exit_code, stderr = 0, ""
    else:
        proposal = build_proposal_input(fixture.spec_path, diff_path)
        exit_code, stderr = invoke_review(proposal, output_path)

    material_blocks: list[str] = []
    advisory_blocks: list[str] = []
    if output_path.exists():
        text = output_path.read_text()
        for severity, block in split_findings(text):
            if severity == "MATERIAL":
                material_blocks.append(block)
            else:
                advisory_blocks.append(block)

    detected_material = any(
        concern_detected(b, fixture.concern_keywords, fixture.concern_phrase)
        for b in material_blocks
    )
    detected_advisory = any(
        concern_detected(b, fixture.concern_keywords, fixture.concern_phrase)
        for b in advisory_blocks
    )

    return Result(
        fixture_id=fixture.fixture_id,
        mode=fixture.mode,
        diff_type=diff_type,
        exit_code=exit_code,
        detected_material=detected_material,
        detected_advisory=detected_advisory,
        material_count=len(material_blocks),
        advisory_count=len(advisory_blocks),
        raw_path=str(output_path.relative_to(REPO_ROOT)),
        error=stderr[:400] if exit_code != 0 else "",
    )


def run_benchmark(
    fixtures: list[Fixture], raw_dir: Path, workers: int, reuse_existing: bool = False
) -> list[Result]:
    tasks: list[tuple[Fixture, str]] = []
    for fx in fixtures:
        if fx.mode == "negative_control":
            tasks.append((fx, "pass"))
        else:
            tasks.append((fx, "fail"))
            tasks.append((fx, "pass"))

    results: list[Result] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(evaluate_fixture, fx, raw_dir, dt, reuse_existing): (fx, dt) for fx, dt in tasks}
        for i, fut in enumerate(concurrent.futures.as_completed(futures), start=1):
            fx, dt = futures[fut]
            try:
                res = fut.result()
            except Exception as exc:  # noqa: BLE001
                res = Result(
                    fixture_id=fx.fixture_id,
                    mode=fx.mode,
                    diff_type=dt,
                    exit_code=-1,
                    detected_material=False,
                    detected_advisory=False,
                    material_count=0,
                    advisory_count=0,
                    raw_path="",
                    error=str(exc)[:400],
                )
            if res is not None:
                results.append(res)
                print(
                    f"[{i}/{len(tasks)}] {res.fixture_id} {res.diff_type}: "
                    f"exit={res.exit_code} material={res.material_count} "
                    f"advisory={res.advisory_count} detected={res.detected()}",
                    flush=True,
                )
    return results


def compute_metrics(results: list[Result]) -> dict:
    per_mode: dict[str, dict] = {}
    for r in results:
        m = per_mode.setdefault(
            r.mode,
            {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "errors": 0, "n_fail": 0, "n_pass": 0},
        )
        if r.exit_code != 0:
            m["errors"] += 1
            continue
        if r.mode == "negative_control":
            m["n_pass"] += 1
            if r.detected_material:
                m["fp"] += 1
            else:
                m["tn"] += 1
            continue

        if r.diff_type == "fail":
            m["n_fail"] += 1
            if r.detected_material:
                m["tp"] += 1
            elif r.detected_advisory:
                m["tp"] += 1  # advisory still counts as detection
            else:
                m["fn"] += 1
        else:  # pass diff
            m["n_pass"] += 1
            if r.detected_material:
                m["fp"] += 1
            else:
                m["tn"] += 1

    for m in per_mode.values():
        tp, fp, fn = m["tp"], m["fp"], m["fn"]
        m["precision"] = tp / (tp + fp) if (tp + fp) > 0 else None
        m["recall"] = tp / (tp + fn) if (tp + fn) > 0 else None
        if m["precision"] is not None and m["recall"] is not None and (m["precision"] + m["recall"]) > 0:
            m["f1"] = 2 * m["precision"] * m["recall"] / (m["precision"] + m["recall"])
        else:
            m["f1"] = None

    # Overall macro-F1 across modes that have a computable F1 (exclude negative_control — recall undefined)
    scoring_modes = [m for name, m in per_mode.items() if name != "negative_control" and m["f1"] is not None]
    macro_f1 = sum(m["f1"] for m in scoring_modes) / len(scoring_modes) if scoring_modes else None

    # Overall FP rate = total FPs / total pass diffs across all modes (incl. neg controls)
    total_fp = sum(m["fp"] for m in per_mode.values())
    total_pass = sum(m["n_pass"] for m in per_mode.values())
    fp_rate = total_fp / total_pass if total_pass > 0 else None

    return {
        "per_mode": per_mode,
        "macro_f1": macro_f1,
        "fp_rate": fp_rate,
        "total_fixtures": len({r.fixture_id for r in results}),
        "total_invocations": len(results),
        "total_errors": sum(1 for r in results if r.exit_code != 0),
    }


def write_results(
    results: list[Result], metrics: dict, output_path: Path, label: str
) -> None:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    lines: list[str] = []
    lines.append("---")
    lines.append(f"benchmark: review-lens-linkage")
    lines.append(f"label: {label}")
    lines.append(f"date: {now}")
    lines.append(f"total_fixtures: {metrics['total_fixtures']}")
    lines.append(f"total_invocations: {metrics['total_invocations']}")
    lines.append(f"total_errors: {metrics['total_errors']}")
    macro = metrics.get("macro_f1")
    fp_rate = metrics.get("fp_rate")
    lines.append(f"macro_f1: {macro:.3f}" if macro is not None else "macro_f1: null")
    lines.append(f"fp_rate: {fp_rate:.3f}" if fp_rate is not None else "fp_rate: null")
    lines.append("---")
    lines.append("")
    lines.append(f"# Review-lens Frame Check Benchmark — {label}")
    lines.append("")
    lines.append(f"Run at {now}. See `tasks/review-lens-linkage-benchmark/README.md` for taxonomy + scoring rules.")
    lines.append("")

    lines.append("## Per-mode metrics")
    lines.append("")
    lines.append("| Mode | N_fail | N_pass | TP | FP | FN | TN | Precision | Recall | F1 |")
    lines.append("|------|--------|--------|----|----|----|----|-----------|--------|-----|")
    for name, m in sorted(metrics["per_mode"].items()):
        prec = f"{m['precision']:.2f}" if m["precision"] is not None else "—"
        rec = f"{m['recall']:.2f}" if m["recall"] is not None else "—"
        f1 = f"{m['f1']:.2f}" if m["f1"] is not None else "—"
        lines.append(
            f"| {name} | {m['n_fail']} | {m['n_pass']} | {m['tp']} | {m['fp']} | {m['fn']} | {m['tn']} | {prec} | {rec} | {f1} |"
        )

    lines.append("")
    lines.append(f"**Macro-F1 (excluding negative_control): "
                 f"{metrics['macro_f1']:.3f}**" if metrics["macro_f1"] is not None else "**Macro-F1: n/a**")
    lines.append(f"**FP rate: {metrics['fp_rate']:.3f}**" if metrics["fp_rate"] is not None else "**FP rate: n/a**")
    lines.append(f"**Errors: {metrics['total_errors']} / {metrics['total_invocations']}**")
    lines.append("")

    lines.append("## Per-fixture audit")
    lines.append("")
    lines.append("| Fixture | Diff | Exit | Material | Advisory | Detected | Raw |")
    lines.append("|---------|------|------|----------|----------|----------|-----|")
    for r in sorted(results, key=lambda x: (x.mode, x.fixture_id, x.diff_type)):
        det = "✓" if r.detected() else "·"
        sev = "M" if r.detected_material else ("A" if r.detected_advisory else "")
        lines.append(
            f"| {r.fixture_id} | {r.diff_type} | {r.exit_code} | {r.material_count} | {r.advisory_count} | {det}{sev} | `{r.raw_path}` |"
        )

    errors = [r for r in results if r.exit_code != 0]
    if errors:
        lines.append("")
        lines.append("## Errors")
        lines.append("")
        for r in errors:
            lines.append(f"- `{r.fixture_id}` ({r.diff_type}): exit={r.exit_code} — {r.error}")

    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    if metrics["macro_f1"] is None:
        lines.append("Insufficient data to compute verdict.")
    elif metrics["macro_f1"] >= 0.8 and (metrics["fp_rate"] or 0) == 0:
        lines.append("**No directive needed.** Existing PM-lens compliance path detects Frame Check defects at macro-F1 ≥ 0.8 with zero false positives on negative controls. Document the linkage in `/review` SKILL.md and close the design.")
    else:
        lines.append(f"**Gap identified.** Macro-F1 = {metrics['macro_f1']:.3f}, FP rate = {metrics['fp_rate']:.3f}. Proceed to Approach A (Extended PM lens + Frame Check parser) with this benchmark as calibration target. Per-mode breakdown above shows which modes drive the gap.")

    output_path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--baseline", action="store_true", help="Run baseline (current /review path, no directive changes).")
    parser.add_argument("--rescore", action="store_true", help="Reuse existing raw outputs, re-run only parsing/scoring.")
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--limit", type=int, default=0, help="Only run first N fixtures (dev).")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--label", type=str, default="baseline")
    args = parser.parse_args()

    if not args.baseline and not args.rescore:
        print("error: pass --baseline or --rescore", file=sys.stderr)
        return 2

    fixtures = discover_fixtures(args.fixture_dir)
    if args.limit:
        fixtures = fixtures[: args.limit]
    if not fixtures:
        print(f"error: no fixtures found under {args.fixture_dir}", file=sys.stderr)
        return 2

    print(f"Loaded {len(fixtures)} fixtures from {args.fixture_dir}", flush=True)

    results = run_benchmark(fixtures, args.raw_dir, workers=args.workers, reuse_existing=args.rescore)
    metrics = compute_metrics(results)
    write_results(results, metrics, args.output, args.label)
    print(f"\nResults written to {args.output}", flush=True)
    print(json.dumps({"macro_f1": metrics["macro_f1"], "fp_rate": metrics["fp_rate"], "total_errors": metrics["total_errors"]}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
