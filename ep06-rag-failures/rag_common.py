"""
Shared RAG pipeline plumbing — Episode 6
=========================================
The parts that DON'T change between the failure and the fix live here:
embedding, retrieval, generation, caching, and pretty-printing.

Each demo file (chunking_failure.py, chunking_fix.py, retrieval_failure.py,
retrieval_fix.py) imports from this module and only defines the ONE thing
that differs — how it chunks, or whether it filters. That way, when you open
the fix file on camera, the difference from the failure file is the whole
story, not buried in boilerplate.

This is the same four-step pipeline from Episode 5:
  CHUNK -> EMBED -> RETRIEVE -> GENERATE

AWS services used:
  - Amazon Bedrock (Titan Text Embeddings V2 for vectors, Claude Haiku for generation)
"""

import os
import json
import numpy as np
import boto3

# ─────────────────────────────────────────────────────────────
# CONFIGURATION (identical to Episode 5)
# ─────────────────────────────────────────────────────────────

# Same six onboarding documents as Episode 5. Same code, same data.
DOCS_FOLDER = os.path.join(
    os.path.dirname(__file__), "..", "ep05-rag-pipeline", "documents"
)

# Each demo caches its chunks + embeddings here so we don't re-embed
# every run. Cache files are named per strategy by the caller.
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")

# Bedrock model IDs.
EMBED_MODEL = "amazon.titan-embed-text-v2:0"        # text -> 1024-d vector
GENERATION_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"  # grounded answers
REGION = "us-east-1"

# One Bedrock client, shared by every demo that imports this module.
bedrock = boto3.client("bedrock-runtime", region_name=REGION)


# ============================================================
# STEP 2: EMBED
# ============================================================
# Convert text into a 1024-dimensional Titan vector. We use the
# SAME model for chunks and questions so they share one vector
# space and cosine similarity is meaningful.
# ============================================================

def embed_text(text: str) -> list[float]:
    """Embed a single piece of text with Titan Text Embeddings V2."""
    response = bedrock.invoke_model(
        modelId=EMBED_MODEL,
        body=json.dumps({"inputText": text}),
    )
    return json.loads(response["body"].read())["embedding"]


def embed_all(chunks: list[dict]) -> np.ndarray:
    """Embed every chunk. One API call per chunk — the slow, paid step."""
    vectors = []
    for i, chunk in enumerate(chunks):
        vectors.append(embed_text(chunk["text"]))
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(chunks)} embedded...")
    print(f"  Done — {len(chunks)} chunks embedded.\n")
    return np.array(vectors)


# ============================================================
# STEP 3: RETRIEVE  (with optional metadata PRE-FILTER)
# ============================================================
# Embed the question, then rank chunks by cosine similarity.
#
# If source_label is given, we FIRST narrow to chunks from that
# source, THEN score only those. That is the retrieval fix:
# narrow the search space before the similarity search runs.
# Leave source_label=None and it scores everything (the failure).
# ============================================================

def retrieve(
    question: str,
    chunks: list[dict],
    embeddings: np.ndarray,
    top_k: int = 5,
    source_label: str | None = None,
) -> list[dict]:
    """Semantic search, optionally restricted to one source via metadata."""
    q_vec = np.array(embed_text(question))

    # ── PRE-FILTER: shrink the candidate set BEFORE scoring ──
    if source_label:
        candidate_idx = [
            i for i, c in enumerate(chunks) if c.get("source_label") == source_label
        ]
    else:
        candidate_idx = list(range(len(chunks)))

    scored = []
    for i in candidate_idx:
        score = np.dot(q_vec, embeddings[i]) / (
            np.linalg.norm(q_vec) * np.linalg.norm(embeddings[i])
        )
        scored.append((i, float(score)))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [
        {
            "text": chunks[i]["text"],
            "source": chunks[i]["source"],
            "source_label": chunks[i].get("source_label"),
            "score": s,
        }
        for i, s in scored[:top_k]
    ]


# ============================================================
# STEP 4: GENERATE
# ============================================================
# Hand the retrieved chunks to Claude and ask it to answer using
# ONLY that context. If the evidence is incomplete, a well-behaved
# model says so instead of inventing the missing numbers.
# ============================================================

def generate_answer(question: str, retrieved: list[dict]) -> str:
    """Ask Claude to answer strictly from the retrieved chunks."""
    context = "\n\n---\n\n".join(
        f"[Source: {r['source']}]\n{r['text']}" for r in retrieved
    )
    prompt = (
        "You are answering questions about PineRidge Solutions' company policies. "
        "Use ONLY the context below. If the answer isn't there, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )
    response = bedrock.converse(
        modelId=GENERATION_MODEL,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
    )
    return response["output"]["message"]["content"][0]["text"]


# ============================================================
# CACHE — chunk once, embed once, reuse
# ============================================================

def _paths(prefix: str) -> tuple[str, str]:
    return (
        os.path.join(CACHE_DIR, f"{prefix}_chunks.json"),
        os.path.join(CACHE_DIR, f"{prefix}_embeddings.npy"),
    )


def load_or_build(prefix: str, build_chunks) -> tuple[list[dict], np.ndarray]:
    """
    Load this strategy's cache, or run build_chunks() + embed and save it.

    prefix       — cache filename prefix (e.g. "paragraph", "heading", "metadata")
    build_chunks — a zero-argument function returning the chunk list
    """
    chunks_path, embed_path = _paths(prefix)

    if os.path.exists(chunks_path) and os.path.exists(embed_path):
        with open(chunks_path, "r") as f:
            chunks = json.load(f)
        embeddings = np.load(embed_path)
        print(f"Loaded from cache: {len(chunks)} chunks ('{prefix}')\n")
        return chunks, embeddings

    print("STEP 1: Chunking documents...")
    chunks = build_chunks()
    print(f"  {len(chunks)} chunks from 6 documents.\n")

    print("STEP 2: Embedding chunks...")
    embeddings = embed_all(chunks)

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(chunks_path, "w") as f:
        json.dump(chunks, f)
    np.save(embed_path, embeddings)
    print("  Cache saved.\n")
    return chunks, embeddings


# ============================================================
# PRETTY-PRINT — show enough of each chunk to SEE its shape
# ============================================================
# We print the first few lines of each retrieved chunk, with the
# original line breaks kept, so on screen you can tell whether a
# chunk is a whole section (heading + bullets) or just a fragment.
# ============================================================

def preview_chunk(text: str, max_lines: int = 6, max_chars: int = 400) -> str:
    """Return the first few non-empty lines of a chunk, indented for display."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    shown = lines[:max_lines]
    body = "\n".join("        " + ln for ln in shown)

    # Note if we clipped the chunk so viewers know there's more.
    clipped = len(lines) > max_lines or len(text) > max_chars
    if len(body) > max_chars + 8 * len(shown):
        body = body[: max_chars + 8 * len(shown)]
        clipped = True
    if clipped:
        body += "\n        ..."
    return body


def print_results(results: list[dict], show_label_only: bool = False) -> None:
    """Print retrieved chunks with score, source, and a multi-line preview."""
    print("  Retrieved chunks (look at what the model was handed):")
    for i, r in enumerate(results):
        src = r["source_label"] if show_label_only else r["source"]
        print(f"\n    [{i+1}] score={r['score']:.3f}  source={src}")
        print(preview_chunk(r["text"]))
    print()


def run_query(
    question: str,
    chunks: list[dict],
    embeddings: np.ndarray,
    source_label: str | None = None,
    show_label_only: bool = False,
) -> None:
    """Retrieve + generate for one question and print the whole thing."""
    print(f"─── Question: {question}\n")
    results = retrieve(question, chunks, embeddings, source_label=source_label)
    print_results(results, show_label_only=show_label_only)
    answer = generate_answer(question, results)
    print(f"  Answer:\n  {answer}\n")
