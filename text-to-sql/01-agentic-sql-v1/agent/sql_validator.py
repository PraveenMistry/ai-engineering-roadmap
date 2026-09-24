"""
Day 15 — Step 3: SQL Validation

This is Day 14's policy.py pattern, applied to SQL specifically: the
LLM generates a query, but whether it EXECUTES is decided here, in
plain deterministic code — never by asking the model "is this query
safe?" The model that just wrote the query is not a trustworthy judge
of whether its own output is dangerous.
"""

import re

FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
    "ATTACH", "DETACH", "PRAGMA", "VACUUM", "REPLACE",
]

ALLOWED_TABLES = {"customers", "products", "invoices", "invoice_items"}

MAX_QUERY_LENGTH = 2000


def validate_sql(sql: str) -> dict:
    """
    Returns {"valid": bool, "errors": list[str]}.
    """
    errors = []

    if not sql or not sql.strip():
        return {"valid": False, "errors": ["Empty query"]}

    if len(sql) > MAX_QUERY_LENGTH:
        errors.append(f"Query exceeds maximum length ({MAX_QUERY_LENGTH} chars)")

    upper_sql = sql.upper()

    stripped = sql.strip().rstrip(";")
    if not stripped.upper().startswith("SELECT"):
        errors.append("Only SELECT statements are permitted")

    if ";" in stripped:
        errors.append("Multiple statements are not permitted (semicolon detected mid-query)")

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper_sql):
            errors.append(f"Forbidden keyword detected: {keyword}")

    referenced_tables = set(re.findall(r"(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)", sql, re.IGNORECASE))
    disallowed = referenced_tables - ALLOWED_TABLES
    if disallowed:
        errors.append(f"Query references disallowed/unknown table(s): {sorted(disallowed)}")

    return {"valid": len(errors) == 0, "errors": errors}


if __name__ == "__main__":
    print(validate_sql("SELECT COUNT(*) FROM customers"))
    print(validate_sql("DROP TABLE customers"))
    print(validate_sql("SELECT * FROM customers; DELETE FROM invoices"))
    print(validate_sql("SELECT * FROM users"))
