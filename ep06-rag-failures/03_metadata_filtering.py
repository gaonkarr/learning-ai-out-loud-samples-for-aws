"""
Episode 6 — Fix 2: Metadata Filtering
========================================
The "90-day rule" problem isn't about chunk size. It's about
disambiguation. Five chunks from five different documents all
score similarly because they all talk about a 90-day timeframe.
Semantic search alone can't tell them apart.

The fix: tag each chunk with its source document at ingestion time.
At query time, filter to the relevant source BEFORE searching.
Narrow first, search second.

This fixes the RETRIEVAL layer.

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
METADATA_CHUNKS_CACHE = os.path.join(CACHE_DIR, "metadata_chunks.json")
METADATA_EMBEDDINGS_CACHE = os.path.join(CACHE_DIR, "metadata_embeddings.npy")

EMBED_MODEL = "amazon.titan-embed-text-v2:0"
GENERATION_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-east-1"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)


# ─────────────────────────────────────────────────────────────
# CHUNKING: Heading-based (same as fix 1)
# ─────────────────────────────────────────────────────────────
# We use heading-based chunking here because it's the better
# baseline after the first fix. But the metadata filtering
# concept works with any chunking strategy.
# ─────────────────────────────────────────────────────────────

def chunk_docs_with_metadata(folder: str) -> list[dict]:
    """
    Heading-based chunking WITH metadata.

    Each chunk now carries:
      - text: the chunk content
      - source: which file it came from (e.g. "01-employee-handbook.md")
      - source_label: a human-readable label for display

    The source field is what we filter on at query time.
    """
    # Map filenames to readable labels
    source_labels = {
        "01-employee-handbook.md": "employee-handbook",
        "02-benefits-guide.md": "benefits-guide",
        "03-leave-policy.md": "leave-policy",
        "04-expense-and-travel-policy.md": "expense-policy",
        "05-engineering-onboarding.md": "engineering-onboarding",
        "06-it-security-policy.md": "it-security-policy",
    }

    chunks = []

    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".md") or filename == "README.md":
            continue

        with open(os.path.join(folder, filename), "r") as f:
            text = f.read()

        # Split on ### headings (subsection level)
        sections = re.split(r'(?=^### )', text, flags=re.MULTILINE)

        for section in sections:
            section = section.strip()
            if not section:
                continue
            if len(section) < 50:
                continue

            chunks.append({
                "text": section,
                "source": filename,
                "source_label": source_labels.get(filename, filename),
            })

    return chunks


# ─────────────────────────────────────────────────────────────
# EMBEDDING (same as before)
# ─────────────────────────────────────────────────────────────

def embed_text(text: str) -> list[float]:
    """Call Titan Embeddings V2."""
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


# ─────────────────────────────────────────────────────────────
# RETRIEVE: With optional metadata filter
# ─────────────────────────────────────────────────────────────
# The key change: filter chunks by source BEFORE computing
# similarity. This narrows the search space so the model only
# sees chunks from the relevant document.
#
# Without filter: search all chunks → ambiguous scores
# With filter: search only matching chunks → clear winner
# ─────────────────────────────────────────────────────────────

def retrieve_with_filter(
    question: str,
    chunks: list[dict],
    embeddings: np.ndarray,
    source_filter: str = None,
    top_k: int = 3,
) -> list[dict]:
    """
    Semantic search with optional metadata pre-filtering.

    If source_filter is provided, only chunks from that source
    are considered. This is the "narrow first, search second" pattern.
    """
    # Apply metadata filter if specified
    if source_filter:
        # Find indices of chunks that match the filter
        filtered_indices = [
            i for i, c in enumerate(chunks)
            if c["source_label"] == source_filter
        ]
    else:
        filtered_indices = list(range(len(chunks)))

    if not filtered_indices:
        return []

    # Embed the question
    q_vec = np.array(embed_text(question))

    # Score only the filtered chunks
    scored = []
    for idx in filtered_indices:
        score = np.dot(q_vec, embeddings[idx]) / (
            np.linalg.norm(q_vec) * np.linalg.norm(embeddings[idx])
        )
        scored.append((idx, float(score)))

    # Sort by score descending, take top K
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:top_k]

    return [
        {
            "text": chunks[idx]["text"],
            "source": chunks[idx]["source"],
            "source_label": chunks[idx]["source_label"],
            "score": score,
        }
        for idx, score in top
    ]


# ─────────────────────────────────────────────────────────────
# GENERATE (same as before)
# ─────────────────────────────────────────────────────────────

def generate_answer(question: str, retrieved: list[dict]) -> str:
    """Pass retrieved chunks + question to Claude."""
    context = "\n\n---\n\n".join(
        f"[Source: {r['source_label']}]\n{r['text']}" for r in retrieved
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
    """Save metadata chunks and embeddings to disk."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(METADATA_CHUNKS_CACHE, "w") as f:
        json.dump(chunks, f)
    np.save(METADATA_EMBEDDINGS_CACHE, embeddings)
    print(f"  Cache saved.\n")


def load_cache():
    """Load cached metadata chunks and embeddings if they exist."""
    if os.path.exists(METADATA_CHUNKS_CACHE) and os.path.exists(METADATA_EMBEDDINGS_CACHE):
        with open(METADATA_CHUNKS_CACHE, "r") as f:
            chunks = json.load(f)
        embeddings = np.load(METADATA_EMBEDDINGS_CACHE)
        return chunks, embeddings
    return None


# ─────────────────────────────────────────────────────────────
# RUN: Demonstrate metadata filtering
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # --- Load from cache or build fresh ---
    cached = load_cache()
    if cached:
        chunks, embeddings = cached
        print(f"Loaded {len(chunks)} chunks from cache.\n")
    else:
        print("Chunking documents (heading-based, with metadata)...")
        chunks = chunk_docs_with_metadata(DOCS_FOLDER)
        print(f"  {len(chunks)} chunks.\n")

        print("Embedding chunks...")
        embeddings = embed_all(chunks)
        save_cache(chunks, embeddings)

    question = "What's the 90-day rule?"

    # Filter to one source, then search.
    # Comment/uncomment to switch which source you filter to.    

    # No filter (shows the ambiguity problem)
    # source_filter = None

    # Filter to employee handbook
    # source_filter = "employee-handbook"

    # Filter to expense policy
    source_filter = "expense-policy"

    # ─────────────────────────────────────────────────────────

    filtered = [c for c in chunks if source_filter is None or c["source_label"] == source_filter]
    print(f"Question: {question}")
    print(f"Filter: {source_filter or 'None'} ({len(filtered)} chunks)")
    print()

    results = retrieve_with_filter(question, chunks, embeddings, source_filter=source_filter, top_k=3)

    print("Retrieved chunks:")
    for i, r in enumerate(results):
        preview = r["text"][:100].replace("\n", " ")
        print(f"  [{i+1}] ({r['score']:.3f}) {r['source_label']}")
        print(f"      {preview}...")
    print()

    answer = generate_answer(question, results)
    print(f"Answer: {answer}")
