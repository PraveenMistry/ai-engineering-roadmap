"""
Day 14 — Mock tools, wired through the enforcement layers.

Call order for ANY tool request, no exceptions:
    1. schema_validation.validate_arguments()  — is the SHAPE trustworthy?
    2. policy.check_tool_permission()           — is the ACTION allowed?
    3. only then does the actual tool logic run

This order is deliberate: validating shape before deciding permission
means a malformed request never reaches business logic at all, and a
permission check never has to reason about garbage input.
"""

from schema_validation import validate_arguments
from policy import check_tool_permission

# Fake in-memory data. Nothing real — a mock for this exercise only.
FAKE_CUSTOMERS = {"123": {"name": "Acme Corp", "email": "billing@acme.example"}}
FAKE_INVOICES = {"inv-001": {"customer_id": "123", "amount": 4200}}

TOOLS_REQUIRING_VALIDATION = {"get_customer", "get_invoice", "create_ticket", "delete_customer", "execute_sql"}


def call_tool(tool_name: str, arguments: dict, requester: str = "policy-agent") -> dict:
    # Layer 1: schema validation
    if tool_name in TOOLS_REQUIRING_VALIDATION:
        validation = validate_arguments(tool_name, arguments)
        if not validation["valid"]:
            return {"success": False, "stage": "schema_validation", "errors": validation["errors"]}

    # Layer 2: policy — deterministic, never an LLM decision
    permission = check_tool_permission(tool_name, requester, arguments)
    if not permission["allowed"]:
        return {"success": False, "stage": "policy", "reason": permission["reason"]}

    # Layer 3: the actual tool logic (mock)
    if tool_name == "search_policy":
        return {"success": True, "result": f"[MOCK] searched policy docs for: {arguments.get('query')}"}

    if tool_name == "get_customer":
        customer = FAKE_CUSTOMERS.get(arguments["customer_id"])
        return {"success": True, "result": customer or "Customer not found"}

    if tool_name == "get_invoice":
        invoice = FAKE_INVOICES.get(arguments["invoice_id"])
        return {"success": True, "result": invoice or "Invoice not found"}

    if tool_name == "create_ticket":
        return {"success": True, "result": f"Ticket created for customer {arguments['customer_id']}"}

    if tool_name == "delete_customer":
        # Unreachable in practice — policy.py already returns "forbidden"
        # before this line can run. Left in deliberately so the dead
        # code path is visible and intentional, not silently missing.
        return {"success": True, "result": f"Customer {arguments['customer_id']} deleted"}

    if tool_name == "execute_sql":
        return {"success": True, "result": f"[MOCK] Executed: {arguments['query']}"}

    return {"success": False, "stage": "unknown_tool", "reason": f"No implementation for '{tool_name}'"}
