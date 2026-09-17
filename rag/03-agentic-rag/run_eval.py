"""
Day 7 — Bonus: Run the full test set through the agent.

This is the part that actually tells you whether the agent is behaving
correctly, not just whether the code runs. Pay most attention to the
`final_status` breakdown at the end — if any "unanswerable" question
comes back "answered", that's the priority bug to fix.
"""

import json

from agent import answer_question

QUESTIONS_PATH = "questions.json"
RESULTS_PATH = "eval_results.json"


def load_questions(path: str = QUESTIONS_PATH) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_eval():
    questions = load_questions()
    results = []

    for i, item in enumerate(questions, start=1):
        category = item["category"]
        question = item["question"]

        print(f"[{i}/{len(questions)}] ({category}) {question}")
        outcome = answer_question(question)

        results.append({
            "category": category,
            "question": question,
            "answer": outcome["answer"],
            "log": outcome["log"],
        })

        print(f"  -> status={outcome['log']['final_status']} "
              f"attempts={outcome['log']['retrieval_attempts']} "
              f"latency={outcome['log']['latency_seconds']}s\n")

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print_summary(results)
    print(f"\nFull results saved to '{RESULTS_PATH}'")


def print_summary(results: list[dict]):
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    by_category = {}
    for r in results:
        cat = r["category"]
        by_category.setdefault(cat, {"answered": 0, "abstained": 0, "error": 0, "total": 0})
        status = r["log"]["final_status"]
        by_category[cat][status] = by_category[cat].get(status, 0) + 1
        by_category[cat]["total"] += 1

    for cat, counts in by_category.items():
        print(f"\n{cat.upper()}  (n={counts['total']})")
        print(f"  answered:  {counts.get('answered', 0)}")
        print(f"  abstained: {counts.get('abstained', 0)}")
        print(f"  error:     {counts.get('error', 0)}")

    # The one number that matters most: did "unanswerable" leak any answers?
    unanswerable = [r for r in results if r["category"] == "unanswerable"]
    leaked = [r for r in unanswerable if r["log"]["final_status"] == "answered"]
    if leaked:
        print(f"\n⚠️  {len(leaked)} unanswerable question(s) got an 'answered' status "
              f"instead of abstaining — check these for hallucination:")
        for r in leaked:
            print(f"   - {r['question']}")
    else:
        print("\n✅ No unanswerable questions leaked an answer — abstain logic held.")


if __name__ == "__main__":
    run_eval()
