#!/usr/bin/env python3.11
"""
INV-1 calibration for REDESIGN A — second-pass FALSIFIED-mechanism classifier.

Per tasks/arm-study-redesigns-judgment.md Challenge 7 (BLOCKING): A3 ships
only if the LLM classifier beats the regex against hand-labeled ground
truth on existing n=3 data, AND the combined AMBIGUOUS+CHALLENGER_FABRICATION
rate stays ≤ 60% (no safe-label collapse).

Subcommands:
  --collect-only  walk stores/arm-study/run-* scored.json, extract every
                  FALSIFIED claim block to a JSONL.
  --sample        if collected population ≤ 50, emit all; else stratified
                  sample of 30 across (arm × Source pattern).
  --label         interactive stdin loop for human labeling. Resumable.
  --compare       run regex + LLM classifiers against ground-truth labels;
                  compute Cohen's kappa + accuracy + safe-label rate;
                  emit PASS/FAIL verdict to stdout + markdown report.

See tasks/arm-study-redesign-a-falsified-classifier-plan.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Late imports keep --help fast and let tests stub these.
import arm_study_scorer as scorer  # noqa: E402

DEFAULT_STORE = REPO_ROOT / "stores" / "arm-study"
CLAIMS_PATH = DEFAULT_STORE / "a3-calibration-claims.jsonl"
SAMPLE_PATH = DEFAULT_STORE / "a3-calibration-sample.jsonl"
LABELS_PATH = DEFAULT_STORE / "a3-calibration-labels.jsonl"
REPORT_PATH = DEFAULT_STORE / "a3-calibration-report.md"

LABEL_BY_KEY = {
    "1": "PROPOSAL_ERROR_CAUGHT",
    "2": "CHALLENGER_FABRICATION",
    "3": "AMBIGUOUS",
    "4": "INFERENCE_NOT_GROUNDED",
}

SAMPLE_THRESHOLD = 50  # ≤ this → label entire population; > this → stratified
STRATIFIED_SAMPLE_SIZE = 30
SAFE_LABEL_CAP = 0.60  # combined AMBIGUOUS + CHALLENGER_FABRICATION rate cap


# ── Subcommand: collect ────────────────────────────────────────────────────


def _classify_source_pattern(source_field: str) -> str:
    """Categorize source attribution into one of {challenger, proposal,
    mixed, other}. Used as a stratification axis."""
    s = (source_field or "").lower()
    has_chal = "challenger" in s
    has_prop = "proposal" in s
    if has_chal and has_prop:
        return "mixed"
    if has_chal:
        return "challenger"
    if has_prop:
        return "proposal"
    return "other"


def collect_falsified_claims(
    store_root: Path = DEFAULT_STORE,
) -> list[dict[str, Any]]:
    """Walk run-* directories, extract every FALSIFIED claim from each
    arm's scored.json."""
    out: list[dict[str, Any]] = []
    for run_dir in sorted(store_root.glob("run-*")):
        scored_path = run_dir / "scored.json"
        if not scored_path.is_file():
            continue
        try:
            scored = json.loads(scored_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        run_id = run_dir.name
        for arm_label, arm_data in (scored.get("arms") or {}).items():
            for dim in ("catch_rate", "miss_rate"):
                vc = (arm_data.get(dim) or {}).get("verify_claims") or {}
                vt = vc.get("verification_text")
                if not vt:
                    continue
                for idx, (claim_text, source, evidence) in enumerate(
                    scorer.iter_falsified_blocks(vt)
                ):
                    out.append({
                        "claim_id": f"{run_id}::{arm_label}::{dim}::{idx}",
                        "run_id": run_id,
                        "arm": arm_label,
                        "dim": dim,
                        "claim_idx": idx,
                        "claim_text": claim_text,
                        "source_field": source,
                        "source_pattern": _classify_source_pattern(source),
                        "verifier_evidence": evidence,
                    })
    return out


def cmd_collect(store_root: Path, output_path: Path) -> int:
    claims = collect_falsified_claims(store_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        for c in claims:
            f.write(json.dumps(c, sort_keys=True) + "\n")
    print(f"Collected {len(claims)} FALSIFIED claims → {output_path}")
    by_pattern = Counter(c["source_pattern"] for c in claims)
    by_arm = Counter(c["arm"] for c in claims)
    print(f"  by arm: {dict(by_arm)}")
    print(f"  by source pattern: {dict(by_pattern)}")
    return 0


# ── Subcommand: sample ─────────────────────────────────────────────────────


def stratified_sample(
    claims: list[dict[str, Any]],
    sample_size: int = STRATIFIED_SAMPLE_SIZE,
    seed: int = 20260419,
) -> list[dict[str, Any]]:
    """Stratified sample across (arm × source_pattern). Deterministic via
    fixed seed. Allocates proportional-to-population per stratum, with at
    least 1 per non-empty stratum if sample_size allows."""
    import random
    rng = random.Random(seed)
    strata: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for c in claims:
        strata[(c["arm"], c["source_pattern"])].append(c)

    total = len(claims)
    if total == 0:
        return []
    if sample_size >= total:
        return list(claims)

    # Floor allocation per stratum (proportional), then distribute remainder.
    allocations: dict[tuple[str, str], int] = {}
    raw_alloc: dict[tuple[str, str], float] = {}
    for key, items in strata.items():
        raw_alloc[key] = sample_size * (len(items) / total)
        allocations[key] = max(1, int(raw_alloc[key])) if items else 0

    over = sum(allocations.values()) - sample_size
    if over > 0:
        # Trim from strata with the smallest fractional remainder.
        order = sorted(allocations.keys(),
                       key=lambda k: raw_alloc[k] - int(raw_alloc[k]))
        for key in order:
            if over <= 0:
                break
            if allocations[key] > 1:
                allocations[key] -= 1
                over -= 1
    elif over < 0:
        # Add to strata with the largest fractional remainder.
        order = sorted(allocations.keys(),
                       key=lambda k: -(raw_alloc[k] - int(raw_alloc[k])))
        for key in order:
            if over >= 0:
                break
            if allocations[key] < len(strata[key]):
                allocations[key] += 1
                over += 1

    sampled: list[dict[str, Any]] = []
    for key, n in allocations.items():
        items = strata[key]
        if n >= len(items):
            sampled.extend(items)
        else:
            sampled.extend(rng.sample(items, n))
    return sampled


def cmd_sample(input_path: Path, output_path: Path) -> int:
    claims = [json.loads(line) for line in input_path.read_text().splitlines()
              if line.strip()]
    if len(claims) <= SAMPLE_THRESHOLD:
        sample = list(claims)
        print(f"Population {len(claims)} ≤ {SAMPLE_THRESHOLD} — labeling all")
    else:
        sample = stratified_sample(claims, STRATIFIED_SAMPLE_SIZE)
        print(
            f"Population {len(claims)} > {SAMPLE_THRESHOLD} — "
            f"stratified sample of {len(sample)}"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        for c in sample:
            f.write(json.dumps(c, sort_keys=True) + "\n")
    by_pattern = Counter(c["source_pattern"] for c in sample)
    by_arm = Counter(c["arm"] for c in sample)
    print(f"  by arm: {dict(by_arm)}")
    print(f"  by source pattern: {dict(by_pattern)}")
    return 0


# ── Subcommand: label ──────────────────────────────────────────────────────


def _load_existing_labels(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("claim_id"):
            out[entry["claim_id"]] = entry
    return out


def _label_prompt(claim: dict[str, Any]) -> str:
    return (
        f"\n{'─' * 70}\n"
        f"claim_id: {claim['claim_id']}\n"
        f"arm: {claim['arm']}  dim: {claim['dim']}  "
        f"source_pattern: {claim['source_pattern']}\n\n"
        f"CLAIM:\n{claim['claim_text']}\n\n"
        f"SOURCE FIELD: {claim['source_field']}\n\n"
        f"VERIFIER EVIDENCE:\n{claim['verifier_evidence']}\n"
        f"{'─' * 70}\n"
        f"  1 = PROPOSAL_ERROR_CAUGHT\n"
        f"  2 = CHALLENGER_FABRICATION\n"
        f"  3 = AMBIGUOUS\n"
        f"  4 = INFERENCE_NOT_GROUNDED\n"
        f"  s = skip   q = quit and save\n"
        f"label: "
    )


def cmd_label(sample_path: Path, labels_path: Path) -> int:
    sample = [json.loads(line) for line in sample_path.read_text().splitlines()
              if line.strip()]
    existing = _load_existing_labels(labels_path)
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    pending = [c for c in sample if c["claim_id"] not in existing]
    if not pending:
        print("All sample claims already labeled.")
        return 0
    print(
        f"{len(existing)} already labeled; {len(pending)} pending. "
        f"q to quit and save."
    )
    with labels_path.open("a") as f:
        for claim in pending:
            sys.stdout.write(_label_prompt(claim))
            sys.stdout.flush()
            try:
                resp = input().strip().lower()
            except EOFError:
                print("\nEOF — saving and exiting.")
                break
            if resp == "q":
                print("Saved progress.")
                break
            if resp == "s":
                continue
            if resp not in LABEL_BY_KEY:
                print(f"  invalid: {resp!r}; skipping (use --label again to retry)")
                continue
            entry = {
                "claim_id": claim["claim_id"],
                "ground_truth": LABEL_BY_KEY[resp],
                "claim_text": claim["claim_text"][:200],
                "arm": claim["arm"],
                "source_pattern": claim["source_pattern"],
            }
            f.write(json.dumps(entry, sort_keys=True) + "\n")
            f.flush()
    return 0


# ── Subcommand: compare ────────────────────────────────────────────────────


def _regex_label_for_claim(source_field: str) -> str:
    """Map regex output to one of A3_MECHANISM_LABELS for like-for-like
    comparison. The regex collapses 4 mechanisms to 3 buckets so this is
    intentionally lossy — that's the bias the LLM is meant to fix."""
    s = (source_field or "").lower()
    has_chal = "challenger" in s
    has_prop = "proposal" in s
    if has_chal and not has_prop:
        return "CHALLENGER_FABRICATION"
    if has_prop:
        return "PROPOSAL_ERROR_CAUGHT"
    return "AMBIGUOUS"


def cohens_kappa(
    pred: list[str], true: list[str], categories: tuple[str, ...],
) -> float | None:
    """Cohen's kappa for two raters over a discrete category set. Returns
    None if there's no variance to measure."""
    if len(pred) != len(true) or not pred:
        return None
    n = len(pred)
    obs_agreement = sum(1 for p, t in zip(pred, true) if p == t) / n
    pred_dist = {c: pred.count(c) / n for c in categories}
    true_dist = {c: true.count(c) / n for c in categories}
    expected_agreement = sum(pred_dist[c] * true_dist[c] for c in categories)
    if expected_agreement >= 1.0:
        return 1.0 if obs_agreement == 1.0 else 0.0
    return (obs_agreement - expected_agreement) / (1.0 - expected_agreement)


def cmd_compare(
    claims_path: Path,
    labels_path: Path,
    report_path: Path,
    classifier_model: str = scorer.A3_DEFAULT_MODEL,
    _llm_call_json=None,
) -> int:
    if not labels_path.is_file():
        print(f"ERROR: labels not found at {labels_path}", file=sys.stderr)
        return 2
    claims_by_id = {
        json.loads(line)["claim_id"]: json.loads(line)
        for line in claims_path.read_text().splitlines() if line.strip()
    }
    labels = _load_existing_labels(labels_path)
    if not labels:
        print("ERROR: no labeled claims", file=sys.stderr)
        return 2

    # Resolve cache/log paths at runtime so monkeypatched test-time module
    # constants are honored (function-default args bind at module load time
    # and would otherwise point at the production paths).
    cache_path = scorer.A3_MECHANISM_CACHE_PATH
    log_path = scorer.A3_ADJUDICATION_LOG_PATH
    cache = scorer._load_mechanism_cache(cache_path=cache_path)
    pred_regex: list[str] = []
    pred_llm: list[str] = []
    truth: list[str] = []
    per_claim: list[dict[str, Any]] = []
    for cid, label_entry in labels.items():
        claim = claims_by_id.get(cid)
        if not claim:
            continue
        gt = label_entry["ground_truth"]
        regex_label = _regex_label_for_claim(claim["source_field"])
        # Run LLM classifier (uses cache if available).
        llm_result = scorer.classify_mechanism_for_claim(
            claim_text=claim["claim_text"],
            source_field=claim["source_field"],
            verifier_evidence=claim["verifier_evidence"],
            proposal_text="",  # calibration sample loses proposal context
            challenger_text="",
            model=classifier_model, cache=cache,
            run_id="calibration",
            cache_path=cache_path, log_path=log_path,
            _llm_call_json=_llm_call_json,
        )
        truth.append(gt)
        pred_regex.append(regex_label)
        pred_llm.append(llm_result["label"])
        per_claim.append({
            "claim_id": cid, "arm": claim["arm"],
            "source_pattern": claim["source_pattern"],
            "ground_truth": gt, "regex": regex_label,
            "llm": llm_result["label"],
        })

    n = len(truth)
    if n == 0:
        print("ERROR: no overlap between sample and labels", file=sys.stderr)
        return 2

    cats = scorer.A3_MECHANISM_LABELS
    kappa_regex = cohens_kappa(pred_regex, truth, cats)
    kappa_llm = cohens_kappa(pred_llm, truth, cats)
    acc_regex = sum(1 for p, t in zip(pred_regex, truth) if p == t) / n
    acc_llm = sum(1 for p, t in zip(pred_llm, truth) if p == t) / n
    safe_label_count = sum(
        1 for p in pred_llm
        if p in ("AMBIGUOUS", "CHALLENGER_FABRICATION")
    )
    safe_label_rate = safe_label_count / n

    # Conservative metric for the head-to-head: the smaller of accuracy and kappa.
    def conservative(acc: float, k: float | None) -> float:
        return min(acc, k) if k is not None else acc

    score_regex = conservative(acc_regex, kappa_regex)
    score_llm = conservative(acc_llm, kappa_llm)

    pass_kappa = score_llm > score_regex
    pass_safe_label = safe_label_rate <= SAFE_LABEL_CAP
    verdict = "PASS" if (pass_kappa and pass_safe_label) else "FAIL"

    fail_reasons = []
    if not pass_kappa:
        fail_reasons.append(
            f"LLM conservative score {score_llm:.3f} ≤ regex {score_regex:.3f}"
        )
    if not pass_safe_label:
        fail_reasons.append(
            f"safe-label rate {safe_label_rate:.2%} > cap {SAFE_LABEL_CAP:.0%}"
        )

    report = [
        "# A3 Calibration Report",
        f"- Sample size: {n}",
        f"- Classifier model: {classifier_model}",
        "",
        "## Head-to-head against ground truth",
        "",
        "| Classifier | Accuracy | Cohen's kappa | Conservative score |",
        "|---|---|---|---|",
        (f"| regex | {acc_regex:.3f} | "
         f"{('—' if kappa_regex is None else f'{kappa_regex:.3f}')} | "
         f"{score_regex:.3f} |"),
        (f"| LLM | {acc_llm:.3f} | "
         f"{('—' if kappa_llm is None else f'{kappa_llm:.3f}')} | "
         f"{score_llm:.3f} |"),
        "",
        "## Safe-label rate (LLM)",
        f"- AMBIGUOUS + CHALLENGER_FABRICATION = {safe_label_count}/{n} = "
        f"{safe_label_rate:.2%}",
        f"- Cap: {SAFE_LABEL_CAP:.0%}",
        "",
        "## Verdict",
        f"**{verdict}** — A3 ships only on PASS.",
    ]
    if fail_reasons:
        report.append("")
        report.append("Reasons:")
        for r in fail_reasons:
            report.append(f"- {r}")
    report.extend(["", "## Per-claim", "",
                   "| claim_id | arm | source_pattern | ground_truth | regex | llm |",
                   "|---|---|---|---|---|---|"])
    for c in per_claim:
        report.append(
            f"| `{c['claim_id'][:60]}` | {c['arm']} | {c['source_pattern']} | "
            f"{c['ground_truth']} | {c['regex']} | {c['llm']} |"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report) + "\n")

    print(f"Sample: n={n}")
    print(f"  regex: acc={acc_regex:.3f}  kappa={kappa_regex}")
    print(f"  llm:   acc={acc_llm:.3f}  kappa={kappa_llm}")
    print(f"  safe-label rate: {safe_label_rate:.2%}")
    print(f"VERDICT: {verdict}")
    if fail_reasons:
        for r in fail_reasons:
            print(f"  - {r}")
    print(f"Report: {report_path}")
    return 0 if verdict == "PASS" else 1


# ── Main ───────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = ap.add_subparsers(dest="cmd", required=False)

    p_collect = sub.add_parser("collect-only",
                               help="Extract FALSIFIED claims from n=3 runs")
    p_collect.add_argument("--store-root", type=Path, default=DEFAULT_STORE)
    p_collect.add_argument("--output", type=Path, default=CLAIMS_PATH)

    p_sample = sub.add_parser("sample", help="Stratified sample for labeling")
    p_sample.add_argument("--input", type=Path, default=CLAIMS_PATH)
    p_sample.add_argument("--output", type=Path, default=SAMPLE_PATH)

    p_label = sub.add_parser("label", help="Interactive hand-labeling")
    p_label.add_argument("--sample", type=Path, default=SAMPLE_PATH)
    p_label.add_argument("--labels", type=Path, default=LABELS_PATH)

    p_compare = sub.add_parser("compare",
                               help="Compute kappa + verdict")
    p_compare.add_argument("--claims", type=Path, default=CLAIMS_PATH)
    p_compare.add_argument("--labels", type=Path, default=LABELS_PATH)
    p_compare.add_argument("--report", type=Path, default=REPORT_PATH)
    p_compare.add_argument("--model", default=scorer.A3_DEFAULT_MODEL)

    # Backward-compat for plan's `--collect-only` flag style.
    ap.add_argument("--collect-only", action="store_true",
                    help="Shortcut for `collect-only` subcommand")

    args = ap.parse_args(argv)

    if args.collect_only:
        return cmd_collect(DEFAULT_STORE, CLAIMS_PATH)
    if args.cmd == "collect-only":
        return cmd_collect(args.store_root, args.output)
    if args.cmd == "sample":
        return cmd_sample(args.input, args.output)
    if args.cmd == "label":
        return cmd_label(args.sample, args.labels)
    if args.cmd == "compare":
        return cmd_compare(args.claims, args.labels, args.report, args.model)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
