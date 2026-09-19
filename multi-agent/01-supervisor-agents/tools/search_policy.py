"""
Day 10 — Shared retrieval tool.

This is a "tool" in the agentic sense: a plain function agents call to
interact with the world outside the LLM. Reuses the exact retrieval
logic from Day 7/8 — nothing about vector search changes when you go
from a single agent to multiple agents. Only the orchestration around
it changes.
"""

import os
import json

import ollama

VECTOR_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "vector_store.json")
EMBEDDING_MODEL = "nomic-embed-text"


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


def search_policy(query: str, k: int = 5) -> list[dict]:
    """
    The tool. Given a query, returns the top-k most relevant chunks,
    each with its text, source document, and similarity score.
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
