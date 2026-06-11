"""
Episode 6 — Show RAG Failures
================================
This file uses the SAME paragraph-based chunking from Episode 5.
Same documents, same embedding model, same retrieval. Two new questions
that expose failures at two different layers.

It demonstrates:
  - Failure 1: Chunks too small (home office question) — CHUNKING layer
  - Failure 2: Ambiguous match (90-day rule question) — RETRIEVAL layer

The model isn't hallucinating. The retrieval is handing it
incomplete or wrong evidence.

AWS Services used:
  - Amazon Bedrock (Titan Embeddings V2, Claude Haiku 4.5)
"""

import os
import json
import numpy as np
import boto3

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

# Same documents as Episode 5
DOCS_FOLDER = os.path.join(os.path.dirname(__file__), "..", "ep05-rag-pipeline", "documents")

# Cache directory — stores chunks + embeddings so we don't re-embed every run
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
CHUNKS_CACHE = os.path.join(CACHE_DIR, "paragraph_chunks.json")
EMBEDDINGS_CACHE = os.path.join(CACHE_DIR, "paragraph_embeddings.npy")

# Bedrock model IDs (same as ep5)
EMBED_MODEL = "amazon.titan-embed-text-v2:0"
GENERATION_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-east-1"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)


# ─────────────────────────────────────────────────────────────
# STEP 1: CHUNK (Same paragraph-based approach as Episode 5)
# ─────────────────────────────────────────────────────────────
# This is the SAME chunking from ep5 — split on double-newlines.
# We're deliberately using the naive approach to show where it
# breaks. The fix comes in 02_fix_heading_chunking.py.
# ─────────────────────────────────────────────────────────────

def chunk_docs_paragraph(folder: str) -> list[dict]:
    """
    Paragraph-based chunking (Episode 5 approach).
    Split on double-newlines with 1 paragraph of overlap.
    """
    chunks = []

    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".md") or filename == "README.md":
            continue

        with open(os.path.join(folder, filename), "r") as f:
            text = f.read()

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        for i in range(len(paragraphs)):
            start = max(0, i - 1)
            chunk_text = "\n\n".join(paragraphs[start : i + 1])
            chunks.append({"text": chunk_text, "source": filename})

    return chunks


# ─────────────────────────────────────────────────────────────
# STEP 2: EMBED
# ─────────────────────────────────────────────────────────────

def embed_text(text: str) -> list[float]:
    """Call Titan Embeddings V2 to get a 1024-dim vector."""
    response = bedrock.invoke_model(
        modelId=EMBED_MODEL,
        body=json.dumps({"inputText": text}),
    )
    result = json.loads(response["body"].read())
    return result["embedding"]


def embed_all(chunks: list[dict]) -> np.ndarray:
    """Embed every chunk. Returns a matrix of shape (num_chunks, 1024)."""
    vectors = []
    for i, chunk in enumerate(chunks):
        vectors.append(embed_text(chunk["text"]))
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(chunks)} embedded...")
    print(f"  Done — {len(chunks)} chunks embedded.\n")
    return np.array(vectors)


# ─────────────────────────────────────────────────────────────
# STEP 3: RETRIEVE (Semantic search — cosine similarity)
# ─────────────────────────────────────────────────────────────

def retrieve(question: str, chunks: list[dict], embeddings: np.ndarray, top_k: int = 3) -> list[dict]:
    """Find the top-K most relevant chunks via cosine similarity."""
    q_vec = np.array(embed_text(question))

    scores = []
    for i in range(len(chunks)):
        score = np.dot(q_vec, embeddings[i]) / (
            np.linalg.norm(q_vec) * np.linalg.norm(embeddings[i])
        )
        scores.append(score)

    top_indices = np.argsort(scores)[::-1][:top_k]

    return [
        {"text": chunks[idx]["text"], "source": chunks[idx]["source"], "score": float(scores[idx])}
        for idx in top_indices
    ]


# ─────────────────────────────────────────────────────────────
# STEP 4: GENERATE (Claude answers from retrieved context)
# ─────────────────────────────────────────────────────────────

def generate_answer(question: str, retrieved: list[dict]) -> str:
    """Pass retrieved chunks + question to Claude. Only use provided context."""
    context = "\n\n---\n\n".join(
        f"[Source: {r['source']}]\n{r['text']}" for r in retrieved
    )

    prompt = (
        f"You are answering questions about PineRidge Solutions' company policies. "
        f"Use ONLY the context below. If the answer isn't there, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )

    response = bedrock.converse(
        modelId=GENERATION_MODEL,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
    )
    return response["output"]["message"]["content"][0]["text"]


# ─────────────────────────────────────────────────────────────
# RUN: Show both failures
# ─────────────────────────────────────────────────────────────

def save_cache(chunks: list[dict], embeddings: np.ndarray):
    """Save chunks and embeddings to disk for subsequent runs."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CHUNKS_CACHE, "w") as f:
        json.dump(chunks, f)
    np.save(EMBEDDINGS_CACHE, embeddings)
    print(f"  Cache saved.\n")


def load_cache():
    """Load cached chunks and embeddings if they exist."""
    if os.path.exists(CHUNKS_CACHE) and os.path.exists(EMBEDDINGS_CACHE):
        with open(CHUNKS_CACHE, "r") as f:
            chunks = json.load(f)
        embeddings = np.load(EMBEDDINGS_CACHE)
        return chunks, embeddings
    return None


if __name__ == "__main__":

    # --- Load from cache or build fresh ---
    cached = load_cache()
    if cached:
        chunks, embeddings = cached
        print(f"Loaded {len(chunks)} chunks from cache.\n")
    else:
        print("Chunking documents (paragraph-based)...")
        chunks = chunk_docs_paragraph(DOCS_FOLDER)
        print(f"  {len(chunks)} chunks from 6 documents.\n")

        print("Embedding chunks...")
        embeddings = embed_all(chunks)
        save_cache(chunks, embeddings)

    # ─────────────────────────────────────────────────────────
    # FAILURE 1: Chunks too small (CHUNKING layer)
    # Uncomment this question, comment out failure 2 below.
    # ─────────────────────────────────────────────────────────

    question = "Can I expense my home office setup during onboarding?"

    # ─────────────────────────────────────────────────────────
    # FAILURE 2: Ambiguous match (RETRIEVAL layer)
    # Uncomment this question, comment out failure 1 above.
    # ─────────────────────────────────────────────────────────

    # question = "What's the 90-day rule?"

    # ─────────────────────────────────────────────────────────

    print(f"Question: {question}\n")

    results = retrieve(question, chunks, embeddings, top_k=5)

    print("Retrieved chunks:")
    for i, r in enumerate(results):
        preview = r["text"][:100].replace("\n", " ")
        print(f"  [{i+1}] ({r['score']:.3f}) {r['source']}")
        print(f"      {preview}...")
    print()

    answer = generate_answer(question, results)
    print(f"Answer: {answer}")
