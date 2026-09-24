"""
Day 14 — Exercise 2: Tool authorization policy layer

This is a deterministic lookup, not an LLM decision. The agent may
REQUEST any tool call it wants, phrased however convincingly — what
actually executes is decided entirely here, in code. This function
never calls an LLM and never will; that's the point.
"""

import re

TOOL_POLICY = {
    "search_policy": "allowed",
    "get_customer": "allowed_with_permission",
    "get_invoice": "allowed_with_permission",
    "create_ticket": "allowed_with_permission",
    "delete_customer": "forbidden",
    "execute_sql": "restricted",
}

# Which requester identities hold which permission grants. A real system
# backs this with an actual identity/permission store (this is Day 12's
# EM Architecture Q4/Q5 territory — "which tools should Research Agent
# have?") — kept as a hardcoded dict here to keep the exercise focused
# on the enforcement mechanism itself.
GRANTED_PERMISSIONS = {
    "policy-agent": {"search_policy"},  # deliberately NO customer-data access at all
    "support-agent": {"search_policy", "get_customer", "get_invoice", "create_ticket"},
}

SAFE_SQL_PATTERN = re.compile(r"^\s*SELECT\s+.+\s+FROM\s+\w+\s*(WHERE\s+.+)?\s*$", re.IGNORECASE)
FORBIDDEN_SQL_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "--", ";", "EXEC"]


def check_tool_permission(tool_name: str, requester: str, arguments: dict) -> dict:
    """
    The ONLY function that decides whether a tool call actually executes.
    Returns {"allowed": bool, "reason": str}.
    """
    policy = TOOL_POLICY.get(tool_name)

    if policy is None:
        return {"allowed": False, "reason": f"Unknown tool '{tool_name}' is not registered"}

    if policy == "forbidden":
        return {"allowed": False, "reason": "Destructive operation is not permitted"}

    if policy == "allowed":
        return {"allowed": True, "reason": "Read-only, no permission required"}

    if policy == "allowed_with_permission":
        granted = GRANTED_PERMISSIONS.get(requester, set())
        if tool_name in granted:
            return {"allowed": True, "reason": f"'{requester}' has an explicit grant for '{tool_name}'"}
        return {"allowed": False, "reason": f"'{requester}' lacks permission for '{tool_name}'"}

    if policy == "restricted":
        if tool_name == "execute_sql":
            return _check_sql_safety(arguments.get("query", ""))
        return {"allowed": False, "reason": "Restricted tool has no defined safety check"}

    return {"allowed": False, "reason": "Unrecognized policy state"}


def _check_sql_safety(query) -> dict:
    if not isinstance(query, str):
        return {"allowed": False, "reason": "Query must be a string"}

    upper_query = query.upper()
    for keyword in FORBIDDEN_SQL_KEYWORDS:
        if keyword in upper_query:
            return {"allowed": False, "reason": f"Query contains forbidden keyword: '{keyword}'"}

    if not SAFE_SQL_PATTERN.match(query):
        return {"allowed": False, "reason": "Only simple SELECT ... FROM ... queries are permitted"}

    return {"allowed": True, "reason": "Read-only SELECT query passed safety check"}
