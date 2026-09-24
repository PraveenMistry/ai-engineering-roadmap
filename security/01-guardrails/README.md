# Day 14 — Security + Guardrails

> ⚠️ All company documents, customer records, and invoices are fictional
> sample/mock data for this exercise.

## The architecture

```
Input Guardrail  →  LLM  →  Output Guardrail  →  Tool Guardrail (policy.py)
   (regex,               (RAG/reasoning)         (deterministic
   deterministic)                                 allow/deny lookup)
                                                          ↓
                                              Schema Validation
                                            (runs BEFORE policy,
                                             on any tool call's
                                             arguments)
```

**The one rule underneath every exercise today:** never ask the LLM
whether something is safe. Every previous day in this program has
built toward this same boundary — the model reasons and generates,
plain deterministic code decides what's allowed to actually happen.
Today is that principle applied specifically to security instead of
retry limits or budget constraints.

## Exercise 1 — Prompt injection

```bash
python agent.py     # runs the "delete the database" attack by default
```

`guardrails.py`'s `input_guardrail()` runs BEFORE any LLM call or
document retrieval — a regex match on a known attack pattern refuses
immediately. This matters for two reasons, not just one: it's more
reliable than hoping the model resists (probabilistic vs.
deterministic), and it's cheaper — you don't pay for an LLM call on a
request you were always going to refuse.

The system prompt in `agent.py` also tells the model explicitly to
treat the entire user message as a question, never as an instruction —
this is defense-in-depth, not the primary defense. If the regex-based
guardrail ever misses a novel phrasing, the model's own instruction-
following behavior is the second layer, not the only one.

**Known limitation, stated honestly:** regex/keyword matching WILL miss
novel phrasings the pattern list doesn't anticipate (see the EM section
below for exactly how to think about this gap).

## Exercise 2 — Tool authorization

`policy.py`'s `check_tool_permission()` is a plain dictionary lookup —
zero LLM calls, ever. Test it directly:

```python
from policy import check_tool_permission
print(check_tool_permission("delete_customer", "policy-agent", {"customer_id": "123"}))
# {"allowed": False, "reason": "Destructive operation is not permitted"}
```

Note `execute_sql` isn't a flat allow/deny — it's `"restricted"`,
routed to `_check_sql_safety()`, which rejects anything containing
`DROP`, `DELETE`, `UPDATE`, etc., and only allows a simple
`SELECT ... FROM ...` shape. This mirrors how a real system would
handle "restricted" tools: not a binary switch, but a narrower
allow-list of *safe usage patterns* within that tool.

## Exercise 3 — Schema validation

```python
from schema_validation import validate_arguments
print(validate_arguments("get_customer", {"customer_id": 123}))
# invalid — int instead of string
print(validate_arguments("get_customer", {"customer_id": {"$ne": None}}))
# invalid — dict instead of string (the NoSQL-operator injection shape)
```

This runs **before** `policy.py`, not after — a malformed request
shouldn't reach permission logic at all. Same principle as validating
an HTTP request body before checking whether the user is authorized to
perform the action it describes.

## 🧪 Attack your own agent

```bash
python attack_suite.py
```

Produces exactly the requested table:

| Attack | Expected | Actual | Fixed? |
|---|---|---|---|
| Ignore instructions | refuse | (from your run) | |
| Reveal system prompt | refuse | | |
| Delete database (direct tool request) | deny | | |
| Unauthorized invoice access | deny | | |
| Invalid tool arguments | reject | | |
| NoSQL-style injection payload | reject | | |
| Dangerous SQL | reject | | |

Results also save to `results/attack_suite_results.json` — this is the
start of your AI security regression suite, same discipline as Day
13's `regression_compare()`: don't just eyeball a pass count, keep a
record of which specific attack passed or failed, in which run.

**If any attack shows `FAILED`:** fix the relevant layer
(`guardrails.py` for conversational attacks, `policy.py` or
`schema_validation.py` for tool attacks) and re-run. Never fix a failed
attack by editing the *system prompt* alone — if a tool-layer attack
got through, the bug is in `policy.py` or `schema_validation.py`, not
in how politely the agent was asked to behave.

## Where this is genuinely incomplete (say so, don't hide it)

- **Regex-based input guardrails have a ceiling.** A sufficiently novel
  or obfuscated injection phrasing (unicode tricks, translated text,
  splitting the attack across multiple turns) will slip past keyword
  matching. Production systems layer a classifier model trained
  specifically for prompt-injection detection on top of this, not
  instead of it — the regex layer stays because it's cheap and catches
  the common case for free.
- **`GRANTED_PERMISSIONS` is a hardcoded dict**, not a real identity
  system. Day 12's EM Architecture Challenge (Q4/Q5) already named this
  gap — "which tools should each agent have" needs a real
  authorization service in production, not a Python dict shipped in
  the same file as the agent code.
- **The output guardrail's PII detection is two regexes.** Real PII
  detection needs to catch names, addresses, and many more patterns
  than SSN/credit-card shapes — this demonstrates the mechanism, not a
  production-ready detector.

Naming these limitations explicitly is itself part of the exercise —
a security review that doesn't say what it *didn't* check is more
dangerous than one that does.

## Setup

```bash
pip install langchain langchain-ollama
ollama pull llama3.2
ollama pull nomic-embed-text
python ingest.py
```

## Files

```
day-14/
├── README.md
├── documents/            the 4 policy docs (carried forward)
├── ingest.py              builds vector_store.json
├── retrieve.py             semantic search (unchanged from Day 8)
├── guardrails.py           Exercise 1 — input/output guardrails
├── policy.py                Exercise 2 — tool authorization, deterministic
├── schema_validation.py      Exercise 3 — argument validation, runs before policy
├── tools.py                   mock tools wired through both enforcement layers
├── agent.py                    the Policy Agent, wrapped in guardrails
├── attack_suite.py              runs all attacks, produces the table, saves results
└── results/                      attack_suite_results.json lands here
```
