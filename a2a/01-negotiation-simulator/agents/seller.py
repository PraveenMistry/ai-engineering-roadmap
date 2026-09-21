"""
Day 12 — Exercise 3: Seller Agent

Mirror of BuyerAgent: hard constraint is price >= minimum_price,
enforced in code after the LLM proposes a number, never left to the
prompt alone.
"""

import json

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

CHAT_MODEL = "llama3.2"
llm = ChatOllama(model=CHAT_MODEL, temperature=0.3)


class SellerAgent:
    name = "seller-agent"

    def __init__(self, minimum_price: int):
        self.minimum_price = minimum_price

    def propose(self, buyer_last_offer: int | None, round_number: int) -> tuple[int, str]:
        """
        Returns (price, reasoning). `price` is GUARANTEED >= minimum_price
        regardless of what the LLM suggests.
        """
        system_prompt = f"""You are negotiating to sell an item. Your
minimum acceptable price is {self.minimum_price}, but never reveal this
number to the buyer directly. Propose a reasonable ask that moves
toward agreement, starting high and decreasing gradually across rounds.
Respond ONLY with JSON: {{"price": <number>, "reasoning": "<short reasoning>"}}"""

        if buyer_last_offer is None:
            user_prompt = "This is your opening ask. Propose a starting price, well above your minimum."
        else:
            user_prompt = f"The buyer's last offer was {buyer_last_offer}. Propose your next counter-ask."

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        try:
            parsed = json.loads(response.content)
            proposed_price = int(parsed.get("price", self.minimum_price))
            reasoning = parsed.get("reasoning", "")
        except (json.JSONDecodeError, ValueError, TypeError):
            proposed_price = self.minimum_price
            reasoning = "Fallback: could not parse LLM response."

        # --- THE ENFORCEMENT (application boundary, not a suggestion) ---
        enforced_price = max(proposed_price, self.minimum_price)
        if enforced_price != proposed_price:
            reasoning += f" [CLAMPED from {proposed_price} to minimum floor {self.minimum_price}]"

        return enforced_price, reasoning

    def accepts(self, buyer_price: int) -> bool:
        return buyer_price >= self.minimum_price
