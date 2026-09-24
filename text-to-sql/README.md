# Agentic Text-to-SQL

> ⚠️ Uses SQLite with fictional generated seed data — see
> `01-agentic-sql-v1/README.md` for why, and exactly what changes to
> run this against real PostgreSQL instead.

| Stage | What it does | Status |
|---|---|---|
| [`01-agentic-sql-v1`](./01-agentic-sql-v1) | Schema retrieval → SQL generation → validation → execution → refinement loop, with read-only execution, timeouts, and audit logging | ✅ Working |

## The direct line back to `security/`

`01-agentic-sql-v1/agent/sql_validator.py` is `security/01-guardrails/policy.py`,
applied to SQL instead of tool calls — same rule: the LLM generates,
deterministic code decides what's allowed to run. This folder is what
that principle looks like once "the tool" is a real database instead
of a mock function.
