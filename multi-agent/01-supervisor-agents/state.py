"""
Day 10 — Shared state contract.

Every agent and the supervisor read/write this same structure. Keeping
it in one file (rather than each agent inventing its own shape) is what
makes agents composable — the supervisor doesn't need to know HOW an
agent works internally, only what fields it's expected to fill in.
"""

from typing import TypedDict, Optional


class MultiAgentState(TypedDict):
    request_id: str
    question: str

    # Which audience(s) this question needs — filled in by the supervisor.
    # ["employee"], ["contractor"], or ["employee", "contractor"] for
    # comparison questions (Exercise 3).
    audiences: list[str]

    # Raw retrieved chunks per audience (ResearchAgent's output)
    employee_documents: list[dict]
    contractor_documents: list[dict]

    # Interpreted answers per audience (PolicyAgent's output)
    employee_answer: Optional[str]
    contractor_answer: Optional[str]

    # Final answer after review/synthesis
    final_answer: Optional[str]

    # "answered" | "partial" | "abstained" | "error"
    status: str

    # Observability (same philosophy as Day 7's logging)
    selected_agents: list[str]
    execution_log: list[dict]     # [{"agent": "...", "seconds": ..., "outcome": "..."}]

    # Exercise 4 — failure simulation
    simulate_failure_in: Optional[str]   # "employee" | "contractor" | None
    failure_reason: Optional[str]
