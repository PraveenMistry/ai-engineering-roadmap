# RAG — Basic → Advanced → Agentic

> ⚠️ All company documents used across these projects (leave policy,
> remote work, contractor rules, engineering practices) are fictional
> sample data written for these exercises — not any real employer's
> actual policies.

This folder tracks one continuous progression, not three separate
projects. Each stage upgrades the previous one's retrieval quality or
decision-making, reusing the same core embedding/retrieval code where
possible.

| Stage | What it adds | Status |
|---|---|---|
| [`01-basic-rag`](./01-basic-rag) | Chunking → embeddings → vector search → answer. A straight line, no judgment involved. | ✅ Working |
| [`02-advanced-rag`](./02-advanced-rag) | Hybrid search, reranking, metadata filtering, query rewriting — fixing specific failure modes of pure vector search | 🚧 Scaffolded, not implemented |
| [`03-agentic-rag`](./03-agentic-rag) | Turns the straight line into a loop: retrieve → evaluate sufficiency → rewrite or answer or **abstain** | ✅ Working |

## The throughline

`01-basic-rag` answers every question the same way, whether or not it
actually has good evidence. `03-agentic-rag` is the fix for that — it
adds a judgment step and a hard-enforced retry limit, so the system can
say "I don't know" instead of guessing. `02-advanced-rag`'s techniques
(better retrieval quality) and `03-agentic-rag`'s judgment loop are
complementary, not competing — better retrieval reduces how often the
agent needs to retry or abstain in the first place.

See [`03-agentic-rag/README.md`](./03-agentic-rag/README.md) for a real
bug this surfaced — a test that failed not because the agent was wrong,
but because the test's assumption about what counts as "unanswerable"
was wrong.