"""
Day 12 — Exercises 4 & 6: Coordinator

Routes every message between Buyer and Seller, logs each one with full
observability fields, and — this is Exercise 6 — decides what happens
when an agent fails mid-negotiation. See README.md for the reasoning
behind the specific choice made here (bounded retry, then terminate).
"""

import json
import os
import time
import uuid

from agents.buyer import BuyerAgent
from agents.seller import SellerAgent
from agents.reviewer import review_negotiation
from protocol.messages import create_message

LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
MAX_ROUNDS = 6
MAX_RETRIES_ON_FAILURE = 2  # Exercise 6's bounded retry limit


def run_negotiation(
    max_budget: int = 950,
    minimum_price: int = 900,
    simulate_seller_failure_round: int | None = None,
) -> dict:
    """
    simulate_seller_failure_round: Exercise 6's failure injection hook.
    Set to a round number (e.g. 2) to force the seller to raise a
    TimeoutError on that round's FIRST attempt, so you can observe the
    coordinator's retry/terminate logic without needing a real outage.
    """
    conversation_id = f"neg-{uuid.uuid4().hex[:6]}"
    buyer = BuyerAgent(max_budget=max_budget)
    seller = SellerAgent(minimum_price=minimum_price)

    messages: list[dict] = []
    status = "in_progress"
    round_number = 0
    last_seller_price = None

    def log_message(msg: dict, latency: float, status_label: str) -> None:
        entry = dict(msg)
        entry["latency"] = round(latency, 3)
        entry["status"] = status_label
        messages.append(entry)

    while round_number < MAX_ROUNDS:
        round_number += 1

        # ---------------- Buyer's turn ----------------
        start = time.time()
        buyer_price, buyer_reasoning = buyer.propose(last_seller_price, round_number)
        elapsed = time.time() - start
        msg_type = "proposal" if round_number == 1 else "counter_proposal"
        buyer_msg = create_message(
            conversation_id, buyer.name, "seller-agent", msg_type,
            {"price": buyer_price, "reasoning": buyer_reasoning},
        )
        log_message(buyer_msg, elapsed, "sent")

        if last_seller_price is not None and buyer_price >= last_seller_price:
            accept_msg = create_message(
                conversation_id, buyer.name, "seller-agent", "accept",
                {"price": last_seller_price},
            )
            log_message(accept_msg, 0, "sent")
            status = "agreed"
            break

        # ---------------- Seller's turn (with Exercise 6 failure handling) ----------------
        seller_result = None
        seller_attempt = 0

        while seller_attempt <= MAX_RETRIES_ON_FAILURE:
            seller_attempt += 1
            start = time.time()
            try:
                if simulate_seller_failure_round == round_number and seller_attempt == 1:
                    raise TimeoutError("Simulated seller agent timeout")
                seller_price, seller_reasoning = seller.propose(buyer_price, round_number)
                elapsed = time.time() - start
                seller_result = (seller_price, seller_reasoning, elapsed)
                break
            except TimeoutError as e:
                elapsed = time.time() - start
                fail_msg = create_message(
                    conversation_id, "seller-agent", buyer.name, "reject",
                    {"error": str(e), "attempt": seller_attempt},
                )
                log_message(fail_msg, elapsed, "failed")
                # loop continues if attempts remain (bounded retry)

        if seller_result is None:
            # Exercise 6's decision, made in code: after MAX_RETRIES_ON_FAILURE
            # attempts, terminate gracefully rather than hang or guess.
            terminate_msg = create_message(
                conversation_id, "coordinator", buyer.name, "terminate",
                {"reason": "seller unavailable after bounded retries"},
            )
            log_message(terminate_msg, 0, "terminated")
            status = "terminated_seller_unavailable"
            break

        seller_price, seller_reasoning, elapsed = seller_result
        seller_msg = create_message(
            conversation_id, "seller-agent", buyer.name, "counter_proposal",
            {"price": seller_price, "reasoning": seller_reasoning},
        )
        log_message(seller_msg, elapsed, "sent")
        last_seller_price = seller_price

        if seller_price <= buyer_price:
            accept_msg = create_message(
                conversation_id, "seller-agent", buyer.name, "accept",
                {"price": buyer_price},
            )
            log_message(accept_msg, 0, "sent")
            status = "agreed"
            break
    else:
        status = "no_agreement_max_rounds"

    review = review_negotiation(messages, max_budget, minimum_price)

    result = {
        "conversation_id": conversation_id,
        "status": status,
        "rounds": round_number,
        "messages": messages,
        "review": review,
    }

    save_log(conversation_id, result)
    return result


def save_log(conversation_id: str, result: dict) -> None:
    os.makedirs(LOGS_DIR, exist_ok=True)
    path = os.path.join(LOGS_DIR, f"{conversation_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"Log saved: {path}")


def print_summary(result: dict) -> None:
    print(f"\nConversation: {result['conversation_id']}")
    print(f"Status: {result['status']}")
    print(f"Rounds: {result['rounds']}")
    print("Review:")
    print(json.dumps(result["review"], indent=2))


if __name__ == "__main__":
    print("=== Normal negotiation ===")
    normal_result = run_negotiation(max_budget=950, minimum_price=900)
    print_summary(normal_result)

    print("\n=== Exercise 6: Seller fails on round 2 ===")
    failure_result = run_negotiation(
        max_budget=950, minimum_price=900, simulate_seller_failure_round=2
    )
    print_summary(failure_result)
