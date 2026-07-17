"""
FAILURE 2 — Ambiguous match
===========================
Run this first. Ask: "What's the 90-day rule?"

Chunking isn't the problem here. The chunks are fine. The problem is that
the SAME phrase means different things in different documents, and semantic
search can't tell them apart.

There are several different "90-day rules" across these policies:
  - Expense policy    — submit expenses within 90 days
  - Employee handbook — 90-day probationary period and review
  - Benefits guide    — RRSP matching starts after 90 days
  - IT security       — elevated access expires after 90 days

With no filter, retrieval scores all 185 chunks and pulls matches from
across the documents, all with low, similar scores. The system floods the
model with mixed context, burns tokens, and the best it can do is ask
"which one do you mean?". Fine with 6 documents. A problem with 6,000.

  Run the fix next:  python3 retrieval_fix.py

Usage:
  python3 retrieval_failure.py
  python3 retrieval_failure.py --question "..."
"""

import os
import re
import argparse
import rag_common as rag

QUESTION = "What's the 90-day rule?"

HEADING_RE = re.compile(r"^#{2,6}\s")

# The metadata we attach to every chunk. Note we DEFINE the source tag here
# (this is what makes the fix possible) but in this failure run we never USE
# it — retrieve() is called without a filter.
SOURCE_LABELS = {
    "01-employee-handbook.md": "employee-handbook",
    "02-benefits-guide.md": "benefits-guide",
    "03-leave-policy.md": "leave-policy",
    "04-expense-and-travel-policy.md": "expense-policy",
    "05-engineering-onboarding.md": "engineering-onboarding",
    "06-it-security-policy.md": "it-security-policy",
}


def chunk_by_heading(text: str, source: str, source_label: str) -> list[dict]:
    """Heading-based chunking, with a source tag stamped on every chunk."""
    chunks = []
    current: list[str] = []

    def flush():
        block = "\n".join(current).strip()
        if block:
            chunks.append({"text": block, "source": source, "source_label": source_label})

    for line in text.split("\n"):
        if HEADING_RE.match(line) and current:
            flush()
            current = [line]
        else:
            current.append(line)
    flush()
    return chunks


def build_chunks() -> list[dict]:
    """Chunk every document and tag it with its source label."""
    chunks = []
    for filename in sorted(os.listdir(rag.DOCS_FOLDER)):
        if not filename.endswith(".md") or filename == "README.md":
            continue
        label = SOURCE_LABELS.get(filename, filename)
        with open(os.path.join(rag.DOCS_FOLDER, filename), "r") as f:
            chunks.extend(chunk_by_heading(f.read(), filename, label))
    return chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ep 6 — retrieval FAILURE (no filter)")
    parser.add_argument("--question", default=QUESTION)
    args = parser.parse_args()

    chunks, embeddings = rag.load_or_build("metadata", build_chunks)

    # No source_label -> search everything. Watch the sources scatter.
    rag.run_query(args.question, chunks, embeddings, source_label=None, show_label_only=True)
