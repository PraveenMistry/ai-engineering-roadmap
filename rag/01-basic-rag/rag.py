"""
Day 5 — Step 3: RAG (Retrieval-Augmented Generation)

Flow:
    Question
        ↓
    Retrieval (retrieve.py)
        ↓
    Context
        ↓
    LLM
        ↓
    Answer (with cited source)

This is the file that ties everything together. Nothing about
ingest.py or retrieve.py changes here — RAG is just "retrieval,
then hand the results to the LLM as context."
"""

import ollama

from retrieve import retrieve_top_k

CHAT_MODEL = "llama3.2"  # run: ollama pull llama3.2
TOP_K = 3

SYSTEM_PROMPT = """You are a company knowledge assistant. Answer the user's
question using ONLY the context provided below. Each piece of context is
labeled with its source document.

Rules:
- Cite the source document(s) you used in your answer.
- If the context does not contain enough information to answer confidently,
  say so explicitly — do NOT guess or make up an answer.
- Keep answers concise and direct.
"""


def build_context(chunks: list[dict]) -> str:
    """
    Formats retrieved chunks into a single context block, each one
    labeled with its source so the LLM (and the user) can trace
    where an answer came from.
    """
    parts = []
    for chunk in chunks:
        parts.append(f"[Source: {chunk['source']}]\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)


def ask(question: str, k: int = TOP_K) -> str:
    """
    The full RAG pipeline for a single question.
    """
    retrieved_chunks = retrieve_top_k(question, k=k)
    context = build_context(retrieved_chunks)

    user_message = f"""Context:
{context}

Question: {question}"""

    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    return response["message"]["content"]


def main():
    print("Company Knowledge Assistant — type 'exit' to quit\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        answer = ask(question)
        print(f"\nAssistant: {answer}\n")


if __name__ == "__main__":
    main()
