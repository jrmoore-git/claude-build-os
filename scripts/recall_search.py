#!/opt/homebrew/bin/python3.11
"""BM25 + semantic recall search across governance files. Pure stdlib, no pip."""
import argparse, json, math, re, sqlite3, sys, urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {"lessons": ROOT / "tasks/lessons.md", "decisions": ROOT / "tasks/decisions.md",
           "sessions": ROOT / "tasks/session-log.md", "current": ROOT / "docs/current-state.md"}

def tokenize(text): return re.findall(r"[a-z0-9_]+", text.lower())

def parse_lessons(text, tags_only=False):
    docs = []
    for m in re.finditer(r"^\| (L\d+) \| .+\|$", text, re.M):
        row = m.group(0)
        if tags_only: row = row.split("|")[-2].strip() if row.count("|") >= 7 else ""
        docs.append(("tasks/lessons.md", text[:m.start()].count("\n") + 1, m.group(1), row))
    return docs

def parse_decisions(text, tags_only=False):
    return [("tasks/decisions.md", text[:m.start()].count("\n") + 1, m.group(1),
             "" if tags_only else m.group(0))
            for m in re.finditer(r"^### (D\d+):.+?(?=\n### D\d+:|\Z)", text, re.M | re.S)]

def parse_sessions(text, tags_only=False):
    if tags_only: return []
    docs, offset = [], 0
    for entry in text.split("\n---\n"):
        label = re.search(r"^## (.+)", entry, re.M)
        docs.append(("tasks/session-log.md", text[:offset].count("\n") + 1 if offset else 1,
                     label.group(1)[:40] if label else "session", entry))
        offset += len(entry) + 5
    return docs

def parse_current(text, tags_only=False):
    return [] if tags_only else [("docs/current-state.md", 1, "current-state", text)]

PARSERS = {"lessons": parse_lessons, "decisions": parse_decisions,
           "sessions": parse_sessions, "current": parse_current}

def bm25(query_tokens, docs, k1=1.5, b=0.75):
    N = len(docs)
    if N == 0: return []
    doc_tokens = [tokenize(d[3]) for d in docs]
    avgdl = sum(len(t) for t in doc_tokens) / N
    df = Counter()
    for toks in doc_tokens:
        for t in set(toks): df[t] += 1
    scores = []
    for i, toks in enumerate(doc_tokens):
        tf, dl, score = Counter(toks), len(toks), 0.0
        for qt in query_tokens:
            if qt not in tf: continue
            idf = math.log((N - df[qt] + 0.5) / (df[qt] + 0.5) + 1)
            score += idf * tf[qt] * (k1 + 1) / (tf[qt] + k1 * (1 - b + b * dl / avgdl))
        if score > 0: scores.append((score, i))
    scores.sort(reverse=True)
    return scores

def semantic_search(query, file_filter=None, top_k=5, threshold=0.5):
    db_path = ROOT / "stores" / "context.db"
    if not db_path.exists():
        print("No embeddings DB found. Run: python3 scripts/embed_governance.py"); return
    body = json.dumps({"model": "nomic-embed-text", "prompt": query[:8000]}).encode()
    try:
        req = urllib.request.Request("http://localhost:11434/api/embeddings", data=body,
                                    headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            q_vec = json.loads(resp.read())["embedding"]
    except Exception as e:
        print(f"Ollama unavailable ({e}). Re-run without --semantic for BM25 results."); return
    conn = sqlite3.connect(str(db_path), timeout=5)
    conn.execute("PRAGMA busy_timeout = 5000")
    query_sql = "SELECT source_file, chunk_id, chunk_text, embedding FROM recall_embeddings"
    params = []
    if file_filter:
        placeholders = ",".join("?" * len(file_filter))
        query_sql += f" WHERE source_file IN ({placeholders})"
        params = list(file_filter)
    rows = conn.execute(query_sql, params).fetchall()
    conn.close()
    results = []
    for src, cid, text, emb_blob in rows:
        d_vec = json.loads(emb_blob)
        dot = sum(a * b for a, b in zip(q_vec, d_vec))
        mag_q = math.sqrt(sum(a * a for a in q_vec))
        mag_d = math.sqrt(sum(b * b for b in d_vec))
        sim = dot / (mag_q * mag_d) if mag_q and mag_d else 0.0
        if sim >= threshold:
            results.append((sim, src, cid, text))
    results.sort(reverse=True)
    if not results:
        print(f"No semantic matches found for: {query}"); sys.exit(0)
    for sim, src, cid, text in results[:top_k]:
        print(f"  {src}  [{cid}]  similarity={sim:.3f}")
        print(f"    {' '.join(text.split())[:120]}\n")

def main():
    p = argparse.ArgumentParser(description="BM25 + semantic search across governance files")
    p.add_argument("terms", nargs="+")
    p.add_argument("--tags", action="store_true", help="Search frontmatter tags only")
    p.add_argument("--semantic", action="store_true", help="Use Ollama semantic search")
    p.add_argument("--files", default="all", help="Comma-separated: lessons,decisions,sessions,current,all")
    p.add_argument("--json", action="store_true", help="Output results as JSON array")
    p.add_argument("--top-k", type=int, default=5, help="Max results to return")
    args = p.parse_args()
    if args.semantic:
        file_map = {"lessons": "tasks/lessons.md", "decisions": "tasks/decisions.md",
                    "sessions": "tasks/session-log.md", "current": "docs/current-state.md"}
        file_filter = None
        if "all" not in args.files:
            file_filter = [file_map[f] for f in args.files.split(",") if f in file_map]
        semantic_search(" ".join(args.terms), file_filter)
        return
    targets = list(PARSERS.keys()) if "all" in args.files else args.files.split(",")
    docs = []
    for t in targets:
        path = SOURCES.get(t)
        if path and path.exists(): docs.extend(PARSERS[t](path.read_text(), tags_only=args.tags))
    results = bm25(tokenize(" ".join(args.terms)), docs)[:args.top_k]
    if not results:
        if args.json:
            print("[]")
        else:
            print(f"No matches found for: {' '.join(args.terms)}")
        sys.exit(0)
    if args.json:
        out = []
        for score, i in results:
            src, line, label, text = docs[i]
            out.append({"source": src, "line": line, "id": label,
                         "score": round(score, 3), "text": " ".join(text.split())[:300]})
        print(json.dumps(out))
    else:
        for score, i in results:
            src, line, label, text = docs[i]
            print(f"  {src}:{line}  [{label}]  score={score:.3f}")
            print(f"    {' '.join(text.split())[:120]}\n")

if __name__ == "__main__":
    main()
