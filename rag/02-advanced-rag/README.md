> ⚠️ **Note:** All company documents in this project (leave policy, remote work, contractor rules, etc.) are **fictional, synthetic sample data** written for this learning exercise. None of this reflects any real employer's actual policies.

# Day 6 — Advanced RAG (Upgrading Day 5's RAG)

> **Status: scaffolded, not fully implemented.** Only the folder structure
> and planning are here. Exercise 1 (metadata-enriched embeddings) was
> paused pending local model verification and superseded by moving ahead
> to Day 7's Agentic RAG build. `keyword_search.py`, `hybrid_search.py`,
> `metadata_filter.py`, `reranker.py`, and `query_rewrite.py` are
> placeholder files, not working implementations. Treat this folder as
> a plan, not a demo.

## The end goal

```
week-01/
└── day-06/
    ├── README.md
    ├── documents/          ← same 3 docs from Day 5, reused
    ├── embeddings.py        [Exercise 1 — today]
    ├── semantic_search.py   [Exercise 1 — today]
    ├── keyword_search.py    [Exercise 2 — later]
    ├── hybrid_search.py     [Exercise 3 — later]
    ├── metadata_filter.py   [Exercise 4 — later]
    ├── reranker.py          [Exercise 5 — later]
    ├── query_rewrite.py     [Exercise 6 — later]
    └── rag.py               [Final assembly — later]
```

We are NOT building all of this today. One file at a time, one concept
at a time — same approach as Day 4's gateway build.

## Why this upgrade matters

Day 5's RAG only had one retrieval strategy: pure vector similarity.
That breaks in predictable ways:

- Exact terms/codes/names sometimes get missed by semantic search alone
  → **keyword_search.py** fixes this
- Combining both signals gets you the best of each
  → **hybrid_search.py**
- Retrieval can accidentally pull HR content when the user asked an
  engineering question
  → **metadata_filter.py**
- The top-k chunks by similarity aren't always the most *useful* chunks
  → **reranker.py**
- Vague or oddly-phrased questions retrieve poorly
  → **query_rewrite.py**

Each file is a standalone, testable upgrade. `rag.py` at the end wires
all of them together — same philosophy as Day 4's Gateway: don't build
the whole machine before you've proven each part works alone.

## Exercise 1 — Semantic Retrieval (today's focus)

Flow:

```
Question
   ↓
Ollama embedding
   ↓
Cosine similarity
   ↓
Top 5 chunks
```

This re-does Day 5's `ingest.py` + `retrieve.py`, but with one important
change: every stored chunk now carries **metadata**, not just text:

```json
{
    "text": "...",
    "embedding": [...],
    "metadata": {
        "document": "remote-work.md",
        "department": "engineering"
    }
}
```

We're not using that metadata yet — that's Exercise 4. Today we just
make sure it's captured and stored correctly at ingestion time, since
retrofitting metadata onto an existing store later is annoying. Storing
it now costs nothing and saves you a rebuild later.

## Before writing any code — one thing to confirm

Run this in your terminal:

```bash
ollama list
```

This shows exactly which models you have pulled locally (chat model,
embedding model, and their exact tags/versions). The embedding code
needs the *exact* model name you have installed — paste that output
back and the real `embeddings.py` + `semantic_search.py` code gets
written to match it exactly, rather than guessing.
