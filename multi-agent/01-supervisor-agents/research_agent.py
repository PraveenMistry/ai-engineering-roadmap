"""
Day 10 — Exercise 1: ResearchAgent

Single responsibility: retrieve relevant documents for a query. That's it.
It does NOT interpret them, judge sufficiency, or generate an answer —
that's PolicyAgent's job. This split matters for the same reason Day 7
kept retrieval and evaluation as separate functions: you want to be able
to test and debug "did we find the right documents?" completely
independently of "did we reason about them correctly?"
"""

import time

from tools.search_policy import search_policy


def research_agent(query: str) -> tuple[list[dict], float]:
    """
    Returns (documents, elapsed_seconds). Timing is returned here
    rather than measured externally so it's accurate to just this
    agent's work, not anything wrapping it.
    """
    start = time.time()
    documents = search_policy(query, k=5)
    elapsed = time.time() - start
    return documents, elapsed


if __name__ == "__main__":
    # Quick standalone test — confirm this agent works BEFORE wiring it
    # into anything else. Same philosophy as Day 5's retrieve.py.
    docs, seconds = research_agent("How many annual leave days do employees get?")
    print(f"Retrieved {len(docs)} documents in {seconds:.2f}s\n")
    for d in docs:
        print(f"  [{d['document']}] score={d['score']:.3f}")
        print(f"    {d['text'][:100]}...\n")
