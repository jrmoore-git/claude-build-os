#!/usr/bin/env python3.11
"""Pre-refine conviction gate for CloudZero velocity v3 proposals.

Reads a markdown proposal, parses the `## Recommendations` section, and verifies
that every top-level numbered recommendation has Owner, Horizon, and Why now
fields with content that passes structural and semantic checks.

Exit 0 on full pass, non-zero on any failure.
"""
import argparse
import json
import re
import sys
from pathlib import Path


HORIZON_ENUM = {"this quarter", "next quarter", "ongoing", "blocking-dependent"}

OWNER_GENERIC_DENYLIST = {
    "engineering",
    "team",
    "leadership",
    "ops",
    "operations",
    "management",
    "product",
    "platform",
    "we",
    "staff",
}

WHY_NOW_VAGUENESS_PHRASES = [
    "re-evaluate if things change",
    "reevaluate if things change",
    "monitor for regression",
    "when we have more data",
    "as needed",
    "as appropriate",
    "if things change",
    "tbd",
]

METRIC_FALLBACK_TOKENS = [
    "time",
    "rate",
    "count",
    "latency",
    "throughput",
    "volume",
    "frequency",
    "p50",
    "p90",
    "p95",
    "p99",
    "median",
]

FIELD_LABELS = ("owner", "horizon", "why now")


def split_recommendations(rec_section_text):
    """Split the Recommendations section body into individual recommendations.

    Top-level numbered list pattern: a line starting with an integer followed by
    `.` or `)` at the very start of the line. Content until the next such line
    (or end of section) belongs to that recommendation.
    """
    lines = rec_section_text.splitlines()
    recs = []
    current = None
    # Allow optional leading markdown bold (**) or italic (*) before the
    # number. LLMs frequently emit bold-numbered recommendations like
    # "**1. Title**" instead of plain "1. Title".
    number_pattern = re.compile(r"^\s{0,3}\*{0,2}(\d+)[\.\)]\s+(.*)$")
    for line in lines:
        match = number_pattern.match(line)
        if match and len(line) - len(line.lstrip()) <= 3:
            if current is not None:
                recs.append("\n".join(current).strip())
            current = [match.group(2)]
            continue
        if current is not None:
            current.append(line)
    if current is not None:
        recs.append("\n".join(current).strip())
    return recs


def extract_recommendations_section(proposal_text):
    """Return text under `## Recommendations` up to the next `## ` heading."""
    pattern = re.compile(
        r"^##\s+Recommendations\s*$(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(proposal_text)
    if not match:
        return None
    return match.group(1)


def extract_section(proposal_text, heading):
    """Return text under a specific `## Heading` up to next `## ` or EOF."""
    escaped = re.escape(heading.lstrip("# ").strip())
    pattern = re.compile(
        rf"^##\s+{escaped}\s*$(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(proposal_text)
    if not match:
        return None
    return match.group(1)


def build_metric_lexicon(proposal_text, methodology_heading):
    """Collect metric name tokens from the Methodology section if present."""
    section = extract_section(proposal_text, methodology_heading)
    if section is None:
        return set()
    tokens = set()
    for line in section.splitlines():
        stripped = line.strip().lower()
        if not stripped:
            continue
        if stripped.startswith("###"):
            name = stripped.lstrip("#").strip()
            if name:
                tokens.add(name)
            continue
        bullet_match = re.match(r"^[\-\*\+]\s+\*?\*?([^:*]+?)[\*:]", stripped)
        if bullet_match:
            tokens.add(bullet_match.group(1).strip())
    return {t for t in tokens if t}


def extract_field(rec_text, field_name):
    """Extract the value of a labeled field from a recommendation paragraph.

    Field value runs from the label to the next recognized field label or
    end of recommendation. Labels are case-insensitive and may be preceded by
    list markers (`-`, `*`), bold (`**`), or nothing.
    """
    labels_alt = "|".join(re.escape(lbl) for lbl in FIELD_LABELS)
    # Match: optional list marker / bold, the field label, separator, then value.
    label_re = re.compile(
        rf"(?i)(?:^|\n|\*\*|\*|-|\s)(?P<label>{re.escape(field_name)})\s*[:\-\u2014\u2013]\s*",
    )
    stop_re = re.compile(
        rf"(?i)(?:\n|\*\*|\s|\*|-)\s*(?:{labels_alt})\s*[:\-\u2014\u2013]",
    )
    match = label_re.search(rec_text)
    if not match:
        return None
    start = match.end()
    tail = rec_text[start:]
    stop_match = stop_re.search(tail)
    if stop_match:
        value = tail[: stop_match.start()]
    else:
        value = tail
    # Trim trailing markdown bold, whitespace, stray brackets.
    value = value.strip()
    value = re.sub(r"\*+$", "", value).strip()
    value = re.sub(r"^\*+", "", value).strip()
    # Cut at first newline that starts a new bullet at column 0.
    newline_split = re.split(r"\n\s*[\-\*\+]\s", value, maxsplit=1)
    value = newline_split[0].strip()
    return value or None


def check_owner(value):
    if value is None:
        return "missing field"
    cleaned = value.strip().strip("[]").strip()
    if not cleaned:
        return "empty value"
    lowered = cleaned.lower()
    if lowered in OWNER_GENERIC_DENYLIST:
        return f'single generic word "{cleaned}"'
    words = cleaned.split()
    if len(words) < 2:
        return f'single generic word "{cleaned}"'
    # Named individual heuristic: exactly two words, both Capitalized, no team
    # nouns in the phrase.
    team_nouns = {
        "team",
        "teams",
        "guild",
        "group",
        "leadership",
        "working",
        "org",
        "council",
        "committee",
        "function",
        "productivity",
        "platform",
        "engineering",
        "product",
        "design",
        "ops",
        "operations",
        "infra",
        "infrastructure",
        "reliability",
        "security",
        "data",
        "analytics",
        "finance",
        "people",
        "hr",
        "success",
        "support",
        "sales",
        "marketing",
        "legal",
        "lead",
        "leads",
        "manager",
        "managers",
        "director",
        "directors",
        "head",
    }
    if len(words) == 2:
        both_capitalized = all(re.match(r"^[A-Z][a-z]+$", w) for w in words)
        has_team_noun = any(w.lower() in team_nouns for w in words)
        if both_capitalized and not has_team_noun:
            return f'looks like a named individual "{cleaned}"'
    return None


def check_horizon(value):
    if value is None:
        return "missing field"
    cleaned = value.strip().strip("[]").strip().lower()
    if not cleaned:
        return "empty value"
    if cleaned in HORIZON_ENUM:
        return None
    return (
        f'value "{cleaned}" not in enum '
        f"[this quarter, next quarter, ongoing, blocking-dependent]"
    )


def check_why_now(value, metric_lexicon):
    if value is None:
        return "missing field"
    cleaned = value.strip().strip("[]").strip()
    if not cleaned:
        return "empty value"
    lowered = cleaned.lower()
    for phrase in WHY_NOW_VAGUENESS_PHRASES:
        if phrase in lowered:
            return (
                "contains no numeric threshold or named metric "
                f'(matched vagueness phrase: "{phrase}")'
            )
    numeric_pattern = re.compile(
        r"(\d+(?:\.\d+)?\s*(?:%|days?|weeks?|months?|hours?|minutes?|seconds?|ms|s|per\s+\w+))"
        r"|(p(?:50|90|95|99)\s*[<>=\u2265\u2264]+\s*\d+)"
        r"|([<>=\u2265\u2264]+\s*\d+(?:\.\d+)?)",
        re.IGNORECASE,
    )
    if numeric_pattern.search(cleaned):
        return None
    for metric_name in metric_lexicon:
        if metric_name and metric_name in lowered:
            return None
    for token in METRIC_FALLBACK_TOKENS:
        if re.search(rf"\b\w+\s+{re.escape(token)}\b", lowered):
            return None
        if re.search(rf"\b{re.escape(token)}\s+\w+\b", lowered):
            return None
    # Named external event heuristic: capitalized multi-word phrase (2+ caps)
    # or a date-like token.
    caps_phrase = re.search(r"(?:[A-Z][a-zA-Z0-9]+[:\s\-]+){1,}[A-Z][a-zA-Z0-9]+", cleaned)
    if caps_phrase:
        return None
    date_pattern = re.search(
        r"\b(?:Q[1-4]|20\d{2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b",
        cleaned,
    )
    if date_pattern:
        return None
    return "contains no numeric threshold or named metric"


def evaluate_recommendation(rec_text, metric_lexicon):
    failures = []
    owner_value = extract_field(rec_text, "owner")
    horizon_value = extract_field(rec_text, "horizon")
    why_value = extract_field(rec_text, "why now")

    owner_reason = check_owner(owner_value)
    if owner_reason:
        failures.append(("Owner", owner_reason))
    horizon_reason = check_horizon(horizon_value)
    if horizon_reason:
        failures.append(("Horizon", horizon_reason))
    why_reason = check_why_now(why_value, metric_lexicon)
    if why_reason:
        failures.append(("Why-now", why_reason))
    return failures


def run_gate(proposal_path, methodology_heading):
    text = Path(proposal_path).read_text(encoding="utf-8")
    rec_section = extract_recommendations_section(text)
    if rec_section is None:
        return {
            "status": "fail",
            "rec_count": 0,
            "failures": [
                {
                    "rec_index": 0,
                    "field": "Section",
                    "reason": "no ## Recommendations section found",
                }
            ],
        }
    recommendations = split_recommendations(rec_section)
    if not recommendations:
        return {
            "status": "fail",
            "rec_count": 0,
            "failures": [
                {
                    "rec_index": 0,
                    "field": "Section",
                    "reason": "Recommendations section contains no numbered items",
                }
            ],
        }
    metric_lexicon = build_metric_lexicon(text, methodology_heading)
    all_failures = []
    for index, rec in enumerate(recommendations, start=1):
        rec_failures = evaluate_recommendation(rec, metric_lexicon)
        for field, reason in rec_failures:
            all_failures.append({"rec_index": index, "field": field, "reason": reason})
    status = "pass" if not all_failures else "fail"
    return {
        "status": status,
        "rec_count": len(recommendations),
        "failures": all_failures,
    }


def format_human(report):
    lines = []
    lines.append(f"Conviction gate: {report['status'].upper()}")
    lines.append(f"Recommendations parsed: {report['rec_count']}")
    if report["failures"]:
        lines.append("Failures:")
        for failure in report["failures"]:
            lines.append(
                f"  [REC {failure['rec_index']}] {failure['field']} FAIL: {failure['reason']}"
            )
    else:
        lines.append("All recommendations passed structural and semantic checks.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Pre-refine conviction gate for velocity v3 proposals.",
    )
    parser.add_argument(
        "--proposal",
        default="tasks/cz-velocity-v3-proposal.md",
        help="Path to proposal markdown (default: tasks/cz-velocity-v3-proposal.md)",
    )
    parser.add_argument(
        "--methodology-section",
        default="## Methodology",
        help="Heading of the methodology section used to build metric lexicon",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON report instead of human-readable output",
    )
    args = parser.parse_args()

    report = run_gate(args.proposal, args.methodology_section)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_human(report))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
