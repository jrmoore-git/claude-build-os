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
import glob as globmod
import json
import os
import re
import sys

# Session-scoped state
SESSION_ID = os.environ.get("CLAUDE_SESSION_ID", str(os.getppid()))
ERROR_TRACKER_FILE = f"/tmp/claude-error-tracker-{SESSION_ID}.json"
SUGGESTION_TRACKER_FILE = f"/tmp/claude-intent-suggestions-{SESSION_ID}.json"

# Project root for artifact detection
PROJECT_ROOT = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
TASKS_DIR = os.path.join(PROJECT_ROOT, "tasks")

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
    # Challenge / scope gate — explicit "should we build this?" language
    (
        re.compile(
            r'\b(is this worth|should we (even |really )?(do|build|add|implement|create)|'
            r'evaluate this|worth building|scope check|'
            r'do we really need)\b',
            re.IGNORECASE,
        ),
        "challenge",
        None,  # dynamic — filled by pipeline-aware logic
    ),
    # Pressure test / devil's advocate — explicit adversarial language
    (
        re.compile(
            r'\b(what could go wrong|devil.s advocate|poke holes|'
            r'stress.?test|pre.?mortem|what if .+ fails)\b',
            re.IGNORECASE,
        ),
        "pressure-test",
        None,  # dynamic — filled by pipeline-aware logic
    ),
    # Ambiguous evaluation — could be either challenge or pressure-test
    (
        re.compile(
            r'\b(is this (a )?(good|solid|sound|right|ready) |'
            r'is this (idea|approach|plan|direction) (good|solid|sound)|'
            r'what do you think (about|of) this|'
            r'sanity check|gut check|does this make sense|'
            r'am I (over|under)thinking|risks?)\b',
            re.IGNORECASE,
        ),
        "challenge-or-pressure-test",
        None,  # dynamic — resolved by pipeline state
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


def detect_pipeline_state():
    """Detect what artifacts exist to infer pipeline position.

    Returns a dict with booleans for each artifact type found,
    plus the most recent topic slug if detectable.
    """
    state = {
        "has_proposal": False,
        "has_challenge": False,
        "has_plan": False,
        "has_pressure_test": False,
        "has_premortem": False,
        "topic": None,
    }
    if not os.path.isdir(TASKS_DIR):
        return state

    # Find the most recent topic by looking at proposals and plans
    proposals = sorted(
        globmod.glob(os.path.join(TASKS_DIR, "*-proposal.md")),
        key=os.path.getmtime,
        reverse=True,
    )
    plans = sorted(
        globmod.glob(os.path.join(TASKS_DIR, "*-plan.md")),
        key=os.path.getmtime,
        reverse=True,
    )

    # Derive topic from most recent proposal or plan
    topic = None
    if proposals:
        topic = os.path.basename(proposals[0]).replace("-proposal.md", "")
    elif plans:
        topic = os.path.basename(plans[0]).replace("-plan.md", "")

    if topic:
        state["topic"] = topic
        state["has_proposal"] = os.path.exists(
            os.path.join(TASKS_DIR, f"{topic}-proposal.md")
        )
        state["has_challenge"] = os.path.exists(
            os.path.join(TASKS_DIR, f"{topic}-challenge.md")
        )
        state["has_plan"] = os.path.exists(
            os.path.join(TASKS_DIR, f"{topic}-plan.md")
        )
        state["has_pressure_test"] = os.path.exists(
            os.path.join(TASKS_DIR, f"{topic}-pressure-test.md")
        )
        state["has_premortem"] = os.path.exists(
            os.path.join(TASKS_DIR, f"{topic}-premortem.md")
        )

    return state


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


def resolve_challenge_vs_pressure_test(skill, pipeline):
    """Use pipeline state to pick the right skill and generate a message.

    Returns (resolved_skill, message) or (None, None) to skip.
    """
    topic = pipeline["topic"]
    topic_label = f" (topic: {topic})" if topic else ""

    # Explicit /challenge language
    if skill == "challenge":
        if pipeline["has_challenge"]:
            # Already challenged — they probably want pressure-test
            return (
                "pressure-test",
                f"ROUTING SUGGESTION: A challenge artifact already exists{topic_label}. "
                "The user may want /pressure-test to stress-test the approach, "
                "or /pressure-test --premortem if a plan exists. "
                "If they truly want to re-challenge, run /challenge."
            )
        return (
            "challenge",
            "ROUTING SUGGESTION: The user is questioning whether this work "
            "is necessary. Run /challenge for a cross-model go/no-go evaluation."
        )

    # Explicit /pressure-test language
    if skill == "pressure-test":
        if pipeline["has_plan"]:
            existing = ""
            if pipeline["has_premortem"]:
                existing = (
                    f" Note: a premortem already exists at "
                    f"tasks/{topic}-premortem.md — re-run to update or "
                    "review the existing one."
                )
            elif pipeline["has_pressure_test"]:
                existing = (
                    f" Note: a pressure-test already exists at "
                    f"tasks/{topic}-pressure-test.md — re-run to update or "
                    "review the existing one."
                )
            return (
                "pressure-test",
                f"ROUTING SUGGESTION: A plan exists{topic_label}. "
                "Run /pressure-test --premortem to assume the plan failed "
                f"and write the post-mortem from the future.{existing}"
            )
        if pipeline["has_proposal"] and not pipeline["has_challenge"]:
            return (
                "pressure-test",
                f"ROUTING SUGGESTION: The user wants adversarial analysis{topic_label}. "
                "Note: no /challenge artifact exists yet — consider whether "
                "/challenge (multi-model go/no-go gate) would be more valuable "
                "at this stage. If the user wants to stress-test the direction "
                "rather than gate it, run /pressure-test."
            )
        return (
            "pressure-test",
            "ROUTING SUGGESTION: The user wants adversarial analysis. "
            "Run /pressure-test for counter-thesis or pre-mortem failure analysis."
        )

    # Ambiguous — "is this a good idea?", "sanity check", "risks"
    if skill == "challenge-or-pressure-test":
        if pipeline["has_plan"]:
            # Post-plan: pressure-test (premortem) is more useful
            existing = ""
            if pipeline["has_premortem"]:
                existing = (
                    f" A premortem already exists at tasks/{topic}-premortem.md"
                    " — review it or re-run with updated context."
                )
            return (
                "pressure-test",
                f"ROUTING SUGGESTION: Ambiguous evaluation request, but a plan "
                f"exists{topic_label}. At this pipeline stage, /pressure-test "
                "--premortem is likely more useful (assumes plan failed, writes "
                f"post-mortem). /challenge is a pre-plan go/no-go gate.{existing}"
            )
        if pipeline["has_challenge"]:
            # Already challenged, no plan yet: pressure-test the approach
            return (
                "pressure-test",
                f"ROUTING SUGGESTION: Ambiguous evaluation request. A challenge "
                f"artifact already exists{topic_label} but no plan yet. "
                "/pressure-test would stress-test the approach. "
                "/challenge would re-run the go/no-go gate."
            )
        if pipeline["has_proposal"]:
            # Proposal exists, not yet challenged: /challenge is the gate
            return (
                "challenge",
                f"ROUTING SUGGESTION: Ambiguous evaluation request. A proposal "
                f"exists{topic_label} but hasn't been challenged yet. "
                "/challenge runs a multi-model go/no-go evaluation (should we "
                "build this?). /pressure-test stress-tests the approach "
                "(what could go wrong?)."
            )
        # No artifacts — default to challenge as the first gate
        return (
            "challenge",
            "ROUTING SUGGESTION: Ambiguous evaluation request with no pipeline "
            "artifacts on disk. Defaulting to /challenge (should we build this?) "
            "as the first gate. If the user already decided to build and wants "
            "adversarial analysis, run /pressure-test instead."
        )

    return (None, None)


def check_proactive_pipeline_routing(pipeline):
    """Generate proactive suggestions based on artifact gaps.

    Returns a list of (skill, message) tuples.
    """
    proactive = []
    topic = pipeline["topic"]
    if not topic:
        return proactive

    # Proposal exists, no challenge yet → suggest /challenge
    if (
        pipeline["has_proposal"]
        and not pipeline["has_challenge"]
    ):
        proactive.append((
            "challenge-proactive",
            f"PROACTIVE ROUTING: A proposal exists (tasks/{topic}-proposal.md) "
            "but hasn't been challenged yet. If the user is about to plan or "
            "build, consider suggesting /challenge first as the go/no-go gate."
        ))

    # Plan exists, no pressure-test or premortem → suggest /pressure-test
    if (
        pipeline["has_plan"]
        and not pipeline["has_pressure_test"]
        and not pipeline["has_premortem"]
    ):
        proactive.append((
            "pressure-test-proactive",
            f"PROACTIVE ROUTING: A plan exists (tasks/{topic}-plan.md) "
            "but hasn't been pressure-tested. If the user is about to build, "
            "consider suggesting /pressure-test --premortem to surface failure "
            "scenarios before execution."
        ))

    return proactive


def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return  # empty output = no suggestion

    prompt = data.get("prompt", "")
    if not prompt:
        return

    suggestions = []
    pipeline = detect_pipeline_state()

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

    # Proactive pipeline routing (artifact-driven)
    for skill_key, message in check_proactive_pipeline_routing(pipeline):
        if not already_suggested(skill_key):
            suggestions.append(message)
            record_suggestion(skill_key)

    # Match user intent (reactive routing)
    for pattern, skill, message in INTENT_PATTERNS:
        if pattern.search(prompt):
            # Dynamic routing for challenge/pressure-test/ambiguous
            if skill in ("challenge", "pressure-test", "challenge-or-pressure-test"):
                resolved_skill, resolved_msg = resolve_challenge_vs_pressure_test(
                    skill, pipeline
                )
                if resolved_skill and not already_suggested(resolved_skill):
                    suggestions.append(resolved_msg)
                    record_suggestion(resolved_skill)
            elif message and not already_suggested(skill):
                suggestions.append(message)
                record_suggestion(skill)
            break  # first match wins

    if suggestions:
        print("\n\n".join(suggestions))


if __name__ == "__main__":
    main()
