"""
Day 5 — Step 2: Retrieval

Flow:
    Vector Store
        ↓
    (query gets embedded the same way chunks were)
        ↓
    Similarity search
        ↓
    Top-k relevant chunks

This file does NOT talk to the LLM. It only answers the question:
"given this query, which stored chunks are most relevant?"
That separation matters — you can test/debug retrieval quality on its
own, without an LLM call muddying whether a bad answer was a retrieval
problem or a generation problem. This distinction becomes very important
in Week 13 (Evaluation).
"""

import os
import json

import ollama

VECTOR_STORE_PATH = "vector_store.json"
EMBEDDING_MODEL = "nomic-embed-text"  # must match the model used in ingest.py


def load_vector_store(path: str = VECTOR_STORE_PATH) -> list[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"'{path}' not found. Run `python ingest.py` first to build it."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def embed_query(query: str) -> list[float]:
    """Embeds the user's question with the SAME model used for chunks.
    This matters: query and chunk embeddings must live in the same
    vector space to be comparable."""
    response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=query)
    return response["embedding"]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Measures how similar two vectors are, from -1 (opposite) to 1 (identical).
    This is the "semantic search" math underneath every vector DB.
    """
    dot_product = sum(x * y for x, y in zip(a, b))
    magnitude_a = sum(x ** 2 for x in a) ** 0.5
    magnitude_b = sum(y ** 2 for y in b) ** 0.5

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def retrieve_top_k(query: str, k: int = 3) -> list[dict]:
    """
    Full retrieval step:
      1. embed the query
      2. score every stored chunk against it
      3. return the top-k highest scoring chunks
    """
    vector_store = load_vector_store()
    query_embedding = embed_query(query)

    scored_chunks = []
    for chunk in vector_store:
        score = cosine_similarity(query_embedding, chunk["embedding"])
        scored_chunks.append({
            "source": chunk["source"],
            "text": chunk["text"],
            "score": score,
        })

    scored_chunks.sort(key=lambda c: c["score"], reverse=True)
    return scored_chunks[:k]


if __name__ == "__main__":
    # Quick manual test — run this file directly to sanity-check retrieval
    # BEFORE plugging it into the LLM in rag.py.
    test_query = "How many days of parental leave do I get?"
    results = retrieve_top_k(test_query, k=3)

    print(f"Query: {test_query}\n")
    for i, r in enumerate(results, start=1):
        print(f"#{i} | score={r['score']:.3f} | source={r['source']}")
        print(f"    {r['text'][:150]}...\n")
