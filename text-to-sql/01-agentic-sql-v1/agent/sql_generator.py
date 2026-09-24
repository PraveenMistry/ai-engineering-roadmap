"""
Day 15 — Step 2: SQL Generation (+ refinement on failure)

Generates a single SELECT query from the question and schema context.
When called again after a validation/execution failure, includes the
prior attempt and its error — same "feed the failure reason back in"
principle as Day 7's query rewriter, just applied to SQL instead of
document search queries.
"""

import json

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

CHAT_MODEL = "llama3.2"
llm = ChatOllama(model=CHAT_MODEL, temperature=0)

SYSTEM_PROMPT = """You generate SQL SELECT queries for a SQLite database.

Rules:
- ONLY generate SELECT statements. Never DROP, DELETE, UPDATE, INSERT,
  ALTER, TRUNCATE, or any statement that modifies data.
- Use ONLY the tables and columns given in the schema below.
- Use standard SQLite SQL syntax (e.g. date('now', '-1 month') style
  functions for relative dates, strftime for month grouping).
- Return exactly one query, no comments, no explanation, no markdown fencing.

Respond ONLY with JSON: {"sql": "<the query>"}"""


def generate_sql(
    question: str,
    schema_context: str,
    previous_attempt: str | None = None,
    previous_error: str | None = None,
) -> str:
    """
    Returns the raw SQL string. previous_attempt/previous_error, when
    given, tell the model exactly what failed and why — this is the
    refinement path from Step 3's upgraded workflow diagram.
    """
    if previous_attempt and previous_error:
        user_prompt = f"""Schema:
{schema_context}

Question: {question}

Your previous attempt failed:
{previous_attempt}

Error: {previous_error}

Generate a corrected query."""
    else:
        user_prompt = f"""Schema:
{schema_context}

Question: {question}"""

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    try:
        parsed = json.loads(response.content)
        return parsed.get("sql", "").strip()
    except json.JSONDecodeError:
        return ""


if __name__ == "__main__":
    from schema_retriever import build_schema_context

    question = "How many customers do we have?"
    schema = build_schema_context(question)
    sql = generate_sql(question, schema)
    print(f"Question: {question}\nGenerated SQL: {sql}")
