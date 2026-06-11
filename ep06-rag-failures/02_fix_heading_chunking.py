"""
Episode 6 — Fix 1: Heading-Based Chunking
============================================
The paragraph chunking from Episode 5 splits sections too short.
But these documents have structure — markdown headings. What if
we split on headings instead of paragraphs?

Each heading + everything under it becomes one chunk.
"5.3 Home Office Setup" plus all the bullet points below it = one chunk.
Related information stays together.

This fixes the CHUNKING layer.

AWS Services used:
  - Amazon Bedrock (Titan Embeddings V2, Claude Haiku 4.5)
"""

import os
import json
import re
import numpy as np
import boto3

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

DOCS_FOLDER = os.path.join(os.path.dirname(__file__), "..", "ep05-rag-pipeline", "documents")

# Cache directory
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
HEADING_CHUNKS_CACHE = os.path.join(CACHE_DIR, "heading_chunks.json")
HEADING_EMBEDDINGS_CACHE = os.path.join(CACHE_DIR, "heading_embeddings.npy")

EMBED_MODEL = "amazon.titan-embed-text-v2:0"
GENERATION_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-east-1"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)


# ─────────────────────────────────────────────────────────────
# THE FIX: Heading-based chunking
# ─────────────────────────────────────────────────────────────
# Instead of splitting on blank lines (paragraphs), we split
# on markdown headings. Each heading plus everything below it
# (until the next heading of the same or higher level) becomes
# one chunk.
#
# Why this works for structured documents:
#   - Policy docs have clear section headings
#   - Related bullet points stay together
#   - The full answer lives under one heading
#
# When this DOESN'T work:
#   - Documents without headings (flowing prose)
#   - Very long sections (you're back to "too much context")
#   - The fix isn't universal — it matches this data shape
# ─────────────────────────────────────────────────────────────

def chunk_docs_heading(folder: str) -> list[dict]:
    """
    Heading-based chunking: split documents on markdown headings.

    Each chunk = one heading + all content under it until the next
    heading at the same or higher level (##, ###, etc.).

    For the episode, we split on level-3 headings (###) which
    represent individual policy subsections like "5.3 Home Office Setup".
    Level-2 headings (##) are section dividers that group subsections.
    """
    chunks = []

    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".md") or filename == "README.md":
            continue

        with open(os.path.join(folder, filename), "r") as f:
            text = f.read()

        # Split on ### headings (subsection level)
        # Keep the heading with its content
        sections = re.split(r'(?=^### )', text, flags=re.MULTILINE)

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Skip very short chunks (just a heading with no content)
            if len(section) < 50:
                continue

            chunks.append({"text": section, "source": filename})

    return chunks


# ─────────────────────────────────────────────────────────────
# EMBED + RETRIEVE + GENERATE (same as before)
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
    """Embed every chunk."""
    vectors = []
    for i, chunk in enumerate(chunks):
        vectors.append(embed_text(chunk["text"]))
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(chunks)} embedded...")
    print(f"  Done — {len(chunks)} chunks embedded.\n")
    return np.array(vectors)


def retrieve(question: str, chunks: list[dict], embeddings: np.ndarray, top_k: int = 3) -> list[dict]:
    """Semantic search via cosine similarity."""
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


def generate_answer(question: str, retrieved: list[dict]) -> str:
    """Pass retrieved chunks + question to Claude."""
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


def save_cache(chunks: list[dict], embeddings: np.ndarray):
    """Save heading-based chunks and embeddings to disk."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(HEADING_CHUNKS_CACHE, "w") as f:
        json.dump(chunks, f)
    np.save(HEADING_EMBEDDINGS_CACHE, embeddings)
    print(f"  Cache saved.\n")


def load_cache():
    """Load cached heading chunks and embeddings if they exist."""
    if os.path.exists(HEADING_CHUNKS_CACHE) and os.path.exists(HEADING_EMBEDDINGS_CACHE):
        with open(HEADING_CHUNKS_CACHE, "r") as f:
            chunks = json.load(f)
        embeddings = np.load(HEADING_EMBEDDINGS_CACHE)
        return chunks, embeddings
    return None


# ─────────────────────────────────────────────────────────────
# RUN: Same question, better chunking
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # --- Load from cache or build fresh ---
    cached = load_cache()
    if cached:
        chunks, embeddings = cached
        print(f"Loaded {len(chunks)} heading-based chunks from cache.\n")
    else:
        print("Chunking documents (heading-based)...")
        chunks = chunk_docs_heading(DOCS_FOLDER)
        print(f"  {len(chunks)} chunks from 6 documents.\n")

        print("Embedding chunks...")
        embeddings = embed_all(chunks)
        save_cache(chunks, embeddings)

    # Same question that failed with paragraph chunking
    question = "Can I expense my home office setup during onboarding?"

    print(f"Question: {question}\n")

    results = retrieve(question, chunks, embeddings)

    print("Retrieved chunks:")
    for i, r in enumerate(results):
        preview = r["text"][:150].replace("\n", " ")
        print(f"  [{i+1}] ({r['score']:.3f}) {r['source']}")
        print(f"      {preview}...")
    print()

    answer = generate_answer(question, results)
    print(f"Answer: {answer}")
