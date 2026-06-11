# Episode 6: Why RAG Gives Wrong Answers (and How to Fix It)

Same documents, same models as Episode 5. This time we break it on purpose, then fix it.

## What this demonstrates

1. **Failure modes** — Two questions that fail with paragraph-based chunking
2. **Fix 1** — Heading-based chunking keeps related info together (chunking layer)
3. **Fix 2** — Metadata filtering narrows the search space (retrieval layer)

## Structure

The episode is grouped by layer:
- **Chunking layer:** Problem → Fix → Strategies
- **Retrieval layer:** Problem → Fix → Strategies

## Setup

From the repo root (one level up):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Documents

Uses the same 6 policy documents from Episode 5. They're referenced at `../ep05-rag-pipeline/documents/`.

## Files

| File | What it shows |
|------|---------------|
| `01_show_failures.py` | Two questions that fail with paragraph chunking |
| `02_fix_heading_chunking.py` | Heading-based chunking fixes the incomplete answer |
| `03_metadata_filtering.py` | Pre-filtering by source fixes the ambiguous match |

## Run

```bash
python3 01_show_failures.py
python3 02_fix_heading_chunking.py
python3 03_metadata_filtering.py
```

Each file caches its embeddings on first run. Subsequent runs load from cache instantly.
Delete the `cache/` folder to force a fresh re-embedding.

## Models used

- `amazon.titan-embed-text-v2:0` — embeddings (us-east-1)
- `us.anthropic.claude-haiku-4-5-20251001-v1:0` — generation (us-east-1)
