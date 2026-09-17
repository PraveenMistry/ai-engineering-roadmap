> ⚠️ **Note:** All company documents in this project (leave policy, remote work, contractor rules, etc.) are **fictional, synthetic sample data** written for this learning exercise. None of this reflects any real employer's actual policies.

# Day 5 — Company Knowledge Assistant (RAG Fundamentals)

## What you're building

```
PDF/DOCX (here: .md files)
     ↓
Chunk
     ↓
Embedding
     ↓
Vector DB   (a JSON file today — Pinecone/pgvector comes in Week 6)
     ↓
RAG
     ↓
Chat
```

Three sample company documents (`leave-policy.md`, `remote-work.md`,
`engineering.md`) act as your "company knowledge." You'll ask it
questions like *"How many sick days do I get?"* and it should answer
using only that content — and tell you when it doesn't know.

## Why three separate files instead of one script

- `ingest.py` — Documents → Parsing → Chunking → Embeddings → Vector Store
- `retrieve.py` — Query → Retrieval → Top-k relevant chunks (no LLM call)
- `rag.py` — Retrieval + Context → LLM → Answer

Keeping retrieval separate from generation is deliberate. In Week 13
(Evaluation) you'll need to test retrieval quality independently of
answer quality — "did we retrieve the right chunks?" is a different
question from "did the LLM answer well given those chunks?" Bad
answers can come from either stage, and you need to isolate which.

## Setup — running fully free, fully local (Ollama)

No API key needed. Everything runs on your M1.

1. Install Ollama: https://ollama.com/download

2. Pull the two models used here:
```bash
ollama pull llama3.2          # chat / generation
ollama pull nomic-embed-text  # embeddings
```

3. Set up your Python environment:
```bash
cd week-01/day-05
python3 -m venv venv
source venv/bin/activate
pip install ollama
```

That's it — no `.env`, no billing, no rate limits. The trade-off: a local
7B-class model like llama3.2 is noticeably weaker than GPT-4o-mini or
Claude, especially on nuanced abstain decisions ("do I actually know
this?"). Good enough to learn the RAG mechanics — worth keeping in mind
when you get to Week 13 (Evaluation) and compare model quality properly.

## Run order (this matters)

### 1. Ingest the documents (run once, or whenever documents/ changes)
```bash
python ingest.py
```
This reads all `.md` files in `documents/`, splits them into overlapping
chunks, embeds each chunk, and saves everything into `vector_store.json`.

### 2. Sanity-check retrieval on its own
```bash
python retrieve.py
```
This runs a hardcoded test query and prints the top 3 matching chunks
with their similarity scores. **Look at the scores and the text before
moving on.** If retrieval is bad here, RAG will be bad no matter how
good your prompt is.

### 3. Run the full assistant
```bash
python rag.py
```
Ask it things like:
- "How many days of annual leave do I get?"
- "Can I work fully remote?"
- "What happens during a SEV1 incident?"
- "What's the company's stance on cryptocurrency?" ← should abstain,
  since nothing in the documents covers this

Type `exit` to quit.

## What to actually pay attention to

1. **Chunk boundaries** — open `vector_store.json` and look at a couple
   of chunks. Did chunking ever cut a sentence awkwardly in half? This
   is exactly why chunk size and overlap are tunable, and why "chunking
   strategy" is its own topic in Week 6.

2. **Similarity scores** — in `retrieve.py`'s output, how much higher
   is the top match's score vs. the others? A huge gap means retrieval
   is confident; a small gap means several chunks are nearly equally
   relevant (or none are truly relevant) — this is one of the signals
   behind "answer vs. abstain" decisions in Agentic RAG (Week 7).

3. **The abstain case** — ask it something totally unrelated to the
   documents. Does it correctly say "I don't have enough information,"
   or does it hallucinate an answer anyway? If it hallucinates, that's
   a prompt problem you can iterate on right now.

## Known limitations (intentional, for today)

- No hybrid/keyword search — pure vector similarity only (Week 6 topic).
- No reranking (Week 6 topic).
- Vector store is a flat JSON file, fine for ~dozens of chunks, not
  built for scale (Week 6: real vector DB).
- No conversation memory — every question is independent (multi-turn
  chat context is a later concern).

None of these are bugs. They're exactly what gets layered on next week.
