#!/usr/bin/env python3.11
"""UserPromptSubmit hook: classify user intent and inject routing suggestions.

Reads the user's message, matches against intent patterns, and outputs
routing context that gets prepended to Claude's processing. Also checks
for recurring-error flags set by hook-error-tracker.py.

This makes skill routing deterministic: the suggestion fires every time
the pattern matches, regardless of Claude's context pressure or mood.

Output: plain text to stdout (injected as additional context).
Empty output = no suggestion.
"""
import json
import os
import re
import sys

# Session-scoped state
SESSION_ID = os.environ.get("CLAUDE_SESSION_ID", str(os.getppid()))
ERROR_TRACKER_FILE = f"/tmp/claude-error-tracker-{SESSION_ID}.json"
SUGGESTION_TRACKER_FILE = f"/tmp/claude-intent-suggestions-{SESSION_ID}.json"

# Intent patterns: (compiled_regex, skill_route, context_message)
# Order matters — first match wins.
INTENT_PATTERNS = [
    # Diagnostic / investigation
    (
        re.compile(
            r'\b(broke|broken|crash|error|fail|bug|weird|not working|'
            r'doesn.t work|stopped working|keeps? failing|debug|diagnose|'
            r'root.?cause|why is .+ happening|why does .+ keep)\b',
            re.IGNORECASE,
        ),
        "investigate",
        (
            "ROUTING SUGGESTION: The user's message indicates a diagnostic need. "
            "Consider running /investigate (symptom mode) for structured root-cause "
            "analysis instead of ad-hoc debugging. If the issue is clearly trivial "
            "(typo, missing import), fix it directly — /investigate is for when the "
            "cause isn't obvious."
        ),
    ),
    # Drift detection
    (
        re.compile(
            r'\b(used to work|changed|different now|diverged|regression|'
            r'wasn.t like this|worked before|broke after)\b',
            re.IGNORECASE,
        ),
        "investigate-drift",
        (
            "ROUTING SUGGESTION: The user describes behavioral drift — something "
            "changed from a known-good state. Consider running /investigate in drift "
            "mode to trace what diverged."
        ),
    ),
    # Problem discovery / new feature
    (
        re.compile(
            r'\b(I want to build|new feature|add support for|create a|'
            r'let.s build|we need to add|implement|build me)\b',
            re.IGNORECASE,
        ),
        "think",
        (
            "ROUTING SUGGESTION: The user wants to build something new. "
            "Consider running /think discover for problem discovery before "
            "jumping to implementation. If the scope is already clear, "
            "/think refine for a quick sanity check."
        ),
    ),
    # Planning
    (
        re.compile(
            r'\b(plan this|how should we build|implementation plan|'
            r'write a plan|plan it out|break this down)\b',
            re.IGNORECASE,
        ),
        "plan",
        (
            "ROUTING SUGGESTION: The user wants an implementation plan. "
            "Consider running /plan to write a structured plan with valid "
            "frontmatter. Use /plan --auto to auto-chain the full pipeline."
        ),
    ),
    # Review
    (
        re.compile(
            r'\b(review this|check my code|is this ready|code review|'
            r'look over this|ready to ship|review the diff)\b',
            re.IGNORECASE,
        ),
        "review",
        (
            "ROUTING SUGGESTION: The user wants a code review. "
            "Consider running /review for cross-model review through "
            "PM, Security, and Architecture lenses."
        ),
    ),
    # Ship / deploy
    (
        re.compile(
            r'\b(ship it|deploy|release this|push to prod|go live|'
            r'ready to ship|let.s ship)\b',
            re.IGNORECASE,
        ),
        "ship",
        (
            "ROUTING SUGGESTION: The user wants to ship. "
            "Consider running /ship for pre-flight gates (tests, review, "
            "verify, QA) before deploying."
        ),
    ),
    # Exploration
    (
        re.compile(
            r'\b(explore options|what are our choices|alternatives|'
            r'brainstorm|divergent|what.s possible|options for)\b',
            re.IGNORECASE,
        ),
        "explore",
        (
            "ROUTING SUGGESTION: The user wants to explore options. "
            "Consider running /explore for 3+ divergent directions "
            "with cross-model synthesis."
        ),
    ),
    # Challenge / scope gate
    (
        re.compile(
            r'\b(is this worth|should we (even |really )?do|'
            r'evaluate this|worth building|scope check|'
            r'do we really need)\b',
            re.IGNORECASE,
        ),
        "challenge",
        (
            "ROUTING SUGGESTION: The user is questioning whether this work "
            "is necessary. Consider running /challenge for a cross-model "
            "evaluation of whether to proceed."
        ),
    ),
    # Pressure test / devil's advocate
    (
        re.compile(
            r'\b(what could go wrong|devil.s advocate|poke holes|'
            r'stress.?test|pre.?mortem|what if .+ fails|risks?)\b',
            re.IGNORECASE,
        ),
        "pressure-test",
        (
            "ROUTING SUGGESTION: The user wants adversarial analysis. "
            "Consider running /pressure-test for counter-thesis or "
            "pre-mortem failure analysis."
        ),
    ),
    # Design
    (
        re.compile(
            r'\b(design (this|the|a|our|my)|what should it look like|UI|UX|'
            r'visual|layout|mockup|wireframe|design system)\b',
            re.IGNORECASE,
        ),
        "design",
        (
            "ROUTING SUGGESTION: The user has a design need. "
            "Consider running /design (infer mode from context: consult "
            "for new design systems, review for visual QA, variants for "
            "exploring options)."
        ),
    ),
    # Research
    (
        re.compile(
            r'\b(research|find out about|what do we know about|'
            r'look up|evidence for|landscape|state of the art)\b',
            re.IGNORECASE,
        ),
        "research",
        (
            "ROUTING SUGGESTION: The user needs research. "
            "Consider running /research for deep web research "
            "with citations via Perplexity Sonar."
        ),
    ),
    # Session end
    (
        re.compile(
            r'\b(wrap up|end session|I.m done|close out|'
            r'that.s it for now|save and quit)\b',
            re.IGNORECASE,
        ),
        "wrap",
        (
            "ROUTING SUGGESTION: The user wants to end the session. "
            "Run /wrap to save handoff, session log, and current state."
        ),
    ),
    # Lost / help
    (
        re.compile(
            r'\b(I.m lost|what can I do|help me|how does this work|'
            r'where do I start|confused|what.s available)\b',
            re.IGNORECASE,
        ),
        "guide",
        (
            "ROUTING SUGGESTION: The user needs orientation. "
            "Run /guide to show the intent-based skill map."
        ),
    ),
]


def load_tracker(path):
    """Load a JSON tracker file, return empty dict on failure."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_tracker(path, data):
    """Save tracker data to JSON file."""
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except OSError:
        pass


def check_recurring_errors():
    """Check if the error tracker has flagged recurring errors."""
    tracker = load_tracker(ERROR_TRACKER_FILE)
    recurring = []
    for sig, info in tracker.items():
        if isinstance(info, dict) and info.get("count", 0) >= 2:
            recurring.append(info.get("summary", sig))
    return recurring


def already_suggested(skill):
    """Check if we already suggested this skill this session."""
    tracker = load_tracker(SUGGESTION_TRACKER_FILE)
    return tracker.get(skill, 0) > 0


def record_suggestion(skill):
    """Record that we suggested this skill."""
    tracker = load_tracker(SUGGESTION_TRACKER_FILE)
    tracker[skill] = tracker.get(skill, 0) + 1
    save_tracker(SUGGESTION_TRACKER_FILE, tracker)


def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return  # empty output = no suggestion

    prompt = data.get("prompt", "")
    if not prompt:
        return

    suggestions = []

    # Check for recurring errors (proactive routing)
    recurring = check_recurring_errors()
    if recurring and not already_suggested("investigate-proactive"):
        error_summary = "; ".join(recurring[:3])
        suggestions.append(
            f"PROACTIVE ROUTING: Recurring errors detected in this session: "
            f"{error_summary}. Consider suggesting /investigate for structured "
            f"root-cause analysis instead of retrying."
        )
        record_suggestion("investigate-proactive")

    # Match user intent (reactive routing)
    for pattern, skill, message in INTENT_PATTERNS:
        if pattern.search(prompt):
            if not already_suggested(skill):
                suggestions.append(message)
                record_suggestion(skill)
            break  # first match wins

    if suggestions:
        print("\n\n".join(suggestions))


if __name__ == "__main__":
    main()
