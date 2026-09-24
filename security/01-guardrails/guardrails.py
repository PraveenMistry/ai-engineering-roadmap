"""
Day 14 — Exercise 1: Input & Output Guardrails

    Input Guardrail -> LLM -> Output Guardrail -> Tool Guardrail (policy.py)

The input guardrail runs BEFORE any LLM call, for two reasons:
  1. An LLM's resistance to a jailbreak is probabilistic — a regex match
     on a known attack pattern is deterministic. Don't rely on the model
     "choosing" to refuse when you can structurally prevent it from ever
     seeing the attempt phrased that way reach generation unchecked.
  2. Blocking early means you don't pay for an LLM call (or a document
     retrieval) on a request you were always going to refuse anyway —
     a genuine cost/latency win, not just a safety one.

This is intentionally simple keyword/regex matching, not ML-based
classification. That's a real limitation (see README), but it's also
exactly the same "start simple, establish the mechanism" principle from
every previous day's exercises.
"""

import re

INJECTION_PATTERNS = [
    (r"ignore (all|any)?\s*(previous|prior|the)?\s*instructions", "instruction override attempt"),
    (r"disregard (your |the )?(rules|guidelines|policy|instructions)", "instruction override attempt"),
    (r"reveal (the )?(hidden |system )?(system )?prompt", "system prompt extraction attempt"),
    (r"(show|print|output) (me )?(your |the )?(system )?(prompt|instructions)", "system prompt extraction attempt"),
    (r"you are (the |an? )?(administrator|admin|root|ceo|owner)", "false authority claim"),
    (r"as the (administrator|admin|ceo|owner)", "false authority claim"),
    (r"delete (the )?(database|all|customer|records)", "destructive action request"),
    (r"export (all )?(customer )?(pii|personal|private) ?(data|information)?", "PII exfiltration attempt"),
    (r"act as (a |an )?(dan|jailbreak|unrestricted)", "jailbreak persona attempt"),
]

COMPILED_INJECTION_PATTERNS = [(re.compile(p, re.IGNORECASE), label) for p, label in INJECTION_PATTERNS]

# Deliberately simple PII detectors for the output guardrail. A real
# system would use a proper PII-detection library; this is enough to
# demonstrate the MECHANISM — catching something in generated output
# that the input guardrail structurally cannot, since it doesn't exist
# until after generation happens.
PII_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "SSN-like pattern"),
    (re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"), "credit-card-like pattern"),
]


def input_guardrail(user_input: str) -> dict:
    """
    Deterministic pre-filter. Runs BEFORE the LLM ever sees the input.
    Returns {"blocked": bool, "reason": str | None}.
    """
    for pattern, label in COMPILED_INJECTION_PATTERNS:
        if pattern.search(user_input):
            return {"blocked": True, "reason": label}
    return {"blocked": False, "reason": None}


def output_guardrail(generated_answer: str) -> dict:
    """
    Runs AFTER generation, before the answer reaches the user. Catches
    what the input guardrail structurally cannot — e.g. a PII pattern
    that shows up in generated text (even innocently, from a retrieved
    chunk the model repeated back).
    Returns {"blocked": bool, "flagged": bool, "reason": str | None, "sanitized_answer": str}.
    """
    for pattern, label in PII_PATTERNS:
        if pattern.search(generated_answer):
            redacted = pattern.sub("[REDACTED]", generated_answer)
            return {
                "blocked": False,
                "flagged": True,
                "reason": label,
                "sanitized_answer": redacted,
            }

    return {
        "blocked": False,
        "flagged": False,
        "reason": None,
        "sanitized_answer": generated_answer,
    }
