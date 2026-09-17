"""
Day 8 — Test suite for graph_agent.py

Covers all 4 required tests:
  1. Direct answer
  2. Multi-step (may rewrite once)
  3. Unanswerable -> abstain
  4. Retry protection -> forced retrieval failure must NOT loop forever
"""

from unittest.mock import patch

import graph_agent


def test_1_direct_answer():
    print("\n=== TEST 1: Direct answer ===")
    result = graph_agent.answer_question("How many annual leave days do employees get?")
    print(f"status={result['status']}  attempts={result['attempt_count']}")
    assert result["status"] == "answered", "Expected a direct answer"
    print("PASS")


def test_2_multi_step():
    print("\n=== TEST 2: Multi-step ===")
    result = graph_agent.answer_question("Does the remote work policy apply to contractors?")
    print(f"status={result['status']}  attempts={result['attempt_count']}  "
          f"queries={result['queries_used']}")
    print(f"documents_retrieved={result['documents_retrieved']}")
    assert result["status"] == "answered", "Expected an eventual answer"
    print("PASS")


def test_3_unanswerable():
    """
    Note: an earlier version of this test used "maternity leave policy" —
    but that question actually has real semantic overlap with the
    documented "parental leave" policy, so a good agent answering it
    with a caveat ("not explicitly called maternity leave, but here's
    the relevant parental leave provision") is CORRECT behavior, not a
    hallucination. That was a flaw in the test's assumption, not a bug
    in the agent. Travel reimbursement has zero overlap with anything
    in the knowledge base, making it a cleaner true-negative test.
    """
    print("\n=== TEST 3: Unanswerable ===")
    result = graph_agent.answer_question("What is the company's travel reimbursement policy?")
    print(f"status={result['status']}  attempts={result['attempt_count']}")
    print(f"documents_retrieved={result['documents_retrieved']}")
    print(f"evaluation_reason={result['evaluation_reason']}")
    print(f"answer={result['answer']}")
    assert result["status"] == "abstained", "Expected the agent to abstain, not guess"
    print("PASS")


def test_3b_graceful_partial_match():
    """
    Not a strict pass/fail assertion — this documents the maternity leave
    case as a real, interesting behavior to eyeball rather than assert on.
    A good answer here explicitly flags that "maternity leave" isn't a
    named policy while still surfacing the genuinely relevant parental
    leave provision. A bad answer would present parental leave numbers
    AS IF they were literally "the maternity leave policy," with no
    caveat. Read the printed answer yourself and judge which this is.
    """
    print("\n=== TEST 3b: Graceful partial match (informational, no assertion) ===")
    result = graph_agent.answer_question("What is our maternity leave policy?")
    print(f"status={result['status']}  attempts={result['attempt_count']}")
    print(f"answer={result['answer']}")
    print("(No assertion — inspect the answer above for an honest caveat vs. a silent substitution.)")


def test_4_retry_protection():
    """
    Forces retrieve_top_k to always return an empty list — simulating a
    total retrieval failure (e.g. vector store down, embedding call
    failing). The graph MUST still terminate at MAX_RETRIES and abstain,
    never loop forever. This is the test that actually proves your
    production guardrail works, independent of model quality.
    """
    print("\n=== TEST 4: Retry protection (forced retrieval failure) ===")

    with patch("graph_agent.retrieve_top_k", return_value=[]):
        result = graph_agent.answer_question("How many annual leave days do employees get?")

    print(f"status={result['status']}  attempts={result['attempt_count']}")
    assert result["status"] == "abstained", "Expected abstain when retrieval always fails"
    assert result["attempt_count"] <= graph_agent.MAX_RETRIES + 1, (
        f"Graph ran {result['attempt_count']} attempts — retry limit was not enforced!"
    )
    print(f"PASS — graph terminated after {result['attempt_count']} attempts, did not loop forever")


if __name__ == "__main__":
    tests = [
        test_1_direct_answer,
        test_2_multi_step,
        test_3_unanswerable,
        test_3b_graceful_partial_match,
        test_4_retry_protection,
    ]

    results = {}
    for test_fn in tests:
        try:
            test_fn()
            results[test_fn.__name__] = "PASS"
        except AssertionError as e:
            print(f"FAILED: {e}")
            results[test_fn.__name__] = f"FAIL — {e}"
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
            results[test_fn.__name__] = f"ERROR — {type(e).__name__}: {e}"

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, outcome in results.items():
        print(f"  {name}: {outcome}")
