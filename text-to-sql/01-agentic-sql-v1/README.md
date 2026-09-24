# Day 15 — Agentic Text-to-SQL v1

> ⚠️ All customers, invoices, and products are fictional seed data
> generated for this exercise.

## A substitution, stated upfront

Using **SQLite**, not PostgreSQL. Zero server setup, built into Python,
and the schema/validator/agent logic are written to port to real
PostgreSQL with minimal changes — see "Porting to PostgreSQL" below.
If you have Postgres available and want the real thing, that section
tells you exactly what to swap.

## The pipeline

```
Question
   ↓
Schema Retrieval    (agent/schema_retriever.py — introspects the LIVE db)
   ↓
SQL Generation       (agent/sql_generator.py — LLM proposes a SELECT)
   ↓
Validation            (agent/sql_validator.py — deterministic, Day 14's pattern)
   ↓
Execution              (agent/executor.py — read-only conn, timeout, audit log)
   ↓
Success ──────────────────────────→ Natural-language Answer
   │
   ↓ (validation OR execution failure)
Refinement (error fed back to SQL Generation) ──→ retry, up to MAX_RETRIES
   │
   ↓ (still failing after MAX_RETRIES)
Fail honestly, state the last error
```

This is the exact same shape as Day 7's RAG loop (retrieve → evaluate →
rewrite → answer/abstain) — just with "evaluate" split into two
concrete checks (validate the SQL's shape, then actually try running
it) and "abstain" renamed "fail" because the failure mode here is
different: not "insufficient evidence" but "the generated query didn't
work," which is meaningfully closer to a normal software bug than an
epistemic gap.

## This is your Day 14 connection

`sql_validator.py` is `policy.py` from Day 14, applied to SQL:

- Forbidden keywords (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`,
  `TRUNCATE`, plus SQLite-specific ones like `ATTACH`/`PRAGMA`) — same
  deterministic keyword-rejection pattern.
- Allowed-tables enforcement — same idea as Day 14's tool allow-list,
  just checking table names instead of tool names.
- **Never asks the LLM whether a query is safe.** The model that wrote
  the query is not a trustworthy judge of its own output — identical
  reasoning to why Day 14's `check_tool_permission()` never calls an LLM.

`executor.py` adds what Day 14 didn't need: a **read-only connection**
(SQLite's `mode=ro` URI — the OS/DB layer refuses writes even if
something slipped past the validator, which is defense-in-depth, not a
replacement for it) and a **query timeout** (a watchdog thread calling
`connection.interrupt()`), plus **audit logging** of every execution
attempt to `logs/audit_log.jsonl` — this is the direct, literal
implementation of the "audit logging" requirement, not a metaphor for it.

## Setup and run

```bash
pip install langchain langchain-ollama
ollama pull llama3.2
python setup_db.py          # builds company.db with 8 customers, 15 invoices
cd agent
python agent.py              # interactive — try the 10 questions yourself
```

Run the evaluation suite:
```bash
cd evaluation
python run_eval.py
```

## The seed data, and why the expected answers are exact

`setup_db.py` computes invoice dates **relative to today** (so "revenue
last month" always means a real month, not a stale hardcoded one), but
the actual amounts, quantities, and row counts are fixed:

- 8 customers, 5 products, 15 invoices (5 per month across 3 months)
- Total invoice value: **3430**
- Unpaid invoices: **3** (held by Globex Inc and Initech)
- Highest-revenue product: **Service Plan** ($1500 across all sales)
- Highest-quantity product: **Widget A** (6 units sold)

`evaluation/test_cases.json` encodes these as exact expected values —
same evaluation discipline as Day 13, just against a database instead
of documents.

## Where the deviation from a "real" setup matters (say so, don't hide it)

- **SQLite has no true concept of a read-only DB *user*** the way
  Postgres does (a role with `GRANT SELECT` only, enforced server-side
  regardless of what connection string a client uses). The `mode=ro`
  URI flag is a client-side promise, not a server-enforced guarantee —
  a determined attacker with filesystem access could reopen the file
  differently. On Postgres, create an actual read-only role:
  ```sql
  CREATE ROLE readonly_agent LOGIN PASSWORD '...';
  GRANT SELECT ON customers, products, invoices, invoice_items TO readonly_agent;
  ```
  and connect as that role — the guarantee then lives in the database
  itself, not in how the client happened to open the connection.
- **The timeout here is client-side** (`connection.interrupt()` after
  5 seconds). Postgres's `SET statement_timeout = '5s'` is enforced by
  the server regardless of what the client does — strictly stronger.
- **`ALLOWED_TABLES` is a hardcoded set.** In a system with real
  role-based access (Day 12's EM Architecture territory again), which
  tables an agent may query should come from that agent's actual
  granted permissions, not a constant in a Python file it could
  theoretically edit.

## Porting to PostgreSQL

1. `pip install psycopg2-binary`
2. In `schema.sql`: `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
3. In `executor.py`: replace the `sqlite3.connect(uri, uri=True)` call
   with a `psycopg2.connect(...)` using a real read-only role's
   credentials, and replace the watchdog-thread timeout with
   `cursor.execute("SET statement_timeout = '5000'")` before running
   the query.
4. Everything else — `schema_retriever.py`'s introspection query
   changes from `PRAGMA table_info` to a query against
   `information_schema.columns`, but the rest of the pipeline
   (`sql_generator.py`, `sql_validator.py`, `agent.py`) needs no
   changes at all, since they only ever deal with SQL text and query
   results, never the connection mechanics directly.

## Files

```
day-15/
├── README.md
├── setup_db.py                  builds company.db with date-relative seed data
├── schema/
│   └── schema.sql                 DDL (SQLite dialect, notes for Postgres)
├── agent/
│   ├── schema_retriever.py         Step 1 — live schema introspection + table selection
│   ├── sql_generator.py             Step 2 — LLM generates/refines SQL
│   ├── sql_validator.py              Step 3 — deterministic guardrail (Day 14's pattern)
│   ├── executor.py                    Step 4 — read-only exec, timeout, audit log
│   └── agent.py                        orchestrates the full retry/refinement loop
├── evaluation/
│   ├── test_cases.json                 10 questions, precomputed exact expected values
│   └── run_eval.py                      runs them all, reports pass/fail
└── logs/
    └── audit_log.jsonl                   populated at runtime by executor.py
```
