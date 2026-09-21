"""
Day 7 — Exercise 1: Baseline retrieval (query side)

Flow:
    Question -> Ollama embedding -> Cosine similarity -> Top-K chunks

No LLM call happens here — this is pure retrieval, kept separate so
agent.py can be tested/debugged without conflating retrieval quality
with agent decision quality.
"""

import os
import json

import ollama

VECTOR_STORE_PATH = "vector_store.json"
EMBEDDING_MODEL = "nomic-embed-text"  # must match ingest.py


def load_vector_store(path: str = VECTOR_STORE_PATH) -> list[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"'{path}' not found. Run `python ingest.py` first to build it."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def embed_query(query: str) -> list[float]:
    response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=query)
    return response["embedding"]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot_product = sum(x * y for x, y in zip(a, b))
    magnitude_a = sum(x ** 2 for x in a) ** 0.5
    magnitude_b = sum(y ** 2 for y in b) ** 0.5

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def retrieve_top_k(query: str, k: int = 5) -> list[dict]:
    """
    Returns top-k chunks, each with its text, source document, and score.
    """
    vector_store = load_vector_store()
    query_embedding = embed_query(query)

    scored_chunks = []
    for chunk in vector_store:
        score = cosine_similarity(query_embedding, chunk["embedding"])
        scored_chunks.append({
            "text": chunk["text"],
            "document": chunk["metadata"]["document"],
            "score": score,
        })

    scored_chunks.sort(key=lambda c: c["score"], reverse=True)
    return scored_chunks[:k]


if __name__ == "__main__":
    test_query = "How many annual leave days do employees get?"
    results = retrieve_top_k(test_query, k=5)

    print(f"Query: {test_query}\n")
    for i, r in enumerate(results, start=1):
        print(f"#{i} | score={r['score']:.3f} | source={r['document']}")
        print(f"    {r['text'][:150]}...\n")
