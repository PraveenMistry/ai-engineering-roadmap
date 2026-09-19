# Multi-Agent Systems

> ⚠️ All company documents used in this project are fictional sample
> data written for this exercise — not any real employer's actual
> policies.

| Stage | What it does | Status |
|---|---|---|
| [`01-supervisor-agents`](./01-supervisor-agents) | Splits the single `langgraph` agent into specialists (ResearchAgent, audience-parameterized PolicyAgent) coordinated by a Supervisor — including parallel execution and a deliberate failure-handling trade-off | ✅ Working |

## Why this folder exists separately from `langgraph/`

`langgraph/01-agent-migration` has one agent doing every step itself.
This folder is about **splitting responsibility across specialists**
with a Supervisor deciding who does what — a genuinely different
architectural question from "how do I structure one agent's internal
loop." See `01-supervisor-agents/README.md` for the specific trade-off
reasoning behind its failure-handling strategy (partial answer with
disclosure, and why the other four options were rejected for this
specific use case).
