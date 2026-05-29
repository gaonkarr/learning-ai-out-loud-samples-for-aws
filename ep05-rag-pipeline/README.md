# Episode 5: RAG Pipeline

A complete Retrieval-Augmented Generation pipeline in one file using Amazon Bedrock.

## What it does

1. **Chunk** — Splits 6 company policy docs into paragraph-sized pieces
2. **Embed** — Converts each chunk into a vector using Titan Embeddings V2
3. **Retrieve** — Embeds your question, finds the closest chunks via cosine similarity
4. **Generate** — Passes retrieved chunks + question to Claude Haiku for a grounded answer

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install boto3 numpy
```

## Run

```bash
python3 rag_demo.py
```

First run: chunks the docs, embeds them (~30s), asks 3 test questions.  
Subsequent runs: loads from cache instantly.

## Models used

- `amazon.titan-embed-text-v2:0` — embeddings (us-east-1)
- `us.anthropic.claude-haiku-4-5-20251001-v1:0` — generation (us-east-1)

## Files

```
├── rag_demo.py      # The full pipeline
└── documents/       # 6 fictional company policy docs (knowledge base)
```
