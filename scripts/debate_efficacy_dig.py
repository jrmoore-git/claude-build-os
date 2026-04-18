#!/usr/bin/env python3.11
"""Deeper analysis: cross-arm vs within-arm duplicates, uniqueness, finding types.

Parses judge 'DUPLICATE_OF_N' verdicts' evidence strings to extract the referenced
finding number (the judge said "DUPLICATE_OF_N" in the verdict field but put the
actual number in the evidence prose — e.g., "Duplicates Finding 14").

For each proposal, computes:
- VALID findings per arm (already known)
- DUPLICATE findings per arm, split into:
  - cross-arm (arm C finding duplicates an arm D finding, or vice versa)
  - within-arm (arm C duplicates arm C, etc.)
  - unresolvable (judge didn't name a number)
- Unique-VALID per arm (VALID + no duplicate-pair on other arm)

Also tags finding TYPE based on regex matching the original finding text:
[ASSUMPTION], [RISK], [OVER-ENGINEERED], [UNDER-ENGINEERED], [ALTERNATIVE], [MATERIAL], [ADVISORY].
"""

import json
import re
from pathlib import Path

STUDY = Path("/Users/justinmoore/buildos/framework/tasks")
TOPICS = ["autobuild", "explore-intake", "learning-velocity", "streamline-rules", "litellm-fallback"]

DUP_REF_PATTERNS = [
    re.compile(r"Duplicates?\s+Finding\s+(\d+)", re.IGNORECASE),
    re.compile(r"duplicate of\s+(\d+)", re.IGNORECASE),
    re.compile(r"#(\d+)"),
    re.compile(r"Finding\s+(\d+)"),
]

TAG_PATTERNS = {
    "MATERIAL": re.compile(r"\[MATERIAL\]", re.IGNORECASE),
    "ADVISORY": re.compile(r"\[ADVISORY\]", re.IGNORECASE),
    "ASSUMPTION": re.compile(r"\[ASSUMPTION\]", re.IGNORECASE),
    "RISK": re.compile(r"\[RISK\]", re.IGNORECASE),
    "ALTERNATIVE": re.compile(r"\[ALTERNATIVE\]", re.IGNORECASE),
    "OVER_ENGINEERED": re.compile(r"\[OVER[- ]ENGINEERED\]", re.IGNORECASE),
    "UNDER_ENGINEERED": re.compile(r"\[UNDER[- ]ENGINEERED\]", re.IGNORECASE),
}


def extract_dup_ref(evidence: str) -> int | None:
    """Try to extract the referenced finding number from DUPLICATE_OF evidence prose."""
    for pat in DUP_REF_PATTERNS:
        m = pat.search(evidence)
        if m:
            try:
                n = int(m.group(1))
                if 1 <= n <= 999:
                    return n
            except ValueError:
                pass
    return None


def tag_finding(text: str) -> dict:
    return {tag: bool(pat.search(text)) for tag, pat in TAG_PATTERNS.items()}


def analyze(topic: str) -> dict:
    mapping = json.loads((STUDY / "debate-efficacy-study-mapping" / f"{topic}.json").read_text())
    by_num = {m["finding_number"]: m for m in mapping}
    # Load full finding texts from anonymized file
    anon_text = (STUDY / "debate-efficacy-study-anonymized" / f"{topic}.md").read_text()
    parts = re.split(r"^## Finding (\d+)$", anon_text, flags=re.MULTILINE)
    text_by_num = {}
    for i in range(1, len(parts) - 1, 2):
        try:
            n = int(parts[i])
            text_by_num[n] = parts[i + 1].strip()
        except ValueError:
            pass
    # Parse adjudication
    adj = (STUDY / "debate-efficacy-study-adjudication" / f"{topic}.md").read_text()
    verdicts = {}
    for line in adj.splitlines():
        line = line.strip()
        if not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "finding" in obj and "verdict" in obj:
            verdicts[obj["finding"]] = obj

    # Walk findings and classify
    per_arm = {
        "C": {"valid": [], "unvalidated": [], "invalid": [], "dup_cross": [], "dup_within": [], "dup_unresolved": []},
        "D": {"valid": [], "unvalidated": [], "invalid": [], "dup_cross": [], "dup_within": [], "dup_unresolved": []},
    }
    tags_per_arm = {"C": {t: 0 for t in TAG_PATTERNS}, "D": {t: 0 for t in TAG_PATTERNS}}
    valid_tags_per_arm = {"C": {t: 0 for t in TAG_PATTERNS}, "D": {t: 0 for t in TAG_PATTERNS}}

    for n, m in by_num.items():
        arm = m["arm"]
        text = text_by_num.get(n, "")
        tags = tag_finding(text)
        for t, v in tags.items():
            if v:
                tags_per_arm[arm][t] += 1
        v = verdicts.get(n)
        if v is None:
            per_arm[arm]["unvalidated"].append(n)
            continue
        verdict_str = v["verdict"]
        evidence = v.get("evidence", "")
        if verdict_str == "VALID_IN_EVIDENCE":
            per_arm[arm]["valid"].append(n)
            for t, vv in tags.items():
                if vv:
                    valid_tags_per_arm[arm][t] += 1
        elif verdict_str == "UNVALIDATED":
            per_arm[arm]["unvalidated"].append(n)
        elif verdict_str == "INVALID":
            per_arm[arm]["invalid"].append(n)
        elif verdict_str.startswith("DUPLICATE"):
            ref = extract_dup_ref(evidence)
            if ref is None or ref not in by_num:
                per_arm[arm]["dup_unresolved"].append(n)
            else:
                ref_arm = by_num[ref]["arm"]
                if ref_arm == arm:
                    per_arm[arm]["dup_within"].append({"finding": n, "ref": ref})
                else:
                    per_arm[arm]["dup_cross"].append({"finding": n, "ref": ref, "ref_arm": ref_arm})

    # Compute adjusted-valid count:
    # For each arm, count valid findings PLUS cross-arm duplicates where THIS arm's
    # finding was the duplicate (other arm got the "first-credit"). These are cases
    # where both arms independently found the same thing but the judge only credited one.
    #
    # So a fair "did arm X find this issue?" count =
    #   arm X's VALID count + count of cross-arm duplicates arm X filed that reference arm Y's VALID finding.
    adjusted_valid = {"C": 0, "D": 0}
    for arm in ("C", "D"):
        adjusted_valid[arm] = len(per_arm[arm]["valid"])
        # Add cross-arm dupes where the referenced finding on the OTHER arm was classified VALID
        for dup in per_arm[arm]["dup_cross"]:
            ref = dup["ref"]
            ref_verdict = verdicts.get(ref, {}).get("verdict", "")
            if ref_verdict == "VALID_IN_EVIDENCE":
                adjusted_valid[arm] += 1

    summary = {
        "topic": topic,
        "raw_valid": {arm: len(per_arm[arm]["valid"]) for arm in ("C", "D")},
        "adjusted_valid_with_cross_dupes": adjusted_valid,
        "dup_cross_count": {arm: len(per_arm[arm]["dup_cross"]) for arm in ("C", "D")},
        "dup_within_count": {arm: len(per_arm[arm]["dup_within"]) for arm in ("C", "D")},
        "dup_unresolved_count": {arm: len(per_arm[arm]["dup_unresolved"]) for arm in ("C", "D")},
        "tag_distribution_all": tags_per_arm,
        "tag_distribution_valid_only": valid_tags_per_arm,
    }
    return summary


def main():
    all_results = [analyze(t) for t in TOPICS]
    # Totals
    totals = {
        "raw_valid": {"C": 0, "D": 0},
        "adjusted_valid_with_cross_dupes": {"C": 0, "D": 0},
        "dup_cross_count": {"C": 0, "D": 0},
        "dup_within_count": {"C": 0, "D": 0},
        "dup_unresolved_count": {"C": 0, "D": 0},
        "tag_distribution_all": {arm: {t: 0 for t in TAG_PATTERNS} for arm in ("C", "D")},
        "tag_distribution_valid_only": {arm: {t: 0 for t in TAG_PATTERNS} for arm in ("C", "D")},
    }
    for r in all_results:
        for arm in ("C", "D"):
            totals["raw_valid"][arm] += r["raw_valid"][arm]
            totals["adjusted_valid_with_cross_dupes"][arm] += r["adjusted_valid_with_cross_dupes"][arm]
            totals["dup_cross_count"][arm] += r["dup_cross_count"][arm]
            totals["dup_within_count"][arm] += r["dup_within_count"][arm]
            totals["dup_unresolved_count"][arm] += r["dup_unresolved_count"][arm]
            for tag in TAG_PATTERNS:
                totals["tag_distribution_all"][arm][tag] += r["tag_distribution_all"][arm][tag]
                totals["tag_distribution_valid_only"][arm][tag] += r["tag_distribution_valid_only"][arm][tag]

    out = {"per_topic": all_results, "totals": totals}
    (STUDY / "debate-efficacy-study-deep-analysis.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(totals, indent=2))


if __name__ == "__main__":
    main()
