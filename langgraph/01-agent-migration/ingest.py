"""
Day 7 — Exercise 1: Baseline retrieval (ingestion side)

Flow:
    Documents -> Parsing -> Chunking -> Embeddings -> Vector Store

Same as Day 5/6, with one addition: every stored chunk now carries a
`metadata` block (which document it came from). We're not filtering on
it yet — the agent uses it in Exercise 6's logging (`documents_retrieved`)
and it's there for future metadata filtering work.
"""

import os
import json
import glob

import ollama

DOCUMENTS_DIR = "documents"
VECTOR_STORE_PATH = "vector_store.json"
EMBEDDING_MODEL = "nomic-embed-text"  # update if your `ollama list` differs

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def load_documents(directory: str) -> list[dict]:
    documents = []
    for filepath in glob.glob(os.path.join(directory, "*.md")):
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        documents.append({
            "source": os.path.basename(filepath),
            "text": text,
        })
    return documents


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def embed_text(text: str) -> list[float]:
    response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)
    return response["embedding"]


def build_vector_store():
    documents = load_documents(DOCUMENTS_DIR)
    print(f"Loaded {len(documents)} document(s) from '{DOCUMENTS_DIR}/'")

    vector_store = []
    chunk_id = 0

    for doc in documents:
        chunks = chunk_text(doc["text"])
        print(f"  {doc['source']}: split into {len(chunks)} chunk(s)")

        for chunk in chunks:
            embedding = embed_text(chunk)
            vector_store.append({
                "id": chunk_id,
                "text": chunk,
                "embedding": embedding,
                "metadata": {
                    "document": doc["source"],
                },
            })
            chunk_id += 1

    with open(VECTOR_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(vector_store, f)

    print(f"\nSaved {len(vector_store)} chunks with embeddings to '{VECTOR_STORE_PATH}'")


if __name__ == "__main__":
    build_vector_store()
