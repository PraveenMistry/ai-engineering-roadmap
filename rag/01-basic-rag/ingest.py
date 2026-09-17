"""
Day 5 — Step 1: Ingestion

Flow:
    Documents
        ↓
    Parsing
        ↓
    Chunking
        ↓
    Embeddings
        ↓
    Vector Store   (a JSON file, today — a real vector DB comes in Week 6)

Run this once (and again any time documents/ changes) to (re)build
vector_store.json. retrieve.py reads from that file; it does not
call the LLM at all.
"""

import os
import json
import glob

import ollama

DOCUMENTS_DIR = "documents"
VECTOR_STORE_PATH = "vector_store.json"
EMBEDDING_MODEL = "nomic-embed-text"  # run: ollama pull nomic-embed-text

CHUNK_SIZE = 500      # characters per chunk (kept simple — word/token-aware
                      # chunking is an Advanced RAG topic, Week 6)
CHUNK_OVERLAP = 100   # characters of overlap between consecutive chunks,
                      # so we don't cut a fact in half at a chunk boundary


def load_documents(directory: str) -> list[dict]:
    """
    Parsing step.
    Reads every .md file in the directory and returns
    [{"source": filename, "text": full_text}, ...]
    """
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
    """
    Chunking step.
    Splits text into overlapping fixed-size character windows.

    Why overlap? If a fact spans the boundary between chunk N and
    chunk N+1, a hard cut with no overlap could destroy that fact.
    Overlap means the end of one chunk repeats at the start of the next.
    """
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
    """
    Embeddings step.
    Converts a chunk of text into a vector using a local Ollama model.
    Runs entirely on your machine — no API key, no cost.
    """
    response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)
    return response["embedding"]


def build_vector_store():
    """
    Runs the full pipeline: Documents -> Parsing -> Chunking -> Embeddings -> Store
    """
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
                "source": doc["source"],
                "text": chunk,
                "embedding": embedding,
            })
            chunk_id += 1

    with open(VECTOR_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(vector_store, f)

    print(f"\nSaved {len(vector_store)} chunks with embeddings to '{VECTOR_STORE_PATH}'")


if __name__ == "__main__":
    build_vector_store()
