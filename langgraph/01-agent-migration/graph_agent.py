"""
Day 8 — Step 3: Enterprise Policy Agent, migrated to LangGraph

This is Day 7's exact agent logic (decide query -> retrieve -> evaluate ->
rewrite/generate/abstain), reusing the SAME retrieve.py you already had.
What changed is only the orchestration layer:

    Day 7:  a hand-written `while` loop with manual attempt counting
    Day 8:  a LangGraph StateGraph with explicit state + conditional edges

The retrieval, evaluation, and generation logic itself is unchanged —
that's the point. We didn't rebuild the agent, we re-plumbed it.
"""

import json
from typing import TypedDict

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from retrieve import retrieve_top_k

CHAT_MODEL = "llama3.2"  # update if your `ollama list` differs
MAX_RETRIES = 2
TOP_K = 5

# Two LLM instances: one constrained to JSON output (decisions/evaluation),
# one plain (final answer generation, where we want natural prose).
llm_json = ChatOllama(model=CHAT_MODEL, temperature=0, format="json")
llm = ChatOllama(model=CHAT_MODEL, temperature=0)


class RAGState(TypedDict):
    question: str
    search_query: str
    documents: list[dict]
    attempt_count: int
    context_sufficient: bool
    evaluation_reason: str
    answer: str
    status: str
    queries_used: list[str]
    documents_retrieved: list[str]


def _invoke_json(system_prompt: str, user_prompt: str) -> dict:
    """Same fail-safe JSON parsing pattern as Day 7's agent.py, just
    wired through LangChain's message format instead of raw ollama.chat."""
    response = llm_json.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        return {}


def build_context(chunks: list[dict]) -> str:
    parts = [f"[Source: {c['document']}]\n{c['text']}" for c in chunks]
    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# Nodes — each one takes the current state, returns a partial state update
# ---------------------------------------------------------------------------

def decide_query(state: RAGState) -> dict:
    print("DECIDE QUERY")
    system_prompt = """You are a search query planner for a company policy
knowledge base. Focus on the underlying information the person needs, not
literal surface wording — questions are sometimes phrased as confirmations
or rhetorical follow-ups. Respond ONLY with JSON:
{"query": "<your search query>"}"""

    parsed = _invoke_json(system_prompt, state["question"])
    query = parsed.get("query", state["question"])
    return {
        "search_query": query,
        "queries_used": [query],
        "attempt_count": 0,
    }


def retrieve(state: RAGState) -> dict:
    print(f"RETRIEVE (attempt {state['attempt_count'] + 1}) query='{state['search_query']}'")
    chunks = retrieve_top_k(state["search_query"], k=TOP_K)
    new_docs = [c["document"] for c in chunks]
    existing_docs = state.get("documents_retrieved", [])
    return {
        "documents": chunks,
        "attempt_count": state["attempt_count"] + 1,
        "documents_retrieved": sorted(set(existing_docs) | set(new_docs)),
    }


def evaluate_context(state: RAGState) -> dict:
    print("EVALUATE")
    system_prompt = """You evaluate whether retrieved context contains
sufficient evidence to confidently answer a question. Be strict. The
question may be phrased as a confirmation or doubt — judge sufficiency
based on whether the context lets you give a substantive factual answer,
even if it contradicts the question's premise. Respond ONLY with JSON:
{"sufficient": true or false, "reason": "<short explanation>"}"""

    context = build_context(state["documents"])
    user_prompt = f"Question: {state['question']}\n\nContext:\n{context}"
    parsed = _invoke_json(system_prompt, user_prompt)

    if "sufficient" not in parsed:
        parsed = {"sufficient": False, "reason": "Evaluator response could not be parsed."}

    return {
        "context_sufficient": parsed["sufficient"],
        "evaluation_reason": parsed["reason"],
    }


def rewrite_query(state: RAGState) -> dict:
    print("REWRITE")
    system_prompt = """The previous search query did not retrieve enough
evidence. Rewrite it using the evaluator's explanation of what was
missing. Respond ONLY with JSON: {"query": "<rewritten search query>"}"""

    user_prompt = f"""Original question: {state['question']}
Previous query: {state['search_query']}
Why it wasn't enough: {state['evaluation_reason']}"""

    parsed = _invoke_json(system_prompt, user_prompt)
    new_query = parsed.get("query", state["search_query"])
    return {
        "search_query": new_query,
        "queries_used": state["queries_used"] + [new_query],
    }


def generate_answer(state: RAGState) -> dict:
    print("GENERATE")
    system_prompt = """You are a company policy assistant. Answer using
ONLY the provided context. Cite the source document(s). Be concise."""

    context = build_context(state["documents"])
    user_prompt = f"Context:\n{context}\n\nQuestion: {state['question']}"

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    return {"answer": response.content, "status": "answered"}


def abstain(state: RAGState) -> dict:
    print("ABSTAIN")
    return {
        "answer": (
            "I don't have enough information in the knowledge base to "
            "answer this confidently. This may not be covered by our "
            "current policy documents."
        ),
        "status": "abstained",
    }


# ---------------------------------------------------------------------------
# Routing — pure Python, no LLM call. This is the boundary that matters:
# the LLM only ever judges sufficiency. Your code decides what happens
# next, including hard-enforcing MAX_RETRIES.
# ---------------------------------------------------------------------------

def route_after_evaluation(state: RAGState) -> str:
    if state["context_sufficient"]:
        return "generate"
    if state["attempt_count"] >= MAX_RETRIES + 1:
        return "abstain"
    return "rewrite"


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(RAGState)

    graph.add_node("decide_query", decide_query)
    graph.add_node("retrieve", retrieve)
    graph.add_node("evaluate", evaluate_context)
    graph.add_node("rewrite", rewrite_query)
    graph.add_node("generate", generate_answer)
    graph.add_node("abstain", abstain)

    graph.add_edge(START, "decide_query")
    graph.add_edge("decide_query", "retrieve")
    graph.add_edge("retrieve", "evaluate")
    graph.add_conditional_edges(
        "evaluate",
        route_after_evaluation,
        {
            "generate": "generate",
            "rewrite": "rewrite",
            "abstain": "abstain",
        },
    )
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("generate", END)
    graph.add_edge("abstain", END)

    return graph.compile()


app = build_graph()


def answer_question(question: str) -> dict:
    initial_state: RAGState = {
        "question": question,
        "search_query": "",
        "documents": [],
        "attempt_count": 0,
        "context_sufficient": False,
        "evaluation_reason": "",
        "answer": "",
        "status": "",
        "queries_used": [],
        "documents_retrieved": [],
    }
    return app.invoke(initial_state)


def main():
    print("Enterprise Policy Agent (LangGraph) — type 'exit' to quit\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        result = answer_question(question)

        print(f"\nAgent: {result['answer']}\n")
        print(f"status={result['status']}  attempts={result['attempt_count']}  "
              f"queries={result['queries_used']}  docs={result['documents_retrieved']}\n")


if __name__ == "__main__":
    main()
