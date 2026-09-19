"""
Day 10 — Exercises 2, 3, 4: Supervisor

The supervisor's job, and ONLY its job:
  1. Classify which audience(s) a question needs (Exercise 2)
  2. Route to the right agent(s), running independent ones in parallel
     when possible (Exercise 3)
  3. Decide what happens when an agent fails (Exercise 4)

Same principle as Day 7/8's routing function: classification and
failure-handling decisions live in plain code wherever possible. The
ONE place an LLM is involved in routing is classify_audiences() below,
because "does this question concern employees, contractors, or both"
genuinely requires language understanding — a plain keyword check would
misclassify constantly (e.g. "Can I work from home?" doesn't say
"employee" anywhere).
"""

import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from research_agent import research_agent
from policy_agent import policy_agent
from reviewer import review_answer, synthesize_answers, partial_answer_notice

CHAT_MODEL = "llama3.2"
llm_json = ChatOllama(model=CHAT_MODEL, temperature=0, format="json")


# ---------------------------------------------------------------------------
# Exercise 2 — Supervisor's classification step ("Choose Agent")
# ---------------------------------------------------------------------------

def classify_audiences(question: str) -> list[str]:
    """
    Decides whether a question needs the employee lens, the contractor
    lens, or both (a comparison question). This is the ONLY LLM call in
    the supervisor — everything else below is plain Python control flow.
    """
    system_prompt = """Classify which audience(s) this policy question
concerns. Respond ONLY with JSON:
{"audiences": ["employee"]} or {"audiences": ["contractor"]} or
{"audiences": ["employee", "contractor"]} if it explicitly compares or
concerns both."""

    response = llm_json.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=question),
    ])

    try:
        parsed = json.loads(response.content)
        audiences = parsed.get("audiences", ["employee"])
    except json.JSONDecodeError:
        audiences = ["employee"]  # safe default rather than crashing

    return audiences


# ---------------------------------------------------------------------------
# Single-audience path (Exercise 2's two test questions)
# ---------------------------------------------------------------------------

def run_single_agent(question: str, audience: str, simulate_failure: bool = False) -> dict:
    """
    Returns a dict with answer, status, and a log entry — used both for
    the simple single-audience path and as a building block for the
    parallel comparison path below.
    """
    log_entry = {"agent": f"{audience}_policy_agent"}

    try:
        docs, research_seconds = research_agent(question)
        answer, policy_seconds = policy_agent(
            question, docs, audience=audience, simulate_failure=simulate_failure
        )
        log_entry["seconds"] = round(research_seconds + policy_seconds, 2)
        log_entry["outcome"] = "success"
        return {"answer": answer, "status": "success", "log": log_entry}

    except TimeoutError as e:
        log_entry["outcome"] = "failed"
        log_entry["error"] = str(e)
        return {"answer": None, "status": "failed", "log": log_entry, "error": str(e)}


def answer_single_audience(question: str, audience: str) -> dict:
    request_id = str(uuid.uuid4())[:8]
    start = time.time()

    result = run_single_agent(question, audience)

    if result["status"] == "failed":
        # No partial data possible here — there's only one source of
        # truth and it failed. Abstain honestly rather than guess.
        final_answer = (
            "I wasn't able to retrieve policy information to answer this "
            "right now due to a system error. Please try again shortly."
        )
        status = "error"
    else:
        final_answer = review_answer(question, result["answer"])
        status = "answered"

    return {
        "request_id": request_id,
        "selected_agent": f"{audience}_policy_agent",
        "execution_time": round(time.time() - start, 2),
        "result": final_answer,
        "status": status,
        "execution_log": [result["log"]],
    }


# ---------------------------------------------------------------------------
# Exercise 3 — Parallel execution for comparison questions
# ---------------------------------------------------------------------------

def answer_comparison(
    question: str,
    mode: str = "parallel",
    simulate_failure_in: str | None = None,
) -> dict:
    """
    mode: "parallel" (real usage) or "sequential" (for the benchmark
    comparison Exercise 3 asks for). simulate_failure_in: "employee",
    "contractor", or None — Exercise 4's failure injection.
    """
    request_id = str(uuid.uuid4())[:8]
    start = time.time()

    fail_employee = simulate_failure_in == "employee"
    fail_contractor = simulate_failure_in == "contractor"

    if mode == "sequential":
        employee_result = run_single_agent(question, "employee", fail_employee)
        contractor_result = run_single_agent(question, "contractor", fail_contractor)
    else:  # parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            employee_future = executor.submit(run_single_agent, question, "employee", fail_employee)
            contractor_future = executor.submit(run_single_agent, question, "contractor", fail_contractor)
            employee_result = employee_future.result()
            contractor_result = contractor_future.result()

    execution_log = [employee_result["log"], contractor_result["log"]]

    # ---- Exercise 4's failure-handling decision lives here ----
    # See README for why "partial answer with clear disclosure" was
    # chosen over retry / full fallback model / full abort / human approval.
    if employee_result["status"] == "success" and contractor_result["status"] == "success":
        final_answer = synthesize_answers(question, employee_result["answer"], contractor_result["answer"])
        status = "answered"
    elif employee_result["status"] == "success" and contractor_result["status"] == "failed":
        final_answer = partial_answer_notice("employee", "contractor", employee_result["answer"])
        status = "partial"
    elif contractor_result["status"] == "success" and employee_result["status"] == "failed":
        final_answer = partial_answer_notice("contractor", "employee", contractor_result["answer"])
        status = "partial"
    else:
        final_answer = (
            "I wasn't able to retrieve policy information for either "
            "employees or contractors right now due to a system error. "
            "Please try again shortly."
        )
        status = "error"

    return {
        "request_id": request_id,
        "selected_agents": ["employee_policy_agent", "contractor_policy_agent"],
        "mode": mode,
        "execution_time": round(time.time() - start, 2),
        "result": final_answer,
        "status": status,
        "execution_log": execution_log,
    }


# ---------------------------------------------------------------------------
# Top-level entry point — Exercise 2's full Supervisor flow
# ---------------------------------------------------------------------------

def answer_question(question: str, simulate_failure_in: str | None = None) -> dict:
    audiences = classify_audiences(question)

    if len(audiences) > 1:
        return answer_comparison(question, mode="parallel", simulate_failure_in=simulate_failure_in)
    else:
        audience = audiences[0]
        fail = simulate_failure_in == audience
        if fail:
            # Reuse the single-audience path but inject failure manually,
            # since answer_single_audience doesn't take the flag directly.
            result = run_single_agent(question, audience, simulate_failure=True)
            return {
                "request_id": str(uuid.uuid4())[:8],
                "selected_agent": f"{audience}_policy_agent",
                "execution_time": result["log"].get("seconds", 0),
                "result": "I wasn't able to retrieve policy information to answer this right now due to a system error. Please try again shortly.",
                "status": "error",
                "execution_log": [result["log"]],
            }
        return answer_single_audience(question, audience)


def benchmark_comparison(question: str):
    """
    Exercise 3's sequential vs parallel measurement. Not meant to be
    rigorous benchmarking — just enough to SEE the architectural
    difference, as the exercise says.
    """
    print(f"Question: {question}\n")

    print("Running SEQUENTIAL...")
    seq_result = answer_comparison(question, mode="sequential")
    print(f"  Sequential total: {seq_result['execution_time']}s")

    print("\nRunning PARALLEL...")
    par_result = answer_comparison(question, mode="parallel")
    print(f"  Parallel total: {par_result['execution_time']}s")

    print(f"\nDifference: {seq_result['execution_time'] - par_result['execution_time']:.2f}s saved with parallel execution")


def main():
    print("Enterprise Policy Agent — Multi-Agent (Supervisor) — type 'exit' to quit\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        result = answer_question(question)
        print(f"\nAgent: {result['result']}\n")
        print(json.dumps(result, indent=2, default=str))
        print()


if __name__ == "__main__":
    main()
