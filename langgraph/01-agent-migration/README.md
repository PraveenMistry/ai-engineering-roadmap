> ⚠️ **Note:** All company documents in this project (leave policy, remote work, contractor rules, etc.) are **fictional, synthetic sample data** written for this learning exercise. None of this reflects any real employer's actual policies.

# Day 8 — LangChain + LangGraph

## What actually changed today

Day 7's agent worked. Today isn't about fixing behavior — it's about
replacing the orchestration layer:

```
Day 7:  a hand-written `while` loop, manually counting attempts,
        manually branching on evaluation results

Day 8:  a LangGraph StateGraph — the same logic, but expressed as
        explicit nodes, an explicit state contract, and explicit
        conditional edges
```

The retrieval, evaluation, and generation code itself barely changed.
That's intentional — we're changing HOW the pieces are wired together,
not rebuilding the pieces.

## Files, in build order

```
day-08/
├── README.md
├── documents/           (same 4 policy docs, carried over from Day 7)
├── ingest.py             (unchanged from Day 7)
├── retrieve.py           (unchanged from Day 7)
├── basic_ollama.py       Step 1 — confirm LangChain talks to Ollama
├── simple_graph.py       Step 2 — toy graph, 3 stages in one file
├── graph_agent.py        Step 3 — real migration of Day 7's agent
└── test_graph.py         Step 4 — the 4 required tests
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U langchain langchain-ollama langgraph
python -c "import langchain, langgraph; print('OK')"
```

Your existing Ollama models (`llama3.2`, `nomic-embed-text`) don't
change — LangChain is just a different Python interface on top of the
same local Ollama server.

## Run order

### 1. Confirm the connection
```bash
python basic_ollama.py
```

### 2. Build the toy graph — watch it grow
Open `simple_graph.py`, set `STAGE = 1`, run it. Then `STAGE = 2`. Then
`STAGE = 3`, and try `force_insufficient_until` at `0`, then `1`, then
`99`. That last one is the real payoff: it proves the graph terminates
even when evaluation NEVER succeeds — the retry limit holds even with
zero real intelligence involved. If that didn't hold here, it wouldn't
hold in the real agent either, no matter how good your prompts are.

```bash
python simple_graph.py
```

### 3. Rebuild the vector store (if you haven't already for this folder)
```bash
python ingest.py
```

### 4. Run the real migrated agent
```bash
python graph_agent.py
```

### 5. Run the test suite
```bash
python test_graph.py
```

## Why the routing function has zero LLM calls in it

Look at `route_after_evaluation` in `graph_agent.py` — it's plain Python,
no model call, no prompt. The LLM's entire job is to answer one narrow
question inside `evaluate_context`: "is this sufficient?" What happens
*next* — retry, abstain, or answer — is a decision your code makes
deterministically. This is the same boundary from Day 7, just made more
visible by LangGraph's structure: state flows through nodes, but control
flow (the edges) is explicit and inspectable, not buried inside a prompt
somewhere hoping the model "does the right thing."

## What to actually verify against the 4 test cases

1. **Direct answer** — "How many annual leave days do employees get?"
   should resolve in 1 attempt. If it takes more, your evaluator might
   be too strict on clean, well-covered questions.

2. **Multi-step** — "Does the remote work policy apply to contractors?"
   should show `documents_retrieved` containing BOTH `remote-work.md`
   and `contractor-policy.md` by the time it answers — if it only ever
   retrieves one of them and still answers, check whether the evaluator
   is being too lenient.

3. **Unanswerable** — "What is our maternity leave policy?" must end
   `abstained`. If it answers anyway, that's a hallucination risk to
   fix before anything else.

4. **Retry protection** — `test_4_retry_protection` mocks `retrieve_top_k`
   to always return nothing, proving the graph still terminates at
   `MAX_RETRIES + 1` attempts and abstains rather than looping. This
   test doesn't need a real LLM to be meaningful — it's testing your
   application's guardrail, not the model's judgment.

## One thing to watch for going forward

Same limitation as Day 7: **no conversation memory across turns.** Each
call to `answer_question()` starts from a fresh `RAGState` — there's no
way for the graph to know what was asked previously. LangGraph actually
has built-in support for this (checkpointers, threads) — worth flagging
now, but we're deliberately not adding it yet. One new capability at a
time.
