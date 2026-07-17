"""
FIX 2 — Metadata pre-filtering
==============================
Run this after retrieval_failure.py, with the SAME question:
"What's the 90-day rule?"

Same chunks, same embeddings as the failure run. The ONLY difference is the
one argument passed to retrieve(): source_label. We tagged every chunk with
its source document at ingestion time; now we FILTER to one source BEFORE the
similarity search runs. Narrow first, search second.

By default this runs ONE source (employee-handbook). To show another, comment
that line out and uncomment the next one at the bottom of this file, then
rerun. Same vague question, a different clean answer each time:
  - employee-handbook -> the 90-day probationary period
  - expense-policy    -> submit expenses within 90 days
  - benefits-guide    -> RRSP matching starts after 90 days
Or pass --source <label> without editing the file.

You picked the filter by hand here. In production a "self-querying retriever"
picks it for you: a small, fast model reads the question and extracts the
filter. Frameworks like LangChain and managed services like Amazon Bedrock
Knowledge Bases do that wiring for you. The idea is the same — don't search
everything when you can narrow it down first.

Usage:
  python3 retrieval_fix.py                         # runs one source (employee-handbook)
  python3 retrieval_fix.py --source benefits-guide # pick a source without editing
  python3 retrieval_fix.py --list-sources
"""

import os
import re
import argparse
import rag_common as rag

QUESTION = "What's the 90-day rule?"

HEADING_RE = re.compile(r"^#{2,6}\s")

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


def run_filtered(question, chunks, embeddings, source_label):
    """Run one filtered query, showing how much the search space shrank."""

    pool = sum(1 for c in chunks if c.get("source_label") == source_label)

    # The whole fix: pass source_label so we PRE-FILTER before scoring.
    print(f"Filter source='{source_label}': {pool} of {len(chunks)} chunks searched\n")

    rag.run_query(question, chunks, embeddings, source_label=source_label, show_label_only=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ep 6 — retrieval FIX (metadata pre-filter)")
    parser.add_argument("--question", default=QUESTION)
    parser.add_argument("--source", default=None, help="Restrict to one source label.")
    parser.add_argument("--list-sources", action="store_true")
    args = parser.parse_args()

    if args.list_sources:
        print("Available source labels:")
        for label in dict.fromkeys(SOURCE_LABELS.values()):
            print(f"  {label}")
        raise SystemExit

    chunks, embeddings = rag.load_or_build("metadata", build_chunks)

    if args.source:
        run_filtered(args.question, chunks, embeddings, args.source)
    else:
        # Run ONE source at a time. Show this one, talk it through, then
        # comment it out, uncomment the next, and rerun. Same vague question,
        # a different clean answer each time.
        # run_filtered(args.question, chunks, embeddings, "employee-handbook")
        run_filtered(args.question, chunks, embeddings, "expense-policy")
        # run_filtered(args.question, chunks, embeddings, "benefits-guide")
        # run_filtered(args.question, chunks, embeddings, "it-security-policy")
