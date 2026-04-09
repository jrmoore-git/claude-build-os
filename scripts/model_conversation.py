#!/usr/bin/env python3
"""
Persistent multi-model conversation manager with automatic context compression.

Maintains named conversation threads with multiple models. Each topic gets its
own isolated state. Keeps last N turns verbatim; compresses older turns into a
rolling summary. State persists across sessions.

Usage:
  mc = scripts/model_conversation.py

  mc init <topic> "System prompt"          # start a new conversation
  mc ask <topic> "Your question"           # send to all 3 models
  mc ask <topic> --model gpt4o "Follow-up" # send to one model
  mc inject <topic> <model> <user_file> <assistant_file>  # seed context
  mc list                                  # show all conversations
  mc history <topic>                       # show one conversation's state
  mc reset <topic>                         # delete one conversation
  mc reset --all                           # delete everything
  mc export <topic>                        # dump full state to stdout
"""
import urllib.request
import json
import sys
import os
import threading
import argparse
from pathlib import Path

# --- Configuration ---

STATE_ROOT = Path.home() / ".build-os" / "model_conversations"

LITELLM_URL = "http://localhost:4000/chat/completions"


def _load_litellm_key():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("LITELLM_MASTER_KEY="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("LITELLM_MASTER_KEY", "")


LITELLM_KEY = _load_litellm_key()

# Configure your models here. Keys are short aliases, values are model IDs
# as recognized by your LiteLLM proxy (or OpenAI-compatible API).
MODELS = {
    "gpt4o": "gpt-4o",
    "gemini": "gemini-2.5-pro",
    "claude": "claude-sonnet-4-20250514",
}

# --- Compression tuning ---
KEEP_RECENT_TURNS = 3
COMPRESS_MAX_WORDS = 1200
COMPRESS_MAX_TOKENS = 2500
COMPRESS_INPUT_CHARS_PER_MSG = 6000


# --- State management (per-topic) ---


def _topic_dir(topic):
    """Sanitize topic name and return its state directory."""
    safe = topic.lower().replace(" ", "-").replace("/", "-")
    return STATE_ROOT / safe


def _state_file(topic):
    return _topic_dir(topic) / "state.json"


def load_state(topic):
    sf = _state_file(topic)
    if sf.exists():
        return json.loads(sf.read_text())
    return {}


def save_state(topic, state):
    td = _topic_dir(topic)
    td.mkdir(parents=True, exist_ok=True)
    _state_file(topic).write_text(json.dumps(state, indent=2))


def list_topics():
    """Return list of (topic_name, state_file_path) for all conversations."""
    if not STATE_ROOT.exists():
        return []
    topics = []
    for d in sorted(STATE_ROOT.iterdir()):
        sf = d / "state.json"
        if d.is_dir() and sf.exists():
            topics.append((d.name, sf))
    return topics


# --- Compression ---


def get_turn_pairs(messages):
    pairs = []
    i = 0
    while i < len(messages):
        if messages[i]["role"] == "user":
            user_msg = messages[i]
            asst_msg = None
            if i + 1 < len(messages) and messages[i + 1]["role"] == "assistant":
                asst_msg = messages[i + 1]
            if asst_msg:
                pairs.append((user_msg, asst_msg))
                i += 2
            else:
                i += 1
        else:
            i += 1
    return pairs


def compress_turns(turns_to_compress, model_name):
    conversation_text = ""
    for user_msg, asst_msg in turns_to_compress:
        conversation_text += f"USER: {user_msg['content'][:COMPRESS_INPUT_CHARS_PER_MSG]}\n\n"
        conversation_text += f"ASSISTANT: {asst_msg['content'][:COMPRESS_INPUT_CHARS_PER_MSG]}\n\n---\n\n"

    prompt = f"""Compress this conversation into a concise summary (max {COMPRESS_MAX_WORDS} words). Preserve:
- All decisions made and their rationale
- All positions taken (agreements, disagreements, verdicts)
- Key technical details (artifact schemas, trigger criteria, enforcement mechanisms)
- All named proposals, skills, or concepts discussed
- Any open questions or unresolved disagreements
- Specific names, numbers, and identifiers

Do NOT preserve:
- Verbose explanations or reasoning chains
- Repeated points
- Pleasantries or meta-commentary

Output ONLY the summary, no preamble.

CONVERSATION:
{conversation_text}"""

    payload = json.dumps({
        "model": MODELS.get(model_name, list(MODELS.values())[0]),
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": COMPRESS_MAX_TOKENS,
        "temperature": 0.1,
    }).encode()

    req = urllib.request.Request(
        LITELLM_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LITELLM_KEY}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.load(resp)
            summary = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("total_tokens", "?")
            print(
                f"    Compressed {len(turns_to_compress)} turns -> {len(summary)} chars ({tokens} tokens)",
                file=sys.stderr,
            )
            return summary
    except Exception as e:
        print(f"    Compression API failed ({e}), using truncation fallback", file=sys.stderr)
        lines = []
        for user_msg, asst_msg in turns_to_compress:
            lines.append(f"Q: {user_msg['content'][:500]}")
            lines.append(f"A: {asst_msg['content'][:1000]}")
        return "PRIOR CONTEXT (truncated):\n" + "\n".join(lines)


def maybe_compress(state, model_name):
    messages = state[model_name]["messages"]

    system_msg = messages[0] if messages and messages[0]["role"] == "system" else None
    existing_summary = None
    summary_idx = None
    for i, m in enumerate(messages):
        if m["role"] == "system" and m.get("_type") == "compressed_summary":
            existing_summary = m
            summary_idx = i
            break

    start_idx = (summary_idx + 1) if summary_idx is not None else 1
    conv_messages = messages[start_idx:]
    pairs = get_turn_pairs(conv_messages)

    if len(pairs) <= KEEP_RECENT_TURNS:
        return

    to_compress = pairs[:-KEEP_RECENT_TURNS]
    to_keep = pairs[-KEEP_RECENT_TURNS:]

    print(
        f"  {model_name}: compressing {len(to_compress)} old turns, keeping {len(to_keep)} recent",
        file=sys.stderr,
    )

    compress_input = []
    if existing_summary:
        compress_input.append(
            (
                {"content": "[Prior compressed context]", "role": "user"},
                {"content": existing_summary["content"], "role": "assistant"},
            )
        )
    compress_input.extend(to_compress)

    new_summary = compress_turns(compress_input, model_name)

    new_messages = [system_msg] if system_msg else []
    new_messages.append(
        {
            "role": "system",
            "content": f"CONVERSATION HISTORY (compressed):\n{new_summary}",
            "_type": "compressed_summary",
        }
    )
    for user_msg, asst_msg in to_keep:
        new_messages.append(user_msg)
        new_messages.append(asst_msg)

    old_chars = sum(len(m.get("content", "")) for m in messages)
    new_chars = sum(len(m.get("content", "")) for m in new_messages)
    pct = 100 - int(new_chars / max(old_chars, 1) * 100)
    print(f"    {model_name}: {old_chars} -> {new_chars} chars ({pct}% reduction)", file=sys.stderr)

    state[model_name]["messages"] = new_messages


# --- Model calling ---


def call_model(name, model_id, messages, results):
    clean_messages = [{k: v for k, v in m.items() if not k.startswith("_")} for m in messages]

    try:
        payload = json.dumps({
            "model": model_id,
            "messages": clean_messages,
            "max_tokens": 3000,
            "temperature": 0.3,
        }).encode()
        req = urllib.request.Request(
            LITELLM_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LITELLM_KEY}",
            },
        )
        print(f"  Calling {name}...", file=sys.stderr)
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.load(resp)
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            results[name] = {
                "content": content,
                "tokens": usage.get("total_tokens", "?"),
                "prompt_tokens": usage.get("prompt_tokens", "?"),
            }
            print(
                f"  {name}: {len(content)} chars, {usage.get('prompt_tokens','?')} prompt + {usage.get('total_tokens','?')} total tokens",
                file=sys.stderr,
            )
    except Exception as e:
        results[name] = {"content": f"ERROR: {e}", "tokens": 0, "prompt_tokens": 0}
        print(f"  {name} FAILED: {e}", file=sys.stderr)


# --- Commands ---


def cmd_init(args):
    topic = args.topic
    if _state_file(topic).exists():
        print(f"Conversation '{topic}' already exists. Use 'reset {topic}' first.", file=sys.stderr)
        sys.exit(1)
    state = {}
    system_msg = {"role": "system", "content": args.system_prompt}
    for name in MODELS:
        state[name] = {"messages": [system_msg]}
    save_state(topic, state)
    print(f"Created conversation '{topic}' for {list(MODELS.keys())}")
    print(f"State: {_state_file(topic)}")


def cmd_ask(args):
    topic = args.topic
    state = load_state(topic)
    if not state:
        print(f"No conversation '{topic}'. Run 'init {topic}' first.", file=sys.stderr)
        sys.exit(1)

    targets = [args.model] if args.model else list(MODELS.keys())

    for name in targets:
        maybe_compress(state, name)
    save_state(topic, state)

    results = {}
    threads = [
        threading.Thread(
            target=call_model,
            args=(
                name,
                MODELS[name],
                state[name]["messages"] + [{"role": "user", "content": args.message}],
                results,
            ),
        )
        for name in targets
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=180)

    for name in targets:
        if name in results and not results[name]["content"].startswith("ERROR"):
            state[name]["messages"].append({"role": "user", "content": args.message})
            state[name]["messages"].append({"role": "assistant", "content": results[name]["content"]})
            outfile = f"/tmp/conv_{topic}_{name}_latest.md"
            with open(outfile, "w") as f:
                f.write(results[name]["content"])

    save_state(topic, state)

    print(f"\nResponses ({topic}):", file=sys.stderr)
    for name in targets:
        r = results.get(name, {})
        ok = "OK" if not r.get("content", "").startswith("ERROR") else "FAILED"
        print(
            f"  {name}: {ok} (prompt: {r.get('prompt_tokens','?')}, total: {r.get('tokens','?')}) -> /tmp/conv_{topic}_{name}_latest.md",
            file=sys.stderr,
        )


def cmd_list(args):
    topics = list_topics()
    if not topics:
        print("No conversations.")
        return
    print(f"{'Topic':<30} {'Models':>8} {'Turns':>6} {'Chars':>10} {'Status':<12}")
    print("-" * 70)
    for topic_name, sf in topics:
        state = json.loads(sf.read_text())
        total_turns = 0
        total_chars = 0
        compressed = False
        for model_data in state.values():
            msgs = model_data.get("messages", [])
            total_turns += len([m for m in msgs if m["role"] == "assistant"])
            total_chars += sum(len(m.get("content", "")) for m in msgs)
            if any(m.get("_type") == "compressed_summary" for m in msgs):
                compressed = True
        status = "[compressed]" if compressed else ""
        print(f"{topic_name:<30} {len(state):>8} {total_turns:>6} {total_chars:>10,} {status:<12}")


def cmd_history(args):
    topic = args.topic
    state = load_state(topic)
    if not state:
        print(f"No conversation '{topic}'.")
        return
    print(f"Conversation: {topic}")
    print(f"State: {_state_file(topic)}")
    print()
    for name, data in state.items():
        msgs = data["messages"]
        turns = len([m for m in msgs if m["role"] == "assistant"])
        chars = sum(len(m.get("content", "")) for m in msgs)
        has_summary = any(m.get("_type") == "compressed_summary" for m in msgs)
        tag = " [compressed]" if has_summary else ""
        print(f"  {name}: {turns} turns, {chars:,} chars{tag}")


def cmd_inject(args):
    topic = args.topic
    state = load_state(topic)
    if not state:
        print(f"No conversation '{topic}'. Run 'init {topic}' first.", file=sys.stderr)
        sys.exit(1)
    with open(args.user_file) as f:
        user_msg = f.read()
    with open(args.assistant_file) as f:
        asst_msg = f.read()
    state[args.model]["messages"].append({"role": "user", "content": user_msg})
    state[args.model]["messages"].append({"role": "assistant", "content": asst_msg})
    save_state(topic, state)
    print(f"Injected turn into '{topic}' for {args.model}: {len(user_msg):,} + {len(asst_msg):,} chars")


def cmd_reset(args):
    if args.all:
        import shutil
        if STATE_ROOT.exists():
            shutil.rmtree(STATE_ROOT)
        print("All conversations deleted.")
        return
    topic = args.topic
    if not topic:
        print("Specify a topic or use --all.", file=sys.stderr)
        sys.exit(1)
    td = _topic_dir(topic)
    if td.exists():
        import shutil
        shutil.rmtree(td)
        print(f"Conversation '{topic}' deleted.")
    else:
        print(f"No conversation '{topic}'.")


def cmd_export(args):
    topic = args.topic
    state = load_state(topic)
    if not state:
        print(f"No conversation '{topic}'.", file=sys.stderr)
        sys.exit(1)
    json.dump(state, sys.stdout, indent=2)


# --- CLI ---

parser = argparse.ArgumentParser(
    description="Multi-model conversation manager",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
sub = parser.add_subparsers(dest="cmd")

p_init = sub.add_parser("init", help="Start a new named conversation")
p_init.add_argument("topic", help="Conversation name (e.g., 'architecture-comparison')")
p_init.add_argument("system_prompt", help="System prompt for all models")

p_ask = sub.add_parser("ask", help="Send message to models")
p_ask.add_argument("topic", help="Conversation name")
p_ask.add_argument("message", help="Your message")
p_ask.add_argument("--model", choices=list(MODELS.keys()), help="Target one model")

sub.add_parser("list", help="Show all conversations")

p_hist = sub.add_parser("history", help="Show one conversation's state")
p_hist.add_argument("topic")

p_inject = sub.add_parser("inject", help="Inject prior exchange into a conversation")
p_inject.add_argument("topic")
p_inject.add_argument("model", choices=list(MODELS.keys()))
p_inject.add_argument("user_file")
p_inject.add_argument("assistant_file")

p_reset = sub.add_parser("reset", help="Delete a conversation (or --all)")
p_reset.add_argument("topic", nargs="?", help="Conversation to delete")
p_reset.add_argument("--all", action="store_true", help="Delete all conversations")

p_export = sub.add_parser("export", help="Dump conversation state to stdout")
p_export.add_argument("topic")

args = parser.parse_args()
cmds = {
    "init": cmd_init,
    "ask": cmd_ask,
    "list": cmd_list,
    "history": cmd_history,
    "inject": cmd_inject,
    "reset": cmd_reset,
    "export": cmd_export,
}
if args.cmd in cmds:
    cmds[args.cmd](args)
else:
    parser.print_help()
