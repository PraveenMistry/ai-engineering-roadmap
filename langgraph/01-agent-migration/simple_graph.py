"""
Day 8 — Step 2: Your first LangGraph, built in 3 stages.

Change STAGE at the bottom of this file to 1, 2, or 3 and re-run.
Nothing here talks to real documents or real retrieval yet — that's
graph_agent.py (Step 3). The point of this file is purely to understand
LangGraph's mechanics: nodes, edges, state, and conditional routing.
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# ---------------------------------------------------------------------------
# STAGE 1:  START -> greet -> END
# ---------------------------------------------------------------------------

class GreetState(TypedDict):
    name: str
    message: str


def greet(state: GreetState) -> dict:
    print("GREET")
    return {"message": f"Hello, {state['name']}!"}


def build_stage_1():
    graph = StateGraph(GreetState)
    graph.add_node("greet", greet)
    graph.add_edge(START, "greet")
    graph.add_edge("greet", END)
    return graph.compile()


# ---------------------------------------------------------------------------
# STAGE 2:  START -> retrieve -> evaluate -> answer -> END
# (still no conditional routing — always flows straight through)
# ---------------------------------------------------------------------------

class RAGState(TypedDict):
    question: str
    search_query: str
    documents: list[str]
    attempt_count: int
    context_sufficient: bool
    answer: str
    status: str


def retrieve(state: RAGState) -> dict:
    print("RETRIEVE")
    # Real retrieval comes in graph_agent.py. For now, pretend we found something.
    return {
        "documents": ["(placeholder chunk)"],
        "attempt_count": state["attempt_count"] + 1,
    }


def evaluate_context(state: RAGState) -> dict:
    print("EVALUATE")
    # Later we'll use Ollama to actually judge this. For now, always sufficient.
    return {"context_sufficient": True}


def generate_answer(state: RAGState) -> dict:
    print("GENERATE")
    return {
        "answer": "Answer generated from retrieved context.",
        "status": "answered",
    }


def build_stage_2():
    graph = StateGraph(RAGState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("evaluate", evaluate_context)
    graph.add_node("generate", generate_answer)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "evaluate")
    graph.add_edge("evaluate", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


# ---------------------------------------------------------------------------
# STAGE 3:  Add rewrite + conditional routing + abstain
#
#   START -> retrieve -> evaluate --sufficient--> generate -> END
#                            |
#                            +--insufficient, attempts left--> rewrite -> retrieve (loop)
#                            |
#                            +--insufficient, out of attempts--> abstain -> END
# ---------------------------------------------------------------------------

MAX_RETRIES = 2


def rewrite_query(state: RAGState) -> dict:
    print("REWRITE")
    return {"search_query": "improved search query"}


def abstain(state: RAGState) -> dict:
    print("ABSTAIN")
    return {
        "answer": "I couldn't find sufficient information in the available company documents.",
        "status": "abstained",
    }


def route_after_evaluation(state: RAGState) -> str:
    """
    This function is pure Python — no LLM call. The LLM's job (in evaluate_context)
    is only to judge sufficiency. Deciding what to DO with that judgment, including
    enforcing the retry limit, belongs entirely to your application code. This is
    the exact boundary the practical calls out: the LLM doesn't control the retry
    limit — your code does.
    """
    if state["context_sufficient"]:
        return "generate"
    if state["attempt_count"] >= MAX_RETRIES:
        return "abstain"
    return "rewrite"


def build_stage_3(force_insufficient_until: int = 0):
    """
    force_insufficient_until lets us simulate evaluate_context saying
    "insufficient" for the first N attempts, purely so we can SEE the
    rewrite loop actually fire without needing a real LLM judgment yet.
    """

    def evaluate_context_stage3(state: RAGState) -> dict:
        print(f"EVALUATE (attempt {state['attempt_count']})")
        sufficient = state["attempt_count"] > force_insufficient_until
        return {"context_sufficient": sufficient}

    graph = StateGraph(RAGState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("evaluate", evaluate_context_stage3)
    graph.add_node("rewrite", rewrite_query)
    graph.add_node("generate", generate_answer)
    graph.add_node("abstain", abstain)

    graph.add_edge(START, "retrieve")
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


if __name__ == "__main__":
    STAGE = 3  # <-- change this to 1, 2, or 3

    if STAGE == 1:
        app = build_stage_1()
        result = app.invoke({"name": "there", "message": ""})
        print("\nFinal state:", result)

    elif STAGE == 2:
        app = build_stage_2()
        result = app.invoke({
            "question": "test question",
            "search_query": "",
            "documents": [],
            "attempt_count": 0,
            "context_sufficient": False,
            "answer": "",
            "status": "",
        })
        print("\nFinal state:", result)

    elif STAGE == 3:
        # Try force_insufficient_until=0 (answers immediately),
        # then =1 (rewrites once then answers),
        # then =99 (always insufficient -> should hit abstain, NOT loop forever)
        app = build_stage_3(force_insufficient_until=1)
        result = app.invoke({
            "question": "test question",
            "search_query": "initial query",
            "documents": [],
            "attempt_count": 0,
            "context_sufficient": False,
            "answer": "",
            "status": "",
        })
        print("\nFinal state:", result)
