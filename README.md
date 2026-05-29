# Learning AI Out Loud — Code Samples for AWS

Code samples from the [Learning AI Out Loud](https://youtube.com/@LearningAIOutLoud) video series, demonstrating AWS AI/ML services.

**This sample works with [Amazon Bedrock](https://aws.amazon.com/bedrock/).**

## Episodes

| Episode | Folder | What it covers |
|---------|--------|----------------|
| 5 | [ep05-rag-pipeline/](ep05-rag-pipeline/) | Build a RAG pipeline from scratch — chunk, embed, retrieve, generate |

## Getting started

Each episode folder has its own README with setup instructions. Generally:

```bash
cd ep05-rag-pipeline/
python3 -m venv .venv
source .venv/bin/activate
pip install boto3 numpy
python3 rag_demo.py
```

## Prerequisites

- Python 3.10+
- AWS credentials configured (`aws configure`)
- Amazon Bedrock model access enabled in your account

## License

MIT-0 — See [LICENSE](LICENSE).
