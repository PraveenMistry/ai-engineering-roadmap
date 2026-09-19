"""
Day 10 — Exercise 1 (continued) + Exercise 3: PolicyAgent

Single responsibility: given already-retrieved documents, interpret
them and produce an answer for a SPECIFIC audience's perspective.

Why parameterize by audience instead of writing a separate
EmployeePolicyAgent / ContractorPolicyAgent class? Because the
reasoning logic is identical — "read this evidence, answer for this
question" — only the LENS changes (whose policy applies). This is the
same instinct as Day 7's _chat_json helper: don't duplicate a pattern
three times when a parameter does the job.

Exercise 4's failure simulation lives here too — this is deliberately
the agent we make fail, since it's the one doing the "real work" (an
LLM call), which is realistically where timeouts/failures happen in
production, not in a fast local vector search.
"""

import time

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

CHAT_MODEL = "llama3.2"  # update if your `ollama list` differs

llm = ChatOllama(model=CHAT_MODEL, temperature=0)


def build_context(chunks: list[dict]) -> str:
    parts = [f"[Source: {c['document']}]\n{c['text']}" for c in chunks]
    return "\n\n---\n\n".join(parts)


def policy_agent(
    question: str,
    documents: list[dict],
    audience: str,
    simulate_failure: bool = False,
) -> tuple[str, float]:
    """
    Returns (answer, elapsed_seconds).

    audience: "employee" or "contractor" — shapes the system prompt so
    the same underlying reasoning is applied through a specific lens.

    simulate_failure: Exercise 4 hook. Set True to force this agent to
    raise, so you can observe how the supervisor handles it — without
    needing to actually break your Ollama server to test failure paths.
    """
    start = time.time()

    if simulate_failure:
        # Exercise 4: deliberately inject a failure to test the
        # supervisor's handling, without relying on a real outage.
        raise TimeoutError(f"Simulated agent timeout ({audience} policy agent)")

    system_prompt = f"""You are a policy assistant answering specifically
from the perspective of a {audience}. Use ONLY the provided context.
Cite the source document(s). If the context doesn't address {audience}s
specifically, say so plainly rather than assuming general policy applies
to them unchanged. Be concise."""

    context = build_context(documents)
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    elapsed = time.time() - start
    return response.content, elapsed


if __name__ == "__main__":
    from research_agent import research_agent

    question = "Can contractors work remotely five days a week?"
    docs, _ = research_agent(question)
    answer, seconds = policy_agent(question, docs, audience="contractor")

    print(f"Answer ({seconds:.2f}s):\n{answer}")
