"""
PineRidge RAG Demo — Episode 5
================================
A complete Retrieval-Augmented Generation (RAG) pipeline in one file.

RAG = Retrieval-Augmented Generation
Instead of asking an LLM to answer from memory (which can hallucinate),
we RETRIEVE relevant documents first, then GENERATE an answer grounded
in those documents.

Pipeline steps:
  1. CHUNK   — Split company docs into small, searchable pieces
  2. EMBED   — Convert each chunk into a numerical vector (embedding)
  3. RETRIEVE — Find the most relevant chunks for a given question
  4. GENERATE — Pass those chunks to an LLM to produce a grounded answer

AWS Services used:
  - Amazon Bedrock (Titan Embeddings V2 for vectors, Claude Haiku 4.5 for generation)
"""

import os
import json
import numpy as np
import boto3

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

# Path to the folder containing our 6 onboarding policy documents
DOCS_FOLDER = os.path.join(os.path.dirname(__file__), "documents")

# Local cache directory — stores chunks + embeddings so we don't
# have to re-embed every time we run the script
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
CHUNKS_CACHE = os.path.join(CACHE_DIR, "chunks.json")
EMBEDDINGS_CACHE = os.path.join(CACHE_DIR, "embeddings.npy")

# Bedrock model IDs
# Titan Embeddings: converts text → 1024-dimensional vector
EMBED_MODEL = "amazon.titan-embed-text-v2:0"
# Claude Haiku 4.5: fast, cheap LLM for generating answers
GENERATION_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# AWS region where Bedrock models are enabled
REGION = "us-east-1"

# Create a Bedrock client
# Requires AWS credentials configured (e.g. aws configure)
bedrock = boto3.client("bedrock-runtime", region_name=REGION)


# ============================================================
# STEP 1: CHUNK
# ============================================================
# WHY: LLMs have context limits, and embeddings work better on
# smaller, focused pieces of text. We split each document into
# paragraph-sized chunks so retrieval can find the most relevant
# snippet rather than returning an entire 10-page doc.
# ============================================================

def chunk_docs(folder: str) -> list[dict]:
    """
    Read all markdown policy documents and split them into chunks.
    Strategy: Split on double-newlines (paragraph boundaries).
    Each chunk includes the previous paragraph for overlap/context,
    so we don't lose meaning at paragraph boundaries.
    Returns a list of dicts: [{"text": "...", "source": "filename.md"}, ...]
    """
    chunks = []

    for filename in sorted(os.listdir(folder)):
        # Only process markdown files, skip README
        if not filename.endswith(".md") or filename == "README.md":
            continue

        with open(os.path.join(folder, filename), "r") as f:
            text = f.read()

        # Split document into paragraphs (separated by blank lines)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        for i in range(len(paragraphs)):
            # Include 1 paragraph of overlap for context continuity
            start = max(0, i - 1)
            chunk_text = "\n\n".join(paragraphs[start : i + 1])

            # Store the chunk text and which file it came from (for citations)
            chunks.append({"text": chunk_text, "source": filename})

    return chunks


# ============================================================
# STEP 2: EMBED
# ============================================================
# WHY: We can't do math on raw text. Embeddings convert text into
# numerical vectors where similar meanings are close together in
# vector space. This lets us find relevant chunks by measuring
# distance between a question vector and all chunk vectors.
#
# KEY INSIGHT: We use the SAME embedding model for both chunks
# and questions — this ensures they live in the same vector space.
# ============================================================

def embed_text(text: str) -> list[float]:
    """
    Call Amazon Titan Embeddings V2 via Bedrock to get a vector
    representation of a single piece of text.
    Returns a list of 1024 floats (the embedding vector).
    """
    response = bedrock.invoke_model( 
        modelId=EMBED_MODEL,
        body=json.dumps({"inputText": text}),
    )
    result = json.loads(response["body"].read())
    return result["embedding"]


def embed_all(chunks: list[dict]) -> np.ndarray:
    """
    Embed every chunk in our collection.
    This is the expensive step — one API call per chunk.
    Returns a NumPy matrix where each row is a chunk's embedding vector.
    Shape: (num_chunks, 1024)
    """
    vectors = []
    for i, chunk in enumerate(chunks):
        vectors.append(embed_text(chunk["text"]))
        # Progress indicator every 20 chunks
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(chunks)} embedded...")
    print(f"  Done — {len(chunks)} chunks embedded.\n")
    return np.array(vectors)


# ============================================================
# STEP 3: RETRIEVE
# ============================================================
# WHY: Given a user's question, we need to find which chunks
# contain the answer. We do this by:
#   1. Embedding the question with the SAME model
#   2. Computing cosine similarity between question and all chunks
#   3. Returning the top-K most similar chunks
#
# Cosine similarity measures the angle between two vectors:
#   1.0 = identical direction (very similar meaning)
#   0.0 = perpendicular (unrelated)
# ============================================================

def retrieve(question: str, chunks: list[dict], embeddings: np.ndarray, top_k: int = 3) -> list[dict]:
    """
    Semantic search: find the top-K chunks most relevant to the question.

    1. Embed the question using the same Titan model
    2. Compute cosine similarity against all chunk embeddings
    3. Return the top-K highest-scoring chunks with their scores
    """
    # Embed the question into the same vector space as our chunks
    q_vec = np.array(embed_text(question))

    # Compare question vector against every chunk vector
    scores = []
    for i in range(len(chunks)):
        # Cosine similarity = dot product / (magnitude_a * magnitude_b)
        score = np.dot(q_vec, embeddings[i]) / (
            np.linalg.norm(q_vec) * np.linalg.norm(embeddings[i])
        )
        scores.append(score)

    # Sort by score descending, take top K
    top_indices = np.argsort(scores)[::-1][:top_k]

    return [
        {"text": chunks[idx]["text"], "source": chunks[idx]["source"], "score": float(scores[idx])}
        for idx in top_indices
    ]


# ============================================================
# STEP 4: GENERATE
# ============================================================
# WHY: Now we have the relevant chunks, but the user wants a
# natural language answer — not raw document snippets. We pass
# the retrieved chunks as context to Claude, which synthesizes
# a coherent answer grounded in the actual documents.
#
# This is the "augmented generation" part of RAG:
#   - Without RAG: LLM answers from memory (may hallucinate)
#   - With RAG: LLM answers from provided context (grounded)
# ============================================================

def generate_answer(question: str, retrieved: list[dict]) -> str:
    """
    Send the retrieved context + question to Claude Haiku 4.5 via Bedrock.

    The prompt instructs Claude to ONLY use the provided context,
    preventing hallucination. If the answer isn't in the context,
    it should say so honestly.
    """
    # Format retrieved chunks with their source for traceability
    context = "\n\n---\n\n".join(
        f"[Source: {r['source']}]\n{r['text']}" for r in retrieved
    )

    # System-style instruction followed by context and question
    prompt = (
        f"You are answering questions about PineRidge Solutions' company policies. "
        f"Use ONLY the context below. If the answer isn't there, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )

    # Call Claude via Bedrock's Converse API
    response = bedrock.converse(
        modelId=GENERATION_MODEL,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
    )
    return response["output"]["message"]["content"][0]["text"]


# ============================================================
# CACHE: Persist chunks & embeddings locally
# ============================================================
# WHY: Embedding is slow and costs money (one API call per chunk).
# After the first run, we save everything to disk so subsequent
# runs skip straight to the retrieval + generation steps.
# Delete the cache/ folder to force a fresh re-embedding.
# ============================================================

def save_cache(chunks: list[dict], embeddings: np.ndarray):
    """Save chunks (JSON) and embeddings (NumPy binary) to disk."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CHUNKS_CACHE, "w") as f:
        json.dump(chunks, f)
    np.save(EMBEDDINGS_CACHE, embeddings)
    print(f"  Cache saved.   ")


def load_cache() -> tuple[list[dict], np.ndarray] | None:
    """Load cached chunks and embeddings if they exist. Returns None if no cache."""
    if os.path.exists(CHUNKS_CACHE) and os.path.exists(EMBEDDINGS_CACHE):
        with open(CHUNKS_CACHE, "r") as f:
            chunks = json.load(f)
        embeddings = np.load(EMBEDDINGS_CACHE)
        return chunks, embeddings
    return None


# ============================================================
# RUN THE FULL PIPELINE
# ============================================================

if __name__ == "__main__":

    # --- Load from cache or build fresh ---
    cached = load_cache()
    if cached:
        # Cache hit: skip the expensive chunking + embedding steps
        chunks, embeddings = cached
        print(f"Loaded from cache: {len(chunks)} chunks, embeddings shape {embeddings.shape}\n")
    else:
        # Cache miss: run the full indexing pipeline

        # Step 1: Split documents into searchable chunks
        print("STEP 1: Chunking documents...")
        chunks = chunk_docs(DOCS_FOLDER)
        print(f"  {len(chunks)} chunks from 6 documents.\n")

        # Step 2: Convert each chunk into a vector embedding
        print("STEP 2: Embedding chunks...")
        embeddings = embed_all(chunks)

        # Persist to disk for next run
        save_cache(chunks, embeddings)

    # --- Step 3 + 4: Ask questions and get grounded answers ---
    # These demonstrate the retrieval + generation loop
    questions = [
        "What's the RRSP matching policy?",                       # Should find benefits guide
        # "How many vacation days do I get as a senior engineer?",  # May not have enough info
        # "What's the 90-day rule?",                                # Ambiguous — shows retrieval limits
    ]

    for question in questions:
        print(f"─── Question: {question}")
        print()

        # RETRIEVE: Find the 3 most relevant chunks
        results = retrieve(question, chunks, embeddings)
        print("  Retrieved chunks:")
        for i, r in enumerate(results):
            preview = r["text"][:80].replace("\n", " ")
            print(f"    [{i+1}] ({r['score']:.3f}) {r['source']}")
            print(f"        {preview}...")
        print()

        # GENERATE: Pass chunks to Claude for a natural language answer
        answer = generate_answer(question, results)
        print(f"  Answer: {answer}\n")
        print()
