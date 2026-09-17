"""
Day 8 — Step 1: Connect LangChain to Ollama

Before building any graph, confirm the LangChain wrapper around your
local Ollama model actually works. If this doesn't run cleanly, nothing
downstream will either.
"""

from langchain_ollama import ChatOllama

CHAT_MODEL = "llama3.2"  # update to match your `ollama list` output

llm = ChatOllama(
    model=CHAT_MODEL,
    temperature=0,  # deterministic output — we want repeatable behavior
                    # while we're learning the workflow, not creativity
)

if __name__ == "__main__":
    response = llm.invoke("Explain RAG in one sentence.")
    print(response.content)
