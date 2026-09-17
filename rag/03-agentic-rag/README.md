> ⚠️ **Note:** All company documents in this project (leave policy, remote work, contractor rules, etc.) are **fictional, synthetic sample data** written for this learning exercise. None of this reflects any real employer's actual policies.

# Day 7 — Enterprise Policy Agent (Agentic RAG)

## What changed from Day 5/6

Day 5/6 RAG was a straight line:

```
Question → Search → Answer
```

That breaks in three specific, predictable ways:
1. The question needs a search query decision — what to actually search for
2. A single search might not surface enough evidence to answer confidently
3. There's no knowledge base at all for some questions — and a straight-line
   RAG system will happily hallucinate an answer anyway

Today's agent turns the straight line into a loop with judgment built in:

```
Question
   ↓
Agent decides search query
   ↓
Search
   ↓
Evaluate: is this enough evidence?
   ├── Yes → Answer
   └── No  → Rewrite query → Search again (up to MAX_RETRIES)
                                   ↓
                        Still not enough → ABSTAIN
```

**One rule underlies everything here: the LLM never touches the vector
database directly.** It only ever *requests* an action (`{"action": "search",
"query": "..."}`) or *returns a judgment* (`{"sufficient": true/false}`).
Your Python code is what actually executes the search, counts the retries,
and enforces the abstain limit. This is the same request→execute→respond
pattern from Day 4's tool calling — an agent is just that pattern, looped.

## Knowledge base

```
documents/
├── leave-policy.md        (updated: 24 days annual leave — matches Exercise 1's test)
├── remote-work.md         (unchanged from Day 5)
├── engineering.md         (unchanged from Day 5)
└── contractor-policy.md   (NEW — deliberately designed for multi-hop questions)
```

`contractor-policy.md` was written so that contractor questions genuinely
require combining it with another document — e.g. "Does the remote work
policy apply to contractors?" needs BOTH `remote-work.md` (what the
default policy is) AND `contractor-policy.md` (that contractors are
exempt from it). A single semantic search often only surfaces one of the
two on the first pass — which is exactly the scenario Exercise 4's query
rewrite is meant to catch.

## Exercise 1 — Baseline retrieval

Reuses Day 6's embedding + cosine similarity retrieval, just re-indexed
to include the new contractor document. Test query:

> "How many annual leave days do employees get?" → expect **24 days**

If this doesn't return 24, the fix isn't in today's code — it's confirming
`ingest.py` picked up the corrected `leave-policy.md` and you re-ran it.

## Exercise 2 — The agent's first decision

Before: your code always searched with the raw user question.
Now: an LLM call decides the actual search query.

Why this matters even though it looks like overhead — user questions
aren't always good search queries. "Can I work remotely?" is a fine
question but a mediocre search query. An LLM can normalize vague phrasing
into something more retrievable ("remote work eligibility policy") before
it ever hits the vector store. This is a small win in Exercise 2, but it's
the same mechanism Exercise 4 leans on harder when the *first* query fails
and needs to be re-thought.

## Exercise 3 — Context evaluation

This is the piece that prevents hallucination later. After retrieval, a
separate LLM call — NOT the same call that will eventually answer the
question — is asked one narrow question: *"is there enough evidence here
to answer confidently?"* It returns structured JSON, not prose, so your
code can branch on it reliably (`if evaluation["sufficient"]:`) instead of
parsing free text.

Keeping this as a separate call from the final answer matters: an LLM
asked to "answer if you can" will often just answer anyway, even on thin
evidence. An LLM asked only to judge sufficiency, with no path to also
produce an answer in the same call, is a cleaner, more honest checkpoint.

## Exercise 4 — Query rewriting

When evaluation says `sufficient: false`, the agent gets one more shot —
it rewrites the query based on the evaluator's stated `reason`, not just
blindly retrying the same search. Feeding the reason back in is the whole
point: "the context doesn't mention contractor eligibility" is actionable
information a rewrite step can use; a blind retry of the identical query
would just get the identical result.

## Exercise 5 — Answer or abstain

The test case that matters most: **"What is our maternity leave policy?"**
There is no such document. A good agent:

```
Search → no useful evidence → rewrite → search again → still nothing
  → max attempts reached → ABSTAIN
```

An abstain response should say plainly that the knowledge base doesn't
cover this — never softly imply an answer it isn't sure of. This is the
single most important behavior in the whole exercise. A RAG system that
retrieves well but still guesses when it shouldn't is arguably worse than
one with mediocre retrieval, because it's *confidently* wrong.

## Exercise 6 — Production observability

Every request now produces a structured log record:

```json
{
  "request_id": "a1b2c3d4",
  "question": "Does the remote work policy apply to contractors?",
  "retrieval_attempts": 2,
  "queries_used": ["remote work contractor policy", "contractor remote work eligibility"],
  "documents_retrieved": ["remote-work.md", "contractor-policy.md"],
  "latency_seconds": 3.42,
  "model": "llama3.2",
  "total_tokens": 1180,
  "final_status": "answered"
}
```

This is the difference between a script and a system. Without this, when
something goes wrong in front of a real user, you have no way to answer
"what did the agent actually search for, how many attempts did it take,
and why did it decide to abstain?" `final_status` should be one of
`answered`, `abstained`, or `error`.

## The test set — questions.json

18 questions across four categories, because a demo that only tests happy
paths tells you nothing:

- **Answerable** — should retrieve cleanly and answer in 1 attempt
- **Multi-step** — require combining `contractor-policy.md` with another
  document; may take 2 attempts before evidence is judged sufficient
- **Unanswerable** — no matching document exists; must end in `abstained`,
  never a guessed answer
- **Ambiguous** — under-specified questions ("Can I work remotely?") where
  a reasonable agent might reasonably ask for clarification rather than
  guess a persona (employee vs. contractor) — worth watching how your
  agent actually handles this, since nothing forces a "correct" behavior
  here the way abstain/answer does

Run all 18 through the agent and look at the aggregate `final_status`
breakdown, not just individual answers. If every "unanswerable" question
comes back `answered` anyway, that's the bug to fix before anything else.

## Files in this folder

```
week-01/day-07/
├── README.md
├── documents/              (4 policy docs, see above)
├── ingest.py                Exercise 1 — builds the vector store
├── retrieve.py               Exercise 1 — semantic search
├── agent.py                Exercises 2-6 — the full agent loop + logging
├── questions.json           test set (18 questions, 4 categories)
└── run_eval.py               runs questions.json through the agent, reports results
```

## Setup

Same as Day 5/6 — no API key needed:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
pip install ollama
```

If your `ollama list` shows different model names/tags than `llama3.2` /
`nomic-embed-text`, update the `CHAT_MODEL` / `EMBEDDING_MODEL` constants
at the top of `ingest.py`, `retrieve.py`, and `agent.py` to match.

## Run order

```bash
python ingest.py       # (re)builds vector_store.json — includes contractor-policy.md now
python retrieve.py     # sanity-check retrieval alone, same as Day 5/6
python agent.py        # runs one interactive question through the full agent loop
python run_eval.py     # runs all 18 questions.json entries, prints a results summary
```
