"""
Day 15 — Step 1 of the pipeline: Schema Retrieval

Reads the ACTUAL live database schema via SQLite's introspection tables
rather than a hardcoded string — schema drift (someone alters a table)
shows up automatically instead of silently going stale.

Also does simple keyword-based "table selection": for a tiny 4-table
database this barely matters, but it demonstrates the concept the
roadmap's Text-to-SQL module calls out — a real system with 200 tables
absolutely cannot dump the full schema into every prompt, so filtering
to relevant tables first is a real, necessary step, not an academic one.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "company.db")

# Keywords that hint a table is relevant — deliberately simple, same
# "start basic, establish the mechanism" principle as every prior day.
TABLE_KEYWORDS = {
    "customers": ["customer", "client", "buyer"],
    "invoices": ["invoice", "revenue", "paid", "unpaid", "bill"],
    "invoice_items": ["item", "product sold", "quantity", "line item"],
    "products": ["product", "item", "sold", "sku"],
}


def get_full_schema(db_path: str = DB_PATH) -> dict:
    """Introspects the live database. Returns {table_name: [column definitions]}."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    schema = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [f"{row[1]} {row[2]}" for row in cursor.fetchall()]  # name, type
        schema[table] = columns

    conn.close()
    return schema


def select_relevant_tables(question: str, schema: dict) -> list[str]:
    """
    Light keyword-based relevance filter. Falls back to ALL tables if
    nothing matches clearly — for a database this small, under-filtering
    is a much safer failure mode than over-filtering and missing a table
    the query actually needed.
    """
    question_lower = question.lower()
    relevant = set()

    for table, keywords in TABLE_KEYWORDS.items():
        if any(kw in question_lower for kw in keywords):
            relevant.add(table)

    if not relevant:
        return list(schema.keys())

    # Questions almost always need customers/invoices as join anchors —
    # include them whenever any other table was matched, since most
    # real questions here are multi-table joins, not single-table lookups.
    relevant.update({"customers", "invoices"} & schema.keys())
    return sorted(relevant)


def build_schema_context(question: str, db_path: str = DB_PATH) -> str:
    """Returns a formatted schema description ready to drop into an LLM prompt."""
    full_schema = get_full_schema(db_path)
    relevant_tables = select_relevant_tables(question, full_schema)

    lines = []
    for table in relevant_tables:
        lines.append(f"TABLE {table} ({', '.join(full_schema[table])})")

    lines.append("\nRelationships:")
    lines.append("invoices.customer_id -> customers.customer_id")
    lines.append("invoice_items.invoice_id -> invoices.invoice_id")
    lines.append("invoice_items.product_id -> products.product_id")

    return "\n".join(lines)


if __name__ == "__main__":
    print(build_schema_context("Which customers have unpaid invoices?"))
