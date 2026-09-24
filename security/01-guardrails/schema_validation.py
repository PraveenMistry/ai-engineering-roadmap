"""
Day 14 — Exercise 3: Schema validation

Never trust external input. AI-generated tool-call arguments ARE
external input — exactly like a JSON body from an untrusted HTTP
client. This layer runs BEFORE policy.py and BEFORE the tool itself,
regardless of what check_tool_permission would decide, because a
malformed request shouldn't even reach permission logic.
"""

TOOL_SCHEMAS = {
    "get_customer": {"customer_id": "string"},
    "get_invoice": {"invoice_id": "string"},
    "create_ticket": {"customer_id": "string", "message": "string"},
    "delete_customer": {"customer_id": "string"},
    "execute_sql": {"query": "string"},
}


def validate_arguments(tool_name: str, arguments: dict) -> dict:
    """
    Returns {"valid": bool, "errors": list[str]}.
    """
    schema = TOOL_SCHEMAS.get(tool_name)
    if schema is None:
        return {"valid": False, "errors": [f"No schema registered for tool '{tool_name}'"]}

    if not isinstance(arguments, dict):
        return {"valid": False, "errors": [f"Arguments must be an object, got {type(arguments).__name__}"]}

    errors = []
    for field, expected_type in schema.items():
        if field not in arguments:
            errors.append(f"Missing required field: '{field}'")
            continue

        value = arguments[field]

        if expected_type == "string" and not isinstance(value, str):
            errors.append(
                f"Field '{field}' must be a string, got {type(value).__name__} "
                f"({value!r}) — possible type-confusion or injection payload "
                f"(e.g. a NoSQL operator object like {{'$ne': null}})"
            )

    # Reject unexpected extra fields too. This matters for exactly the
    # NoSQL-operator case: {"customer_id": {"$ne": null}} would pass a
    # naive "does customer_id exist?" check while smuggling an operator
    # object through as the value — catching the wrong TYPE (above)
    # already blocks it, but rejecting unknown top-level fields closes
    # the same class of surprise for arguments with extra smuggled keys.
    unexpected = set(arguments.keys()) - set(schema.keys())
    if unexpected:
        errors.append(f"Unexpected field(s) not in schema: {sorted(unexpected)}")

    return {"valid": len(errors) == 0, "errors": errors}
