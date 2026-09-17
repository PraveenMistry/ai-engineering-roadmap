"""
Day 7 — Exercises 2-6: The Enterprise Policy Agent

Flow:
    Question
       |
    Agent decides search query        (Exercise 2)
       |
    Search                             (Exercise 1's retrieve.py)
       |
    Evaluate: sufficient evidence?    (Exercise 3)
       |-- yes --> Answer
       |-- no  --> Rewrite query      (Exercise 4)
                       |
                   Search again (up to MAX_RETRIES)
                       |
                   Still insufficient --> ABSTAIN   (Exercise 5)

Every call logs structured data for observability.               (Exercise 6)

IMPORTANT: the LLM never touches the vector database directly. It only
ever returns JSON describing what it wants to do ({"action": "search",
"query": ...}) or a judgment ({"sufficient": true/false}). This code is
what actually executes searches and enforces retry limits.
"""

import json
import time
import uuid

import ollama

from retrieve import retrieve_top_k

CHAT_MODEL = "llama3.2"  # update if your `ollama list` differs
MAX_RETRIES = 2          # total attempts = 1 initial + MAX_RETRIES rewrites
TOP_K = 5


def _chat_json(system_prompt: str, user_prompt: str) -> tuple[dict, int]:
    """
    Calls the LLM and parses its response as JSON.
    Returns (parsed_dict, total_tokens_used).

    Centralizing this in one place means every structured-output call
    (Exercise 2's decision, Exercise 3's evaluation, Exercise 4's rewrite)
    shares the same parsing + fallback behavior instead of three separate
    copies of "try to parse JSON, hope for the best."
    """
    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        format="json",  # ask Ollama to constrain output to valid JSON
    )

    content = response["message"]["content"]
    tokens = response.get("eval_count", 0) + response.get("prompt_eval_count", 0)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        # If the model still returns something unparseable, fail safe
        # rather than crashing the whole agent loop.
        parsed = {}

    return parsed, tokens


# ---------------------------------------------------------------------------
# Exercise 2 — Agent decides the search query
# ---------------------------------------------------------------------------

def decide_search_query(question: str) -> tuple[str, int]:
    system_prompt = """You are a search query planner for a company policy
knowledge base. Given a user's question, produce the best possible search
query to retrieve relevant policy documents.

Focus on the underlying information the person actually needs, not the
literal surface wording. Questions are sometimes phrased as confirmations,
rhetorical questions, or casual follow-ups (e.g. "do you mean there's no
parental leave policy?" or "wait, really?") — in these cases, search for
the topic itself (e.g. "parental leave entitlement"), not for the
phrasing of the doubt or confirmation.

Respond ONLY with JSON in this exact shape:
{"action": "search", "query": "<your search query>"}
"""
    parsed, tokens = _chat_json(system_prompt, question)
    query = parsed.get("query", question)  # fall back to raw question if parsing fails
    return query, tokens


# ---------------------------------------------------------------------------
# Exercise 3 — Context evaluation
# ---------------------------------------------------------------------------

def evaluate_context(question: str, context: str) -> tuple[dict, int]:
    system_prompt = """You evaluate whether retrieved context contains
sufficient evidence to confidently answer a question. Be strict: if the
context only partially addresses the question, or doesn't mention it at
all, say insufficient.

The question may be phrased as a confirmation, doubt, or rhetorical
follow-up (e.g. "do you mean there's no parental leave policy?"). In
these cases, judge sufficiency based on whether the context lets you
give a factual, substantive answer about the underlying topic — even if
that answer contradicts the premise of the question (e.g. the context
proving a policy DOES exist is sufficient evidence, even though the
question implied it might not).

Respond ONLY with JSON in this exact shape:
{"sufficient": true or false, "reason": "<short explanation>"}
"""
    user_prompt = f"Question: {question}\n\nContext:\n{context}"
    parsed, tokens = _chat_json(system_prompt, user_prompt)

    # Fail safe: if parsing fails, treat as insufficient rather than
    # silently proceeding to answer on unverified evidence.
    if "sufficient" not in parsed:
        parsed = {"sufficient": False, "reason": "Evaluator response could not be parsed."}

    return parsed, tokens


# ---------------------------------------------------------------------------
# Exercise 4 — Query rewriting
# ---------------------------------------------------------------------------

def rewrite_query(question: str, previous_query: str, reason: str) -> tuple[str, int]:
    system_prompt = """The previous search query did not retrieve enough
evidence to answer the user's question. Rewrite the search query to be
more likely to find the missing information, using the evaluator's
explanation of what was missing.

Respond ONLY with JSON in this exact shape:
{"action": "search", "query": "<rewritten search query>"}
"""
    user_prompt = f"""Original question: {question}
Previous query: {previous_query}
Why it wasn't enough: {reason}"""

    parsed, tokens = _chat_json(system_prompt, user_prompt)
    new_query = parsed.get("query", previous_query)
    return new_query, tokens


# ---------------------------------------------------------------------------
# Final answer generation (only called once evidence is judged sufficient)
# ---------------------------------------------------------------------------

def generate_answer(question: str, context: str) -> tuple[str, int]:
    system_prompt = """You are a company policy assistant. Answer the
question using ONLY the provided context. Cite the source document(s)
in your answer. Be concise."""

    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    tokens = response.get("eval_count", 0) + response.get("prompt_eval_count", 0)
    return response["message"]["content"], tokens


def build_context(chunks: list[dict]) -> str:
    parts = [f"[Source: {c['document']}]\n{c['text']}" for c in chunks]
    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# Exercises 5 & 6 — The full loop: answer, abstain, and log everything
# ---------------------------------------------------------------------------

def answer_question(question: str) -> dict:
    """
    Runs the full agent loop for a single question.
    Returns a dict with the answer AND the structured log record —
    exactly what Exercise 6 asks for.
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    queries_used = []
    documents_retrieved = set()
    evaluations = []  # NEW: track every attempt's evaluator verdict + reason
    total_tokens = 0
    answer = None
    final_status = "error"

    query, tokens = decide_search_query(question)
    total_tokens += tokens

    attempt = 0
    while attempt <= MAX_RETRIES:
        attempt += 1
        queries_used.append(query)

        chunks = retrieve_top_k(query, k=TOP_K)
        for c in chunks:
            documents_retrieved.add(c["document"])
        context = build_context(chunks)

        evaluation, tokens = evaluate_context(question, context)
        total_tokens += tokens
        evaluations.append({
            "attempt": attempt,
            "query": query,
            "sufficient": evaluation.get("sufficient"),
            "reason": evaluation.get("reason"),
        })

        if evaluation.get("sufficient"):
            answer, tokens = generate_answer(question, context)
            total_tokens += tokens
            final_status = "answered"
            break

        if attempt <= MAX_RETRIES:
            query, tokens = rewrite_query(question, query, evaluation.get("reason", ""))
            total_tokens += tokens
        else:
            answer = (
                "I don't have enough information in the knowledge base to "
                "answer this confidently. This may not be covered by our "
                "current policy documents."
            )
            final_status = "abstained"

    latency = round(time.time() - start_time, 2)

    log_record = {
        "request_id": request_id,
        "question": question,
        "retrieval_attempts": attempt,
        "queries_used": queries_used,
        "evaluations": evaluations,
        "documents_retrieved": sorted(documents_retrieved),
        "latency_seconds": latency,
        "model": CHAT_MODEL,
        "total_tokens": total_tokens,
        "final_status": final_status,
    }

    return {"answer": answer, "log": log_record}


def main():
    print("Enterprise Policy Agent — type 'exit' to quit\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        result = answer_question(question)

        print(f"\nAgent: {result['answer']}\n")
        print("--- log ---")
        print(json.dumps(result["log"], indent=2))
        print()


if __name__ == "__main__":
    main()
