# Episode 6: Why RAG gives wrong answers (and how to fix retrieval failures)

The Episode 5 pipeline worked. Two questions, two correct answers. This folder breaks it on purpose, then fixes it, using the same code and the same six [Amazon Bedrock](https://aws.amazon.com/bedrock?trk=44b16281-e090-49b6-97d8-f1cea54d9e87&sc_channel=el)-powered documents.

The headline: when RAG returns a wrong answer, it's usually not a model problem. It's a retrieval problem. And retrieval is fixable. This demo shows two distinct failure modes and the one-layer fix for each.

## 📺 Watch and/or read

This repo is the code companion for Episode 6 of *Learning AI Out Loud*. The video and blog walk through the *why*. This README covers the *how* of running it.

- 🎥 **Video:** Why RAG gives wrong answers (and how to fix it) — [link coming soon]
- 📝 **Blog:** Why RAG gives wrong answers (and how to fix retrieval failures) — [link coming soon]
- 📺 **Series playlist:** [Learning AI Out Loud](https://www.youtube.com/playlist?list=PLTuh5MoXKZTwoeROV-bA4_6maw0FIoeEf)
- ⬅️ **Start here:** [Episode 5 — building RAG from scratch](../ep05-rag-pipeline/)

## What are the two failure modes?

RAG failures decompose into two layers. Diagnose which layer broke, fix that layer.

1. **Chunking — the answer gets split.** "Can I expense my home office setup during onboarding?" Retrieval finds the right document but the $750 stipend and the $1,200 ergonomic assessment sit under a heading, split from it by a chunk boundary. The model answers honestly but incompletely.
2. **Retrieval — the match is ambiguous.** "What's the 90-day rule?" Four different policies use that exact phrase: expense submission, probation review, RRSP matching, and security access. Semantic search can't tell them apart, so it pulls from everywhere and the model can only ask you to clarify.

Neither is the model inventing things. Both times it answered from exactly what it was handed. Wrong evidence in, wrong answer out.

## How do you fix chunks that split the answer?

Split on **headings** instead of blank lines. Each section heading plus everything under it becomes one chunk, so related facts stay together.

The failure and the fix are in separate files, so you can run one, talk through it, then swap to the other:

```bash
python3 chunking_failure.py    # paragraph chunking — incomplete answer
python3 chunking_fix.py         # heading chunking — complete answer
```

What you'll see: the paragraph-based chunker (the Episode 5 default) retrieves the right documents but an incomplete answer. Notice chunk [2] below — it lands on the "5.3 Home Office Setup" heading, but only the intro line came with it. The dollar amounts sit in a separate chunk that never makes the top 5. The heading-based chunker keeps the whole section together, so the model gets the $750 stipend and the $1,200 ergonomic budget in one piece.

```
$ python3 chunking_failure.py
─── Question: Can I expense my home office setup during onboarding?

  Retrieved chunks (look at what the model was handed):

    [1] score=0.478  source=04-expense-and-travel-policy.md
        (See Benefits Guide Section 5.3 for home office stipend details.)
        For equipment beyond the stipend:
        - Ergonomic assessment recommendation required (see Benefits Guide).
        ...

    [2] score=0.473  source=02-benefits-guide.md
        ### 5.3 Home Office Setup
        For hybrid and remote employees:          ← heading + intro, no numbers

    ... [3]-[5] cross-references and the onboarding timeline

  Answer:
  ...that stipend are referenced in Benefits Guide Section 5.3, but those
  details are not included in the context I have access to. [...] I don't
  have specific information about whether home office setup expenses are
  available during the onboarding period itself.
```

Then run the fix:

```
$ python3 chunking_fix.py
─── Question: Can I expense my home office setup during onboarding?

  Retrieved chunks (look at what the model was handed):

    [2] score=0.492  source=02-benefits-guide.md
        ### 5.3 Home Office Setup
        For hybrid and remote employees:
        - One-time home office stipend: $750 upon hire (receipts within 60 days).
        - Annual refresh: $250 per year for replacement items.
        - Ergonomic assessment: ... PineRidge will cover up to $1,200 ...
        ...

  Answer:
  Yes, you can expense your home office setup during onboarding. One-time
  home office stipend of $750 upon hire (receipts within 60 days), up to
  $1,200 for ergonomic equipment if the HR assessment recommends it, a
  $250/year refresh, and an internet subsidy of $50/month (remote) or
  $25/month (hybrid).
```

Same question, same model. The failing run even names the gap: the stipend details are "not included in the context I have access to." That's not hallucination, it's incomplete evidence. The fix wasn't a better model. It was a better split.

Ask your own question against either strategy with `--question "..."`.

## How do you fix an ambiguous match?

Tag every chunk with its **source** when you store it, then **filter to one source before the similarity search runs**. Narrow first, search second. This is called pre-filtering.

Same split-file setup, so you can run the failure and talk before showing the fix:

```bash
python3 retrieval_failure.py    # no filter — ambiguous, model asks you to clarify
python3 retrieval_fix.py         # source pre-filter — one clean answer per source
```

What you'll see: unfiltered, "What's the 90-day rule?" pulls chunks from four different documents, all with low, similar scores, and the model can only ask which one you mean. `retrieval_fix.py` runs one source at a time — filtered to `employee-handbook`, it searches 26 chunks instead of 185 and answers with the probationary period. To show a different source, comment/uncomment the `run_filtered(...)` line at the bottom of the file and rerun (or pass `--source expense-policy` to get the 90-day submission deadline).

```
$ python3 retrieval_failure.py
─── Question: What's the 90-day rule?

  Retrieved chunks (look at what the model was handed):

    [1] score=0.394  source=it-security-policy
        ### 1.3 Principle of Least Privilege and the 90-Day Access Rule
        - Access is granted on a least-privilege basis.
        - Elevated access ... expires after 90 days unless renewed.
        ...

    [2] score=0.349  source=employee-handbook
        ### 1.3 The 90-Day Review
        At the end of your probationary period, your manager conducts...
        ...

    ... [3]-[5] more handbook, plus expense-policy and leave-policy

  Answer:
  ...there are actually two different "90-day rules": the 90-Day Access
  Rule (elevated access expires after 90 days) and the 90-Day Review
  (end of the probationary period). Which one were you asking about?
```

Then run the fix. It filters to one source (edit the file to switch, or use `--source`):

```
$ python3 retrieval_fix.py
Filter source='employee-handbook': 26 of 185 chunks searched

─── Question: What's the 90-day rule?
  ...
  Answer:
  The 90-day rule refers to the probationary period all new employees
  serve: bi-weekly manager check-ins, no internal transfers, and a formal
  review at the end that transitions you to regular employee status.
```

Swap the source (comment/uncomment in the file, or `--source expense-policy`) and rerun:

```
$ python3 retrieval_fix.py --source expense-policy
Filter source='expense-policy': 27 of 185 chunks searched

─── Question: What's the 90-day rule?
  ...
  Answer:
  The 90-Day Submission Rule: expenses must be submitted within 90 calendar
  days of being incurred. 91–120 days needs manager approval; past 120 days
  is not reimbursed except in extraordinary circumstances.
```

Same vague question. A different clean answer each time, because we narrowed the search space before the similarity search ran. Note the unfiltered scores (all around 0.27–0.39) — nothing stands out, which is exactly why semantic search alone can't resolve the ambiguity.

Filter to a specific source yourself:

```bash
python3 retrieval_fix.py --source benefits-guide   # the RRSP 90-day rule
python3 retrieval_fix.py --list-sources            # see all six labels
```

## Who picks the filter in production?

In this demo, you pick it by hand. In production a **self-querying retriever** picks it for you: pass the question to a small, fast model and ask which metadata filter applies. It's a classification task, so it doesn't need an expensive model (the "right model for the right job" point from Episode 3). The expensive model handles only the final answer.

Frameworks like LangChain give you this as a building block. Managed services like the [Amazon Bedrock Knowledge Bases](https://aws.amazon.com/bedrock/knowledge-bases?trk=44b16281-e090-49b6-97d8-f1cea54d9e87&sc_channel=el) run the filter step as part of the pipeline. They don't swap models behind your back — you still choose which model does what. They handle the wiring: pull the filter out of the question, apply it before the search.

One production note on that source tag, and a distinction worth being precise about. In this demo we attach the tag to each chunk while we're chunking (`retrieval_fix.py` stamps `source_label` on every chunk), so it's **chunk-level** metadata. Metadata can also live on the file itself. If your documents sit in [Amazon S3](https://aws.amazon.com/s3?trk=44b16281-e090-49b6-97d8-f1cea54d9e87&sc_channel=el), a feature called [S3 annotations](https://aws.amazon.com/blogs/aws/amazon-s3-annotations-attach-rich-queryable-context-directly-to-your-objects/?trk=44b16281-e090-49b6-97d8-f1cea54d9e87&sc_channel=el) lets you attach rich, updatable context straight to the object, and it stays queryable.

The difference: our example adds metadata *while chunking*, so it's per-chunk. S3 annotations add metadata to the *whole file*, so every chunk from that file inherits it. File-level context is great for the coarse cut — which document, which source, which category. Chunk-level context is what you need when different chunks from the same file deserve different tags. Most real systems use both: annotate the file for discovery, tag the chunk for precision.

## Setup

From the repo root (one level up from this folder):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You also need:

- AWS credentials configured (`aws configure` or an SSO profile)
- Amazon Bedrock **model access** enabled for both models below in `us-east-1`

This demo reads the six policy documents from [`../ep05-rag-pipeline/documents/`](../ep05-rag-pipeline/documents/) — same data as Episode 5, so keep that folder in place.

## Files

Each layer has a **failure** file and a **fix** file. The fix file changes exactly one thing from its failure file, so on screen the difference is the whole story. Shared pipeline plumbing (embed, retrieve, generate, cache, printing) lives in `rag_common.py`.

```
ep06-rag-failures/
├── rag_common.py         # Shared pipeline: embed, retrieve (+optional filter), generate, cache
│
├── chunking_failure.py   # Layer 1 FAILURE: paragraph chunking splits the answer
├── chunking_fix.py       # Layer 1 FIX:     heading chunking keeps the section whole
│
├── retrieval_failure.py  # Layer 2 FAILURE: no filter, ambiguous match across documents
├── retrieval_fix.py      # Layer 2 FIX:     tag by source, pre-filter before searching
│
└── cache/                # Auto-generated on first run (git-ignored)
    ├── paragraph_chunks.json / paragraph_embeddings.npy   (chunking_failure)
    ├── heading_chunks.json   / heading_embeddings.npy     (chunking_fix)
    └── metadata_chunks.json  / metadata_embeddings.npy    (both retrieval files)
```

The first run of each script chunks and embeds (~30 seconds, one Titan call per chunk), then caches the result. The two retrieval files share the `metadata_*` cache, so once one has embedded, the other is instant. Delete a `cache/` file to force a fresh re-embedding.

## Chunking strategies, at a glance

Heading-based isn't always the answer. If your documents have no headings, it won't help. If sections are huge, you're back to the "too much context" problem. Common alternatives:

| Strategy | How it splits | When to reach for it |
|----------|---------------|----------------------|
| Fixed-size | Every N tokens, ignoring structure | Uniform text; simplest baseline |
| Recursive | Headings, then paragraphs, then sentences (fallback chain) | Most frameworks' sensible default |
| Semantic | Where consecutive-sentence similarity drops | Meaning-dense text without clear structure |
| Parent-child | Small chunks for search, return the large parent for generation | Precise retrieval AND complete context |
| Heading-based | On markdown/section headings | Structured docs like these policies |

There's no universal right answer. A [study of chunking strategies for RAG](https://research.trychroma.com/evaluating-chunking) found the chunking choice can matter as much as the embedding model. A reasonable starting point for most systems: recursive splitting, 256–512 token chunks, 10–20% overlap. That's a default, not a law.

## Models used

| Step | Model | Why |
|------|-------|-----|
| Embed | `amazon.titan-embed-text-v2:0` | Fast, cheap, 1024-d vectors, runs on Bedrock |
| Generate | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Cheapest Claude tier, plenty for grounded Q&A |

Both run in `us-east-1`. Switch regions or models by editing the constants at the top of each script.

## Questions to try

- **Chunking, home office:** run both files with `--question "How much is the home office stipend for new hires?"` and compare paragraph vs heading.
- **Retrieval, each 90-day rule:** `retrieval_fix.py --source benefits-guide` (RRSP), `--source it-security-policy` (access expiry), `--source employee-handbook` (probation), `--source expense-policy` (submission deadline). Same phrase, four meanings.
- **A question one document can't answer:** filter to a source that doesn't hold the answer and watch the scores drop. Weak retrieval is a signal in itself.

## What's next

Everything so far, the model reads your stuff and answers. It doesn't *do* anything. Episode 7 changes that: the model picks up tools, calls an API, and takes action on what it finds. [Ride along](https://youtube.com/@RohiniGaonkar).
