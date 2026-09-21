"""
Day 11 — Exercise 1: MCP Server

Deliberately simple: plain keyword search over local .md files. No LLM,
no embeddings, no vector store. The point of today isn't retrieval
quality — it's understanding the MCP protocol boundary itself, without
AI complexity muddying what's actually happening under the hood.

Uses the official MCP Python SDK's FastMCP helper, which handles the
protocol plumbing (tool registration, schema generation, stdio
transport) so this file only needs to define what the tool actually does.
"""

import os
import re

from mcp.server.fastmcp import FastMCP

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

mcp = FastMCP("policy-search-server")


def load_documents() -> dict[str, str]:
    documents = {}
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".md"):
            with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
                documents[filename] = f.read()
    return documents


def keyword_search(query: str, documents: dict[str, str], max_results: int = 3) -> list[dict]:
    """
    Splits each document into paragraphs, scores each paragraph by how
    many query words it contains, returns the top matches. This is
    intentionally naive — no stemming, no semantic understanding. It's
    just enough to prove the protocol works end to end before we
    reconnect it to something smarter later.
    """
    query_words = set(query.lower().split())
    scored = []

    for filename, text in documents.items():
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for paragraph in paragraphs:
            paragraph_words = set(re.findall(r"\w+", paragraph.lower()))
            overlap = len(query_words & paragraph_words)
            if overlap > 0:
                scored.append({"document": filename, "content": paragraph, "score": overlap})

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:max_results]


@mcp.tool()
def search_policy(query: str) -> dict:
    """
    Search company policy documents (leave, remote work, contractor
    policy) for content relevant to the given query.

    Args:
        query: what to search for, e.g. "remote work" or "annual leave"
    """
    documents = load_documents()
    matches = keyword_search(query, documents)
    return {
        "results": [
            {"document": m["document"], "content": m["content"]}
            for m in matches
        ]
    }


if __name__ == "__main__":
    mcp.run()
