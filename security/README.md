# Security + Guardrails

> ⚠️ All company/customer/invoice data used here is fictional mock data.

| Stage | What it does | Status |
|---|---|---|
| [`01-guardrails`](./01-guardrails) | Input/output guardrails, deterministic tool authorization, schema validation, and a runnable attack suite | ✅ Working |

## The rule this whole topic enforces

Every previous topic folder built toward the same boundary in a
different context — Day 7's retry limits, Day 10's failure handling,
Day 12's price constraints. This folder applies it to security
specifically: **the LLM reasons and generates; deterministic code
decides what's actually allowed to happen.** See
`01-guardrails/README.md` for the honest list of what this
implementation does NOT yet cover — stating a security control's
limits is part of the control, not a footnote.
