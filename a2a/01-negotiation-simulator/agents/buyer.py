"""
Day 12 — Exercise 2: Buyer Agent

Hard constraint: price <= max_budget. The LLM proposes a number based
on negotiation context; the code clamps it afterward. No matter how the
model is prompted, worded, or how "convinced" it gets mid-negotiation,
it is structurally impossible for this agent to offer above budget —
the enforcement doesn't live in the prompt, it lives in a line of code
that runs regardless of what the LLM said.
"""

import json

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

CHAT_MODEL = "llama3.2"  # update if your `ollama list` differs
llm = ChatOllama(model=CHAT_MODEL, temperature=0.3)  # slight variability = more natural negotiation


class BuyerAgent:
    name = "buyer-agent"

    def __init__(self, max_budget: int):
        self.max_budget = max_budget

    def propose(self, seller_last_offer: int | None, round_number: int) -> tuple[int, str]:
        """
        Returns (price, reasoning). `price` is GUARANTEED <= max_budget
        regardless of what the LLM suggests.
        """
        system_prompt = f"""You are negotiating to buy an item. Your
maximum budget is {self.max_budget}, but never reveal this number to
the seller directly. Propose a reasonable offer that moves toward
agreement, starting low and increasing gradually across rounds.
Respond ONLY with JSON: {{"price": <number>, "reasoning": "<short reasoning>"}}"""

        if seller_last_offer is None:
            user_prompt = "This is your opening offer. Propose a starting price, well below your budget."
        else:
            user_prompt = f"The seller's last ask was {seller_last_offer}. Propose your next counter-offer."

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        try:
            parsed = json.loads(response.content)
            proposed_price = int(parsed.get("price", self.max_budget))
            reasoning = parsed.get("reasoning", "")
        except (json.JSONDecodeError, ValueError, TypeError):
            proposed_price = self.max_budget
            reasoning = "Fallback: could not parse LLM response."

        # --- THE ENFORCEMENT (application boundary, not a suggestion) ---
        enforced_price = min(proposed_price, self.max_budget)
        if enforced_price != proposed_price:
            reasoning += f" [CLAMPED from {proposed_price} to budget limit {self.max_budget}]"

        return enforced_price, reasoning

    def accepts(self, seller_price: int) -> bool:
        return seller_price <= self.max_budget
