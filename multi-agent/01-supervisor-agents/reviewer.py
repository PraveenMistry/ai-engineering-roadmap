"""
Day 10 — Reviewer / Synthesizer

Two related jobs, deliberately kept in one file because they're the
same underlying operation: "take one or more draft answers and produce
the final response the user sees."

  - review_answer():    one input -> lightly quality-checked output
  - synthesize_answers(): two independent inputs -> one combined output
                           (Exercise 3's parallel-execution path)

This mirrors the Planner -> Executor -> Critic pattern from the
roadmap: PolicyAgent(s) are the Executor(s), this file is the Critic /
final-assembly stage.
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

CHAT_MODEL = "llama3.2"
llm = ChatOllama(model=CHAT_MODEL, temperature=0)


def review_answer(question: str, draft_answer: str) -> str:
    """
    Single-agent path. A light pass, not a rewrite — mainly checking
    the answer actually addresses the question and didn't drift.
    """
    system_prompt = """You review draft answers for clarity and
relevance before they reach the user. If the draft is already clear,
concise, and directly answers the question, return it UNCHANGED. Only
edit if there's a real problem (unclear, off-topic, or missing a
citation)."""

    user_prompt = f"Question: {question}\n\nDraft answer:\n{draft_answer}"

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    return response.content


def synthesize_answers(question: str, employee_answer: str, contractor_answer: str) -> str:
    """
    Multi-agent path (Exercise 3). Combines two independently-produced
    answers into one coherent comparison. This is a genuinely different
    task from review_answer — it has to reconcile two perspectives, not
    just polish one.
    """
    system_prompt = """You combine two independent policy answers — one
from an employee's perspective, one from a contractor's — into a single
clear comparison that directly answers the original question. Preserve
the specific facts and citations from both. Make the difference between
the two explicit."""

    user_prompt = f"""Original question: {question}

Employee perspective:
{employee_answer}

Contractor perspective:
{contractor_answer}"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    return response.content


def partial_answer_notice(available_audience: str, failed_audience: str, available_answer: str) -> str:
    """
    Exercise 4's fallback path. Used when one branch of a comparison
    fails — see README for why "partial answer with clear disclosure"
    was chosen over retry/abort/fallback-model/human-approval here.
    """
    return (
        f"I could only retrieve {available_audience} policy information — "
        f"the {failed_audience} lookup failed and couldn't be completed. "
        f"Here's what I found for {available_audience}s:\n\n{available_answer}\n\n"
        f"Please ask again if you specifically need the {failed_audience} side, "
        f"or contact HR directly for a complete comparison right now."
    )
