# Learning AI Out Loud — Code Samples for AWS

Workspace for the **Learning AI Out Loud** series, a ground-up walkthrough of building with AI from first principles. Hosted by a cloud architect and AWS developer advocate returning from maternity leave, learning AI in public.

- 📺 **Watch:** [@RohiniGaonkar on YouTube](https://youtube.com/@RohiniGaonkar)
- 📝 **Read:** [dev.to/aws series](https://dev.to/rohini_gaonkar)

## Who it's for

- **Curious non-coders** (PMs, designers, ops, analysts, architects) who work around tech but don't code daily
- **Experienced developers** who feel behind on AI and want a ground-up refresher without condescension

Each episode delivers the *what and why* for everyone, plus an architecture beat for builders who want the *how*.

## What the series covered so far (ongoing)

| # | Title | Blog |
|---|-------|------|
| 1 | What Even Is AI? (I Took a Break & Had to Relearn Everything) | [Read](https://dev.to/aws/what-even-is-ai-i-took-a-break-had-to-relearn-everything-3dpj) |
| 2 | Why does AI lie? Hallucinations explained simply | [Read](https://dev.to/aws/why-does-ai-lie-hallucinations-explained-simply-1c7g) |
| 3 | Bigger AI models aren't always better. Here's how to actually choose. | [Read](https://dev.to/aws/bigger-ai-models-arent-always-better-heres-how-to-actually-choose-56pc) |
| 4 | Why does AI forget what you said (and how to fix it) | [Read](https://dev.to/aws/why-does-ai-forget-what-you-said-and-how-to-fix-it-52f6) |
| 5 | How to make AI answer questions about your documents — building RAG from scratch | [Read](https://dev.to/aws/how-to-make-ai-answer-questions-about-your-documents-by-building-rag-from-scratch-4dg0) |

Every episode demos something working, then shows where it breaks. No fluff, just useful.

## What's in this folder

```
.
├── learning-ai-out-loud-samples/  ← Published code repo, one folder per episode
└── README.md                      ← You are here
```

### Code

All published code samples live in [`learning-ai-out-loud-samples/`](learning-ai-out-loud-samples/), a standalone GitHub-ready repo. Each episode gets its own folder with setup instructions, sample questions, and a runnable script.

Episodes can use different demo data, different services, and different model combinations. The per-episode folder layout keeps that clean — Ep 5 might use a fictional onboarding doc set, Ep 7 might need a weather API, Ep 8 might bring its own scenario. Each folder is self-contained.

Start with the per-episode README when you want to clone, run, or follow along.

**This sample works with [Amazon Bedrock](https://aws.amazon.com/bedrock/).**

## Episodes

| Episode | Folder | What it covers |
|---------|--------|----------------|
| 5 | [ep05-rag-pipeline/](ep05-rag-pipeline/) | Build a RAG pipeline from scratch: chunk, embed, retrieve, generate |

## Getting started

One venv at the repo root covers all episodes:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then run code for each episode:

```bash
cd ep05-rag-pipeline/
python3 rag_demo.py
```

## Prerequisites

- Python 3.10+
- AWS credentials configured (`aws configure`)
- Amazon Bedrock model access enabled in your account

## License and IP

MIT-0 — See [LICENSE](LICENSE).

Any demo content here is 100% fictional. No real company, product, person, address, or policy is referenced. Safe for public use on YouTube, blog posts, GitHub repos, and any demo you want to build on top of it.

If you reuse the demo data in your own talks or projects, a credit back to the series is appreciated but not required.
