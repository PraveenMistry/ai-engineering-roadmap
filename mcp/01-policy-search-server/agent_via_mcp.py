"""
Day 11 — Exercise 3: Agent connected through the MCP protocol boundary

Before (Day 10 - multi-agent):  Agent -> Python function -> vector search
                   (policy_agent.py called tools/search_policy.py
                   directly, in the same process)

Now:               Agent -> MCP Client -> MCP Server -> search_policy()
                   -> documents -> back to Agent

The interpretation step (the LLM call) is UNCHANGED from Day 10 —
only retrieval moved behind a protocol boundary. That's the whole
point of MCP: the search capability could now run on a different
machine, be written in a different language, or get swapped for a
completely different implementation (e.g. Day 10's real embeddings
search instead of today's naive keyword search) — and this agent code
would not need to change AT ALL, because it only knows about the tool's
name and its input/output shape, not how it works internally.
"""

import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

SERVER_SCRIPT = "mcp_server.py"
CHAT_MODEL = "llama3.2"  # update if your `ollama list` differs

llm = ChatOllama(model=CHAT_MODEL, temperature=0)


async def search_via_mcp(query: str) -> list[dict]:
    """Same job as Day 10's research_agent() — but retrieval now
    happens through the MCP protocol instead of a direct function call."""
    server_params = StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("search_policy", arguments={"query": query})

            for content_block in result.content:
                if content_block.type == "text":
                    parsed = json.loads(content_block.text)
                    return parsed.get("results", [])
    return []


def generate_answer(question: str, documents: list[dict]) -> str:
    """Same job as Day 10's policy_agent() interpretation step —
    unchanged, because only the retrieval side moved."""
    if not documents:
        return "I couldn't find any relevant policy information for this question."

    context = "\n\n---\n\n".join(
        f"[Source: {d['document']}]\n{d['content']}" for d in documents
    )
    system_prompt = """You are a company policy assistant. Answer using
ONLY the provided context. Cite the source document(s). Be concise. If
the context doesn't address the question, say so."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {question}"),
    ])
    return response.content


async def answer_question(question: str) -> str:
    documents = await search_via_mcp(question)
    return generate_answer(question, documents)


async def main():
    print("Policy Agent (via MCP) — type 'exit' to quit\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        answer = await answer_question(question)
        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    asyncio.run(main())
