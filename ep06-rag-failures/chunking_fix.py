"""
FIX 1 — Heading-based chunking
==============================
Run this after chunking_failure.py, with the SAME question:
"Can I expense my home office setup during onboarding?"

The only thing that changed from chunking_failure.py is the chunker below.
Instead of splitting on blank lines, we split on markdown headings. Each
section heading plus everything under it — the intro line AND the bullet
list of dollar amounts — becomes ONE chunk. Related information stays
together, so "5.3 Home Office Setup" travels as a whole.

Now the model has complete evidence and gives a complete answer: the $750
stipend, the $250/year refresh, the $1,200 ergonomic assessment, all of it.

The fix wasn't a better model. It was a better split.

Usage:
  python3 chunking_fix.py
  python3 chunking_fix.py --question "..."
"""

import os
import re
import argparse
import rag_common as rag

QUESTION = "Can I expense my home office setup during onboarding?"

# Matches markdown headings of level 2 or deeper: ##, ###, ####, ...
# We deliberately do NOT split on the level-1 title (#) so the document
# title stays attached to its opening section.
HEADING_RE = re.compile(r"^#{2,6}\s")


# ============================================================
# STEP 1: CHUNK — heading-based (the fix)
# ============================================================
# THIS is the whole difference from chunking_failure.py.

def chunk_by_heading(text: str, source: str) -> list[dict]:
    """
    Split a document so each heading, plus everything beneath it until the
    next heading, becomes a single chunk.
    """
    chunks = []
    current: list[str] = []

    for line in text.split("\n"):
        # A new heading starts a new section. Flush what we've collected.
        if HEADING_RE.match(line) and current:
            block = "\n".join(current).strip()
            if block:
                chunks.append({"text": block, "source": source})
            current = [line]
        else:
            current.append(line)

    # Don't forget the final section.
    block = "\n".join(current).strip()
    if block:
        chunks.append({"text": block, "source": source})
    return chunks


def build_chunks() -> list[dict]:
    """Heading-chunk all six policy documents."""
    chunks = []
    for filename in sorted(os.listdir(rag.DOCS_FOLDER)):
        if not filename.endswith(".md") or filename == "README.md":
            continue
        with open(os.path.join(rag.DOCS_FOLDER, filename), "r") as f:
            chunks.extend(chunk_by_heading(f.read(), filename))
    return chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ep 6 — chunking FIX (heading-based)")
    parser.add_argument("--question", default=QUESTION)
    args = parser.parse_args()

    chunks, embeddings = rag.load_or_build("heading", build_chunks)
    rag.run_query(args.question, chunks, embeddings)
