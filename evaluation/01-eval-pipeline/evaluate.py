"""
Day 13 — Exercise 2: Run the agent across the full dataset.

Saves a timestamped, labeled results file to results/ so Exercise 6's
before/after comparison has two real snapshots to diff, not just
whatever's currently in memory.
"""

import json
import os
import sys
import time

from agent import run_agent

DATASET_PATH = "dataset.json"
RESULTS_DIR = "results"


def load_dataset(path: str = DATASET_PATH) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_evaluation(label: str = "run") -> str:
    """
    Runs every question in dataset.json through the agent, saves results,
    returns the path to the saved file.
    """
    dataset = load_dataset()
    results = []

    for i, item in enumerate(dataset, start=1):
        print(f"[{i}/{len(dataset)}] ({item['category']}) {item['question']}")
        result = run_agent(item["id"], item["question"])
        results.append(result)
        print(f"  -> status={result['status']}  latency={result['latency_ms']}ms  "
              f"tool_calls={result['tool_calls']}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = int(time.time())
    output_path = os.path.join(RESULTS_DIR, f"{label}_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved: {output_path}")
    return output_path


if __name__ == "__main__":
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    run_evaluation(label)
