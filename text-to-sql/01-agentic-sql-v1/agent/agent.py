"""
Day 15 — The full Agentic Text-to-SQL pipeline

    Question
       |
    Schema Retrieval
       |
    SQL Generation
       |
    Validation ----fail----> Refinement (feed error back) --> Generation (retry)
       |success
    Execution ----fail----> Refinement (feed error back) --> Generation (retry)
       |success
    Natural-language Answer

MAX_RETRIES is enforced in code, never left to the model to "decide"
when to stop trying — same non-negotiable principle as every retry
loop in this entire program (Day 7's rewrite loop, Day 12's failure
handling, Day 13's bounded evaluation attempts).
"""

import json
import time

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from schema_retriever import build_schema_context
from sql_generator import generate_sql
from sql_validator import validate_sql
from executor import execute_query

CHAT_MODEL = "llama3.2"
MAX_RETRIES = 2  # total attempts = 1 initial + 2 refinements

llm = ChatOllama(model=CHAT_MODEL, temperature=0)


def answer_in_natural_language(question: str, sql: str, columns: list, rows: list) -> str:
    system_prompt = """You explain SQL query results in plain, concise
natural language. State the actual numbers/values from the results —
never invent numbers not present in the data given to you."""

    result_preview = json.dumps({"columns": columns, "rows": rows[:20]}, default=str)
    user_prompt = f"""Question: {question}
SQL used: {sql}
Result: {result_preview}"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    return response.content


def answer_question(question: str) -> dict:
    """
    Returns a full trace: final answer, status, SQL used, attempt count,
    and per-attempt detail — same observability discipline as every
    previous day's agent.
    """
    start = time.time()
    schema_context = build_schema_context(question)

    sql = None
    error = None
    attempts_log = []
    status = "failed"
    final_result = None

    for attempt in range(1, MAX_RETRIES + 2):  # 1 initial + MAX_RETRIES refinements
        sql = generate_sql(question, schema_context, previous_attempt=sql, previous_error=error)

        validation = validate_sql(sql)
        if not validation["valid"]:
            error = "; ".join(validation["errors"])
            attempts_log.append({"attempt": attempt, "sql": sql, "stage": "validation", "error": error})
            continue

        result = execute_query(sql, question=question, attempt=attempt)
        if result["success"]:
            status = "answered"
            final_result = result
            attempts_log.append({"attempt": attempt, "sql": sql, "stage": "execution", "error": None})
            break
        else:
            error = result["error"]
            attempts_log.append({"attempt": attempt, "sql": sql, "stage": "execution", "error": error})

    latency_ms = round((time.time() - start) * 1000)

    if status == "answered":
        answer = answer_in_natural_language(
            question, sql, final_result["columns"], final_result["rows"]
        )
    else:
        answer = (
            "I wasn't able to generate a valid, executable query for this question "
            f"after {len(attempts_log)} attempt(s). Last error: {error}"
        )

    return {
        "question": question,
        "status": status,
        "sql": sql,
        "answer": answer,
        "attempts": len(attempts_log),
        "attempts_log": attempts_log,
        "latency_ms": latency_ms,
    }


def main():
    print("Agentic Text-to-SQL — type 'exit' to quit\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        result = answer_question(question)
        print(f"\nSQL: {result['sql']}")
        print(f"Answer: {result['answer']}")
        print(f"Status: {result['status']}  Attempts: {result['attempts']}  Latency: {result['latency_ms']}ms\n")


if __name__ == "__main__":
    main()
