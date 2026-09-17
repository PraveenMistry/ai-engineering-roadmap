# LangGraph

> ⚠️ All company documents used in this project are fictional sample
> data written for this exercise — not any real employer's actual
> policies.

| Stage | What it does | Status |
|---|---|---|
| [`01-agent-migration`](./01-agent-migration) | Migrates `rag/03-agentic-rag`'s hand-written retry loop into a LangGraph `StateGraph` — same logic, explicit state/nodes/conditional edges instead of a manual `while` loop | ✅ Working |

## Why this folder exists separately from `rag/`

The retrieval and evaluation logic didn't change here — only the
orchestration layer did. Keeping this separate from `rag/` makes that
distinction visible in the repo structure itself: this folder is about
*how the pieces are wired together*, not about retrieval quality.

Future additions here: conversation memory (LangGraph checkpointers),
then a proper multi-agent split once a single agent isn't enough.