# Learning AI Out Loud — Code Samples for AWS

Workspace for the **Learning AI Out Loud** series, a ground-up walkthrough of building with AI from first principles. Hosted by a cloud architect and AWS developer advocate returning from maternity leave, learning AI in public.

- 📺 **Watch:** [@RohiniGaonkar on YouTube](https://youtube.com/@RohiniGaonkar)
- 📝 **Read:** [dev.to/aws series](https://dev.to/rohini_gaonkar)

## Who it's for

- **Curious non-coders** (PMs, designers, ops, analysts, architects) who work around tech but don't code daily
- **Experienced developers** who feel behind on AI and want a ground-up refresher without condescension

Each episode delivers the *what and why* for everyone, plus an architecture beat for builders who want the *how*.

## What the series covered so far (ongoing)

| Episode | Title | Dev.to | AWS Builder Center | Video |
|---------|-------|--------|--------------------|-------|
| 1 | What even is AI? I took a break, had to relearn everything | [Read](https://dev.to/aws/what-even-is-ai-i-took-a-break-had-to-relearn-everything-3dpj) | [Read](https://builder.aws.com/content/3DwmczRvQ5ixlgoThRI6x9maFB2/what-even-is-ai-i-took-a-break-and-had-to-relearn-everything) | [Watch](https://www.youtube.com/watch?v=ly3P-NpLni0) |
| 2 | Why does AI lie? Hallucinations explained simply | [Read](https://dev.to/aws/why-does-ai-lie-hallucinations-explained-simply-1c7g) | [Read](https://builder.aws.com/content/3DlndPKEzyHp05T8T6tZZnl7F5f/why-does-ai-lie-hallucinations-explained-simply) | [Watch](https://www.youtube.com/watch?v=sMb4wmGbeD8) |
| 3 | Bigger AI models aren't always better. Here's how to actually choose. | [Read](https://dev.to/aws/bigger-ai-models-arent-always-better-heres-how-to-actually-choose-56pc) | [Read](https://builder.aws.com/content/3DMHF89CWvyASiU7CC0WQx1Fd8U/bigger-ai-models-arent-always-better-heres-how-to-actually-choose) | [Watch](https://www.youtube.com/watch?v=fb3d6-HnGMM) |
| 4 | Why does AI forget what you said, and how to fix it | [Read](https://dev.to/aws/why-does-ai-forget-what-you-said-and-how-to-fix-it-4e5g) | [Read](https://builder.aws.com/content/3DwpTl5V8cbiIA13y1fUVXHudYz/why-does-ai-forget-what-you-said-and-how-to-fix-it) | [Watch](https://www.youtube.com/watch?v=ULp_WbgkHzc) |
| 5 | How to make AI answer questions about your documents — building RAG from scratch | [Read](https://dev.to/aws/how-to-make-ai-answer-questions-about-your-documents-by-building-rag-from-scratch-4dg0) | [Read](https://builder.aws.com/content/3F0Eiejm567GfStoJzxrBFvm59I/how-to-make-ai-answer-questions-about-your-documents-by-building-rag-from-scratch) | [Watch](https://www.youtube.com/watch?v=l4aA2NLmWBQ) |
| 6 | Why RAG gives wrong answers (and how to fix retrieval failures) | [Read](https://dev.to/aws/why-rag-gives-wrong-answers-and-how-to-fix-retrieval-failures-gbj) | [Read](https://builder.aws.com/content/3GeD1cv2is6e1JmHSO0ayHlvoGm/why-rag-gives-wrong-answers-and-how-to-fix-retrieval-failures) | [Watch](https://www.youtube.com/watch?v=KsICvZxAyxM) |
| 7 | How AI actually calls an API: tool calling, and how ChatGPT knows today's date | [Read](https://dev.to/aws/how-ai-actually-calls-an-api-tool-calling-explained-from-scratch-4lf8) | [Read](https://builder.aws.com/content/3JQXxclnjAEFozjqf5LiLXgafrK/how-ai-actually-calls-an-api-tool-calling-explained-from-scratch) | [Watch](https://www.youtube.com/watch?v=mCnsIHja5cw) |

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
| 6 | [ep06-rag-failures/](ep06-rag-failures/) | Break RAG two ways and fix it: heading-based chunking, metadata pre-filtering |
| 7 | [ep07-tool-calling/](ep07-tool-calling/) | Give the model a tool: the four-step tool-calling loop, where it breaks (wrong arguments), and MCP |

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
