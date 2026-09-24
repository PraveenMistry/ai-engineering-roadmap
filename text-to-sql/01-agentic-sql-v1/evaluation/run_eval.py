"""
Day 15 — Evaluation runner

Runs all 10 test cases through the agent and checks whether each
expected value actually appears in the generated answer. Same
substring-match-first philosophy as Day 13 — simple, but establishes
the pipeline; a stricter version would parse the SQL result directly
rather than checking the natural-language answer text.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
from agent import answer_question  # noqa: E402

TEST_CASES_PATH = os.path.join(os.path.dirname(__file__), "test_cases.json")


def load_test_cases():
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def run_evaluation():
    test_cases = load_test_cases()
    results = []

    for case in test_cases:
        print(f"[{case['id']}] {case['question']}")
        result = answer_question(case["question"])

        answer_lower = (result["answer"] or "").lower()
        missing = [
            expected for expected in case["expected_answer_contains"]
            if expected.lower() not in answer_lower
        ]
        passed = len(missing) == 0

        print(f"  SQL: {result['sql']}")
        print(f"  Answer: {result['answer']}")
        print(f"  {'PASS' if passed else 'FAIL — missing: ' + str(missing)}")
        print(f"  attempts={result['attempts']}  latency={result['latency_ms']}ms\n")

        results.append({
            "id": case["id"],
            "question": case["question"],
            "passed": passed,
            "missing": missing,
            "sql": result["sql"],
            "answer": result["answer"],
            "attempts": result["attempts"],
            "latency_ms": result["latency_ms"],
        })

    passed_count = sum(1 for r in results if r["passed"])
    print(f"\n{passed_count}/{len(results)} passed")

    if passed_count < len(results):
        print("Failed cases:")
        for r in results:
            if not r["passed"]:
                print(f"  - [{r['id']}] {r['question']}  (missing: {r['missing']})")

    return results


if __name__ == "__main__":
    run_evaluation()
