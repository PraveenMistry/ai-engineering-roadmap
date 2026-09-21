# Evaluation + Observability

> ⚠️ All company documents used here are fictional sample data.

| Stage | What it does | Status |
|---|---|---|
| [`01-eval-pipeline`](./01-eval-pipeline) | 20-question eval dataset, instrumented agent, basic metrics, LLM judge, multi-agent trace analysis, and a real regression test | ✅ Working |

## Why this matters more than it looks like it does

Every previous topic folder produced a system that *worked* on the
examples we happened to try. This folder is about the uncomfortable
next question: **how do you know it still works after you change
something?** See `01-eval-pipeline/README.md`'s opening note for a
concrete example of this discipline applied to itself — an earlier
exercise's own "expected answer" turned out to be wrong, based on
findings from `rag/03-agentic-rag`.
