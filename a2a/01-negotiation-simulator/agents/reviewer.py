"""
Day 12 — Exercise 5: Reviewer

Doesn't participate in the negotiation — reviews the message log
AFTER it's done. This is deliberately a separate pass, not something
baked into the coordinator's real-time logic, so the audit trail exists
independent of whether the negotiation itself went well or is disputed
later. Same instinct as Day 7's structured logging: you want to be able
to answer "what actually happened here?" without trusting either
agent's own account of events.
"""


def review_negotiation(messages: list[dict], buyer_max_budget: int, seller_min_price: int) -> dict:
    findings = {
        "total_rounds": 0,
        "final_price": None,
        "outcome": "unknown",
        "buyer_exceeded_budget": False,
        "seller_below_minimum": False,
        "clamped_offers": [],   # evidence the enforcement layer actually fired
    }

    proposal_messages = [m for m in messages if m["type"] in ("proposal", "counter_proposal")]
    findings["total_rounds"] = len(proposal_messages)

    for m in messages:
        reasoning = m.get("payload", {}).get("reasoning", "") or ""
        if "[CLAMPED" in reasoning:
            findings["clamped_offers"].append({
                "message_id": m["message_id"],
                "sender": m["sender"],
                "reasoning": reasoning,
            })

    accept_messages = [m for m in messages if m["type"] == "accept"]
    if accept_messages:
        final = accept_messages[-1]
        final_price = final["payload"]["price"]
        findings["final_price"] = final_price
        findings["outcome"] = "agreed"

        # These should NEVER be true if enforcement worked correctly —
        # checking them anyway is the whole point of an independent
        # reviewer. Don't just trust that the code you wrote earlier
        # actually ran the way you think it did.
        if final_price > buyer_max_budget:
            findings["buyer_exceeded_budget"] = True
        if final_price < seller_min_price:
            findings["seller_below_minimum"] = True
    else:
        findings["outcome"] = "no_agreement"

    return findings
