#!/usr/bin/env python3.11
"""Anonymize arm C + arm D challenger findings for blinded adjudication.

Study-specific tool for tasks/debate-efficacy-study-*. Not part of production debate pipeline.

For each proposal topic:
1. Parse findings from arm-c/<topic>.md and arm-d/<topic>.md
2. Tag each with its source arm
3. Shuffle so order carries no arm signal
4. Write anonymized numbered list to anonymized/<topic>.md (judge input)
5. Write mapping to mapping/<topic>.json (arm identity per finding number — judge does NOT see this)

Usage: python3.11 scripts/debate_efficacy_anonymize.py
"""

import json
import random
import re
from pathlib import Path

STUDY_ROOT = Path("/Users/justinmoore/buildos/framework/tasks")
TOPICS = ["autobuild", "explore-intake", "learning-velocity", "streamline-rules", "litellm-fallback"]
SEED = 20260417  # reproducible anonymization

# Parse findings from a debate.py challenge output file.
# Structure: "## Challenger X (persona) — Challenges" blocks, each containing
# "## Challenges" subsection with numbered items (1. ... 2. ...), then
# "## Concessions" and "## Verdict".
CHALLENGER_HEADER = re.compile(
    r"^## Challenger ([A-Z]) \(([\w-]+)\) — Challenges", re.MULTILINE
)
# Split on "## " major headers within a challenger block to find the Challenges subsection.


def parse_findings(filepath: Path) -> list[dict]:
    """Return list of {persona, finding_text} dicts for all numbered findings."""
    text = filepath.read_text()
    findings = []
    # Split by challenger headers
    parts = CHALLENGER_HEADER.split(text)
    # parts = [preamble, letter1, persona1, body1, letter2, persona2, body2, ...]
    for i in range(1, len(parts), 3):
        if i + 2 >= len(parts):
            break
        letter = parts[i]
        persona = parts[i + 1]
        body = parts[i + 2]
        # Find the "## Challenges" subsection, ends at next "## " header
        challenges_match = re.search(
            r"## Challenges\s*\n(.*?)(?=\n## |\Z)", body, re.DOTALL
        )
        if not challenges_match:
            continue
        challenges_text = challenges_match.group(1)
        # Parse numbered items — match `1. ` through `20. ` at line start
        items = re.split(r"\n(?=\d+\.\s)", challenges_text.strip())
        for item in items:
            item = item.strip()
            if not item or not re.match(r"^\d+\.\s", item):
                continue
            # Strip leading number
            finding = re.sub(r"^\d+\.\s*", "", item, count=1).strip()
            findings.append(
                {
                    "persona": persona,
                    "challenger_letter": letter,
                    "text": finding,
                }
            )
    return findings


def main():
    random.seed(SEED)
    anon_dir = STUDY_ROOT / "debate-efficacy-study-anonymized"
    map_dir = STUDY_ROOT / "debate-efficacy-study-mapping"
    anon_dir.mkdir(exist_ok=True)
    map_dir.mkdir(exist_ok=True)

    summary = []

    for topic in TOPICS:
        arm_c_file = STUDY_ROOT / "debate-efficacy-study-arm-c" / f"{topic}.md"
        arm_d_file = STUDY_ROOT / "debate-efficacy-study-arm-d" / f"{topic}.md"

        if not arm_c_file.exists():
            print(f"MISSING {arm_c_file}")
            continue
        if not arm_d_file.exists():
            print(f"MISSING {arm_d_file}")
            continue

        c_findings = [
            {**f, "arm": "C"} for f in parse_findings(arm_c_file)
        ]
        d_findings = [
            {**f, "arm": "D"} for f in parse_findings(arm_d_file)
        ]
        pooled = c_findings + d_findings
        random.shuffle(pooled)

        # Write anonymized list (judge input)
        anon_lines = [
            f"# Anonymized Findings — {topic}",
            "",
            f"Total: {len(pooled)} findings pooled from two anonymous reviewer panels.",
            f"Arm C contributed {len(c_findings)}; arm D contributed {len(d_findings)}.",
            "Arm identity is withheld from the judge by design.",
            "",
            "---",
            "",
        ]
        mapping = []
        for idx, f in enumerate(pooled, start=1):
            anon_lines.append(f"## Finding {idx}")
            anon_lines.append("")
            anon_lines.append(f["text"])
            anon_lines.append("")
            mapping.append(
                {
                    "finding_number": idx,
                    "arm": f["arm"],
                    "persona": f["persona"],
                    "challenger_letter": f["challenger_letter"],
                    "text_preview": f["text"][:120],
                }
            )

        (anon_dir / f"{topic}.md").write_text("\n".join(anon_lines))
        (map_dir / f"{topic}.json").write_text(json.dumps(mapping, indent=2))

        summary.append(
            {
                "topic": topic,
                "arm_c_count": len(c_findings),
                "arm_d_count": len(d_findings),
                "pooled_count": len(pooled),
            }
        )
        print(
            f"{topic}: arm C={len(c_findings)}, arm D={len(d_findings)}, pooled={len(pooled)}"
        )

    (STUDY_ROOT / "debate-efficacy-study-anonymization-summary.json").write_text(
        json.dumps(summary, indent=2)
    )
    print("\nWrote anonymized findings + mappings.")


if __name__ == "__main__":
    main()
