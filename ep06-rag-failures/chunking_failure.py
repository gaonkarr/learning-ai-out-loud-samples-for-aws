"""
FAILURE 1 — Chunks too small
=============================
Run this first. Ask: "Can I expense my home office setup during onboarding?"

This is the Episode 5 chunker, unchanged. It splits documents on blank
lines (paragraph boundaries) with one paragraph of overlap.

WHY IT BREAKS: a markdown section like "5.3 Home Office Setup" is a heading,
then an intro line, then a bullet list of dollar amounts. Those are separate
paragraphs. Retrieval can match the heading but miss the numbers, so the
model gets the right topic with the actual answer ($750 stipend, $1,200
ergonomic budget) cut off. It answers honestly, but incompletely.

The chunks are too small. The search found the right place; the paragraph
split cut the answer short.

  Run the fix next:  python3 chunking_fix.py

Usage:
  python3 chunking_failure.py
  python3 chunking_failure.py --question "..."
"""

import os
import argparse
import rag_common as rag

QUESTION = "Can I expense my home office setup during onboarding?"


# ============================================================
# STEP 1: CHUNK — paragraph-based (the failing strategy)
# ============================================================

def chunk_by_paragraph(text: str, source: str) -> list[dict]:
    """Split a document on blank lines, with one paragraph of overlap."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    for i in range(len(paragraphs)):
        # Include the previous paragraph for a little context continuity.
        start = max(0, i - 1)
        chunk_text = "\n\n".join(paragraphs[start : i + 1])
        chunks.append({"text": chunk_text, "source": source})
    return chunks


def build_chunks() -> list[dict]:
    """Paragraph-chunk all six policy documents."""
    chunks = []
    for filename in sorted(os.listdir(rag.DOCS_FOLDER)):
        if not filename.endswith(".md") or filename == "README.md":
            continue
        with open(os.path.join(rag.DOCS_FOLDER, filename), "r") as f:
            chunks.extend(chunk_by_paragraph(f.read(), filename))
    return chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ep 6 — chunking FAILURE (paragraph)")
    parser.add_argument("--question", default=QUESTION)
    args = parser.parse_args()

    chunks, embeddings = rag.load_or_build("paragraph", build_chunks)
    rag.run_query(args.question, chunks, embeddings)
