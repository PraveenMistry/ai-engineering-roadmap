# Day 10 — Multi-Agent Enterprise Policy System

> ⚠️ All company documents (leave policy, remote work, contractor rules,
> engineering practices) are fictional sample data for this exercise.

## What changed from Day 7/8

Day 7/8 had ONE agent doing everything: retrieve, evaluate, rewrite,
answer. Today splits that into specialists with narrower jobs:

```
ResearchAgent   → retrieves documents only, no interpretation
PolicyAgent     → interprets evidence, FOR A SPECIFIC AUDIENCE (employee/contractor)
Reviewer        → quality-checks a single answer, OR synthesizes two
Supervisor      → classifies the question, routes to the right agent(s),
                  runs independent agents in parallel, handles failures
```

## Why PolicyAgent is parameterized instead of two separate files

The file structure given for today lists `research_agent.py` and
`policy_agent.py` — but Exercise 3 needs an "Employee Policy Agent" and
a "Contractor Agent." Rather than duplicating near-identical files, one
`policy_agent(question, documents, audience)` function does both — the
reasoning process is identical, only the lens (`audience`) changes.
Same instinct as Day 7's shared `_chat_json` helper: a parameter beats
copy-pasted logic that will inevitably drift out of sync.

## Exercise 1 — Two specialist agents

Test each one standalone BEFORE wiring them together — same philosophy
as every previous day:

```bash
python research_agent.py    # confirms retrieval alone works
python policy_agent.py      # confirms interpretation alone works
```

Notice `research_agent.py` never touches an LLM, and `policy_agent.py`
never touches the vector store directly — it only receives documents
that were already retrieved. This separation is what makes Exercise 4's
failure simulation meaningful: we can make PolicyAgent fail without
breaking ResearchAgent, and observe exactly how the Supervisor reacts.

## Exercise 2 — Supervisor

```
Question → Supervisor classifies audience(s) → routes to agent(s) → Result
```

Run:
```bash
python supervisor.py
```

Try the two test questions:
- *"How many annual leave days do employees receive?"* → classified as
  `["employee"]`, routes straight through the single-agent path
- *"Can contractors work remotely five days a week?"* → classified as
  `["contractor"]`

Every response includes `request_id`, `selected_agent`, `execution_time`,
and `result` exactly as required — printed as JSON after each answer.

**One thing to watch:** `classify_audiences()` is the ONLY LLM call
involved in routing. Everything after that — which function runs, how
failures are handled — is plain Python. Same boundary principle from
every previous day: the model classifies, code decides.

## Exercise 3 — Parallel execution

Ask: *"Compare employee and contractor remote-work policies."* This
gets classified as `["employee", "contractor"]` and triggers
`answer_comparison()`, which can run in two modes:

```
Sequential:  ResearchAgent(employee) → PolicyAgent(employee) →
             ResearchAgent(contractor) → PolicyAgent(contractor) → Synthesizer

Parallel:    ResearchAgent(employee) → PolicyAgent(employee) ──┐
             ResearchAgent(contractor) → PolicyAgent(contractor) ──┼──→ Synthesizer
```

Run the built-in comparison:
```python
from supervisor import benchmark_comparison
benchmark_comparison("Compare employee and contractor remote-work policies.")
```

This uses `concurrent.futures.ThreadPoolExecutor` to run both branches
concurrently — genuinely parallel, not just organized to look parallel.
Expect the parallel run to take roughly as long as the SLOWER of the
two branches, not the sum of both — that's the entire point of running
independent work concurrently instead of one-after-another.

## Exercise 4 — Failure simulation and the trade-off decision

Trigger it directly:
```python
from supervisor import answer_comparison
result = answer_comparison(
    "Compare employee and contractor remote-work policies.",
    simulate_failure_in="contractor",
)
print(result["status"])   # "partial"
print(result["result"])   # explains what happened, doesn't pretend nothing did
```

### The decision, and why

When one branch of a comparison fails, I chose: **partial answer with
explicit disclosure** — not retry, not a fallback model, not a full
abort, and not human approval. Here's the reasoning for each option I
rejected:

- **Retry** — only makes sense for genuinely transient errors (a
  momentary network blip). A simulated timeout, or a real failure in
  the LLM call itself, is likely to fail again immediately on retry,
  just adding latency for no benefit. I'd only add retry here if I had
  evidence failures were actually transient in practice, not by default.
- **Fallback to a different model** — overkill for what's essentially a
  low-stakes internal Q&A tool. Fallback providers make sense when
  uptime is genuinely business-critical (Day 4's LLM Gateway territory);
  here the cost of added complexity isn't justified by the stakes.
- **Full abort** — throwing away the SUCCESSFUL half of the answer
  because the other half failed is strictly worse for the user than
  giving them what did work. If the employee lookup succeeded, telling
  the user nothing at all is a worse outcome than giving them the
  employee answer with an honest note about what's missing.
- **Human approval** — appropriate for high-stakes actions (Week 14's
  territory: deleting data, deploying to production). A policy Q&A
  answer is not that. Adding a human-in-the-loop step here would slow
  down a low-risk interaction for no real safety benefit.

**The one non-negotiable part of this decision:** the partial answer
must clearly say what's missing and why, never silently present half
the picture as if it were the whole answer. `status: "partial"` in the
log makes this distinction machine-readable too — worth remembering for
Week 13's evaluation work, where "answered" and "partial" should almost
certainly be tracked as different outcomes, not lumped together as
"success."

If this were a higher-stakes system — approving an actual refund,
executing a production deployment — several of these rejected options
(retry with backoff, human approval) would become the right call
instead. The lesson isn't "partial answer is always correct." It's
that **the right failure-handling strategy depends entirely on the
stakes of what failed**, and that's worth deciding deliberately, not
defaulting to whatever's easiest to code.

## Setup

Same as previous days:
```bash
ollama pull llama3.2
ollama pull nomic-embed-text
pip install ollama langchain langchain-ollama
python ingest.py    # builds vector_store.json for this folder
```

## Files

```
day-10/
├── README.md
├── state.py              shared state contract
├── tools/
│   └── search_policy.py  the one tool both agents share
├── research_agent.py     Exercise 1 — retrieval only
├── policy_agent.py       Exercise 1/3 — interpretation, audience-parameterized
├── reviewer.py           quality check (single) + synthesizer (comparison)
└── supervisor.py         Exercises 2/3/4 — classification, routing, parallel execution, failure handling
```
