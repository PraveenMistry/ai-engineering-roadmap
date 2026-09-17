# AI Engineering Roadmap — Build Log

Code from my self-directed 17-week program moving from backend engineering
into AI/Agentic engineering depth. Organized by topic, with each topic
folder containing the numbered stages of that topic's progression.

> ⚠️ **Synthetic data notice:** Every "company document" used across these
> projects (leave policy, remote work policy, contractor rules, engineering
> practices) is fictional sample data I wrote for these exercises. None of
> it reflects any real employer's actual policies, and no real company data
> is used anywhere in this repo.

## Structure

```
ai-engineering-roadmap/
├── rag/
│   ├── 01-basic-rag/          ✅ chunking, embeddings, vector search
│   ├── 02-advanced-rag/       🚧 hybrid search, reranking, metadata filtering (scaffolded)
│   └── 03-agentic-rag/        ✅ retrieve → evaluate → rewrite → answer/abstain
└── langgraph/
    └── 01-agent-migration/    ✅ the agentic-rag loop, rebuilt as a LangGraph StateGraph
```

Each topic folder has its own README explaining the progression within
it. Each numbered stage has its own README with setup and run
instructions specific to that project.

## Running any project locally

Everything here runs entirely free and local using [Ollama](https://ollama.com) —
no API key required.

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

Then `cd` into the specific stage folder you want and follow its own
README.

## Why this exists

This is a working build log, not a polished product — including the
bugs. A couple of write-ups on my
[Medium](https://medium.com/@praveenmistry) reference specific folders
here directly, including a real false test assertion that turned out to
reveal a flawed test assumption rather than an actual bug in the agent
(see `rag/03-agentic-rag`).

## Roadmap

New topic folders will be added as the program continues:
`multi-agent/`, `mcp/`, `evaluation/`, `security/`, `production/`, and a
final capstone — following the same topic → numbered-stage pattern
established here.
